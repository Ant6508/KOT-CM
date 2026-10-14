# -*- coding: utf-8 -*-
"""Phase 2 : charger une base de la fenetre dans l'editeur du jeu (spec, section 9).

Rien ici n'importe frida a l'import : la fenetre s'ouvre sans lui, et le
chargement dit alors comment l'installer.
"""

import os
from pathlib import Path


def dossier_donnees(environ=os.environ) -> Path:
    """Sauvegardes, live.json, copie de frida-server : ~/.kotcm, ou le dossier de KOTCM_DOSSIER."""
    return Path(environ["KOTCM_DOSSIER"]) if environ.get("KOTCM_DOSSIER") else Path.home() / ".kotcm"


class ErreurLive(Exception):
    """Un refus ou un echec du chargement live. `cle` est une cle de textes.py."""

    def __init__(self, cle: str, **valeurs):
        super().__init__(cle, valeurs)
        self.cle = cle
        self.valeurs = valeurs
