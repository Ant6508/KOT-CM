# -*- coding: utf-8 -*-
"""adb, frida-server et attache au jeu, pour le chargement live.

Les lectures adb (chemin d'adb, appareils, version, pid) viennent du noyau
commun (`kotnoyau.adb`) ; kotcm garde ici ses erreurs (`ErreurLive`, cles de
`textes.py`), son choix d'appareil (--serial, puis ANDROID_SERIAL, puis le seul
connecte) et son frida-server. Aucun chemin ni serial de l'operateur : adb est
pris dans KOT_ADB ou KOTCM_ADB, puis dans le SDK, le PATH, les emplacements
standard, enfin le dossier de MEmu (kotnoyau.adb.chemin_adb). La version du jeu
doit avoir une table d'adresses dans le noyau.

frida : kotcm utilise frida 17.19.0 et son serveur
`/data/local/tmp/frida-server-17.19.0` (spec, 9.2 bis et 9.3). Il le pousse
s'il est absent de l'appareil ou n'en porte pas l'empreinte (copie locale,
telechargee au besoin depuis la release officielle), le lance s'il ne tourne
pas, et refuse de s'attacher si un autre frida-server tourne : un seul a la
fois sur l'appareil.
"""

from __future__ import annotations

import hashlib
import http.client
import lzma
import os
import shutil
import subprocess
import time
import urllib.request
from pathlib import Path

from kotcm.live import ErreurLive, dossier_donnees
from kotnoyau import adb as noyau_adb
# Repris du noyau ; ADB_STANDARD, CLE_MEMU et parse_pid restent importables d'ici (tests, chargeur).
from kotnoyau.adb import (ADB_STANDARD, CLE_MEMU, PAQUET, ErreurAdb, dossier_memu,  # noqa: F401
                          parse_appareils, parse_pid, parse_version)
from kotnoyau.table import Table, VersionInconnue, disponibles

FRIDA = "17.19.0"
SERVEUR = "/data/local/tmp/frida-server-" + FRIDA
NOM_SERVEUR = "frida-server-%s-android-x86_64" % FRIDA
URL_SERVEUR = "https://github.com/frida/frida/releases/download/%s/%s.xz" % (FRIDA, NOM_SERVEUR)
# Empreinte de la release officielle decompressee (relevee le 2026-10-14) : une copie, locale ou sur
# l'appareil, qui ne la porte pas (fichier mal choisi, abime) est remplacee au lieu de bloquer.
# A changer avec FRIDA : sinon tout telechargement serait refuse.
SHA256_SERVEUR = "e6f7e35901db8e83d40088d51692afa77bd23c8ae69e521c3e5955f741a7b9d6"


def chemin_adb(environ=os.environ, which=shutil.which, existe=os.path.isfile, memu=dossier_memu) -> str:
    """L'adb choisi par l'utilisateur, sinon celui du SDK, sinon celui de MEmu (kotnoyau.adb.chemin_adb)."""
    try:
        return noyau_adb.chemin_adb(environ, which, existe, memu)
    except ErreurAdb as e:
        raise ErreurLive("live_adb_absent") from e


def versions_connues() -> str:
    return ", ".join("%s (%d)" % (t.nom, t.code) for t in (Table.pour(c) for c in disponibles()))


def seul_appareil(appareils: list[str]) -> str:
    if len(appareils) == 1:
        return appareils[0]
    raise ErreurLive("live_appareil", appareils=", ".join(appareils) or "-")


def parse_serveurs(sortie: str) -> tuple[bool, list[str]]:
    """Sortie de `ps -A -o PID,ARGS` -> (le notre tourne, les autres frida-server)."""
    notre, autres = False, []
    for ligne in sortie.splitlines()[1:]:
        champs = ligne.split()
        if len(champs) < 2:
            continue
        nom = champs[1].rsplit("/", 1)[-1]
        if nom == "frida-server-" + FRIDA:
            notre = True
        elif nom.startswith("frida-server"):
            autres.append(nom)
    return notre, autres


def telecharger(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=120) as reponse:
        return reponse.read()


