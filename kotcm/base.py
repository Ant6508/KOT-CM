# -*- coding: utf-8 -*-
"""Une base : un `Dungeon` protobuf et les operations de l'editeur.

La base enveloppe le Dungeon au lieu de le traduire : tous les champs, meme
ceux dont on ignore le sens, sont gardes, d'ou l'aller-retour a l'octet pres.
Invariants : exactement une porte et un totem ; identifiants 0, 1, 2... dans
l'ordre de la liste (porte 0, totem 1), gemmes en fin de liste.
"""

from __future__ import annotations

import copy
from dataclasses import fields

from kotcm.catalogue import GEMMES, PORTE, TOTEM
from kotcm.corpus import Forme
from kotcm.modeles import Modeles
from kotcm.protobuf import Donjon, Obstacle
from kotcm.regles import BLOODHOUND, SUPPORTS

# Positions par defaut du mod de l'ami (TrObjectInfo::CreateTrObjectsByIDs), aimantees ensuite.
DEFAUT_PORTE, DEFAUT_TOTEM = (64, 64), (64, 192)
DEFAUT_STRUCTURE_X, DEFAUT_STRUCTURE_Y = 64, 256
PLATEFORME, TRAMPOLINE, ANTIGRAVITE = 11, 12, 7
CHAMPS_MODIFIABLES = {f.name for f in fields(Obstacle)} - {"ident"}


class Base:
    def __init__(self, donjon: Donjon, modeles: Modeles):
        self.donjon = donjon
        self.modeles = modeles

    # --- creation, lecture, ecriture ---------------------------------------

    @classmethod
    def nouvelle(cls, forme: Forme, modeles: Modeles) -> "Base":
        """La forme, la porte, le totem et les objets de structure aux positions par defaut du mod."""
        base = cls(Donjon(grille=forme.grille, **modeles.donjon), modeles)
        base._ajouter(PORTE, *DEFAUT_PORTE)
        base._ajouter(TOTEM, *DEFAUT_TOTEM)
        y = DEFAUT_STRUCTURE_Y
        for numero, nombre in ((PLATEFORME, forme.plateformes), (TRAMPOLINE, forme.trampolines),
                               (ANTIGRAVITE, forme.antigravites)):
            for _ in range(nombre):
                base._ajouter(numero, DEFAUT_STRUCTURE_X, y)
                y += 64
        return base

    @classmethod
    def depuis_octets(cls, octets: bytes, modeles: Modeles) -> "Base":
        return cls(Donjon.depuis_octets(octets), modeles)

    def octets(self) -> bytes:
        return self.donjon.octets()

    def copie(self) -> "Base":
        return Base(copy.deepcopy(self.donjon), self.modeles)

    # --- objets ----------------------------------------------------------------

    def obstacle(self, ident: int) -> Obstacle:
        for o in self.donjon.obstacles:
            if o.ident == ident:
                return o
        raise KeyError("aucun objet d'identifiant %d" % ident)

    def poser(self, numero: int, x: int, y: int) -> int:
        """Pose un objet de ce type (modele recopie, position aimantee) ; rend son identifiant."""
        if numero in (PORTE, TOTEM):
            raise ValueError("la porte et le totem existent deja : on les deplace")
        return self._ajouter(numero, x, y)

    def modifier(self, ident: int, **champs) -> None:
        """Change des champs d'un objet (type, x, y, orientation, vx, vy, f6...). Pas d'aimantation."""
        inconnus = set(champs) - CHAMPS_MODIFIABLES
        if inconnus:
            raise ValueError("champs non modifiables : %s" % ", ".join(sorted(inconnus)))
        o = self.obstacle(ident)
        nouveau = champs.get("type", o.type)
        if nouveau != o.type and (o.type in (PORTE, TOTEM) or nouveau in (PORTE, TOTEM)):
            raise ValueError("la porte et le totem ne changent pas de type, et rien ne le devient")
        orientation = champs.get("orientation")
        if nouveau == BLOODHOUND and orientation is not None and orientation not in SUPPORTS:
            raise ValueError("l'orientation d'un bloodhound va de 0 a 3 (saisie : %d)" % orientation)
        for nom, valeur in champs.items():
            setattr(o, nom, valeur)

    def retirer(self, ident: int) -> None:
        o = self.obstacle(ident)
        if o.type in (PORTE, TOTEM):
            raise ValueError("la porte et le totem ne se retirent pas")
        self.donjon.obstacles.remove(o)
        self._renumeroter()

    # --- interne ---------------------------------------------------------------

    def _ajouter(self, numero: int, x: int, y: int) -> int:
        x, y = self.modeles.aimanter(numero, x, y)
        o = Obstacle(type=numero, x=x, y=y, ident=0, **self.modeles.champs(numero))
        liste = self.donjon.obstacles
        rang = next((i for i, g in enumerate(liste) if g.type in GEMMES), len(liste))
        liste.insert(rang, o)
        self._renumeroter()
        return o.ident

    def _renumeroter(self) -> None:
        for i, o in enumerate(self.donjon.obstacles):
            o.ident = i
