# -*- coding: utf-8 -*-
"""La fenetre tkinter (disposition B de la spec) : donjon a gauche, panneau a droite.

Ne fait que dessiner l'etat d'`Edition` et lui transmettre les gestes. Tous
les textes passent par le Traducteur ; changer de langue reconstruit les
widgets sans toucher a la base ouverte. « Charger dans le jeu » et
« Decharger » passent par le `Chargeur` de kotcm.live (phase 2).
"""

from __future__ import annotations

import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from kotcm.catalogue import GEMMES, PORTE, TOTEM, TYPES, posables, type_de
from kotcm.edition import Edition, ErreurLecture
from kotcm.live import ErreurLive
from kotcm.protobuf import HAUTEUR, LARGEUR
from kotcm.regles import base_2x2, zone_porte, zone_totem
from kotcm.textes import LANGUES, PREFERENCES, Traducteur, sauver_langue

ECHELLE = 0.8               # pixels ecran par pixel du donjon
MARGE = 16                  # epaisseur des murs dessines
RAYON = 11                  # rayon d'une pastille, en pixels ecran
CARREAU = 64
LARGEUR_PX, HAUTEUR_PX = 896, 512
CHAMPS_FICHE = ("x", "y", "orientation", "vx", "vy")
CHAMPS_BRUTS = ("f6", "f7", "f9", "f13", "f14", "f15", "f16")    # sens inconnu : noms bruts
BOOLEENS = ("f7", "f15")
COULEURS = {"mur": "#6b4f2a", "fond": "#2b2b2b", "bloc": "#8a6a3c", "trait": "#444444",
            "selection": "#ffd400", "refus": "#ff1744", "zone": "#ff8a80"}


def vers_ecran(x: float, y: float) -> tuple[float, float]:
    return MARGE + x * ECHELLE, MARGE + y * ECHELLE


def vers_donjon(xe: float, ye: float) -> tuple[int, int]:
    return round((xe - MARGE) / ECHELLE), round((ye - MARGE) / ECHELLE)


def _entier(texte: str) -> int | None:
    texte = texte.strip()
    return int(texte) if texte else None


