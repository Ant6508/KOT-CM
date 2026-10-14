# -*- coding: utf-8 -*-
"""Charger une base dans l'editeur du jeu, et remettre celle du joueur (spec, section 9).

Le jeu parse le `.bin` dans le message `Dungeon` de l'emplacement courant de
`DungeonStorage`, depuis l'accueil : l'editeur le lit a son ouverture.
« Enregistrer » est neutralise par un patch qui ne disparait qu'au
redemarrage du jeu ou par `decharger`.

Garde-fous :

- rien n'est ecrit si la memoire du jeu n'a pas la forme attendue, si
  l'editeur est ouvert, ou si le code d'« Enregistrer » est inconnu ;
- la base du joueur est copiee sur disque avant la premiere ecriture
  (`sauvegardes/` du dossier de donnees, `~/.kotcm` ou `KOTCM_DOSSIER`, jamais
  ecrasee ni effacee), puis le patch est pose, puis l'etat du chargement est
  enregistre (`live.json`, au meme endroit), et alors seulement la base est
  ecrite ;
- l'etat enregistre ne vaut que pour le meme processus du jeu, patch pose :
  un jeu redemarre a recharge la base du serveur ;
- apres chaque ecriture, le jeu reserialise l'emplacement et doit rendre
  exactement les octets ecrits ; sinon la base du joueur est remise.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from kotcm.live import ErreurLive, dossier_donnees


@dataclass(frozen=True)
class Chargement:
    serial: str
    pid: int
    emplacement: int
    sauvegarde: str      # le .bin de la base du joueur
    empreinte: str       # sha256 de la derniere base chargee


def empreinte(octets: bytes) -> str:
    return hashlib.sha256(octets).hexdigest()


class Chargeur:
    def __init__(self, connecter, dossier: Path | None = None, horloge=datetime.now):
        self.connecter = connecter      # () -> gestionnaire de contexte qui rend la connexion au jeu
        self.dossier = Path(dossier) if dossier else dossier_donnees()
        self.horloge = horloge

    # --- etat enregistre ----------------------------------------------------------

    @property
    def fichier(self) -> Path:
        return self.dossier / "live.json"

    def chargement(self) -> Chargement | None:
        """Le dernier chargement non decharge, tel qu'enregistre (peut-etre perime)."""
        try:
            return Chargement(**json.loads(self.fichier.read_text(encoding="utf-8")))
        except (OSError, ValueError, TypeError):
            return None

    def chargee(self) -> int | None:
        """L'emplacement de la base chargee selon l'etat enregistre, sinon None (sans toucher au jeu)."""
        c = self.chargement()
        return c.emplacement if c else None

    # --- operations ---------------------------------------------------------------

    def charger(self, octets: bytes) -> int:
        with self.connecter() as jeu:
            etat = jeu.etat()
            self._verifier(etat)
            c = self._valide(jeu, etat)
            if c is None:
                if etat.patch == "pose":
                    raise ErreurLive("live_patch_orphelin")
                sauvegarde = str(self._sauvegarder(etat.emplacement, etat.octets))
            elif c.emplacement != etat.emplacement:
                raise ErreurLive("live_emplacement_change", avant=c.emplacement, maintenant=etat.emplacement)
            else:
                sauvegarde = c.sauvegarde
            jeu.patcher(True)
            self._enregistrer(Chargement(jeu.serial, jeu.pid, etat.emplacement, sauvegarde, empreinte(octets)))
            relu = jeu.ecrire(etat.emplacement, octets)
            if relu != octets:
                self._remettre(jeu, etat.emplacement, Path(sauvegarde))
                raise ErreurLive("live_ecriture", detail=self._ecart(octets, relu))
            return etat.emplacement

    def decharger(self) -> int:
        with self.connecter() as jeu:
            etat = jeu.etat()
            self._verifier(etat)
            c = self._valide(jeu, etat)
            if c is None:
                perime = self.chargement() is not None
                self._oublier()
                if etat.patch == "pose":
                    raise ErreurLive("live_patch_orphelin")
                if perime:
                    raise ErreurLive("live_redemarre")
                raise ErreurLive("live_rien_a_decharger")
            self._remettre(jeu, c.emplacement, Path(c.sauvegarde))
            return c.emplacement

    # --- interne -----------------------------------------------------------------------

    @staticmethod
    def _verifier(etat) -> None:
        if not etat.ds_ok or etat.emplacement is None or not 0 <= etat.emplacement <= 3 or not etat.emplacement_ok:
            raise ErreurLive("live_structure", detail=etat.detail or "emplacement %r" % (etat.emplacement,))
        if etat.editeur:
            raise ErreurLive("live_editeur_ouvert")
        if etat.patch == "inconnu":
            raise ErreurLive("live_patch_inconnu")

    def _valide(self, jeu, etat) -> Chargement | None:
        """Le chargement enregistre s'il concerne ce processus du jeu, patch toujours pose."""
        c = self.chargement()
        if c is None or (c.serial, c.pid) != (jeu.serial, jeu.pid) or etat.patch != "pose":
            return None
        return c

    def _sauvegarder(self, emplacement: int, octets: bytes) -> Path:
        dossier = self.dossier / "sauvegardes"
        dossier.mkdir(parents=True, exist_ok=True)
        racine = "emplacement%d_%s" % (emplacement, self.horloge().strftime("%Y%m%d-%H%M%S"))
        chemin, n = dossier / (racine + ".bin"), 2
        while chemin.exists():
            chemin, n = dossier / ("%s_%d.bin" % (racine, n)), n + 1
        chemin.write_bytes(octets)
        return chemin

    def _remettre(self, jeu, emplacement: int, sauvegarde: Path) -> None:
        """Remet la base du joueur, retire le patch, oublie le chargement."""
        octets = sauvegarde.read_bytes()
        if jeu.ecrire(emplacement, octets) != octets:
            raise ErreurLive("live_remise", sauvegarde=str(sauvegarde))   # patch et etat gardes
        jeu.patcher(False)
        self._oublier()

    def _enregistrer(self, c: Chargement) -> None:
        self.dossier.mkdir(parents=True, exist_ok=True)
        self.fichier.write_text(json.dumps(asdict(c), indent=1), encoding="utf-8")

    def _oublier(self) -> None:
        self.fichier.unlink(missing_ok=True)

    @staticmethod
    def _ecart(attendus: bytes, relus: bytes | None) -> str:
        if relus is None:
            return "illisible"
        if len(relus) != len(attendus):
            return "%d octets relus au lieu de %d" % (len(relus), len(attendus))
        return "octets differents"