def copie_locale(dossier: Path, telecharger=telecharger, empreinte: str = SHA256_SERVEUR) -> Path:
    """La copie locale de frida-server, telechargee et decompressee au besoin.

    Une copie presente mais d'une autre empreinte est remplacee. L'ecriture
    passe par un `.part` renomme a la fin : une copie a moitie ecrite n'est
    jamais prise pour la bonne. Tout echec (reseau, archive, empreinte,
    disque) donne `live_telechargement`, qui dit ou poser le fichier a la main.
    """
    chemin = Path(dossier) / "frida-server" / NOM_SERVEUR
    if chemin.is_dir():         # l'extraction de 7-Zip cree un dossier a ce nom : rien ne pourrait s'y ecrire
        raise ErreurLive("live_dossier_a_la_place", chemin=str(chemin))
    try:
        if chemin.is_file() and hashlib.sha256(chemin.read_bytes()).hexdigest() == empreinte:
            return chemin
    except OSError:
        pass                    # copie illisible : retelechargee, et l'ecriture dira si le disque refuse

    def echec(detail: str) -> ErreurLive:
        return ErreurLive("live_telechargement", version=FRIDA, url=URL_SERVEUR, chemin=str(chemin), detail=detail)

    try:
        binaire = lzma.decompress(telecharger(URL_SERVEUR))
    except (OSError, ValueError, lzma.LZMAError, http.client.HTTPException) as e:
        raise echec(str(e) or type(e).__name__) from e
    recue = hashlib.sha256(binaire).hexdigest()
    if recue != empreinte:
        raise echec("sha256 %s != %s" % (recue[:12], empreinte[:12]))
    partiel = chemin.with_name(chemin.name + ".part")
    try:
        chemin.parent.mkdir(parents=True, exist_ok=True)
        partiel.write_bytes(binaire)
        os.replace(partiel, chemin)
    except OSError as e:
        try:
            partiel.unlink(missing_ok=True)
        except OSError:
            pass            # un .part qui reste sera reecrit au prochain essai
        raise echec(str(e)) from e
    return chemin


class Appareil:
    def __init__(self, serial: str | None = None, environ=os.environ, executer=subprocess.run,
                 attendre=time.sleep, telecharger=telecharger, empreinte: str = SHA256_SERVEUR):
        self._demande = serial
        self.environ, self.executer, self.attendre = environ, executer, attendre
        self.telecharger, self.empreinte = telecharger, empreinte
        self._adb: str | None = None
        self._serial: str | None = None

    def _lancer(self, args: list[str], avec_serial: bool = True) -> str:
        if self._adb is None:
            self._adb = chemin_adb(self.environ)
        commande = [self._adb] + (["-s", self.serial] if avec_serial else []) + args
        # stdin ferme : `adb shell` transmettrait sinon notre entree au shell Android.
        r = self.executer(commande, stdin=subprocess.DEVNULL, capture_output=True, text=True)
        if r.returncode != 0:
            raise ErreurLive("live_adb", detail="%s : %s" % (" ".join(args), (r.stderr or "").strip()))
        return r.stdout

    @property
    def serial(self) -> str:
        if self._serial is None:
            self._serial = (self._demande or self.environ.get("ANDROID_SERIAL")
                            or seul_appareil(parse_appareils(self._lancer(["devices"], avec_serial=False))))
        return self._serial

    def shell(self, commande: str) -> str:
        return self._lancer(["shell", commande])

    def verifier_version(self) -> Table:
        """La table d'adresses du jeu installe ; refus (live_version) d'une version sans table."""
        v = parse_version(self.shell("dumpsys package " + PAQUET))
        if v is not None:
            try:
                return Table.pour(v[1], v[0])
            except VersionInconnue:
                pass
        raise ErreurLive("live_version", trouvee=("%s (%d)" % v) if v else "?", connues=versions_connues())

    def pid_jeu(self) -> int:
        pid = parse_pid(self.shell("pidof " + PAQUET))
        if pid is None:
            raise ErreurLive("live_jeu_absent")
        return pid

    def pousser_serveur(self) -> None:
        """Pousse frida-server sur l'appareil depuis la copie locale (telechargee au besoin)."""
        local = copie_locale(dossier_donnees(self.environ), self.telecharger, self.empreinte)
        self._lancer(["push", str(local), SERVEUR])

    def preparer_serveur(self) -> None:
        """Lance notre frida-server (pousse d'abord s'il manque ou n'est pas le bon) ; refuse si un autre tourne."""
        notre, autres = parse_serveurs(self.shell("ps -A -o PID,ARGS"))
        if autres:
            raise ErreurLive("live_autre_serveur", serveurs=", ".join(autres))
        if notre:
            return
        # Absent, abime ou d'une autre version : on pousse la copie locale, verifiee elle aussi.
        if self.shell("sha256sum %s 2>/dev/null || echo absent" % SERVEUR).split()[:1] != [self.empreinte]:
            self.pousser_serveur()
        # A chaque lancement : sinon un push dont le chmod a echoue resterait inutilisable.
        self.shell("chmod 755 " + SERVEUR)
        # nohup et flux rediriges : sinon adb shell reste bloque sur le serveur detache.
        self.shell("nohup %s -D </dev/null >/dev/null 2>&1 &" % SERVEUR)
        for _ in range(20):
            self.attendre(0.25)
            if parse_serveurs(self.shell("ps -A -o PID,ARGS"))[0]:
                return
        raise ErreurLive("live_serveur_lance", chemin=SERVEUR)

    def attacher(self, pid: int):
        """Session frida sur le jeu, par pid (le nom du processus est tronque par ART)."""
        try:
            import frida
        except ImportError as e:
            raise ErreurLive("live_frida_absent", attendue=FRIDA) from e
        if frida.__version__ != FRIDA:
            raise ErreurLive("live_frida_version", trouvee=frida.__version__, attendue=FRIDA)
        return frida.get_device(self.serial, timeout=10).attach(pid)
