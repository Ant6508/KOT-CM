import pytest

from kotcm.corpus import Corpus
from kotcm.edition import Edition, ErreurLecture, Resume, chemin_libre
from kotcm.modeles import Modeles


@pytest.fixture
def ed():
    e = Edition(Corpus(), Modeles())
    e.nouvelle(e.corpus.forme("commune", 69))
    return e


def test_nouvelle_base(ed):
    assert ed.forme().numero == 69
    assert ed.modifiee and ed.chemin_ouvert is None and ed.suggestion() is None
    assert ed.resume() == Resume(objets=2, problemes=2, non_verifies=0)   # porte et totem dans un bloc


def test_glisser_aimante_sauf_en_placement_libre(ed):
    ident = ed.poser(8, 700, 100)
    assert (ed.base.obstacle(ident).x, ed.base.obstacle(ident).y) == (672, 96)
    ed.deplacer(ident, 745, 230)
    assert (ed.base.obstacle(ident).x, ed.base.obstacle(ident).y) == (736, 224)
    ed.libre = True
    ed.deplacer(ident, 745, 230)
    assert (ed.base.obstacle(ident).x, ed.base.obstacle(ident).y) == (745, 230)
    ident2 = ed.poser(4, 101, 102)
    assert (ed.base.obstacle(ident2).x, ed.base.obstacle(ident2).y) == (101, 102)


def test_annuler(ed):
    ident = ed.poser(8, 672, 96)
    ed.modifier(ident, type=4)
    assert ed.annuler() and ed.base.obstacle(ident).type == 8
    assert ed.annuler() and len(ed.base.donjon.obstacles) == 2
    assert not ed.annuler()


def test_une_erreur_ne_laisse_pas_d_etape_d_annulation(ed):
    with pytest.raises(ValueError):
        ed.retirer(0)
    with pytest.raises(ValueError):
        ed.modifier(1, type=8)
    assert not ed.annuler()


def test_selection_effacee_si_l_objet_disparait(ed):
    ident = ed.poser(8, 672, 96)
    ed.selectionner(ident)
    ed.annuler()
    assert ed.selection is None


def test_ne_jamais_ecraser_le_fichier_ouvert(ed, tmp_path):
    source = tmp_path / "donjon_a.bin"
    ed.enregistrer(str(source))
    ed.ouvrir(str(source))
    assert not ed.modifiee
    (tmp_path / "donjon_a_kotcm.bin").write_bytes(b"")
    assert ed.suggestion() == str(tmp_path / "donjon_a_kotcm_2.bin")
    with pytest.raises(ValueError):
        ed.enregistrer(str(source))
    ed.poser(8, 672, 96)
    ed.enregistrer(ed.suggestion())
    assert ed.chemin_sortie == str(tmp_path / "donjon_a_kotcm_2.bin")
    assert ed.suggestion() == ed.chemin_sortie and not ed.modifiee
    assert len(source.read_bytes()) < len((tmp_path / "donjon_a_kotcm_2.bin").read_bytes())


def test_fichier_illisible(ed, tmp_path):
    mauvais = tmp_path / "x.bin"
    mauvais.write_bytes(b"\x0f\xff")
    with pytest.raises(ErreurLecture):
        ed.ouvrir(str(mauvais))
    with pytest.raises(ErreurLecture):
        ed.ouvrir(str(tmp_path / "absent.bin"))
    assert ed.forme().numero == 69          # la base ouverte reste la


def test_chemin_libre():
    pris = {"a.bin", "a_2.bin"}
    assert chemin_libre("b.bin", existe=pris.__contains__) == "b.bin"
    assert chemin_libre("a.bin", existe=pris.__contains__) == "a_3.bin"
