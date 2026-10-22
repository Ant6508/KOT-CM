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
                         ou (garde bleu) dans ses carreaux en plus ; zone etendue d'un carreau
                         a droite et en bas pour l'anti-gravite ;
  1 sur le totem         carreau dans les 2 x 2 du totem (etendus de meme pour l'anti-gravite) ;
  4 sur un bloc         porte, totem, ou emprise d'un piege (anti-gravite, depuis son carreau
                         moins (1, 1)) : un de ses carreaux
                         est un bloc ou sort du cadre (pour un piege, controle apres un code 0) ;
  0 valide.
Porte et totem : 4 si un de leurs 2 x 2 carreaux est un bloc ou sort du cadre.

Types dont les regles propres sont connues : porte, totem, scie, garde bleu,
bloodhound, anti-gravite, garde rouge, oiseau chercheur, canon (verdict "verifie"). Pour les autres,
seules les regles communes (codes 2 sans liste propre, et 1) sont appliquees : verdict "non verifie".
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
# Rayon du garde bleu (vx ; vy = 0), releve dans l'editeur du jeu le 2026-10-09 : la poignee jaune
# reste sur l'horizontale, vers la droite, de 192 a 448 par pas de 64 (tiree ailleurs, elle s'y recale).
RAYONS_GARDE_BLEU = tuple(range(192, 449, 64))
ANTIGRAVITE, GARDE_ROUGE = 7, 9
# Types dont l'octet +0x194 est nul (anti-gravite) : les zones de la porte et du totem s'etendent
# d'un carreau a droite et en bas (calcul editeur_calcul_codes du jeu).
ETENDUES = {ANTIGRAVITE: 1}
# Emprise : carreaux, depuis son carreau moins (1, 1), ni bloc ni hors du cadre (controle a l'enregistrement, code 4).
EMPRISES = {ANTIGRAVITE: ((0, 0), (0, 1), (1, 0), (1, 1))}
# Course du garde rouge (vx, vy), releve dans l'editeur du jeu le 2026-10-16 (kot_headless,
# controller/placements.COURSES) : horizontale (192 a 832) ou verticale (192 a 448), dans les deux sens.
# La poignee s'aimante a la course la plus proche sans regarder le cadre (regle course_hors_cadre hors perimetre).
COURSES_GARDE_ROUGE = (tuple((s * n, 0) for s in (1, -1) for n in range(192, 833, 64))
                       + tuple((0, s * n) for s in (1, -1) for n in range(192, 449, 64)))


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


def zone_porte(porte: Obstacle, etendue: int = 0) -> tuple[int, int, int, int]:
    """(colonne, rangee, largeur, hauteur) en carreaux des 4 x 4 carreaux interdits autour de la porte,
    plus `etendue` carreau a droite et en bas."""
    pc, pr = base_2x2(porte)
    return pc - 1, pr - 1, 4 + etendue, 4 + etendue


def zone_totem(totem: Obstacle, etendue: int = 0) -> tuple[int, int, int, int]:
    tc, tr = base_2x2(totem)
    return tc, tr, 2 + etendue, 2 + etendue


def _code_piege(o: Obstacle, grille: int, porte: Obstacle | None, totem: Obstacle | None) -> int:
    c, r = carreau(o)
    bc, br = base_2x2(o)
    if o.type == BLOODHOUND:
        if (o.orientation or 0) not in SUPPORTS:
            return 3
        dc, dr = SUPPORTS[o.orientation or 0]
        if not (plein(grille, c, r) or plein(grille, c + dc, r + dr)):
            return 3
    if porte is not None:
        zc, zr, zl, zh = zone_porte(porte, ETENDUES.get(o.type, 0))
        if zc <= c < zc + zl and zr <= r < zr + zh:
            return 2
        pc, pr = base_2x2(porte)
        if any((c, r) == (pc + dc, pr + dr) for dc, dr in PROCHES_PORTE.get(o.type, ())):
            return 2
    if totem is not None:
        zc, zr, zl, zh = zone_totem(totem, ETENDUES.get(o.type, 0))
        if zc <= c < zc + zl and zr <= r < zr + zh:
            return 1
    if any(plein(grille, bc + dc, br + dr) for dc, dr in EMPRISES.get(o.type, ())):
        return 4
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
