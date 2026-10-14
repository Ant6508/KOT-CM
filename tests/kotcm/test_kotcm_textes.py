import ast
import json
import re
import string
from pathlib import Path

import pytest

from kotcm.catalogue import TYPES
from kotcm.textes import TEXTES, Traducteur, langue_initiale, sauver_langue

PAQUET = Path(__file__).resolve().parents[2] / "kotcm"


def _marqueurs(texte):
    return {nom for _, nom, _, _ in string.Formatter().parse(texte) if nom}


def test_memes_cles_dans_les_deux_langues():
    assert set(TEXTES["fr"]) == set(TEXTES["en"])


def test_memes_marqueurs_dans_les_deux_langues():
    assert [c for c in TEXTES["fr"] if _marqueurs(TEXTES["fr"][c]) != _marqueurs(TEXTES["en"][c])] == []


def test_chaque_cle_litterale_utilisee_existe():
    utilisees = set()
    for fichier in PAQUET.rglob("*.py"):
        utilisees |= set(re.findall(r"\bt\(\s*\"([a-z0-9_]+)\"\s*[,)]", fichier.read_text(encoding="utf-8")))
    assert utilisees and sorted(utilisees - set(TEXTES["fr"])) == []


def test_familles_de_cles_construites():
    # fenetre.py : t("col_" + c), t("champ_" + nom), t("regle_%d" % code)
    construites = (["col_" + c for c in ("id", "type", "x", "y", "verdict")]
                   + ["champ_" + n for n in ("type", "x", "y", "orientation", "vx", "vy")]
                   + ["regle_%d" % code for code in (1, 2, 3, 4)])
    assert [c for c in construites if c not in TEXTES["fr"]] == []


def test_chaque_type_a_un_nom_et_une_abreviation():
    manquants = [n for n in TYPES for l in TEXTES if "type_%d" % n not in TEXTES[l] or "abrev_%d" % n not in TEXTES[l]]
    assert manquants == []


def test_traducteur():
    tr = Traducteur("fr")
    assert tr.t("forme_commune", numero=69) == "n° 69, commune"
    assert tr.nom_type(8) == "scie" and tr.nom_type(99) == "type 99 (inconnu)"
    tr.langue = "en"
    assert tr.nom_type(8) == "saw" and tr.abrev_type(99) == "?"
    with pytest.raises(ValueError):
        tr.langue = "de"


def test_langue_initiale(tmp_path):
    pref = tmp_path / "kotcm.json"
    assert langue_initiale(None, pref, systeme=lambda: "fr") == "fr"
    sauver_langue("en", pref)
    assert json.loads(pref.read_text()) == {"langue": "en"}
    assert langue_initiale(None, pref, systeme=lambda: "fr") == "en"
    assert langue_initiale("fr", pref, systeme=lambda: "en") == "fr"
    pref.write_text("pas du json")
    assert langue_initiale(None, pref, systeme=lambda: "en") == "en"


def test_chaque_erreur_live_a_son_texte_et_ses_marqueurs():
    # ErreurLive("cle", nom=valeur...) : la cle existe, et ses marqueurs sont les noms passes.
    appels = []
    for fichier in PAQUET.rglob("*.py"):
        for noeud in ast.walk(ast.parse(fichier.read_text(encoding="utf-8"))):
            if isinstance(noeud, ast.Call) and getattr(noeud.func, "id", None) == "ErreurLive" and noeud.args:
                appels.append((noeud.args[0].value, {k.arg for k in noeud.keywords}))
    assert appels and [(cle, noms) for cle, noms in appels
                       if cle not in TEXTES["fr"] or _marqueurs(TEXTES["fr"][cle]) != noms] == []


def test_le_message_de_chargement_rappelle_les_deux_risques():
    # Spec, 9.3 et 9.4 : les gestes partent au serveur ; un piege non possede fait planter « Essayer ».
    assert "serveur" in TEXTES["fr"]["live_charge_ok"] and "possèdes" in TEXTES["fr"]["live_charge_ok"]
    assert "server" in TEXTES["en"]["live_charge_ok"] and "don't own" in TEXTES["en"]["live_charge_ok"]
