"""
Riders of the "Going Down" elevator, rendered through the corner camera like the car (liftcam_car.py):
bodies are ellipsoids lit by the car's lamp and snapped to short colour ramps (banded, form-following shading),
each part outlined in a darker shade of its own colour; faces, hair strands and small details are projected
and drawn as crisp pixels. Output: full-frame RGBA images (252x174) with a transparent background.
"""
import math, os, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import liftcam_render as Rn
from liftcam_render import W, H, CW, CH, CD, Prim, seg, hit_prims, rot_y, rot_x, hexc

def mk(base, dark=0.42, light=1.22):
    """6-tone ramp around a base colour: shadows cooler, lights warmer (as in the game's sprites)."""
    b = hexc(base)
    out = []
    for f in np.linspace(dark, light, 6):
        c = b * f
        c = c + (np.array([-6, -3, 8]) * (1 - f) if f < 1 else np.array([6, 4, -4]) * (f - 1) * 2)
        out.append(np.clip(c, 0, 255))
    return np.array(out)

SKIN = np.array([hexc(x) for x in ('#5e4034', '#805f4f', '#ab7e68', '#c99a7c', '#e1b290', '#efc6a4')])
SKIN2 = np.array([hexc(x) for x in ('#3f2a20', '#5a3d2f', '#7a5440', '#97694f', '#b38063', '#c99577')])

# ------------------------------------------------------------------ who is who
P = {
    'pruitt': dict(h=1.55, skin=SKIN, hair='perm', hairc='#b7a0cc', top='#c9a04a', scarf='#d98c98', bottom='#5d6f8f', skirt=True, glasses='#3b3030', old=True),
    'haldane': dict(h=1.78, skin=SKIN, hair='bald', hairc='#5a3e2c', top='#3a4a62', tie='#c0463a', bottom='#2e3a4e', wide=1.08),
    'rafi': dict(h=1.74, skin=SKIN2, hair='cap', hairc='#2f2a26', capc='#c0463a', top='#8a6a3c', bottom='#4f6284'),
    'mila': dict(h=1.60, skin=SKIN, hair='bob', hairc='#2a2522', top='#3f8f88', bottom='#4f6284', backpack='#e2b63e', phones='#df6d5c', wide=0.92),
    'gus': dict(h=1.70, skin=SKIN2, hair='beanie', hairc='#b9b4ac', capc='#555452', top='#6d7a5a', overalls='#56663f', bottom='#56663f', mustache='#b9b4ac', old=True),
    'toby': dict(h=1.15, skin=SKIN, hair='dino', hairc='#6aa04a', top='#4b6aa0', bottom='#3a4a62', wide=0.9),
    'mom': dict(h=1.66, skin=SKIN, hair='ponytail', hairc='#6a4832', top='#c0463a', bottom='#2a2826'),
    'grey': dict(h=1.82, skin=SKIN, hair='fedora', hairc='#3a3634', capc='#7b7b7b', top='#555452', bottom='#3a3836', coat=True, noface=True),
    'tech': dict(h=1.76, skin=SKIN, hair='hardhat', hairc='#3a2a20', capc='#e2b63e', top='#4b6aa0', overalls='#3d5683', bottom='#3d5683'),
    'dev': dict(h=1.76, skin=SKIN2, hair='short', hairc='#1c1816', top='#c0463a', bottom='#4f6284'),
    'priya': dict(h=1.63, skin=SKIN2, hair='ponytail', hairc='#211c19', top='#e2b63e', bottom='#3a3836', tiec='#3f8f88', wide=0.94),
}

SLOTS = {'L': (0.30, 0.44), 'R': (0.80, 0.40), 'C': (0.58, 0.80)}
DOOR = (0.57, 1.30)
MID = {k: ((v[0] + DOOR[0]) / 2, (v[1] + DOOR[1]) / 2) for k, v in SLOTS.items()}

def yaw_to_cam(x, z):
    """Yaw that turns a person standing at (x, z) to look up at the camera."""
    return math.atan2(Rn.CAM[0] - x, Rn.CAM[2] - z)

