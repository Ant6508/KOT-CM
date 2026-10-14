# KOT-CM — mode créatif pour King of Thieves

Construis des bases de **King of Thieves** sur ton PC, pose et règle les
pièges à ton gré, puis charge-les dans l'éditeur du jeu pour les jouer en
mode **Essayer**.

- **143 formes de base** : les 130 formes du jeu et 13 formes moddées.
- **Tous les types de pièges**, posés au clic et déplacés au glisser,
  aimantés comme dans le jeu ou placés au pixel ; type, position, orientation
  et rayon réglables.
- **Les règles de placement du jeu**, vérifiées au fil de l'eau (trop près de
  la porte, sur le totem, sans paroi…).
- Bases enregistrées en `.bin` : le format de donjon du jeu lui-même.
- **Chargement dans le jeu** (facultatif) : la base remplace le préréglage
  courant dans l'éditeur du jeu, depuis l'accueil ; tu la joues avec
  **Essayer**, puis **Décharger** remet ta propre base, à l'octet près.

Portage en Python du *Creative Mode Mod Menu* d'OvovUsus (voir
[Crédits](#crédits)), pour King of Thieves **2.84** sur l'émulateur Android
**MEmu**, sous Windows. L'éditeur marche hors ligne ; seul le chargement dans
le jeu demande MEmu.

> **Règle d'usage : ta propre base, ou des bases que tu construis toi-même.
> Jamais la base d'un autre joueur sans son accord. N'enregistre jamais une
> base chargée dans le jeu.**
>
> Projet personnel, non affilié à ZeptoLab. Tu l'utilises à tes risques.

*English version: [README.md](README.md).*

## À lire avant de charger une base dans le jeu

1. **Ne déplace, ne tourne, n'ajoute ni ne retire aucun objet dans l'éditeur
   tant qu'une base kotcm est chargée : sers-toi seulement d'Essayer.** Les
   emplacements de l'éditeur sont des brouillons gardés par le serveur du
   jeu : chaque geste dans l'éditeur part au serveur, qui l'applique à **ton
   propre** brouillon (tes vrais pièges et tes gemmes). Ta base défendue, elle,
   reste protégée. Si tu as déplacé quelque chose par mégarde : décharge,
   redémarre le jeu, et vérifie ta propre base dans l'éditeur avant tout
   enregistrement.
2. **Un piège que tu ne possèdes pas peut faire planter Essayer.** L'éditeur
   l'affiche, mais Essayer a besoin de ses images. Le jeu redémarre et
   recharge ta base du serveur : rien n'est perdu. Construis avec les pièges
   que tu possèdes pour jouer tes bases.
3. **« Enregistrer » est neutralisé** tant qu'une base est chargée, pour
   qu'une base kotcm ne soit jamais enregistrée comme ta base. N'essaie pas de
   le contourner.

## Ce qu'il te faut

- Windows 10 ou 11, 64 bits.
- Une connexion internet, pour l'installation et le premier chargement dans
  le jeu.
- Pour le chargement dans le jeu seulement : environ 3 Go d'espace disque
  (MEmu et le jeu).

## Installation

Compte un quart d'heure, une demi-heure avec MEmu. Chaque étape finit par une
vérification : ne passe à la suivante que si elle réussit.

### 1. Python

1. Sur <https://www.python.org/downloads/windows/>, sous une version
   **Python 3.14**, clique **Windows installer (64-bit)** (pas le *Python
   install manager* listé en premier). Toute version à partir de la 3.10
   convient ; l'outil est testé en 3.14.
2. Lance l'installeur. **Sur le premier écran, coche « Add python.exe to
   PATH »**, puis clique *Install Now*.
3. Si tu passes par *Customize installation*, laisse **« tcl/tk and IDLE »**
   coché : la fenêtre en a besoin.

**Vérification :** ouvre un **nouveau** terminal (menu Démarrer, tape
`PowerShell`, Entrée) et tape :

```
python --version
```

Il doit répondre `Python 3.x.y` avec x égal à 10 ou plus. S'il ouvre le
Microsoft Store ou dit que la commande est introuvable, la case « Add
python.exe to PATH » n'était pas cochée : relance l'installeur, choisis
*Modify*, puis *Next*, coche **« Add Python to environment variables »** et
valide. Ouvre ensuite un nouveau terminal.

### 2. Récupérer le projet

Au choix :

- **Sans Git** : sur <https://github.com/Ant6508/KOT-CM>, bouton vert
  **Code** → **Download ZIP**. Clic droit sur le fichier téléchargé →
  *Extraire tout…*. Le ZIP contient un dossier `KOT-CM-main` : c'est le
  dossier du projet. Place-le où tu veux, par exemple `C:\KOT-CM` (si
  *Extraire tout* a créé `KOT-CM-main\KOT-CM-main`, prends le dossier
  intérieur).
- **Avec Git** (<https://git-scm.com/download/win>), plus pratique pour les
  mises à jour :

  ```
  git clone https://github.com/Ant6508/KOT-CM C:\KOT-CM
  ```

Toutes les commandes suivantes se tapent dans un terminal ouvert **dans le
dossier du projet** :

```
cd C:\KOT-CM
```

**Vérification :** `dir` liste, entre autres, `kotcm`, `tests` et
`pyproject.toml`.

### 3. Environnement Python

```
python -m venv .venv
.venv\Scripts\python.exe -m pip install -e ".[live,dev]"
```

La première commande crée un Python propre au projet, dans `.venv`. La
seconde y installe Frida 17.19.0 (pour le chargement dans le jeu) et pytest.
Toutes les commandes du projet appellent ensuite **ce** Python,
`.venv\Scripts\python.exe`, sans activation : pas besoin d'`Activate.ps1`,
que PowerShell bloque souvent.

**Vérification :** une des dernières lignes commence par `Successfully
installed` et cite `frida-17.19.0` (un `[notice]` sur une version plus récente
de pip peut suivre : ignore-le).

### 4. Vérifier l'installation

```
.venv\Scripts\python.exe -m pytest -q
```

**Vérification :** la dernière ligne dit `N passed`, avec peut-être quelques
`skipped`, mais aucun `failed` ni `error`. Ces tests ne touchent ni au jeu ni
à MEmu.

### 5. Premier lancement

```
.venv\Scripts\python.exe -m kotcm
```

**Vérification :** la fenêtre **kotcm — mode créatif** s'ouvre. Elle démarre
en français si Windows est en français, en anglais sinon ; **Langue** (fr / en)
la change, et le choix est retenu.

L'éditeur est prêt. Les étapes suivantes ne servent qu'à charger des bases
dans le jeu.

### 6. MEmu

1. Télécharge MEmu sur <https://www.memuplay.com> et installe-le avec les
   options proposées par défaut.
2. Lance MEmu et attends l'écran d'accueil Android.
3. Ouvre les **Paramètres** de MEmu (icône d'engrenage dans la barre de
   droite), onglet **Moteur** (*Engine*) : active le **mode Root** (*Root
   mode*).
4. Enregistre, puis redémarre MEmu quand il te le propose.

Pourquoi : l'outil a besoin des droits root sur l'émulateur pour y lancer
frida-server, le petit programme par lequel il lit et écrit la mémoire du jeu.
Il lui faut une instance Android 64 bits (il a été testé sur l'Android 9,
64 bits, de MEmu).

**Vérification :** après le redémarrage, les paramètres de MEmu montrent
toujours le mode Root activé.

### 7. King of Thieves 2.84

1. Dans MEmu, ouvre le **Play Store**, connecte-toi avec un compte Google et
   installe **King of Thieves**.
2. Lance le jeu une fois, jusqu'à ta base, pour qu'il finisse de télécharger
   ses données.
3. Dans le Play Store, sur la page de King of Thieves, menu **⋮** → décoche
   **Activer la mise à jour automatique** (le libellé peut varier).

**Vérification :** dans MEmu, *Paramètres* Android → *Applications* → *King
of Thieves* : la version affichée doit être **2.84**.

L'outil est lié à cette version exacte (versionCode 4755781) : il écrit dans
la mémoire du jeu à des adresses relevées sur la 2.84. Avec une autre
version, il refuse de charger plutôt que d'écrire au mauvais endroit. Si le
Play Store installe une version plus récente, le chargement ne marchera plus
tant que ces adresses n'auront pas été mises à jour (voir [Limites](#limites)) ;
l'éditeur hors ligne, lui, marche toujours.

### 8. Premier chargement dans le jeu

1. Dans la fenêtre de kotcm, construis ou ouvre une base (voir
   [Utilisation](#utilisation)).
2. Dans MEmu, amène le jeu sur son **accueil**, éditeur fermé.
3. Clique **Charger dans le jeu**.

   **La toute première fois**, kotcm installe d'abord frida-server sur MEmu :
   il le télécharge (34 Mo), le copie dans MEmu et le lance. La fenêtre ne
   répond plus pendant ce temps ; compte une minute. Les fois suivantes,
   c'est immédiat.

L'outil trouve tout seul l'`adb` livré avec MEmu : pas besoin d'installer le
SDK Android.

**Vérification :** un message dit *Base chargée dans l'emplacement N*. Dans
le jeu, appuie sur **MODIFIER** : ta base kotcm est là. Appuie sur
**Essayer** pour la jouer. Reviens ensuite à l'accueil (flèche retour) et
clique **Décharger du jeu** : *Ta base est remise dans l'emplacement N*.

## Utilisation

### La fenêtre

```
.venv\Scripts\python.exe -m kotcm
.venv\Scripts\python.exe -m kotcm ma_base.bin
.venv\Scripts\python.exe -m kotcm --langue fr
```

- **Nouvelle…** : choisis une forme parmi les 143 (*commune* ou *moddée*,
  avec son auteur). La porte, le totem et les objets de structure de la forme
  (plateformes, trampolines, anti-gravité) sont posés à des positions par
  défaut : déplace-les.
- **Palette** (sous le donjon) : clique un type, puis clique dans le donjon
  pour le poser. Un `*` signale un *modèle supposé* : un type jamais relevé
  dans une vraie base ; ses champs sont devinés (les valeurs les plus
  fréquentes des pièges relevés).
- **Clic** : sélectionne ; **glisser** : déplace ; **clic droit** : retire
  (sauf la porte et le totem). **Ctrl+Z** annule.
- **placement libre** : pose au pixel au lieu d'aimanter comme le jeu.
- **Le panneau de droite** : la forme, la liste des objets, les champs de
  l'objet sélectionné (type, x, y, orientation, vx, vy ; *autres champs* pour
  les champs bruts) : tape une valeur et appuie sur Entrée.
- **Règles** : un objet que le jeu refuserait est entouré de rouge, et le
  message du jeu figure sous **Règles** dans le panneau de droite. *Non vérifié* : les règles propres à ce type de piège ne
  sont pas connues ; seules celles communes à tous les pièges sont vérifiées.
  L'outil signale sans jamais bloquer : c'est le jeu qui refusera **Essayer**
  sur une base qui enfreint ses règles.
- **Enregistrer .bin** : n'écrase jamais le fichier ouvert ; le premier
  enregistrement propose `<nom>_kotcm.bin`.

### Le chargement dans le jeu

- **Charger dans le jeu** : depuis l'**accueil** du jeu, éditeur fermé. La
  base remplace le préréglage courant de l'éditeur ; appuie sur
  **MODIFIER**, puis **Essayer**. Pour charger une nouvelle version : flèche
  retour jusqu'à l'accueil (sans rien toucher), de nouveau **Charger dans le
  jeu**, **MODIFIER**.
- **Décharger du jeu** : remet ta propre base et rend « Enregistrer ».
  Fermer la fenêtre avec une base chargée propose de la décharger.
- Avant le premier chargement, kotcm copie ta base dans
  `%USERPROFILE%\.kotcm\sauvegardes\`. Ces copies ne sont jamais écrasées ni
  effacées. Le dossier `.kotcm` garde aussi la copie de frida-server
  (116 Mo). Pour ranger les données de kotcm ailleurs, définis `KOTCM_DOSSIER`
  avant de lancer, par exemple `$env:KOTCM_DOSSIER = "D:\kotcm-data"`. Cela ne
  vaut que pour ce terminal : définis-la dans chaque terminal, ou une fois pour
  toutes avec `setx KOTCM_DOSSIER D:\kotcm-data`, puis ouvre un nouveau
  terminal. Le choix de langue reste dans `%USERPROFILE%\.kotcm.json`.
- Si le jeu redémarre (plantage, déconnexion pour inactivité), il recharge ta
  base du serveur : le chargement a simplement disparu. Recharge si tu veux.

La même chose sans la fenêtre :

```
.venv\Scripts\python.exe -m kotcm.live charger ma_base.bin
.venv\Scripts\python.exe -m kotcm.live decharger
.venv\Scripts\python.exe -m kotcm.live etat
```

### Plusieurs instances de MEmu

Avec une seule instance ouverte, l'outil la trouve seul. Avec plusieurs, il
refuse de deviner et liste les appareils. Choisis l'instance avec
`--serial` :

```
.venv\Scripts\python.exe -m kotcm --serial 127.0.0.1:21503
```

La première instance de MEmu répond sur `127.0.0.1:21503`, la deuxième sur
`127.0.0.1:21513`, et ainsi de suite (+10 par instance). La variable
`ANDROID_SERIAL` fait la même chose pour tout le terminal :
`$env:ANDROID_SERIAL = "127.0.0.1:21513"`.

### Mettre à jour

Avec Git : `git pull` dans le dossier du projet. Avec le ZIP : télécharge le
nouveau ZIP et remplace les fichiers, en gardant tes fichiers `.bin`. Dans
les deux cas, relance ensuite :

```
.venv\Scripts\python.exe -m pip install -e ".[live,dev]"
```

## Dépannage

| Message | Cause | Remède |
|---|---|---|
| `python` n'est pas reconnu, ou le Microsoft Store s'ouvre | Python n'est pas dans le PATH | Étape 1 : relance l'installeur, *Modify*, « Add Python to environment variables », puis ouvre un nouveau terminal |
| `No module named 'tkinter'` | Python installé sans tcl/tk | Relance l'installeur, *Modify*, coche « tcl/tk and IDLE » |
| `frida n'est pas installé` ou `frida X est installé, kotcm attend 17.19.0` | Étape 3 sautée, ou une autre version de Frida dans `.venv` | `.venv\Scripts\python.exe -m pip install "frida==17.19.0"` |
| `adb introuvable` | MEmu n'est pas installé, ou installé d'une façon que l'outil ne reconnaît pas | Installe MEmu (étape 6). Sinon, donne le chemin complet d'`adb.exe`, par exemple `$env:KOTCM_ADB = "C:\Program Files\Microvirt\MEmu\adb.exe"` |
| `adb a échoué : ...` | Mauvais `--serial`, ou cette instance de MEmu n'est pas lancée | Vérifie l'instance (voir [Plusieurs instances de MEmu](#plusieurs-instances-de-memu)) |
| `Choisis l'appareil avec --serial` | Aucun MEmu lancé, ou plusieurs | Lance MEmu ; avec plusieurs instances, voir [Plusieurs instances de MEmu](#plusieurs-instances-de-memu). S'il dit `(connectés : -)` alors que MEmu tourne, redémarre MEmu |
| `Le jeu installé est en ... ; kotcm ne connaît que la 2.84` | King of Thieves n'est pas en 2.84 | L'outil ne marche qu'avec la 2.84 (voir [Limites](#limites)) |
| `King of Thieves ne tourne pas.` | Le jeu est fermé | Lance King of Thieves dans MEmu, jusqu'à l'accueil |
| `Un autre frida-server tourne` | Un autre outil Frida a laissé son serveur tourner dans MEmu | Redémarre MEmu, puis recommence |
| `frida-server 17.19.0 manque ou n'est pas le bon, et n'a pas pu être téléchargé` | Pas d'internet, ou GitHub injoignable | Vérifie ta connexion et recommence. Sinon, suis le message : télécharge l'archive à la main, décompresse-la avec 7-Zip, pose le fichier où il le dit |
| `Un dossier occupe la place du fichier frida-server` | L'archive a été décompressée dans un dossier de ce nom | Supprime le dossier, ou sors-en le fichier et pose-le à sa place |
| `frida-server ne démarre pas` ou `Impossible de s'attacher au jeu` | Mode Root désactivé, ou instance Android 32 bits | Vérifie le mode Root (étape 6) et que l'instance est en 64 bits (dans le gestionnaire Multi-MEmu), puis redémarre MEmu |
| `L'éditeur est ouvert` | Le jeu n'est pas sur son accueil | Flèche retour dans le jeu, sans enregistrer, puis recommence |
| `L'emplacement courant est passé de A à B : décharge d'abord.` | Tu as changé de préréglage dans le jeu pendant un chargement | Clique **Décharger du jeu**, puis recharge |
| `Mémoire du jeu inattendue (...)` | Le jeu n'est pas exactement en 2.84, ou démarre encore | Attends l'accueil et recommence ; sinon vérifie la version (étape 7) |
| `Le jeu ne dessine plus` | MEmu est réduit ou le jeu est en arrière-plan | Remets le jeu au premier plan, puis recommence |
| `« Enregistrer » est déjà neutralisé, mais kotcm n'a pas de copie de ta base` | Les données de kotcm ont été effacées pendant un chargement | Redémarre le jeu : il recharge ta base du serveur |
| Le jeu se ferme pendant **Essayer** | Un piège que tu ne possèdes pas (voir [À lire avant](#à-lire-avant-de-charger-une-base-dans-le-jeu)) | Relance le jeu : ta base est revenue. Retire ce piège de la base kotcm |
| Les tests de l'étape 4 échouent | Installation incomplète | Refais l'étape 3, puis l'étape 4 |

## Limites

- **King of Thieves 2.84 seulement** pour le chargement dans le jeu : l'outil
  écrit dans la mémoire du jeu à des adresses relevées sur cette version, à
  retrouver à chaque mise à jour du jeu. L'éditeur hors ligne ne dépend pas
  de la version du jeu.
- **MEmu sous Windows seulement** (Android 64 bits, root).
- **Les gestes dans l'éditeur atteignent le serveur** tant qu'une base est
  chargée (voir [À lire avant](#à-lire-avant-de-charger-une-base-dans-le-jeu)) ;
  les bloquer viendra peut-être dans une version suivante.
- Les règles de placement sont exactes pour la porte, le totem, la scie, le
  garde bleu et le bloodhound ; pour les autres pièges, seules les règles
  communes à tous les pièges sont vérifiées (*non vérifié*).
- L'interface et les messages sont en français et en anglais ; le code
  lui-même (noms, commentaires, docstrings) est en français.

## Crédits

- **OvovUsus** (<https://github.com/OvovUsus>), auteur du *Creative Mode Mod
  Menu*, des formes de base numérisées et du reverse engineering en 2.76 sur
  lesquels cet outil s'appuie. Portage fait avec son accord, sous la même
  licence.
- Les auteurs des formes moddées : **Peter Biskup** (spover), **krypt**
  (krp.t), **Soruem** (complore) et **Disconnect** (4disc0nnect4).

## Licence

GPL-3.0, comme le mod d'origine : voir [LICENSE](LICENSE).
