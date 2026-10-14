# -*- coding: utf-8 -*-
"""Codec d'un `KTProtocol::Dungeon`, sans passer par le jeu.

Recopie (pas d'import : kotcm ne depend pas du reste de kot_headless) de
`controller/bundle.py` (varints, champs) et de `controller/donjon.py`
(Donjon, Obstacle, grille). Schema relu dans le binaire (kot_headless,
NOTES.md, seance du 2026-09-29 suite 6) :

    Dungeon           1 obstacles (repete), 2 int32, 3 enum, 4 int32,
                      5 grille (int32), 6 int32, 7 bool
    Dungeon_Obstacle  1 type (requis), 2 x, 3 y (requis, pixels, y vers le bas),
                      4 identifiant (requis), 6, 7, 9, 10 orientation,
                      11/12 vecteur (vx, vy), 13, 14, 15 bool, 16 enum

Seuls les champs presents (`None` = absent) sont ecrits, dans l'ordre ou le
jeu les serialise : un donjon capture se reproduit octet pour octet.

Grille : 7 x 4 cases de 128 px, bit `ligne * 7 + colonne`, ligne 0 en haut,
1 = bloc ; c'est aussi la `DungeonValue` du mod de l'ami.
"""

from __future__ import annotations

from dataclasses import dataclass, field

VARINT, I64, LEN, I32 = 0, 1, 2, 5
LARGEUR, HAUTEUR = 7, 4


def varint(n: int) -> bytes:
    """Varint protobuf ; un int32 negatif s'encode sur 10 octets (extension de signe a 64 bits)."""
    if n < 0:
        n += 1 << 64
    out = bytearray()
    while True:
        octet = n & 0x7F
        n >>= 7
        if n:
            out.append(octet | 0x80)
        else:
            out.append(octet)
            return bytes(out)


def cle(numero: int, type_wire: int) -> bytes:
    return varint((numero << 3) | type_wire)


def entier(numero: int, valeur: int) -> bytes:
    return cle(numero, VARINT) + varint(valeur)


def message(numero: int, contenu: bytes) -> bytes:
    return cle(numero, LEN) + varint(len(contenu)) + contenu


def lire_varint(octets: bytes, i: int) -> tuple[int, int]:
    n, decalage = 0, 0
    while True:
        octet = octets[i]
        i += 1
        n |= (octet & 0x7F) << decalage
        decalage += 7
        if not octet & 0x80:
            return n, i


def champs(octets: bytes) -> list[tuple[int, int, int | bytes]]:
    """Decode un niveau de message : [(numero, type_wire, valeur)], valeur brute pour LEN/I32/I64."""
    out, i = [], 0
    while i < len(octets):
        k, i = lire_varint(octets, i)
        numero, type_wire = k >> 3, k & 7
        if type_wire == VARINT:
            valeur, i = lire_varint(octets, i)
            if valeur >= 1 << 63:
                valeur -= 1 << 64
        elif type_wire == LEN:
            n, i = lire_varint(octets, i)
            valeur, i = octets[i:i + n], i + n
        elif type_wire == I32:
            valeur, i = octets[i:i + 4], i + 4
        elif type_wire == I64:
            valeur, i = octets[i:i + 8], i + 8
        else:
            raise ValueError("type wire %d non gere (octet %d)" % (type_wire, i))
        out.append((numero, type_wire, valeur))
    return out


def grille_depuis_lignes(lignes: list[str]) -> int:
    """['#......', ...] (4 lignes de 7, '#' = bloc) -> entier de la grille."""
    if len(lignes) != HAUTEUR or any(len(l) != LARGEUR for l in lignes):
        raise ValueError("grille attendue : %d lignes de %d cases" % (HAUTEUR, LARGEUR))
    valeur = 0
    for y, ligne in enumerate(lignes):
        for x, case in enumerate(ligne):
            if case == "#":
                valeur |= 1 << (y * LARGEUR + x)
    return valeur


def lignes_depuis_grille(valeur: int) -> list[str]:
    return ["".join("#" if valeur >> (y * LARGEUR + x) & 1 else "." for x in range(LARGEUR))
            for y in range(HAUTEUR)]


# (numero de champ, attribut), dans l'ordre de serialisation du jeu.
CHAMPS_OBSTACLE = [(1, "type"), (2, "x"), (3, "y"), (4, "ident"), (6, "f6"), (7, "f7"),
                   (9, "f9"), (10, "orientation"), (11, "vx"), (12, "vy"), (13, "f13"),
                   (14, "f14"), (15, "f15"), (16, "f16")]
CHAMPS_DONJON = [(2, "f2"), (3, "f3"), (4, "f4"), (5, "grille"), (6, "f6"), (7, "f7")]
BOOLEENS = {"f15", "f7"}


def _ecrire(objet, table) -> bytes:
    out = b""
    for numero, nom in table:
        valeur = getattr(objet, nom)
        if valeur is not None:
            out += entier(numero, int(valeur))
    return out


def _lire(octets: bytes, table) -> dict:
    noms = dict(table)
    valeurs = {}
    for numero, _, valeur in champs(octets):
        if numero in noms:
            nom = noms[numero]
            valeurs[nom] = bool(valeur) if nom in BOOLEENS else valeur
    return valeurs


@dataclass
class Obstacle:
    type: int
    x: int
    y: int
    ident: int
    f6: int | None = None
    f7: bool | None = None
    f9: int | None = None
    orientation: int | None = None
    vx: int | None = None
    vy: int | None = None
    f13: int | None = None
    f14: int | None = None
    f15: bool | None = None
    f16: int | None = None

    def octets(self) -> bytes:
        return _ecrire(self, CHAMPS_OBSTACLE)

    @classmethod
    def depuis_octets(cls, octets: bytes) -> "Obstacle":
        return cls(**_lire(octets, CHAMPS_OBSTACLE))


@dataclass
class Donjon:
    obstacles: list[Obstacle] = field(default_factory=list)
    f2: int | None = None
    f3: int | None = None
    f4: int | None = None
    grille: int | None = None
    f6: int | None = None
    f7: bool | None = None

    def octets(self) -> bytes:
        return b"".join(message(1, o.octets()) for o in self.obstacles) + _ecrire(self, CHAMPS_DONJON)

    @classmethod
    def depuis_octets(cls, octets: bytes) -> "Donjon":
        obstacles = [Obstacle.depuis_octets(v) for n, _, v in champs(octets) if n == 1]
        return cls(obstacles=obstacles, **_lire(octets, CHAMPS_DONJON))
