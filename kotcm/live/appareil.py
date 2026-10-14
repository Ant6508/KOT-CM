# -*- coding: utf-8 -*-
"""adb, frida-server et attache au jeu, pour le chargement live.

Recopie et adapte de `controller/device.py` (kot_headless) et de
`controller/device.py` (kot_reverse) : kotcm n'importe rien de `controller/`.
Aucun chemin ni serial de l'operateur : adb est pris dans KOTCM_ADB, puis dans
le SDK de ANDROID_SDK_ROOT ou ANDROID_HOME, puis dans le PATH, puis aux
emplacements standard du SDK Android, puis dans le dossier de MEmu (lu dans le
registre, comme le TAS) ; l'appareil dans --serial, puis ANDROID_SERIAL, puis
le seul appareil connecte.

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
import re
import shutil
import subprocess
import time
import urllib.request
from pathlib import Path

from kotcm.live import ErreurLive, dossier_donnees

PAQUET = "com.zeptolab.thieves.google"
VERSION = ("2.84", 4755781)
FRIDA = "17.19.0"
SERVEUR = "/data/local/tmp/frida-server-" + FRIDA
NOM_SERVEUR = "frida-server-%s-android-x86_64" % FRIDA
URL_SERVEUR = "https://github.com/frida/frida/releases/download/%s/%s.xz" % (FRIDA, NOM_SERVEUR)
# Empreinte de la release officielle decompressee (relevee le 2026-10-14) : une copie, locale ou sur
# l'appareil, qui ne la porte pas (fichier mal choisi, abime) est remplacee au lieu de bloquer.
# A changer avec FRIDA : sinon tout telechargement serait refuse.
SHA256_SERVEUR = "e6f7e35901db8e83d40088d51692afa77bd23c8ae69e521c3e5955f741a7b9d6"
ADB_STANDARD = (
    os.path.join(os.environ.get("LOCALAPPDATA", ""), "Android", "Sdk", "platform-tools", "adb.exe"),
    r"C:\Program Files (x86)\Android\android-sdk\platform-tools\adb.exe",
)
# L'installeur de MEmu inscrit ici son dossier (InstallLocation, par exemple
# C:\Program Files\Microvirt) ; adb.exe est dans le sous-dossier MEmu.
CLE_MEMU = r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\MEmu"


def dossier_memu() -> str | None:
    """Le dossier d'installation de MEmu lu dans le registre, ou None (winreg n'existe que sous Windows)."""
    try:
        import winreg
    except ImportError:
        return None
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, CLE_MEMU) as cle:
            valeur, _ = winreg.QueryValueEx(cle, "InstallLocation")
    except OSError:
        return None
    return valeur or None


def chemin_adb(environ=os.environ, which=shutil.which, existe=os.path.isfile, memu=dossier_memu) -> str:
    """L'adb choisi par l'utilisateur, sinon celui du SDK, sinon celui de MEmu.

    Le SDK passe avant MEmu : quand deux adb de versions differentes parlent au
    meme serveur adb, chacun le redemarre et coupe les connexions des autres.
    """
    if environ.get("KOTCM_ADB"):
        return environ["KOTCM_ADB"]
    for variable in ("ANDROID_SDK_ROOT", "ANDROID_HOME"):
        if environ.get(variable):
            candidat = os.path.join(environ[variable], "platform-tools", "adb.exe")
            if existe(candidat):
                return candidat
    trouve = which("adb")
    if trouve:
        return trouve
    for chemin in ADB_STANDARD:
        if existe(chemin):
            return chemin
    dossier = memu()
    if dossier:
        candidat = os.path.join(dossier, "MEmu", "adb.exe")
        if existe(candidat):
            return candidat
    raise ErreurLive("live_adb_absent")


def parse_appareils(sortie: str) -> list[str]:
    """Les serials en etat `device` dans la sortie de `adb devices`."""
    serials = []
    for ligne in sortie.splitlines()[1:]:
        champs = ligne.split()
        if len(champs) >= 2 and champs[1] == "device":
            serials.append(champs[0])
    return serials


def seul_appareil(appareils: list[str]) -> str:
    if len(appareils) == 1:
        return appareils[0]
    raise ErreurLive("live_appareil", appareils=", ".join(appareils) or "-")


def parse_version(dumpsys: str) -> tuple[str, int] | None:
    nom = re.search(r"\bversionName=(\S+)", dumpsys)
    code = re.search(r"\bversionCode=(\d+)", dumpsys)
    return (nom.group(1), int(code.group(1))) if nom and code else None


def parse_pid(sortie: str) -> int | None:
    champs = sortie.split()
    return int(champs[0]) if champs and champs[0].isdigit() else None


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

    def verifier_version(self) -> None:
        v = parse_version(self.shell("dumpsys package " + PAQUET))
        if v != VERSION:
            raise ErreurLive("live_version", trouvee=("%s (%d)" % v) if v else "?")

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
