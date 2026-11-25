"""
Builds the "Going Down" cage art from the delivered pixel art in mod/art_override/liftcam (see
art_brief/LiftCam/美術需求_給Codex.md and guide/spec.json), plus the few layers made by code:
night / lights-off versions of the car, the floor-number digits, the signal glitches and the night-vision ghost.

    build(out_dir) -> layout {name: {w, h, anims?}}, spec

Character frames are 64x100 with the feet at (32, 96). Here every frame goes into a 64x122 cell: standing
frames at the top, sitting frames 22 px lower (the brief draws them higher), so one feet point works for both.
"""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageOps
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import liftcam_art as Old          # glitch frames and the 3x5 font

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'art_override', 'liftcam')
W, H = 252, 174
DOOR_BOX = (84, 10, 172, 152)            # x0, y0, x1, y1 (inclusive): the door variants are cut from here
DISPLAY_BOX = (112, 6, 131, 16)
CELL = (64, 122)                         # character cell: 64x100 frame + 22 px for sitting frames
FEET = (32, 96)
SIT_DY = 22
DOG_CELL = (28, 24)

def img(rel):
    p = os.path.join(ROOT, rel + '.png')
    if not os.path.isfile(p): raise SystemExit('missing art: ' + p)
    return Image.open(p).convert('RGBA')