# ------------------------------------------------------------------ body
class Body:
    def __init__(self, name, x, z, yaw=0.0, pose='stand', arms='down', talk=False, walk=0, sit=False, look_up=False):
        self.sp = P[name]; self.name = name
        self.x, self.z, self.yaw = x, z, yaw
        self.pose, self.arms, self.talk, self.walk, self.sit = pose, arms, talk, walk, sit
        self.look_up = look_up
        self.prims, self.mats, self.feat = [], [], []
        self.build()

    def wp(self, lx, ly, lz):
        """Body-local point (metres, scaled by height) -> world."""
        s = self.sp['h'] / 1.72
        p = rot_y(self.yaw) @ np.array([lx * s * self.sp.get('wide', 1.0), ly * s, lz * s])
        return np.array([self.x, 0, self.z]) + p

    def add(self, prim, ramp, off=0.0, kind=None):
        self.prims.append(prim); self.mats.append((ramp, off, kind))

    def ell(self, c, r, ramp, off=0.0, kind=None, M=None, gid=None):
        s = self.sp['h'] / 1.72; wd = self.sp.get('wide', 1.0)
        R_ = rot_y(self.yaw) if M is None else rot_y(self.yaw) @ M
        self.add(Prim('ell', self.wp(*c), np.array(r) * s * np.array([wd, 1, wd if kind != 'head' else 1])), ramp, off, kind)
        self.prims[-1].M = R_
        if gid is not None: self.prims[-1].gid = gid

    def limb(self, a, b, rad, ramp, off=0.0):
        s = self.sp['h'] / 1.72
        self.add(seg(self.wp(*a), self.wp(*b), rad * s), ramp, off)

    def build(self):
        sp = self.sp
        top, bot = mk(sp['top']), mk(sp['bottom'])
        skin = sp['skin']; hairc = mk(sp['hairc'])
        dy = -0.55 if self.sit else 0.0
        w = self.walk
        # legs + shoes (mostly hidden from the ceiling, but they anchor the figure)
        if not self.sit:
            for side in (-1, 1):
                st = w * side * 0.09
                self.limb((side * 0.085, 0.86, 0), (side * 0.09, 0.1, st), 0.068, bot)
                self.ell((side * 0.09, 0.04, st + 0.04), (0.05, 0.04, 0.12), mk('#2a2624'))
            if sp.get('skirt'): self.ell((0, 0.68, 0), (0.2, 0.26, 0.15), bot)
        else:
            for side in (-1, 1):
                self.limb((side * 0.1, 0.3, 0.05), (side * 0.12, 0.45, 0.36), 0.07, bot)
                self.limb((side * 0.12, 0.45, 0.36), (side * 0.12, 0.08, 0.5), 0.06, bot)
        # torso, hips, shoulders
        tl = 0.32 if sp.get('coat') else 0.27
        self.ell((0, 0.94 + dy, 0), (0.16, 0.13, 0.11), bot if not sp.get('coat') else top)
        self.ell((0, 1.20 + dy - (0.06 if sp.get('coat') else 0), 0), (0.185, tl, 0.12), top, kind='torso')
        tg = len(self.prims) - 1
        for side in (-1, 1): self.ell((side * 0.13, 1.37 + dy, 0), (0.09, 0.07, 0.095), top, kind='torso', gid=('grp', tg))
        if sp.get('backpack'):
            self.ell((0, 1.22 + dy, -0.15), (0.15, 0.18, 0.08), mk(sp['backpack']))
        if sp.get('scarf'): self.ell((0, 1.45 + dy, 0), (0.12, 0.05, 0.1), mk(sp['scarf']))
        # neck + head
        self.ell((0, 1.47 + dy, 0), (0.05, 0.07, 0.05), skin, -0.3)
        hp = (0, 1.60 + dy, 0.0)
        tilt = rot_x(-0.35) if self.look_up else np.eye(3)
        turn = rot_y(0.3) if (self.talk and not self.look_up) else np.eye(3)
        self.headM = turn @ tilt
        self.head_c = hp
        self.ell(hp, (0.086, 0.112, 0.1), skin, kind='head', M=self.headM)
        for side in (-1, 1):   # ears
            self.ell(self.hl((side * 0.084, -0.005, -0.005)), (0.016, 0.03, 0.022), skin, -0.2, M=self.headM)
        if not sp.get('noface'):
            self.ell(self.hl((0, -0.025, 0.098)), (0.016, 0.03, 0.022), skin, 0.15, M=self.headM)   # nose
        self.hair(hairc)
        self.arms_(top, skin)

    def hl(self, p):
        """Head-local offset -> body-local point (follows the head's turn and tilt)."""
        return tuple(np.array(self.head_c) + self.headM @ np.array(p))

    def hair(self, hc):
        sp = self.sp; st = sp['hair']; M = self.headM
        if st == 'perm':
            for a in range(0, 360, 40):
                for el, rr in ((0.55, 0.095), (0.15, 0.1)):
                    if el < 0.3 and 20 < a < 160 and False: continue
                    v = np.array([math.sin(math.radians(a)) * math.cos(el), math.sin(el), math.cos(math.radians(a)) * math.cos(el)])
                    if v[2] > 0.5 and el < 0.3: continue      # keep the face free
                    self.ell(self.hl(v * np.array([0.09, 0.11, 0.1]) + np.array([0, 0.02, -0.01])), (0.04, 0.038, 0.04), hc, 0.1, M=M)
            self.ell(self.hl((0, 0.07, -0.01)), (0.07, 0.05, 0.07), hc, 0.2, M=M)
        elif st == 'cap':
            self.ell(self.hl((0, 0.035, -0.005)), (0.093, 0.08, 0.104), mk(sp['capc']), 0.1, M=M)
            self.ell(self.hl((0, 0.035, 0.1)), (0.075, 0.012, 0.07), mk(sp['capc']), -0.6, M=M)
        elif st == 'beanie':
            self.ell(self.hl((0, 0.04, -0.005)), (0.094, 0.085, 0.104), mk(sp['capc']), 0.0, kind='knit', M=M)
        elif st == 'fedora':
            self.ell(self.hl((0, 0.06, 0)), (0.19, 0.014, 0.2), mk(sp['capc']), -0.4, M=M)
            self.ell(self.hl((0, 0.1, -0.005)), (0.09, 0.07, 0.1), mk(sp['capc']), 0.1, kind='hatband', M=M)
        elif st == 'hardhat':
            self.ell(self.hl((0, 0.05, 0.01)), (0.125, 0.012, 0.145), mk(sp['capc']), -0.4, M=M)
            self.ell(self.hl((0, 0.06, -0.005)), (0.1, 0.085, 0.112), mk(sp['capc']), 0.2, kind='ridge', M=M)
        elif st == 'dino':
            self.ell(self.hl((0, 0.01, -0.01)), (0.1, 0.125, 0.11), hc, 0.0, kind='hood', M=M)
            for i in range(4):
                a = 0.4 - i * 0.55
                v = np.array([0, math.cos(a) * 0.13, math.sin(a) * 0.12 - 0.01])
                self.ell(self.hl(tuple(v)), (0.012, 0.03, 0.025), mk('#e2b63e'), 0.2, M=M)
        elif st == 'ponytail':
            self.limb(self.hl((0, 0.02, -0.1)), self.hl((0, -0.13, -0.135)), 0.028, hc, 0.0)
            self.ell(self.hl((0, 0.025, -0.098)), (0.022, 0.02, 0.02), mk(sp.get('tiec', '#c0463a')), 0.2, M=M)
        if sp.get('phones'):
            ph = mk(sp['phones'])
            for side in (-1, 1): self.ell(self.hl((side * 0.093, 0.0, 0)), (0.022, 0.04, 0.035), ph, 0.0, M=M)
            for i in range(7):
                a = math.radians(-70 + i * 23.3)
                self.ell(self.hl((math.sin(a) * 0.098, math.cos(a) * 0.12, 0.0)), (0.012, 0.012, 0.012), mk('#2a2826'), 0.2, M=M)

    def arms_(self, top, skin):
        a = self.arms; dy = -0.55 if self.sit else 0.0
        def arm(side, el, hand):
            sh = (side * 0.2, 1.38 + dy, 0)
            self.limb(sh, el, 0.055, top); self.limb(el, hand, 0.047, top)
            self.ell(hand, (0.04, 0.05, 0.035), skin, 0.1)
        sw = self.walk * 0.12
        if self.sit:
            for side in (-1, 1): arm(side, (side * 0.22, 1.05 + dy, 0.15), (side * 0.14, 1.0 + dy + 0.0, 0.42))
            return
        for side in (-1, 1):
            if a == 'phone' and side == 1:
                arm(1, (0.22, 1.18, 0.06), (0.1, 1.55, 0.02))
                self.ell((0.095, 1.58, 0.0), (0.012, 0.06, 0.03), mk('#2a2826'), 0.0)
            elif a in ('up', 'upL', 'upR', 'wave') and ((a == 'up') or (a == 'upL' and side < 0) or (a in ('upR', 'wave') and side > 0)):
                arm(side, (side * 0.3, 1.62, 0.02), (side * 0.22, 1.9, 0.04))
            elif a in ('box', 'carry'):
                arm(side, (side * 0.22, 1.12, 0.12), (side * 0.17, 1.14, 0.3))
            elif a == 'mop' and side == 1:
                arm(1, (0.22, 1.12, 0.1), (0.12, 1.08, 0.3))
                self.limb((0.12, 1.5, 0.28), (0.3, 0.02, 0.5), 0.016, mk('#8a6a3c'))
            else:
                arm(side, (side * 0.22, 1.1, -sw * side), (side * 0.21, 0.84, -sw * side * 1.5))
        if a == 'box':
            self.add(Prim('box', self.wp(0, 1.15, 0.33), np.array([0.2, 0.15, 0.17]) * self.sp['h'] / 1.72, rot_y(self.yaw)), mk('#c39a62'), 0.0, 'parcel')

