# -*- coding: utf-8 -*-
"""Agents JS et attache Frida (methodes/frida.md).

`charger_agent(source, table)` place devant le JS un prélude `var ADR = {nom: 0x…};` avec les
seules adresses que l'agent cite (`ADR.nom`), et refuse au chargement un nom absent de la
table, au lieu d'un hook posé à une mauvaise adresse. `attacher` s'attache par pid : le nom
du processus est tronqué par ART. frida est celui du venv hôte, importé ici seulement.
"""

from __future__ import annotations

import re

from kotnoyau.adb import Adb, ErreurAdb
from kotnoyau.table import Table

ADR = re.compile(r"\bADR\.([A-Za-z_]\w*)")


class AdresseInconnue(Exception):
    pass


def noms_utilises(source: str) -> list[str]:
    return sorted(set(ADR.findall(source)))


def charger_agent(source: str, table: Table) -> str:
    noms = noms_utilises(source)
    manquants = [n for n in noms if n not in table.entrees]
    if manquants:
        raise AdresseInconnue("adresses absentes de la table %d (%s) : %s" % (table.code, table.nom, ", ".join(manquants)))
    return "var ADR = {%s};\n" % ", ".join("%s: 0x%x" % (n, table.adresse(n)) for n in noms) + source


def attacher(adb: Adb, pid: int | None = None, frida_module=None):
    """Session frida sur le jeu, par pid (celui du jeu par défaut)."""
    if frida_module is None:
        import frida as frida_module
    if pid is None:
        pid = adb.pid_jeu()
        if pid is None:
            raise ErreurAdb("le jeu ne tourne pas sur %s" % adb.serial)
    return frida_module.get_device(adb.serial, timeout=10).attach(pid)
