"""
Builds a public release from the mod/ workspace:

    python -I make_release.py <release name, e.g. 1.0>

dist/release-<name>/
  DNFTM-Cages-<name>.zip    for players: installer, ModLoader, the cages (no story notes)
  DNFTM-ModKit-<name>.zip   for modders: the same + the editor (without the game's pictures) + build_catalog.py
  github/dnftm-modkit/      the source tree for the public repository (+ dnftm-modkit-src-<name>.zip)

Stops when the versions disagree: ModLoader Hooks.Version, src/Directory.Build.props, the built DLLs, the editor's
LOADER_LATEST and every cage's minLoader must all point at the same loader.
Run it after building the loader and the installer in Release (see README.md).
"""
import json, os, re, shutil, subprocess, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.normpath(os.path.join(HERE, '..'))
NAME = sys.argv[1] if len(sys.argv) > 1 else '1.0'
CAGES = ['MothScreen', 'LiftCam']                      # released cages (GhostRoom / NightReader are test cages)
OUT = os.path.join(MOD, 'dist', 'release-' + NAME)
PLAYER_README = ['README.txt', '说明_简体中文.txt', '說明_繁體中文.txt']   # English first (default)
REPO_FILES = ['README.md', 'README.zh-CN.md', 'README.zh-TW.md', 'LICENSE', '.gitignore']

def read(p): return open(os.path.join(MOD, p), encoding='utf-8').read()
def die(msg): sys.exit('RELEASE STOPPED: ' + msg)

# ---------------------------------------------------------------- versions
hooks = re.search(r'const string Version = "([\d.]+)"', read('src/ModLoader/Hooks.cs')).group(1)
props = re.search(r'<Version>([\d.]+)</Version>', read('src/Directory.Build.props')).group(1)
editor = re.search(r"const LOADER_LATEST = '([\d.]+)'", read('editor/core.js')).group(1)
if not hooks == props == editor: die('loader versions differ: Hooks.cs %s, Directory.Build.props %s, editor %s' % (hooks, props, editor))
LOADER = hooks
def ver(v): return tuple(int(x) for x in v.split('.'))
for c in CAGES:
    m = json.loads(read('data/%s/mod.json' % c))
    if ver(m.get('minLoader', '0.0.0')) > ver(LOADER): die('%s needs loader %s, newer than %s' % (c, m['minLoader'], LOADER))
    if m.get('minLoader') != LOADER: die('%s minLoader is %s; the release unifies it to %s' % (c, m.get('minLoader'), LOADER))
BIN = {'DNFTMModLoader.dll': 'src/ModLoader/bin/Release/DNFTMModLoader.dll',
       'DNFTM-ModInstaller.exe': 'src/Installer/bin/Release/net472/DNFTM-ModInstaller.exe',
       'DNFTM-ModInstaller.exe.config': 'src/Installer/bin/Release/net472/DNFTM-ModInstaller.exe.config',
       'Mono.Cecil.dll': 'src/Installer/bin/Release/net472/Mono.Cecil.dll'}
for k, p in BIN.items():
    if not os.path.exists(os.path.join(MOD, p)): die('missing %s: build the loader and the installer in Release first' % p)
blob = open(os.path.join(MOD, BIN['DNFTMModLoader.dll']), 'rb').read()
if LOADER.encode('utf-16-le') not in blob: die('the built DNFTMModLoader.dll is not %s: rebuild it' % LOADER)
inst = open(os.path.join(MOD, BIN['DNFTM-ModInstaller.exe']), 'rb').read()
want = (LOADER + '.0').encode('utf-16-le')
if want not in inst: die('the built installer is not version %s: rebuild it' % LOADER)
print('versions OK: installer, ModLoader, editor and cages all at', LOADER)

# ---------------------------------------------------------------- helpers
if os.path.isdir(OUT): shutil.rmtree(OUT)
os.makedirs(OUT)
SKIP_DIRS = {'__pycache__', 'bin', 'obj', '.git'}
def copytree(src, dst, skip_files=()):
    for root, dirs, files in os.walk(src):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if f in skip_files or f.endswith('.pyc'): continue
            s = os.path.join(root, f); d = os.path.join(dst, os.path.relpath(s, src))
            os.makedirs(os.path.dirname(d), exist_ok=True); shutil.copy2(s, d)