class Fenetre:
    def __init__(self, racine: tk.Tk, edition: Edition, traducteur: Traducteur, preferences=PREFERENCES,
                 chargeur=None):
        self.racine, self.ed, self.tr, self.preferences = racine, edition, traducteur, preferences
        self.chargeur = chargeur              # kotcm.live.chargeur.Chargeur ; None : pas de chargement live
        self.arme: int | None = None          # type choisi dans la palette, pose au prochain clic
        self._glisse = None                   # (ident, x0 ecran, y0 ecran, dernier x, dernier y)
        self.libre = tk.BooleanVar(value=edition.libre)
        self._bruts_visibles = False
        self.racine.bind("<Control-z>", lambda e: self.annuler())
        self.racine.protocol("WM_DELETE_WINDOW", self.quitter)
        self.construire()

    # --- construction --------------------------------------------------------

    def construire(self) -> None:
        for enfant in self.racine.winfo_children():
            enfant.destroy()
        t = self.tr.t
        self.racine.title(t("titre"))

        barre = ttk.Frame(self.racine, padding=4)
        barre.pack(side="top", fill="x")
        ttk.Button(barre, text=t("nouvelle"), command=self.choisir_forme).pack(side="left")
        ttk.Button(barre, text=t("ouvrir"), command=self.ouvrir).pack(side="left")
        ttk.Button(barre, text=t("enregistrer"), command=self.enregistrer).pack(side="left")
        ttk.Button(barre, text=t("annuler"), command=self.annuler).pack(side="left", padx=(8, 0))
        ttk.Checkbutton(barre, text=t("libre"), variable=self.libre,
                        command=self._basculer_libre).pack(side="left", padx=8)
        langue = ttk.Menubutton(barre, text=t("langue"))
        menu = tk.Menu(langue, tearoff=False)
        for code in LANGUES:
            menu.add_command(label=code, command=lambda c=code: self.changer_langue(c))
        langue["menu"] = menu
        langue.pack(side="left")
        self.bouton_decharger = ttk.Button(barre, text=t("decharger"), command=self.decharger_du_jeu)
        self.bouton_decharger.pack(side="right")
        self.bouton_charger = ttk.Button(barre, text=t("charger"), command=self.charger_dans_le_jeu)
        self.bouton_charger.pack(side="right")

        centre = ttk.Frame(self.racine, padding=4)
        centre.pack(side="top", fill="both", expand=True)
        gauche = ttk.Frame(centre)
        gauche.pack(side="left", fill="y")
        self.canevas = tk.Canvas(gauche, width=LARGEUR_PX * ECHELLE + 2 * MARGE,
                                 height=HAUTEUR_PX * ECHELLE + 2 * MARGE, highlightthickness=0)
        self.canevas.pack(side="top")
        self.canevas.bind("<ButtonPress-1>", self._appui)
        self.canevas.bind("<B1-Motion>", self._glisser)
        self.canevas.bind("<ButtonRelease-1>", self._relache)
        self.canevas.bind("<ButtonPress-3>", self._retirer_sous)
        palette = ttk.Frame(gauche)
        palette.pack(side="top", fill="x", pady=4)
        for i, numero in enumerate(posables()):
            texte = self.tr.nom_type(numero) + ("" if self.ed.modeles.est_mesure(numero) else " *")
            ttk.Button(palette, text=texte, command=lambda n=numero: self._armer(n)).grid(
                row=i // 6, column=i % 6, sticky="ew")
        ttk.Label(gauche, text="* " + t("modele_suppose"), foreground="#666666").pack(anchor="w")

        panneau = ttk.Frame(centre, padding=(8, 0))
        panneau.pack(side="left", fill="both", expand=True)
        ttk.Label(panneau, text=t("forme"), font=("TkDefaultFont", 9, "bold")).pack(anchor="w")
        self.etiquette_forme = ttk.Label(panneau)
        self.etiquette_forme.pack(anchor="w")
        ttk.Label(panneau, text=t("objets"), font=("TkDefaultFont", 9, "bold")).pack(anchor="w", pady=(6, 0))
        colonnes = ("id", "type", "x", "y", "verdict")
        self.liste = ttk.Treeview(panneau, columns=colonnes, show="headings", height=10)
        for c, largeur in zip(colonnes, (30, 130, 45, 45, 55)):
            self.liste.heading(c, text=t("col_" + c))
            self.liste.column(c, width=largeur, anchor="w")
        self.liste.pack(anchor="w", fill="x")
        self.liste.bind("<<TreeviewSelect>>", self._choix_liste)

        self.etiquette_selection = ttk.Label(panneau, font=("TkDefaultFont", 9, "bold"))
        self.etiquette_selection.pack(anchor="w", pady=(6, 0))
        fiche = ttk.Frame(panneau)
        fiche.pack(anchor="w")
        ttk.Label(fiche, text=t("champ_type")).grid(row=0, column=0, sticky="w")
        # Ni porte ni totem dans la liste : il y en a toujours exactement un de chaque.
        self.choix_type = ttk.Combobox(fiche, width=24, state="readonly",
                                       values=["%d — %s" % (n, self.tr.nom_type(n)) for n in TYPES
                                               if n not in (PORTE, TOTEM)])
        self.choix_type.grid(row=0, column=1, sticky="w")
        self.choix_type.bind("<<ComboboxSelected>>", lambda e: self._appliquer_fiche())
        self.saisies = {}
        for i, nom in enumerate(CHAMPS_FICHE, start=1):
            ttk.Label(fiche, text=t("champ_" + nom)).grid(row=i, column=0, sticky="w")
            saisie = ttk.Entry(fiche, width=10)
            saisie.grid(row=i, column=1, sticky="w")
            saisie.bind("<Return>", lambda e: self._appliquer_fiche())
            self.saisies[nom] = saisie
        self.bouton_bruts = ttk.Button(panneau, command=self._basculer_bruts)
        self.bouton_bruts.pack(anchor="w", pady=(4, 0))
        self.cadre_bruts = ttk.Frame(panneau)
        for i, nom in enumerate(CHAMPS_BRUTS):
            ttk.Label(self.cadre_bruts, text=nom).grid(row=i // 4, column=2 * (i % 4), sticky="w")
            saisie = ttk.Entry(self.cadre_bruts, width=5)
            saisie.grid(row=i // 4, column=2 * (i % 4) + 1, sticky="w", padx=(2, 6))
            saisie.bind("<Return>", lambda e: self._appliquer_fiche())
            self.saisies[nom] = saisie
        self._montrer_bruts(self._bruts_visibles)

        ttk.Label(panneau, text=t("regles"), font=("TkDefaultFont", 9, "bold")).pack(anchor="w", pady=(6, 0))
        self.etiquette_regles = ttk.Label(panneau, justify="left", wraplength=300)
        self.etiquette_regles.pack(anchor="w")

        self.etiquette_etat = ttk.Label(self.racine, relief="sunken", padding=2)
        self.etiquette_etat.pack(side="bottom", fill="x")
        self.rafraichir()

    # --- dessin ------------------------------------------------------------------

    def rafraichir(self) -> None:
        self._dessiner()
        self._remplir_panneau()

    def _dessiner(self) -> None:
        c = self.canevas
        c.delete("all")
        l, h = LARGEUR_PX * ECHELLE + 2 * MARGE, HAUTEUR_PX * ECHELLE + 2 * MARGE
        c.create_rectangle(0, 0, l, h, fill=COULEURS["mur"], width=0)
        c.create_rectangle(*vers_ecran(0, 0), *vers_ecran(LARGEUR_PX, HAUTEUR_PX), fill=COULEURS["fond"], width=0)
        for k in range(1, LARGEUR_PX // CARREAU):
            c.create_line(*vers_ecran(k * CARREAU, 0), *vers_ecran(k * CARREAU, HAUTEUR_PX),
                          fill=COULEURS["trait"], dash=(1, 3))
        for k in range(1, HAUTEUR_PX // CARREAU):
            c.create_line(*vers_ecran(0, k * CARREAU), *vers_ecran(LARGEUR_PX, k * CARREAU),
                          fill=COULEURS["trait"], dash=(1, 3))
        if self.ed.base is None:
            return
        donjon = self.ed.base.donjon
        grille = donjon.grille or 0
        for r in range(HAUTEUR):
            for col in range(LARGEUR):
                if grille >> (r * LARGEUR + col) & 1:
                    c.create_rectangle(*vers_ecran(col * 128, r * 128), *vers_ecran((col + 1) * 128, (r + 1) * 128),
                                       fill=COULEURS["bloc"], outline=COULEURS["mur"])
        self._dessiner_zones()
        verdicts = self.ed.verdicts()
        for o in donjon.obstacles:
            t = type_de(o.type)
            v = verdicts.get(o.ident)
            if o.ident == self.ed.selection:
                bord, epaisseur = COULEURS["selection"], 3
            elif v is not None and v.code:
                bord, epaisseur = COULEURS["refus"], 3
            else:
                bord, epaisseur = "black", 1
            etiquette = "o%d" % o.ident
            if t.case:
                bc, br = base_2x2(o)
                x0, y0 = vers_ecran(bc * CARREAU, br * CARREAU)
                x1, y1 = vers_ecran((bc + 2) * CARREAU, (br + 2) * CARREAU)
            else:
                xe, ye = vers_ecran(o.x, o.y)
                r = RAYON / 2 if o.type in GEMMES else RAYON
                x0, y0, x1, y1 = xe - r, ye - r, xe + r, ye + r
            forme = c.create_rectangle if t.case else c.create_oval
            forme(x0, y0, x1, y1, fill=t.couleur, outline=bord, width=epaisseur, tags=(etiquette,))
            if o.type not in GEMMES:
                c.create_text((x0 + x1) / 2, (y0 + y1) / 2, text=self.tr.abrev_type(o.type),
                              fill="white", font=("TkDefaultFont", 8, "bold"), tags=(etiquette,))

    def _dessiner_zones(self) -> None:
        """Zones interdites de la porte et du totem quand un piege est selectionne."""
        if self.ed.selection is None:
            return
        o = self.ed.base.obstacle(self.ed.selection)
        if o.type in (PORTE, TOTEM) or o.type in GEMMES:
            return
        for objet in self.ed.base.donjon.obstacles:
            if objet.type in (PORTE, TOTEM):
                zc, zr, zl, zh = (zone_porte if objet.type == PORTE else zone_totem)(objet)
                self.canevas.create_rectangle(*vers_ecran(zc * CARREAU, zr * CARREAU),
                                              *vers_ecran((zc + zl) * CARREAU, (zr + zh) * CARREAU),
                                              outline=COULEURS["zone"], dash=(4, 2), stipple="gray25",
                                              fill=COULEURS["zone"])

    def _remplir_panneau(self) -> None:
        t, ed = self.tr.t, self.ed
        forme = ed.forme()
        if forme is None:
            self.etiquette_forme["text"] = t("forme_inconnue") if ed.base else ""
        elif forme.origine == "commune":
            self.etiquette_forme["text"] = t("forme_commune", numero=forme.numero)
        else:
            self.etiquette_forme["text"] = t("forme_moddee", numero=forme.numero, auteur=forme.auteur)
        self.liste.delete(*self.liste.get_children())
        verdicts = ed.verdicts()
        lignes = []
        if ed.base:
            for o in ed.base.donjon.obstacles:
                v = verdicts.get(o.ident)
                if v is None:
                    symbole = ""
                else:
                    symbole = ("✖ %d" % v.code if v.code else "✔") + ("" if v.verifie else " ?")
                    if v.code:
                        ligne = t("regle_ligne", nom=self.tr.nom_type(o.type), x=o.x, y=o.y,
                                  message=t("regle_%d" % v.code))
                        lignes.append(ligne + ("" if v.verifie else " — " + t("verdict_non_verifie")))
                self.liste.insert("", "end", iid=str(o.ident),
                                  values=(o.ident, self.tr.nom_type(o.type), o.x, o.y, symbole))
        if ed.selection is not None:
            self.liste.selection_set(str(ed.selection))
        self._remplir_fiche()
        valides = sum(1 for v in verdicts.values() if not v.code)
        self.etiquette_regles["text"] = "\n".join(lignes) if lignes else (
            t("tout_valide", n=valides) if ed.base else "")
        r = ed.resume()
        fichier = ed.chemin_sortie or ed.chemin_ouvert
        etat = t("etat", fichier=os.path.basename(fichier) if fichier else t("nouvelle_base"),
                 modif=t("modifiee") if ed.modifiee else t("a_jour"),
                 n=r.objets, p=r.problemes, nv=r.non_verifies)
        chargee = self.chargeur.chargee() if self.chargeur else None
        if chargee is not None:
            etat += t("etat_live", emplacement=chargee)
        self.etiquette_etat["text"] = etat
        self.bouton_charger["state"] = "normal" if self.chargeur and ed.base else "disabled"
        self.bouton_decharger["state"] = "normal" if chargee is not None else "disabled"

    def _remplir_fiche(self) -> None:
        o = self.ed.base.obstacle(self.ed.selection) if self.ed.selection is not None else None
        nom = "%d — %s" % (o.ident, self.tr.nom_type(o.type)) if o else self.tr.t("aucune_selection")
        self.etiquette_selection["text"] = self.tr.t("selection_objet", nom=nom)
        self.choix_type.set("%d — %s" % (o.type, self.tr.nom_type(o.type)) if o else "")
        fige = o is None or o.type in (PORTE, TOTEM)          # leur type ne change pas
        self.choix_type["state"] = "disabled" if fige else "readonly"
        for nom, saisie in self.saisies.items():
            saisie.delete(0, "end")
            valeur = getattr(o, nom) if o else None
            if valeur is not None:
                saisie.insert(0, str(int(valeur)))

    # --- gestes ------------------------------------------------------------------

    def _objet_sous(self, xe: float, ye: float) -> int | None:
        for item in reversed(self.canevas.find_overlapping(xe - 2, ye - 2, xe + 2, ye + 2)):
            for etiquette in self.canevas.gettags(item):
                if etiquette.startswith("o"):
                    return int(etiquette[1:])
        return None

    def _armer(self, numero: int) -> None:
        self.arme = numero
        self.canevas.config(cursor="crosshair")

    def _appui(self, ev) -> None:
        if self.ed.base is None:
            return
        if self.arme is not None:
            numero, self.arme = self.arme, None
            self.canevas.config(cursor="")
            self.ed.poser(numero, *vers_donjon(ev.x, ev.y))
            self.rafraichir()
            return
        ident = self._objet_sous(ev.x, ev.y)
        self.ed.selectionner(ident)
        self.rafraichir()
        self._glisse = (ident, ev.x, ev.y, ev.x, ev.y) if ident is not None else None

    def _glisser(self, ev) -> None:
        if self._glisse is None:
            return
        ident, x0, y0, xd, yd = self._glisse
        self.canevas.move("o%d" % ident, ev.x - xd, ev.y - yd)
        self._glisse = (ident, x0, y0, ev.x, ev.y)

    def _relache(self, ev) -> None:
        if self._glisse is None:
            return
        ident, x0, y0, _, _ = self._glisse
        self._glisse = None
        if (ev.x, ev.y) == (x0, y0):
            return
        o = self.ed.base.obstacle(ident)
        self.ed.deplacer(ident, round(o.x + (ev.x - x0) / ECHELLE), round(o.y + (ev.y - y0) / ECHELLE))
        self.rafraichir()

    def _retirer_sous(self, ev) -> None:
        ident = self._objet_sous(ev.x, ev.y)
        if ident is None:
            return
        try:
            self.ed.retirer(ident)
        except ValueError:
            messagebox.showinfo(self.tr.t("erreur"), self.tr.t("retrait_interdit"), parent=self.racine)
        self.rafraichir()

    def _choix_liste(self, _ev) -> None:
        choix = self.liste.selection()
        ident = int(choix[0]) if choix else None
        if ident != self.ed.selection:
            self.ed.selectionner(ident)
            self.rafraichir()

    def _appliquer_fiche(self) -> None:
        if self.ed.selection is None:
            return
        try:
            champs = {nom: _entier(s.get()) for nom, s in self.saisies.items()}
            for nom in BOOLEENS:
                if champs[nom] is not None:
                    champs[nom] = bool(champs[nom])
            if champs["x"] is None or champs["y"] is None:
                raise ValueError("x et y sont requis")
            if self.choix_type.get():
                champs["type"] = int(self.choix_type.get().split()[0])
            self.ed.modifier(self.ed.selection, **champs)
        except ValueError as e:
            messagebox.showerror(self.tr.t("erreur"), self.tr.t("erreur_saisie", erreur=e), parent=self.racine)
        self.rafraichir()

    def _basculer_libre(self) -> None:
        self.ed.libre = self.libre.get()

    def _basculer_bruts(self) -> None:
        self._montrer_bruts(not self._bruts_visibles)

    def _montrer_bruts(self, visibles: bool) -> None:
        self._bruts_visibles = visibles
        self.bouton_bruts["text"] = ("▾ " if visibles else "▸ ") + self.tr.t("autres_champs")
        if visibles:
            self.cadre_bruts.pack(anchor="w", after=self.bouton_bruts)
        else:
            self.cadre_bruts.pack_forget()

    # --- barre d'outils --------------------------------------------------------------

    def choisir_forme(self) -> None:
        t = self.tr.t
        dialogue = tk.Toplevel(self.racine)
        dialogue.title(t("choisir_forme"))
        liste = tk.Listbox(dialogue, width=48, height=20)
        formes = self.ed.corpus.formes
        for f in formes:
            liste.insert("end", t("forme_commune", numero=f.numero) if f.origine == "commune"
                         else t("forme_moddee", numero=f.numero, auteur=f.auteur))
        liste.pack(fill="both", expand=True)

        def choisir(_ev=None):
            if liste.curselection():
                self.ed.nouvelle(formes[liste.curselection()[0]])
                dialogue.destroy()
                self.rafraichir()

        liste.bind("<Double-Button-1>", choisir)
        ttk.Button(dialogue, text=t("choisir"), command=choisir).pack()

    def ouvrir(self) -> None:
        chemin = filedialog.askopenfilename(parent=self.racine, filetypes=[(self.tr.t("fichiers_bin"), "*.bin")])
        if not chemin:
            return
        try:
            self.ed.ouvrir(chemin)
        except ErreurLecture as e:
            messagebox.showerror(self.tr.t("erreur"), self.tr.t("erreur_lecture", erreur=e), parent=self.racine)
        self.rafraichir()

    def enregistrer(self) -> None:
        if self.ed.base is None:
            return
        chemin = self.ed.chemin_sortie
        if chemin is None:
            suggestion = self.ed.suggestion()
            chemin = filedialog.asksaveasfilename(
                parent=self.racine, defaultextension=".bin",
                filetypes=[(self.tr.t("fichiers_bin"), "*.bin")],
                initialdir=os.path.dirname(suggestion) if suggestion else None,
                initialfile=os.path.basename(suggestion) if suggestion else "base_kotcm.bin")
            if not chemin:
                return
        try:
            self.ed.enregistrer(chemin)
        except (OSError, ValueError) as e:
            messagebox.showerror(self.tr.t("erreur"), str(e), parent=self.racine)
        self.rafraichir()

    def annuler(self) -> None:
        if self.ed.annuler():
            self.rafraichir()

    def changer_langue(self, langue: str) -> None:
        self.tr.langue = langue
        sauver_langue(langue, self.preferences)
        self.construire()

    # --- chargement live -----------------------------------------------------------------

    def charger_dans_le_jeu(self) -> None:
        if self.chargeur is None or self.ed.base is None:
            return
        t = self.tr.t
        problemes = self.ed.resume().problemes
        if problemes and not messagebox.askyesno(t("charger"), t("live_problemes", p=problemes), parent=self.racine):
            return
        self._live(lambda: self.chargeur.charger(self.ed.base.octets()), "live_charge_ok")

    def decharger_du_jeu(self) -> None:
        if self.chargeur is not None:
            self._live(self.chargeur.decharger, "live_decharge_ok")

    def quitter(self) -> None:
        if self.chargeur is not None and self.chargeur.chargee() is not None:
            reponse = messagebox.askyesnocancel(self.tr.t("titre"), self.tr.t("live_quitter"), parent=self.racine)
            if reponse is None or (reponse and not self._live(self.chargeur.decharger, "live_decharge_ok")):
                return
        self.racine.destroy()

    def _live(self, action, cle_ok: str) -> bool:
        """Lance une operation live (curseur d'attente), affiche son resultat ; vrai si elle a reussi."""
        self.racine.config(cursor="watch")
        self.racine.update_idletasks()
        try:
            emplacement = action()
        except ErreurLive as e:
            messagebox.showerror(self.tr.t("erreur"), self.tr.t(e.cle, **e.valeurs), parent=self.racine)
            return False
        finally:
            self.racine.config(cursor="")
            self.rafraichir()
        messagebox.showinfo(self.tr.t("titre"), self.tr.t(cle_ok, emplacement=emplacement), parent=self.racine)
        return True