def sheet(frames, cols=None):
    w, h = frames[0].size
    cols = cols or len(frames)
    rows = (len(frames) + cols - 1) // cols
    out = Image.new('RGBA', (w * cols, h * rows), (0, 0, 0, 0))
    for i, f in enumerate(frames): out.paste(f, ((i % cols) * w, (i // cols) * h))
    return out

def night(im):
    px = im.copy(); p = px.load()
    for y in range(px.height):
        for x in range(px.width):
            r, g, b, a = p[x, y]
            p[x, y] = (int(r * 0.58 + 4), int(g * 0.62 + 6), int(b * 0.82 + 16), a)
    return px

def lights_off(im):
    """Lights off (day 7): almost black, only the steel edges and the door seam hold a little light."""
    px = im.copy(); p = px.load()
    for y in range(px.height):
        for x in range(px.width):
            r, g, b, a = p[x, y]
            v = (r + g + b) / 3
            k = 0.10 if v < 150 else 0.2
            p[x, y] = (int(r * k + 6), int(g * k + 7), int(b * k + 12), 255)
    return px

def lights_off_nv(im):
    """The same dark car as seen through night vision (v0.7): the game only swaps layers when night vision is on, it does
    not brighten them, so the lights-off car stayed black while the night-vision-only ghost glowed. This copy keeps
    the doors, frame and wall panels readable at about half the ghost's brightness."""
    a = np.asarray(im).astype(float)
    v = a[..., :3] @ np.array([0.299, 0.587, 0.114])
    v = 10 + v * 0.36
    out = np.dstack([v * 0.92, v, v * 0.92, np.full(v.shape, 255.0)]).clip(0, 255).astype('uint8')
    return Image.fromarray(out, 'RGBA')

def door_frames():
    names = ['car', 'door_open1', 'door_open2', 'door_open', 'door_pried', 'door_sign']
    x0, y0, x1, y1 = DOOR_BOX
    day = [img('bg/' + n).crop((x0, y0, x1 + 1, y1 + 1)) for n in names]
    frames = day + [night(f) for f in day]
    a = {'closed': [0], 'open': [1, 2, 3], 'close': [2, 1, 0], 'isOpen': [3], 'pried': [4], 'sign': [5]}
    anims = dict(a); anims.update({k + 'N': [i + 6 for i in v] for k, v in a.items()}); anims['default'] = [0]
    return anims, frames

FLOORS = ['G'] + [str(i) for i in range(1, 13)] + ['13', '--', 'off']
def display_frames():
    w, h = DISPLAY_BOX[2] - DISPLAY_BOX[0] + 1, DISPLAY_BOX[3] - DISPLAY_BOX[1] + 1
    frames = []
    for f in FLOORS:
        im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        if f != 'off':
            col = (255, 106, 74, 255) if f == '13' else (255, 180, 60, 255)
            s = f if len(f) == 2 else ' ' + f
            x = (w - Old.text_w(s)) // 2
            Old.text(d, x, (h - 5) // 2, '88', (70, 44, 20, 255)); Old.text(d, x, (h - 5) // 2, s, col)
        frames.append(im)
    anims = {('f' + f.replace('-', 'err')): [i] for i, f in enumerate(FLOORS)}
    anims['default'] = [FLOORS.index('G')]
    anims['blink13'] = [FLOORS.index('13'), FLOORS.index('off')]
    anims['errBlink'] = [FLOORS.index('--'), FLOORS.index('off')]
    return anims, frames

# ------------------------------------------------------------------ characters
# Talking with the back to the camera: the head stays turned for the whole line (one held frame). Alternating
# back_talk / back flipped between "turned round" and "back of the head" four times a second (v0.2).
# 'turn' is the in-between frame when somebody who walked in facing the camera turns to face the doors.
STD = {'default': ['back'], 'habla': ['back_talk'], 'turn': ['back_talk'], 'front': ['front'], 'hablaF': ['front_talk', 'front'],
       'walkF': ['walk_f1', 'walk_f2'], 'walkB': ['walk_b1', 'walk_b2']}
EXTRA = {
    'pruitt': {'sit': ['sit'], 'sitHabla': ['sit_talk', 'sit']},
    'haldane': {'wave': ['wave', 'wave_talk', 'wave'], 'sit': ['sit'], 'sitHabla': ['sit_talk', 'sit']},
    'rafi': {'nobox': ['nobox'], 'noboxHabla': ['nobox_talk'], 'sit': ['sit'], 'sitHabla': ['sit_talk', 'sit']},
    'mila': {'dance': ['dance1', 'dance2', 'dance3', 'dance4'], 'fall': ['fall'], 'fallHabla': ['fall_talk', 'fall'],
             'grimace': ['grimace1', 'grimace2']},
    'gus': {'mop': ['mop1', 'mop2']},
    'toby': {'jump': ['jump1', 'jump2'], 'waveF': ['wave1', 'wave2']},
    'dev': {'carry': ['carry'], 'carryHabla': ['carry_talk'], 'carryTurn': ['carry_talk'], 'carryWalkF': ['carry_walk_f1', 'carry_walk_f2'],
            'carryWalkB': ['carry_walk_b1', 'carry_walk_b2']},
}
EXTRA['dev'] = {}         # v0.7: the wardrobe scene is gone, so are the carrying poses
EXTRA['priya'] = EXTRA['dev']
CHARS = ['pruitt', 'haldane', 'rafi', 'mila', 'gus', 'toby', 'mom', 'grey', 'tech', 'dev', 'priya']

# Back-to-camera talk frames turn the head to the right. Talking to somebody on the left uses the frame mirrored
# (v0.4). Mirroring would swap Haldane's phone, Rafi's parcel and the technician's phone to the other hand, so they
# face straight ahead instead.
NO_MIRROR = {'haldane', 'rafi', 'tech'}
LEFT_TALK = {'hablaL': 'back_talk', 'noboxHablaL': 'nobox_talk', 'carryHablaL': 'carry_talk'}

# Perspective on the way through the doors (v0.5): the doorway is only ~31 px wide at the sill and the landing lies
# further away, while people are ~40 px wide. Walking frames therefore also come shrunk around the feet point, and the
# story picks the size from the feet's y (liftcam_story.scale_at), so people get smaller as they step out.
SCALES = (95, 90, 85, 80, 75, 70, 65, 60)   # 5 % steps (v0.6): smaller jumps in size
WALK_ANIMS = ('walkF', 'walkB', 'carryWalkF', 'carryWalkB')

def shrink(frame, pct, feet=FEET):
    """frame (64x100, feet at FEET) scaled to pct %, feet kept in place; colours from the frame's own palette.

    Detail-preserving (v0.7): each new pixel covers a block of source pixels. A plain average blurred 1-px features
    away (pupils, mouths, outlines: faces looked eyeless at 90 % and below). Here a block that contains a pixel much
    darker than its average and really dark (a pupil, an outline) takes that pixel's colour; failing that, a much
    lighter, near-white pixel (the white of an eye); otherwise the average, snapped to the palette."""
    k = pct / 100.0
    a = np.asarray(frame).astype(float)
    src_rgb, src_a = a[..., :3], a[..., 3]
    lum = src_rgb @ np.array([0.299, 0.587, 0.114])
    pal = np.unique(np.asarray(frame)[np.asarray(frame)[..., 3] > 0][:, :3], axis=0).astype(float)
    W0, H0 = frame.size
    w, h = max(1, round(W0 * k)), max(1, round(H0 * k))
    out = np.zeros((h, w, 4), 'uint8')
    for j in range(h):
        y0, y1 = int(j / k), max(int(j / k) + 1, int(np.ceil((j + 1) / k)))
        for i in range(w):
            x0, x1 = int(i / k), max(int(i / k) + 1, int(np.ceil((i + 1) / k)))
            blk_a = src_a[y0:y1, x0:x1] > 0
            cover = blk_a.mean()
            if cover < 0.43: continue
            rgb = src_rgb[y0:y1, x0:x1][blk_a]; l = lum[y0:y1, x0:x1][blk_a]
            avg = rgb.mean(0); la = l.mean()
            if cover > 0.7 and l.min() < min(la - 38, 75): col = rgb[l.argmin()]
            elif cover > 0.7 and l.max() > max(la + 55, 175): col = rgb[l.argmax()]
            else: col = pal[((pal - avg) ** 2).sum(1).argmin()]
            out[j, i, :3] = col; out[j, i, 3] = 255
    res = Image.new('RGBA', frame.size, (0, 0, 0, 0))
    res.paste(Image.fromarray(out, 'RGBA'), (round(feet[0] - feet[0] * k), round(feet[1] + 1 - (feet[1] + 1) * k)))
    return res

# Pixel fixes applied on top of the delivered art (v0.7): Haldane's sitting face is drawn small and his pupils were
# mid-grey (about the brightness of the skin shadow), so in game he looked eyeless. Each listed pixel gets the
# frame's darkest colour.
EYE_FIX = {('haldane', 'sit'): [(32, 40), (37, 40)], ('haldane', 'sit_talk'): [(32, 40), (37, 40)]}

def fixed(name, pose, im):
    pts = EYE_FIX.get((name, pose))
    if not pts: return im
    a = np.asarray(im).copy()
    op = a[a[..., 3] > 0][:, :3]
    dark = op[(op.astype(int) @ np.array([299, 587, 114])).argmin()]
    for x, y in pts: a[y, x, :3] = dark
    return Image.fromarray(a)

def cell(frame, sitting):
    c = Image.new('RGBA', CELL, (0, 0, 0, 0)); c.paste(frame, (0, SIT_DY if sitting else 0)); return c

def person(name):
    std = dict(STD)
    if name == 'grey': std = {'default': ['back'], 'habla': ['back'], 'turn': ['back'], 'front': ['back'], 'hablaF': ['back'],
                              'walkF': ['walk_f1', 'walk_f2'], 'walkB': ['walk_b1', 'walk_b2']}
    want = dict(std); want.update(EXTRA.get(name, {}))
    order, frames = [], []
    for poses in want.values():
        for p in poses:
            if p not in order:
                order.append(p); frames.append(cell(fixed(name, p, img('people/%s/%s' % (name, p))), p.startswith(('sit', 'fall'))))
    for anim_name in WALK_ANIMS:
        if anim_name not in want: continue
        for pct in SCALES:
            names = []
            for p in want[anim_name]:
                key = '%s@%d' % (p, pct)
                if key not in order:
                    order.append(key); frames.append(cell(shrink(img('people/%s/%s' % (name, p)), pct), False))
                names.append(key)
            want['%s%d' % (anim_name, pct)] = names
    # Optional poses drawn later (v0.7 brief, art_brief/LiftCam/美術需求_第3輪_側耳傾聽.md): back to the camera, head and
    # ear turned to the picture's left. listen_left -> 'listenL' (used while somebody on the left talks);
    # talk_left -> 'hablaL' instead of the mirrored back_talk.
    for pose, anim_name in (('listen_left', 'listenL'), ('talk_left', 'hablaL')):
        if os.path.isfile(os.path.join(ROOT, 'people', name, pose + '.png')):
            order.append(pose); frames.append(cell(img('people/%s/%s' % (name, pose)), False))
            want[anim_name] = [pose]
    for anim_name, src in LEFT_TALK.items():
        if anim_name in want: continue
        base = {'hablaL': 'default', 'noboxHablaL': 'nobox', 'carryHablaL': 'carry'}[anim_name]
        if base not in want: continue
        if name in NO_MIRROR and src == 'back_talk' or name == 'grey':
            want[anim_name] = list(want[base]); continue
        order.append(src + '_L'); frames.append(ImageOps.mirror(cell(img('people/%s/%s' % (name, src)), False)))
        want[anim_name] = [src + '_L']
    order.append('_gone'); frames.append(Image.new('RGBA', CELL, (0, 0, 0, 0)))
    anims = {k: [order.index(p) for p in v] for k, v in want.items()}
    anims['gone'] = [order.index('_gone')]
    return anims, frames

def dog():
    names = ['sit', 'walk1', 'walk2', 'sniff', 'sleep', 'bark']
    frames = [img('people/dog/' + n) for n in names]
    anims = {'default': [0], 'sit': [0], 'walk': [1, 2], 'sniff': [3, 0], 'sleep': [4], 'bark': [5, 0]}
    for pct in SCALES:            # smaller on the landing, like the people (v0.5)
        anims['walk%d' % pct] = [len(frames), len(frames) + 1]
        frames += [shrink(img('people/dog/' + n), pct, (DOG_CELL[0] // 2, DOG_CELL[1] - 2)) for n in ('walk1', 'walk2')]
    return anims, frames

def doorway_mask():
    """Pixels of the doorway: where the open doors show the landing instead of the closed leaves."""
    car = np.asarray(img('bg/car'))[..., :3].astype(int); op = np.asarray(img('bg/door_open'))[..., :3].astype(int)
    m = (np.abs(car - op).sum(2) > 24)
    ys, xs = np.where(m)
    out = np.zeros_like(m)
    for y in range(ys.min(), ys.max() + 1):     # fill each row between the leftmost and rightmost changed pixel
        row = np.where(m[y])[0]
        if len(row): out[y, row.min():row.max() + 1] = True
    # v0.6: the door frame's inner faces (neutral grey strips at both sides) belong to the jamb, not to the landing:
    # people on the landing must walk behind them. Trim neutral grey pixels off both ends of every row.
    def frame_px(px):
        r, g, b = px
        return max(r, g, b) - min(r, g, b) <= 3 and max(r, g, b) >= 55
    rows, lefts, rights = [], [], []
    for y in range(out.shape[0]):
        row = np.where(out[y])[0]
        if not len(row): continue
        a, b = row.min(), row.max()
        while a < b and frame_px(op[y, a]): a += 1
        while b > a and frame_px(op[y, b]): b -= 1
        if y < 118: rows.append(y); lefts.append(a); rights.append(b)
    # the frame edges are straight lines in the picture: fit them (robustly: the outer 80 % of each side) and cut
    # the mask along the lines, so the edge is clean instead of ragged
    ys_, l_, r_ = np.array(rows), np.array(lefts), np.array(rights)
    kl = np.polyfit(ys_, l_, 1); kr = np.polyfit(ys_, r_, 1)
    for _ in range(2):
        rl = l_ - np.polyval(kl, ys_); rr = r_ - np.polyval(kr, ys_)
        okl = rl >= np.percentile(rl, 20); okr = rr <= np.percentile(rr, 80)
        kl = np.polyfit(ys_[okl], l_[okl], 1); kr = np.polyfit(ys_[okr], r_[okr], 1)
    for y in range(out.shape[0]):
        if not out[y].any(): continue
        a, b = int(np.ceil(np.polyval(kl, y))), int(np.floor(np.polyval(kr, y)))
        out[y, :max(a, 0)] = False; out[y, b + 1:] = False
    # the threshold rows: as wide as the doorway, so feet stepping onto the sill are not clipped
    full = out[118].copy()
    for y in range(118, ys.max() + 1): out[y] = full
    return out

def jamb():
    """The car (day / night) with the doorway transparent: people walking on the landing are hidden behind it until
    they reach the doorway, so they step out from behind the door frame instead of popping up."""
    hole = doorway_mask()
    frames = []
    for im in (img('bg/car'), night(img('bg/car'))):
        a = np.asarray(im).copy(); a[hole, 3] = 0; frames.append(Image.fromarray(a))
    return {'default': [0], 'day': [0], 'night': [1]}, frames

def ghost():
    """Night-vision only: the man in the grey hat standing in the dark car."""
    g = cell(img('people/grey/back'), False); p = g.load()
    for y in range(g.height):
        for x in range(g.width):
            r, gg, b, a = p[x, y]
            if a: p[x, y] = (int(r * 0.35 + 36), int(gg * 0.45 + 70), int(b * 0.35 + 36), 255)
    return g

def build(out):
    os.makedirs(out, exist_ok=True)
    L, spec = {}, {}
    def save(name, im):
        p = os.path.join(out, name + '.png'); im.save(p, optimize=True); L[name] = {'w': im.width, 'h': im.height}
    def save_sheet(name, anims, frames, cols=None):
        p = os.path.join(out, name + '.png'); sheet(frames, cols).save(p, optimize=True)
        L[name] = {'w': frames[0].width, 'h': frames[0].height, 'anims': anims}
    car = img('bg/car')
    save_sheet('car', {'default': [0], 'day': [0], 'night': [1]}, [car, night(car)])
    a, f = door_frames(); save_sheet('doors', a, f)
    a, f = display_frames(); save_sheet('display', a, f)
    for n in CHARS:
        a, f = person(n); save_sheet(n, a, f, cols=8)
    a, f = dog(); save_sheet('dog', a, f)
    a, f = jamb(); save_sheet('jamb', a, f)
    for n in ('bucket', 'toolbox'): save(n, img('props/' + n))
    save('dark', lights_off(img('bg/door_sign')))
    save('darkNV', lights_off_nv(img('bg/door_sign')))
    save('ghost', ghost())
    a, f = Old.glitch(); save_sheet('glitch', a, f)
    save('dot', Image.new('RGBA', (1, 1), (0, 0, 0, 0)))
    return L

if __name__ == '__main__':
    print(json.dumps({k: {kk: (sorted(vv) if kk == 'anims' else vv) for kk, vv in v.items()} for k, v in build(sys.argv[1]).items()}, indent=0)[:3000])
