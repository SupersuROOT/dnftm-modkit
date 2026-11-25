"""
A tiny ray caster that renders the "Going Down" elevator and its riders as pixel art (numpy).

Why: the original game's art is hand-painted pixel art whose shading follows the form in several close
tones with colour-matched outlines. Flat polygons drawn by code look like vector icons. Rendering simple 3D
shapes (a box-shaped car, people made of ellipsoids) and snapping the light to short colour ramps taken from
the game's palette gives the same banded, form-following look, and a correct corner-camera perspective.

World: metres, x to the right (seen from the back wall), y up, z towards the doors.
The car is CW x CH x CD; the doors are in the wall z = CD. The camera hangs in the back-left top corner.
"""
import math
import numpy as np
from PIL import Image

W, H = 252, 174
CW, CH, CD = 1.15, 2.25, 1.40          # a small car: 1.15 m wide, 1.4 m deep
DOOR_X = (0.22, 0.92); DOOR_H = 2.0
CAM = np.array([0.05, 2.20, 0.05])
LOOK = np.array([0.62, 1.05, CD])
HFOV = 98.0
BARREL = 0.08

def hexc(s): s = s.lstrip('#'); return np.array([int(s[i:i + 2], 16) for i in (0, 2, 4)], float)
def ramp(*cols): return np.array([hexc(c) for c in cols])

# colour ramps, dark -> light (muted, warm, like the game's interiors)
R = {
    'wood':  ramp('#3a271d', '#50362a', '#664534', '#7d563f', '#94684c', '#a97b5b'),
    'woodP': ramp('#33221a', '#472f24', '#5c3e2f', '#714d39', '#875e46', '#9b7055'),
    'steel': ramp('#3c4148', '#525860', '#6a7179', '#848b92', '#9fa5ab', '#babfc3'),
    'door':  ramp('#41474e', '#575e66', '#70777f', '#8a9198', '#a5abb1', '#c1c5c9'),
    'floor': ramp('#34312c', '#45413a', '#56514a', '#69635a', '#7c766b', '#8e887c'),
    'tileJ': ramp('#2a2824', '#36332e', '#433f39', '#524d46', '#615b53', '#6f6960'),
    'brass': ramp('#4e3a1c', '#6d5226', '#8e6c33', '#b08a45', '#cfaa5e', '#e8c983'),
    'ceil':  ramp('#4a4744', '#5d5955', '#726d68', '#88837c', '#a09a92', '#bdb7ae'),
    'lamp':  ramp('#d9d2bf', '#e6dfcc', '#f0ead8', '#f7f2e2', '#fcf8ec', '#fffdf6'),
    'hall':  ramp('#24221f', '#302d29', '#3d3934', '#4b4640', '#5a544d', '#6a635a'),
    'hallW': ramp('#2e2b2a', '#3c3836', '#4b4643', '#5b5551', '#6d6661', '#7f7771'),
    'black': ramp('#0e0d0c', '#151412', '#1c1a18', '#23211e', '#2a2724', '#312e2a'),
    'paper': ramp('#8a7f68', '#a39780', '#bbae95', '#cfc3a9', '#e0d6be', '#eee6d2'),
    'red':   ramp('#4a1714', '#6b221d', '#8c3028', '#ad4034', '#c85444', '#de6c5a'),
}

# ------------------------------------------------------------------ camera rays
def basis(cam, look):
    f = look - cam; f = f / np.linalg.norm(f)
    r = -np.cross(f, [0, 1, 0]); r /= np.linalg.norm(r)     # x right, y up, z forward: left-handed
    u = np.cross(f, r)
    return f, r, u

