import os
from pathlib import Path

import pytest

from kotcm.protobuf import Donjon, Obstacle, champs, grille_depuis_lignes, lignes_depuis_grille, varint

RACINE = Path(__file__).resolve().parents[2]
CAPTURES = Path(os.environ.get("KOTCM_CAPTURES", RACINE / "captures"))
# Les donjons, pas le dossier : captures/ peut exister sans donjon capture (bases enregistrees par kotcm).
DONJONS = sorted(CAPTURES.glob("donjon*.bin")) if CAPTURES.is_dir() else []
LIGNES_69 = ["#......", "#....#.", "#.##...", "#.##.##"]


def test_varint_negatif_sur_dix_octets():
    assert varint(-256) == bytes.fromhex("80feffffffffffffff01")
    assert champs(b"\x08" + varint(-256)) == [(1, 0, -256)]


def test_grille_de_la_forme_69():
    assert grille_depuis_lignes(LIGNES_69) == 0xda35081
    assert lignes_depuis_grille(0xda35081) == LIGNES_69


def test_aller_retour_d_un_donjon_construit():
    d = Donjon(obstacles=[Obstacle(type=1, x=384, y=242, ident=0, f6=1, f7=False, f15=False, f16=1),
                          Obstacle(type=9, x=864, y=352, ident=1, f6=1, vx=0, vy=-256, f15=True)],
               f2=0, f3=2, f4=5, grille=0xda35081, f6=1, f7=False)
    assert Donjon.depuis_octets(d.octets()) == d


def test_champs_absents_non_ecrits():
    assert Obstacle(type=8, x=0, y=0, ident=0).octets() == bytes.fromhex("0808100018002000")


@pytest.mark.skipif(not DONJONS, reason="aucun donjon*.bin dans captures/ (KOTCM_CAPTURES pour un autre dossier)")
def test_aller_retour_de_toutes_les_captures():
    ecarts = [f.name for f in DONJONS if Donjon.depuis_octets(f.read_bytes()).octets() != f.read_bytes()]
    assert ecarts == []
