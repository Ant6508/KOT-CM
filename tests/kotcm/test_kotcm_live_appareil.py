import hashlib
import http.client
import lzma
import os
import subprocess
import sys

import pytest

from kotcm.live import ErreurLive
from kotcm.live.appareil import (ADB_STANDARD, NOM_SERVEUR, SERVEUR, SHA256_SERVEUR, URL_SERVEUR, Appareil,
                                 chemin_adb, copie_locale, dossier_memu, parse_appareils, parse_pid,
                                 parse_serveurs, parse_version, seul_appareil)

EMPREINTE_ELF = hashlib.sha256(b"ELF").hexdigest()      # le faux frida-server des tests

PS_RIEN = "  PID ARGS\n    1 /init\n  812 com.zeptolab.thieves.google\n"
PS_NOTRE = PS_RIEN + " 9001 /data/local/tmp/frida-server-17.19.0 -D\n"
PS_TAS = PS_RIEN + " 7001 /data/local/tmp/frida-server -D\n"


class FauxAdb:
    """Rend la sortie prevue pour chaque commande ; une liste se consomme appel apres appel."""

    def __init__(self, reponses):
        self.reponses = reponses
        self.commandes = []

    def __call__(self, commande, **_):
        args = commande[3:] if commande[1] == "-s" else commande[1:]
        cle = " ".join(args)
        self.commandes.append(cle)
        for motif, sortie in self.reponses.items():
            if cle.startswith(motif):
                if isinstance(sortie, list):
                    sortie = sortie.pop(0) if len(sortie) > 1 else sortie[0]
                return subprocess.CompletedProcess(commande, 0, sortie, "")
        return subprocess.CompletedProcess(commande, 1, "", "commande inattendue")


def appareil(reponses, serial="127.0.0.1:5555"):
    # Jamais le vrai ~/.kotcm ni le reseau : une poussee inattendue echoue tout de suite.
    adb = FauxAdb(reponses)
    return Appareil(serial, environ={"KOTCM_ADB": "adb", "KOTCM_DOSSIER": "dossier-de-test-inexistant"},
                    executer=adb, attendre=lambda s: None,
                    telecharger=lambda url: pytest.fail("telechargement inattendu")), adb


def test_chemin_adb():
    sans_memu = dict(memu=lambda: None)
    assert chemin_adb({"KOTCM_ADB": "x/adb"}, **sans_memu) == "x/adb"
    assert chemin_adb({}, which=lambda n: "p/adb", **sans_memu) == "p/adb"
    assert chemin_adb({}, which=lambda n: None, existe=lambda c: c in ADB_STANDARD, **sans_memu) == ADB_STANDARD[0]
    with pytest.raises(ErreurLive) as e:
        chemin_adb({}, which=lambda n: None, existe=lambda c: False, **sans_memu)
    assert e.value.cle == "live_adb_absent"


def test_chemin_adb_du_sdk_puis_de_memu():
    sdk = os.path.join("S", "platform-tools", "adb.exe")
    memu = os.path.join("M", "MEmu", "adb.exe")
    assert chemin_adb({"ANDROID_SDK_ROOT": "S"}, which=lambda n: "p/adb", existe=lambda c: True) == sdk
    assert chemin_adb({"ANDROID_HOME": "S"}, which=lambda n: "p/adb", existe=lambda c: True) == sdk
    # SDK declare mais sans adb : on passe au suivant.
    assert chemin_adb({"ANDROID_HOME": "S"}, which=lambda n: "p/adb", existe=lambda c: False) == "p/adb"
    # Poste neuf : ni SDK ni adb dans le PATH, l'adb livre avec MEmu (dossier lu dans le registre).
    assert chemin_adb({}, which=lambda n: None, existe=lambda c: c == memu, memu=lambda: "M") == memu
    # Le SDK a sa place standard passe avant MEmu : un seul adb pour tout l'outillage.
    assert chemin_adb({}, which=lambda n: None, existe=lambda c: True, memu=lambda: "M") == ADB_STANDARD[0]


def test_dossier_memu_sans_winreg(monkeypatch):
    monkeypatch.setitem(sys.modules, "winreg", None)          # import winreg -> ImportError, comme hors Windows
    assert dossier_memu() is None


