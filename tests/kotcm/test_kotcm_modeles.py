import pytest

from kotcm.modeles import Modeles, aimanter


@pytest.fixture(scope="module")
def modeles():
    return Modeles()


def test_aimanter():
    assert aimanter(710, 32, 896) == 736
    assert aimanter(700, 32, 896) == 672
    assert aimanter(-40, 32, 896) == 32
    assert aimanter(2000, 32, 896) == 864
    assert aimanter(64, 50, 512) == 50
    assert aimanter(511, 50, 512) == 498


def test_pas_mesures(modeles):
    assert modeles.aimant(1) == (0, 50)        # porte
    assert modeles.aimant(2) == (0, 35)        # totem
    assert modeles.aimant(8) == (32, 32)       # scie
    assert modeles.aimant(11) == (0, 0)        # plateforme
    assert modeles.aimant(18) is None          # gemme : libre
    assert modeles.aimanter(8, 740, 100) == (736, 96)
    assert modeles.aimanter(18, 261, 240) == (261, 240)


def test_modeles_mesures_et_supposes(modeles):
    assert modeles.est_mesure(4) and not modeles.est_mesure(45)
    assert modeles.champs(9)["vy"] == -256              # garde rouge : vecteur vertical
    assert modeles.champs(10)["vx"] == 192              # garde bleu : rayon 192
    assert modeles.champs(45) == {"f6": 1, "f7": False, "f9": 0, "orientation": 0, "vx": 180, "vy": 0,
                                  "f13": 0, "f14": 0, "f15": True, "f16": 1}
    assert modeles.aimant(45) == (32, 32)
    assert modeles.donjon == {"f2": 0, "f3": 2, "f4": 5, "f6": 1, "f7": False}
