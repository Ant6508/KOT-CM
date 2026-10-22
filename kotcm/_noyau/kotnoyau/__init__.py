# -*- coding: utf-8 -*-
"""Noyau commun des outils KOT : table d'adresses de libthieves.so par version, garde de
version, adb, attache Frida (spec docs/superpowers/specs/2026-10-21-noyau-design.md).

Aucune dépendance : frida est celui du venv hôte (le TAS reste en 17.18), importé
seulement par `frida_.attacher`.
"""

import sys


def sortie_utf8() -> None:
    """Les CLI écrivent en UTF-8 même dans une console Windows en cp1252."""
    for flux in (sys.stdout, sys.stderr):
        if hasattr(flux, "reconfigure"):
            flux.reconfigure(encoding="utf-8", errors="replace")
