# -*- coding: utf-8 -*-
"""python -m kotcm [base.bin] [--langue fr|en] [--serial S] : la fenetre du mode creatif."""

from __future__ import annotations

import argparse

from kotcm.corpus import Corpus
from kotcm.edition import Edition
from kotcm.live.appareil import Appareil
from kotcm.live.chargeur import Chargeur
from kotcm.live.session import Connexion
from kotcm.modeles import Modeles
from kotcm.textes import LANGUES, Traducteur, langue_initiale


def main(argv=None) -> None:
    p = argparse.ArgumentParser(prog="python -m kotcm", description=__doc__.splitlines()[0])
    p.add_argument("base", nargs="?", help="donjon .bin a ouvrir")
    p.add_argument("--langue", choices=LANGUES)
    p.add_argument("--serial", help="appareil adb du jeu (sinon ANDROID_SERIAL, sinon le seul connecte)")
    a = p.parse_args(argv)
    edition = Edition(Corpus(), Modeles())
    if a.base:
        edition.ouvrir(a.base)

    import tkinter as tk
    from kotcm.fenetre import Fenetre

    racine = tk.Tk()
    # frida n'est importe qu'au premier chargement : la fenetre s'ouvre sans lui.
    chargeur = Chargeur(lambda: Connexion(Appareil(a.serial)))
    Fenetre(racine, edition, Traducteur(langue_initiale(a.langue)), chargeur=chargeur)
    racine.mainloop()


if __name__ == "__main__":
    main()
