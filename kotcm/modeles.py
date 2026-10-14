# -*- coding: utf-8 -*-
"""Modeles d'obstacles par type et pas d'aimantation : modeles.json (outils/extraire_modeles.py).

Poser un objet recopie le modele de son type : les champs que l'on ne
comprend pas (f6, f15...) prennent la valeur que le jeu leur donne le plus
souvent. Un type jamais capture prend le modele par defaut des pieges : il
est alors "suppose".
"""

from __future__ import annotations

import json
from pathlib import Path

MODELES = Path(__file__).resolve().parent / "modeles.json"
CARREAU = 64
LARGEUR_PX, HAUTEUR_PX = 896, 512
AIMANT_DEFAUT = (32, 32)        # centre d'un carreau, celui de tous les pieges captures


def aimanter(valeur: int, decalage: int, maxi: int) -> int:
    """La valeur `decalage + 64 k` la plus proche, bornee a [decalage, maxi[."""
    k = (valeur - decalage + CARREAU // 2) // CARREAU
    haut = decalage + CARREAU * ((maxi - 1 - decalage) // CARREAU)
    return min(max(decalage + CARREAU * k, decalage), haut)


class Modeles:
    def __init__(self, chemin: Path = MODELES):
        donnees = json.loads(Path(chemin).read_text(encoding="utf-8"))
        self._types = {int(n): m for n, m in donnees["types"].items()}
        self._defaut = donnees["defaut_piege"]
        self.donjon: dict = donnees["donjon"]

    def est_mesure(self, numero: int) -> bool:
        return numero in self._types

    def champs(self, numero: int) -> dict:
        """Les champs d'un nouvel objet de ce type (hors type, x, y, ident)."""
        return dict(self._types[numero]["champs"] if numero in self._types else self._defaut)

    def aimant(self, numero: int) -> tuple[int, int] | None:
        """(x mod 64, y mod 64) des positions de ce type, ou None : placement libre."""
        if numero not in self._types:
            return AIMANT_DEFAUT
        a = self._types[numero]["aimant"]
        return tuple(a) if a else None

    def aimanter(self, numero: int, x: int, y: int) -> tuple[int, int]:
        a = self.aimant(numero)
        if a is None:
            return x, y
        return aimanter(x, a[0], LARGEUR_PX), aimanter(y, a[1], HAUTEUR_PX)
