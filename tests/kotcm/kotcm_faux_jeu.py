"""Faux jeu pour les tests du chargement live : l'interface de `Connexion`, sans emulateur.

Quatre emplacements d'octets, un patch, un editeur ouvert ou non. `refus` : nombre
d'ecritures a rater (le jeu relit alors des octets tronques)."""

from kotcm.live import ErreurLive
from kotcm.live.session import Etat

JOUEUR = b"la base du joueur"
KOTCM = b"une base kotcm"


class FauxJeuLive:
    def __init__(self, serial="127.0.0.1:5555", pid=812, courant=3, octets=JOUEUR, patch="origine"):
        self.serial, self.pid, self.courant, self.patch = serial, pid, courant, patch
        self.emplacements = {i: b"autre emplacement" for i in range(4)}
        self.emplacements[courant] = octets
        self.editeur = False
        self.ds_ok = True
        self.refus = 0
        self.ecritures = []

    def __call__(self):            # le Chargeur appelle connecter() : le faux jeu est sa propre fabrique
        return self

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def etat(self) -> Etat:
        return Etat(ds_ok=self.ds_ok, emplacement=self.courant, emplacement_ok=True, detail=None,
                    octets=self.emplacements[self.courant], patch=self.patch, editeur=self.editeur)

    def ecrire(self, emplacement, octets):
        if self.editeur:
            raise ErreurLive("live_editeur_ouvert")
        self.ecritures.append((emplacement, octets))
        if self.refus:
            self.refus -= 1
            self.emplacements[emplacement] = octets[:-1]
        else:
            self.emplacements[emplacement] = octets
        return self.emplacements[emplacement]

    def patcher(self, poser):
        if self.patch == "inconnu":
            raise ErreurLive("live_patch_inconnu")
        self.patch = "pose" if poser else "origine"
        return self.patch
