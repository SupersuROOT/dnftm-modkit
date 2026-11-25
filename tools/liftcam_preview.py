"""
Replays the built "Going Down" cage the way the game runs it and checks / draws the staging.

    python -I tools/liftcam_preview.py <built LiftCam dir> audit
    python -I tools/liftcam_preview.py <built LiftCam dir> says  <scene> <out.png> [--nv]
    python -I tools/liftcam_preview.py <built LiftCam dir> steps <scene> <out.png> [who,who] [--nv]

audit: for every scene, at every line and every walking step:
  - two people standing on (almost) the same spot;
  - draw order against depth: of two overlapping people, the one whose feet are lower in the picture (closer to the
    lens) must be drawn in front;
  - a person walking through somebody who stands still;
  - a landing twin visible while the doors are not open;
  - a person talking while hidden.
--nv renders with night vision on (nightVision layers hidden, nightVisionOnly layers shown).
Kept in the project (v0.7) because the scratchpad copies of these checks were lost twice.
"""
import json, os, sys
from PIL import Image, ImageDraw

H = 174
D = sys.argv[1]
mod = json.load(open(os.path.join(D, 'mod.json')))
cage = json.load(open(os.path.join(D, 'files', 'liftCam.json')))
en = json.load(open(os.path.join(D, 'merge', 'loc', 'en.json')))['liftCam']
OBJS = {o['name']: o for o in mod['sceneTemplates'][0]['art']['cameras'][0]['objects']}
PEOPLE = ('pruitt', 'haldane', 'rafi', 'mila', 'gus', 'toby', 'mom', 'grey', 'tech', 'dev', 'priya', 'dog')
FEET = {n: (32, 96) for n in PEOPLE}; FEET['dog'] = (14, 22)
SHEETS = {}

