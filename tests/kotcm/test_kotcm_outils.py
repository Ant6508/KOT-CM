"""Les outils de generation des donnees (kotcm/outils) : non publies, ces tests se sautent sans eux."""

import pytest

pytest.importorskip("kotcm.outils")

from kotcm.outils.extraire_corpus import lire_presets  # noqa: E402
from kotcm.outils.extraire_modeles import modeles_depuis  # noqa: E402
from kotcm.protobuf import Donjon, Obstacle  # noqa: E402


def test_lecture_d_un_entete():
    texte = (
        "\t/* [0]   */\t{0, \t\tnullptr, \t\t\t\t\t\t{}, 0},\n"
        "\t/* [21]  */\t{14680836,\t\tnullptr, TrObjectInfo::CreateTrObjectsByIDs<2>({11,11}), 2 + 0 + 0},\n"
        "\t/* [8]   */\t{153094656,\t\"Disconnect (4disc0nnect4)\", "
        "\tTrObjectInfo::CreateTrObjectsByIDs<3>({11,11}), 2 + 0 + 1},\n"
    )
    assert lire_presets(texte, "moddee") == [
        {"origine": "moddee", "numero": 21, "grille": 14680836, "auteur": None,
         "plateformes": 2, "trampolines": 0, "antigravites": 0},
        {"origine": "moddee", "numero": 8, "grille": 153094656, "auteur": "Disconnect (4disc0nnect4)",
         "plateformes": 2, "trampolines": 0, "antigravites": 1},
    ]


def test_modeles_depuis():
    porte = dict(f6=1, f7=False, f9=0, orientation=0, vx=180, vy=0, f13=0, f14=0, f15=False, f16=1)
    d = Donjon(obstacles=[Obstacle(type=1, x=384, y=242, ident=0, **porte),
                          Obstacle(type=8, x=672, y=352, ident=1, **dict(porte, f15=True)),
                          Obstacle(type=18, x=261, y=240, ident=2, **dict(porte, f6=0)),
                          Obstacle(type=18, x=242, y=311, ident=3, **dict(porte, f6=0))],
               f2=0, f3=2, f4=5, grille=1, f6=1, f7=False)
    m = modeles_depuis([d, d])
    assert m["types"]["1"] == {"compte": 2, "champs": porte, "aimant": [0, 50]}
    assert m["types"]["18"]["aimant"] is None
    assert m["defaut_piege"]["f15"] is True
    assert m["donjon"] == {"f2": 0, "f3": 2, "f4": 5, "f6": 1, "f7": False}
