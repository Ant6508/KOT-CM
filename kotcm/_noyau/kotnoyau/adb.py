# -*- coding: utf-8 -*-
"""adb pour tous les outils KOT : trouver adb, choisir l'appareil, shell, version du jeu, pid, frida-server.

Repris de kotcm/live/appareil.py (2026-10-14), dépendances injectées pour les tests sans
émulateur. adb : KOT_ADB, puis KOTCM_ADB, puis le SDK (ANDROID_SDK_ROOT, ANDROID_HOME), le
PATH, les emplacements standard, enfin le dossier de MEmu lu dans le registre ; le SDK passe
avant MEmu (deux adb de versions différentes se coupent leurs connexions, methodes/memu.md).
Appareil : celui demandé, puis KOT_SERIAL (TAS), puis ANDROID_SERIAL (kotcm), puis le seul
connecté ; avec plusieurs instances ouvertes, on refuse de deviner.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from dataclasses import dataclass

PAQUET = "com.zeptolab.thieves.google"
ADB_STANDARD = (
    os.path.join(os.environ.get("LOCALAPPDATA", ""), "Android", "Sdk", "platform-tools", "adb.exe"),
    r"C:\Program Files (x86)\Android\android-sdk\platform-tools\adb.exe",
)
CLE_MEMU = r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\MEmu"


class ErreurAdb(Exception):
    pass


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
    for variable in ("KOT_ADB", "KOTCM_ADB"):
        if environ.get(variable):
            return environ[variable]
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
    raise ErreurAdb("adb introuvable : poser KOT_ADB sur le chemin d'adb.exe")


def parse_appareils(sortie: str) -> list[str]:
    """Les serials en état `device` dans la sortie de `adb devices`."""
    serials = []
    for ligne in sortie.splitlines()[1:]:
        champs = ligne.split()
        if len(champs) >= 2 and champs[1] == "device":
            serials.append(champs[0])
    return serials


def parse_version(dumpsys: str) -> tuple[str, int] | None:
    nom = re.search(r"\bversionName=(\S+)", dumpsys)
    code = re.search(r"\bversionCode=(\d+)", dumpsys)
    return (nom.group(1), int(code.group(1))) if nom and code else None


def parse_pid(sortie: str) -> int | None:
    champs = sortie.split()
    return int(champs[0]) if champs and champs[0].isdigit() else None


@dataclass(frozen=True)
class ServeurFrida:
    pid: int
    chemin: str


def parse_serveurs(sortie: str) -> list[ServeurFrida]:
    """Les frida-server de la sortie de `ps -A -o PID,ARGS`, avec le chemin de leur binaire."""
    serveurs = []
    for ligne in sortie.splitlines()[1:]:
        champs = ligne.split()
        if len(champs) >= 2 and champs[0].isdigit() and champs[1].rsplit("/", 1)[-1].startswith("frida-server"):
            serveurs.append(ServeurFrida(int(champs[0]), champs[1]))
    return serveurs


class Adb:
    def __init__(self, serial: str | None = None, environ=os.environ, executer=subprocess.run):
        self._demande, self.environ, self.executer = serial, environ, executer
        self._adb: str | None = None
        self._serial: str | None = None

    def lancer(self, args: list[str], avec_serial: bool = True) -> str:
        if self._adb is None:
            self._adb = chemin_adb(self.environ)
        commande = [self._adb] + (["-s", self.serial] if avec_serial else []) + args
        # stdin fermé : `adb shell` transmettrait sinon notre entrée au shell Android.
        r = self.executer(commande, stdin=subprocess.DEVNULL, capture_output=True, text=True)
        if r.returncode != 0:
            raise ErreurAdb("adb %s : %s" % (" ".join(args), (r.stderr or "").strip()))
        return r.stdout

    def appareils(self) -> list[str]:
        return parse_appareils(self.lancer(["devices"], avec_serial=False))

    @property
    def serial(self) -> str:
        if self._serial is None:
            choisi = self._demande or self.environ.get("KOT_SERIAL") or self.environ.get("ANDROID_SERIAL")
            if not choisi:
                appareils = self.appareils()
                if not appareils:
                    raise ErreurAdb("aucun appareil adb : lancer MEmu")
                if len(appareils) > 1:
                    raise ErreurAdb("%d appareils connectés (%s) : préciser l'instance (--serial ou KOT_SERIAL)"
                                    % (len(appareils), ", ".join(appareils)))
                choisi = appareils[0]
            self._serial = choisi
        return self._serial

    def shell(self, commande: str) -> str:
        return self.lancer(["shell", commande])

    def version(self) -> tuple[str, int] | None:
        """(versionName, versionCode) du jeu installé, ou None."""
        return parse_version(self.shell("dumpsys package " + PAQUET))

    def pid_jeu(self) -> int | None:
        return parse_pid(self.shell("pidof " + PAQUET))

    def serveurs_frida(self) -> list[ServeurFrida]:
        return parse_serveurs(self.shell("ps -A -o PID,ARGS"))
