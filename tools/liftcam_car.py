"""
The elevator car for the "Going Down" cage, in the game's interior style.

Two passes:
  1. a ray cast through the corner camera fills only the big planes (floor, walls, ceiling) with smooth light
     snapped to 4-6 tone ramps, so the light falls in a few clean bands like the game's painted rooms;
  2. everything with an edge (wall corners, door frame and leaves, panel seams, kick plates, the hand rails,
     tile joints, the display, the button panel, notices, scuffs) is projected through the same camera and
     drawn as crisp 1 px pixel-art lines and polygons.
"""
import math, os, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import liftcam_render as Rn
from liftcam_render import W, H, CW, CH, CD, DOOR_X, DOOR_H, DISP, PANEL, hexc, ramp

R = {
    # neutral steel greys, like the game's own elevator (its whole background uses about 60 colours)
    'wood':  ramp('#2f2f2f', '#454545', '#5b5b5b', '#727272', '#8a8a8a', '#a3a3a3'),
    'steel': ramp('#303030', '#474747', '#5e5e5e', '#777777', '#919191', '#acacac'),
    'door':  ramp('#3a3a3a', '#535353', '#6b6b6b', '#848484', '#9e9e9e', '#b8b8b8'),
    'floor': ramp('#2a2320', '#382e29', '#463a33', '#55473e', '#64554a', '#726256'),
    'brass': ramp('#4e3a1c', '#6d5226', '#8e6c33', '#b08a45', '#cfaa5e', '#e8c983'),
    'ceil':  ramp('#45423f', '#57534f', '#6b6661', '#807a74', '#968f88', '#ada69e'),
    'hall':  ramp('#262421', '#33302c', '#413d38', '#504b45', '#5f5952', '#6f685f'),
    'hallW': ramp('#3a3431', '#4a433f', '#5b534e', '#6d645e', '#80766f', '#938880'),
    'paper': ramp('#8a7f68', '#a39780', '#bbae95', '#cfc3a9', '#e0d6be', '#eee6d2'),
    'red':   ramp('#4a1714', '#6b221d', '#8c3028', '#ad4034', '#c85444', '#de6c5a'),
    'yel':   ramp('#5a4410', '#7d5f17', '#a07d22', '#c49c30', '#ddb848', '#efd170'),
    'ink':   ramp('#141210', '#1c1a17', '#24211d', '#2c2924', '#35312b', '#3e3a33'),
}
def c(name, i): return tuple(int(v) for v in R[name][i])

def q(light, n=6):
    return np.clip(np.floor(light * n), 0, 5).astype(int)

# ------------------------------------------------------------------ pass 1: planes
def fill():
    o, d = Rn.camera_rays(); o = o.reshape(-1, 3); d = d.reshape(-1, 3)
    t, face, p, _, _ = Rn.car_hits(o, d, 0.0)
    x, y, z = p[:, 0], p[:, 1], p[:, 2]
    img = np.zeros((o.shape[0], 3))
    gid = face.copy()
    # floor: a round pool of light under the lamp, darker towards the walls
    m = face == 0
    r = np.hypot((x - CW / 2) / CW, (z - CD / 2) / CD)
    img[m] = R['floor'][np.where(r < 0.42, 3, 2)[m]]
    m = face == 1
    img[m] = R['ceil'][3]
    # side/back walls: lit from above and from the middle of the car, darker low down and at the far ends
    for fi in (2, 3, 4):
        m = face == fi
        u = z if fi in (2, 3) else x
        span = CD if fi in (2, 3) else CW
        li = 0.40 + 0.30 * (y / CH) + 0.18 * (1 - np.abs(u - span / 2) / (span / 2)) - (0.10 if fi == 3 else 0)
        img[m] = R['wood'][{2: 3, 3: 2, 4: 3}[fi]]
    # door wall (steel)
    m = face == 5
    li = 0.5 + 0.3 * (y / CH) + 0.2 * (1 - np.abs(x - CW / 2) / (CW / 2))
    img[m] = R['steel'][4]
    return img.reshape(H, W, 3), gid.reshape(H, W), p.reshape(H, W, 3)