def camera_rays(cam=CAM, look=LOOK, hfov=HFOV, barrel=BARREL):
    f, r, u = basis(cam, look)
    tw = math.tan(math.radians(hfov / 2))
    xs = (np.arange(W) + 0.5) / W * 2 - 1
    ys = 1 - (np.arange(H) + 0.5) / H * 2
    X, Y = np.meshgrid(xs, ys)
    Y = Y * H / W
    rr = X * X + Y * Y
    X = X * (1 + barrel * rr); Y = Y * (1 + barrel * rr)          # wide CCTV lens
    d = f[None, None, :] + X[..., None] * tw * r[None, None, :] + Y[..., None] * tw * u[None, None, :]
    d /= np.linalg.norm(d, axis=-1, keepdims=True)
    return np.broadcast_to(cam, d.shape).copy(), d

def project(p, cam=CAM, look=LOOK, hfov=HFOV, barrel=BARREL):
    """World point -> image pixel (approximate inverse of the lens, good to a pixel)."""
    p = np.asarray(p, float)
    f, r, u = basis(cam, look)
    v = p - cam; z = v @ f
    tw = math.tan(math.radians(hfov / 2))
    X, Y = (v @ r) / z / tw, (v @ u) / z / tw
    for _ in range(3):   # undo the barrel by fixed-point iteration
        rr = X * X + Y * Y
        X, Y = (v @ r) / z / tw / (1 + barrel * rr), (v @ u) / z / tw / (1 + barrel * rr)
    rr = X * X + Y * Y
    Xd, Yd = X * (1 + barrel * rr), Y * (1 + barrel * rr)
    return ((Xd + 1) / 2 * W, (1 - Yd * W / H) / 2 * H)

# ------------------------------------------------------------------ primitives
def rot_y(a):
    c, s = math.cos(a), math.sin(a); return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
def rot_x(a):
    c, s = math.cos(a), math.sin(a); return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
def rot_z(a):
    c, s = math.cos(a), math.sin(a); return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])

class Prim:
    """Ellipsoid ('ell') or box ('box') with centre c, half-sizes r and rotation M (local -> world).
    mat(local_point, normal_local, world_point) -> (ramp name, tone offset array, extra dict)."""
    def __init__(self, kind, c, r, M=None, mat='steel', gid=0, shade=0.0, spec=0.0, flat=False):
        self.kind, self.c, self.r = kind, np.asarray(c, float), np.asarray(r, float)
        self.M = np.eye(3) if M is None else np.asarray(M, float)
        self.mat, self.gid, self.shade, self.spec, self.flat = mat, gid, shade, spec, flat

