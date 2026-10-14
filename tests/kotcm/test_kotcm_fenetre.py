from pathlib import Path

import pytest

tk = pytest.importorskip("tkinter")

import kotcm.fenetre as module_fenetre  # noqa: E402
from kotcm.corpus import Corpus  # noqa: E402
from kotcm.edition import Edition  # noqa: E402
from kotcm.fenetre import Fenetre, vers_donjon, vers_ecran  # noqa: E402
from kotcm.live.chargeur import Chargeur  # noqa: E402
from kotcm.modeles import Modeles  # noqa: E402
from kotcm.textes import TEXTES, Traducteur  # noqa: E402
from kotcm_faux_jeu import JOUEUR, FauxJeuLive  # noqa: E402


@pytest.fixture(scope="module")
def racine():
    # Une seule racine Tk par processus : sous Windows, en creer plusieurs de suite
    # echoue par moments ("invalid command name tcl_findLibrary"). Fenetre reconstruit
    # ses widgets dans la racine qu'on lui donne.
    try:
        r = tk.Tk()
    except tk.TclError:
        pytest.skip("pas d'ecran")
    r.withdraw()
    yield r
    r.destroy()


def test_conversion_ecran_donjon():
    assert vers_donjon(*vers_ecran(736, 96)) == (736, 96)


@pytest.mark.parametrize("langue,titre", [("fr", "kotcm — mode créatif"), ("en", "kotcm — creative mode")])
def test_fenetre_se_construit_et_change_de_langue(racine, tmp_path, langue, titre):
    ed = Edition(Corpus(), Modeles())
    ed.nouvelle(ed.corpus.forme("commune", 130))
    ident = ed.poser(8, 352, 96)
    ed.selectionner(ident)
    fen = Fenetre(racine, ed, Traducteur("fr" if langue == "en" else "en"), preferences=tmp_path / "p.json")
    fen.changer_langue(langue)
    racine.update_idletasks()
    assert racine.title() == titre
    assert len(fen.liste.get_children()) == 6
    assert fen.saisies["x"].get() == "352"
    assert (tmp_path / "p.json").exists()


def test_fiche_applique_x_et_les_champs_bruts(racine, tmp_path):
    ed = Edition(Corpus(), Modeles())
    ed.nouvelle(ed.corpus.forme("commune", 69))
    ident = ed.poser(8, 352, 96)
    ed.selectionner(ident)
    fen = Fenetre(racine, ed, Traducteur("en"), preferences=tmp_path / "p.json")
    fen._basculer_bruts()
    assert fen.bouton_bruts["text"] == "▾ other fields"
    assert fen.etiquette_selection["text"] == "Selection: 2 — saw"
    for nom, valeur in (("x", "360"), ("f15", "0")):
        fen.saisies[nom].delete(0, "end")
        fen.saisies[nom].insert(0, valeur)
    fen._appliquer_fiche()
    o = ed.base.obstacle(ident)
    assert (o.x, o.f15) == (360, False)


def test_le_type_de_la_porte_et_du_totem_est_fige(racine, tmp_path):
    ed = Edition(Corpus(), Modeles())
    ed.nouvelle(ed.corpus.forme("commune", 69))
    scie = ed.poser(8, 352, 96)
    fen = Fenetre(racine, ed, Traducteur("fr"), preferences=tmp_path / "p.json")
    for ident in (0, 1):                                  # porte, totem
        ed.selectionner(ident)
        fen.rafraichir()
        assert str(fen.choix_type["state"]) == "disabled"
    ed.selectionner(scie)
    fen.rafraichir()
    assert str(fen.choix_type["state"]) == "readonly"
    assert [v for v in fen.choix_type["values"] if v.split()[0] in ("1", "2")] == []


def test_fenetre_sans_base(racine, tmp_path):
    fen = Fenetre(racine, Edition(Corpus(), Modeles()), Traducteur("fr"), preferences=tmp_path / "p.json")
    racine.update_idletasks()
    assert fen.liste.get_children() == ()
    assert fen.etiquette_selection["text"] == "Sélection : (aucune)"
    assert str(fen.bouton_charger["state"]) == str(fen.bouton_decharger["state"]) == "disabled"


