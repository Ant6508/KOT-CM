import json
from pathlib import Path

import pytest

from kotcm.corpus import Corpus

DONNEES = Path(__file__).resolve().parents[1] / "donnees"


@pytest.fixture(scope="module")
def corpus():
    return Corpus()


def test_143_formes_toutes_distinctes(corpus):
    assert len(corpus.formes) == 143
    assert sum(f.origine == "commune" for f in corpus.formes) == 130
    assert len({f.grille for f in corpus.formes}) == 143


def test_les_grilles_capturees_sont_dans_le_corpus(corpus):
    grilles = json.loads((DONNEES / "kotcm_grilles_capturees.json").read_text(encoding="utf-8"))
    assert len(grilles) == 47
    assert [g for g in grilles if corpus.par_grille(g) is None] == []


def test_forme_par_grille_et_par_numero(corpus):
    f = corpus.par_grille(0xda35081)
    assert (f.origine, f.numero, f.auteur) == ("commune", 69, None)
    assert corpus.forme("commune", 69) == f
    assert corpus.par_grille(0) is None and corpus.par_grille(None) is None
    with pytest.raises(KeyError):
        corpus.forme("commune", 0)


def test_credits_et_auteurs(corpus):
    assert "github.com/OvovUsus" in corpus.credits
    assert corpus.forme("moddee", 2).auteur == "krypt (krp.t)"


def test_moddee_8_compte_fait_foi(corpus):
    f = corpus.forme("moddee", 8)
    assert (f.plateformes, f.trampolines, f.antigravites) == (2, 0, 1)