def seg(a, b, rad, **k):
    """Ellipsoid stretched between points a and b (a limb)."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    v = b - a; L = np.linalg.norm(v); y = v / L
    x = np.cross(y, [0, 0, 1]) if abs(y[2]) < 0.9 else np.cross(y, [1, 0, 0]); x /= np.linalg.norm(x)
    z = np.cross(x, y)
    return Prim('ell', (a + b) / 2, (rad, L / 2 + rad * 0.4, rad), np.stack([x, y, z], 1), **k)

def hit_prims(o, d, prims):
    """Returns t, prim index, local point, local normal, world normal for the nearest hits."""
    n = o.shape[0]
    tbest = np.full(n, np.inf); idx = np.full(n, -1)
    lp = np.zeros((n, 3)); ln = np.zeros((n, 3)); wn = np.zeros((n, 3))
    for i, p in enumerate(prims):
        Mi = p.M.T
        ol = (o - p.c) @ Mi.T; dl = d @ Mi.T
        if p.kind == 'ell':
            os_, ds = ol / p.r, dl / p.r
            a = (ds * ds).sum(1); b = 2 * (os_ * ds).sum(1); c = (os_ * os_).sum(1) - 1
            disc = b * b - 4 * a * c
            ok = disc >= 0
            sq = np.sqrt(np.where(ok, disc, 0))
            t = (-b - sq) / (2 * a)
            t = np.where(ok & (t > 1e-4), t, np.inf)
            q = ol + dl * t[:, None]
            nl = q / (p.r ** 2)
        else:
            inv = 1 / np.where(np.abs(dl) < 1e-9, 1e-9, dl)
            t1 = (-p.r - ol) * inv; t2 = (p.r - ol) * inv
            tmin = np.minimum(t1, t2).max(1); tmax = np.maximum(t1, t2).min(1)
            t = np.where((tmax >= tmin) & (tmin > 1e-4), tmin, np.inf)
            q = ol + dl * t[:, None]
            ax = np.argmax(np.abs(q) / p.r, 1)
            nl = np.zeros_like(q); nl[np.arange(n), ax] = np.sign(q[np.arange(n), ax])
        better = t < tbest
        tbest = np.where(better, t, tbest); idx = np.where(better, i, idx)
        lp[better] = q[better]; nlu = nl / np.maximum(np.linalg.norm(nl, axis=1, keepdims=True), 1e-9)
        ln[better] = nlu[better]; wn[better] = (nlu @ p.M.T)[better]
    return tbest, idx, lp, ln, wn

# ------------------------------------------------------------------ the car (inside of a box) + corridor
FONT = {
 'G': '011100101101011', '0': '111101101101111', '1': '010110010010111', '2': '111001111100111', '3': '111001111001111',
 '4': '101101111001001', '5': '111100111001111', '6': '111100111101111', '7': '111001001001001', '8': '111101111101111',
 '9': '111101111001111', '-': '000000111000000', ' ': '000000000000000',
}
DISP = (0.46, 0.68, 2.07, 2.16)     # display on the door wall: x0, x1, y0, y1
PANEL = (0.97, 1.09, 0.95, 1.42)    # button panel on the door wall, right of the doors

def car_hits(o, d, door_gap=0.0):
    """Hits on the inside of the car (6 planes); through the open doors the ray continues into the corridor."""
    n = o.shape[0]
    t = np.full(n, np.inf); face = np.full(n, -1)
    planes = [(1, 0.0, 'floor'), (1, CH, 'ceil'), (0, 0.0, 'wallL'), (0, CW, 'wallR'), (2, 0.0, 'back'), (2, CD, 'front')]
    for i, (ax, v, _) in enumerate(planes):
        dd = d[:, ax]
        ti = (v - o[:, ax]) / np.where(np.abs(dd) < 1e-9, 1e-9, dd)
        ok = (ti > 1e-5) & (ti < t)
        t = np.where(ok, ti, t); face = np.where(ok, i, face)
    p = o + d * t[:, None]
    # open doors: rays through the gap go on into the corridor
    mid = (DOOR_X[0] + DOOR_X[1]) / 2
    through = (face == 5) & (p[:, 1] < DOOR_H) & (np.abs(p[:, 0] - mid) < door_gap / 2)
    return t, face, p, through, [pl[2] for pl in planes]

def corridor_hits(o, d):
    """The landing beyond the doors: floor, far wall (with a flat door), side walls."""
    n = o.shape[0]
    t = np.full(n, np.inf); face = np.full(n, -1)
    planes = [(1, 0.0), (1, 2.6), (2, CD + 1.6), (0, -1.8), (0, CW + 1.8)]
    for i, (ax, v) in enumerate(planes):
        dd = d[:, ax]
        ti = (v - o[:, ax]) / np.where(np.abs(dd) < 1e-9, 1e-9, dd)
        ok = (ti > 1e-5) & (ti < t)
        t = np.where(ok, ti, t); face = np.where(ok, i, face)
    return t, face, o + d * t[:, None]

def tone(rmp, light, offset=0):
    """Light (0..~1.3) -> one of the ramp's 6 tones, in hard bands."""
    k = np.clip(np.floor(light * 5.2 + offset), 0, 5).astype(int)
    return rmp[k]

