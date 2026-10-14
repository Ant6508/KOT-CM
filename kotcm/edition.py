# -*- coding: utf-8 -*-
"""L'etat de la fenetre, sans tkinter : base ouverte, selection, annulation, enregistrement.

La fenetre (fenetre.py) ne fait que dessiner cet etat et lui transmettre les
gestes : tout ce qui se teste se teste ici.

Enregistrement : la fenetre n'ecrase jamais un fichier qu'elle a ouvert. Le
premier enregistrement d'une base ouverte propose `<nom>_kotcm.bin` (ou
`<nom>_kotcm_2.bin`... s'il existe) ; les suivants vont dans le fichier choisi.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from kotcm.base import Base
from kotcm.corpus import Corpus, Forme
from kotcm.modeles import Modeles
from kotcm.regles import Verdict, verdicts


class ErreurLecture(Exception):
    """Le fichier n'est pas un donjon lisible."""


@dataclass(frozen=True)
class Resume:
    objets: int
    problemes: int
    non_verifies: int


def chemin_libre(chemin: str, existe=os.path.exists) -> str:
    """`chemin` s'il n'existe pas, sinon `<racine>_2<ext>`, `<racine>_3<ext>`..."""
    if not existe(chemin):
        return chemin
    racine, ext = os.path.splitext(chemin)
    n = 2
    while existe("%s_%d%s" % (racine, n, ext)):
        n += 1
    return "%s_%d%s" % (racine, n, ext)


class Edition:
    def __init__(self, corpus: Corpus, modeles: Modeles):
        self.corpus = corpus
        self.modeles = modeles
        self.base: Base | None = None
        self.chemin_ouvert: str | None = None      # fichier lu : jamais ecrase
        self.chemin_sortie: str | None = None      # fichier choisi au premier enregistrement
        self.modifiee = False
        self.selection: int | None = None
        self.libre = False
        self._pile: list[Base] = []

    # --- ouvrir, creer, enregistrer -----------------------------------------------

    def nouvelle(self, forme: Forme) -> None:
        self._remplacer(Base.nouvelle(forme, self.modeles), None)

    def ouvrir(self, chemin: str) -> None:
        try:
            with open(chemin, "rb") as f:
                base = Base.depuis_octets(f.read(), self.modeles)
        except (OSError, ValueError, TypeError, IndexError) as e:
            raise ErreurLecture("%s : %s" % (os.path.basename(chemin), e)) from e
        self._remplacer(base, chemin)

    def suggestion(self, existe=os.path.exists) -> str | None:
        """Le fichier propose au premier enregistrement d'une base ouverte ; None pour une base nouvelle."""
        if self.chemin_sortie:
            return self.chemin_sortie
        if self.chemin_ouvert is None:
            return None
        racine, ext = os.path.splitext(self.chemin_ouvert)
        return chemin_libre("%s_kotcm%s" % (racine, ext or ".bin"), existe)

    def enregistrer(self, chemin: str) -> None:
        if self.chemin_ouvert and os.path.abspath(chemin) == os.path.abspath(self.chemin_ouvert):
            raise ValueError("refus d'ecraser le fichier ouvert %s" % self.chemin_ouvert)
        with open(chemin, "wb") as f:
            f.write(self.base.octets())
        self.chemin_sortie = chemin
        self.modifiee = False

    # --- gestes ------------------------------------------------------------------

    def selectionner(self, ident: int | None) -> None:
        self.selection = ident

    def poser(self, numero: int, x: int, y: int) -> int:
        self._empiler()
        if self.libre:
            ident = self.base.poser(numero, 0, 0)
            self.base.modifier(ident, x=x, y=y)
        else:
            ident = self.base.poser(numero, x, y)
        self.selection = ident
        return ident

    def deplacer(self, ident: int, x: int, y: int) -> None:
        """Glisser : position aimantee au pas du type, sauf en placement libre."""
        if not self.libre:
            x, y = self.modeles.aimanter(self.base.obstacle(ident).type, x, y)
        self.modifier(ident, x=x, y=y)

    def modifier(self, ident: int, **champs) -> None:
        """Saisie au clavier : valeurs prises telles quelles."""
        self._empiler()
        try:
            self.base.modifier(ident, **champs)
        except (KeyError, ValueError):
            self._pile.pop()
            raise

    def retirer(self, ident: int) -> None:
        self._empiler()
        try:
            self.base.retirer(ident)
        except (KeyError, ValueError):
            self._pile.pop()
            raise
        self.selection = None

    def annuler(self) -> bool:
        if not self._pile:
            return False
        self.base = self._pile.pop()
        self.modifiee = True
        if self.selection is not None and self.selection >= len(self.base.donjon.obstacles):
            self.selection = None
        return True

    # --- lecture -------------------------------------------------------------------

    def forme(self) -> Forme | None:
        return self.corpus.par_grille(self.base.donjon.grille) if self.base else None

    def verdicts(self) -> dict[int, Verdict]:
        return verdicts(self.base.donjon) if self.base else {}

    def resume(self) -> Resume:
        v = self.verdicts().values()
        return Resume(objets=len(self.base.donjon.obstacles) if self.base else 0,
                      problemes=sum(1 for x in v if x.code),
                      non_verifies=sum(1 for x in v if not x.verifie))

    # --- interne -----------------------------------------------------------------

    def _remplacer(self, base: Base, chemin: str | None) -> None:
        self.base, self.chemin_ouvert, self.chemin_sortie = base, chemin, None
        self.modifiee, self.selection, self._pile = chemin is None, None, []

    def _empiler(self) -> None:
        if self.base is None:
            raise ValueError("aucune base ouverte")
        self._pile.append(self.base.copie())
        self.modifiee = True
