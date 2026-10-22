# -*- coding: utf-8 -*-
"""La table d'adresses de libthieves.so d'une version du jeu (spec 2026-10-21-noyau-design, section 3).

Une table par versionCode, `tables/<code>.toml` ; elle contient les adresses que le code lit,
et fait foi pour elles. Le code Python lit une adresse par `table.adresse("nom")` (seul accès,
pour que `usages` le trouve), un agent JS par `ADR.nom` (`frida_.charger_agent`).

Sortes : `vtable` (clé : classe), `slot` (clé : `Classe[n]`), `export` (clé : symbole mangle),
`manuel` (sans clé, avec `octets` ou `section`). `decalage` : offset = ancre + decalage, pour
une adresse au milieu d'une fonction. `octets` : octets attendus à l'offset, pour toute sorte.
"""

from __future__ import annotations

import json
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path

TABLES = Path(__file__).resolve().parent / "tables"
SORTES = ("vtable", "slot", "export", "manuel")
CHAMPS = {"offset", "sorte", "cle", "decalage", "octets", "section", "fiche"}
NOM = re.compile(r"^[a-z][a-z0-9_]*$")
SLOT = re.compile(r"^(.+)\[(\d+)\]$")


class TableInvalide(Exception):
    pass


def disponibles(dossier: Path = TABLES) -> list[int]:
    """Les versionCode qui ont une table (`<code>.toml`, pas les brouillons)."""
    return sorted(int(p.stem) for p in Path(dossier).glob("*.toml") if p.stem.isdigit())


class VersionInconnue(Exception):
    def __init__(self, code: int, nom: str | None = None, dossier: Path = TABLES):
        self.code, self.nom = code, nom
        version = "%d (%s)" % (code, nom) if nom else str(code)
        connues = ", ".join(str(c) for c in disponibles(dossier)) or "aucune"
        super().__init__("pas de table d'adresses pour %s (tables : %s) : lancer `python -m kotnoyau.retrouver`"
                         % (version, connues))


@dataclass(frozen=True)
class Entree:
    nom: str
    offset: int
    sorte: str
    cle: str | None = None
    decalage: int = 0
    octets: bytes | None = None
    section: str | None = None
    fiche: str | None = None

    @property
    def ancre(self) -> int:
        """L'adresse que la clé désigne : offset - decalage."""
        return self.offset - self.decalage

    def slot(self) -> tuple[str, int]:
        m = SLOT.match(self.cle or "")
        if not m:
            raise TableInvalide("%s : clé de slot attendue sous la forme Classe[n]" % self.nom)
        return m.group(1), int(m.group(2))


def entree(nom: str, champs: dict) -> Entree:
    def refus(raison: str):
        raise TableInvalide("%s : %s" % (nom, raison))

    if not NOM.match(nom):
        refus("nom invalide (minuscules, chiffres, _)")
    inconnus = set(champs) - CHAMPS
    if inconnus:
        refus("champs inconnus : " + ", ".join(sorted(inconnus)))
    sorte = champs.get("sorte")
    if sorte not in SORTES:
        refus("sorte %r hors de %s" % (sorte, ", ".join(SORTES)))
    offset = champs.get("offset")
    if not isinstance(offset, int) or offset <= 0:
        refus("offset manquant ou nul")
    cle = champs.get("cle")
    if sorte == "manuel":
        if cle is not None:
            refus("une entrée manuelle n'a pas de clé")
    elif not isinstance(cle, str) or not cle:
        refus("clé manquante")
    if sorte == "slot" and not SLOT.match(cle):
        refus("clé de slot attendue sous la forme Classe[n]")
    octets = champs.get("octets")
    if octets is not None:
        try:
            octets = bytes.fromhex(octets)
        except (TypeError, ValueError):
            refus("octets : hexadécimal attendu")
        if not octets:
            refus("octets vides")
    section = champs.get("section")
    if sorte == "manuel" and octets is None and section is None:
        refus("une entrée manuelle demande des octets ou une section")
    decalage = champs.get("decalage", 0)
    if not isinstance(decalage, int) or decalage < 0:
        refus("décalage invalide")
    return Entree(nom, offset, sorte, cle, decalage, octets, section, champs.get("fiche"))


class Table:
    def __init__(self, code: int, nom: str, entrees: dict[str, Entree]):
        self.code, self.nom, self.entrees = code, nom, entrees

    @classmethod
    def lire(cls, chemin) -> "Table":
        with open(chemin, "rb") as f:
            try:
                donnees = tomllib.load(f)
            except tomllib.TOMLDecodeError as e:
                raise TableInvalide("%s : %s" % (chemin, e)) from e
        version = donnees.get("version", {})
        code, nom = version.get("code"), version.get("nom")
        if not isinstance(code, int) or not isinstance(nom, str):
            raise TableInvalide("%s : [version] demande code (entier) et nom (texte)" % chemin)
        return cls(code, nom, {n: entree(n, c) for n, c in donnees.get("adresses", {}).items()})

    @classmethod
    def pour(cls, code: int, nom: str | None = None, dossier: Path = TABLES) -> "Table":
        chemin = Path(dossier) / ("%d.toml" % code)
        if not chemin.is_file():
            raise VersionInconnue(code, nom, dossier)
        return cls.lire(chemin)

    @classmethod
    def derniere(cls, dossier: Path = TABLES) -> "Table":
        """La table du plus grand versionCode : la version de référence des métadonnées des sorties."""
        codes = disponibles(dossier)
        if not codes:
            raise TableInvalide("aucune table dans %s" % dossier)
        return cls.pour(codes[-1], dossier=dossier)

    def adresse(self, nom: str) -> int:
        try:
            return self.entrees[nom].offset
        except KeyError:
            raise KeyError("adresse %r absente de la table %d (%s)" % (nom, self.code, self.nom)) from None


def en_toml(code: int, nom: str, entrees: list[Entree], notes: dict[str, str] | None = None,
            entete: str = "") -> str:
    """Le texte TOML d'une table ; `notes` : un commentaire au-dessus d'une entrée (brouillons)."""
    notes = notes or {}
    lignes = [entete] if entete else []
    lignes += ["[version]", "code = %d" % code, "nom = %s" % json.dumps(nom, ensure_ascii=False), ""]
    for e in entrees:
        if e.nom in notes:
            lignes.append("# " + notes[e.nom])
        lignes += ["[adresses.%s]" % e.nom, "offset = 0x%x" % e.offset, 'sorte = "%s"' % e.sorte]
        if e.cle is not None:
            lignes.append("cle = %s" % json.dumps(e.cle, ensure_ascii=False))
        if e.decalage:
            lignes.append("decalage = 0x%x" % e.decalage)
        if e.octets is not None:
            lignes.append('octets = "%s"' % e.octets.hex())
        if e.section is not None:
            lignes.append("section = %s" % json.dumps(e.section))
        if e.fiche is not None:
            lignes.append("fiche = %s" % json.dumps(e.fiche, ensure_ascii=False))
        lignes.append("")
    return "\n".join(lignes)
