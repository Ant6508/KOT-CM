# -*- coding: utf-8 -*-
"""Le corpus des formes de base : formes.json (genere par outils/extraire_corpus.py).

Une forme = une grille de blocs et les objets de structure fournis avec elle
(plateformes, trampolines, anti-gravites). Aucune forme ne porte de pieges.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

FORMES = Path(__file__).resolve().parent / "formes.json"


@dataclass(frozen=True)
class Forme:
    origine: str            # "commune" ou "moddee"
    numero: int
    grille: int
    auteur: str | None
    plateformes: int
    trampolines: int
    antigravites: int


class Corpus:
    def __init__(self, chemin: Path = FORMES):
        donnees = json.loads(Path(chemin).read_text(encoding="utf-8"))
        self.credits: str = donnees["credits"]
        self.formes: list[Forme] = [Forme(**f) for f in donnees["formes"]]
        self._par_grille = {f.grille: f for f in self.formes}

    def par_grille(self, grille: int | None) -> Forme | None:
        """La forme de cette grille, ou None (grille absente ou nulle)."""
        return self._par_grille.get(grille) if grille else None

    def forme(self, origine: str, numero: int) -> Forme:
        for f in self.formes:
            if (f.origine, f.numero) == (origine, numero):
                return f
        raise KeyError("forme %s n %d absente du corpus" % (origine, numero))
