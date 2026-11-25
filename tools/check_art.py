"""
Checks replacement art in mod/art_override before it goes into the build, and makes a review sheet.

    python -I check_art.py [review.png]

For every file in art_override/{web,cam,reflect,browser,prize}: size (exact or integer multiple), transparency rules,
colour count, soft edges (semi-transparent pixels, which look blurry in the game), then a sheet with
current art | replacement side by side, scaled 3x.
"""
import os, sys, warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import moth_art as A
import moth_web as Wb
import moth_prize as Pz

ROOT = A.OVERRIDE_DIR
CAM = (80, 57)
SIZES = {'cam': {k: CAM for k in ('face', 'talk', 'angry', 'scared', 'mask', 'maskTalk', 'empty')},
         'reflect': {k: (252, 174) for k in ('sleep', 'stare', 'empty')},
         'browser': {'kestrel_photo': (130, 80)}, 'prize': dict(Pz.SIZES)}
SIZES['web'] = {name: fn().size for name, fn in Wb.IMAGES.items()}
TRANSPARENT = {('prize', 'prize_jar'), ('prize', 'prize_jar_sel'), ('prize', 'prize_jar_popup'), ('web', 'door_guest'), ('reflect', 'sleep'), ('reflect', 'stare'), ('reflect', 'empty')}

def current(kind, name):
    if kind == 'web': return Wb.IMAGES[name]().convert('RGBA')
    if kind == 'prize':
        return {'prize_jar': Pz.jar(1), 'prize_jar_sel': Pz.outline(Pz.jar(1), (58, 44, 50, 255)), 'prize_jar_popup': Pz.popup()}[name]
    if kind == 'reflect': return A.reflection(name)
    if kind == 'browser':
        _, _, (x0, y0, x1, y1) = A.browser_base('', '')
        return A.b_photo().crop((x0 + 14, y0 + 4, x1 - 13, y1 - 3))
    mood = {'face': 'neutral'}.get(name, name)
    if name in ('mask', 'maskTalk'): return A.face_elias(*CAM, mask=True)
    if name == 'empty': return Image.new('RGBA', CAM, (40, 40, 40, 255))
    return A.face_elias(*CAM, mood)

def check(kind, name, path):
    msgs, im = [], Image.open(path)
    want = SIZES.get(kind, {}).get(name)
    if want is None: return ['unknown file name (not used by the cage)'], None
    im = im.convert('RGBA'); w, h = want
    if im.size != want:
        k = im.width // w
        if k < 1 or im.size != (w * k, h * k): return ['size %dx%d, need %dx%d (or 2x/3x/4x...)' % (im.width, im.height, w, h)], None
        # an upscaled pixel image has k x k blocks of one colour
        small = im.resize(want, Image.NEAREST)
        if small.resize(im.size, Image.NEAREST).tobytes() != im.tobytes():
            msgs.append('%dx upscale is not made of clean %dx%d pixel blocks (blurry or off-grid): will look soft' % (k, k, k))
        im = small
    alpha = [p[3] for p in im.getdata()]
    if (kind, name) in TRANSPARENT:
        if min(alpha) == 255: msgs.append('needs a transparent background')
    elif min(alpha) < 255: msgs.append('must be fully opaque (no transparent pixels)')
    soft = sum(1 for a in alpha if 0 < a < 255)
    if (kind, name) == ('prize', 'prize_jar_popup'):
        # the game's popups have a 1 px black shadow at alpha 153 under the panel (kept from the template)
        soft = sum(1 for p in im.getdata() if 0 < p[3] < 255 and not (p[:3] == (0, 0, 0) and p[3] == 153))
    if soft and kind != 'reflect': msgs.append('%d semi-transparent pixels (anti-aliasing); edges should be hard' % soft)
    colours = len(set(p for p in im.getdata() if p[3]))
    if colours > 64: msgs.append('%d colours: too many for this style (aim for 16-40)' % colours)
    return msgs or ['OK (%d colours)' % colours], im

def main(out):
    rows = []
    for kind in ('web', 'cam', 'reflect', 'browser', 'prize'):
        d = os.path.join(ROOT, kind)
        if not os.path.isdir(d): continue
        for f in sorted(os.listdir(d)):
            if not f.lower().endswith('.png'): continue
            name = f[:-4]
            msgs, im = check(kind, name, os.path.join(d, f))
            print('%-8s %-16s %s' % (kind, name, ' | '.join(msgs)))
            if im is not None: rows.append((kind + '/' + name, current(kind, name), im))
    if not rows: print('nothing in', ROOT); return
    S = 3
    cw = max(max(a.width, b.width) for _, a, b in rows) * S
    ch = sum(max(a.height, b.height) * S + 16 for _, a, b in rows)
    sheet = Image.new('RGBA', (cw * 2 + 30, ch), (48, 48, 48, 255)); d = ImageDraw.Draw(sheet); y = 0
    for label, a, b in rows:
        d.text((4, y + 2), label + '   current  |  new', fill=(255, 230, 0))
        for i, im in enumerate((a, b)):
            big = im.resize((im.width * S, im.height * S), Image.NEAREST)
            bg = Image.new('RGBA', big.size, (20, 20, 24, 255)); bg.alpha_composite(big)
            sheet.alpha_composite(bg, (i * (cw + 30), y + 14))
        y += max(a.height, b.height) * S + 16
    sheet.save(out); print('review sheet:', out)

if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'review.png'))