def frame_img(o, idx):
    if 'sheet' in o:
        key = o['sheet']['image']
        if key not in SHEETS: SHEETS[key] = Image.open(os.path.join(D, key)).convert('RGBA')
        sh = SHEETS[key]; w, h = o['sheet']['w'], o['sheet']['h']; cols = sh.width // w
        return sh.crop(((idx % cols) * w, (idx // cols) * h, (idx % cols + 1) * w, (idx // cols + 1) * h))
    key = o['image']
    if key not in SHEETS: SHEETS[key] = Image.open(os.path.join(D, key)).convert('RGBA')
    return SHEETS[key]

def size_of(o):
    if 'sheet' in o: return o['sheet']['w'], o['sheet']['h']
    return frame_img(o, 0).size

def text_of(a):
    try: return en.get(a['text'].split('~')[0].split('_')[1], '?')
    except Exception: return '?'

def order():
    out, s = [], 'start'
    while s and s not in out:
        out.append(s); s = cage['script']['scenes'][s].get('goto')
    return out

class State:
    def __init__(self):
        self.s = {n: {'on': True, 'pos': (o['x'], o['y']), 'anim': 'default', 'z': o['z']} for n, o in OBJS.items()}
    def feet(self, n):
        o = OBJS[n]; x, y = self.s[n]['pos']; w, h = size_of(o)
        if n in FEET or n[:-1] in FEET:
            fx, fy = FEET.get(n, FEET.get(n[:-1]))
            return x + fx, H - y - h + fy
        return x + w / 2, H - y
    def frame(self, n):
        o = OBJS[n]
        if 'sheet' not in o: return frame_img(o, 0)
        an = o['animations'].get(self.s[n]['anim']) or o['animations'].get('default') or next(iter(o['animations'].values()))
        return frame_img(o, an['frames'][0])
    def visible(self, n, nv=False):
        o = OBJS[n]
        if not self.s[n]['on']: return False
        if o.get('role') == 'nightVisionOnly' and not nv: return False
        if o.get('role') == 'nightVision' and nv: return False
        return True
    def bbox(self, n):
        fr = self.frame(n); bb = fr.getbbox()
        if not bb: return None
        x, y = self.s[n]['pos']; top = H - y - fr.height
        return (x + bb[0], top + bb[1], x + bb[2], top + bb[3])
    def render(self, caption='', nv=False):
        im = Image.new('RGBA', (252, H), (0, 0, 0, 255))
        for n in sorted(OBJS, key=lambda k: -self.s[k]['z']):
            if not self.visible(n, nv): continue
            fr = self.frame(n); x, y = self.s[n]['pos']
            im.alpha_composite(fr, (int(round(x)), int(round(H - y - fr.height))))
        if nv:
            g = im.convert('L').point(lambda v: min(255, int(v * 1.6)))
            im = Image.merge('RGBA', (g.point(lambda v: v // 4), g, g.point(lambda v: v // 4), Image.new('L', g.size, 255)))
        c = Image.new('RGBA', (252, H + 26), (255, 255, 255, 255)); c.paste(im, (0, 0))
        d = ImageDraw.Draw(c); d.text((2, H + 1), caption[:60], fill=(0, 0, 0)); d.text((2, H + 13), caption[60:120], fill=(0, 0, 0))
        return c

def doors_open(st):
    return st.s['doors']['anim'].rstrip('N') in ('open', 'isOpen', 'pried')

def check(st, where, issues, walking=None):
    vis = [p for p in PEOPLE if st.visible(p)]
    feet = {p: st.feet(p) for p in vis}
    for i, a in enumerate(vis):
        for b in vis[i + 1:]:
            (ax, ay), (bx, by) = feet[a], feet[b]
            if walking is None and abs(ax - bx) < 12 and abs(ay - by) < 8 and 'dog' not in (a, b):
                issues.append('%s: %s and %s stand on the same spot (%d,%d)/(%d,%d)' % (where, a, b, ax, ay, bx, by))
            ba, bb = st.bbox(a), st.bbox(b)
            if not ba or not bb: continue
            ov = min(ba[2], bb[2]) - max(ba[0], bb[0]) > 2 and min(ba[3], bb[3]) - max(ba[1], bb[1]) > 2
            if ov and abs(ay - by) >= 3:
                front, back = (a, b) if ay > by else (b, a)
                if st.s[front]['z'] >= st.s[back]['z']:
                    issues.append('%s: %s (feet y %d) is drawn behind %s (feet y %d)' % (where, front, max(ay, by), back, min(ay, by)))
            if walking in (a, b):
                other = b if walking == a else a
                if other != 'dog' and walking != 'dog' and ((ax - bx) ** 2 + (ay - by) ** 2) ** 0.5 < 9:
                    issues.append('%s: %s walks through %s' % (where, walking, other))
    for n in OBJS:
        if n.endswith('H') and n[:-1] in PEOPLE and st.visible(n) and not doors_open(st):
            issues.append('%s: landing twin %s visible with the doors %s' % (where, n, st.s['doors']['anim']))

def run(mode='audit', scene_want=None, who=None, nv=False):
    st = State(); issues = []; pics = []
    for scn in order():
        s = cage['script']['scenes'][scn]; k = 0
        for a in s['script']:
            n = a.get('id'); act = a.get('action')
            if n not in st.s: continue
            if act == 'enable': st.s[n]['on'] = True
            elif act == 'disable': st.s[n]['on'] = False
            elif act == 'setin': st.s[n]['pos'] = (a['position']['x'], a['position']['y'])
            elif act == 'setz': st.s[n]['z'] = a['z']
            elif act == 'animation': st.s[n]['anim'] = a['animation']
            elif act == 'move':
                x0, y0 = st.s[n]['pos']; x1, y1 = a['position']['x'], a['position']['y']
                if 'subanimation' in a: st.s[n]['anim'] = a['subanimation']
                steps = max(1, int(round(a['time'] / 0.12)))
                for i in range(1, steps + 1):
                    st.s[n]['pos'] = (x0 + (x1 - x0) * i / steps, y0 + (y1 - y0) * i / steps)
                    if mode == 'audit' and n in PEOPLE: check(st, '%s move %s' % (scn, n), issues, walking=n)
                    if mode == 'steps' and scn == scene_want and (not who or n in who or n[:-1] in who):
                        pics.append(st.render('%s %s' % (n, st.s[n]['anim']), nv))
                st.s[n]['anim'] = a.get('endAnimation', 'default' if 'subanimation' in a else st.s[n]['anim'])
            elif act == 'say':
                k += 1
                if 'subanimation' in a: st.s[n]['anim'] = a['subanimation']
                if mode == 'audit':
                    check(st, '%s #%d %s' % (scn, k, n), issues)
                    if n in PEOPLE and not st.visible(n): issues.append('%s #%d: %s talks while hidden' % (scn, k, n))
                if mode == 'says' and scn == scene_want:
                    pics.append(st.render('#%d %s: %s' % (k, n, text_of(a)), nv))
                if 'endanimation' in a: st.s[n]['anim'] = a['endanimation']
    return issues, pics

def sheet(pics, out, cols=4):
    if not pics: print('nothing to draw'); return
    w, h = pics[0].size
    sh = Image.new('RGBA', (cols * (w + 4), ((len(pics) + cols - 1) // cols) * (h + 4)), (255, 255, 255, 255))
    for i, p in enumerate(pics): sh.paste(p, ((i % cols) * (w + 4), (i // cols) * (h + 4)))
    sh.resize((sh.width * 2, sh.height * 2), Image.NEAREST).save(out)
    print(len(pics), 'pictures ->', out)

if __name__ == '__main__':
    mode = sys.argv[2]; nv = '--nv' in sys.argv
    args = [x for x in sys.argv[3:] if x != '--nv']
    if mode == 'audit':
        issues, _ = run('audit')
        seen = set()
        for i in issues:
            if i not in seen: print(i); seen.add(i)
        print('issues', len(seen))
    else:
        who = set(args[2].split(',')) if len(args) > 2 else None
        _, pics = run(mode, args[0], who, nv)
        sheet(pics, args[1], cols=4 if mode == 'says' else 8)
