import json
from dataclasses import replace
from pathlib import Path

import pytest

from kotcm.protobuf import Donjon, Obstacle, grille_depuis_lignes
from kotcm.regles import Verdict, verdicts

ORACLE = Path(__file__).resolve().parents[1] / "donnees" / "placements_oracle.json"
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
    canon = _avec(BASE, 3, type=4)
    assert verdicts(canon)[3] == Verdict(0, False)
    assert verdicts(_avec(canon, 3, x=352, y=96))[3] == Verdict(2, False)


def test_bloodhound_d_orientation_hors_de_0_a_3_sans_paroi():
    assert verdicts(_avec(BASE, 4, orientation=4))[4] == Verdict(3, True)
    assert verdicts(_avec(BASE, 4, orientation=225))[4] == Verdict(3, True)


def test_une_regle_qui_echoue_rend_non_verifie():
    assert verdicts(_avec(BASE, 4, x=None))[4] == Verdict(0, False)


@pytest.mark.skipif(not ORACLE.exists(), reason="cas de l'oracle non publies")
def test_cas_tires_de_l_oracle_de_l_editeur():
    cas = json.loads(ORACLE.read_text(encoding="utf-8"))
    ecarts = []
    for i, c in enumerate(cas):
        d = dict(c["donjon"])
        donjon = Donjon(obstacles=[Obstacle(**o) for o in d.pop("obstacles")], **d)
        if verdicts(donjon)[c["ident"]].code != c["code"]:
            ecarts.append(i)
    assert len(cas) == 280 and ecarts == []