class Boites:
    """Les boites de dialogue de la fenetre : reponse prevue, messages notes."""

    def __init__(self, monkeypatch):
        self.reponse, self.vues = True, []
        for nom in ("showinfo", "showerror", "askyesno", "askyesnocancel"):
            monkeypatch.setattr(module_fenetre.messagebox, nom,
                                lambda titre, message, nom=nom, **_: self._voir(nom, message))

    def _voir(self, nom, message):
        self.vues.append((nom, message))
        return self.reponse


@pytest.fixture
def boites(monkeypatch):
    return Boites(monkeypatch)


def fenetre_live(racine, tmp_path, forme=130):
    ed = Edition(Corpus(), Modeles())
    ed.nouvelle(ed.corpus.forme("commune", forme))
    jeu = FauxJeuLive()
    fen = Fenetre(racine, ed, Traducteur("fr"), preferences=tmp_path / "p.json",
                  chargeur=Chargeur(jeu, dossier=tmp_path / "kotcm"))
    return fen, ed, jeu


def test_charger_puis_decharger_depuis_la_fenetre(racine, tmp_path, boites):
    fen, ed, jeu = fenetre_live(racine, tmp_path)
    assert str(fen.bouton_charger["state"]) == "normal" and str(fen.bouton_decharger["state"]) == "disabled"
    fen.charger_dans_le_jeu()
    assert jeu.emplacements[3] == ed.base.octets() and jeu.patch == "pose"
    assert boites.vues[-1][0] == "showinfo" and boites.vues[-1][1].startswith("Base chargée dans l'emplacement 3.")
    assert fen.etiquette_etat["text"].endswith(" · chargée dans le jeu (emplacement 3)")
    assert str(fen.bouton_decharger["state"]) == "normal"
    fen.decharger_du_jeu()
    assert jeu.emplacements[3] == JOUEUR and jeu.patch == "origine"
    assert boites.vues[-1] == ("showinfo", "Ta base est remise dans l'emplacement 3.")
    assert "chargée dans le jeu" not in fen.etiquette_etat["text"]
    assert str(fen.bouton_decharger["state"]) == "disabled"


def test_une_base_refusee_par_les_regles_demande_confirmation(racine, tmp_path, boites):
    fen, ed, jeu = fenetre_live(racine, tmp_path, forme=69)       # porte et totem dans un bloc
    boites.reponse = False
    fen.charger_dans_le_jeu()
    assert boites.vues == [("askyesno", "2 objet(s) refusé(s) par les règles : le jeu refusera « Essayer ». "
                                        "Charger quand même ?")]
    assert jeu.ecritures == []


def test_un_refus_du_jeu_s_affiche(racine, tmp_path, boites):
    fen, ed, jeu = fenetre_live(racine, tmp_path)
    jeu.editeur = True
    fen.charger_dans_le_jeu()
    assert boites.vues[-1][0] == "showerror" and boites.vues[-1][1].startswith("L'éditeur est ouvert")
    assert str(fen.racine["cursor"]) == ""


def test_quitter_propose_de_decharger(racine, tmp_path, boites, monkeypatch):
    fermee = []
    monkeypatch.setattr(racine, "destroy", lambda: fermee.append(True))
    fen, ed, jeu = fenetre_live(racine, tmp_path)
    fen.charger_dans_le_jeu()
    boites.reponse = None                                        # Annuler : on reste
    fen.quitter()
    assert fermee == [] and jeu.patch == "pose"
    boites.reponse = True                                        # Oui : decharger, puis fermer
    fen.quitter()
    assert fermee == [True] and jeu.emplacements[3] == JOUEUR


def test_chaque_texte_defini_est_utilise():
    # Ici et pas dans test_kotcm_textes : la fenetre, qui utilise la plupart des cles, vient en dernier.
    paquet = Path(__file__).resolve().parents[2] / "kotcm"
    code = "".join(p.read_text(encoding="utf-8") for p in paquet.rglob("*.py") if p.name != "textes.py")
    familles = ("type_", "abrev_", "col_", "champ_", "regle_")   # cles construites (type_8, col_x...)
    internes = ("type_inconnu", "abrev_inconnu")                   # utilisees par Traducteur lui-meme
    inutilisees = [c for c in TEXTES["fr"]
                   if not c.startswith(familles) and c not in internes and '"%s"' % c not in code]
    assert inutilisees == []
