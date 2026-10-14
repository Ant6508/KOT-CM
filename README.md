# KOT_CM — creative mode for King of Thieves

Build **King of Thieves** bases on your PC, place and edit traps as you like,
then load them into the game's own editor to play them in **Try** mode.

- **143 base shapes**: the 130 shapes of the game and 13 modded shapes.
- **Every trap type**, placed by click and moved by drag, snapped like in the
  game or placed to the pixel; type, position, orientation and range
  editable.
- **The game's placement rules**, checked as you go (too close to the door,
  on the totem, no wall to stand on...).
- Bases saved as `.bin`: the game's own dungeon format.
- **Load into the game** (optional): the base replaces the current preset in
  the game's editor, from the home screen; you play it with **Try**, then
  **Unload** puts your own base back, byte for byte.

A Python port of the *Creative Mode Mod Menu* by OvovUsus (see
[Credits](#credits)), for King of Thieves **2.84** on the **MEmu** Android
emulator, on Windows. The editor works offline; only the loading into the
game needs MEmu.

> **Usage rule: your own base, or bases you build yourself. Never another
> player's base without their consent. Never save a loaded base in the
> game.**
>
> Personal project, not affiliated with ZeptoLab. Use it at your own risk.

*Version française : [README.fr.md](README.fr.md).*

## Read this before loading a base into the game

1. **Don't move, rotate, add or remove any object in the editor while a kotcm
   base is loaded: only use Try.** The game's editor slots are drafts kept by
   the game server: each move in the editor is sent to the server, which
   applies it to **your own** draft (your real traps and gems). Your defended
   base itself stays protected. If you moved something by mistake: unload,
   restart the game, and check your own base in the editor before any Save.
2. **A trap you don't own may crash Try.** The editor shows it, but Try needs
   its graphics. The game restarts and reloads your base from the server:
   nothing is lost. Build with the traps you own to play your bases.
3. **"Save" is disabled** while a base is loaded, so that a kotcm base is
   never saved as your base. Don't try to get around it.

## What you need

- Windows 10 or 11, 64-bit.
- An internet connection, for the installation and the first loading into
  the game.
- For the loading into the game only: about 3 GB of disk space (MEmu and the
  game).

## Installation

Allow a quarter of an hour, half an hour with MEmu. Each step ends with a
check: only move on to the next one if it passes.

### 1. Python

1. On <https://www.python.org/downloads/windows/>, under a **Python 3.14**
   release, click **Windows installer (64-bit)** (not the *Python install
   manager* listed first). Any version from 3.10 works; the tool is tested on
   3.14.
2. Run the installer. **On the first screen, tick "Add python.exe to
   PATH"**, then click *Install Now*.
3. If you go through *Customize installation*, keep **"tcl/tk and IDLE"**
   ticked: the window needs it.

**Check:** open a **new** terminal (Start menu, type `PowerShell`, Enter) and
type:

```
python --version
```

It must answer `Python 3.x.y` with x equal to 10 or more. If it opens the
Microsoft Store or says the command isn't found, the "Add python.exe to PATH"
box wasn't ticked: run the installer again, choose *Modify*, then *Next*, tick
**"Add Python to environment variables"** and confirm. Then open a new
terminal.

### 2. Get the project

Either:

- **Without Git**: on <https://github.com/Ant6508/KOT_CM>, green **Code**
  button → **Download ZIP**. Right-click the downloaded file → *Extract
  All…*. The ZIP contains a `KOT_CM-main` folder: that's the project folder.
  Put it wherever you like, for example `C:\KOT_CM` (if *Extract All* made
  `KOT_CM-main\KOT_CM-main`, take the inner folder).
- **With Git** (<https://git-scm.com/download/win>), handier to get updates:

  ```
  git clone https://github.com/Ant6508/KOT_CM C:\KOT_CM
  ```

All the following commands are typed in a terminal opened **in the project
folder**:

```
cd C:\KOT_CM
```

**Check:** `dir` lists, among others, `kotcm`, `tests` and `pyproject.toml`.

### 3. Python environment

```
python -m venv .venv
.venv\Scripts\python.exe -m pip install -e ".[live,dev]"
```

The first command creates a Python of the project's own, in `.venv`. The
second installs Frida 17.19.0 (for the loading into the game) and pytest
into it. All the project's commands then call **this** Python,
`.venv\Scripts\python.exe`, without activation: no need for `Activate.ps1`,
which PowerShell often blocks.

**Check:** one of the last lines starts with `Successfully installed` and
mentions `frida-17.19.0` (a `[notice]` about a newer pip may follow: ignore
it).

### 4. Check the installation

```
.venv\Scripts\python.exe -m pytest -q
```

**Check:** the last line says `N passed`, maybe with a few `skipped`, but no
`failed` or `error`. These tests touch neither the game nor MEmu.

### 5. First launch

```
.venv\Scripts\python.exe -m kotcm
```

**Check:** the **kotcm — creative mode** window opens. It starts in French if
Windows is set to French, in English otherwise; **Language** (fr / en)
switches it, and the choice is remembered.

The editor is ready. The next steps are only needed to load bases into the
game.

### 6. MEmu

1. Download MEmu from <https://www.memuplay.com> and install it with the
   default options.
2. Launch MEmu and wait for the Android home screen.
3. Open MEmu's **Settings** (gear icon in the right-hand bar), **Engine**
   tab: turn on **Root mode**.
4. Save, then restart MEmu when it offers to.

Why: the tool needs root rights on the emulator to run frida-server there,
the small program through which it reads and writes the game's memory. It
needs a 64-bit Android instance (it was tested on MEmu's Android 9, 64-bit).

**Check:** after the restart, MEmu's settings still show Root mode on.

### 7. King of Thieves 2.84

1. In MEmu, open the **Play Store**, sign in with a Google account and install
   **King of Thieves**.
2. Launch the game once, up to your base, so it finishes downloading its data.
3. In the Play Store, on the King of Thieves page, menu **⋮** → untick
   **Enable auto update** (the wording may vary).

**Check:** in MEmu, Android *Settings* → *Apps* → *King of Thieves*: the
version shown must be **2.84**.

The tool is tied to this exact version (versionCode 4755781): it writes into
the game's memory at addresses recorded on 2.84. With any other version, it
refuses to load rather than write in the wrong place. If the Play Store
installs a newer version, the loading won't work until those addresses have
been updated (see [Limitations](#limitations)); the offline editor still
works.

### 8. First loading into the game

1. In the kotcm window, build or open a base (see [Usage](#usage)).
2. In MEmu, bring the game to its **home screen**, editor closed.
3. Click **Load into the game**.

   **The very first time**, kotcm first installs frida-server on MEmu: it
   downloads it (34 MB), copies it into MEmu and starts it. The window doesn't
   respond for that time; allow a minute. The following times, it's
   immediate.

The tool finds the `adb` shipped with MEmu on its own: no need to install the
Android SDK.

**Check:** a message says *Base loaded into slot N*. In the game, tap
**EDIT**: your kotcm base is there. Tap **Try** to play it. Then come back to
the home screen (back arrow) and click **Unload from the game**: *Your base is
back in slot N*.

## Usage

### The window

```
.venv\Scripts\python.exe -m kotcm
.venv\Scripts\python.exe -m kotcm my_base.bin
.venv\Scripts\python.exe -m kotcm --langue en
```

- **New…**: pick a shape among the 143 (*common* or *modded*, with its
  author). The door, the totem and the shape's structure objects (platforms,
  trampolines, anti-gravity) are placed at default positions: move them.
- **Palette** (under the dungeon): click a type, then click in the dungeon to
  place it. A `*` marks an *assumed model*: a type never recorded in a real
  base; its fields are a guess (the most common values among recorded
  traps).
- **Click** selects, **drag** moves, **right-click** removes (except the door
  and the totem). **Ctrl+Z** undoes.
- **free placement**: places to the pixel instead of snapping like the game.
- **The side panel**: the shape, the list of objects, the selected object's
  fields (type, x, y, orientation, vx, vy; *other fields* for the raw ones):
  type a value and press Enter.
- **Rules**: an object the game would refuse is outlined in red, and the
  game's message is listed under **Rules** in the side panel. *Not verified*: the rules specific to that trap type aren't known;
  only the ones common to all traps are checked. The tool warns but never
  blocks: the game itself will refuse **Try** on a base that breaks its
  rules.
- **Save .bin**: never overwrites the file you opened; the first save offers
  `<name>_kotcm.bin`.

### Loading into the game

- **Load into the game**: from the game's **home screen**, editor closed. The
  base replaces the current preset of the editor; tap **EDIT**, then **Try**.
  To load a new version: back arrow to the home screen (without touching
  anything), **Load into the game** again, **EDIT**.
- **Unload from the game**: puts your own base back and gives "Save" back.
  Closing the window with a base loaded offers to unload it.
- Before the first loading, kotcm copies your base to
  `%USERPROFILE%\.kotcm\sauvegardes\`. These copies are never overwritten or
  deleted. The `.kotcm` folder also keeps the copy of frida-server (116 MB).
  To keep kotcm's data elsewhere, set `KOTCM_DOSSIER` before launching, for
  example `$env:KOTCM_DOSSIER = "D:\kotcm-data"`. That lasts for that terminal
  only: set it in every terminal you use, or once for all with
  `setx KOTCM_DOSSIER D:\kotcm-data`, then open a new terminal. The language
  choice stays in `%USERPROFILE%\.kotcm.json`.
- If the game restarts (crash, idle disconnection), it reloads your base from
  the server: the loading is simply gone. Load again if you want to.

The same without the window:

```
.venv\Scripts\python.exe -m kotcm.live charger my_base.bin
.venv\Scripts\python.exe -m kotcm.live decharger
.venv\Scripts\python.exe -m kotcm.live etat
```

### Several MEmu instances

With a single instance open, the tool finds it on its own. With several, it
refuses to guess and lists the devices. Pick the instance with `--serial`:

```
.venv\Scripts\python.exe -m kotcm --serial 127.0.0.1:21503
```

The first MEmu instance answers on `127.0.0.1:21503`, the second on
`127.0.0.1:21513`, and so on (+10 per instance). The `ANDROID_SERIAL`
variable does the same for the whole terminal:
`$env:ANDROID_SERIAL = "127.0.0.1:21513"`.

### Updating

With Git: `git pull` in the project folder. With the ZIP: download the new ZIP
and replace the files, keeping your `.bin` files. Either way, then run again:

```
.venv\Scripts\python.exe -m pip install -e ".[live,dev]"
```

## Troubleshooting

| Message | Cause | Fix |
|---|---|---|
| `python` isn't recognized, or the Microsoft Store opens | Python isn't in the PATH | Step 1: run the installer again, *Modify*, "Add Python to environment variables", then open a new terminal |
| `No module named 'tkinter'` | Python installed without tcl/tk | Run the installer again, *Modify*, tick "tcl/tk and IDLE" |
| `frida is not installed` or `frida X is installed, kotcm expects 17.19.0` | Step 3 skipped, or another Frida version in `.venv` | `.venv\Scripts\python.exe -m pip install "frida==17.19.0"` |
| `adb not found` | MEmu isn't installed, or installed in a way the tool doesn't recognize | Install MEmu (step 6). Otherwise, give the full path of `adb.exe`, for example `$env:KOTCM_ADB = "C:\Program Files\Microvirt\MEmu\adb.exe"` |
| `adb failed: ...` | Wrong `--serial`, or that MEmu instance isn't started | Check the instance (see [Several MEmu instances](#several-memu-instances)) |
| `Choose the device with --serial` | No MEmu running, or several | Launch MEmu; with several instances, see [Several MEmu instances](#several-memu-instances). If it says `(connected: -)` while MEmu is running, restart MEmu |
| `The installed game is ...; kotcm only knows 2.84` | King of Thieves isn't on 2.84 | The tool only works with 2.84 (see [Limitations](#limitations)) |
| `King of Thieves is not running.` | The game is closed | Launch King of Thieves in MEmu, up to the home screen |
| `Another frida-server is running` | Another Frida tool left its server running in MEmu | Restart MEmu, then try again |
| `frida-server 17.19.0 is missing or not the right one, and could not be downloaded` | No internet, or GitHub unreachable | Check your connection and try again. Otherwise, follow the message: download the archive by hand, unpack it with 7-Zip, put the file where it says |
| `A folder is in the place of the frida-server file` | The archive was unpacked into a folder of that name | Delete the folder, or take the file out of it and put it in its place |
| `frida-server does not start` or `Cannot attach to the game` | Root mode off, or a 32-bit Android instance | Check Root mode (step 6) and that the instance is 64-bit (in the Multi-MEmu manager), then restart MEmu |
| `The editor is open` | The game isn't on its home screen | Back arrow in the game, without saving, then try again |
| `The current slot changed from A to B: unload first.` | You switched preset in the game while a base was loaded | Click **Unload from the game**, then load again |
| `Unexpected game memory (...)` | The game isn't exactly 2.84, or is still starting | Wait for the home screen and try again; otherwise check the version (step 7) |
| `The game is not drawing` | MEmu is minimized or the game is in the background | Bring the game to the foreground, then try again |
| `“Save” is already disabled, but kotcm has no copy of your base` | kotcm's data was deleted while a base was loaded | Restart the game: it reloads your base from the server |
| The game closes during **Try** | A trap you don't own (see [Read this before](#read-this-before-loading-a-base-into-the-game)) | Relaunch the game: your base is back. Remove that trap from the kotcm base |
| The step 4 tests fail | Incomplete installation | Redo step 3, then step 4 |

## Limitations

- **King of Thieves 2.84 only** for the loading into the game: the tool
  writes into the game's memory at addresses recorded on this version, and
  they have to be found again with every game update. The offline editor
  doesn't depend on the game version.
- **MEmu on Windows only** (64-bit Android, root).
- **Moves in the editor reach the server** while a base is loaded (see
  [Read this before](#read-this-before-loading-a-base-into-the-game));
  blocking them may come in a later version.
- Placement rules are exact for the door, the totem, the saw, the blue guard
  and the bloodhound; for the other traps, only the rules common to all traps
  are checked (*not verified*).
- The interface and messages are in English and French, but the code itself
  (names, comments, docstrings) is in French.

## Credits

- **OvovUsus** (<https://github.com/OvovUsus>), author of the *Creative Mode
  Mod Menu*, of the digitized base shapes and of the reverse engineering on
  2.76 this tool is built on. Ported with their agreement, under the same
  license.
- The authors of the modded shapes: **Peter Biskup** (spover), **krypt**
  (krp.t), **Soruem** (complore) and **Disconnect** (4disc0nnect4).

## License

GPL-3.0, like the original mod: see [LICENSE](LICENSE).