# ------------------------------------------------------------------ material functions
def flat(light):
    """The game's way: one flat colour per part and, at most, one narrow shadow tone on the side away
    from the lamp. Form is described by lines, not by shading."""
    return np.where(light < 0.50, 2, 3).astype(int)

def head_tone(body, lp, ln, light, ramp_skin):
    """Hair or skin on the head ellipsoid, by hair style, from the head-local point."""
    sp = body.sp; st = sp['hair']
    n = ln
    e = np.arcsin(np.clip(n[:, 1], -1, 1)); a = np.arctan2(n[:, 0], n[:, 2])
    aa = np.abs(a)
    if st in ('short', 'ponytail', 'cap', 'fedora', 'hardhat', 'beanie'): hair = (e > 0.42) | ((aa > 0.9) & (e > -0.05)) | ((aa > 2.0) & (e > -0.55))
    elif st == 'bob': hair = (e > 0.33) | ((aa > 0.75) & (e > -0.75))
    elif st == 'perm': hair = (e > 0.3) | ((aa > 1.1) & (e > -0.35))
    elif st == 'bald': hair = (aa > 1.25) & (e > -0.5) & (e < 0.2)
    elif st == 'dino': hair = np.zeros(len(e), bool)
    else: hair = e > 0.4
    hairc = mk(sp['hairc'])
    k = flat(light)
    col = ramp_skin[k + 1].copy()
    strands = (np.sin(a * 26 + e * 4) > 0.8) * -2
    kh = np.clip(k + strands, 0, 5)
    col[hair] = hairc[kh[hair]]
    if st == 'bald':   # a shiny crown
        shine = (e > 0.75) & (k >= 4)
        col[shine] = np.array([250, 228, 205])
    return col