def lighting(p, n, mode):
    """Ceiling lamp + ambient; 'night' is dimmer and bluish (done later), 'dark' only the corridor glow."""
    lamp = np.array([CW / 2, CH - 0.05, CD / 2])
    L = lamp - p; dist = np.linalg.norm(L, axis=1, keepdims=True); L /= dist
    diff = np.clip((n * L).sum(1), 0, 1) / (0.55 + 0.35 * dist[:, 0] ** 2)
    amb = 0.42
    if mode == 'dark': return np.full(p.shape[0], 0.04)
    k = 0.62 if mode == 'night' else 1.0
    return (amb + 0.55 * diff) * k

def ao(p):
    """Darken next to the car's edges and corners (soft contact shadows)."""
    dx = np.minimum(p[:, 0], CW - p[:, 0]); dy = np.minimum(p[:, 1], CH - p[:, 1]); dz = np.minimum(p[:, 2], CD - p[:, 2])
    m = np.sort(np.stack([dx, dy, dz], 1), 1)[:, 1]          # distance to the nearest edge
    return np.clip(m / 0.22, 0, 1) * 0.16 - 0.16

def render_car(mode='day', door_gap=0.0, digits='G', sign=False, pried=False):
    o, d = camera_rays(); o = o.reshape(-1, 3); d = d.reshape(-1, 3)
    t, face, p, through, names = car_hits(o, d, door_gap)
    img = np.zeros((o.shape[0], 3)); gid = np.zeros(o.shape[0], int); depth = t.copy()
    normals = np.array([[0, 1, 0], [0, -1, 0], [1, 0, 0], [-1, 0, 0], [0, 0, 1], [0, 0, -1]], float)
    n = normals[np.clip(face, 0, 5)]
    lt = lighting(p, n, mode) + ao(p)
    x, y, z = p[:, 0], p[:, 1], p[:, 2]
    def put(mask, rmp, off=0.0, g=1, light=None):
        li = lt if light is None else light
        img[mask] = tone(R[rmp], li[mask], off if np.isscalar(off) else off[mask]); gid[mask] = g
    # floor: 40 cm rubber tiles, darker joints, a worn light path from the doors
    fl = face == 0
    tile = ((np.floor(x / 0.35) + np.floor(z / 0.35)) % 2) * 0.25
    joint = (np.abs(((x + 0.175) % 0.35) - 0.175) > 0.168) | (np.abs(((z + 0.175) % 0.35) - 0.175) > 0.168)
    put(fl, 'floor', tile, 1)
    put(fl & joint, 'tileJ', 0.3, 1)
    # ceiling (rarely seen) with the lamp panel
    ce = face == 1
    put(ce, 'ceil', 0, 2)
    lampm = ce & (np.abs(x - CW / 2) < 0.32) & (np.abs(z - CD / 2) < 0.42)
    put(lampm, 'lamp', 0.6 if mode != 'dark' else -6, 3)
    # side and back walls: wood veneer panels above a steel kick plate, a brass hand rail
    for fi, g in ((2, 4), (3, 5), (4, 6)):
        wm = face == fi
        u = z if fi in (2, 3) else x
        panel = (np.floor(u / 0.44) % 2) * 0.3
        grain = 0.0
        seam = np.abs(((u + 0.22) % 0.44) - 0.22) > 0.212
        put(wm, 'wood', panel + grain, g)
        put(wm & seam, 'woodP', -0.2, g)
        trim = wm & (np.abs(y - 1.62) < 0.018)
        put(trim, 'woodP', -0.4, g)
        put(wm & (y < 0.12), 'steel', 0.1, g + 20)
    # door wall: brushed steel, the door frame, the leaves, the display and the button panel
    fw = face == 5
    brushed = (np.sin(x * 70) > 0.8) * 0.3
    put(fw, 'steel', brushed, 7)
    inframe = fw & (x > DOOR_X[0] - 0.07) & (x < DOOR_X[1] + 0.07) & (y < DOOR_H + 0.07)
    put(inframe, 'door', 0.55, 8)
    leaves = fw & (x > DOOR_X[0]) & (x < DOOR_X[1]) & (y < DOOR_H)
    mid = (DOOR_X[0] + DOOR_X[1]) / 2
    put(leaves, 'door', brushed * 0.6 + 0.15, 9)
    gap = leaves & (np.abs(x - mid) < max(door_gap / 2, 0.011))
    put(gap, 'black', 1, 10)
    lgap = leaves & (np.abs(x - mid) >= door_gap / 2) & (np.abs(np.abs(x - mid) - door_gap / 2) < 0.012)
    put(lgap & (door_gap > 0), 'door', -1.2, 9)
    put(fw & (y < 0.04) & (x > DOOR_X[0] - 0.07) & (x < DOOR_X[1] + 0.07), 'steel', 1.2, 11)
    # display
    dm = fw & (x > DISP[0]) & (x < DISP[1]) & (y > DISP[2]) & (y < DISP[3])
    put(dm, 'black', 0, 12)
    if digits.strip() and mode != 'dark':
        gx = ((x - DISP[0]) / (DISP[1] - DISP[0]) * 24).astype(int); gy = ((DISP[3] - y) / (DISP[3] - DISP[2]) * 8).astype(int)
        bm = np.zeros((8, 24), bool); s = digits if len(digits) == 2 else ' ' + digits
        for i, ch in enumerate(s):
            g = FONT.get(ch, FONT[' '])
            for j, b in enumerate(g):
                if b == '1':
                    yy, xx = 1 + (j // 3) * 1, 7 + i * 5 + (j % 3) * 1
                    bm[yy:yy + 1, xx:xx + 1] = True
        lit = dm & bm[np.clip(gy, 0, 7), np.clip(gx, 0, 23)]
        col = hexc('#ff6a4a') if digits == '13' else hexc('#ffb43c')
        img[lit] = col
    # button panel (brass) with two columns of buttons and a red alarm button
    pm = fw & (x > PANEL[0]) & (x < PANEL[1]) & (y > PANEL[2]) & (y < PANEL[3])
    put(pm, 'brass', 0.3, 13)
    bu = pm & (np.abs(((x - PANEL[0]) % 0.07) - 0.035) < 0.013) & (np.abs(((y - PANEL[2]) % 0.075) - 0.0375) < 0.013) & (y < PANEL[3] - 0.08)
    put(bu, 'paper', 1.5, 13)
    put(pm & (y > PANEL[3] - 0.07) & (np.abs(x - (PANEL[0] + PANEL[1]) / 2) < 0.025), 'red', 2, 13)
    # an inspection certificate in a brass frame on the right wall
    cm = (face == 3) & (np.abs(z - 1.35) < 0.13) & (np.abs(y - 1.45) < 0.17)
    put(cm, 'brass', 0.5, 14)
    put(cm & (np.abs(z - 1.35) < 0.11) & (np.abs(y - 1.45) < 0.15), 'paper', 1.2, 14)
    # brass hand rails on the side walls (a horizontal cylinder in front of the wall)
    for xw, sgn, g in ((0.0, 1, 15), (CW, -1, 16)):
        cyl = Prim('ell', (xw + sgn * 0.045, 0.92, CD / 2), (0.022, 0.022, CD / 2 - 0.08), mat='brass')
        tr, ir, _, _, wnr = hit_prims(o, d, [cyl])
        m = (tr < t) & np.isfinite(tr)
        lr = lighting(o + d * tr[:, None], wnr, mode)
        put(m, 'brass', 0.2, g, light=np.where(m, lr, 0)); depth = np.where(m, tr, depth)
    # signs taped on the doors (day 7)
    if sign:
        sm = leaves & (np.abs(x - mid) < 0.26) & (np.abs(y - 1.45) < 0.15)
        put(sm, 'paper', 2.2, 17)
        txt = sm & (np.abs(y - 1.49) < 0.022) & (np.abs(x - mid) < 0.2) & (np.sin(x * 140) > 0)
        txt2 = sm & (np.abs(y - 1.41) < 0.022) & (np.abs(x - mid) < 0.16) & (np.sin(x * 140) > 0)
        put(txt | txt2, 'red', 2, 17)
        for k in (1, -1):
            tp = leaves & (np.abs((y - 1.45) - k * (x - mid) * 0.9) < 0.03) & (np.abs(x - mid) < 0.42)
            img[tp] = hexc('#d9b23a'); gid[tp] = 18
    # through the open doors: the landing
    if door_gap > 0:
        th = np.where(through)[0]
        if len(th):
            o2 = p[th] + d[th] * 1e-4; tc, fc, pc = corridor_hits(o2, d[th])
            nc = np.array([[0, 1, 0], [0, -1, 0], [0, 0, -1], [1, 0, 0], [-1, 0, 0]], float)[np.clip(fc, 0, 4)]
            lc = 0.35 + 0.4 * np.clip((nc * np.array([0, 0.6, -0.8])).sum(1), 0, 1)
            if mode == 'night': lc *= 0.7
            if mode == 'dark': lc *= 0.4
            col = tone(R['hallW'], lc, 0.0)
            flc = fc == 0
            col[flc] = tone(R['hall'], lc[flc], ((np.floor(pc[flc, 0] / 0.3) + np.floor(pc[flc, 2] / 0.3)) % 2) * 0.3)
            dr = (fc == 2) & (np.abs(pc[:, 0] - mid) < 0.42) & (pc[:, 1] < 2.0)
            col[dr] = tone(R['woodP'], lc[dr], 0.6)
            knob = dr & (np.abs(pc[:, 0] - (mid + 0.3)) < 0.03) & (np.abs(pc[:, 1] - 1.0) < 0.03)
            col[knob] = R['brass'][4]
            if pried:
                beam = np.abs(np.arctan2(pc[:, 0] - mid, pc[:, 1] - 1.6)) < 0.25
                col[beam] = col[beam] * 0.4 + np.array([250, 236, 190]) * 0.6
            img[th] = col; gid[th] = 30 + np.clip(fc, 0, 4); depth[th] = t[th] + tc
    if mode == 'night':
        img = img * np.array([0.62, 0.66, 0.86]) + np.array([4, 6, 16])
    if mode == 'dark':
        img = img * 0.35 + np.array([4, 5, 9])
    return finish(img, gid, depth)

def finish(img, gid, depth, alpha=None):
    """Colour-matched outlines where surfaces meet (darker version of the nearer surface), then an image."""
    img = img.reshape(H, W, 3); gid = gid.reshape(H, W); depth = depth.reshape(H, W)
    out = img.copy()
    edge = np.zeros((H, W), bool)
    for dy, dx in ((0, 1), (1, 0), (0, -1), (-1, 0)):
        g2 = np.roll(np.roll(gid, dy, 0), dx, 1); d2 = np.roll(np.roll(depth, dy, 0), dx, 1)
        e = (g2 != gid) & (depth <= d2 + 1e-6)
        if dy == 1: e[0, :] = False
        if dy == -1: e[-1, :] = False
        if dx == 1: e[:, 0] = False
        if dx == -1: e[:, -1] = False
        edge |= e
    out[edge] = out[edge] * 0.45
    rgba = np.concatenate([np.clip(out, 0, 255), np.full((H, W, 1), 255.0)], 2)
    if alpha is not None: rgba[..., 3] = alpha.reshape(H, W)
    return Image.fromarray(rgba.astype(np.uint8), 'RGBA')

if __name__ == '__main__':
    import sys
    im = render_car(sys.argv[2] if len(sys.argv) > 2 else 'day')
    im.resize((W * 3, H * 3), Image.NEAREST).save(sys.argv[1])
