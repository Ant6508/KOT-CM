import re

import pytest

from kotcm.live import ErreurLive
from kotcm.live.session import AGENT, Connexion, Etat
from kotnoyau.frida_ import charger_agent, noms_utilises
from kotnoyau.table import Table

RPC_ETAT = {"ds": True, "courant": 3, "ok": True, "detail": None, "octets": "0a00", "patch": "origine",
            "editeur": False, "meme_fil": None}


class FauxScript:
    def __init__(self, exports):
        self.exports_sync = exports
        self.charge = self.decharge = False

    def load(self):
        self.charge = True

    def unload(self):
        self.decharge = True


class FausseSession:
    def __init__(self, exports):
        self.script = FauxScript(exports)
        self.detachee = False
        self.source = None

    def create_script(self, source):
        self.source = source
        return self.script

    def detach(self):
        self.detachee = True


class FauxAppareil:
    serial = "s"

    def __init__(self, exports, version_ok=True):
        self.session = FausseSession(exports)
        self.version_ok = version_ok
        self.serveur_prepare = False

    def verifier_version(self):
        if not self.version_ok:
            raise ErreurLive("live_version", trouvee="2.85 (1)", connues="2.84 (4755781)")
        return Table.pour(4755781)

    def preparer_serveur(self):
        self.serveur_prepare = True

    def pid_jeu(self):
        return 812

    def attacher(self, pid):
        assert pid == 812
        return self.session


class Exports:
    def __init__(self, **reponses):
        self.reponses = reponses
        self.appels = []

    def __getattr__(self, nom):
        def appel(*args):
            self.appels.append((nom, args))
            r = self.reponses[nom]
            if isinstance(r, Exception):
                raise r
            return r
        return appel


def test_etat_depuis_l_agent():
    e = Etat.depuis_agent(RPC_ETAT)
    assert e == Etat(ds_ok=True, emplacement=3, emplacement_ok=True, detail=None, octets=b"\x0a\x00",
                     patch="origine", editeur=False, meme_fil=None)


def test_connexion_ouvre_et_ferme_la_session():
    a = FauxAppareil(Exports(etat=RPC_ETAT))
    with Connexion(a) as jeu:
        assert (jeu.serial, jeu.pid) == ("s", 812) and a.serveur_prepare
        assert jeu.etat().octets == b"\x0a\x00"
    assert a.session.script.charge and a.session.script.decharge and a.session.detachee
    assert a.session.source == charger_agent(AGENT.read_text(encoding="utf-8"), Table.pour(4755781))


def test_garde_de_version_avant_toute_attache():
    a = FauxAppareil(Exports(), version_ok=False)
    with pytest.raises(ErreurLive) as e:
        with Connexion(a):
            pass
    assert e.value.cle == "live_version" and not a.serveur_prepare and a.session.source is None


def test_ecrire():
    ex = Exports(ecrire={"ecrit": True, "ok": True, "detail": None, "octets": "0a00"})
    with Connexion(FauxAppareil(ex)) as jeu:
        assert jeu.ecrire(3, b"\x0a\x00") == b"\x0a\x00"
    assert ex.appels == [("ecrire", (3, "0a00"))]
    ex.reponses["ecrire"] = {"ecrit": True, "ok": False, "detail": None, "octets": "0a"}
    with Connexion(FauxAppareil(ex)) as jeu:
        assert jeu.ecrire(3, b"\x0a\x00") is None


@pytest.mark.parametrize("detail,cle", [("editeur", "live_editeur_ouvert"),
                                        ("emplacement 3 : pas un Dungeon", "live_structure")])
def test_ecrire_refuse(detail, cle):
    ex = Exports(ecrire={"ecrit": False, "detail": detail})
    with Connexion(FauxAppareil(ex)) as jeu:
        with pytest.raises(ErreurLive) as e:
            jeu.ecrire(3, b"\x0a\x00")
    assert e.value.cle == cle


def test_patch_inconnu_et_erreurs_de_l_agent():
    ex = Exports(patcher="inconnu", etat=RuntimeError("Error: live_jeu_ne_dessine_pas"),
                 evenements=RuntimeError("boum"))
    with Connexion(FauxAppareil(ex)) as jeu:
        for appel, cle in ((lambda: jeu.patcher(True), "live_patch_inconnu"),
                           (jeu.etat, "live_jeu_ne_dessine_pas"),
                           (lambda: jeu.evenements(1), "live_agent")):
            with pytest.raises(ErreurLive) as e:
                appel()
            assert e.value.cle == cle


def test_l_agent_lit_ses_adresses_dans_la_table():
    source = AGENT.read_text(encoding="utf-8")
    assert noms_utilises(source) == ["dungeon_storage", "editeur_evenement", "editeur_image",
                                     "kotcm_patch_enregistrer", "parse_from_array", "serialize_to_string",
                                     "user_profile_ptr", "vt_dungeon", "vt_dungeon_obstacle", "vt_dungeon_storage"]
    assert "kotcm_patch_enregistrer: 0x1570c5f" in charger_agent(source, Table.pour(4755781))
    assert re.search(r"ORIGINE = \[0x0f, 0x84, 0xd2, 0x02, 0x00, 0x00\]", source)
    assert re.search(r"PATCHE = \[0xe9, 0xd3, 0x02, 0x00, 0x00, 0x90\]", source)
    assert set(re.findall(r"^  (\w+): function", source, re.M)) == {"etat", "ecrire", "patcher", "evenements"}