def zipdir(folder, zpath):
    with zipfile.ZipFile(zpath, 'w', zipfile.ZIP_DEFLATED) as z:
        base = os.path.dirname(folder)
        for root, dirs, files in os.walk(folder):
            for f in sorted(files):
                p = os.path.join(root, f); z.write(p, os.path.relpath(p, base))
    print('  ', os.path.relpath(zpath, MOD), '%.1f MB' % (os.path.getsize(zpath) / 1e6))
def cage_files(c, dst):
    """A cage as players get it: the game files and its README, not the story notes or review documents."""
    src = os.path.join(MOD, 'data', c)
    os.makedirs(dst, exist_ok=True)
    for item in os.listdir(src):
        p = os.path.join(src, item)
        if os.path.isdir(p): copytree(p, os.path.join(dst, item))
        elif item == 'mod.json' or (item.startswith('README_') and item.endswith('.txt')): shutil.copy2(p, dst)
def public_editor(dst):
    copytree(os.path.join(MOD, 'editor'), dst, skip_files=('catalog.js',))
    subprocess.check_call([sys.executable, '-I', os.path.join(HERE, 'strip_catalog.py'), os.path.join(MOD, 'editor', 'catalog.js'), os.path.join(dst, 'catalog.js')])

# ---------------------------------------------------------------- players
players = os.path.join(OUT, 'DNFTM-Cages-' + NAME)
os.makedirs(players)
for k, p in BIN.items(): shutil.copy2(os.path.join(MOD, p), os.path.join(players, k))
for c in CAGES: cage_files(c, os.path.join(players, 'Mods', c))
for f in PLAYER_README: shutil.copy2(os.path.join(MOD, 'release', f), players)
zipdir(players, players + '.zip')

# ---------------------------------------------------------------- modders
kit = os.path.join(OUT, 'DNFTM-ModKit-' + NAME)
shutil.copytree(players, kit)
shutil.copy2(os.path.join(MOD, 'README_安裝說明.txt'), kit)
for f in REPO_FILES[:3]: shutil.copy2(os.path.join(MOD, 'release', 'github', f), kit)   # modder guide in 3 languages
public_editor(os.path.join(kit, 'Editor'))
os.makedirs(os.path.join(kit, 'tools'))
shutil.copy2(os.path.join(HERE, 'build_catalog.py'), os.path.join(kit, 'tools'))
zipdir(kit, kit + '.zip')

# ---------------------------------------------------------------- source repository
repo = os.path.join(OUT, 'github', 'dnftm-modkit')
os.makedirs(repo)
copytree(os.path.join(MOD, 'src'), os.path.join(repo, 'src'))
copytree(os.path.join(MOD, 'tools'), os.path.join(repo, 'tools'))
copytree(os.path.join(MOD, 'art_override'), os.path.join(repo, 'art_override'), skip_files=('review.png',))
for c in CAGES:                                          # game files, README and the story notes (no review files)
    cage_files(c, os.path.join(repo, 'data', c))
    if os.path.exists(os.path.join(MOD, 'data', c, 'STORY.md')): shutil.copy2(os.path.join(MOD, 'data', c, 'STORY.md'), os.path.join(repo, 'data', c))
public_editor(os.path.join(repo, 'editor'))
for f in REPO_FILES: shutil.copy2(os.path.join(MOD, 'release', 'github', f), repo)
for f in ('README_安裝說明.txt',): shutil.copy2(os.path.join(MOD, f), repo)
os.makedirs(os.path.join(repo, 'release'))
for f in PLAYER_README: shutil.copy2(os.path.join(MOD, 'release', f), os.path.join(repo, 'release'))
for f in REPO_FILES:
    os.makedirs(os.path.join(repo, 'release', 'github'), exist_ok=True)
    shutil.copy2(os.path.join(MOD, 'release', 'github', f), os.path.join(repo, 'release', 'github'))
# nothing from the game may be in the repository: no extracted pictures, no game DLLs
for root, dirs, files in os.walk(repo):
    for f in files:
        if f.lower() in ('assembly-unityscript.dll', 'unityengine.dll') or f.endswith('.assets'): die('game file in repo: ' + f)
for p in [os.path.join(repo, 'editor', 'catalog.js'), os.path.join(kit, 'Editor', 'catalog.js')]:
    if 'data:image/png' in open(p, encoding='utf-8').read(): die('game pictures left in ' + p)
zipdir(repo, os.path.join(OUT, 'github', 'dnftm-modkit-src-%s.zip' % NAME))
print('release', NAME, 'in', os.path.relpath(OUT, MOD))