def render(bodies, extra=None, shadow=True):
    """Renders a list of Body objects (and optional (Prim, ramp) extras) -> RGBA image (transparent bg)."""
    o, d = Rn.camera_rays(); o = o.reshape(-1, 3); d = d.reshape(-1, 3)
    prims, owner = [], []
    for bi, b in enumerate(bodies):
        for i, p in enumerate(b.prims):
            prims.append(p); owner.append((bi, i))
    t, idx, lp, ln, wn = hit_prims(o, d, prims)
    hit = np.isfinite(t)
    img = np.zeros((o.shape[0], 3)); gid = np.full(o.shape[0], -1); alpha = np.zeros(o.shape[0])
    p = o + d * np.where(hit, t, 0)[:, None]
    lamp = np.array([CW / 2, CH - 0.05, CD / 2])
    L = lamp - p; dist = np.linalg.norm(L, axis=1, keepdims=True) + 1e-9; L = L / dist
    light = 0.30 + 0.78 * np.clip((wn * L).sum(1), 0, 1) / (0.6 + 0.3 * dist[:, 0] ** 2)
    for k, (bi, pi) in enumerate(owner):
        m = hit & (idx == k)
        if not m.any(): continue
        body = bodies[bi]; ramp, off, kind = body.mats[pi]
        li = light[m] + off * 0.17
        if kind == 'head':
            img[m] = head_tone(body, lp[m], ln[m], li, ramp)
        else:
            tn = flat(li)
            if kind == 'knit': tn = np.clip(tn - (np.sin(np.arctan2(ln[m, 0], ln[m, 2]) * 30) > 0.3), 0, 5)
            if kind == 'hood':   # the dinosaur hood leaves a face opening
                e = np.arcsin(np.clip(ln[m, 1], -1, 1)); a = np.arctan2(ln[m, 0], ln[m, 2])
                face = (np.abs(a) < 0.75) & (e < 0.25) & (e > -0.75)
                col = ramp[tn].copy(); col[face] = body.sp['skin'][tn[face]]; img[m] = col
                gid[m] = bi * 100 + pi; alpha[m] = 255; continue
            col = ramp[tn].copy()
            if kind == 'torso':
                lx, ly, lz = lp[m, 0], lp[m, 1], lp[m, 2]
                sp = body.sp; s = sp['h'] / 1.72
                if sp.get('tie'):
                    shirt = (lz > 0) & (np.abs(lx) < 0.045 * s) & (ly > 0.1 * s)
                    col[shirt] = SKIN[5] * 0 + np.array([236, 232, 222]) * (0.75 + 0.05 * tn[shirt, None])
                    tie = (lz > 0) & (np.abs(lx) < 0.018 * s) & (ly > -0.15 * s) & (ly < 0.2 * s)
                    col[tie] = mk(sp['tie'])[tn[tie]]
                if sp.get('overalls'):
                    ov = mk(sp['overalls'])
                    bib = ((lz > 0) & (np.abs(lx) < 0.09 * s) & (ly < 0.12 * s)) | (ly < -0.12 * s)
                    straps = (np.abs(np.abs(lx) - 0.08 * s) < 0.018 * s)
                    col[bib | straps] = ov[tn[bib | straps]]
                if sp.get('backpack'):
                    strp = (lz < 0.03) & (np.abs(np.abs(lx) - 0.09 * s) < 0.02 * s) & (ly > 0)
                    col[strp] = mk('#9a7a20')[tn[strp]]
            if kind == 'hatband':
                band = (np.arcsin(np.clip(ln[m, 1], -1, 1)) < 0.35)
                col[band] = mk('#1e1c1a')[tn[band]]
            if kind == 'ridge':
                ridge = np.abs(ln[m, 0]) < 0.12
                col[ridge] = ramp[np.clip(tn[ridge] + 1, 0, 5)]
            if kind == 'parcel':
                tp = np.abs(lp[m, 0]) < 0.02
                col[tp] = np.array([226, 207, 138])
            img[m] = col
        g = body.prims[pi].gid
        gid[m] = bi * 100 + (g[1] if isinstance(g, tuple) else pi); alpha[m] = 255
    depth = np.where(hit, t, 1e9)
    # contact shadow on the floor
    if shadow:
        tf = np.where(d[:, 1] < 0, (0 - o[:, 1]) / np.where(d[:, 1] < 0, d[:, 1], -1), np.inf)
        pf = o + d * tf[:, None]
        for b in bodies:
            sh = (~hit) & (np.hypot((pf[:, 0] - b.x) / 0.24, (pf[:, 2] - b.z) / 0.2) < 1)
            img[sh] = 0; alpha[sh] = 80; gid[sh] = -2
    out = Rn.finish(img, np.where(alpha > 0, gid, -1), depth, alpha)
    arr = np.asarray(out).copy()
    # outlines against the transparent background
    a = arr[..., 3] == 255
    edge = a & ~(np.roll(a, 1, 0) & np.roll(a, -1, 0) & np.roll(a, 1, 1) & np.roll(a, -1, 1))
    arr[edge, :3] = (arr[edge, :3] * 0.6).astype(np.uint8)
    im = Image.fromarray(arr, 'RGBA')
    for b in bodies: features(im, b)
    return im

