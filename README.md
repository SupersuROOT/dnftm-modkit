# DNFTM ModKit

**English** | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md)

An unofficial modding kit for **Do Not Feed the Monkeys** (Fictiorama Studios, 2018): a runtime mod loader, an
installer, a browser-based cage editor and two story cages made with it.

> This project is not affiliated with or endorsed by Fictiorama Studios or the game's publishers. You need your own
> copy of the game (Windows, Steam or GOG). The repository contains **no game files**: no game DLLs, no extracted
> pictures, no game text. The loader patches the game on the player's own machine.

## What's inside

| | Version | |
|---|---|---|
| ModLoader (`src/ModLoader`) | 0.5.10 | Loads cages from the game's `Mods` folder at runtime: new cages, scene templates with your own PNG art and animations, notebook pages, browser pages, news and ending pictures, prizes on the shelf. Adds a **MODS** page to the main menu. |
| Installer (`src/Installer`) | 0.5.10 | Injects the loader's hooks into the game's `Assembly-UnityScript.dll` (with Mono.Cecil) and keeps a backup; option 2 restores it. |
| Editor (`editor/`) | 0.5.0 | Open `editor/index.html` in Chrome or Edge. Edits everything the loader supports, checks cages for mistakes that would break the game, reads and writes the `Mods` folder directly. |
| Moth Screen (`data/MothScreen`) | 2.5 | A 7-day story cage: you watch the desktop and microphone of a teenage hacker hired to find a woman's address. Searches, deductions, phone calls, chat, a door visit, several endings. English and Simplified Chinese. |
| Going Down (`data/LiftCam`) | 0.6.2 | A fake cage: the CCTV camera of an apartment-block lift. No keywords; just watch. English and Simplified Chinese. |

## Playing (players)

Download `DNFTM-Cages-<version>.zip` from the Releases page, then:

1. Copy **all** files of the zip into the game folder (next to `dnftm.exe`).
2. Run `DNFTM-ModInstaller.exe` and type `1`. The first line shows the installer and loader versions, e.g.
   `DNFTM Mod Installer 0.5.10 (ModLoader 0.5.10)`.
3. Start the game. The main-menu notebook has a new **MODS** page: tick the cages and start a **new game**.

To uninstall, run the installer again and type `2`, then delete the `Mods` folder.

## Making cages (modders)

Download `DNFTM-ModKit-<version>.zip` (installer, loader, the two cages, the editor), or use this repository.
Editor guide: `editor/README_编辑器说明.txt` (Simplified Chinese).

The public editor has **no scene previews** (they would be the game's own art). If you own the game, rebuild the
full catalog from your copy in a few seconds (step-by-step guide in Chinese: `editor/README_從遊戲提取預覽圖.txt`):

```bash
python -m pip install UnityPy Pillow opencc
python tools/build_catalog.py "<game>/dnftm_Data" editor/catalog.js
```

Keep that file to yourself: it contains the game's pictures.

### mod.json features of loader 0.5.10

| Key | Since | What |
|---|---|---|
| `cages` `[{id, insertAt}]` | ≤ 0.5 | Register cages (cage JSON in `files/<id>.json`, texts in `merge/loc/{en,ch}.json`). |
| `sceneTemplates` `[{id, cloneFrom, keepCameras, art}]` | ≤ 0.5 | Copy a game scene; `art` builds cameras from your own PNGs (objects, sprite sheets, animations, night layers). |
| `cameraEffects` `[{story, cloneFrom}]` | ≤ 0.5 | Fixed camera look of a cage. |
| image paths `mods/<Mod>/<file>` | 0.5 | Your PNGs in news, browser pages, chat avatars, endings, door visitors. |
| `diaryPages[].words / keep / actions` | 0.5.3 | Notebook page cloned from a game cage: keyword → slot, kept circles and arrows, phone/chat buttons. |
| `diaryPages[].main / upper / copies` | 0.5.4 | Words that can be picked in calls/chats/missions, capitalised names, copied boxes and slots. |
| `diaryPages[].selectors` | 0.5.5 | Deductions: the "?" on a circle with three answers. |
| `diaryPages[].moves` | 0.5.6 | Move parts of the page; `sx`/`sy` scale them (0.5.9). |
| `minLoader` | ≤ 0.5 | The MODS page tells players to update an older loader. |
| `prizes` `[{id, template, x, y, image, selected, popup}]` | 0.5.10 | A prize's own object on the room's prize shelf (without one the game freezes when the prize is received). |

### Building from source

Loader and installer (.NET 8 SDK; the loader targets .NET 3.5 like the game and compiles against the game's own
DLLs, so point it at your game):

```bash
cd src/ModLoader && dotnet build -c Release -p:GameManaged="<game>/dnftm_Data/Managed"
cd ../Installer  && dotnet build -c Release
```

The version of both is set once in `src/Directory.Build.props` and must match `Version` in
`src/ModLoader/Hooks.cs`.

Cages (Python 3 with Pillow and numpy: `python -m pip install Pillow numpy`). Build into a scratch folder, then copy
into `data/` (text ids stay stable because the builders read the previous `data/` files):

```bash
python tools/build_moth.py /tmp/out     # -> /tmp/out/MothScreen
python tools/build_liftcam.py /tmp/out  # -> /tmp/out/LiftCam
```

Release packages: `python tools/make_release.py 1.0` (stops if any version disagrees).

### Layout

```
src/            ModLoader and installer (C#)
editor/         browser editor (catalog.js without the game's pictures)
tools/          cage builders, art helpers, catalog extraction, release script
data/           the two cages as they go into the game's Mods folder (+ STORY.md design notes, spoilers!)
art_override/   final art of the cages (made for this project)
release/        player readme and these repository files
```

## License

MIT (see `LICENSE`) for the code, the editor, the cages and their art. *Do Not Feed the Monkeys* and its assets
belong to their owners and are not part of this project.

