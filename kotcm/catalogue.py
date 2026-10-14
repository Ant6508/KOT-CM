# -*- coding: utf-8 -*-
"""Catalogue des types d'objet : numero (champ 1 du protobuf), dessin, posable, regles connues.

Les noms et abreviations affiches sont dans textes.py (cles `type_<n>` et
`abrev_<n>`). Numeros et noms repris du mod de l'ami (ListOfTrapsAndObjects.cpp),
gemmes 17 et 18 identifiees dans kot_headless (NOTES.md, 2026-09-30).
"""

from __future__ import annotations

from dataclasses import dataclass

PORTE, TOTEM = 1, 2
GEMMES = (17, 18)


@dataclass(frozen=True)
class Type:
    numero: int
    couleur: str
    posable: bool = True            # propose dans la palette
    regles_connues: bool = False    # regles propres relevees dans l'editeur (spec 2026-10-09)
    case: bool = False              # dessine sur 2 x 2 carreaux (porte, totem)


TYPES = {t.numero: t for t in (
    Type(1, "#2e7d32", posable=False, regles_connues=True, case=True),   # porte
    Type(2, "#c9a400", posable=False, regles_connues=True, case=True),   # totem
    Type(3, "#8a6a3c"),                                                  # bloc
    Type(4, "#455a64"),                                                  # canon
    Type(6, "#263238"),                                                  # canon chercheur
    Type(7, "#00838f"),                                                  # anti-gravite
    Type(8, "#c62828", regles_connues=True),                             # scie
    Type(9, "#b71c1c"),                                                  # garde rouge
    Type(10, "#1565c0", regles_connues=True),                            # garde bleu
    Type(11, "#6d4c41"),                                                 # plateforme
    Type(12, "#ef6c00"),                                                 # trampoline
    Type(13, "#8d6e63"),                                                 # plateforme cassable
    Type(14, "#5e35b1"),                                                 # oiseau chercheur
    Type(17, "#f9a825", posable=False),                                  # gemme
    Type(18, "#fbc02d", posable=False),                                  # gemme
    Type(21, "#00695c"),                                                 # ricochet
    Type(39, "#d84315"),                                                 # dragon
    Type(40, "#bf360c"),                                                 # fourneau
    Type(41, "#ad1457"),                                                 # scie aleatoire
    Type(42, "#4527a0"),                                                 # warder
    Type(44, "#6a1b9a", regles_connues=True),                            # bloodhound
    Type(45, "#ec407a"),                                                 # bonbon
    Type(46, "#0277bd"),                                                 # canon electrique
    Type(47, "#37474f"),                                                 # araignee
    Type(48, "#558b2f"),                                                 # hopblob
)}

INCONNU = Type(0, "#9e9e9e", posable=False)


def type_de(numero: int) -> Type:
    """Le type de ce numero, ou INCONNU (numero absent de la table)."""
    return TYPES.get(numero, INCONNU)


def posables() -> list[int]:
    return [n for n, t in TYPES.items() if t.posable]
