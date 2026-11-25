"""
Pixel art for the "Going Down" cage (id liftCam): a CCTV camera high in the back corner of a small, old
apartment elevator, looking steeply down at the doors. Drawn with Pillow at 1:1 scale (view 252x174).

Style follows the original game (checked against its cage backgrounds and character sprites, e.g. Elevator
Crusoe, Red Fred), without reusing any of its images:
  * flat planes with 2-3 hard shade steps, light from the top-left, no gradients or noise;
  * every part outlined in a darker shade of its own colour (not black);
  * people with realistic proportions and the game's faces: big white eyes in black rims under a heavy
    lid, short brows, a one-pixel nose shadow; seen from a high angle, so the crown of the head and the
    shoulders show and the legs are short;
  * 12-18 colours per character.

    python liftcam_art.py <out_dir>
"""
import math, os, random, sys
from PIL import Image, ImageDraw

W, H = 252, 174

def hx(s, a=255):
    s = s.lstrip('#'); return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), a)

def dk(c, f=0.62):
    """Darker, slightly more saturated version of a colour (the game's outline colour)."""
    r, g, b = c[:3]; m = (r + g + b) / 3
    return tuple(max(0, min(255, int((v + (v - m) * 0.25) * f))) for v in (r, g, b)) + (255,)

def lt(c, f=1.18):
    return tuple(min(255, int(v * f + 8)) for v in c[:3]) + (255,)

C = {k: hx(v) for k, v in dict(
    # car
    wood='#8a5b3c', woodL='#a06c49', woodD='#6c442c', woodDD='#4c2f1f',
    brass='#c49a4a', brassL='#e3c27a', brassD='#8c6a2c',
    steel='#9aa3a8', steelL='#b9c0c3', steelD='#79838a', steelDD='#59626a',
    floor='#6f6a5e', floorL='#7f796b', floorLL='#8d8676', floorD='#5c584e', floorDD='#47443c',
    ceil='#3a3634', ceilD='#2b2826',
    hall='#4f4a47', hallD='#3c3836', hallF='#6b625a', hallL='#d8c9a3',
    amber='#ffb43c', amberD='#3a2610', lcd='#17120f', red='#c0463a', redD='#86302a', redL='#df6d5c',
    white='#f4efe4', paper='#e8dcc0', paperD='#c9b994', black='#141210',
    # skin (the game's three-step skin ramp) and a darker ramp
    skin='#e1b290', skinS='#ab7e68', skinD='#805f4f',
    skin2='#b98463', skin2S='#8e604a', skin2D='#694537',
    # clothes and hair
    navy='#3a4a62', grey='#7b7b7b', greyL='#9c9a96', greyD='#555452', charcoal='#4d4c4a',
    lilac='#b7a0cc', mustard='#c9a04a', pink='#d98c98', teal='#3f8f88', yel='#e2b63e',
    green='#5f7f4a', blue='#4b6aa0', brown='#7a5238', cream='#e9dcbc', denim='#4f6284',
    hairDk='#2f2a26', hairBr='#5a3e2c', hairGrey='#b9b4ac', dino='#6aa04a',
    card='#c39a62', cardL='#d9b47e', cardD='#9a7444', tape='#e2cf8a',
).items()}
T = (0, 0, 0, 0)

def new(w, h, col=T): return Image.new('RGBA', (w, h), col)

def sheet(frames):
    w, h = frames[0].size
    out = new(w * len(frames), h)
    for i, f in enumerate(frames): out.paste(f, (i * w, 0))
    return out

