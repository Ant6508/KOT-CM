# -*- coding: utf-8 -*-
"""La garde de version commune : la table d'adresses du jeu installé, ou un refus avant toute attache.

Remplace, au fil des migrations, les VERSION_ATTENDUE / EXPECTED_VERSION_* / VERSION_CODE
des dépôts (liste : docs/savoir/versions.md, check-list, étape 5).
"""

from __future__ import annotations

from pathlib import Path

from kotnoyau.adb import Adb, ErreurAdb
from kotnoyau.table import TABLES, Table


def garde(adb: Adb, dossier: Path = TABLES) -> Table:
    version = adb.version()
    if version is None:
        raise ErreurAdb("King of Thieves n'est pas installé sur %s" % adb.serial)
    nom, code = version
    return Table.pour(code, nom, dossier)
