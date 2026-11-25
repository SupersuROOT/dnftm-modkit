"""
Builds the "Going Down" mod folder (Mods/LiftCam) from the delivered art in mod/art_override/liftcam
(liftcam_sprites.py, liftcam_web.py) and the story in liftcam_story.py.

    python -I build_liftcam.py <out Mods dir>

Build into a scratch folder, then copy into mod/data: text ids are kept stable by reading the previous
mod/data/LiftCam loc files.
"""
import json, os, re, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import liftcam_sprites as Sp
import liftcam_story as S
import liftcam_web as Wb

MOD = 'LiftCam'
OUT = os.path.join(sys.argv[1], MOD)
CAGE = S.CAGE
T = S.T
HERE = os.path.dirname(os.path.abspath(__file__))

# ------------------------------------------------------------------ art
if os.path.isdir(OUT): shutil.rmtree(OUT)
artdir = os.path.join(OUT, 'art', CAGE)
L = Sp.build(artdir)
Wb.build(os.path.join(OUT, 'web'))
rel = lambda n: 'art/%s/%s.png' % (CAGE, n)
for k, v in S.SIZES.items():
    if k in L: assert (L[k]['w'], L[k]['h']) == v, (k, v, L[k])

FPS = {'doors': 8, 'display': 2, 'glitch': 10, 'dog': 4, 'car': 1}
NO_LOOP = {('doors', 'open'), ('doors', 'close'), ('glitch', 'burst'), ('glitch', 'roll'), ('haldane', 'wave'), ('dog', 'bark')}
FPS_ANIM = 3   # entering / leaving frames

objects = []
def obj(name, image=None, pos=None, role=None):
    o = {'name': name, 'pivot': 'bottomLeft', 'z': S.Z[name]}
    o.update(pos or {'x': 0, 'y': 0})
    lay = L.get(image or name)
    if lay and 'anims' in lay:
        o['sheet'] = {'image': rel(image or name), 'w': lay['w'], 'h': lay['h']}
        o['animations'] = {}
        for an, frames in lay['anims'].items():
            walking = an.startswith('enter') or an.startswith('leave')
            loop = len(frames) > 1 and (name, an) not in NO_LOOP and not walking
            o['animations'][an] = {'frames': frames, 'fps': FPS_ANIM if walking else FPS.get(name, 4), 'loop': loop}
    else:
        o['image'] = rel(image or name)
    if role: o['role'] = role
    objects.append(o)

obj('car')
obj('doors', pos=S.tl_pos('doors', *S.DOOR_TL))
obj('display', pos=S.tl_pos('display', *S.DISPLAY_TL))
for p in S.PEOPLE + S.PROPS:
    obj(p, pos=S.feet_pos(p, *(S.DOG if p == 'dog' else S.SPOTS['C'])))
for t in S.TWINS: obj(t, image=t[:-1], pos=S.feet_pos(t, *S.SPOTS['sideL']))   # landing twins share the sheets
obj('jamb')
obj('dark')
obj('darkNV', role='nightVisionOnly')     # v0.7: the dark car under night vision
obj('ghost', pos=S.feet_pos('ghost', *S.SPOTS['L']), role='nightVisionOnly')
obj('glitch')
obj('sfx', 'dot', pos=S.tl_pos('sfx', *S.SFX_TL)); obj('outside', 'dot', pos=S.tl_pos('outside', *S.OUT_TL))

# ------------------------------------------------------------------ news, mails, endings, Shock.tv
news = {k: {'title': T(*t), 'subtitle': T(*s), 'image': img} for k, (t, s, img) in S.NEWS.items()}
emails = {k: {'email': T(*m['email']), 'subject': T(*m['subject']), 'text': T(*m['text'])} for k, m in S.EMAILS.items()}
# no 'recordings' table: the game then sets recordable = false and the cage cannot be recorded
endings = {'frames': {k: {'text': T(en, zh), 'image': img} for k, (en, zh, img) in S.ENDINGS.items()}}

# Scene start/finish events -> named generic events run once by a "triggerEvents" action (the game re-runs
# start/finishEvents while it is paused, which repeated mails every frame in Moth Screen).
generic = dict(S.GENERIC)
for name, sc in S.SCENES.items():
    script = sc['script']
    if sc.get('startEvents'):
        generic[name + '_start'] = sc.pop('startEvents')
        script.insert(1 if script and script[0].get('action') == 'blinkLed' else 0, {'action': 'triggerEvents', 'events': name + '_start', 'id': 'sfx'})
    if sc.get('finishEvents'):
        generic[name + '_finish'] = sc.pop('finishEvents')
        at = len(script) - 1 if script and script[-1].get('action') == 'stopLed' else len(script)
        script.insert(at, {'action': 'triggerEvents', 'events': name + '_finish', 'id': 'sfx'})

