# -*- coding: utf-8 -*-
"""python -m kotcm.live etat|evenements|charger BASE|decharger : le chargement live sans la fenetre.

`etat` et `evenements` ne font que lire (l'essai de la phase 2 s'en sert) ;
`charger` et `decharger` font ce que font les boutons de la fenetre.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from kotcm.live import ErreurLive
from kotcm.live.appareil import Appareil
from kotcm.live.chargeur import Chargeur
from kotcm.live.session import Connexion
from kotcm.textes import LANGUES, Traducteur, langue_initiale


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="python -m kotcm.live", description=__doc__.splitlines()[0])
    p.add_argument("commande", choices=("etat", "evenements", "charger", "decharger"))
    p.add_argument("base", nargs="?", help="charger : le .bin a charger")
    p.add_argument("--serial", help="appareil adb (sinon ANDROID_SERIAL, sinon le seul connecte)")
    p.add_argument("--sortie", help="etat : ecrire l'emplacement courant dans ce fichier")
    p.add_argument("--secondes", type=float, default=30.0, help="evenements : duree de l'ecoute")
    p.add_argument("--langue", choices=LANGUES)
    a = p.parse_args(argv)
    if a.commande == "charger" and not a.base:
        p.error("charger : le fichier .bin est requis")
    tr = Traducteur(langue_initiale(a.langue))

    def connecter():
        return Connexion(Appareil(a.serial))

    try:
        if a.commande == "etat":
            with connecter() as jeu:
                e = jeu.etat()
            if a.sortie and e.octets is not None:
                Path(a.sortie).parent.mkdir(parents=True, exist_ok=True)
                Path(a.sortie).write_bytes(e.octets)
            print(json.dumps({"serial": jeu.serial, "pid": jeu.pid, "ds_ok": e.ds_ok, "emplacement": e.emplacement,
                              "emplacement_ok": e.emplacement_ok, "detail": e.detail,
                              "octets": len(e.octets) if e.octets is not None else None,
                              "sha256": hashlib.sha256(e.octets).hexdigest() if e.octets is not None else None,
                              "patch": e.patch, "editeur": e.editeur, "meme_fil": e.meme_fil}, indent=1))
        elif a.commande == "evenements":
            print("ecoute des evenements de l'editeur pendant %g s..." % a.secondes, flush=True)
            with connecter() as jeu:
                print(jeu.evenements(a.secondes))
        elif a.commande == "charger":
            print(tr.t("live_charge_ok", emplacement=Chargeur(connecter).charger(Path(a.base).read_bytes())))
        else:
            print(tr.t("live_decharge_ok", emplacement=Chargeur(connecter).decharger()))
    except ErreurLive as e:
        print(tr.t(e.cle, **e.valeurs), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
