# -*- coding: utf-8 -*-
"""La connexion au jeu le temps d'une operation : `with Connexion(Appareil()) as jeu: ...`.

A l'entree : garde de version, frida-server 17.19.0, attache par pid, agent
charge. A la sortie, l'agent est decharge et la session fermee : une seule
session ouverte, et seulement le temps de l'operation (spec, 9.3). Le patch
d'« Enregistrer » survit a la fermeture (agent.js).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from kotcm.live import ErreurLive

AGENT = Path(__file__).with_name("agent.js")


@dataclass(frozen=True)
class Etat:
    ds_ok: bool                   # vtable de DungeonStorage reconnue
    emplacement: int | None       # emplacement courant de l'editeur (0 a 3)
    emplacement_ok: bool          # un Dungeon, et des Dungeon_Obstacle
    detail: str | None            # ce qui ne va pas, sinon None
    octets: bytes | None          # l'emplacement courant serialise par le jeu
    patch: str                    # "origine", "pose" ou "inconnu"
    editeur: bool                 # l'editeur tourne
    meme_fil: bool | None = None  # l'editeur tourne dans le fil de nativeDrawFrame (None : ferme)

    @classmethod
    def depuis_agent(cls, r: dict) -> "Etat":
        return cls(ds_ok=bool(r["ds"]), emplacement=r["courant"], emplacement_ok=bool(r["ok"]),
                   detail=r["detail"], octets=bytes.fromhex(r["octets"]) if r["octets"] is not None else None,
                   patch=r["patch"], editeur=bool(r["editeur"]), meme_fil=r.get("meme_fil"))


class Connexion:
    def __init__(self, appareil):
        self.appareil = appareil
        self.serial: str | None = None
        self.pid: int | None = None
        self._session = None
        self._script = None

    def __enter__(self) -> "Connexion":
        a = self.appareil
        a.verifier_version()
        a.preparer_serveur()
        self.serial, self.pid = a.serial, a.pid_jeu()
        try:
            self._session = a.attacher(self.pid)
            self._script = self._session.create_script(AGENT.read_text(encoding="utf-8"))
            self._script.load()
        except ErreurLive:
            self.__exit__(None, None, None)
            raise
        except Exception as e:
            self.__exit__(None, None, None)
            raise ErreurLive("live_attache", detail=str(e)) from e
        return self

    def __exit__(self, *exc) -> bool:
        for fermer in (getattr(self._script, "unload", None), getattr(self._session, "detach", None)):
            try:
                if fermer is not None:
                    fermer()
            except Exception:
                pass                # le jeu a pu se fermer entre-temps
        self._script = self._session = None
        return False

    def _appel(self, nom: str, *args):
        try:
            return getattr(self._script.exports_sync, nom)(*args)
        except Exception as e:
            if "live_jeu_ne_dessine_pas" in str(e):
                raise ErreurLive("live_jeu_ne_dessine_pas") from e
            raise ErreurLive("live_agent", detail=str(e)) from e

    def etat(self) -> Etat:
        return Etat.depuis_agent(self._appel("etat"))

    def ecrire(self, emplacement: int, octets: bytes) -> bytes | None:
        """Le jeu parse `octets` dans l'emplacement ; rend l'emplacement reserialise (None : illisible)."""
        r = self._appel("ecrire", emplacement, octets.hex())
        if not r["ecrit"]:
            if r["detail"] == "editeur":
                raise ErreurLive("live_editeur_ouvert")
            raise ErreurLive("live_structure", detail=r["detail"])
        return bytes.fromhex(r["octets"]) if r["ok"] and r["octets"] is not None else None

    def patcher(self, poser: bool) -> str:
        etat = self._appel("patcher", bool(poser))
        if etat == "inconnu":
            raise ErreurLive("live_patch_inconnu")
        return etat

    def evenements(self, secondes: float) -> list[int]:
        return self._appel("evenements", int(secondes * 1000))
