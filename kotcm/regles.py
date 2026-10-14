# -*- coding: utf-8 -*-
"""Regles de placement de l'editeur : le code d'erreur de chaque objet, signale sans bloquer.

Recopie et etendu de `controller/placements.py` (kot_headless, spec
2026-10-09-regles-placement : 123 792 cas sans desaccord avec l'editeur).

Repere : cadre de 14 x 8 carreaux de 64 px ; carreau d'un objet =
((x + 1) // 64, (y + 1) // 64) ; porte et totem sur 2 x 2 carreaux depuis
leur carreau moins (1, 1).

Codes (un par objet, dans cet ordre de priorite) :
  3 sans paroi           bloodhound : ni sa case de 128 px ni le carreau voisin
                         du cote de son orientation n'est un bloc, ou son
                         orientation n'est pas de 0 a 3 ;
  2 trop pres de porte   carreau dans les 2 x 2 de la porte elargis d'un carreau,
                         ou (garde bleu) dans ses carreaux en plus ;
  1 sur le totem         carreau dans les 2 x 2 du totem ;
  0 valide.
Porte et totem : 4 si un de leurs 2 x 2 carreaux est un bloc ou sort du cadre.

Types dont les regles propres sont connues : porte, totem, scie, garde bleu,
bloodhound (verdict "verifie"). Pour les autres, seules les regles communes
(codes 2 sans liste propre, et 1) sont appliquees : verdict "non verifie".
Les gemmes (17, 18) n'ont pas de verdict.
"""

from __future__ import annotations

from dataclasses import dataclass

from kotcm.catalogue import GEMMES, PORTE, TOTEM, type_de
from kotcm.protobuf import LARGEUR, Donjon, Obstacle

CARREAU = 64
COLONNES, RANGEES = 14, 8
GARDE_BLEU, BLOODHOUND = 10, 44
# Bloodhound : orientation -> carreau (colonne, rangee) de la paroi qui le porte.
SUPPORTS = {0: (-1, 0), 1: (0, -1), 2: (1, 0), 3: (0, 1)}
# Carreaux en plus, depuis la base de la porte, trop pres d'elle pour un piege.
PROCHES_PORTE = {GARDE_BLEU: ((0, 3), (1, 3))}


@dataclass(frozen=True)
class Verdict:
    code: int
    verifie: bool


def carreau(o: Obstacle) -> tuple[int, int]:
    return (o.x + 1) // CARREAU, (o.y + 1) // CARREAU


def base_2x2(o: Obstacle) -> tuple[int, int]:
    """Premier des 2 x 2 carreaux de la porte ou du totem."""
    c, r = carreau(o)
    return c - 1, r - 1


def dans_cadre(c: int, r: int) -> bool:
    return 0 <= c < COLONNES and 0 <= r < RANGEES


def plein(grille: int, c: int, r: int) -> bool:
    """Le carreau (c, r) est-il dans un bloc ? Hors du cadre : oui, le bord est une paroi."""
    if not dans_cadre(c, r):
        return True
    return bool(grille >> ((r // 2) * LARGEUR + c // 2) & 1)


def zone_porte(porte: Obstacle) -> tuple[int, int, int, int]:
    """(colonne, rangee, largeur, hauteur) en carreaux des 4 x 4 carreaux interdits autour de la porte."""
    pc, pr = base_2x2(porte)
    return pc - 1, pr - 1, 4, 4


def zone_totem(totem: Obstacle) -> tuple[int, int, int, int]:
    tc, tr = base_2x2(totem)
    return tc, tr, 2, 2


def _code_piege(o: Obstacle, grille: int, porte: Obstacle | None, totem: Obstacle | None) -> int:
    c, r = carreau(o)
    if o.type == BLOODHOUND:
        if (o.orientation or 0) not in SUPPORTS:
            return 3
        dc, dr = SUPPORTS[o.orientation or 0]
        if not (plein(grille, c, r) or plein(grille, c + dc, r + dr)):
            return 3
    if porte is not None:
        zc, zr, zl, zh = zone_porte(porte)
        if zc <= c < zc + zl and zr <= r < zr + zh:
            return 2
        pc, pr = base_2x2(porte)
        if any((c, r) == (pc + dc, pr + dr) for dc, dr in PROCHES_PORTE.get(o.type, ())):
            return 2
    if totem is not None:
        zc, zr, zl, zh = zone_totem(totem)
        if zc <= c < zc + zl and zr <= r < zr + zh:
            return 1
    return 0


def _verdict(o: Obstacle, grille: int, porte: Obstacle | None, totem: Obstacle | None) -> Verdict:
    if o.type in (PORTE, TOTEM):
        c, r = base_2x2(o)
        code = 4 if any(plein(grille, c + i, r + j) for i in (0, 1) for j in (0, 1)) else 0
        return Verdict(code, True)
    return Verdict(_code_piege(o, grille, porte, totem), type_de(o.type).regles_connues)


def verdicts(donjon: Donjon) -> dict[int, Verdict]:
    """{ident: Verdict} de chaque objet hors gemmes. Une regle qui echoue rend un verdict non verifie."""
    objets = [o for o in donjon.obstacles if o.type not in GEMMES]
    grille = donjon.grille or 0
    porte = next((o for o in objets if o.type == PORTE), None)
    totem = next((o for o in objets if o.type == TOTEM), None)
    out = {}
    for o in objets:
        try:
            out[o.ident] = _verdict(o, grille, porte, totem)
        except Exception:       # noqa: BLE001 -- signaler sans bloquer (spec, section 8)
            out[o.ident] = Verdict(0, False)
    return out
