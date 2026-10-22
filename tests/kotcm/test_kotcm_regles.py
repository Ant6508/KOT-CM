import json
from dataclasses import replace
from pathlib import Path

import pytest

from kotcm.protobuf import Donjon, Obstacle, grille_depuis_lignes
from kotcm.regles import Verdict, verdicts

DONNEES = Path(__file__).resolve().parents[1] / "donnees"
ORACLES = (DONNEES / "placements_oracle.json", DONNEES / "placements_oracle_d2.json")
GRILLE = grille_depuis_lignes(["#......", "#....#.", "#.##...", "#.##.##"])
BASE = Donjon(obstacles=[
    Obstacle(type=1, x=384, y=242, ident=0, f6=1),                 # porte
    Obstacle(type=2, x=832, y=355, ident=1, f6=1),                 # totem
    Obstacle(type=10, x=32, y=352, ident=2, f6=1, vx=192, vy=0),   # garde bleu
    Obstacle(type=8, x=672, y=352, ident=3, f6=1),                 # scie
    Obstacle(type=44, x=672, y=96, ident=4, f6=1, orientation=3),  # bloodhound
    Obstacle(type=18, x=242, y=311, ident=5, f6=0),                # gemme
], f3=2, f4=5, grille=GRILLE)


def _avec(donjon, ident, **champs):
    return replace(donjon, obstacles=[replace(o, **champs) if o.ident == ident else o for o in donjon.obstacles])


def test_base_valide_gemmes_sans_verdict():
    v = verdicts(BASE)
    assert set(v) == {0, 1, 2, 3, 4}
    assert all(x == Verdict(0, True) for x in v.values())


def test_codes_des_types_connus():
    assert verdicts(_avec(BASE, 3, x=352, y=96))[3] == Verdict(2, True)       # scie trop pres de la porte
    assert verdicts(_avec(BASE, 3, x=800, y=352))[3] == Verdict(1, True)      # scie sur le totem
    assert verdicts(_avec(BASE, 4, x=480, y=224, orientation=0))[4] == Verdict(3, True)   # bloodhound sans paroi
    assert verdicts(_avec(BASE, 0, y=50))[0] == Verdict(4, True)              # porte derriere le terrain


def test_autres_types_non_verifies():
    electrique = _avec(BASE, 3, type=46)
    assert verdicts(electrique)[3] == Verdict(0, False)
    assert verdicts(_avec(electrique, 3, x=352, y=96))[3] == Verdict(2, False)


NOUVELLE = Donjon(obstacles=[
    Obstacle(type=1, x=832, y=114, ident=0, f6=1),                    # porte
    Obstacle(type=2, x=64, y=227, ident=1, f6=1),                     # totem
    Obstacle(type=7, x=320, y=256, ident=2, f6=1, vx=180, vy=0),      # anti-gravite
    Obstacle(type=9, x=32, y=288, ident=3, f6=1, vx=576, vy=0),       # garde rouge
    Obstacle(type=14, x=672, y=160, ident=4, f6=1, orientation=0),    # oiseau chercheur
    Obstacle(type=4, x=864, y=352, ident=5, f6=1, orientation=0),     # canon
], f3=3, f4=5, grille=grille_depuis_lignes(["##..#..", ".#.##..", ".......", "...##.#"]))


def test_types_de_la_nouvelle_base_verifies():
    assert all(v == Verdict(0, True) for v in verdicts(NOUVELLE).values())
    assert verdicts(_avec(NOUVELLE, 5, x=736, y=160))[5] == Verdict(2, True)     # canon pres de la porte
    assert verdicts(_avec(NOUVELLE, 2, x=384, y=128))[2] == Verdict(4, True)      # anti-gravite : emprise dans un bloc
    assert verdicts(_avec(NOUVELLE, 2, x=320, y=64))[2] == Verdict(0, True)       # depuis le carreau, ce serait un bloc
    assert verdicts(_avec(NOUVELLE, 2, x=704, y=192))[2] == Verdict(2, True)      # zone de la porte elargie (+0x194)
    totem_deplace = _avec(NOUVELLE, 1, x=448, y=99)
    assert verdicts(_avec(totem_deplace, 2, x=384, y=128))[2] == Verdict(1, True)  # zone du totem elargie


def test_bloodhound_d_orientation_hors_de_0_a_3_sans_paroi():
    assert verdicts(_avec(BASE, 4, orientation=4))[4] == Verdict(3, True)
    assert verdicts(_avec(BASE, 4, orientation=225))[4] == Verdict(3, True)


def test_une_regle_qui_echoue_rend_non_verifie():
    assert verdicts(_avec(BASE, 4, x=None))[4] == Verdict(0, False)


@pytest.mark.parametrize("oracle", ORACLES, ids=lambda p: p.name)
def test_cas_tires_de_l_oracle_de_l_editeur(oracle):
    if not oracle.exists():
        pytest.skip("cas de l'oracle non publies")
    cas = json.loads(oracle.read_text(encoding="utf-8"))
    ecarts = []
    for i, c in enumerate(cas):
        d = dict(c["donjon"])
        donjon = Donjon(obstacles=[Obstacle(**o) for o in d.pop("obstacles")], **d)
        if verdicts(donjon)[c["ident"]].code != c["code"]:
            ecarts.append(i)
    assert cas and ecarts == []
    if oracle.name == "placements_oracle.json":
        assert len(cas) == 280
