from datetime import datetime
from pathlib import Path

import pytest

from kotcm.live import ErreurLive, dossier_donnees
from kotcm.live.chargeur import Chargeur, empreinte
from kotcm_faux_jeu import JOUEUR, KOTCM, FauxJeuLive


def chargeur(jeu, dossier):
    return Chargeur(jeu, dossier=dossier, horloge=lambda: datetime(2026, 10, 14, 9, 30, 0))


def sauvegardes(dossier):
    return sorted(p.name for p in (dossier / "sauvegardes").glob("*.bin"))


def test_charger_sauvegarde_la_base_du_joueur_pose_le_patch_puis_ecrit(tmp_path):
    jeu = FauxJeuLive()
    ch = chargeur(jeu, tmp_path)
    assert ch.chargee() is None
    assert ch.charger(KOTCM) == 3
    assert jeu.emplacements[3] == KOTCM and jeu.patch == "pose"
    assert sauvegardes(tmp_path) == ["emplacement3_20261014-093000.bin"]
    assert (tmp_path / "sauvegardes" / "emplacement3_20261014-093000.bin").read_bytes() == JOUEUR
    c = ch.chargement()
    assert (c.serial, c.pid, c.emplacement, c.empreinte) == ("127.0.0.1:5555", 812, 3, empreinte(KOTCM))
    assert ch.chargee() == 3


def test_recharger_garde_la_premiere_sauvegarde(tmp_path):
    jeu = FauxJeuLive()
    ch = chargeur(jeu, tmp_path)
    ch.charger(KOTCM)
    ch.charger(b"une autre base kotcm")
    assert jeu.emplacements[3] == b"une autre base kotcm"
    assert sauvegardes(tmp_path) == ["emplacement3_20261014-093000.bin"]
    assert ch.chargement().empreinte == empreinte(b"une autre base kotcm")


def test_decharger_remet_la_base_du_joueur_a_l_octet_pres(tmp_path):
    jeu = FauxJeuLive()
    ch = chargeur(jeu, tmp_path)
    ch.charger(KOTCM)
    assert ch.decharger() == 3
    assert jeu.emplacements[3] == JOUEUR and jeu.patch == "origine"
    assert ch.chargee() is None and not ch.fichier.exists()
    assert sauvegardes(tmp_path) == ["emplacement3_20261014-093000.bin"]     # jamais effacee


@pytest.mark.parametrize("panne,cle", [("ds_ok", "live_structure"), ("editeur", "live_editeur_ouvert"),
                                       ("patch", "live_patch_inconnu")])
def test_refus_sans_rien_ecrire(tmp_path, panne, cle):
    jeu = FauxJeuLive()
    if panne == "ds_ok":
        jeu.ds_ok = False
    elif panne == "editeur":
        jeu.editeur = True
    else:
        jeu.patch = "inconnu"
    with pytest.raises(ErreurLive) as e:
        chargeur(jeu, tmp_path).charger(KOTCM)
    assert e.value.cle == cle
    assert jeu.ecritures == [] and jeu.emplacements[3] == JOUEUR
    assert not (tmp_path / "live.json").exists() and not (tmp_path / "sauvegardes").exists()


def test_ecriture_relue_differente_remet_la_base_du_joueur(tmp_path):
    jeu = FauxJeuLive()
    jeu.refus = 1
    ch = chargeur(jeu, tmp_path)
    with pytest.raises(ErreurLive) as e:
        ch.charger(KOTCM)
    assert (e.value.cle, e.value.valeurs) == ("live_ecriture",
                                              {"detail": "%d octets relus au lieu de %d" % (len(KOTCM) - 1, len(KOTCM))})
    assert jeu.emplacements[3] == JOUEUR and jeu.patch == "origine" and ch.chargee() is None


def test_remise_impossible_garde_le_patch_et_l_etat(tmp_path):
    jeu = FauxJeuLive()
    ch = chargeur(jeu, tmp_path)
    ch.charger(KOTCM)
    jeu.refus = 1
    with pytest.raises(ErreurLive) as e:
        ch.decharger()
    assert e.value.cle == "live_remise" and jeu.patch == "pose" and ch.chargee() == 3


def test_jeu_redemarre_depuis_le_chargement(tmp_path):
    ch = chargeur(FauxJeuLive(), tmp_path)
    ch.charger(KOTCM)
    relance = FauxJeuLive(pid=900)                      # patch disparu, base du serveur rechargee
    ch.connecter = relance
    with pytest.raises(ErreurLive) as e:
        ch.decharger()
    assert e.value.cle == "live_redemarre" and ch.chargee() is None
    ch.horloge = lambda: datetime(2026, 10, 14, 10, 0, 0)
    ch.charger(KOTCM)                                   # nouvelle sauvegarde, prise sur le jeu relance
    assert sauvegardes(tmp_path) == ["emplacement3_20261014-093000.bin", "emplacement3_20261014-100000.bin"]


def test_patch_pose_sans_chargement_connu(tmp_path):
    jeu = FauxJeuLive(patch="pose")
    with pytest.raises(ErreurLive) as e:
        chargeur(jeu, tmp_path).charger(KOTCM)
    assert e.value.cle == "live_patch_orphelin" and jeu.ecritures == []


def test_rien_a_decharger(tmp_path):
    with pytest.raises(ErreurLive) as e:
        chargeur(FauxJeuLive(), tmp_path).decharger()
    assert e.value.cle == "live_rien_a_decharger"


def test_emplacement_change_entre_deux_chargements(tmp_path):
    jeu = FauxJeuLive()
    ch = chargeur(jeu, tmp_path)
    ch.charger(KOTCM)
    jeu.courant = 2
    with pytest.raises(ErreurLive) as e:
        ch.charger(KOTCM)
    assert (e.value.cle, e.value.valeurs) == ("live_emplacement_change", {"avant": 3, "maintenant": 2})
    assert ch.decharger() == 3                          # remet l'emplacement charge, pas le courant
    assert jeu.emplacements[3] == JOUEUR and jeu.emplacements[2] == b"autre emplacement"


def test_dossier_de_donnees_par_defaut_ou_kotcm_dossier(tmp_path, monkeypatch):
    assert dossier_donnees({}) == Path.home() / ".kotcm"
    assert dossier_donnees({"KOTCM_DOSSIER": str(tmp_path)}) == tmp_path
    monkeypatch.setenv("KOTCM_DOSSIER", str(tmp_path / "ailleurs"))
    assert Chargeur(FauxJeuLive).dossier == tmp_path / "ailleurs"