# ------------------------------------------------------------------ crisp 2D details: faces
def features(im, b):
    sp = b.sp
    if sp.get('noface'): return
    d = ImageDraw.Draw(im)
    s = sp['h'] / 1.72
    def W_(p): return np.array(b.wp(*b.hl(p))) if False else b.wp(*b.hl(p))
    hc = b.wp(*b.head_c)
    fwd = b.wp(*b.hl((0, 0, 0.1))) - hc; fwd /= np.linalg.norm(fwd)
    to_cam = Rn.CAM - hc; to_cam /= np.linalg.norm(to_cam)
    facing = (fwd * to_cam).sum()
    if facing < 0.15: return
    cx, cy = Rn.project(hc)
    ex_, ey_ = Rn.project(b.wp(*b.hl((0.1, 0, 0))))
    rpx = math.hypot(ex_ - cx, ey_ - cy)          # head radius on screen
    def pt(p): x, y = Rn.project(b.wp(*b.hl(p))); return round(x), round(y)
    blk = (20, 16, 14, 255); wht = (244, 240, 230, 255)
    hair = tuple(int(v) for v in mk(sp['hairc'])[1]) + (255,)
    skd = tuple(int(v) for v in sp['skin'][1]) + (255,)
    for side in (-1, 1):
        x, y = pt((side * 0.036, 0.008, 0.092))
        if rpx >= 9:
            d.rectangle((x - 2, y - 1, x + 1, y + 1), fill=blk)          # rim and heavy lid
            d.rectangle((x - 1, y, x, y), fill=wht)
            d.point((x - (0 if side > 0 else 1), y), fill=blk)            # pupil
            bx, by = pt((side * 0.038, 0.04, 0.09))
            d.line((bx - 2, by, bx + 1, by), fill=hair if sp['hair'] != 'bald' else skd)
        else:
            d.point((x, y), fill=blk)
        if sp.get('glasses') and rpx >= 9:
            d.rectangle((x - 3, y - 2, x + 2, y + 2), outline=tuple(int(v) for v in hexc(sp['glasses'])) + (255,))
    mx, my = pt((0, -0.06, 0.088))
    if b.talk: d.rectangle((mx - 1, my, mx + 1, my + 1), fill=(90, 40, 34, 255))
    else: d.line((mx - 1, my, mx + 1, my), fill=skd)
    if sp.get('mustache') and rpx >= 8:
        d.line((mx - 2, my - 1, mx + 2, my - 1), fill=tuple(int(v) for v in hexc(sp['mustache'])) + (255,))
    if sp.get('old') and rpx >= 10:
        fx, fy = pt((0, 0.06, 0.088)); d.line((fx - 2, fy, fx + 2, fy), fill=skd)