# ------------------------------------------------------------------ pass 2: projected pixel-art drawing
def cam_depth(pt):
    f, r, u = Rn.basis(Rn.CAM, Rn.LOOK)
    return (np.asarray(pt, float) - Rn.CAM) @ f

def P(pt):
    x, y = Rn.project(pt); return (x, y)

NEAR = 0.75   # lines closer to the lens than this are not drawn (they would smear across the frame)

def poly3(pts, n=10, closed=True):
    """Projected polygon (closed) with subdivided edges; points too close to the lens are dropped."""
    out = []
    seq = list(pts) + ([pts[0]] if closed else [])
    for a, b in zip(seq, seq[1:]):
        a, b = np.asarray(a, float), np.asarray(b, float)
        for j in range(n + (0 if closed else 1)):
            pt = a + (b - a) * j / n
            if cam_depth(pt) > NEAR: out.append(P(pt))
    return [(round(x), round(y)) for x, y in out]

def runs3(pts, n=10):
    """Open polyline split into the visible runs (no jumps across points dropped near the lens)."""
    runs, cur = [], []
    for a, b in zip(pts, pts[1:]):
        a, b = np.asarray(a, float), np.asarray(b, float)
        for j in range(n + 1):
            pt = a + (b - a) * j / n
            if cam_depth(pt) > NEAR: cur.append(tuple(round(v) for v in P(pt)))
            elif cur: runs.append(cur); cur = []
    if cur: runs.append(cur)
    return runs

def wall_pt(wall, u, y, off=0.0):
    """Point on a wall: wall L (x=0), R (x=CW), B (z=0), F (z=CD); u runs along the wall."""
    if wall == 'L': return (off, y, u)
    if wall == 'R': return (CW - off, y, u)
    if wall == 'B': return (u, y, off)
    return (u, y, CD - off)

def wall_quad(wall, u0, u1, y0, y1, off=0.0):
    return [wall_pt(wall, u0, y0, off), wall_pt(wall, u1, y0, off), wall_pt(wall, u1, y1, off), wall_pt(wall, u0, y1, off)]