def test_choix_de_l_appareil():
    sortie = "List of devices attached\n127.0.0.1:21503\tdevice\nemulator-5554\toffline\n\n"
    assert parse_appareils(sortie) == ["127.0.0.1:21503"]
    assert seul_appareil(["c"]) == "c"
    with pytest.raises(ErreurLive) as e:
        seul_appareil(["c", "d"])
    assert (e.value.cle, e.value.valeurs) == ("live_appareil", {"appareils": "c, d"})


def test_lectures():
    assert parse_version("  versionCode=4755781 minSdk=21\n  versionName=2.84\n") == ("2.84", 4755781)
    assert parse_version("rien") is None
    assert parse_pid("812\n") == 812 and parse_pid("") is None
    assert parse_serveurs(PS_NOTRE) == (True, [])
    assert parse_serveurs(PS_TAS) == (False, ["frida-server"])


def test_serial_demande_puis_android_serial_puis_seul_appareil():
    devices = FauxAdb({"devices": "List of devices attached\nemulator-5554\tdevice\n"})
    assert Appareil("a", environ={"ANDROID_SERIAL": "b"}, executer=FauxAdb({})).serial == "a"
    assert Appareil(environ={"ANDROID_SERIAL": "b"}, executer=FauxAdb({})).serial == "b"
    assert Appareil(environ={"KOTCM_ADB": "adb"}, executer=devices).serial == "emulator-5554"


def test_garde_de_version():
    a, _ = appareil({"shell dumpsys": "versionCode=4755781\nversionName=2.84\n"})
    assert a.verifier_version().adresse("vt_dungeon_storage") == 0x1fb1170
    a, _ = appareil({"shell dumpsys": "versionCode=4800000\nversionName=2.85\n"})
    with pytest.raises(ErreurLive) as e:
        a.verifier_version()
    assert (e.value.cle, e.value.valeurs) == ("live_version", {"trouvee": "2.85 (4800000)",
                                                               "connues": "2.84 (4755781)"})


def test_les_lectures_viennent_du_noyau():
    import kotnoyau.adb as noyau
    from kotcm.live import appareil as module

    for nom in ("parse_appareils", "parse_version", "parse_pid", "dossier_memu"):
        assert getattr(module, nom) is getattr(noyau, nom)
    assert module.PAQUET == noyau.PAQUET and module.ADB_STANDARD == noyau.ADB_STANDARD


def test_jeu_absent():
    a, _ = appareil({"shell pidof": ""})
    with pytest.raises(ErreurLive) as e:
        a.pid_jeu()
    assert e.value.cle == "live_jeu_absent"


def test_serveur_deja_lance():
    a, adb = appareil({"shell ps": PS_NOTRE})
    a.preparer_serveur()
    assert adb.commandes == ["shell ps -A -o PID,ARGS"]


def test_serveur_lance_s_il_ne_tourne_pas():
    a, adb = appareil({"shell ps": [PS_RIEN, PS_RIEN, PS_NOTRE], "shell sha256sum": SHA256_SERVEUR + "  " + SERVEUR,
                       "shell chmod": "", "shell nohup": ""})
    a.preparer_serveur()
    assert not any(c.startswith("push") for c in adb.commandes)               # le bon fichier est deja la
    assert adb.commandes[2:4] == ["shell chmod 755 " + SERVEUR,
                                  "shell nohup %s -D </dev/null >/dev/null 2>&1 &" % SERVEUR]


def test_refus_si_un_autre_serveur_tourne():
    a, adb = appareil({"shell ps": PS_TAS})
    with pytest.raises(ErreurLive) as e:
        a.preparer_serveur()
    assert (e.value.cle, e.value.valeurs) == ("live_autre_serveur", {"serveurs": "frida-server"})
    assert not any(c.startswith("shell nohup") for c in adb.commandes)


@pytest.mark.parametrize("sur_l_appareil", ["absent\n", "0123abcd  " + SERVEUR])   # absent, ou pas le bon
def test_serveur_absent_ou_abime_pousse_depuis_la_copie_locale_puis_lance(tmp_path, sur_l_appareil):
    local = tmp_path / "frida-server" / NOM_SERVEUR
    local.parent.mkdir()
    local.write_bytes(b"ELF")
    adb = FauxAdb({"shell ps": [PS_RIEN, PS_NOTRE], "shell sha256sum": sur_l_appareil, "push": "",
                   "shell chmod": "", "shell nohup": ""})
    a = Appareil("127.0.0.1:5555", environ={"KOTCM_ADB": "adb", "KOTCM_DOSSIER": str(tmp_path)}, executer=adb,
                 attendre=lambda s: None, telecharger=lambda url: pytest.fail("copie locale presente"),
                 empreinte=EMPREINTE_ELF)
    a.preparer_serveur()
    assert adb.commandes[1] == "shell sha256sum %s 2>/dev/null || echo absent" % SERVEUR
    assert adb.commandes[2:5] == ["push %s %s" % (local, SERVEUR), "shell chmod 755 " + SERVEUR,
                                  "shell nohup %s -D </dev/null >/dev/null 2>&1 &" % SERVEUR]


