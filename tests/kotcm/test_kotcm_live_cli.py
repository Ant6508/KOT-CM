import json
import subprocess
import sys
from pathlib import Path

import pytest

import kotcm.live.__main__ as cli
from kotcm_faux_jeu import JOUEUR, KOTCM, FauxJeuLive

RACINE = Path(__file__).resolve().parents[2]


@pytest.fixture
def jeu(monkeypatch, tmp_path):
    faux = FauxJeuLive()
    monkeypatch.setattr(cli, "Appareil", lambda serial: None)
    monkeypatch.setattr(cli, "Connexion", lambda appareil: faux)
    monkeypatch.setenv("KOTCM_DOSSIER", str(tmp_path / "kotcm"))
    return faux


def test_etat_ecrit_l_emplacement_courant(jeu, tmp_path, capsys):
    sortie = tmp_path / "essai" / "accueil.bin"
    assert cli.main(["etat", "--sortie", str(sortie), "--langue", "fr"]) == 0
    r = json.loads(capsys.readouterr().out)
    assert (r["emplacement"], r["octets"], r["patch"], r["editeur"]) == (3, len(JOUEUR), "origine", False)
    assert sortie.read_bytes() == JOUEUR


def test_charger_puis_decharger(jeu, tmp_path, capsys):
    base = tmp_path / "base.bin"
    base.write_bytes(KOTCM)
    assert cli.main(["charger", str(base), "--langue", "fr"]) == 0
    assert "Base chargée dans l'emplacement 3" in capsys.readouterr().out
    assert jeu.emplacements[3] == KOTCM and jeu.patch == "pose"
    assert (tmp_path / "kotcm" / "live.json").exists()
    assert cli.main(["decharger", "--langue", "en"]) == 0
    assert capsys.readouterr().out.strip() == "Your base is back in slot 3."
    assert jeu.emplacements[3] == JOUEUR and jeu.patch == "origine"


def test_un_refus_s_affiche_dans_la_langue(jeu, capsys):
    jeu.editeur = True
    assert cli.main(["decharger", "--langue", "fr"]) == 1
    assert capsys.readouterr().err.startswith("L'éditeur est ouvert")


def test_frida_n_est_importe_qu_a_l_attache():
    # La fenetre et la ligne de commande s'ouvrent sans frida installe.
    code = "import sys, kotcm.__main__, kotcm.live.__main__; print('frida' in sys.modules)"
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=RACINE)
    assert r.stdout.strip() == "False", r.stderr