def draw_car(mode='day', door='closed', sign=False):
    img, gid, pos = fill()
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), 'RGB').convert('RGBA')
    d = ImageDraw.Draw(im)
    def L(pts, col, w=1, n=10):
        for pp in runs3(pts, n):
            if len(pp) > 1: d.line(pp, fill=col, width=w)
    def F(pts, fill, outline=None, n=6):
        pp = poly3(pts, n, True)
        if len(pp) > 2: d.polygon(pp, fill=fill, outline=outline)
    # --- floor: tile joints, a worn path, a dropped receipt
    for i in range(1, int(CW / 0.35) + 1):
        L([(i * 0.35, 0, 0), (i * 0.35, 0, CD)], c('floor', 1))
    for i in range(1, int(CD / 0.35) + 1):
        L([(0, 0, i * 0.35), (CW, 0, i * 0.35)], c('floor', 1))
    F([(0.16, 0, 0.42), (0.27, 0, 0.36), (0.31, 0, 0.44), (0.2, 0, 0.5)], c('paper', 4), c('paper', 1))
    L([(0.2, 0.001, 0.43), (0.28, 0.001, 0.4)], c('paper', 1))
    # --- kick plates (steel) on every wall
    for wall, span in (('L', CD), ('R', CD), ('B', CW)):
        F(wall_quad(wall, 0, span, 0, 0.12), c('steel', 2))
        L([wall_pt(wall, 0, 0.12), wall_pt(wall, span, 0.12)], c('steel', 4))
    for x0, x1 in ((0, DOOR_X[0] - 0.07), (DOOR_X[1] + 0.07, CW)):
        F(wall_quad('F', x0, x1, 0, 0.12), c('steel', 1)); L([wall_pt('F', x0, 0.12), wall_pt('F', x1, 0.12)], c('steel', 3))
    for (wall, u) in (('R', 0.55), ('R', 1.2), ('L', 0.9), ('B', 0.7)):   # scuff marks
        L([wall_pt(wall, u, 0.05), wall_pt(wall, u + 0.07, 0.07)], c('steel', 0))
    # --- wood panels: seams with a lit bevel, a top rail
    for wall, span in (('L', CD), ('R', CD), ('B', CW)):
        k = 1
        while k * 0.44 < span - 0.05:
            u = k * 0.44
            L([wall_pt(wall, u, 0.12), wall_pt(wall, u, CH)], c('wood', 0))
            L([wall_pt(wall, u + 0.014, 0.12), wall_pt(wall, u + 0.014, CH)], c('wood', 5))
            k += 1
        L([wall_pt(wall, 0, 1.55), wall_pt(wall, span, 1.55)], c('wood', 1))
        L([wall_pt(wall, 0, 1.565), wall_pt(wall, span, 1.565)], c('wood', 4))
    # --- corners of the car
    for a, b in (((0, 0, CD), (0, CH, CD)), ((CW, 0, CD), (CW, CH, CD)), ((CW, 0, 0), (CW, CH, 0)),
                 ((0, 0, 0), (0, 0, CD)), ((CW, 0, 0), (CW, 0, CD)), ((0, 0, CD), (CW, 0, CD)), ((0, 0, 0), (CW, 0, 0))):
        L([a, b], c('wood', 0) if a[2] != CD or b[2] != CD else c('steel', 0))
    # --- notices: inspection certificate (right wall), no-smoking sign, a camera sticker (left wall)
    F(wall_quad('R', 1.2, 1.5, 1.3, 1.62), c('steel', 1), c('steel', 0))
    F(wall_quad('R', 1.22, 1.48, 1.32, 1.6), c('paper', 4))
    for i in range(4): L([wall_pt('R', 1.25, 1.55 - i * 0.05), wall_pt('R', 1.25 + (0.2 if i % 2 else 0.14), 1.55 - i * 0.05)], c('paper', 1))
    L([wall_pt('R', 1.27, 1.36), wall_pt('R', 1.33, 1.36)], c('red', 3))
    F(wall_quad('R', 0.62, 0.71, 1.62, 1.71), c('paper', 5), c('red', 2))
    L([wall_pt('R', 0.63, 1.63), wall_pt('R', 0.7, 1.7)], c('red', 3), 1)
    F(wall_quad('L', 1.25, 1.43, 1.55, 1.7), c('yel', 4), c('yel', 0))
    F(wall_quad('L', 1.29, 1.37, 1.6, 1.65), c('ink', 2))
    # --- bumper rails: a dark steel band along the side walls, light top edge
    for wall in ('L', 'R', 'B'):
        span = CW if wall == 'B' else CD
        F(wall_quad(wall, 0.0, span, 0.82, 0.96, 0.02), c('steel', 1), c('steel', 0))
        L([wall_pt(wall, 0.0, 0.955, 0.021), wall_pt(wall, span, 0.955, 0.021)], c('steel', 4))
        L([wall_pt(wall, 0.0, 0.94, 0.021), wall_pt(wall, span, 0.94, 0.021)], c('steel', 2))
    # --- door wall: frame, opening, leaves, sill, display, button panel, intercom
    fx0, fx1 = DOOR_X[0] - 0.07, DOOR_X[1] + 0.07
    F(wall_quad('F', fx0, fx1, 0, DOOR_H + 0.07), c('door', 4), c('steel', 0))
    L([wall_pt('F', fx0 + 0.02, DOOR_H + 0.05), wall_pt('F', fx1 - 0.02, DOOR_H + 0.05)], c('door', 5))
    F(wall_quad('F', DOOR_X[0], DOOR_X[1], 0, DOOR_H), c('hall', 1), c('ink', 0))
    F([(fx0, 0.002, CD - 0.07), (fx1, 0.002, CD - 0.07), (fx1, 0.002, CD), (fx0, 0.002, CD)], c('steel', 4), c('steel', 1))
    L([(fx0, 0.003, CD - 0.035), (fx1, 0.003, CD - 0.035)], c('steel', 1))
    F(wall_quad('F', DISP[0], DISP[1], DISP[2], DISP[3]), c('ink', 0), c('steel', 0))
    F(wall_quad('F', PANEL[0], PANEL[1], PANEL[2], PANEL[3]), c('steel', 1), c('steel', 0))
    L([wall_pt('F', PANEL[0] + 0.01, PANEL[3] - 0.01), wall_pt('F', PANEL[1] - 0.01, PANEL[3] - 0.01)], c('steel', 3))
    for row in range(6):
        for col in range(2):
            px, py = P(wall_pt('F', PANEL[0] + 0.045 + col * 0.05, PANEL[2] + 0.06 + row * 0.055))
            d.rectangle((round(px), round(py), round(px) + 1, round(py)), fill=c('yel', 5))
            d.point((round(px), round(py) + 1), fill=c('steel', 0))
    px, py = P(wall_pt('F', (PANEL[0] + PANEL[1]) / 2, PANEL[3] - 0.05)); d.rectangle((round(px) - 1, round(py), round(px) + 1, round(py) + 1), fill=c('red', 4))
    F(wall_quad('F', PANEL[0] + 0.01, PANEL[1] - 0.01, 0.72, 0.86), c('steel', 1), c('steel', 0))
    for i in range(3): L([wall_pt('F', PANEL[0] + 0.03, 0.75 + i * 0.04), wall_pt('F', PANEL[1] - 0.03, 0.75 + i * 0.04)], c('ink', 1))
    draw_leaves(im, d, door, sign)
    px_ = np.asarray(im).astype(float)
    if mode == 'night':
        px_[..., :3] = px_[..., :3] * np.array([0.6, 0.64, 0.84]) + np.array([4, 6, 16])
    if mode == 'dark':
        px_[..., :3] = px_[..., :3] * 0.1 + np.array([5, 6, 10])
    return Image.fromarray(np.clip(px_, 0, 255).astype(np.uint8), 'RGBA')