def test_copie_locale_telechargee_et_decompressee(tmp_path):
    urls = []

    def telecharger(url):
        urls.append(url)
        return lzma.compress(b"ELF")

    chemin = copie_locale(tmp_path, telecharger, EMPREINTE_ELF)
    assert chemin == tmp_path / "frida-server" / "frida-server-17.19.0-android-x86_64"
    assert chemin.read_bytes() == b"ELF"
    assert urls == ["https://github.com/frida/frida/releases/download/17.19.0/"
                    "frida-server-17.19.0-android-x86_64.xz"]
    assert [p.name for p in chemin.parent.iterdir()] == [chemin.name]          # pas de .part qui traine
    assert copie_locale(tmp_path, lambda url: pytest.fail("deja la"), EMPREINTE_ELF) == chemin


def test_copie_locale_d_une_autre_empreinte_remplacee(tmp_path):
    # Un fichier mal choisi a la main (autre architecture, page HTML, archive non decompressee).
    chemin = tmp_path / "frida-server" / NOM_SERVEUR
    chemin.parent.mkdir()
    chemin.write_bytes(b"<html>")
    assert copie_locale(tmp_path, lambda url: lzma.compress(b"ELF"), EMPREINTE_ELF).read_bytes() == b"ELF"


@pytest.mark.parametrize("panne", [OSError("pas de reseau"), http.client.IncompleteRead(b""), b"pas du xz",
                                   lzma.compress(b"une autre version")])
def test_telechargement_impossible(tmp_path, panne):
    def telecharger(url):
        if isinstance(panne, Exception):
            raise panne
        return panne

    with pytest.raises(ErreurLive) as e:
        copie_locale(tmp_path, telecharger, EMPREINTE_ELF)
    assert e.value.cle == "live_telechargement"
    assert e.value.valeurs["url"] == URL_SERVEUR
    assert e.value.valeurs["chemin"] == str(tmp_path / "frida-server" / NOM_SERVEUR)
    assert not (tmp_path / "frida-server").exists()


def test_dossier_a_la_place_du_fichier(tmp_path):
    # L'extraction de 7-Zip cree un dossier a ce nom : message clair, sans telechargement inutile.
    chemin = tmp_path / "frida-server" / NOM_SERVEUR
    chemin.mkdir(parents=True)
    with pytest.raises(ErreurLive) as e:
        copie_locale(tmp_path, lambda url: pytest.fail("telechargement inutile"), EMPREINTE_ELF)
    assert (e.value.cle, e.value.valeurs) == ("live_dossier_a_la_place", {"chemin": str(chemin)})


def test_ecriture_impossible(tmp_path):
    # Le .part ne peut pas s'ecrire (ici un dossier a sa place ; ailleurs disque plein) : message, pas de copie.
    chemin = tmp_path / "frida-server" / NOM_SERVEUR
    (tmp_path / "frida-server" / (NOM_SERVEUR + ".part")).mkdir(parents=True)
    with pytest.raises(ErreurLive) as e:
        copie_locale(tmp_path, lambda url: lzma.compress(b"ELF"), EMPREINTE_ELF)
    assert e.value.cle == "live_telechargement"
    assert not chemin.exists()


def test_copie_locale_illisible_retelechargee(tmp_path, monkeypatch):
    chemin = tmp_path / "frida-server" / NOM_SERVEUR
    chemin.parent.mkdir()
    chemin.write_bytes(b"ELF")

    def illisible(self):
        raise PermissionError("verrouille")

    monkeypatch.setattr(type(chemin), "read_bytes", illisible)
    assert copie_locale(tmp_path, lambda url: lzma.compress(b"ELF"), EMPREINTE_ELF) == chemin


def test_echec_d_adb():
    a, _ = appareil({})
    with pytest.raises(ErreurLive) as e:
        a.shell("pidof x")
    assert e.value.cle == "live_adb" and "commande inattendue" in e.value.valeurs["detail"]

