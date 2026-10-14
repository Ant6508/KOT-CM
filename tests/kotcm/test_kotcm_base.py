import pytest

from kotcm.base import Base
from kotcm.corpus import Corpus
from kotcm.modeles import Modeles
from kotcm.protobuf import Donjon


@pytest.fixture(scope="module")
def corpus():
    return Corpus()


@pytest.fixture(scope="module")
def modeles():
    return Modeles()


def _resume(base):
    return [(o.ident, o.type, o.x, o.y) for o in base.donjon.obstacles]


def test_nouvelle_base_depuis_une_forme(corpus, modeles):
    base = Base.nouvelle(corpus.forme("commune", 130), modeles)     # 2 plateformes, 1 trampoline
    assert base.donjon.grille == 142614553
    assert (base.donjon.f3, base.donjon.f4) == (2, 5)
    assert _resume(base) == [(0, 1, 64, 50), (1, 2, 64, 163), (2, 11, 64, 256), (3, 11, 64, 320),
                             (4, 12, 64, 384)]


def test_poser_avant_les_gemmes_et_renumeroter(corpus, modeles):
    base = Base.nouvelle(corpus.forme("commune", 69), modeles)
    base._ajouter(18, 242, 311)
    ident = base.poser(4, 740, 100)
    assert ident == 2
    assert _resume(base) == [(0, 1, 64, 50), (1, 2, 64, 163), (2, 4, 736, 96), (3, 18, 242, 311)]
    canon = base.obstacle(2)
    assert (canon.vx, canon.vy, canon.f15) == (180, 0, True)
    base.retirer(2)
    assert _resume(base) == [(0, 1, 64, 50), (1, 2, 64, 163), (2, 18, 242, 311)]


def test_porte_et_totem_proteges(corpus, modeles):
    base = Base.nouvelle(corpus.forme("commune", 69), modeles)
    with pytest.raises(ValueError):
        base.retirer(0)
    with pytest.raises(ValueError):
        base.poser(2, 100, 100)
    with pytest.raises(ValueError):
        base.modifier(1, type=8)
    ident = base.poser(8, 352, 96)
    with pytest.raises(ValueError):
        base.modifier(ident, type=1)
    with pytest.raises(ValueError):
        base.modifier(ident, couleur=1)


def test_porte_et_totem_ne_s_echangent_pas(corpus, modeles):
    # Sinon deux portes ou deux totems (signale par l'operateur le 2026-10-13).
    base = Base.nouvelle(corpus.forme("commune", 69), modeles)
    with pytest.raises(ValueError):
        base.modifier(0, type=2)
    with pytest.raises(ValueError):
        base.modifier(1, type=1)
    assert [o.type for o in base.donjon.obstacles] == [1, 2]
    base.modifier(0, type=1, x=128)          # garder son propre type reste permis
    assert base.obstacle(0).x == 128


def test_modifier_change_le_type_sans_aimanter(corpus, modeles):
    base = Base.nouvelle(corpus.forme("commune", 69), modeles)
    ident = base.poser(8, 736, 96)
    base.modifier(ident, type=4, x=740, orientation=1)
    o = base.obstacle(ident)
    assert (o.type, o.x, o.y, o.orientation) == (4, 740, 96, 1)


def test_orientation_du_bloodhound_de_0_a_3(corpus, modeles):
    # Defaut releve a la recette de la phase 2 : la fiche acceptait 4.
    base = Base.nouvelle(corpus.forme("commune", 69), modeles)
    ident = base.poser(44, 672, 96)
    for refusee in (4, -1, 225):
        with pytest.raises(ValueError):
            base.modifier(ident, orientation=refusee)
    base.modifier(ident, orientation=3)
    base.modifier(ident, orientation=None)               # saisie videe : champ absent, lu comme 0
    base.obstacle(ident).orientation = 7                 # lu ainsi dans un .bin : on peut encore le glisser
    base.modifier(ident, x=608, y=96)
    assert (base.obstacle(ident).x, base.obstacle(ident).orientation) == (608, 7)


def test_orientation_des_autres_types_non_bornee(corpus, modeles):
    # Le type 21 porte des orientations en degres (45, 135, 225, 315 dans les captures).
    base = Base.nouvelle(corpus.forme("commune", 69), modeles)
    ident = base.poser(21, 672, 96)
    base.modifier(ident, orientation=225)
    with pytest.raises(ValueError):
        base.modifier(ident, type=44, orientation=225)   # devenir bloodhound avec une orientation hors bornes
    base.modifier(ident, type=44)                        # sans saisie d'orientation : permis, les regles le signalent
    assert base.obstacle(ident).type == 44


def test_aller_retour_octets(corpus, modeles):
    base = Base.nouvelle(corpus.forme("moddee", 8), modeles)
    base.poser(10, 480, 224)
    relue = Base.depuis_octets(base.octets(), modeles)
    assert relue.donjon == base.donjon
    assert Donjon.depuis_octets(relue.octets()) == base.donjon


def test_copie_independante(corpus, modeles):
    base = Base.nouvelle(corpus.forme("commune", 69), modeles)
    copie = base.copie()
    base.poser(8, 352, 96)
    assert len(copie.donjon.obstacles) == 2
