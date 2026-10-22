# -*- coding: utf-8 -*-
"""Textes affiches, en francais et en anglais ; langue de depart et preference.

Exception a la convention ASCII du depot : les textes affiches portent leurs
accents. Aucun texte affiche n'est ecrit ailleurs : on passe par
`Traducteur.t(cle, **valeurs)`. Une troisieme langue = un dictionnaire de plus.
"""

from __future__ import annotations

import json
import locale
import os
from pathlib import Path

LANGUES = ("fr", "en")
PREFERENCES = Path.home() / ".kotcm.json"

TEXTES = {
    "fr": {
        "titre": "kotcm — mode créatif",
        "nouvelle": "Nouvelle…",
        "ouvrir": "Ouvrir .bin",
        "enregistrer": "Enregistrer .bin",
        "annuler": "Annuler",
        "libre": "placement libre",
        "langue": "Langue",
        "charger": "Charger dans le jeu",
        "live_adb_absent": "adb introuvable : installe MEmu, ou définis KOTCM_ADB, ou ajoute le dossier d'adb au PATH.",
        "live_adb": "adb a échoué : {detail}",
        "live_appareil": "Choisis l'appareil avec --serial ou ANDROID_SERIAL (connectés : {appareils}).",
        "live_version": "Le jeu installé est en {trouvee} ; kotcm ne connaît que {connues}.",
        "live_jeu_absent": "King of Thieves ne tourne pas.",
        "live_autre_serveur": "Un autre frida-server tourne ({serveurs}) : arrête-le d'abord (redémarre MEmu).",
        "live_telechargement": "frida-server {version} manque ou n'est pas le bon, et n'a pas pu être téléchargé ({detail}). Télécharge-le à la main : {url} ; décompresse-le (7-Zip) et pose le fichier ici : {chemin}",
        "live_dossier_a_la_place": "Un dossier occupe la place du fichier frida-server : {chemin}. Supprime-le (ou sors-en le fichier frida-server et pose-le à sa place), puis recommence.",
        "live_serveur_lance": "frida-server ne démarre pas ({chemin}).",
        "live_frida_absent": "frida n'est pas installé : pip install frida=={attendue}",
        "live_frida_version": "frida {trouvee} est installé, kotcm attend {attendue} : pip install frida=={attendue}",
        "live_attache": "Impossible de s'attacher au jeu : {detail}",
        "live_agent": "L'agent a échoué : {detail}",
        "live_jeu_ne_dessine_pas": "Le jeu ne dessine plus (en arrière-plan ?) : rien n'a été écrit.",
        "live_structure": "Mémoire du jeu inattendue ({detail}) : rien n'a été écrit.",
        "live_editeur_ouvert": "L'éditeur est ouvert : reviens à l'accueil (flèche retour, sans enregistrer), puis recommence.",
        "live_patch_inconnu": "Le code d'« Enregistrer » n'est pas celui attendu : rien n'a été écrit.",
        "live_patch_orphelin": "« Enregistrer » est déjà neutralisé, mais kotcm n'a pas de copie de ta base pour ce lancement du jeu. Redémarre le jeu : il rechargera ta base du serveur.",
        "live_emplacement_change": "L'emplacement courant est passé de {avant} à {maintenant} : décharge d'abord.",
        "live_ecriture": "Le jeu n'a pas relu la base à l'identique ({detail}) : ta base est remise en place.",
        "live_remise": "Ta base n'a pas pu être remise ; sa copie est dans {sauvegarde}. Redémarre le jeu : il rechargera ta base du serveur.",
        "live_rien_a_decharger": "Aucune base kotcm n'est chargée.",
        "live_redemarre": "Le jeu a redémarré depuis le chargement : ta base du serveur est en place, rien à décharger.",
        "live_charge_ok": "Base chargée dans l'emplacement {emplacement}. À l'accueil, appuie sur « MODIFIER », puis « Essayer ». Ne déplace aucun objet dans l'éditeur : chaque geste part au serveur. Un piège que tu ne possèdes pas peut faire planter « Essayer » : le jeu redémarre, rien n'est perdu. « Enregistrer » est neutralisé jusqu'au déchargement.",
        "live_decharge_ok": "Ta base est remise dans l'emplacement {emplacement}.",
        "decharger": "Décharger du jeu",
        "etat_live": " · chargée dans le jeu (emplacement {emplacement})",
        "live_problemes": "{p} objet(s) refusé(s) par les règles : le jeu refusera « Essayer ». Charger quand même ?",
        "live_quitter": "Une base kotcm est chargée dans le jeu. La décharger avant de quitter ?",
        "forme": "Forme",
        "forme_commune": "n° {numero}, commune",
        "forme_moddee": "moddée n° {numero}, par {auteur}",
        "forme_inconnue": "forme inconnue",
        "objets": "Objets",
        "col_id": "id",
        "col_type": "type",
        "col_x": "x",
        "col_y": "y",
        "col_verdict": "règle",
        "selection_objet": "Sélection : {nom}",
        "aucune_selection": "(aucune)",
        "champ_type": "type",
        "champ_x": "x",
        "champ_y": "y",
        "champ_orientation": "orientation",
        "champ_vx": "vx",
        "champ_vy": "vy",
        "autres_champs": "autres champs",
        "regles": "Règles",
        "regle_1": "Le piège est sur le totem",
        "regle_2": "Le piège est trop près de la porte !",
        "regle_3": "Le piège n'a pas de paroi",
        "regle_4": "L'objet est derrière le terrain",
        "regle_ligne": "{nom} ({x}, {y}) : {message}",
        "verdict_non_verifie": "non vérifié",
        "tout_valide": "{n} objet(s) valides",
        "etat": "{fichier} · {modif} · {n} objets · {p} problème(s) · {nv} non vérifié(s)",
        "modifiee": "modifiée",
        "a_jour": "à jour",
        "nouvelle_base": "nouvelle base",
        "choisir_forme": "Choisir une forme",
        "choisir": "Choisir",
        "erreur": "Erreur",
        "erreur_lecture": "Fichier illisible : {erreur}",
        "erreur_saisie": "Saisie invalide : {erreur}",
        "retrait_interdit": "La porte et le totem ne se retirent pas.",
        "modele_suppose": "modèle supposé",
        "type_inconnu": "type {numero} (inconnu)",
        "abrev_inconnu": "?",
        "fichiers_bin": "Donjons (.bin)",
        "type_1": "porte", "abrev_1": "P",
        "type_2": "totem", "abrev_2": "T",
        "type_3": "bloc", "abrev_3": "Bl",
        "type_4": "canon", "abrev_4": "C",
        "type_6": "canon chercheur", "abrev_6": "CC",
        "type_7": "anti-gravité", "abrev_7": "AG",
        "type_8": "scie", "abrev_8": "S",
        "type_9": "garde rouge", "abrev_9": "GR",
        "type_10": "garde bleu", "abrev_10": "GB",
        "type_11": "plateforme", "abrev_11": "Pl",
        "type_12": "trampoline", "abrev_12": "Tr",
        "type_13": "plateforme cassable", "abrev_13": "PC",
        "type_14": "oiseau chercheur", "abrev_14": "Oi",
        "type_17": "gemme", "abrev_17": "g",
        "type_18": "gemme", "abrev_18": "g",
        "type_21": "ricochet", "abrev_21": "Ri",
        "type_39": "dragon", "abrev_39": "Dr",
        "type_40": "fourneau", "abrev_40": "Fo",
        "type_41": "scie aléatoire", "abrev_41": "SA",
        "type_42": "warder", "abrev_42": "Wa",
        "type_44": "bloodhound", "abrev_44": "BH",
        "type_45": "bonbon", "abrev_45": "Bo",
        "type_46": "canon électrique", "abrev_46": "CE",
        "type_47": "araignée", "abrev_47": "Ar",
        "type_48": "hopblob", "abrev_48": "Hb",
    },
    "en": {
        "titre": "kotcm — creative mode",
        "nouvelle": "New…",
        "ouvrir": "Open .bin",
        "enregistrer": "Save .bin",
        "annuler": "Undo",
        "libre": "free placement",
        "langue": "Language",
        "charger": "Load into the game",
        "live_adb_absent": "adb not found: install MEmu, or set KOTCM_ADB, or add adb's folder to the PATH.",
        "live_adb": "adb failed: {detail}",
        "live_appareil": "Choose the device with --serial or ANDROID_SERIAL (connected: {appareils}).",
        "live_version": "The installed game is {trouvee}; kotcm only knows {connues}.",
        "live_jeu_absent": "King of Thieves is not running.",
        "live_autre_serveur": "Another frida-server is running ({serveurs}): stop it first (restart MEmu).",
        "live_telechargement": "frida-server {version} is missing or not the right one, and could not be downloaded ({detail}). Download it by hand: {url}; unpack it (7-Zip) and put the file here: {chemin}",
        "live_dossier_a_la_place": "A folder is in the place of the frida-server file: {chemin}. Delete it (or take the frida-server file out of it and put it in its place), then try again.",
        "live_serveur_lance": "frida-server does not start ({chemin}).",
        "live_frida_absent": "frida is not installed: pip install frida=={attendue}",
        "live_frida_version": "frida {trouvee} is installed, kotcm expects {attendue}: pip install frida=={attendue}",
        "live_attache": "Cannot attach to the game: {detail}",
        "live_agent": "The agent failed: {detail}",
        "live_jeu_ne_dessine_pas": "The game is not drawing (in the background?): nothing was written.",
        "live_structure": "Unexpected game memory ({detail}): nothing was written.",
        "live_editeur_ouvert": "The editor is open: go back to the home screen (back arrow, without saving), then try again.",
        "live_patch_inconnu": "The “Save” code is not the expected one: nothing was written.",
        "live_patch_orphelin": "“Save” is already disabled, but kotcm has no copy of your base for this game launch. Restart the game: it will reload your base from the server.",
        "live_emplacement_change": "The current slot changed from {avant} to {maintenant}: unload first.",
        "live_ecriture": "The game did not read the base back identically ({detail}): your base is put back.",
        "live_remise": "Your base could not be put back; its copy is in {sauvegarde}. Restart the game: it will reload your base from the server.",
        "live_rien_a_decharger": "No kotcm base is loaded.",
        "live_redemarre": "The game restarted since loading: your server base is back, nothing to unload.",
        "live_charge_ok": "Base loaded into slot {emplacement}. From the home screen, tap “EDIT”, then “Try”. Do not move any object in the editor: every move is sent to the server. A trap you don't own may crash “Try”: the game restarts, nothing is lost. “Save” is disabled until you unload.",
        "live_decharge_ok": "Your base is back in slot {emplacement}.",
        "decharger": "Unload from the game",
        "etat_live": " · loaded in the game (slot {emplacement})",
        "live_problemes": "{p} object(s) break the placement rules: the game will refuse “Try”. Load anyway?",
        "live_quitter": "A kotcm base is loaded in the game. Unload it before quitting?",
        "forme": "Shape",
        "forme_commune": "#{numero}, common",
        "forme_moddee": "modded #{numero}, by {auteur}",
        "forme_inconnue": "unknown shape",
        "objets": "Objects",
        "col_id": "id",
        "col_type": "type",
        "col_x": "x",
        "col_y": "y",
        "col_verdict": "rule",
        "selection_objet": "Selection: {nom}",
        "aucune_selection": "(none)",
        "champ_type": "type",
        "champ_x": "x",
        "champ_y": "y",
        "champ_orientation": "orientation",
        "champ_vx": "vx",
        "champ_vy": "vy",
        "autres_champs": "other fields",
        "regles": "Rules",
        "regle_1": "The trap is on the totem",
        "regle_2": "The trap is too close to the door!",
        "regle_3": "The trap has no wall to stand on",
        "regle_4": "The object is behind the terrain",
        "regle_ligne": "{nom} ({x}, {y}): {message}",
        "verdict_non_verifie": "not verified",
        "tout_valide": "{n} valid object(s)",
        "etat": "{fichier} · {modif} · {n} objects · {p} problem(s) · {nv} not verified",
        "modifiee": "modified",
        "a_jour": "saved",
        "nouvelle_base": "new base",
        "choisir_forme": "Choose a shape",
        "choisir": "Choose",
        "erreur": "Error",
        "erreur_lecture": "Unreadable file: {erreur}",
        "erreur_saisie": "Invalid input: {erreur}",
        "retrait_interdit": "The door and the totem cannot be removed.",
        "modele_suppose": "assumed model",
        "type_inconnu": "type {numero} (unknown)",
        "abrev_inconnu": "?",
        "fichiers_bin": "Dungeons (.bin)",
        "type_1": "door", "abrev_1": "D",
        "type_2": "totem", "abrev_2": "T",
        "type_3": "block", "abrev_3": "Bk",
        "type_4": "cannon", "abrev_4": "C",
        "type_6": "homing cannon", "abrev_6": "HC",
        "type_7": "anti-gravity", "abrev_7": "AG",
        "type_8": "saw", "abrev_8": "S",
        "type_9": "red guard", "abrev_9": "RG",
        "type_10": "blue guard", "abrev_10": "BG",
        "type_11": "platform", "abrev_11": "Pl",
        "type_12": "trampoline", "abrev_12": "Tr",
        "type_13": "broken platform", "abrev_13": "BP",
        "type_14": "seeker bird", "abrev_14": "Bi",
        "type_17": "gem", "abrev_17": "g",
        "type_18": "gem", "abrev_18": "g",
        "type_21": "ricochet", "abrev_21": "Ri",
        "type_39": "dragon", "abrev_39": "Dr",
        "type_40": "furnace", "abrev_40": "Fu",
        "type_41": "random saw", "abrev_41": "RS",
        "type_42": "warder", "abrev_42": "Wa",
        "type_44": "bloodhound", "abrev_44": "BH",
        "type_45": "candy", "abrev_45": "Ca",
        "type_46": "electro cannon", "abrev_46": "EC",
        "type_47": "spider", "abrev_47": "Sp",
        "type_48": "hopblob", "abrev_48": "Hb",
    },
}