if __name__ == '__main__':
    import liftcam_car as Car
    out = sys.argv[1]
    bg = Car.draw_car('day')
    sc = []
    def comp(bodies):
        im = bg.copy(); im.alpha_composite(render(bodies)); return im
    yaw_back = 0.0
    sc.append(comp([Body('pruitt', *SLOTS['L']), Body('haldane', *SLOTS['R'], arms='phone')]))
    sc.append(comp([Body('mila', *SLOTS['C'], arms='up'), Body('rafi', *DOOR, yaw=math.pi, arms='box')]))
    sc.append(comp([Body('gus', *SLOTS['L'], yaw=yaw_to_cam(*SLOTS['L']), look_up=True), Body('grey', *SLOTS['R'])]))
    sc.append(comp([Body('haldane', *SLOTS['L'], yaw=yaw_to_cam(*SLOTS['L']), look_up=True, talk=True, arms='wave'), Body('toby', *SLOTS['C'], yaw=yaw_to_cam(*SLOTS['C']), look_up=True), Body('tech', *SLOTS['R'])]))
    sh = Image.new('RGBA', (W * 2 + 4, H * 2 + 4), (255, 255, 255, 255))
    for i, im in enumerate(sc): sh.paste(im, ((i % 2) * (W + 4), (i // 2) * (H + 4)))
    sh.resize((sh.width * 3, sh.height * 3), Image.NEAREST).save(out)