def draw_leaves(im, d, door, sign):
    """Door leaves inside the opening. door: closed | open1 | open2 | open | pried."""
    gap = {'closed': 0.0, 'open1': 0.18, 'open2': 0.46, 'open': 0.8, 'pried': 0.16}[door]
    mid = (DOOR_X[0] + DOOR_X[1]) / 2
    def F(pts, fill, outline=None):
        pp = poly3(pts, 6, True)
        if len(pp) > 2: d.polygon(pp, fill=fill, outline=outline)
    def L(pts, col, w=1):
        for pp in runs3(pts, 10):
            if len(pp) > 1: d.line(pp, fill=col, width=w)
    if gap > 0:   # the landing behind the doors
        lay = Image.new('RGBA', im.size, (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
        def LF(pts, fill, outline=None):
            pp = poly3(pts, 6, True)
            if len(pp) > 2: ld.polygon(pp, fill=fill, outline=outline)
        far = CD + 1.5
        LF([(-1.2, 0, far), (CW + 1.2, 0, far), (CW + 1.2, 2.6, far), (-1.2, 2.6, far)], c('hallW', 2))
        LF([(-1.2, 0, CD), (CW + 1.2, 0, CD), (CW + 1.2, 0, far), (-1.2, 0, far)], c('hall', 3))
        for i in range(-4, 9):
            for pp in runs3([(i * 0.3, 0.001, CD), (i * 0.3, 0.001, far)], 6):
                if len(pp) > 1: ld.line(pp, fill=c('hall', 1))
        LF([(mid - 0.42, 0, far), (mid + 0.42, 0, far), (mid + 0.42, 2.0, far), (mid - 0.42, 2.0, far)], c('wood', 2), c('wood', 0))
        kx, ky = P((mid + 0.3, 1.0, far)); ld.point((round(kx), round(ky)), fill=c('brass', 5))
        LF([(mid - 0.12, 2.15, far), (mid + 0.12, 2.15, far), (mid + 0.12, 2.25, far), (mid - 0.12, 2.25, far)], c('paper', 5))
        mask = Image.new('L', im.size, 0)
        ImageDraw.Draw(mask).polygon(poly3(wall_quad('F', DOOR_X[0], DOOR_X[1], 0, DOOR_H), 6, True), fill=255)
        im.paste(lay, (0, 0), Image.composite(lay.getchannel('A'), Image.new('L', im.size, 0), mask))
    for side in (-1, 1):
        a = DOOR_X[0] if side < 0 else mid + gap / 2
        b = mid - gap / 2 if side < 0 else DOOR_X[1]
        if b - a < 0.02: continue
        F(wall_quad('F', a, b, 0, DOOR_H, 0.01), c('door', 3), c('ink', 0))
        w = b - a
        for f0, f1, tn in ((0.12, 0.2, 4), (0.2, 0.24, 5), (0.62, 0.66, 4)):   # reflections of the lamp
            F(wall_quad('F', a + w * f0, a + w * f1, 0.02, DOOR_H - 0.02, 0.011), c('door', tn))
        L([wall_pt('F', a + 0.01, DOOR_H - 0.01, 0.012), wall_pt('F', b - 0.01, DOOR_H - 0.01, 0.012)], c('door', 5))
    if gap == 0: L([wall_pt('F', mid, 0, 0.012), wall_pt('F', mid, DOOR_H, 0.012)], c('ink', 0))
    if door == 'pried':
        lay = Image.new('RGBA', im.size, (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
        ld.polygon(poly3([(mid - 0.05, 1.7, CD), (mid + 0.05, 1.7, CD), (mid + 0.5, 0, CD - 0.9), (mid - 0.5, 0, CD - 0.9)], 4, True), fill=(255, 238, 186, 90))
        im.alpha_composite(lay)
        for sx in (-0.09, 0.09):   # gloved hands in the gap
            F(wall_quad('F', mid + sx - 0.03, mid + sx + 0.03, 1.2, 1.32, 0.02), c('yel', 4), c('yel', 0))
        px, py = P((mid, 1.72, CD + 0.1)); d.ellipse((round(px) - 2, round(py) - 2, round(px) + 2, round(py) + 2), fill=(255, 250, 220))
    if sign:
        F(wall_quad('F', mid - 0.24, mid + 0.24, 1.3, 1.6, 0.013), c('paper', 5), c('red', 2))
        for yy, ww in ((1.52, 0.17), (1.42, 0.13)):
            L([wall_pt('F', mid - ww, yy, 0.014), wall_pt('F', mid + ww, yy, 0.014)], c('red', 3), 2)
        for k in (1, -1):
            L([wall_pt('F', DOOR_X[0] + 0.04, 1.45 - k * 0.45, 0.015), wall_pt('F', DOOR_X[1] - 0.04, 1.45 + k * 0.45, 0.015)], c('yel', 4), 3)

def door_bbox():
    pp = poly3(wall_quad('F', DOOR_X[0], DOOR_X[1], 0, DOOR_H), 6, True) + [p for r in runs3([(DOOR_X[0], 0, CD - 1.0), (DOOR_X[1], 0, CD - 1.0)], 2) for p in r]
    xs, ys = [p[0] for p in pp], [p[1] for p in pp]
    return max(0, min(xs) - 3), max(0, min(ys) - 3), min(W - 1, max(xs) + 3), min(H - 1, max(ys) + 3)

def display_tl():
    pp = poly3(wall_quad('F', DISP[0], DISP[1], DISP[2], DISP[3]), 2, True)
    xs, ys = [p[0] for p in pp], [p[1] for p in pp]
    return (min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1)

if __name__ == '__main__':
    import sys
    ims = [draw_car('day'), draw_car('day', 'open'), draw_car('night'), draw_car('day', 'pried', sign=False)]
    sh = Image.new('RGBA', (W * 2 + 4, H * 2 + 4), (255, 255, 255, 255))
    for i, im in enumerate(ims): sh.paste(im, ((i % 2) * (W + 4), (i // 2) * (H + 4)))
    sh.resize((sh.width * 3, sh.height * 3), Image.NEAREST).save(sys.argv[1])
    print(door_bbox(), display_tl())