class Traducteur:
    def __init__(self, langue: str = "fr"):
        self.langue = langue

    @property
    def langue(self) -> str:
        return self._langue

    @langue.setter
    def langue(self, langue: str) -> None:
        if langue not in LANGUES:
            raise ValueError("langue %r inconnue (attendu : %s)" % (langue, ", ".join(LANGUES)))
        self._langue = langue

    def t(self, cle: str, **valeurs) -> str:
        return TEXTES[self._langue][cle].format(**valeurs)

    def nom_type(self, numero: int) -> str:
        cle = "type_%d" % numero
        return self.t(cle) if cle in TEXTES[self._langue] else self.t("type_inconnu", numero=numero)

    def abrev_type(self, numero: int) -> str:
        cle = "abrev_%d" % numero
        return self.t(cle) if cle in TEXTES[self._langue] else self.t("abrev_inconnu")


def _langue_windows() -> str | None:
    try:
        import ctypes
        identifiant = ctypes.windll.kernel32.GetUserDefaultUILanguage()
    except (AttributeError, OSError):
        return None
    return "fr" if identifiant & 0x3FF == 0x0C else "en"


def langue_systeme() -> str:
    """'fr' si le systeme est en francais, 'en' dans tous les autres cas."""
    for nom in (os.environ.get("LANG"), locale.getlocale()[0]):
        if nom:
            return "fr" if nom.lower().startswith(("fr", "french")) else "en"
    return _langue_windows() or "en"


def langue_initiale(option: str | None, preferences: Path = PREFERENCES, systeme=langue_systeme) -> str:
    """--langue si donnee, sinon le dernier choix enregistre, sinon la langue du systeme."""
    if option:
        return option
    try:
        langue = json.loads(Path(preferences).read_text(encoding="utf-8")).get("langue")
    except (OSError, ValueError, AttributeError):
        langue = None
    return langue if langue in LANGUES else systeme()


def sauver_langue(langue: str, preferences: Path = PREFERENCES) -> None:
    try:
        Path(preferences).write_text(json.dumps({"langue": langue}), encoding="utf-8")
    except OSError:
        pass        # une preference perdue ne doit pas empecher de travailler