FONT = {
 'A': '010101111101101', 'B': '110101110101110', 'C': '011100100100011', 'D': '110101101101110', 'E': '111100110100111',
 'F': '111100110100100', 'G': '011100101101011', 'H': '101101111101101', 'I': '111010010010111', 'K': '101101110101101',
 'L': '100100100100111', 'M': '101111111101101', 'N': '110101101101101', 'O': '010101101101010', 'P': '110101110100100',
 'R': '110101110101101', 'S': '011100010001110', 'T': '111010010010010', 'U': '101101101101111', 'V': '101101101101010',
 'W': '101101111111101', 'X': '101101010101101', 'Y': '101101010010010', '0': '111101101101111', '1': '010110010010111',
 '2': '111001111100111', '3': '111001111001111', '4': '101101111001001', '5': '111100111001111', '6': '111100111101111',
 '7': '111001001001001', '8': '111101111101111', '9': '111101111001111', '-': '000000111000000', ' ': '000000000000000',
 '.': '000000000000010', '/': '001001010100100', 'M2': '',
}
def text(d, x, y, s, col):
    for ch in s:
        g = FONT.get(ch.upper(), FONT[' '])
        for i, b in enumerate(g):
            if b == '1': d.point((x + i % 3, y + i // 3), fill=col)
        x += 4
    return x
def text_w(s): return len(s) * 4 - 1

# ------------------------------------------------------------------ part painter
def paint(img, shapes, base, shade=None, light=None, line=None, split=0.62, lsplit=0.3, ldepth=0.35, outline=True):
    """Fills the union of shapes [('poly', pts) | ('ell', box) | ('rect', box)] on img with the game's
    flat shading: base colour, the right part in shade, a top-left light patch, and a 1px outline in a
    darker shade of the same colour."""
    m = Image.new('L', img.size, 0); d = ImageDraw.Draw(m)
    for kind, g in shapes:
        if kind == 'poly': d.polygon([(round(x), round(y)) for x, y in g], fill=255)
        elif kind == 'ell': d.ellipse(tuple(round(v) for v in g), fill=255)
        else: d.rectangle(tuple(round(v) for v in g), fill=255)
    bb = m.getbbox()
    if not bb: return
    x0, y0, x1, y1 = bb
    shade = shade or dk(base, 0.82); line = line or dk(base, 0.6)
    mp, px = m.load(), img.load()
    w, h = img.size
    for y in range(y0, y1):
        for x in range(x0, x1):
            if not mp[x, y]: continue
            edge = outline and any(not (0 <= x + a < w and 0 <= y + b < h and mp[x + a, y + b]) for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            if edge: c = line
            elif x >= x0 + (x1 - x0) * split: c = shade
            elif light and x < x0 + (x1 - x0) * lsplit and y < y0 + (y1 - y0) * ldepth: c = light
            else: c = base
            px[x, y] = c

def ell(cx, cy, rx, ry): return ('ell', (cx - rx, cy - ry, cx + rx, cy + ry))
def poly(*pts): return ('poly', pts)
def rect(x0, y0, x1, y1): return ('rect', (x0, y0, x1, y1))

# ------------------------------------------------------------------ geometry of the car (image coords)
# A very small car seen from a ceiling camera right above the back wall, with a wide lens: the doors at the
# top, a little floor, the side walls bowing outwards (barrel distortion, like the game's ATM camera).
# Layout is planned undistorted, then every point goes through fish().
FC = (126, 92)                 # distortion centre
FISH = 0.16
def fish(p):
    x, y = p; dx, dy = (x - FC[0]) / 150, (y - FC[1]) / 150
    k = 1 + FISH * (dx * dx + dy * dy)
    return (FC[0] + (x - FC[0]) * k, FC[1] + (y - FC[1]) * k)

def fpoly(*pts, n=14):
    """Polygon with every edge subdivided, then distorted."""
    out = []
    for i, a in enumerate(pts):
        b = pts[(i + 1) % len(pts)]
        for j in range(n):
            t = j / n; out.append(fish((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)))
    return ('poly', out)

def fline(d, a, b, fill, width=1, n=20):
    d.line([fish((a[0] + (b[0] - a[0]) * j / n, a[1] + (b[1] - a[1]) * j / n)) for j in range(n + 1)], fill=fill, width=width)

FAR = 90                       # far floor edge (foot of the door wall), undistorted
FX0, FX1 = 90, 162
NX0, NX1 = 22, 230             # floor edge at the bottom of the frame
def xl(y): return FX0 + (y - FAR) * (NX0 - FX0) / (H - FAR)
def xr(y): return FX1 + (y - FAR) * (NX1 - FX1) / (H - FAR)
NAD = (126, 250)
def up(px, py, k): return (px + (px - NAD[0]) * k, py + (py - NAD[1]) * k)

DOOR_POLY = [fish(p) for p in ((103, 88), (149, 88), (153, 16), (99, 16))]
DOOR_POLY = [(round(x), round(y)) for x, y in DOOR_POLY]
DOOR = (min(p[0] for p in DOOR_POLY), min(p[1] for p in DOOR_POLY), max(p[0] for p in DOOR_POLY), max(p[1] for p in DOOR_POLY))
DISPLAY_TL = (114, 2)
SLOTS = {'L': 78, 'C': 126, 'R': 174}        # where the busts stand (centre x)
DOGSPOT = (126, 100)                          # the little bit of floor that stays visible between people

def car(mode='day'):
    im = new(W, H, C['wood']); d = ImageDraw.Draw(im)
    # side walls: wood veneer panels; seams follow the wall verticals (rays from the nadir)
    for side, edge in ((-1, xl), (1, xr)):
        ys = [FAR - 10, FAR + 34, H + 80]
        for i in range(len(ys) - 1):
            a, b = (edge(ys[i]), ys[i]), (edge(ys[i + 1]), ys[i + 1])
            q = fpoly(a, b, up(*b, 9), up(*a, 9))
            base = (C['woodL'] if i % 2 else C['wood']) if side < 0 else (C['wood'] if i % 2 else C['woodD'])
            paint(im, [q], base, base, None, C['woodDD'], outline=False)
            fline(d, a, up(*a, 9), C['woodDD'])
        pts = [(edge(y), y) for y in range(FAR - 10, H + 80, 6)]
        paint(im, [fpoly(*(pts + [up(x, y, 0.07) for x, y in pts][::-1]), n=2)], C['steelD'], C['steelD'], None, C['steelDD'], outline=False)
        for k, col, wdt in ((0.07, C['steelL'], 1), (0.40, C['brassD'], 4), (0.40, C['brass'], 2)):
            d.line([fish(up(x, y, k)) for x, y in pts], fill=col, width=wdt)
        d.line([(x, y - 1) for x, y in (fish(up(x, y, 0.40)) for x, y in pts)], fill=C['brassL'])
    # far wall: brushed steel around the doors
    fl, fr = up(FX0, FAR, 2.5), up(FX1, FAR, 2.5)
    paint(im, [fpoly((FX0, FAR), (FX1, FAR), fr, fl)], C['steel'], C['steel'], None, C['steelDD'])
    for x in range(FX0 + 3, FX1 - 1, 6):
        fline(d, (x, FAR - 3), up(x, FAR, 2.5), C['steelL'] if (x // 6) % 2 else C['steelD'])
    fline(d, (FX0, FAR), fl, C['woodDD'], 2); fline(d, (FX1, FAR), fr, C['steelDD'], 2)
    # door frame, opening (the leaves are a sprite), display bezel, threshold
    frame = [fish(p) for p in ((97, 92), (155, 92), (160, 10), (92, 10))]
    paint(im, [('poly', frame)], C['steelL'], C['steelL'], None, C['steelDD'])
    paint(im, [('poly', DOOR_POLY)], C['hallD'], C['hallD'], None, C['black'])
    paint(im, [rect(DISPLAY_TL[0] - 1, DISPLAY_TL[1] - 1, DISPLAY_TL[0] + 24, DISPLAY_TL[1] + 8)], C['steelDD'], None, None, C['black'])
    paint(im, [fpoly((100, 87), (152, 87), (154, 94), (98, 94), n=3)], C['steelD'], C['steelD'], None, C['steelDD'])
    fline(d, (101, 90), (151, 90), C['steelL'])
    # button panel (brass) on the right wall next to the door, inspection certificate on the left
    a, b = (xr(FAR + 1), FAR + 1), (xr(FAR + 7), FAR + 7)
    paint(im, [fpoly(up(*a, 0.36), up(*b, 0.36), up(*b, 0.52), up(*a, 0.52), n=4)], C['brass'], C['brass'], C['brassL'], C['brassD'])
    for i in range(5):
        for t in (0.3, 0.75):
            p = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
            x, y = fish(up(*p, 0.38 + i * 0.03)); d.point((round(x), round(y)), fill=C['paper'])
    x, y = fish(up(a[0] + 3, a[1] + 3, 0.5)); d.rectangle((round(x) - 1, round(y), round(x), round(y) + 1), fill=C['red'])
    a, b = (xl(FAR + 4), FAR + 4), (xl(FAR + 14), FAR + 14)
    paint(im, [fpoly(up(*a, 0.5), up(*b, 0.5), up(*b, 0.64), up(*a, 0.64), n=4)], C['paper'], C['paperD'], None, C['brassD'], split=0.85)
    # floor: worn rubber tiles with the lamp's light pool in hard bands
    paint(im, [fpoly((FX0, FAR), (FX1, FAR), (NX1, H + 20), (NX0, H + 20))], C['floor'], C['floor'], None, C['floorDD'], outline=False)
    fpx = Image.new('L', (W, H), 0); ImageDraw.Draw(fpx).polygon(fpoly((FX0 + 1, FAR + 1), (FX1 - 1, FAR + 1), (NX1, H + 20), (NX0, H + 20))[1], fill=255)
    m, px = fpx.load(), im.load()
    for y in range(H):
        for x in range(W):
            if not m[x, y]: continue
            r = math.hypot((x - 126) / 1.25, y - 132)
            px[x, y] = C['floorLL'] if r < 26 else C['floorL'] if r < 46 else C['floor'] if r < 70 else C['floorD']
    for i in range(1, 4):
        t = i / 4; fline(d, (FX0 + (FX1 - FX0) * t, FAR), (NX0 + (NX1 - NX0) * t, H + 20), C['floorD'])
    for yy in (108, 136):
        fline(d, (xl(yy), yy), (xr(yy), yy), C['floorD'])
    # the lens: curved hard-edged bands darken the corners (the game's ATM camera does the same)
    for y in range(H):
        for x in range(W):
            r = math.hypot((x - 126) / 140, (y - 96) / 104)
            if r > 1.0:
                c = px[x, y]; f = 0.78 if r < 1.12 else 0.62
                px[x, y] = (int(c[0] * f), int(c[1] * f), int(c[2] * f), 255)
    if mode == 'night':
        for y in range(H):
            for x in range(W):
                r, g, b, a = px[x, y]
                px[x, y] = (int(r * 0.42 + 6), int(g * 0.46 + 8), int(b * 0.62 + 18), a)
    return im

def doors():
    """Door leaves inside the (trapezoid) opening: closed, opening 1-2, open (corridor), pried, sign."""
    x0, y0, x1, y1 = DOOR
    w, h = x1 - x0 + 1, y1 - y0 + 1
    P = [(x - x0, y - y0) for x, y in DOOR_POLY]
    def at(t, y):   # x on the opening at height y, t 0..1 from left to right edge
        f = (y - P[3][1]) / (P[0][1] - P[3][1])
        l = P[3][0] + (P[0][0] - P[3][0]) * f; r = P[2][0] + (P[1][0] - P[2][0]) * f
        return l + (r - l) * t
    def corridor(img):
        paint(img, [poly(*P)], C['hall'], C['hallD'], None, C['black'], split=0.85)
        d = ImageDraw.Draw(img)
        fy = int(h * 0.55)
        paint(img, [poly((at(0, fy), fy), (at(1, fy), fy), P[1], P[0])], C['hallF'], C['hallF'], None, C['hallD'], outline=False)
        paint(img, [rect(at(0.36, 16), 12, at(0.64, 16), fy - 1)], C['woodD'], C['woodDD'], None, C['woodDD'])   # flat door opposite
        d.point((round(at(0.58, 24)), 24), fill=C['brassL'])
        paint(img, [rect(at(0.08, 10), 8, at(0.08, 10) + 5, 11)], C['hallL'], None, None, C['brassD'])   # wall lamp
    def leaves(gap, sign=False):
        img = new(w, h); corridor(img)
        for side in (0, 1):
            if side == 0: q = [(at(0, P[3][1]), P[3][1]), (at(0.5, P[3][1]) - gap / 2, P[3][1]), (at(0.5, P[0][1]) - gap / 2, P[0][1]), (at(0, P[0][1]), P[0][1])]
            else: q = [(at(0.5, P[3][1]) + gap / 2, P[3][1]), (at(1, P[3][1]), P[3][1]), (at(1, P[0][1]), P[0][1]), (at(0.5, P[0][1]) + gap / 2, P[0][1])]
            if q[1][0] - q[0][0] < 2: continue
            paint(img, [poly(*q)], C['steel'], C['steelD'], C['steelL'], C['steelDD'], split=0.86 if side else 0.9, lsplit=0.25, ldepth=1.0)
        d = ImageDraw.Draw(img)
        for t in (0.25, 0.75):
            if gap < 10: d.line([(at(t, 6), 6), (at(t, h - 4), h - 4)], fill=C['steelL'])
        if sign:
            paint(img, [poly((at(0.3, 14), 14), (at(0.7, 14), 14), (at(0.7, 28), 28), (at(0.3, 28), 28))], C['white'], C['paper'], None, C['red'], split=0.9)
            text(d, round(at(0.3, 16)) + 3, 16, 'OUT OF', C['red']); text(d, round(at(0.3, 22)) + 4, 22, 'ORDER', C['red'])
            d.line([(at(0.08, 6), 6), (at(0.92, 38), 38)], fill=C['yel'], width=3)
            d.line([(at(0.08, 38), 38), (at(0.92, 6), 6)], fill=C['yel'], width=3)
        return img
    pried = leaves(16)
    d = ImageDraw.Draw(pried)
    d.polygon([(at(0.46, 6), 6), (at(0.54, 6), 6), (at(0.9, h - 1), h - 1), (at(0.1, h - 1), h - 1)], fill=(255, 238, 180, 110))
    paint(pried, [ell(at(0.5, 8), 8, 3, 3)], C['white'], C['paper'], None, C['yel'])
    paint(pried, [rect(at(0.5, 30) - 10, 28, at(0.5, 30) - 6, 33)], C['yel'], None, None, dk(C['yel']))
    paint(pried, [rect(at(0.5, 30) + 6, 28, at(0.5, 30) + 10, 33)], C['yel'], None, None, dk(C['yel']))
    frames = [leaves(0), leaves(16), leaves(34), leaves(80), pried, leaves(0, sign=True)]
    return {'closed': [0], 'open': [1, 2, 3], 'close': [2, 1, 0], 'isOpen': [3], 'pried': [4], 'sign': [5], 'default': [0]}, frames

FLOORS = ['G'] + [str(i) for i in range(1, 13)] + ['13', '--', 'off']
def display():
    frames = []
    for f in FLOORS:
        im = new(24, 8, C['lcd']); d = ImageDraw.Draw(im)
        d.rectangle((0, 0, 23, 7), outline=C['black'])
        if f != 'off':
            col = C['amber'] if f != '13' else C['redL']
            s = f if len(f) == 2 else ' ' + f
            x = 12 - text_w(s) // 2 - 1
            text(d, x, 1, '88', C['amberD']); text(d, x, 1, s, col)
            d.polygon([(19, 2), (21, 2), (20, 1)], fill=C['amberD']); d.polygon([(19, 5), (21, 5), (20, 6)], fill=C['amberD'])
        frames.append(im)
    anims = {('f' + f.replace('-', 'err')): [i] for i, f in enumerate(FLOORS)}
    anims['default'] = [FLOORS.index('G')]
    anims['blink13'] = [FLOORS.index('13'), FLOORS.index('off')]
    anims['errBlink'] = [FLOORS.index('--'), FLOORS.index('off')]
    return anims, frames

# ------------------------------------------------------------------ people, high-angle 3/4 view
PW, PH = 48, 78
BASE = PH - 3          # feet baseline inside a person cell (feet point = (PW//2, BASE))

def skin_of(sp): return sp.get('skin', (C['skin'], C['skinS'], C['skinD']))

def figure(sp, facing='front', walk=0, talk=False, arms='down', sit=False, lean=0, eyes='open'):
    """One frame of a person. sp: spec dict; facing front (towards the camera) or back (towards the doors)."""
    img = new(PW, PH)
    s = sp.get('scale', 1.0)
    cx = PW // 2 + lean
    by = BASE
    sk, sks, skd = skin_of(sp)
    top = sp['top']; bot = sp.get('bottom', C['navy']); shoe = sp.get('shoes', C['black'])
    # high angle: big head, broad shoulders, short legs
    hr = 7.2 * s                       # head radius
    sh_y = by - 33 * s                 # shoulder line
    hip_y = by - 15 * s
    head_c = (cx, sh_y - hr + 2 * s)
    sw = sp.get('shoulders', 12) * s   # half shoulder width
    if sit:
        return sitting(sp, facing, talk, arms)
    front = facing == 'front'
    # legs and shoes
    lw = 3.2 * s
    for side in (-1, 1):
        step = walk * side * 2 * s
        lx = cx + side * 3.4 * s
        foot_y = by - 1 + (step if front else -step) * 0.6
        if sp.get('skirt'):
            paint(img, [rect(lx - lw * 0.7, hip_y + 2, lx + lw * 0.7, foot_y - 1)], sk, sks, None, skd, split=0.7)
        else:
            paint(img, [poly((lx - lw, hip_y), (lx + lw, hip_y), (lx + lw * 0.85, foot_y - 1), (lx - lw * 0.85, foot_y - 1))], bot, dk(bot, 0.82), None, dk(bot, 0.55), split=0.6)
        paint(img, [ell(lx + side * 0.6, foot_y, lw + 0.6, 2.2 * s)], shoe, dk(shoe, 0.8), lt(shoe), dk(shoe, 0.5))
    if sp.get('skirt'):
        sc = sp['skirt']
        paint(img, [poly((cx - sw * 0.8, hip_y - 4 * s), (cx + sw * 0.8, hip_y - 4 * s), (cx + sw, hip_y + 7 * s), (cx - sw, hip_y + 7 * s))], sc, dk(sc, 0.82), None, dk(sc, 0.55))
    # back items (worn behind when facing the camera)
    if sp.get('backpack') and front:
        bp = sp['backpack']
        paint(img, [rect(cx - sw - 1, sh_y + 2, cx - sw + 2, hip_y - 4)], bp, dk(bp, 0.8), None, dk(bp, 0.55))
    # torso
    tc = sp.get('coat', False)
    tb = hip_y + (6 * s if tc else 1)
    paint(img, [poly((cx - sw, sh_y + 2 * s), (cx + sw, sh_y + 2 * s), (cx + sw * 0.78, tb), (cx - sw * 0.78, tb)),
                ell(cx - sw + 3 * s, sh_y + 3 * s, 3.4 * s, 3 * s), ell(cx + sw - 3 * s, sh_y + 3 * s, 3.4 * s, 3 * s)],
          top, dk(top, 0.82), lt(top), dk(top, 0.55), split=0.64)
    dd = ImageDraw.Draw(img)
    if sp.get('tie') and front:
        paint(img, [poly((cx - 2, sh_y + 1), (cx + 2, sh_y + 1), (cx, sh_y + 5))], C['white'], C['white'], None, C['paperD'])
        paint(img, [poly((cx - 1, sh_y + 4), (cx + 1, sh_y + 4), (cx + 1.5, sh_y + 13), (cx, sh_y + 15), (cx - 1.5, sh_y + 13))], sp['tie'], sp['tie'], None, dk(sp['tie']))
    if sp.get('scarf'):
        sc = sp['scarf']
        paint(img, [ell(cx, sh_y + 1.5 * s, sw * 0.75, 3.2 * s)], sc, dk(sc, 0.82), lt(sc), dk(sc, 0.55))
    if sp.get('overalls') and front:
        o = sp['overalls']
        paint(img, [rect(cx - 5 * s, sh_y + 7 * s, cx + 5 * s, hip_y + 1)], o, dk(o, 0.82), None, dk(o, 0.55))
        dd.line((cx - 5 * s, sh_y + 7 * s, cx - 4 * s, sh_y + 1), fill=dk(o, 0.6)); dd.line((cx + 5 * s, sh_y + 7 * s, cx + 4 * s, sh_y + 1), fill=dk(o, 0.6))
    if sp.get('backpack') and not front:
        bp = sp['backpack']
        paint(img, [poly((cx - 7 * s, sh_y + 3 * s), (cx + 7 * s, sh_y + 3 * s), (cx + 7.5 * s, hip_y - 1), (cx - 7.5 * s, hip_y - 1))], bp, dk(bp, 0.82), lt(bp), dk(bp, 0.55))
        dd.line((cx - 5 * s, sh_y + 8 * s, cx + 5 * s, sh_y + 8 * s), fill=dk(bp, 0.6))
    # arms
    hand = lambda x, y: paint(img, [ell(x, y, 1.9 * s, 2.2 * s)], sk, sks, None, skd, split=0.7)
    sleeve = sp.get('sleeve', top)
    def arm(side, ex, ey, hx_, hy_, show_hand=True):
        sx = cx + side * (sw - 1.5 * s); sy = sh_y + 3 * s
        paint(img, [poly((sx - 2.2 * s, sy), (sx + 2.2 * s, sy), (ex + 2 * s, ey), (ex - 2 * s, ey)),
                    poly((ex - 2 * s, ey - 1), (ex + 2 * s, ey - 1), (hx_ + 1.6 * s, hy_), (hx_ - 1.6 * s, hy_)), ell(ex, ey, 2.1 * s, 2.1 * s)],
              sleeve, dk(sleeve, 0.82), None, dk(sleeve, 0.55), split=0.6)
        if show_hand: hand(hx_, hy_ + 1)
    sx = lambda side, dx=0: cx + side * (sw + dx)
    swing = walk * 1.5 * s
    poses = {
        'down': [(-1, sx(-1, 0.5), sh_y + 11 * s - swing, sx(-1, 0.3), hip_y + 1 - swing), (1, sx(1, 0.5), sh_y + 11 * s + swing, sx(1, 0.3), hip_y + 1 + swing)],
        'phone': [(-1, sx(-1, 0.5), sh_y + 11 * s, sx(-1, 0.3), hip_y + 1), (1, sx(1, 2), sh_y + 9 * s, cx + hr * 0.9, head_c[1] + 2 * s)],
        'up': [(-1, sx(-1, 3), sh_y - 6 * s, sx(-1, 4), sh_y - 16 * s), (1, sx(1, 3), sh_y - 6 * s, sx(1, 4), sh_y - 16 * s)],
        'upL': [(-1, sx(-1, 3), sh_y - 6 * s, sx(-1, 2), sh_y - 16 * s), (1, sx(1, 4), sh_y + 6 * s, sx(1, 8), sh_y + 4 * s)],
        'upR': [(-1, sx(-1, 4), sh_y + 6 * s, sx(-1, 8), sh_y + 4 * s), (1, sx(1, 3), sh_y - 6 * s, sx(1, 2), sh_y - 16 * s)],
        'wave': [(-1, sx(-1, 0.5), sh_y + 11 * s, sx(-1, 0.3), hip_y + 1), (1, sx(1, 4), sh_y + 2 * s, sx(1, 5), sh_y - 9 * s)],
        'box': [(-1, sx(-1, 1), sh_y + 9 * s, cx - 9 * s, sh_y + 13 * s), (1, sx(1, 1), sh_y + 9 * s, cx + 9 * s, sh_y + 13 * s)],
        'mop': [(-1, sx(-1, 0.5), sh_y + 11 * s, sx(-1, 0.3), hip_y + 1), (1, sx(1, 1), sh_y + 10 * s, cx + 6 * s, sh_y + 14 * s)],
        'hips': [(-1, sx(-1, 3), sh_y + 8 * s, cx - sw + 2, hip_y - 3), (1, sx(1, 3), sh_y + 8 * s, cx + sw - 2, hip_y - 3)],
    }
    order = poses[arms]
    for side, ex, ey, hx_, hy_ in order:
        arm(side, ex, ey, hx_, hy_, show_hand=arms != 'box')
    # neck + head
    paint(img, [rect(cx - 2 * s, head_c[1] + hr - 3 * s, cx + 2 * s, sh_y + 2 * s)], sks, skd, None, skd, outline=False)
    head(img, sp, head_c, hr, front, talk, eyes)
    # carried things on top
    if arms == 'phone':
        px_, py_ = cx + hr * 0.9, head_c[1] + 1 * s
        paint(img, [rect(px_ - 1, py_ - 3, px_ + 1, py_ + 3)], C['black'], C['black'], None, C['black'])
    if arms == 'box':
        bx = [cx - 10 * s, sh_y + 4 * s, cx + 10 * s, sh_y + 20 * s]
        paint(img, [rect(*bx)], C['card'], C['cardD'], C['cardL'], dk(C['cardD'], 0.7), split=0.75, ldepth=0.3)
        ImageDraw.Draw(img).line((cx, bx[1] + 1, cx, bx[3] - 1), fill=C['tape'])
        paint(img, [rect(cx - 7 * s, bx[1] + 5, cx - 1 * s, bx[1] + 9)], C['white'], None, None, C['paperD'])
        hand(cx - 10 * s, sh_y + 13 * s); hand(cx + 10 * s, sh_y + 13 * s)
    if arms == 'mop':
        dd = ImageDraw.Draw(img)
        dd.line((cx + 6 * s, sh_y + 6 * s, cx + 14 * s, by - 2), fill=dk(C['woodL'], 0.9), width=2)
        paint(img, [ell(cx + 15 * s, by - 2, 5 * s, 2.2 * s)], C['cream'], C['paperD'], None, dk(C['paperD']))
    if sp.get('extra'): sp['extra'](img, cx, head_c, hr, sh_y, hip_y, by, front)
    return img

def head(img, sp, c, r, front, talk, eyes='open'):
    sk, sks, skd = skin_of(sp)
    cx, cy = c
    st = sp['hair']
    hc = sp.get('hairc', C['hairDk'])
    d = ImageDraw.Draw(img)
    # long hair behind the head
    if st in ('bob', 'ponytail') and front:
        paint(img, [ell(cx, cy + 1, r + 1.2, r + 0.8)], hc, dk(hc, 0.85), None, dk(hc, 0.55))
    # skull / face (from above the face is foreshortened into the lower half of the head)
    paint(img, [ell(cx, cy, r, r * 1.02)], sk, sks, None, skd, split=0.66)
    if front:
        for side in (-1, 1):   # ears
            paint(img, [ell(cx + side * r, cy + 1.6, 1.4, 2)], sk, sks, None, skd, split=0.5)
        ey = round(cy + r * 0.28)
        if not sp.get('noface'):
            for side in (-1, 1):
                ex = round(cx + side * r * 0.42) - (1 if side < 0 else 0)
                if eyes == 'closed':
                    d.line((ex - 1, ey + 1, ex + 2, ey + 1), fill=C['black'])
                else:
                    d.rectangle((ex - 1, ey - 1, ex + 2, ey + 1), fill=C['black'])      # rim + heavy lid
                    d.rectangle((ex, ey, ex + 1, ey), fill=C['white'])
                    d.point((ex + (1 if side < 0 else 0), ey), fill=C['black'])         # pupil looking at the camera's side
                d.line((ex - 1, ey - 3, ex + 2, ey - 3), fill=dk(hc, 0.9) if st not in ('bald',) else skd)   # brow
            d.point((cx, ey + 2), fill=sks); d.point((cx, ey + 3), fill=skd)            # nose
            my = ey + 5
            if talk:
                d.rectangle((cx - 1, my, cx + 1, my + 1), fill=hx('#5a2a24')); d.point((cx, my + 1), fill=hx('#9a4a44'))
            else:
                d.line((cx - 1, my, cx + 1, my), fill=skd)
            if sp.get('mustache'):
                d.line((cx - 2, my - 1, cx + 2, my - 1), fill=sp['mustache'])
            if sp.get('glasses'):
                for side in (-1, 1):
                    ex = round(cx + side * r * 0.42) - (1 if side < 0 else 0)
                    d.rectangle((ex - 2, ey - 2, ex + 3, ey + 2), outline=sp['glasses'])
                d.point((cx, ey - 1), fill=sp['glasses'])
    hair(img, sp, c, r, front, talk)

def hair(img, sp, c, r, front, talk):
    cx, cy = c
    st = sp['hair']; hc = sp.get('hairc', C['hairDk'])
    hs, hl, hd = dk(hc, 0.82), lt(hc), dk(hc, 0.55)
    d = ImageDraw.Draw(img)
    cover = 0.15 if front else 1.4    # how far down the hair reaches (relative to r)
    if st == 'perm':
        bumps = [(-0.7, -0.5), (0, -0.85), (0.7, -0.5), (-0.95, 0.15), (0.95, 0.15), (-0.35, -0.2), (0.35, -0.2)]
        if not front: bumps += [(-0.5, 0.6), (0.5, 0.6), (0, 0.4), (0, 0.9)]
        paint(img, [ell(cx + bx * r, cy + by_ * r, r * 0.52, r * 0.5) for bx, by_ in bumps], hc, hs, hl, hd, split=0.68)
        for bx, by_ in bumps[:5]: d.point((round(cx + bx * r - 1), round(cy + by_ * r)), fill=hs)
    elif st == 'bald':
        # the crown stays bare: the camera sees it. Hair only around the sides and the back.
        if front:
            for side in (-1, 1): paint(img, [ell(cx + side * r * 0.9, cy + 0.5, r * 0.28, r * 0.5)], hc, hs, None, hd)
            d.line((cx - 3, cy - r * 0.55, cx + 2, cy - r * 0.7), fill=hc)       # two combed-over strands
            d.line((cx - 2, cy - r * 0.35, cx + 3, cy - r * 0.5), fill=hc)
        else:
            paint(img, [poly((cx - r, cy), (cx + r, cy), (cx + r * 0.8, cy + r * 0.9), (cx - r * 0.8, cy + r * 0.9))], hc, hs, None, hd)
            d.line((cx - 3, cy - r * 0.45, cx + 2, cy - r * 0.6), fill=hc)
        d.point((round(cx - r * 0.35), round(cy - r * 0.5)), fill=C['white'])       # shine on the bald spot
        d.point((round(cx - r * 0.25), round(cy - r * 0.6)), fill=lt(skin_of(sp)[0], 1.06))
    elif st == 'cap':
        cc = sp['capc']
        paint(img, [ell(cx, cy - r * 0.15, r * 1.02, r * 0.88)], cc, dk(cc, 0.82), lt(cc), dk(cc, 0.55))
        if front: paint(img, [ell(cx, cy + r * 0.05, r * 0.95, r * 0.3)], dk(cc, 0.85), dk(cc, 0.75), None, dk(cc, 0.5))
        else:
            paint(img, [ell(cx, cy - r * 0.9, r * 0.8, r * 0.3)], dk(cc, 0.85), dk(cc, 0.75), None, dk(cc, 0.5))
            paint(img, [poly((cx - r * 0.9, cy + 0.2 * r), (cx + r * 0.9, cy + 0.2 * r), (cx + r * 0.7, cy + r * 0.9), (cx - r * 0.7, cy + r * 0.9))], C['hairDk'], C['hairDk'], None, C['black'])
        d.point((cx, round(cy - r * 0.4)), fill=lt(cc, 1.3))
    elif st in ('short', 'bob', 'ponytail'):
        if front:
            sh = [poly((cx - r, cy + r * 0.1), (cx - r * 0.95, cy - r * 0.6), (cx - r * 0.4, cy - r), (cx + r * 0.5, cy - r), (cx + r, cy - r * 0.5),
                       (cx + r, cy + r * 0.1), (cx + r * 0.5, cy - r * 0.25), (cx - r * 0.2, cy - r * 0.15), (cx - r * 0.7, cy - r * 0.05))]
            if st == 'bob': sh += [rect(cx - r - 1, cy - r * 0.3, cx - r * 0.6, cy + r * 0.9), rect(cx + r * 0.6, cy - r * 0.3, cx + r + 1, cy + r * 0.9)]
        else:
            low = 0.55 if st == 'short' else 1.05
            sh = [ell(cx, cy - r * 0.05, r * 1.02, r * 0.98), rect(cx - r * 0.95, cy, cx + r * 0.95, cy + r * low)]
        paint(img, sh, hc, hs, hl, hd, split=0.66)
        if st == 'ponytail':
            py = cy + (r * 1.1 if not front else -r * 1.05)
            paint(img, [ell(cx, py, r * 0.32, r * 0.5)], hc, hs, hl, hd)
        d.line((cx - r * 0.5, cy - r * 0.7, cx + r * 0.1, cy - r * 0.85), fill=hl)
    elif st == 'beanie':
        bc = sp['capc']
        paint(img, [poly((cx - r * 1.02, cy - r * (0.05 if front else -0.5)), (cx - r * 0.8, cy - r * 0.8), (cx, cy - r * 1.05), (cx + r * 0.8, cy - r * 0.8),
                         (cx + r * 1.02, cy - r * (0.05 if front else -0.5)))], bc, dk(bc, 0.82), lt(bc), dk(bc, 0.55))
        for i in range(-4, 5, 2): d.line((cx + i * r / 5, cy - r * 0.85, cx + i * r / 5, cy - r * (0.15 if front else -0.4)), fill=dk(bc, 0.82))
        if front: d.line((cx - r, cy - r * 0.15, cx + r, cy - r * 0.15), fill=dk(bc, 0.6))
    elif st == 'fedora':
        fc = sp['capc']
        paint(img, [ell(cx, cy - r * 0.1, r * 1.5, r * 1.0)], dk(fc, 0.9), dk(fc, 0.78), None, dk(fc, 0.5))   # brim from above
        paint(img, [ell(cx, cy - r * 0.25, r * 0.9, r * 0.75)], fc, dk(fc, 0.82), lt(fc), dk(fc, 0.55))
        d.line((cx - r * 0.5, cy - r * 0.25, cx + r * 0.5, cy - r * 0.25), fill=dk(fc, 0.6))
        paint(img, [rect(cx - r * 0.8, cy + r * 0.05, cx + r * 0.8, cy + r * 0.25)], C['black'], C['black'], None, C['black'], outline=False)
    elif st == 'hardhat':
        y = C['yel']
        paint(img, [ell(cx, cy - r * 0.15, r * 1.2, r * 0.95)], dk(y, 0.85), None, None, dk(y, 0.55))
        paint(img, [ell(cx, cy - r * 0.3, r * 0.95, r * 0.75)], y, dk(y, 0.82), lt(y), dk(y, 0.55))
        d.line((cx, cy - r * 0.95, cx, cy + r * 0.3), fill=dk(y, 0.7))
    elif st == 'dino':
        g = C['dino']
        paint(img, [ell(cx, cy - r * 0.1, r * 1.12, r * 1.05), rect(cx - r * 1.1, cy - r * 0.1, cx + r * 1.1, cy + r * (0.35 if front else 1.0))],
              g, dk(g, 0.82), lt(g), dk(g, 0.55))
        if front:
            paint(img, [ell(cx, cy + r * 0.35, r * 0.75, r * 0.6)], *skin_of(sp)[:2], None, skin_of(sp)[2])
            ey = round(cy + r * 0.3)
            for side in (-1, 1):
                ex = round(cx + side * r * 0.38)
                d.rectangle((ex - 1, ey - 1, ex, ey), fill=C['black']); d.point((ex, ey), fill=C['white'])
            d.line((cx - 1, ey + 3, cx + 1, ey + 3), fill=skin_of(sp)[2])
            if talk: d.rectangle((cx - 1, ey + 3, cx + 1, ey + 4), fill=hx('#5a2a24'))
            for side in (-1, 1): d.point((round(cx + side * r * 0.5), round(cy - r * 0.6)), fill=C['white'])
        for i in range(-2, 3):
            yy = cy - r * 0.95 + (i + 2) * r * 0.45 if not front else cy - r * 1.05 + (i + 2) * r * 0.22
            paint(img, [poly((cx - 2, yy + 2), (cx + 2, yy + 2), (cx, yy - 2))], C['yel'], None, None, dk(C['yel']))
    if sp.get('headphones'):
        pc = sp['headphones']
        d.arc((round(cx - r - 1), round(cy - r - 1), round(cx + r + 1), round(cy + r)), 190, 350, fill=C['black'], width=2)
        for side in (-1, 1): paint(img, [ell(cx + side * (r + 0.5), cy + 1, 2.4, 3.2)], pc, dk(pc, 0.8), lt(pc), C['black'])

def sitting(sp, facing='front', talk=False, arms='down'):
    """Sitting on the floor facing the camera, knees up (waiting while stuck, Mila's fall, Rafi's lunch)."""
    img = new(PW, PH); s = sp.get('scale', 1.0); cx = PW // 2; by = BASE
    sk, sks, skd = skin_of(sp)
    top = sp['top']; bot = sp.get('bottom', C['navy']); shoe = sp.get('shoes', C['black'])
    hip_y = by - 10 * s; sh_y = by - 24 * s; hr = 7.2 * s
    if sp.get('skirt'): bot = sp['skirt']
    for side in (-1, 1):  # knees towards the camera
        kx = cx + side * 6 * s
        paint(img, [poly((cx + side * 2 * s, hip_y), (kx + side * 3 * s, hip_y - 2 * s), (kx + side * 3.5 * s, by - 2), (kx - side * 1 * s, by - 2))], bot, dk(bot, 0.82), lt(bot), dk(bot, 0.55))
        paint(img, [ell(kx + side * 1.5 * s, by - 1, 3.2 * s, 2 * s)], shoe, dk(shoe, 0.8), None, dk(shoe, 0.5))
    sw = sp.get('shoulders', 12) * s
    paint(img, [poly((cx - sw, sh_y + 2), (cx + sw, sh_y + 2), (cx + sw * 0.8, hip_y + 1), (cx - sw * 0.8, hip_y + 1)),
                ell(cx - sw + 3, sh_y + 3, 3.4 * s, 3 * s), ell(cx + sw - 3, sh_y + 3, 3.4 * s, 3 * s)], top, dk(top, 0.82), lt(top), dk(top, 0.55), split=0.64)
    if sp.get('scarf'): paint(img, [ell(cx, sh_y + 1.5, sw * 0.75, 3.2 * s)], sp['scarf'], dk(sp['scarf'], 0.82), None, dk(sp['scarf'], 0.55))
    for side in (-1, 1):   # forearms resting on the knees
        sl = sp.get('sleeve', top)
        paint(img, [poly((cx + side * (sw - 2), sh_y + 3), (cx + side * (sw + 1), sh_y + 3), (cx + side * 7 * s, hip_y - 1), (cx + side * 4 * s, hip_y - 1))], sl, dk(sl, 0.82), None, dk(sl, 0.55))
        paint(img, [ell(cx + side * 5.5 * s, hip_y - 1, 1.9 * s, 2 * s)], sk, sks, None, skd)
    paint(img, [rect(cx - 2 * s, sh_y - 3, cx + 2 * s, sh_y + 2)], sks, skd, None, skd, outline=False)
    head(img, sp, (cx, sh_y - hr + 2 * s), hr, facing == 'front', talk)
    if sp.get('lunch'):
        paint(img, [rect(cx - 3, hip_y - 6, cx + 4, hip_y - 2)], C['cream'], C['paperD'], None, C['brown'])
        ImageDraw.Draw(img).line((cx - 3, hip_y - 4, cx + 4, hip_y - 4), fill=C['green'])
    return img

SPEC = {
    'pruitt': dict(hair='perm', hairc=C['lilac'], top=C['mustard'], scarf=C['pink'], skirt=hx('#5d6f8f'), glasses=hx('#3b3030'),
                   shoes=hx('#5a3a2c'), scale=0.93, shoulders=11),
    'haldane': dict(hair='bald', hairc=C['hairBr'], top=C['navy'], tie=C['red'], bottom=dk(C['navy'], 0.85), shoulders=13),
    'rafi': dict(hair='cap', capc=C['red'], top=hx('#8a6a3c'), bottom=C['denim'], skin=(C['skin2'], C['skin2S'], C['skin2D']), shoes=hx('#4a3b30')),
    'mila': dict(hair='bob', hairc=C['hairDk'], headphones=C['redL'], top=C['teal'], backpack=C['yel'], bottom=C['denim'],
                 shoes=C['white'], scale=0.9, shoulders=10.5),
    'gus': dict(hair='beanie', capc=C['greyD'], top=hx('#6d7a5a'), overalls=hx('#5a6a4a'), bottom=hx('#5a6a4a'), mustache=C['hairGrey'],
                skin=(C['skin2'], C['skin2S'], C['skin2D']), shoes=hx('#3e3630')),
    'dev': dict(hair='short', hairc=C['black'], top=C['red'], bottom=C['denim'], skin=(C['skin2'], C['skin2S'], C['skin2D'])),
    'priya': dict(hair='ponytail', hairc=C['hairDk'], top=C['yel'], bottom=C['charcoal'], skin=(C['skin2'], C['skin2S'], C['skin2D']),
                  scale=0.94, shoulders=10.5),
    'toby': dict(hair='dino', top=C['blue'], bottom=C['navy'], shoes=C['red'], scale=0.64, shoulders=12),
    'mom': dict(hair='ponytail', hairc=C['hairBr'], top=C['red'], bottom=C['black'], scale=0.95, shoulders=11),
    'grey': dict(hair='fedora', capc=C['grey'], top=C['greyD'], coat=True, bottom=C['charcoal'], noface=True, shoulders=12.5),
    'tech': dict(hair='hardhat', top=C['blue'], overalls=dk(C['blue'], 0.9), bottom=dk(C['blue'], 0.9), shoes=hx('#3a3a3a')),
}

def dog():
    """Duchess: small white dog with a red collar, seen from above at 3/4. sit, walk, sniff, sleep, bark."""
    w, h = 22, 18
    wc, ws, wd = C['white'], hx('#cfc6b6'), hx('#8f877a')
    def f(kind):
        im = new(w, h)
        if kind == 'sleep':
            paint(im, [ell(11, 12, 7, 4.5)], wc, ws, None, wd)
            paint(im, [ell(6, 11, 3.5, 3)], wc, ws, None, wd); ImageDraw.Draw(im).line((4, 11, 6, 11), fill=wd)
            return im
        o = {'walk1': 1, 'walk2': -1}.get(kind, 0)
        for lx, ly in ((7, 15 + o), (14, 15 - o)):
            paint(im, [rect(lx - 1, ly - 3, lx + 1, ly)], ws, ws, None, wd, outline=False)
        paint(im, [ell(11, 11, 6, 4)], wc, ws, None, wd)                       # body
        paint(im, [poly((16, 9), (19, 6), (18, 10))], wc, ws, None, wd)        # tail
        hx_, hy_ = (6, 11) if kind == 'sniff' else (7, 6)
        paint(im, [ell(hx_, hy_, 3.6, 3.4)], wc, ws, None, wd)                # head
        for side in (-1, 1): paint(im, [ell(hx_ + side * 3, hy_ - 1, 1.4, 2)], ws, wd, None, wd)
        d = ImageDraw.Draw(im)
        d.point((hx_ - 1, hy_), fill=C['black']); d.point((hx_ + 1, hy_), fill=C['black']); d.point((hx_, hy_ + 2), fill=C['black'])
        d.line((hx_ - 2, hy_ + 3, hx_ + 2, hy_ + 3), fill=C['red'])
        if kind == 'bark': d.point((hx_, hy_ + 3), fill=hx('#5a2a24')); d.rectangle((hx_ - 1, hy_ + 2, hx_ + 1, hy_ + 2), fill=hx('#5a2a24'))
        return im
    frames = [f(k) for k in ('sit', 'walk1', 'walk2', 'sniff', 'sleep', 'bark')]
    return {'default': [0], 'walk': [1, 2], 'sniff': [3, 0], 'sleep': [4], 'bark': [5, 0]}, frames

def props():
    b = new(16, 16)
    paint(b, [poly((2, 4), (14, 4), (12, 14), (4, 14))], C['yel'], dk(C['yel'], 0.82), lt(C['yel']), dk(C['yel'], 0.55))
    paint(b, [ell(8, 4, 6, 2.2)], hx('#6f8fb0'), hx('#5a7898'), None, dk(C['yel'], 0.55))
    t = new(22, 14)
    paint(t, [rect(2, 4, 19, 12)], C['red'], C['redD'], C['redL'], dk(C['redD'], 0.7))
    paint(t, [rect(7, 1, 14, 4)], C['greyD'], None, None, C['black'])
    ImageDraw.Draw(t).line((2, 7, 19, 7), fill=C['redD'])
    return {'bucket': b, 'toolbox': t}

def glitch():
    """Signal trouble in the game's flat style: blank, two tears, two noise frames, roll bar, NO SIGNAL, snow."""
    def tear(seed):
        rr = random.Random(seed); im = new(W, H); d = ImageDraw.Draw(im)
        for _ in range(6):
            y = rr.randrange(0, H - 6); hh = rr.randrange(1, 4); dx = rr.randrange(-40, 40)
            col = rr.choice([(214, 214, 222, 160), (110, 200, 200, 130), (200, 90, 150, 120), (12, 12, 16, 210)])
            d.rectangle((max(0, dx), y, min(W - 1, W + dx), y + hh), fill=col)
        return im
    def noise(seed, dens):
        rr = random.Random(seed); im = new(W, H); px = im.load()
        for y in range(H):
            band = rr.random() < 0.15
            for x in range(0, W, 2):
                if rr.random() < dens * (3 if band else 1):
                    v = rr.choice((70, 130, 190, 235)); px[x, y] = (v, v, v, 180)
                    if x + 1 < W: px[x + 1, y] = (v, v, v, 180)
        return im
    def roll():
        im = new(W, H); d = ImageDraw.Draw(im)
        d.rectangle((0, 58, W - 1, 76), fill=(220, 220, 230, 60)); d.rectangle((0, 63, W - 1, 70), fill=(250, 250, 255, 110))
        return im
    def nosignal():
        im = new(W, H, (22, 26, 60, 255)); d = ImageDraw.Draw(im)
        bars = [(196, 196, 196), (196, 196, 60), (60, 196, 196), (60, 196, 60), (196, 60, 196), (196, 60, 60), (60, 60, 196)]
        bw = W // len(bars)
        for i, c in enumerate(bars): d.rectangle((i * bw, 0, (i + 1) * bw, 118), fill=c + (255,))
        d.rectangle((0, 118, W, H), fill=(26, 26, 34, 255))
        s = 'NO SIGNAL'; x = (W - text_w(s) * 2) // 2
        d.rectangle((x - 6, 132, x + text_w(s) * 2 + 6, 150), fill=(10, 10, 14, 255))
        for ch in s:
            g = FONT.get(ch, FONT[' '])
            for i, b in enumerate(g):
                if b == '1': d.rectangle((x + (i % 3) * 2, 136 + (i // 3) * 2, x + (i % 3) * 2 + 1, 137 + (i // 3) * 2), fill=(236, 236, 240, 255))
            x += 8
        return im
    frames = [new(W, H), tear(1), tear(2), noise(3, 0.08), noise(4, 0.1), roll(), nosignal(), noise(5, 0.45)]
    anims = {'default': [0], 'off': [0], 'burst': [1, 3, 2, 4, 0], 'roll': [5, 1, 5, 0], 'static': [3, 4], 'nosignal': [6], 'snow': [7, 3, 7, 4]}
    return anims, frames

def outside_dot(): return new(1, 1)

# ------------------------------------------------------------------ replacement hook for generated art
OVERRIDE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'art_override', 'liftcam')
def override(kind, name, size):
    """mod/art_override/liftcam/<kind>/<name>.png, exact size or an integer multiple (scaled down nearest)."""
    path = os.path.join(OVERRIDE_DIR, kind, name + '.png')
    if not os.path.isfile(path): return None
    im = Image.open(path).convert('RGBA')
    if im.size != size:
        k = im.width // size[0]
        if k < 1 or im.size != (size[0] * k, size[1] * k): raise SystemExit('%s: wrong size %s' % (path, im.size))
        im = im.resize(size, Image.NEAREST)
    return im

# ------------------------------------------------------------------ busts: what the ceiling camera sees
# The car is tiny and the camera is right above the riders: like the game's ATM camera, people fill the frame.
# Most of the time they face the doors, so we see the crown, the hair, the ears and the shoulders from behind.
# A person sheet is full-frame (252x174) with the bust centred at x=126; the object is moved sideways to its
# slot. Entering/leaving frames draw the small walking figure at the doors (compensating the slot offset).

BX = 126

def b_head_back(img, sp, s, yo, hdx=0):
    sk, sks, skd = skin_of(sp)
    cx, cy = BX + hdx, 100 + yo
    for side in (-1, 1):   # ears
        paint(img, [ell(cx + side * 22 * s, cy + 8 * s, 4.5 * s, 7.5 * s)], sk, sks, None, skd, split=0.55)
        ImageDraw.Draw(img).line((cx + side * 22 * s, cy + 5 * s, cx + side * 22 * s, cy + 11 * s), fill=sks)
    paint(img, [ell(cx, cy, 22 * s, 25 * s)], sk, sks, lt(sk, 1.06), skd, split=0.64)
    return cx, cy

def b_head_front(img, sp, s, yo, talk, eyes='open'):
    sk, sks, skd = skin_of(sp)
    cx, cy = BX, 98 + yo
    d = ImageDraw.Draw(img)
    if sp['hair'] in ('bob', 'ponytail') and sp.get('long', True):
        hc = sp.get('hairc', C['hairDk']); paint(img, [ell(cx, cy - 2 * s, 25 * s, 22 * s)], hc, dk(hc, 0.85), None, dk(hc, 0.55))
    for side in (-1, 1):
        paint(img, [ell(cx + side * 21 * s, cy + 6 * s, 4.5 * s, 7 * s)], sk, sks, None, skd, split=0.5)
    # face seen from above: big forehead, features low on the head, short chin
    paint(img, [ell(cx, cy, 21 * s, 25 * s), ell(cx, cy + 14 * s, 15 * s, 14 * s)], sk, sks, lt(sk, 1.05), skd, split=0.66)
    if not sp.get('noface'):
        ey = cy + 8 * s
        for side in (-1, 1):
            ex = cx + side * 9 * s
            if eyes == 'closed':
                d.line((ex - 4 * s, ey + 1, ex + 4 * s, ey + 1), fill=C['black'], width=2)
            else:
                paint(img, [ell(ex, ey, 4.6 * s, 3.2 * s)], C['white'], C['white'], None, C['black'])
                d.ellipse((ex - 1.6 * s + side * 0.6, ey - 1.8 * s, ex + 1.6 * s + side * 0.6, ey + 1.4 * s), fill=C['black'])   # pupils up at the lens
                d.line((ex - 4.6 * s, ey - 3 * s, ex + 4.6 * s, ey - 3 * s), fill=C['black'], width=2)                     # heavy lid
                d.line((ex - 3 * s, ey + 3.4 * s, ex + 3 * s, ey + 3.4 * s), fill=sks)
            bc = dk(sp.get('hairc', C['hairDk']), 0.9) if sp['hair'] not in ('bald',) else C['hairBr']
            d.line((ex - 5 * s, ey - 6 * s - side, ex + 4 * s, ey - 6 * s + side * 0), fill=bc, width=2)            # brows
        # nose: lit ridge, shaded right side, nostrils
        paint(img, [poly((cx - 1 * s, ey - 2 * s), (cx + 2 * s, ey - 2 * s), (cx + 4 * s, ey + 9 * s), (cx - 3 * s, ey + 9 * s))], sk, sks, None, sks, split=0.55)
        d.point((cx - 2 * s, ey + 9 * s), fill=skd); d.point((cx + 2 * s, ey + 9 * s), fill=skd)
        my = ey + 14 * s
        if talk:
            paint(img, [ell(cx, my, 4 * s, 2.6 * s)], hx('#5a2a24'), hx('#5a2a24'), None, hx('#3a1814'))
            d.line((cx - 2 * s, my + 1.5 * s, cx + 2 * s, my + 1.5 * s), fill=hx('#a4524a'))
        else:
            d.line((cx - 5 * s, my, cx + 5 * s, my), fill=skd, width=2); d.line((cx - 3 * s, my + 2, cx + 3 * s, my + 2), fill=sks)
        if sp.get('old'):
            for i in (0, 4): d.line((cx - 9 * s, cy - 10 * s + i, cx + 9 * s, cy - 10 * s + i), fill=sks)
            for side in (-1, 1): d.line((cx + side * 5 * s, ey + 8 * s, cx + side * 8 * s, my + 2 * s), fill=sks)
        if sp.get('mustache'):
            paint(img, [ell(cx, my - 3 * s, 7 * s, 2.2 * s)], sp['mustache'], dk(sp['mustache'], 0.85), None, dk(sp['mustache'], 0.6))
        if sp.get('glasses'):
            g = sp['glasses']
            for side in (-1, 1):
                ex = cx + side * 9 * s; d.ellipse((ex - 6 * s, ey - 5 * s, ex + 6 * s, ey + 5 * s), outline=g, width=1)
            d.line((cx - 3 * s, ey - 1, cx + 3 * s, ey - 1), fill=g)
    return cx, cy

def b_hair(img, sp, s, cx, cy, front):
    st = sp['hair']; hc = sp.get('hairc', C['hairDk'])
    hs, hl, hd = dk(hc, 0.82), lt(hc, 1.15), dk(hc, 0.55)
    d = ImageDraw.Draw(img)
    if st == 'perm':
        r = random.Random(3)
        cs = [(-14, -14), (0, -19), (14, -14), (-19, -2), (19, -2), (-7, -6), (7, -6), (0, 2), (-11, 7), (11, 7)]
        if not front: cs += [(-16, 12), (16, 12), (-6, 16), (6, 16), (0, 20), (0, 10)]
        else: cs = [c for c in cs if c[1] < 0] + [(-21, 6), (21, 6)]
        paint(img, [ell(cx + x * s, cy + y * s, 8 * s, 7.5 * s) for x, y in cs], hc, hs, None, hd, split=0.66)
        for x, y in cs:
            px_, py_ = cx + x * s, cy + y * s
            d.arc((px_ - 6 * s, py_ - 5 * s, px_ + 6 * s, py_ + 6 * s), 10, 120, fill=hs, width=2)
            d.arc((px_ - 5 * s, py_ - 6 * s, px_ + 4 * s, py_ + 3 * s), 190, 260, fill=hl, width=2)
    elif st == 'bald':
        # the crown is bare and shiny: the camera's favourite. Hair only round the back and the sides.
        if front:
            for side in (-1, 1): paint(img, [ell(cx + side * 19 * s, cy + 2 * s, 5 * s, 9 * s)], hc, hs, None, hd)
        else:
            paint(img, [poly((cx - 22 * s, cy + 2 * s), (cx - 12 * s, cy + 6 * s), (cx + 12 * s, cy + 6 * s), (cx + 22 * s, cy + 2 * s),
                             (cx + 19 * s, cy + 18 * s), (cx + 8 * s, cy + 24 * s), (cx - 8 * s, cy + 24 * s), (cx - 19 * s, cy + 18 * s))], hc, hs, hl, hd)
            for i in range(-3, 4): d.line((cx + i * 5 * s, cy + 8 * s, cx + i * 5 * s + 1, cy + 20 * s), fill=hs)
        for i in range(2):   # the comb-over: two brave strands across the top
            y0 = cy - 8 * s + i * 5 * s
            d.line((cx - 19 * s, y0 + 5, cx - 6 * s, y0 - 3, cx + 8 * s, y0 - 2), fill=hc, width=1)
        paint(img, [ell(cx - 8 * s, cy - 12 * s, 6 * s, 4 * s)], lt(skin_of(sp)[0], 1.08), None, None, lt(skin_of(sp)[0], 1.08), outline=False)
        d.point((cx - 10 * s, cy - 14 * s), fill=C['white']); d.point((cx - 9 * s, cy - 14 * s), fill=C['white'])
    elif st == 'cap':
        cc = sp['capc']
        if not front:
            paint(img, [ell(cx, cy - 19 * s, 18 * s, 8 * s)], dk(cc, 0.8), dk(cc, 0.72), None, dk(cc, 0.5))   # brim, pointing at the doors
            paint(img, [ell(cx, cy + 12 * s, 20 * s, 12 * s)], C['hairDk'], dk(C['hairDk'], 0.8), None, C['black'])   # short hair at the nape
        paint(img, [ell(cx, cy - 3 * s, 23 * s, 22 * s if not front else 18 * s)], cc, dk(cc, 0.82), lt(cc), dk(cc, 0.55), split=0.64)
        for a in (-0.7, -0.25, 0.25, 0.7):   # panel seams to the button
            d.line((cx, cy - 6 * s, cx + math.sin(a) * 22 * s, cy - 6 * s + math.cos(a) * 18 * s * (1 if not front else -1)), fill=dk(cc, 0.75))
        paint(img, [ell(cx, cy - 6 * s, 2.5 * s, 2.5 * s)], dk(cc, 0.85), None, None, dk(cc, 0.6))
        if not front:
            paint(img, [ell(cx, cy + 12 * s, 7 * s, 5 * s)], C['hairDk'], None, None, dk(cc, 0.6))     # strap opening
            d.line((cx - 7 * s, cy + 14 * s, cx + 7 * s, cy + 14 * s), fill=dk(cc, 0.6), width=2)
        else:
            paint(img, [ell(cx, cy - 18 * s, 19 * s, 6 * s)], dk(cc, 0.82), dk(cc, 0.72), None, dk(cc, 0.5))
    elif st in ('short', 'bob', 'ponytail'):
        if front:
            sh = [ell(cx, cy - 8 * s, 22 * s, 18 * s)]
            if st == 'bob': sh += [rect(cx - 24 * s, cy - 8 * s, cx - 17 * s, cy + 14 * s), rect(cx + 17 * s, cy - 8 * s, cx + 24 * s, cy + 14 * s)]
            paint(img, sh, hc, hs, hl, hd, split=0.64, ldepth=0.25)
            for i in range(-4, 5): d.line((cx + i * 4 * s, cy - 24 * s, cx + i * 5 * s, cy - 2 * s), fill=hs)
            paint(img, [ell(cx, cy + 0 * s, 15 * s, 5 * s)], skin_of(sp)[0], skin_of(sp)[1], None, skin_of(sp)[0], outline=False)  # forehead below the fringe
        else:
            low = {'short': 14, 'bob': 26, 'ponytail': 18}[st]
            paint(img, [ell(cx, cy - 1 * s, 23 * s, 25 * s), rect(cx - 22 * s, cy, cx + 22 * s, cy + low * s)], hc, hs, hl, hd, split=0.64, ldepth=0.3)
            for i in range(-5, 6):   # strands from the crown
                d.line((cx + i * 1.2 * s, cy - 14 * s, cx + i * 4.2 * s, cy + low * s - 2), fill=hs)
            d.arc((cx - 16 * s, cy - 20 * s, cx + 10 * s, cy + 2 * s), 200, 300, fill=hl, width=2)   # sheen
            if st == 'ponytail':
                paint(img, [ell(cx, cy + 20 * s, 5 * s, 4 * s)], sp.get('hairtie', C['red']), None, None, dk(sp.get('hairtie', C['red'])))
                paint(img, [poly((cx - 6 * s, cy + 22 * s), (cx + 6 * s, cy + 22 * s), (cx + 4 * s, cy + 52 * s), (cx, cy + 58 * s), (cx - 4 * s, cy + 52 * s))], hc, hs, hl, hd)
    elif st == 'beanie':
        bc = sp['capc']
        if not front:
            paint(img, [ell(cx, cy + 14 * s, 19 * s, 10 * s)], C['hairGrey'], dk(C['hairGrey'], 0.85), None, dk(C['hairGrey'], 0.6))
        paint(img, [ell(cx, cy - 4 * s, 23 * s, 22 * s)], bc, dk(bc, 0.82), lt(bc), dk(bc, 0.55), split=0.64)
        for i in range(-5, 6): d.line((cx + i * 1 * s, cy - 22 * s, cx + i * 4 * s, cy + 12 * s), fill=dk(bc, 0.8))
        paint(img, [ell(cx, cy + (12 if not front else -2) * s, 22 * s, 6 * s)] if not front else [rect(cx - 21 * s, cy - 4 * s, cx + 21 * s, cy + 1 * s)],
              lt(bc, 1.05), bc, None, dk(bc, 0.55))
    elif st == 'fedora':
        fc = sp['capc']
        paint(img, [ell(cx, cy - 2 * s, 38 * s, 30 * s)], dk(fc, 0.9), dk(fc, 0.78), lt(fc, 1.05), dk(fc, 0.5), split=0.66)   # brim
        paint(img, [ell(cx, cy - 4 * s, 22 * s, 19 * s)], fc, dk(fc, 0.82), lt(fc), dk(fc, 0.55), split=0.64)
        d.arc((cx - 22 * s, cy - 23 * s, cx + 22 * s, cy + 15 * s), 20, 160, fill=C['black'], width=3)   # hat band
        d.line((cx - 10 * s, cy - 8 * s, cx + 10 * s, cy - 8 * s), fill=dk(fc, 0.6), width=2)             # the dent
        d.line((cx - 5 * s, cy - 14 * s, cx + 5 * s, cy - 14 * s), fill=lt(fc, 1.2))
    elif st == 'hardhat':
        y = C['yel']
        paint(img, [ell(cx, cy - 2 * s, 29 * s, 26 * s)], dk(y, 0.85), dk(y, 0.75), None, dk(y, 0.55))
        paint(img, [ell(cx, cy - 4 * s, 23 * s, 21 * s)], y, dk(y, 0.82), lt(y), dk(y, 0.55), split=0.64)
        paint(img, [rect(cx - 3 * s, cy - 24 * s, cx + 3 * s, cy + 16 * s)], lt(y, 1.05), y, None, dk(y, 0.6))
    elif st == 'dino':
        g = C['dino']
        paint(img, [ell(cx, cy, 25 * s, 27 * s)], g, dk(g, 0.82), lt(g), dk(g, 0.55), split=0.64)
        if front:
            paint(img, [ell(cx, cy + 10 * s, 15 * s, 13 * s)], *skin_of(sp)[:2], None, skin_of(sp)[2])
            for side in (-1, 1):
                ex = cx + side * 6 * s; ey = cy + 8 * s
                paint(img, [ell(ex, ey, 3.4 * s, 2.6 * s)], C['white'], None, None, C['black'])
                d.point((ex, ey), fill=C['black']); d.point((ex, ey - 1), fill=C['black'])
            d.line((cx - 3 * s, cy + 17 * s, cx + 3 * s, cy + 17 * s), fill=skin_of(sp)[2], width=2)
            for side in (-1, 1): paint(img, [ell(cx + side * 12 * s, cy - 14 * s, 3 * s, 3 * s)], C['white'], None, None, C['black'])  # hood eyes
        for i in range(5):
            yy = cy - 22 * s + i * (11 * s if not front else 3 * s)
            paint(img, [poly((cx - 5 * s, yy + 4 * s), (cx + 5 * s, yy + 4 * s), (cx, yy - 5 * s))], C['yel'], dk(C['yel'], 0.85), None, dk(C['yel']))
    if sp.get('headphones'):
        pc = sp['headphones']
        d.arc((cx - 25 * s, cy - 26 * s, cx + 25 * s, cy + 22 * s), 185, 355, fill=C['black'], width=4)
        d.arc((cx - 24 * s, cy - 25 * s, cx + 24 * s, cy + 21 * s), 200, 340, fill=C['greyD'], width=1)
        for side in (-1, 1): paint(img, [ell(cx + side * 24 * s, cy + 6 * s, 6 * s, 9 * s)], pc, dk(pc, 0.8), lt(pc), C['black'])

def b_body(img, sp, s, yo, front, arms):
    top = sp['top']; sk, sks, skd = skin_of(sp)
    d = ImageDraw.Draw(img)
    sy = 138 + yo
    if arms == 'box' and not front:   # the parcel he carries sticks out on both sides, beyond his shoulders
        paint(img, [rect(BX - 66 * s, sy - 26 * s, BX + 66 * s, sy + 4 * s)], C['card'], C['cardD'], C['cardL'], dk(C['cardD'], 0.7), split=0.8, ldepth=0.3)
        d.line((BX - 66 * s, sy - 12 * s, BX + 66 * s, sy - 12 * s), fill=C['tape'], width=2)
    if sp.get('backpack') and not front:
        pass
    shp = [ell(BX - 46 * s, sy + 12 * s, 22 * s, 17 * s), ell(BX + 46 * s, sy + 12 * s, 22 * s, 17 * s),
           poly((BX - 50 * s, sy + 2 * s), (BX + 50 * s, sy + 2 * s), (BX + 66 * s, 200), (BX - 66 * s, 200))]
    paint(img, shp, top, dk(top, 0.82), lt(top), dk(top, 0.55), split=0.62, lsplit=0.22, ldepth=0.25)
    # cloth folds
    for side in (-1, 1):
        d.arc((BX + side * 30 * s - 14 * s, sy + 8 * s, BX + side * 30 * s + 14 * s, sy + 30 * s), 200 if side < 0 else 250, 290 if side < 0 else 340, fill=dk(top, 0.7))
    if not front:
        if sp.get('seam', True): d.line((BX, sy + 6 * s, BX, H), fill=dk(top, 0.72))
        if sp.get('backpack'):
            bp = sp['backpack']
            for side in (-1, 1): d.line((BX + side * 26 * s, sy + 2 * s, BX + side * 30 * s, H), fill=dk(bp, 0.6), width=max(3, round(5 * s)))
            paint(img, [rect(BX - 30 * s, sy + 18 * s, BX + 30 * s, 200)], bp, dk(bp, 0.82), lt(bp), dk(bp, 0.55), split=0.75, ldepth=0.3)
            d.line((BX - 28 * s, sy + 24 * s, BX + 28 * s, sy + 24 * s), fill=dk(bp, 0.65), width=2)
        if sp.get('overalls'):
            o = sp['overalls']
            for side in (-1, 1): d.line((BX + side * 18 * s, sy, BX + side * 14 * s, H), fill=o, width=max(4, round(6 * s)))
    else:
        if sp.get('tie'):
            paint(img, [poly((BX - 10 * s, sy - 2 * s), (BX + 10 * s, sy - 2 * s), (BX, sy + 16 * s))], C['white'], C['paper'], None, C['paperD'])
            paint(img, [poly((BX - 3 * s, sy + 4 * s), (BX + 3 * s, sy + 4 * s), (BX + 5 * s, sy + 34 * s), (BX, sy + 40 * s), (BX - 5 * s, sy + 34 * s))], sp['tie'], dk(sp['tie'], 0.82), None, dk(sp['tie'], 0.55))
        if sp.get('overalls'):
            o = sp['overalls']
            paint(img, [rect(BX - 22 * s, sy + 18 * s, BX + 22 * s, 200)], o, dk(o, 0.82), None, dk(o, 0.55))
            for side in (-1, 1): d.line((BX + side * 20 * s, sy + 18 * s, BX + side * 16 * s, sy), fill=dk(o, 0.8), width=max(3, round(4 * s)))
    # neck (in shadow from behind) + collar
    paint(img, [rect(BX - 10 * s, 112 * s + yo + (1 - s) * 112, BX + 10 * s, sy + 4 * s)], sks if not front else sk, skd, None, skd, outline=False)
    col = sp.get('collar', dk(top, 0.9))
    if not sp.get('noCollar'):
        paint(img, [ell(BX, sy + 1 * s, 15 * s, 6 * s)], col, dk(col, 0.85), lt(col), dk(col, 0.6))
        paint(img, [ell(BX, sy - 1 * s, 10.5 * s, 3.5 * s)], sks if not front else sk, skd, None, skd, outline=False)
    if sp.get('scarf'):
        sc = sp['scarf']; paint(img, [ell(BX, sy + 2 * s, 24 * s, 9 * s)], sc, dk(sc, 0.82), lt(sc), dk(sc, 0.55))
        d.line((BX - 20 * s, sy + 2 * s, BX + 20 * s, sy + 2 * s), fill=dk(sc, 0.72))

def b_arms(img, sp, s, yo, front, arms, head_c):
    """Arms that come up into the picture (most poses keep them below the frame)."""
    sk, sks, skd = skin_of(sp); sl = sp.get('sleeve', sp['top'])
    sy = 138 + yo
    def limb(a, b, c, w=7):
        paint(img, [poly((a[0] - w * s, a[1]), (a[0] + w * s, a[1]), (b[0] + w * 0.85 * s, b[1]), (b[0] - w * 0.85 * s, b[1])), ell(b[0], b[1], w * 0.9 * s, w * 0.9 * s),
                    poly((b[0] - w * 0.8 * s, b[1]), (b[0] + w * 0.8 * s, b[1]), (c[0] + w * 0.7 * s, c[1]), (c[0] - w * 0.7 * s, c[1]))],
              sl, dk(sl, 0.82), lt(sl), dk(sl, 0.55), split=0.6)
        paint(img, [ell(c[0], c[1] - 3 * s, 5.5 * s, 6.5 * s)], sk, sks, lt(sk), skd, split=0.6)
    hx_, hy_ = head_c
    if arms == 'phone':
        limb((BX + 48 * s, sy + 26 * s), (BX + 42 * s, sy - 6 * s), (hx_ + 22 * s, hy_ + 6 * s))
        paint(img, [rect(hx_ + 17 * s, hy_ - 6 * s, hx_ + 23 * s, hy_ + 12 * s)], C['black'], C['black'], C['greyD'], C['black'])
    elif arms in ('up', 'upL', 'upR'):
        for side in (-1, 1):
            if (arms == 'upL' and side > 0) or (arms == 'upR' and side < 0): continue
            limb((BX + side * 46 * s, sy + 8 * s), (BX + side * 52 * s, sy - 30 * s), (BX + side * 34 * s, sy - 72 * s))
    elif arms == 'wave':
        limb((BX + 48 * s, sy + 20 * s), (BX + 62 * s, sy - 10 * s), (BX + 56 * s, sy - 46 * s))
        d = ImageDraw.Draw(img)
        for i in range(4): d.line((BX + (50 + i * 4) * s, sy - 50 * s, BX + (49 + i * 4.5) * s, sy - 58 * s), fill=sks, width=2)
    elif arms == 'box' and front:
        paint(img, [rect(BX - 44 * s, sy + 6 * s, BX + 44 * s, H)], C['card'], C['cardD'], C['cardL'], dk(C['cardD'], 0.7), split=0.8, ldepth=0.3)
        ImageDraw.Draw(img).line((BX, sy + 6 * s, BX, H), fill=C['tape'], width=2)
        for side in (-1, 1): paint(img, [ell(BX + side * 42 * s, sy + 20 * s, 6 * s, 8 * s)], sk, sks, None, skd)
    elif arms == 'mop':
        d = ImageDraw.Draw(img)
        d.line((BX + 58 * s, H, BX + 30 * s, 66 + yo), fill=C['woodD'], width=4); d.line((BX + 57 * s, H, BX + 29 * s, 66 + yo), fill=C['woodL'], width=1)
        paint(img, [ell(BX + 52 * s, sy + 18 * s, 6 * s, 7 * s)], sk, sks, None, skd)

def bust(sp, facing='back', talk=False, arms='down', sit=False, eyes='open'):
    img = new(W, H)
    s = sp.get('bscale', 1.0)
    yo = sp.get('byo', 0) + (36 if sit else 0)
    front = facing == 'front'
    if sit: s *= 0.88
    b_body(img, sp, s, yo, front, arms)
    if sit:   # knees in front of the chest
        bot = sp.get('skirt', sp.get('bottom', C['navy']))
        for side in (-1, 1):
            paint(img, [ell(BX + side * 22 * s, H - 6, 18 * s, 13 * s)], bot, dk(bot, 0.82), lt(bot), dk(bot, 0.55))
            paint(img, [ell(BX + side * 22 * s, H - 14, 6 * s, 6 * s)], *skin_of(sp)[:2], None, skin_of(sp)[2])
    if front:
        hc_ = b_head_front(img, sp, s, yo, talk, eyes)
    else:
        hc_ = b_head_back(img, sp, s, yo, hdx=2 if talk else 0)
    b_hair(img, sp, s, hc_[0], hc_[1], front)
    if not sit: b_arms(img, sp, s, yo, front, arms, hc_)
    if sit and sp.get('lunch'):
        paint(img, [rect(BX - 10, H - 30, BX + 12, H - 20)], C['cream'], C['paperD'], None, C['brown'])
        ImageDraw.Draw(img).line((BX - 10, H - 25, BX + 12, H - 25), fill=C['green'], width=2)
    if not front and talk and not sp.get('noface'):   # a sliver of cheek and jaw when they turn to speak
        sk, sks, skd = skin_of(sp)
        paint(img, [ell(hc_[0] + 21 * s, hc_[1] + 16 * s, 4 * s, 6 * s)], sk, sks, None, skd)
    return img

BSPEC = {
    'pruitt': dict(hair='perm', hairc=C['lilac'], top=C['mustard'], scarf=C['pink'], glasses=hx('#3b3030'), old=True, bscale=0.9, byo=8),
    'haldane': dict(hair='bald', hairc=C['hairBr'], top=C['navy'], tie=C['red'], collar=C['white'], bscale=1.06),
    'rafi': dict(hair='cap', capc=C['red'], top=hx('#8a6a3c'), skin=(C['skin2'], C['skin2S'], C['skin2D']), collar=hx('#6e5432')),
    'mila': dict(hair='bob', hairc=C['hairDk'], headphones=C['redL'], top=C['teal'], backpack=C['yel'], bscale=0.92, byo=6, collar=dk(C['teal'], 0.85)),
    'gus': dict(hair='beanie', capc=C['greyD'], top=hx('#6d7a5a'), overalls=hx('#56663f'), mustache=C['hairGrey'], old=True,
                skin=(C['skin2'], C['skin2S'], C['skin2D'])),
    'toby': dict(hair='dino', top=C['blue'], bscale=0.66, byo=34, noCollar=True),
    'mom': dict(hair='ponytail', hairc=C['hairBr'], top=C['red'], bscale=0.95, byo=4),
    'grey': dict(hair='fedora', capc=C['grey'], top=C['greyD'], noface=True, seam=False, collar=C['charcoal'], bscale=1.02),
    'tech': dict(hair='hardhat', top=C['blue'], overalls=dk(C['blue'], 0.85), collar=dk(C['blue'], 0.8)),
    'dev': dict(hair='short', hairc=C['black'], top=C['red'], skin=(C['skin2'], C['skin2S'], C['skin2D']), bscale=0.92),
    'priya': dict(hair='ponytail', hairc=C['hairDk'], top=C['yel'], skin=(C['skin2'], C['skin2S'], C['skin2D']), bscale=0.86, byo=4, hairtie=C['teal']),
}

def walker(name, slot, kind):
    """Entering / leaving frames: the small walking figure, drawn so that it lands on the doors (far) or halfway
    (mid) whatever slot the object has been moved to. kind: farF, midF, midB, farB."""
    img = new(W, H)
    dx = SLOTS[slot] - BX
    sp = dict(SPEC[name])
    far = kind.startswith('far')
    sp['scale'] = sp.get('scale', 1.0) * (0.62 if far else 1.0)
    f = figure(sp, facing='front' if kind.endswith('F') else 'back', walk=1 if kind in ('farF', 'midB') else -1,
               arms={'haldane': 'phone', 'rafi': 'box'}.get(name, 'down'))
    if not far: f = f.resize((round(f.width * 1.35), round(f.height * 1.35)), Image.NEAREST)
    fx = BX - dx if far else BX - dx // 2
    fy = 94 if far else 150
    off = (PH - BASE) * (1 if far else 1.35)
    img.alpha_composite(f, (round(fx - f.width / 2), round(fy - f.height + off)))
    return img

def person(name):
    sp = BSPEC[name]
    b = lambda **k: bust(sp, **k)
    base_arms = {'haldane': 'phone', 'rafi': 'box'}.get(name, 'down')
    frames = [b(arms=base_arms), b(arms=base_arms, talk=True), b(facing='front', arms=base_arms), b(facing='front', arms=base_arms, talk=True), new(W, H)]
    anims = {'default': [0], 'habla': [1, 0], 'front': [2], 'hablaF': [3, 2], 'gone': [4]}
    def add(anim, *fr):
        idx = []
        for x in fr: frames.append(x); idx.append(len(frames) - 1)
        anims[anim] = idx
    for slot in SLOTS:
        ff, mf, mb, fb = (walker(name, slot, k) for k in ('farF', 'midF', 'midB', 'farB'))
        frames += [ff, mf, mb, fb]; n = len(frames)
        anims['enter' + slot] = [n - 4, n - 3, 2]
        anims['leave' + slot] = [n - 2, n - 1, 4]
    if name in ('haldane', 'pruitt'):
        add('sit', b(facing='front', sit=True)); add('sitHabla', b(facing='front', sit=True, talk=True), b(facing='front', sit=True))
    if name == 'haldane':
        add('wave', b(facing='front', arms='wave'), b(facing='front', arms='wave', talk=True))
        add('nophone', b())
    if name == 'rafi':
        add('nobox', b()); add('noboxHabla', b(talk=True), b())
        lunch = dict(sp, lunch=True)
        add('sit', bust(lunch, facing='front', sit=True)); add('sitHabla', bust(lunch, facing='front', sit=True, talk=True), bust(lunch, facing='front', sit=True))
    if name == 'mila':
        add('dance', b(arms='upL'), b(arms='up'), b(arms='upR'), b(arms='up', talk=True))
        add('fall', b(facing='front', sit=True)); add('fallHabla', b(facing='front', sit=True, talk=True), b(facing='front', sit=True))
        add('grimace', b(facing='front', arms='wave', talk=True), b(facing='front', arms='wave'))
    if name == 'toby':
        add('jump', b(arms='up'), b(arms='upR'))
        add('waveF', b(facing='front', arms='wave', talk=True), b(facing='front', arms='wave'))
    if name == 'gus':
        add('mop', b(arms='mop'), b(arms='mop', talk=True))
    return anims, frames

def couple():
    """Dev and Priya side by side, and the flat-pack wardrobe box wedged diagonally towards the doors."""
    frames = []
    def two(talkD=False, talkP=False, box=False, front=False):
        im = new(W, H)
        dv = bust(BSPEC['dev'], facing='front' if front else 'back', talk=talkD, arms='up' if box else 'down')
        pr = bust(BSPEC['priya'], facing='front' if front else 'back', talk=talkP, arms='up' if box else 'down')
        if box:
            bx = new(W, H)
            paint(bx, [poly((40, 54), (60, 34), (214, 92), (196, 114))], C['card'], C['cardD'], C['cardL'], dk(C['cardD'], 0.7), split=0.85)
            d = ImageDraw.Draw(bx); d.line([(50, 44), (205, 103)], fill=C['tape'], width=2)
            paint(bx, [poly((110, 64), (136, 74), (132, 82), (106, 72))], C['white'], None, None, C['paperD'])
            im.alpha_composite(bx)
        im.alpha_composite(pr, (-52, 0)); im.alpha_composite(dv, (52, 0))
        return im
    frames = [two(box=True), two(box=True, talkD=True), two(box=True, talkP=True), two(), two(talkP=True), two(talkD=True), new(W, H)]
    anims = {'default': [0], 'box': [0], 'hablaDev': [1, 0], 'hablaPriya': [2, 0], 'nobox': [3], 'hablaNobox': [4, 3], 'hablaNoboxDev': [5, 3], 'gone': [6]}
    # entering/leaving: the two small figures (with the box when they carry it)
    def pair(scale, fy, back, box):
        im = new(W, H)
        for name, x in (('priya', -14), ('dev', 14)):
            sp = dict(SPEC[name]); sp['scale'] = sp.get('scale', 1.0) * scale
            f = figure(sp, facing='back' if back else 'front', walk=1, arms='up' if box else 'down')
            if scale > 0.9: f = f.resize((round(f.width * 1.3), round(f.height * 1.3)), Image.NEAREST); xx = x * 2
            else: xx = x
            im.alpha_composite(f, (round(BX + xx - f.width / 2), round(fy - f.height + 3)))
        if box:
            w_ = 40 if scale < 0.9 else 90
            paint(im, [poly((BX - w_ / 2, fy - 50 * scale - 6), (BX - w_ / 2 + 6, fy - 50 * scale - 12), (BX + w_ / 2, fy - 50 * scale + 6), (BX + w_ / 2 - 6, fy - 50 * scale + 12))],
                  C['card'], C['cardD'], None, dk(C['cardD'], 0.7))
        return im
    for name, fr in (('enterC', [pair(0.62, 94, False, True), pair(1.0, 150, False, True), 0]),
                     ('enterNoboxC', [pair(0.62, 94, False, False), pair(1.0, 150, False, False), 3]),
                     ('leaveC', [pair(1.0, 150, True, True), pair(0.62, 94, True, True), 6]),
                     ('leaveNoboxC', [pair(1.0, 150, True, False), pair(0.62, 94, True, False), 6])):
        idx = []
        for x in fr:
            if isinstance(x, int): idx.append(x)
            else: frames.append(x); idx.append(len(frames) - 1)
        anims[name] = idx
    return anims, frames

def dark():
    """Lights off: only the seams of the doors catch corridor light."""
    im = new(W, H, (9, 10, 15, 246)); d = ImageDraw.Draw(im)
    (a, b, c_, e) = DOOR_POLY
    d.line([e, a], fill=(34, 36, 42, 255)); d.line([c_, b], fill=(34, 36, 42, 255))
    d.line([((e[0] + c_[0]) // 2, e[1]), ((a[0] + b[0]) // 2, a[1])], fill=(80, 76, 62, 255))
    d.line([(a[0] - 2, a[1] + 3), (b[0] + 2, b[1] + 3)], fill=(56, 54, 46, 255))
    d.rectangle((DISPLAY_TL[0] - 1, DISPLAY_TL[1] - 1, DISPLAY_TL[0] + 24, DISPLAY_TL[1] + 8), outline=(22, 22, 26, 255))
    return im

def ghost():
    """Night-vision-only: the man in the grey hat, standing in the dark car, facing the doors."""
    im = bust(BSPEC['grey'])
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if a: px[x, y] = (int(r * 0.4 + 30), int(g * 0.5 + 60), int(b * 0.4 + 30), min(a, 190))
    return im

PEOPLE = ['pruitt', 'haldane', 'rafi', 'mila', 'gus', 'toby', 'mom', 'grey', 'tech']
PW_BUST, PH_BUST = W, H

def build(out):
    os.makedirs(out, exist_ok=True)
    L, SPEC_OUT = {}, {}
    def save(name, img, kind='cam'):
        img = override(kind, name, img.size) or img
        p = os.path.join(out, name + '.png'); img.save(p)
        SPEC_OUT['%s/%s' % (kind, name)] = {'size': list(img.size), 'transparent': img.getpixel((0, 0))[3] == 0, 'current': p}
        L.setdefault(name, {'w': img.width, 'h': img.height})
    def save_sheet(name, anims, frames, kind='cam'):
        frames = [override(kind, '%s_%d' % (name, i), f.size) or f for i, f in enumerate(frames)]
        p = os.path.join(out, name + '.png'); sheet(frames).save(p, optimize=True)
        for i, f in enumerate(frames):
            SPEC_OUT['%s/%s_%d' % (kind, name, i)] = {'size': list(f.size), 'transparent': True, 'current': p, 'cell': i}
        L[name] = {'w': frames[0].width, 'h': frames[0].height, 'anims': anims}
    save_sheet('car', {'default': [0], 'day': [0], 'night': [1]}, [car('day'), car('night')])
    a, f = doors(); save_sheet('doors', a, f)
    a, f = display(); save_sheet('display', a, f)
    for n in PEOPLE:
        a, f = person(n); save_sheet(n, a, f, 'people')
    a, f = couple(); save_sheet('couple', a, f, 'people')
    a, f = dog(); save_sheet('dog', a, f, 'people')
    for k, im in props().items(): save(k, im)
    save('dark', dark()); save('ghost', ghost(), 'people')
    a, f = glitch(); save_sheet('glitch', a, f, 'fx')
    save('dot', outside_dot(), 'fx')
    return L, SPEC_OUT

if __name__ == '__main__':
    import json
    L, _ = build(sys.argv[1])
    print(json.dumps({k: {kk: (list(vv) if kk == 'anims' else vv) for kk, vv in v.items()} for k, v in L.items()}, indent=0)[:2500])