cage = {
    'metadata': {'id': CAGE, 'hint': '', 'tmpContainer': CAGE, 'difficulty': 10, 'interest': 60},
    'items': {}, 'prizes': {}, 'chatConfig': {}, 'chats': {}, 'phoneCalls': {}, 'emails': emails, 'news': news,
    'keywords': {}, 'diaryConfig': {'zones': [], 'arrows': [], 'images': []}, 'genericEvents': generic,
    'script': {'metadata': {'cameras': 1, 'id': CAGE, 'startScene': 'start'}, 'predefinedActions': {}, 'scenes': S.SCENES},
}

manifest = {
    'name': 'Going Down',
    'minLoader': '0.5.10',
    'cages': [{'id': CAGE, 'insertAt': 0}],
    'sceneTemplates': [{'id': CAGE, 'cloneFrom': '3', 'keepCameras': 1, 'art': {'cameras': [{'clear': True, 'objects': objects}]}}],
    # the original elevator cage's camera look (colour/noise settings only; none of its art is used)
    'cameraEffects': [{'story': CAGE, 'cloneFrom': 'elevatorCrusoe'}],
    # an empty notebook page: the cage has no keywords at all
    'diaryPages': [{'story': CAGE, 'cloneFrom': 'sayCheese', 'words': {}, 'keep': []}],
}

# ------------------------------------------------------------------ stable text ids (saves keep them)
def _stable_ids():
    base = os.path.join(HERE, '..', 'data', MOD, 'merge', 'loc')
    try:
        old_en = json.load(open(os.path.join(base, 'en.json'), encoding='utf-8'))[CAGE]
        old_ch = json.load(open(os.path.join(base, 'ch.json'), encoding='utf-8'))[CAGE]
    except (OSError, KeyError, ValueError):
        return {i + 1: i + 1 for i in range(len(S.TXT))}, {}, {}
    free, by_en = {}, {}
    for k in sorted(old_en, key=int):
        free.setdefault((old_en[k], old_ch.get(k)), []).append(int(k)); by_en.setdefault(old_en[k], []).append(int(k))
    used, out, nxt, pending = set(), {}, max(map(int, old_en)) + 1 if old_en else 1, []
    for i, (en, zh) in enumerate(S.TXT):
        c = [x for x in free.get((en, zh), []) if x not in used]
        if c: out[i + 1] = c[0]; used.add(c[0])
        else: pending.append(i)
    for i in pending:
        c = [x for x in by_en.get(S.TXT[i][0], []) if x not in used]
        if c: out[i + 1] = c[0]; used.add(c[0])
        else: out[i + 1] = nxt; nxt += 1
    return out, {k: v for k, v in old_en.items() if int(k) not in used}, {k: v for k, v in old_ch.items() if int(k) not in used}
ID, OLD_EN, OLD_CH = _stable_ids()
_idre = re.compile(r'(?<![A-Za-z0-9])%s_(\d+)~' % CAGE)
def _renum(x):
    if isinstance(x, str): return _idre.sub(lambda m: '%s_%d~' % (CAGE, ID[int(m.group(1))]), x)
    if isinstance(x, dict): return {k: _renum(v) for k, v in x.items()}
    if isinstance(x, list): return [_renum(v) for v in x]
    return x

def dump(path, data):
    p = os.path.join(OUT, path); os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8') as f: json.dump(_renum(data), f, ensure_ascii=False, indent=1)

assert not any('[' in en and '[/' in en for en, zh in S.TXT), 'keyword tag found: this cage has no keywords'
dump('mod.json', manifest)
dump('files/%s.json' % CAGE, cage)
dump('merge/loc/en.json', {CAGE: dict(OLD_EN, **{str(ID[i + 1]): en for i, (en, zh) in enumerate(S.TXT)})})
dump('merge/loc/ch.json', {CAGE: dict(OLD_CH, **{str(ID[i + 1]): zh for i, (en, zh) in enumerate(S.TXT)})})
dump('merge/endings.json', endings)
readme = os.path.join(HERE, '..', 'data', MOD, 'README_下行中.txt')
if os.path.isfile(readme): shutil.copy(readme, OUT)

# (art_override/liftcam/spec.json is the art brief's deliverable list: not written here)

says = sum(1 for s in S.SCENES.values() for a in s['script'] if a.get('action') == 'say')
print('scenes', len(S.SCENES), 'says', says, 'texts', len(S.TXT), 'objects', len(objects))
