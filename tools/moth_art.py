"""
Pixel art for the "Moth Screen" cage: a hacked desktop watched through the Primate Observation Club relay.
Everything is drawn here with Pillow at 1:1 scale (camera view 252x174), so the output is real pixel art.

    python moth_art.py <out_dir>

Writes one PNG per object (sprite sheets are a single row of equal cells) and returns the layout used by
build_moth.py (cell sizes, animation names -> frame indices).
"""
import math, os, random, sys
from PIL import Image, ImageDraw

W, H = 252, 174

# ------------------------------------------------------------------ palette (muted, warm, like the game's cages)
def hx(s, a=255):
    s = s.lstrip('#'); return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), a)

C = {k: hx(v) for k, v in dict(
    # dusk-blue wallpaper ramp + warm lamp ramp (the game's night rooms use these desaturated blues)
    bg0='#1e2230', bg1='#262c3c', bg2='#303849', bg3='#3d4658', bg4='#4f586a',
    lamp0='#fff1c4', lamp1='#f0d48a', lamp2='#d9a64e', lamp3='#a8742e', lamp4='#6e4a24',
    moth='#c9b892', mothD='#8f7d5c', mothL='#ead9b0', eye='#c8603e',
    # retro OS chrome: beige plastic with an olive title bar (like the game's NH greens)
    chrome0='#efe6cc', chrome1='#d6caa8', chrome2='#b3a684', chrome3='#857959', chrome4='#4f4634',
    title='#6b7a3e', titleL='#8d9c58', titleD='#4a5629', titleT='#f1ecd6', body='#22261f', bodyL='#2d3229',
    term='#b2cc72', termD='#6f8448', termB='#1b2016',
    red='#c45a45', redD='#87392b', yel='#ddb553', grn='#7fa456', blue='#56739e', blueD='#3c5274', blueL='#a9bcd6',
    paper='#ece3ca', paperD='#d4c8a8', paperDD='#a99d7e', ink='#3a3128', inkL='#6f6452', link='#4a6890',
    grey='#8d877a', lgrey='#c9c1ad', dgrey='#5c574d', white='#f8f2df', black='#2a211d',
    skin='#e6b98f', skinL='#f3d2ae', skinD='#c08c69', skinDD='#8e5e48', hair='#4a3427', hairL='#6e5038', hairD='#2e2019',
    hood='#58694c', hoodD='#3f4d37', hoodDD='#2c3627', hoodL='#728463',
    nhair='#c4613f', nhairL='#e08458', nhairD='#8a3f2a', nshirt='#e3c46e', nshirtD='#b89648',
    cork='#b88f60', corkD='#93704a', corkL='#cfa776', string='#b8402f',
    gold='#e3bf5e', screen='#a9cad6', out='#2a211d',
).items()}
T = (0, 0, 0, 0)

# ------------------------------------------------------------------ 3x5 pixel font (caps; lowercase drawn as caps)
FONT = {
 'A': '010101111101101', 'B': '110101110101110', 'C': '011100100100011', 'D': '110101101101110', 'E': '111100110100111',
 'F': '111100110100100', 'G': '011100101101011', 'H': '101101111101101', 'I': '111010010010111', 'J': '001001001101010',
 'K': '101101110101101', 'L': '100100100100111', 'M': '101111111101101', 'N': '110101101101101', 'O': '010101101101010',
 'P': '110101110100100', 'Q': '010101101110011', 'R': '110101110101101', 'S': '011100010001110', 'T': '111010010010010',
 'U': '101101101101111', 'V': '101101101101010', 'W': '101101111111101', 'X': '101101010101101', 'Y': '101101010010010',
 'Z': '111001010100111', '0': '010101111101010', '1': '010110010010111', '2': '110001010100111', '3': '110001010001110',
 '4': '101101111001001', '5': '111100110001110', '6': '011100111101111', '7': '111001010010010', '8': '111101111101111',
 '9': '111101111001110', '.': '000000000000010', ',': '000000000010100', ':': '000010000010000', ';': '000010000010100',
 '!': '010010010000010', '?': '110001010000010', '-': '000000111000000', '_': '000000000000111', '/': '001001010100100',
 '@': '010101111100011', "'": '010010000000000', '"': '101101000000000', '(': '010100100100010', ')': '010001001001010',
 '+': '000010111010000', '=': '000111000111000', '>': '100010001010100', '<': '001010100010001', '#': '101111101111101',
 '%': '101001010100101', '*': '000101010101000', '&': '010101010101011', '$': '011110010011110', '~': '000011110000000',
 '[': '110100100100110', ']': '011001001001011', '|': '010010010010010', ' ': '000000000000000', '^': '010101000000000',
}

def text(d, x, y, s, col, cap=None):
    """Draws s with the top-left of the first glyph at (x, y). Returns the x after the text."""
    for ch in s:
        g = FONT.get(ch.upper(), FONT['?'])
        for i, b in enumerate(g):
            if b == '1': d.point((x + i % 3, y + i // 3), fill=col)
        x += 4
    return x

def text_w(s): return len(s) * 4 - 1

def text_big(d, x, y, s, col):
    """2x scaled font for headlines."""
    for ch in s:
        g = FONT.get(ch.upper(), FONT['?'])
        for i, b in enumerate(g):
            if b == '1': d.rectangle((x + (i % 3) * 2, y + (i // 3) * 2, x + (i % 3) * 2 + 1, y + (i // 3) * 2 + 1), fill=col)
        x += 8
    return x

def scribble(d, x, y, w, col, seed=0, gap=True):
    """A line of 'unreadable' tiny text: little dashes of varying length."""
    r = random.Random(seed)
    cx = x
    while cx < x + w:
        L = r.randint(2, 7)
        L = min(L, x + w - cx)
        d.line((cx, y, cx + L - 1, y), fill=col)
        cx += L + (2 if gap else 1)

# ------------------------------------------------------------------ helpers
def new(w, h, col=T): return Image.new('RGBA', (w, h), col)

def outline(img, col, src_alpha=1):
    """Adds a 1px outline around opaque pixels (in place)."""
    w, h = img.size
    px = img.load()
    mask = [[px[x, y][3] >= src_alpha for x in range(w)] for y in range(h)]
    for y in range(h):
        for x in range(w):
            if mask[y][x]: continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and mask[ny][nx]:
                    px[x, y] = col; break
    return img

def ascii_sprite(rows, pal):
    h = len(rows); w = max(len(r) for r in rows)
    im = new(w, h); px = im.load()
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch in pal and pal[ch] is not None: px[x, y] = pal[ch]
    return im

def dither_v(d, box, c1, c2):
    """Vertical gradient with ordered (Bayer 4x4) dithering between two colours."""
    B = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]
    x0, y0, x1, y1 = box
    for y in range(y0, y1 + 1):
        t = (y - y0) / max(1, y1 - y0)
        for x in range(x0, x1 + 1):
            d.point((x, y), fill=c2 if t * 16 > B[y % 4][x % 4] + 0.5 else c1)

SHADOW = (20, 14, 12, 90)

def bevel(d, box, hi, lo):
    x0, y0, x1, y1 = box
    d.line((x0, y0, x1, y0), fill=hi); d.line((x0, y0, x0, y1), fill=hi)
    d.line((x0, y1, x1, y1), fill=lo); d.line((x1, y0, x1, y1), fill=lo)

def window(w, h, title, theme='dark', icon=None):
    """Retro OS window: warm dark outline, beige bevelled frame, olive striped title bar, sunken content
    area and a soft drop shadow (the sprite is 2px larger than w x h). Returns (image, draw, content box)."""
    im = new(w + 2, h + 2); d = ImageDraw.Draw(im)
    d.rectangle((2, 2, w + 1, h + 1), fill=SHADOW)
    d.rectangle((0, 0, w - 1, h - 1), fill=C['out'])
    d.rectangle((1, 1, w - 2, h - 2), fill=C['chrome1'])
    bevel(d, (1, 1, w - 2, h - 2), C['chrome0'], C['chrome3'])
    # title bar
    d.rectangle((2, 2, w - 3, 9), fill=C['title'])
    for y in (3, 5, 7): d.line((3, y, w - 4, y), fill=C['titleL'])
    d.line((2, 9, w - 3, 9), fill=C['titleD'])
    tw = text_w(title)
    tx = 6 if icon is None else (icon(d, 4, 3) or 13)
    d.rectangle((tx - 2, 2, tx + tw + 1, 8), fill=C['title'])
    text(d, tx, 3, title, C['titleT'])
    # close box (classic square) on the right
    d.rectangle((w - 10, 3, w - 5, 8), fill=C['title']); d.rectangle((w - 10, 3, w - 5, 8), outline=C['chrome0'])
    d.point((w - 8, 5), fill=C['chrome0']); d.point((w - 7, 6), fill=C['chrome0'])
    # sunken content area
    body = C['body'] if theme == 'dark' else C['paper']
    d.rectangle((3, 11, w - 4, h - 4), fill=body)
    bevel(d, (2, 10, w - 3, h - 3), C['chrome3'], C['chrome0'])
    return im, d, (3, 11, w - 4, h - 4)

def sheet(frames):
    w, h = frames[0].size
    out = new(w * len(frames), h)
    for i, f in enumerate(frames): out.paste(f, (i * w, 0))
    return out

def paste(dst, src, xy):
    dst.alpha_composite(src, xy)

# ------------------------------------------------------------------ small sprites
MOTH = [
    "..m.........m..",
    "...m.......m...",
    "mmm.m.....m.mmm",
    "MMMmmm.b.mmmMMM",
    "MLLMmmmbmmmMLLM",
    "MLeLMmmbmmMLeLM",
    ".MLLMmmbmmMLLM.",
    "..MMMmmbmmMMM..",
    "...MmMmbmMmM...",
    "....MM.b.MM....",
    ".......b.......",
]
MOTH2 = [  # wings up
    "..m.........m..",
    "MMMm.......mMMM",
    "MLLMm.....mMLLM",
    "MLeLMm.b.mMLeLM",
    ".MLLMmmbmmMLLM.",
    "..MMmmmbmmmMM..",
    "...mmm.b.mmm...",
    "....m..b..m....",
    ".......b.......",
    ".......b.......",
    "...............",
]
def moth_pal(scale_col=None):
    return {'m': C['moth'], 'M': C['mothD'], 'L': C['mothL'], 'e': C['eye'], 'b': C['hair'], '.': None}

def cursor_frames():
    arrow = ascii_sprite([
        "k........",
        "kk.......",
        "kwk......",
        "kwwk.....",
        "kwwwk....",
        "kwwwwk...",
        "kwwwwwk..",
        "kwwwwwwk.",
        "kwwwwkkkk",
        "kwkwwk...",
        "kk.kwwk..",
        "k...kwk..",
        ".....kk..",
    ], {'k': C['black'], 'w': C['white']})
    click = ascii_sprite([
        "k........",
        "kk.......",
        "kyk......",
        "kyyk.....",
        "kyyyk....",
        "kyyyyk...",
        "kyyyyyk..",
        "kyyyyyyk.",
        "kyyyykkkk",
        "kykyyk...",
        "kk.kyyk..",
        "k...kyk..",
        ".....kk..",
    ], {'k': C['black'], 'y': C['yel']})
    hour1 = ascii_sprite([
        "kkkkkkk..",
        "kwwwwwk..",
        ".kyyyk...",
        "..kyk....",
        "...k.....",
        "..kwk....",
        ".kwwwk...",
        "kwwwwwk..",
        "kkkkkkk..",
        ".........", ".........", ".........", ".........",
    ], {'k': C['black'], 'w': C['white'], 'y': C['yel']})
    hour2 = ascii_sprite([
        "kkkkkkk..",
        "kwwwwwk..",
        ".kwwwk...",
        "..kwk....",
        "...k.....",
        "..kyk....",
        ".kyyyk...",
        "kyyyyyk..",
        "kkkkkkk..",
        ".........", ".........", ".........", ".........",
    ], {'k': C['black'], 'w': C['white'], 'y': C['yel']})
    return [arrow, click, hour1, hour2]

def voice_frames():
    """Microphone level meter of the Club overlay. Speech bubbles are anchored on it."""
    out = []
    for lv in ([1, 1, 1, 1, 1, 1, 1, 1], [2, 4, 3, 6, 2, 5, 3, 1], [4, 6, 5, 3, 6, 2, 4, 3], [3, 2, 6, 4, 3, 6, 2, 5], [1, 2, 1, 1, 2, 1, 1, 1]):
        im = new(40, 11); d = ImageDraw.Draw(im)
        d.rounded_rectangle((0, 0, 39, 10), 3, fill=(10, 10, 12, 200))
        # mic glyph
        d.rectangle((3, 2, 5, 5), fill=C['lgrey']); d.line((2, 5, 2, 6), fill=C['grey']); d.line((6, 5, 6, 6), fill=C['grey'])
        d.line((3, 7, 5, 7), fill=C['grey']); d.point((4, 8), fill=C['grey'])
        for i, v in enumerate(lv):
            x = 10 + i * 3
            col = C['red'] if v >= 6 else (C['yel'] if v >= 4 else C['grn'])
            d.rectangle((x, 8 - v, x + 1, 8), fill=col)
        text(d, 35 - 8, 3, '', C['lgrey'])
        out.append(im)
    return out

# ------------------------------------------------------------------ portraits
def layer(w, h):
    im = new(w, h); return im, ImageDraw.Draw(im)

def stack(base, *layers, line=None):
    """Composite part layers onto base, each outlined with the warm dark line colour (game-style outlines)."""
    for L in layers:
        if line is not False: outline(L, line or C['out'])
        base.alpha_composite(L)
    return base

def face_elias(w, h, mood='neutral', glow=True, mask=False):
    """Webcam bust of Elias (m0th): olive hoodie, messy brown hair, round glasses, monitor glow on one side."""
    im, d = layer(w, h)
    # room behind: dim wall, moth poster, shelf with books, lit by the monitor
    dither_v(d, (0, 0, w - 1, h - 1), C['bg2'], C['bg1'])
    d.rectangle((3, 4, 18, 24), fill=C['out']); d.rectangle((4, 5, 17, 23), fill=C['redD']); d.rectangle((4, 5, 17, 6), fill=C['red'])
    m = ascii_sprite(MOTH, moth_pal()).resize((12, 9), Image.NEAREST); paste(im, m, (5, 10))
    d.rectangle((w - 23, 15, w - 2, 17), fill=C['out']); d.line((w - 22, 15, w - 3, 15), fill=C['corkD'])
    for i, c in enumerate(('blue', 'yel', 'redD', 'grn', 'chrome2')):
        d.rectangle((w - 22 + i * 4, 8 - (i % 2), w - 20 + i * 4, 14), fill=C[c]); d.line((w - 22 + i * 4, 8 - (i % 2), w - 22 + i * 4, 14), fill=C['out'])
    cx = w // 2
    # body (hoodie)
    body, bd = layer(w, h)
    bd.ellipse((cx - 27, h - 23, cx + 27, h + 24), fill=C['hood'])
    bd.ellipse((cx - 27, h - 23, cx - 5, h + 24), fill=C['hoodL'])
    bd.ellipse((cx + 8, h - 20, cx + 27, h + 24), fill=C['hoodD'])
    bd.polygon([(cx - 9, h - 21), (cx, h - 9), (cx + 9, h - 21)], fill=C['hoodDD'])
    hoodb, hbd = layer(w, h)
    hbd.ellipse((cx - 17, 8, cx + 17, h - 11), fill=C['hoodD'])
    hbd.ellipse((cx + 4, 10, cx + 17, h - 13), fill=C['hoodDD'])
    stack(im, hoodb, body)
    # strings
    d2 = ImageDraw.Draw(im)
    d2.line((cx - 3, h - 13, cx - 4, h - 4), fill=C['chrome1']); d2.line((cx + 3, h - 13, cx + 4, h - 4), fill=C['chrome1'])
    d2.point((cx - 4, h - 3), fill=C['chrome2']); d2.point((cx + 4, h - 3), fill=C['chrome2'])
    # head
    head, hd = layer(w, h)
    hd.rectangle((cx - 4, h - 25, cx + 4, h - 17), fill=C['skinD'])
    hd.ellipse((cx - 11, 12, cx + 11, h - 19), fill=C['skin'])
    hd.ellipse((cx + 2, 13, cx + 11, h - 20), fill=C['skinD'])
    hd.ellipse((cx - 9, 16, cx - 3, 26), fill=C['skinL'])
    hd.ellipse((cx - 13, 24, cx - 9, 31), fill=C['skin']); hd.ellipse((cx + 9, 24, cx + 13, 31), fill=C['skinD'])  # ears
    hair, rd = layer(w, h)
    rd.ellipse((cx - 13, 6, cx + 13, 24), fill=C['hair'])
    for i in range(-12, 13, 3):
        rd.polygon([(cx + i, 17), (cx + i + 3, 17), (cx + i + 1, 23 + (i % 2))], fill=C['hair'])
    rd.chord((cx - 13, 6, cx + 13, 24), -60, 40, fill=C['hairD'])
    rd.ellipse((cx - 11, 7, cx + 10, 22), fill=C['hair'])
    for p in ((cx - 7, 9), (cx - 6, 9), (cx - 5, 10), (cx - 2, 9), (cx - 1, 10), (cx - 9, 12)):
        rd.point(p, fill=C['hairL'])
    stack(im, head, hair)
    d = ImageDraw.Draw(im)
    ey = 28
    if mask:
        mm = ascii_sprite(MOTH, moth_pal()).resize((30, 22), Image.NEAREST)
        outline(mm, C['out']); paste(im, mm, (cx - 15, ey - 11))
        d.line((cx - 15, ey + 2, cx - 20, ey + 6), fill=C['paperD'])  # string of the paper mask
        return im
    # brows
    if mood == 'angry':
        d.line((cx - 9, ey - 6, cx - 3, ey - 4), fill=C['hairD']); d.line((cx + 2, ey - 4, cx + 8, ey - 6), fill=C['hairD'])
    elif mood == 'scared':
        d.line((cx - 9, ey - 5, cx - 3, ey - 7), fill=C['hairD']); d.line((cx + 2, ey - 7, cx + 8, ey - 5), fill=C['hairD'])
    else:
        d.line((cx - 9, ey - 6, cx - 3, ey - 6), fill=C['hairD']); d.line((cx + 2, ey - 6, cx + 8, ey - 6), fill=C['hairD'])
    # glasses (lenses catch the screen)
    for gx in (cx - 6, cx + 5):
        d.ellipse((gx - 4, ey - 3, gx + 4, ey + 3), fill=(169, 202, 214, 90), outline=C['out'])
        d.point((gx - 2, ey - 2), fill=C['white']); d.point((gx - 1, ey - 2), fill=C['white'])
        d.point((gx, ey), fill=C['out']); d.point((gx + 1, ey), fill=C['out'])
    d.line((cx - 2, ey - 1, cx + 1, ey - 1), fill=C['out'])
    if mood == 'scared':
        d.point((cx - 6, ey - 1), fill=C['white']); d.point((cx + 5, ey - 1), fill=C['white'])
    # nose + mouth
    d.line((cx + 1, ey + 3, cx + 1, ey + 5), fill=C['skinDD']); d.point((cx, ey + 6), fill=C['skinDD'])
    my = ey + 10
    if mood == 'talk':
        d.ellipse((cx - 3, my - 2, cx + 3, my + 2), fill=C['out']); d.line((cx - 1, my + 1, cx + 1, my + 1), fill=C['redD'])
    elif mood == 'angry':
        d.rectangle((cx - 4, my - 1, cx + 4, my + 1), fill=C['out']); d.line((cx - 3, my, cx + 3, my), fill=C['white'])
    elif mood == 'scared':
        d.ellipse((cx - 2, my - 2, cx + 2, my + 3), fill=C['out'])
    else:
        d.line((cx - 3, my, cx + 2, my), fill=C['skinDD']); d.point((cx + 3, my - 1), fill=C['skinDD'])
    # cold monitor light on the left cheek (dithered)
    if glow:
        for y in range(14, h - 20):
            for x in range(cx - 11, cx - 5):
                p = im.getpixel((x, y))
                if p[:3] in (C['skin'][:3], C['skinL'][:3]) and (x + y) % 2 == 0: im.putpixel((x, y), hx('#c9c3c4'))
    return im

def face_nora(w, h, bg='blueL'):
    """Avatar of Nora Vance: copper bob, freckles, mustard top, outlined like the game's characters."""
    im, d = layer(w, h)
    d.rectangle((0, 0, w - 1, h - 1), fill=C[bg])
    cx = w // 2
    body, bd = layer(w, h)
    bd.ellipse((1, h - h // 3, w - 2, h + h // 3), fill=C['nshirt']); bd.ellipse((cx + 2, h - h // 3 + 2, w - 2, h + h // 3), fill=C['nshirtD'])
    hairb, hb = layer(w, h)
    hb.ellipse((cx - w // 3 - 1, h // 6 - 1, cx + w // 3 + 1, h * 3 // 4), fill=C['nhair'])
    hb.ellipse((cx + 1, h // 6, cx + w // 3 + 1, h * 3 // 4), fill=C['nhairD'])
    stack(im, hairb, body)
    head, hd = layer(w, h)
    hd.rectangle((cx - 1, h * 3 // 5, cx + 1, h * 3 // 4), fill=C['skinD'])
    hd.ellipse((cx - w // 4, h // 4, cx + w // 4, h * 2 // 3), fill=C['skin'])
    hd.ellipse((cx + 1, h // 4 + 1, cx + w // 4, h * 2 // 3), fill=C['skinD'])
    stack(im, head)
    d = ImageDraw.Draw(im)
    d.rectangle((cx - w // 4 - 1, h // 4 - 1, cx + w // 4, h // 4 + 1), fill=C['nhair']); d.point((cx - 2, h // 4 + 2), fill=C['nhair'])
    d.line((cx - w // 4 + 1, h // 4 - 1, cx, h // 4 - 1), fill=C['nhairL'])
    ey = h // 4 + h // 8 + 1
    d.point((cx - 2, ey), fill=C['out']); d.point((cx + 2, ey), fill=C['out'])
    d.line((cx - 1, ey + 3, cx + 1, ey + 3), fill=C['redD'])
    d.point((cx - 3, ey + 2), fill=C['nhairD']); d.point((cx + 3, ey + 2), fill=C['nhairD']); d.point((cx - 2, ey + 2), fill=C['skinD'])
    return im

def host_frame(w, h, talk):
    """Tutorial host: black balaclava, sunglasses, laptop covered in stickers, very serious."""
    im, d = layer(w, h)
    dither_v(d, (0, 0, w - 1, h - 1), hx('#3d4658'), hx('#262c3c'))
    for x in range(4, w, 10): d.rectangle((x, 6, x + 5, 12), fill=hx('#4a5468'))  # foam panels
    cx = w // 2
    body, bd = layer(w, h)
    bd.ellipse((cx - 21, h - 15, cx + 21, h + 20), fill=hx('#2e2a28')); bd.ellipse((cx + 4, h - 13, cx + 21, h + 20), fill=hx('#211e1c'))
    head, hd = layer(w, h)
    hd.ellipse((cx - 11, 4, cx + 11, h - 10), fill=hx('#2e2a28')); hd.ellipse((cx + 2, 5, cx + 11, h - 11), fill=hx('#211e1c'))
    stack(im, body, head)
    d = ImageDraw.Draw(im)
    d.rectangle((cx - 9, 12, cx + 9, 18), fill=C['skin']); d.line((cx - 9, 18, cx + 9, 18), fill=C['skinD'])
    d.rectangle((cx - 8, 13, cx - 2, 16), fill=C['out']); d.rectangle((cx + 2, 13, cx + 8, 16), fill=C['out'])
    d.line((cx - 7, 13, cx - 4, 13), fill=C['grey']); d.line((cx + 3, 13, cx + 6, 13), fill=C['grey'])
    if talk:
        d.ellipse((cx - 3, 22, cx + 3, 27), fill=C['skinDD']); d.line((cx - 2, 25, cx + 2, 25), fill=C['redD'])
    else:
        d.rectangle((cx - 3, 24, cx + 3, 25), fill=C['skinDD'])
    lap, ld = layer(w, h)
    ld.rectangle((cx - 17, h - 11, cx + 17, h - 1), fill=C['chrome2']); ld.line((cx - 17, h - 11, cx + 17, h - 11), fill=C['chrome0'])
    stack(im, lap)
    d.rectangle((cx - 13, h - 8, cx - 9, h - 5), fill=C['red']); d.rectangle((cx + 6, h - 8, cx + 10, h - 4), fill=C['yel']); d.ellipse((cx - 3, h - 8, cx + 1, h - 4), fill=C['grn'])
    return im

def face_dorian(w, h):
    """Grainy grey news photo of Dorian Pell: square jaw, beard, cap."""
    im = new(w, h); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, w - 1, h - 1), fill=hx('#7a7a7a'))
    cx = w // 2
    g1, g2, g3, g4 = hx('#3d3d3d'), hx('#a8a8a8'), hx('#8d8d8d'), hx('#5a5a5a')
    d.ellipse((cx - w // 2, h - h // 3, cx + w // 2, h + h // 2), fill=g1)
    d.rectangle((cx - w // 4, h // 4, cx + w // 4, h * 2 // 3), fill=g2)
    d.rectangle((cx - w // 4, h // 2, cx + w // 4, h * 2 // 3 + 2), fill=g4)  # beard
    d.rectangle((cx - w // 4 - 2, h // 6, cx + w // 4 + 2, h // 4 + 1), fill=g1)  # cap
    d.rectangle((cx - w // 4 - 2, h // 4, cx + w // 4 + 5, h // 4 + 1), fill=g1)
    ey = h // 4 + 4
    d.line((cx - 4, ey, cx - 2, ey), fill=g1); d.line((cx + 2, ey, cx + 4, ey), fill=g1)
    d.line((cx - 2, h // 2 + 2, cx + 2, h // 2 + 2), fill=g1)
    r = random.Random(7)
    for _ in range(w * h // 6):
        x, y = r.randrange(w), r.randrange(h)
        p = im.getpixel((x, y)); v = r.choice((-14, 14))
        im.putpixel((x, y), (max(0, min(255, p[0] + v)),) * 3 + (255,))
    return im

# ------------------------------------------------------------------ wallpaper / desktop
def icon_trash(d, x, y):
    d.rectangle((x + 2, y + 1, x + 9, y + 2), fill=C['lgrey']); d.rectangle((x + 4, y, x + 7, y), fill=C['lgrey'])
    d.rectangle((x + 3, y + 3, x + 8, y + 11), fill=C['grey'])
    for i in (4, 6, 8): d.line((x + i - 0, y + 4, x + i - 0, y + 10), fill=C['dgrey'])

def icon_folder(d, x, y, col='yel'):
    d.rectangle((x + 1, y + 1, x + 5, y + 2), fill=C[col])
    d.rectangle((x + 1, y + 2, x + 10, y + 10), fill=C[col])
    d.rectangle((x + 1, y + 4, x + 10, y + 10), fill=hx('#c89c36') if col == 'yel' else C['redD'])

def icon_txt(d, x, y):
    d.rectangle((x + 2, y, x + 9, y + 11), fill=C['paper'])
    d.polygon([(x + 7, y), (x + 9, y + 2), (x + 7, y + 2)], fill=C['paperDD'])
    for i in range(3, 10, 2): d.line((x + 3, y + i, x + 7, y + i), fill=C['inkL'])

def icon_exe(d, x, y):
    d.rectangle((x + 1, y + 1, x + 10, y + 10), fill=C['bg4'])
    m = ascii_sprite(MOTH, moth_pal()).resize((8, 6), Image.NEAREST)
    d._image.alpha_composite(m, (x + 2, y + 3))

def bayer(x, y): return [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]][y % 4][x % 4]

def wallpaper():
    """Desktop wallpaper painted like one of the game's night scenes: a desk lamp in a dark room,
    a cone of warm light with moths circling it, a window with the city at night."""
    im, d = layer(W, H)
    dither_v(d, (0, 0, W - 1, H - 12), C['bg1'], C['bg2'])
    # window at night (right)
    d.rectangle((168, 12, 238, 80), fill=C['out'])
    dither_v(d, (170, 14, 236, 78), hx('#1b2033'), hx('#2b3550'))
    r = random.Random(4)
    for i in range(9):
        bx = 170 + i * 8; bh = r.randint(14, 34)
        d.rectangle((bx, 78 - bh, bx + 6, 78), fill=hx('#151a28'))
        for _ in range(3):
            wx, wy = bx + r.randint(1, 5), 78 - r.randint(2, bh - 2)
            d.point((wx, wy), fill=C['lamp2'] if r.random() < .7 else C['lamp1'])
    d.line((203, 14, 203, 78), fill=C['out']); d.line((170, 46, 236, 46), fill=C['out'])
    d.rectangle((166, 80, 240, 83), fill=C['chrome3']); d.line((166, 80, 240, 80), fill=C['chrome2'])
    d.ellipse((222, 20, 230, 28), fill=C['lamp0'])
    # desk surface
    d.rectangle((0, 128, W - 1, H - 12), fill=hx('#3a2c22'))
    d.line((0, 128, W - 1, 128), fill=hx('#5a4433')); d.line((0, 129, W - 1, 129), fill=hx('#4a372a'))
    # cone of light (dithered warm wash)
    lx, ly = 120, 46
    for y in range(ly, H - 12):
        span = (y - ly) * 0.75 + 4
        for x in range(int(lx - span), int(lx + span)):
            if not 0 <= x < W: continue
            t = 1 - abs(x - lx) / span
            k = t * (1 - (y - ly) / 150) * 16
            if k > bayer(x, y) + 3:
                p = im.getpixel((x, y))
                col = C['lamp3'] if y >= 128 else C['bg4']
                if k > bayer(x, y) + 9: col = C['lamp2'] if y >= 128 else hx('#6a6a6a')
                im.putpixel((x, y), col)
    # lamp: arm + shade + bulb
    lampL, ld = layer(W, H)
    ld.line((150, 126, 140, 90), fill=C['chrome3'], width=3); ld.line((140, 90, 126, 40), fill=C['chrome3'], width=3)
    ld.ellipse((140, 122, 164, 130), fill=C['chrome3'])
    ld.polygon([(104, 46), (136, 46), (128, 30), (112, 30)], fill=C['title']); ld.polygon([(122, 46), (136, 46), (128, 30), (122, 30)], fill=C['titleD'])
    stack(im, lampL)
    d = ImageDraw.Draw(im)
    d.ellipse((114, 43, 126, 50), fill=C['lamp0']); d.line((112, 31, 127, 31), fill=C['titleL'])
    # glow halo around the bulb
    for rr in range(22, 6, -1):
        for a in range(0, 360, 3):
            x = int(120 + rr * math.cos(math.radians(a))); y = int(50 + rr * 0.6 * math.sin(math.radians(a)))
            if 0 <= x < W and 0 <= y < 128 and y > 46 and (22 - rr) * 0.9 > bayer(x, y):
                d.point((x, y), fill=C['lamp1'] if rr < 12 else C['lamp2'])
    # moths around the light
    m1 = ascii_sprite(MOTH, moth_pal()); m2 = ascii_sprite(MOTH2, moth_pal())
    for (mx, my, sp) in ((92, 58, m1), (140, 66, m2), (106, 82, m1), (132, 92, m2)):
        s = sp.copy(); outline(s, C['out']); paste(im, s, (mx, my))
    big = ascii_sprite(MOTH, moth_pal()).resize((30, 22), Image.NEAREST); outline(big, C['out']); paste(im, big, (60, 96))
    # props on the desk: energy drink cans, a mug
    for (cx_, col) in ((196, C['grn']), (206, C['red'])):
        d.rectangle((cx_ - 1, 112, cx_ + 6, 128), fill=C['out']); d.rectangle((cx_, 113, cx_ + 5, 127), fill=col); d.line((cx_ + 1, 113, cx_ + 1, 127), fill=C['white'])
    d.rectangle((220, 116, 232, 128), fill=C['out']); d.rectangle((221, 117, 231, 127), fill=C['chrome1']); d.line((231, 119, 234, 122), fill=C['out'])
    s = 'THE LIGHT FINDS YOU'
    text(d, 120 - text_w(s) // 2, 136, s, C['mothD'])
    # desktop icons (left column), labels in a dark plate like the game's captions
    icons = [(icon_trash, 'TRASH'), (lambda d, x, y: icon_folder(d, x, y), 'TOOLS'), (icon_txt, 'TARGET'), (icon_exe, 'M0TH'),
             (lambda d, x, y: icon_folder(d, x, y, 'red'), 'DONT')]
    for i, (fn, label) in enumerate(icons):
        y = 8 + i * 26
        fn(d, 10, y)
        lw = text_w(label)
        d.rectangle((16 - lw // 2 - 2, y + 13, 16 - lw // 2 + lw + 1, y + 19), fill=(30, 24, 20, 150))
        text(d, 16 - lw // 2, y + 14, label, C['white'])
    # taskbar: dark plastic strip. The game writes its white camera messages ("RECORDING", "OVERWRITING",
    # "BUFFER FULL") at the bottom-left of the view, so this strip must stay dark for them to be readable.
    TB, TBL, TBD = hx('#2b2620'), hx('#463f34'), hx('#1a1714')
    d.rectangle((0, H - 11, W - 1, H - 1), fill=TB)
    d.line((0, H - 11, W - 1, H - 11), fill=C['out']); d.line((0, H - 10, W - 1, H - 10), fill=TBL)
    d.rectangle((2, H - 9, 17, H - 2), fill=TBL); bevel(d, (2, H - 9, 17, H - 2), hx('#5c5344'), TBD)
    m = ascii_sprite(MOTH, moth_pal()).resize((11, 7), Image.NEAREST); paste(im, m, (4, H - 8))
    for i, c in enumerate(('blue', 'term', 'red', 'yel')):
        x = 22 + i * 12
        d.rectangle((x, H - 9, x + 9, H - 2), fill=TBL); bevel(d, (x, H - 9, x + 9, H - 2), hx('#5c5344'), TBD)
        d.rectangle((x + 3, H - 7, x + 6, H - 4), fill=C[c] if c != 'term' else C['term'])
    d.rectangle((W - 58, H - 9, W - 2, H - 2), fill=TBD); bevel(d, (W - 58, H - 9, W - 2, H - 2), TBD, TBL)
    for i in range(3): d.line((W - 55 + i * 2, H - 4, W - 55 + i * 2, H - 4 - i * 2), fill=C['lgrey'])
    d.rectangle((W - 47, H - 7, W - 46, H - 5), fill=C['lgrey']); d.polygon([(W - 46, H - 7), (W - 43, H - 9), (W - 43, H - 3), (W - 46, H - 5)], fill=C['lgrey'])
    return im

def club_overlay():
    """On top of everything: the Club feed marks plus a CRT-glass look (vignette, faint scanlines, glare),
    so the flat desktop reads like a monitor seen through the game's cameras."""
    im, d = layer(W, H)
    px = im.load()
    for y in range(H):
        for x in range(W):
            dx, dy = (x - W / 2) / (W / 2), (y - H / 2) / (H / 2)
            v = (dx * dx + dy * dy)
            a = 0
            if v > 0.55: a = int(min(1, (v - 0.55) / 0.9) * 120)
            if y % 2 == 1: a = max(a, 16)
            if a: px[x, y] = (20, 16, 18, a)
    # glare streak (top-left, diagonal)
    for i in range(0, 60):
        for t in range(3):
            x, y = 14 + i + t, 4 + i // 2
            if 0 <= x < W and 0 <= y < H and bayer(x, y) < 6: px[x, y] = (255, 250, 235, 26)
    col = (235, 225, 195, 170)
    for (x, y, sx, sy) in ((3, 3, 1, 1), (W - 4, 3, -1, 1), (3, H - 15, 1, -1), (W - 4, H - 15, -1, -1)):
        d.line((x, y, x + 8 * sx, y), fill=col); d.line((x, y, x, y + 6 * sy), fill=col)
    d.rectangle((W - 74, 5, W - 7, 13), fill=(30, 24, 20, 170))
    d.ellipse((W - 72, 7, W - 68, 11), fill=C['red'])
    text(d, W - 65, 7, 'POC RELAY 07', (235, 225, 195, 220))
    return im

# ------------------------------------------------------------------ windows
BW, BH = 164, 112   # browser

def browser_base(url, title='WEB'):
    im, d, (x0, y0, x1, y1) = window(BW, BH, title, theme='light')
    d.rectangle((x0, y0, x1, y0 + 8), fill=C['lgrey'])
    d.rectangle((x0 + 2, y0 + 1, x0 + 4, y0 + 6), fill=C['grey']); d.rectangle((x0 + 6, y0 + 1, x0 + 8, y0 + 6), fill=C['grey'])
    d.rectangle((x0 + 11, y0 + 1, x1 - 2, y0 + 7), fill=C['white'])
    text(d, x0 + 13, y0 + 2, url[:35], C['inkL'])
    return im, d, (x0, y0 + 10, x1, y1)

def post_box(d, x, y, w, h, kind, seed):
    d.rectangle((x, y, x + w, y + h), fill=C['white']); d.rectangle((x, y, x + w, y + h), outline=C['paperD'])
    # thumbnail
    tx, ty = x + 2, y + 2
    th = h - 4
    if kind == 'cat':
        d.rectangle((tx, ty, tx + th, ty + th), fill=hx('#d7c8a8'))
        d.ellipse((tx + 3, ty + 6, tx + th - 2, ty + th - 1), fill=hx('#e39a52'))
        d.polygon([(tx + 4, ty + 7), (tx + 5, ty + 3), (tx + 7, ty + 6)], fill=hx('#e39a52'))
        d.polygon([(tx + th - 6, ty + 6), (tx + th - 4, ty + 3), (tx + th - 3, ty + 7)], fill=hx('#e39a52'))
        d.point((tx + 6, ty + 9), fill=C['ink']); d.point((tx + th - 5, ty + 9), fill=C['ink'])
    elif kind == 'bakery':
        d.rectangle((tx, ty, tx + th, ty + th), fill=hx('#f0d9b5'))
        d.rectangle((tx, ty, tx + th, ty + 3), fill=hx('#c0607a'))
        for i in range(0, th, 4): d.rectangle((tx + i, ty + 3, tx + i + 1, ty + 5), fill=C['white'])
        d.rectangle((tx + 3, ty + 8, tx + th - 3, ty + th - 1), fill=C['screen'])
        d.ellipse((tx + 5, ty + 10, tx + 9, ty + 13), fill=hx('#c9893e'))
    elif kind == 'bike':
        d.rectangle((tx, ty, tx + th, ty + th), fill=hx('#bcd3b0'))
        d.ellipse((tx + 1, ty + th - 7, tx + 6, ty + th - 2), outline=C['ink']); d.ellipse((tx + th - 6, ty + th - 7, tx + th - 1, ty + th - 2), outline=C['ink'])
        d.line((tx + 3, ty + th - 4, tx + 7, ty + th - 9, tx + th - 3, ty + th - 4), fill=C['blue'])
        d.line((tx + 7, ty + th - 9, tx + 9, ty + th - 4), fill=C['blue'])
    elif kind == 'window':
        d.rectangle((tx, ty, tx + th, ty + th), fill=hx('#8fa3b5'))
        d.rectangle((tx + 2, ty + 2, tx + th - 2, ty + th - 2), fill=hx('#b9cbd8'))
        d.rectangle((tx + 4, ty + 4, tx + 10, ty + 6), fill=hx('#2f6a3a'))
        d.ellipse((tx + th - 8, ty + th - 8, tx + th - 3, ty + th - 3), fill=C['white'])
    scribble(d, tx + th + 3, y + 3, w - th - 7, C['inkL'], seed)
    scribble(d, tx + th + 3, y + 6, w - th - 14, C['paperDD'], seed + 1)
    d.point((x + w - 4, y + h - 3), fill=C['red']); d.point((x + w - 5, y + h - 3), fill=C['red'])

def b_meta():
    im, d, (x0, y0, x1, y1) = browser_base('METAYOU.COM/NORA.VANCE', 'METAYOU')
    d.rectangle((x0, y0, x1, y0 + 9), fill=C['blue'])
    text(d, x0 + 3, y0 + 3, 'METAYOU', C['white'])
    av = face_nora(24, 24); paste(im, av, (x0 + 4, y0 + 12))
    d.rectangle((x0 + 4, y0 + 12, x0 + 27, y0 + 35), outline=C['white'])
    text(d, x0 + 32, y0 + 14, 'NORA VANCE', C['ink'])
    text(d, x0 + 32, y0 + 21, 'BAKER. ARTIST.', C['inkL'])
    text(d, x0 + 32, y0 + 27, 'CAT MOM', C['inkL'])
    d.rectangle((x1 - 30, y0 + 14, x1 - 4, y0 + 20), fill=C['blue']); text(d, x1 - 28, y0 + 15, 'FOLLOW', C['white'])
    post_box(d, x0 + 3, y0 + 38, x1 - x0 - 7, 18, 'cat', 1)
    post_box(d, x0 + 3, y0 + 58, x1 - x0 - 7, 18, 'bakery', 3)
    post_box(d, x0 + 3, y0 + 78, x1 - x0 - 7, 10, 'bike', 5)
    return im

def b_photo(mark=False):
    im, d, (x0, y0, x1, y1) = browser_base('METAYOU.COM/PHOTO/8812', 'METAYOU')
    d.rectangle((x0, y0, x1, y1), fill=C['black'])
    # photo: cafe window, morning, with a reflected street sign
    px0, py0, px1, py1 = x0 + 14, y0 + 4, x1 - 14, y1 - 4
    dither_v(d, (px0, py0, px1, py1), hx('#9fb7c9'), hx('#6d8396'))
    d.rectangle((px0, py1 - 22, px1, py1), fill=hx('#5b4636'))       # table
    d.rectangle((px0 + 20, py1 - 34, px0 + 32, py1 - 22), fill=C['white']); d.rectangle((px0 + 32, py1 - 31, px0 + 35, py1 - 26), fill=C['white'])
    d.rectangle((px0 + 22, py1 - 33, px0 + 30, py1 - 31), fill=hx('#7a4e2e'))
    d.ellipse((px0 + 50, py1 - 30, px0 + 70, py1 - 22), fill=hx('#d79a4e'))  # croissant
    d.line((px0 + 54, py1 - 29, px0 + 56, py1 - 23), fill=hx('#a66a2a')); d.line((px0 + 60, py1 - 30, px0 + 61, py1 - 22), fill=hx('#a66a2a'))
    # reflection: mirrored green street sign "KESTREL LN"
    sx, sy = px1 - 50, py0 + 12
    photo = override('browser', 'kestrel_photo', (px1 - px0 + 1, py1 - py0 + 1))
    if photo is not None:   # generated photo (the sign must sit where the red circle is drawn, see the art brief)
        im.alpha_composite(photo, (px0, py0))
        if mark:
            d.ellipse((sx - 6, sy - 6, sx + 47, sy + 15), outline=C['red']); d.ellipse((sx - 5, sy - 5, sx + 46, sy + 14), outline=C['red'])
        return im
    sign = new(42, 9); sd = ImageDraw.Draw(sign)
    sd.rectangle((0, 0, 41, 8), fill=(47, 106, 58, 150)); text(sd, 2, 2, 'KESTREL LN', (240, 240, 230, 150))
    sign = sign.transpose(Image.FLIP_LEFT_RIGHT)
    paste(im, sign, (sx, sy)); d.line((sx + 20, sy + 9, sx + 20, sy + 30), fill=(60, 60, 60, 120))
    if mark:
        d.ellipse((sx - 6, sy - 6, sx + 47, sy + 15), outline=C['red'])
        d.ellipse((sx - 5, sy - 5, sx + 46, sy + 14), outline=C['red'])
    return im

def street_map(d, box, pin=None, pinlabel=None, city=False, seed=3):
    x0, y0, x1, y1 = box
    d.rectangle(box, fill=hx('#e6e0cc'))
    r = random.Random(seed)
    for _ in range(9):
        bx, by = r.randint(x0, x1 - 18), r.randint(y0, y1 - 12)
        d.rectangle((bx, by, bx + r.randint(8, 18), by + r.randint(6, 12)), fill=hx('#d4ccb2'))
    d.rectangle((x0 + 5, y0 + 30, x0 + 30, y0 + 50), fill=hx('#b7d1a0'))  # park
    d.line((x0, y0 + 22, x1, y0 + 28), fill=C['white'], width=3)
    d.line((x0 + 60, y0, x0 + 52, y1), fill=C['white'], width=3)
    d.line((x0, y1 - 18, x1, y1 - 24), fill=C['white'], width=2)
    d.line((x0 + 110, y0, x0 + 118, y1), fill=hx('#f2d58a'), width=3)
    d.line((x0, y0 + 60, x1, y0 + 64), fill=hx('#9fc4dd'), width=4)  # river
    if pin:
        px, py = pin
        d.ellipse((px - 3, py - 8, px + 3, py - 2), fill=C['red']); d.polygon([(px - 2, py - 4), (px + 2, py - 4), (px, py)], fill=C['red'])
        d.point((px, py - 5), fill=C['white'])
        if pinlabel:
            d.rectangle((px + 5, py - 9, px + 6 + text_w(pinlabel) + 2, py - 3), fill=C['white']); text(d, px + 7, py - 8, pinlabel, C['ink'])

def b_map():
    im, d, (x0, y0, x1, y1) = browser_base('MAPS.WEB/?Q=KESTREL+LANE', 'MAPS')
    street_map(d, (x0, y0, x1, y1), pin=(x0 + 88, y0 + 44), pinlabel='KESTREL LN')
    return im

def b_geo(step):
    im, d, (x0, y0, x1, y1) = browser_base('IPLOCATE.NET/77.41.9.130', 'IPLOCATE')
    street_map(d, (x0, y0 + 12, x1, y1), pin=(x0 + 40 + step * 25, y0 + 30 + step * 9) if step >= 0 else None,
               pinlabel='RELAY?' if step < 2 else 'HERE', seed=11)
    d.rectangle((x0, y0, x1, y0 + 10), fill=C['ink'])
    text(d, x0 + 3, y0 + 3, 'IP 77.41.9.130  ACCURACY ' + ('5KM', '800M', '40M')[max(0, min(2, step))], C['term'])
    return im

def b_reset(state):
    im, d, (x0, y0, x1, y1) = browser_base('METAYOU.COM/RECOVER', 'METAYOU')
    d.rectangle((x0, y0, x1, y0 + 9), fill=C['blue']); text(d, x0 + 3, y0 + 3, 'METAYOU', C['white'])
    text(d, x0 + 10, y0 + 16, 'FORGOT YOUR PASSWORD?', C['ink'])
    text(d, x0 + 10, y0 + 26, 'SECURITY QUESTION:', C['inkL'])
    text(d, x0 + 10, y0 + 33, 'NAME OF YOUR FIRST PET?', C['ink'])
    d.rectangle((x0 + 10, y0 + 42, x1 - 10, y0 + 52), fill=C['white'], outline=C['grey'])
    ans = {'empty': '_', 'fail': 'FLUFFY', 'ok': 'BISCUIT', 'locked': 'BISCUIT'}[state]
    text(d, x0 + 13, y0 + 45, ans, C['ink'])
    d.rectangle((x0 + 10, y0 + 56, x0 + 44, y0 + 64), fill=C['blue']); text(d, x0 + 13, y0 + 58, 'SUBMIT', C['white'])
    if state == 'fail':
        text(d, x0 + 10, y0 + 70, 'WRONG ANSWER. 2 TRIES LEFT.', C['red'])
    if state == 'ok':
        text(d, x0 + 10, y0 + 70, 'CODE SENT TO N****@MAIL.WEB', C['grn'])
    if state == 'locked':
        text(d, x0 + 10, y0 + 70, 'ACCOUNT LOCKED BY OWNER.', C['red'])
        text(d, x0 + 10, y0 + 77, '2-STEP LOGIN IS ON.', C['red'])
    return im

def b_phish(sent=False):
    im, d, (x0, y0, x1, y1) = browser_base('MAIL.WEB/COMPOSE', 'MAIL')
    text(d, x0 + 4, y0 + 3, 'FROM: SECURITY@METAY0U.CO', C['ink'])
    text(d, x0 + 4, y0 + 10, 'TO:   NORA.V@MAIL.WEB', C['ink'])
    text(d, x0 + 4, y0 + 17, 'SUBJ: UNUSUAL LOGIN!!!', C['red'])
    d.line((x0 + 2, y0 + 24, x1 - 2, y0 + 24), fill=C['paperD'])
    d.rectangle((x0 + 4, y0 + 27, x0 + 40, y0 + 33), fill=C['blue']); text(d, x0 + 6, y0 + 28, 'METAYOU', C['white'])
    text(d, x0 + 4, y0 + 37, 'DEAR USER,', C['ink'])
    text(d, x0 + 4, y0 + 44, 'SOMEONE TRIED TO LOG IN.', C['ink'])
    text(d, x0 + 4, y0 + 51, 'CLICK HERE TO VERIFY:', C['ink'])
    text(d, x0 + 4, y0 + 58, 'METAY0U.CO/VERIFY', C['link']); d.line((x0 + 4, y0 + 64, x0 + 70, y0 + 64), fill=C['link'])
    text(d, x0 + 4, y0 + 69, 'THANK YOU, METAYOU TEAM', C['inkL'])
    d.rectangle((x1 - 34, y1 - 11, x1 - 4, y1 - 3), fill=C['grn'] if sent else C['blue'])
    text(d, x1 - 31, y1 - 9, 'SENT!' if sent else 'SEND', C['white'])
    return im

def b_inbox():
    im, d, (x0, y0, x1, y1) = browser_base('METAYOU.COM/MESSAGES', 'METAYOU - NORA')
    d.rectangle((x0, y0, x1, y0 + 9), fill=C['blue']); text(d, x0 + 3, y0 + 3, 'MESSAGES (LOGGED IN AS NORA)', C['white'])
    rows = [('DORIAN', 'ANSWER ME.', 'red'), ('DORIAN', 'I KNOW WHERE YOU WORK', 'red'), ('DORIAN', 'YOU CANT HIDE FOREVER', 'red'),
            ('SIS', 'STAY WITH ME A WHILE?', 'ink'), ('BAKERY', 'SHIFT SWAP FRI', 'ink'), ('COURT', 'ORDER GRANTED', 'blue')]
    for i, (who, msg, col) in enumerate(rows):
        y = y0 + 13 + i * 12
        d.rectangle((x0 + 2, y, x1 - 2, y + 10), fill=C['white'])
        d.rectangle((x0 + 4, y + 2, x0 + 10, y + 8), fill=C['grey'] if who != 'DORIAN' else hx('#5a5a5a'))
        text(d, x0 + 13, y + 1, who, C['ink']); text(d, x0 + 13, y + 6 - 1 + 1, '', C['ink'])
        text(d, x0 + 54, y + 3, msg[:26], C[col])
    return im

def b_private():
    im, d, (x0, y0, x1, y1) = browser_base('METAYOU.COM/NORA.VANCE', 'METAYOU')
    d.rectangle((x0, y0, x1, y0 + 9), fill=C['blue']); text(d, x0 + 3, y0 + 3, 'METAYOU', C['white'])
    cx = (x0 + x1) // 2
    d.rectangle((cx - 8, y0 + 28, cx + 8, y0 + 42), fill=C['grey']); d.arc((cx - 6, y0 + 18, cx + 6, y0 + 34), 180, 360, fill=C['grey'], width=2)
    d.rectangle((cx - 1, y0 + 33, cx + 1, y0 + 37), fill=C['ink'])
    s = 'THIS ACCOUNT IS PRIVATE'; text(d, cx - text_w(s) // 2, y0 + 50, s, C['ink'])
    s = 'POSTS HIDDEN. PHOTOS REMOVED.'; text(d, cx - text_w(s) // 2, y0 + 58, s, C['inkL'])
    return im

def b_news(variant):
    im, d, (x0, y0, x1, y1) = browser_base('THENEWTRUTH.COM/LOCAL', 'THE NEW TRUTH')
    d.rectangle((x0, y0, x1, y0 + 12), fill=C['white'])
    text_big(d, x0 + 4, y0 + 2, 'THE NEW TRUTH', C['ink'])
    d.line((x0, y0 + 13, x1, y0 + 13), fill=C['ink'])
    heads = {'intruder': ('INTRUDER ON', 'KESTREL LANE'), 'empty': ('BREAK-IN AT', 'EMPTY FLAT'), 'teen': ('TEEN HACKER', 'ARRESTED'),
             'dorian': ('STALKER', 'ARRESTED')}[variant]
    text_big(d, x0 + 4, y0 + 18, heads[0], C['ink']); text_big(d, x0 + 4, y0 + 30, heads[1], C['redD'])
    ph = (x1 - 46, y0 + 18, x1 - 4, y0 + 52)
    if variant == 'dorian':
        paste(im, face_dorian(42, 34), (ph[0], ph[1]))
    else:
        dither_v(d, ph, hx('#6d6a7a'), hx('#3d3b47'))
        d.rectangle((ph[0] + 8, ph[1] + 10, ph[0] + 24, ph[3]), fill=hx('#2a2830'))
        d.rectangle((ph[0] + 11, ph[1] + 14, ph[0] + 15, ph[1] + 18), fill=C['yel'])
        d.rectangle((ph[0] + 28, ph[1] + 20, ph[0] + 34, ph[3]), fill=hx('#4c4a57'))
    for i in range(7): scribble(d, x0 + 4, y0 + 48 + i * 5, (x1 - x0) - (54 if i < 1 else 10), C['inkL'], 20 + i)
    return im

def b_dorian():
    im, d, (x0, y0, x1, y1) = browser_base('SEARCH.WEB/?Q=DORIAN+PELL', 'SEARCH')
    text(d, x0 + 4, y0 + 3, 'RESULTS FOR: DORIAN PELL', C['ink'])
    paste(im, face_dorian(30, 34), (x0 + 4, y0 + 12))
    text(d, x0 + 38, y0 + 13, 'RESTRAINING ORDER', C['link'])
    text(d, x0 + 38, y0 + 20, 'GRANTED AGAINST', C['ink'])
    text(d, x0 + 38, y0 + 27, 'LOCAL MAN', C['ink'])
    text(d, x0 + 38, y0 + 36, 'ALIAS: CROW', C['red'])
    for i in range(3):
        y = y0 + 52 + i * 12
        text(d, x0 + 4, y, ('DARKBOARD USER CROW...', 'PELL, D. - 2 COMPLAINTS', 'METAYOU: DORIAN P.')[i], C['link'])
        scribble(d, x0 + 4, y + 6, 110, C['inkL'], 40 + i)
    return im

def b_poc():
    im, d, (x0, y0, x1, y1) = browser_base('PRIMATE-OBS.CLUB', 'P.O.C.')
    d.rectangle((x0, y0, x1, y1), fill=hx('#1d2a1e'))
    cx = (x0 + x1) // 2
    # monkey eye logo
    d.ellipse((cx - 16, y0 + 8, cx + 16, y0 + 30), fill=hx('#c9b58a'))
    d.ellipse((cx - 7, y0 + 12, cx + 7, y0 + 26), fill=hx('#6b4a2a')); d.ellipse((cx - 3, y0 + 16, cx + 3, y0 + 22), fill=C['black'])
    d.point((cx - 2, y0 + 17), fill=C['white'])
    s = 'PRIMATE OBSERVATION CLUB'; text(d, cx - text_w(s) // 2, y0 + 36, s, hx('#c9b58a'))
    s = 'MEMBERS ONLY'; text(d, cx - text_w(s) // 2, y0 + 44, s, C['red'])
    d.rectangle((cx - 34, y0 + 54, cx + 34, y0 + 62), fill=C['black'], outline=hx('#c9b58a')); text(d, cx - 31, y0 + 56, 'PASSWORD: ****', C['grey'])
    s = 'DO NOT FEED THE MONKEYS.'; text(d, cx - text_w(s) // 2, y0 + 72, s, hx('#7f8f6a'))
    return im

def b_welcome():
    im, d, (x0, y0, x1, y1) = browser_base('PRIMATE-OBS.CLUB/WELCOME', 'P.O.C.')
    d.rectangle((x0, y0, x1, y1), fill=hx('#1d2a1e'))
    s = 'WELCOME, NEW MEMBER'; text(d, (x0 + x1) // 2 - text_w(s) // 2, y0 + 4, s, hx('#c9b58a'))
    r = random.Random(5)
    for i in range(6):
        cx, cy = x0 + 6 + (i % 3) * 52, y0 + 14 + (i // 3) * 36
        d.rectangle((cx, cy, cx + 46, cy + 30), fill=C['black'])
        dither_v(d, (cx + 1, cy + 1, cx + 45, cy + 29), hx('#4d4436'), hx('#2a2620'))
        for _ in range(3):
            bx, by = r.randint(cx + 3, cx + 36), r.randint(cy + 8, cy + 22)
            d.rectangle((bx, by, bx + r.randint(3, 8), by + r.randint(4, 8)), fill=r.choice((C['hood'], C['redD'], C['corkD'], C['blueD'])))
        text(d, cx + 2, cy + 2, 'CAGE %02d' % (i + 3), C['lgrey'])
        if i == 4:
            d.rectangle((cx, cy, cx + 46, cy + 30), outline=C['red'])
            text(d, cx + 2, cy + 24, '? YOU', C['red'])
    return im

def b_search():
    im, d, (x0, y0, x1, y1) = browser_base('SEARCH.WEB/?Q=FIND+ADDRESS+FROM+PHOTO', 'SEARCH')
    text(d, x0 + 4, y0 + 3, 'HOW TO FIND AN ADDRESS', C['ink']); text(d, x0 + 4, y0 + 9, 'FROM A PHOTO (EASY!!)', C['ink'])
    for i in range(5):
        y = y0 + 20 + i * 14
        text(d, x0 + 4, y, ('10 OSINT TRICKS PROS USE', 'REFLECTIONS GIVE YOU AWAY', 'IS THIS LEGAL? (NO)', 'FORUM: H4CK SCHOOL', 'STREET SIGNS + MAPS')[i], C['link'])
        scribble(d, x0 + 4, y + 6, 130, C['inkL'], 60 + i)
    return im

def browser_frames():
    names = ['meta', 'photo', 'photoMark', 'map', 'resetEmpty', 'resetFail', 'resetOk', 'resetLocked', 'phish', 'phishSent',
             'inbox', 'private', 'newsIntruder', 'newsEmpty', 'dorian', 'poc', 'geo0', 'geo1', 'geo2', 'search', 'welcome']
    fr = [b_meta(), b_photo(), b_photo(True), b_map(), b_reset('empty'), b_reset('fail'), b_reset('ok'), b_reset('locked'),
          b_phish(), b_phish(True), b_inbox(), b_private(), b_news('intruder'), b_news('empty'), b_dorian(), b_poc(),
          b_geo(0), b_geo(1), b_geo(2), b_search(), b_welcome()]
    return names, fr

# --- terminal
TW, TH = 124, 70
def term_frame(lines, cursor=True, title='TERMINAL'):
    im, d, (x0, y0, x1, y1) = window(TW, TH, title)
    d.rectangle((x0, y0, x1, y1), fill=C['termB'])
    y = y0 + 2
    for ln in lines[-9:]:
        col = C['term']
        if ln.startswith('!'): col, ln = C['red'], ln[1:]
        elif ln.startswith('~'): col, ln = C['termD'], ln[1:]
        elif ln.startswith('^'): col, ln = C['yel'], ln[1:]
        text(d, x0 + 2, y, ln[:29], col)
        y += 6
    if cursor:
        lx = x0 + 2 + text_w(lines[-1].lstrip('!~^')[:29]) + 2 if lines else x0 + 2
        d.rectangle((lx, y - 6, lx + 2, y - 2), fill=C['term'])
    return im

P = 'M0TH@SHED:~$ '
TERM_SEQ = {
    'idle': [[P], [P]],
    'typing': [[P + 'NMAP -SV 10.0.0.1'], [P + 'NMAP -SV 10.0.0.1', '~STARTING SCAN...'],
               [P + 'NMAP -SV 10.0.0.1', '~STARTING SCAN...', '~22/TCP OPEN SSH', '~80/TCP OPEN HTTP'],
               [P + 'NMAP -SV 10.0.0.1', '~STARTING SCAN...', '~22/TCP OPEN SSH', '~80/TCP OPEN HTTP', '^DONE: IT IS MY ROUTER', P]],
    'phish': [[P + 'PYTHON PHISH.PY'], [P + 'PYTHON PHISH.PY', '~CLONING METAYOU LOGIN...'],
              [P + 'PYTHON PHISH.PY', '~CLONING METAYOU LOGIN...', '~SERVING ON METAY0U.CO', '^WAITING FOR VICTIM...']],
    'denied': [[P + 'SUDO KILL -9 4471', '!OPERATION NOT PERMITTED', P], [P + 'SUDO KILL -9 4471', '!OPERATION NOT PERMITTED', '!PROCESS IS PROTECTED', P]],
    'trace': [[P + 'TRACEROUTE POC_RELAY'], [P + 'TRACEROUTE POC_RELAY', '~1  192.168.0.1  1MS'],
              [P + 'TRACEROUTE POC_RELAY', '~1  192.168.0.1  1MS', '~2  10.44.0.1  9MS', '~3  * * *'],
              [P + 'TRACEROUTE POC_RELAY', '~1  192.168.0.1  1MS', '~2  10.44.0.1  9MS', '~3  * * *', '~4  77.41.9.130', '^RELAY.PRIMATE-OBS.CLUB']],
    'wipe': [[P + 'SHRED -U TARGET.TXT'], [P + 'SHRED -U TARGET.TXT', '~PASS 1/3...'], [P + 'SHRED -U TARGET.TXT', '~PASS 1/3...', '~PASS 3/3', '^GONE.', P]],
    'vpn': [[P + 'FREEVPN --CONNECT'], [P + 'FREEVPN --CONNECT', '~CONNECTED: FREEVPN (FREE!)'], [P + 'FREEVPN --CONNECT', '~CONNECTED: FREEVPN (FREE!)', '!WARNING: DNS LEAK', P]],
}
def term_frames():
    names, frames, anims = [], [], {}
    for k, seq in TERM_SEQ.items():
        idx = []
        for i, lines in enumerate(seq):
            for blink in ((True, False) if k == 'idle' else (True,)):
                frames.append(term_frame(lines, cursor=blink)); idx.append(len(frames) - 1)
        anims[k] = idx
    return anims, frames

# --- tutorial video
VW, VH = 106, 78
def video_frames():
    fr = []
    for talk in (False, True):
        for ep in ('EP.7 SOCIAL ENGINEERING', 'EP.12 STAY ANONYMOUS'):
            im, d, (x0, y0, x1, y1) = window(VW, VH, 'H4CK SCHOOL')
            d.rectangle((x0, y0, x1, y1), fill=C['black'])
            paste(im, host_frame(x1 - x0 + 1, y1 - y0 - 12, talk), (x0, y0))
            d.rectangle((x0, y1 - 11, x1, y1), fill=hx('#101010'))
            text(d, x0 + 2, y1 - 9, ep[:25], C['yel'])
            d.rectangle((x0 + 2, y1 - 3, x1 - 2, y1 - 2), fill=C['dgrey']); d.rectangle((x0 + 2, y1 - 3, x0 + 30 + (20 if talk else 0), y1 - 2), fill=C['red'])
            fr.append(im)
    # 0 ep7 idle, 1 ep12 idle, 2 ep7 talk, 3 ep12 talk
    anims = {'ep7': [0], 'ep7talk': [2, 0, 2, 2, 0], 'ep12': [1], 'ep12talk': [3, 1, 3, 3, 1]}
    return anims, fr

# --- DarkBoard chat
CW, CH = 100, 104
CHAT_STATES = {
    'empty': [],
    'job': [('CROW', 'GOT A JOB 4 U'), ('CROW', 'FIND WHERE SHE LIVES'), ('CROW', 'NORA VANCE'), ('CROW', '300 COINS'), ('M0TH', 'EZ. DEAL')],
    'push': [('CROW', 'PROGRESS?'), ('M0TH', 'GOT HER STREET'), ('CROW', 'I NEED THE NUMBER'), ('CROW', 'AND HER SCHEDULE'), ('M0TH', 'WHY?'), ('CROW', 'SHE OWES ME')],
    'paid': [('M0TH', 'KESTREL LANE 14'), ('CROW', 'GOOD BOY'), ('*', '+300 COINS RECEIVED'), ('CROW', 'NOW DELETE IT ALL')],
    'paidWrong': [('M0TH', 'KESTREL LANE 14'), ('CROW', 'GOOD BOY'), ('*', '+300 COINS RECEIVED'), ('CROW', 'NOW DELETE IT ALL')],
    'threat': [('M0TH', 'YOU USED ME'), ('M0TH', 'YOU ARE DORIAN'), ('CROW', 'CAREFUL KID'), ('CROW', 'I FOUND HER.'), ('CROW', 'I CAN FIND YOU.')],
    'banned': [('*', 'USER CROW WAS BANNED'), ('*', 'REASON: ARRESTED LOL')],
}
def wrap_words(msg, width):
    lines, cur = [], ''
    for w in msg.split(' '):
        if cur and len(cur) + 1 + len(w) > width: lines.append(cur); cur = w
        else: cur = (cur + ' ' + w).strip()
    lines.append(cur); return lines

def chat_frame(msgs):
    im, d, (x0, y0, x1, y1) = window(CW, CH, 'DARKBOARD #JOBS')
    d.rectangle((x0, y0, x1, y1), fill=hx('#17131c'))
    y = y0 + 2
    for who, msg in msgs[-8:]:
        if who == '*':
            text(d, x0 + 2, y, msg[:23], C['yel']); y += 9; continue
        col = C['red'] if who == 'CROW' else C['term']
        text(d, x0 + 2, y, who + ':', col)
        first = 23 - len(who) - 1
        parts = wrap_words(msg, first)
        text(d, x0 + 2 + text_w(who + ':') + 3, y, parts[0], C['lgrey'])
        for extra in parts[1:]:
            y += 6; text(d, x0 + 2 + text_w(who + ':') + 3, y, extra, C['lgrey'])
        y += 9
    d.rectangle((x0, y1 - 8, x1, y1), fill=hx('#221c29')); text(d, x0 + 2, y1 - 6, '>_', C['grey'])
    return im
def chat_frames():
    anims, frames = {}, []
    for k, msgs in CHAT_STATES.items():
        idx = []
        # reveal messages one by one (last frame = full state)
        steps = range(1, len(msgs) + 1) if msgs else [0]
        for n in steps:
            frames.append(chat_frame(msgs[:n])); idx.append(len(frames) - 1)
        anims[k] = idx
        anims[k + 'Full'] = [idx[-1]]
    return anims, frames

# --- notes TARGET.txt
NW, NH = 78, 92
NOTE_LINES = ['TARGET: NORA VANCE', 'METAYOU: PUBLIC (LOL)', 'JOB: SWEET CRUMB', 'CAT: ORANGE (BISCUIT?)', 'BLUE BIKE',
              'PH: 555-0147', 'STREET: KESTREL LN', 'NO. 14 ?', 'SHIFT ENDS 18:00']
def notes_frame(n, title='TARGET.TXT'):
    im, d, (x0, y0, x1, y1) = window(NW, NH, title, theme='light')
    for i, ln in enumerate(NOTE_LINES[:n]):
        text(d, x0 + 2, y0 + 2 + i * 8, ln[:18], C['ink'] if not ln.startswith('PH') else C['redD'])
    if n == 0:
        d.rectangle((x0 + 2, y0 + 2, x0 + 3, y0 + 6), fill=C['ink'])
    return im
def notes_frames():
    fr = [notes_frame(n) for n in range(len(NOTE_LINES) + 1)]
    return {('n%d' % i): [i] for i in range(len(fr))}, fr

# --- doxx board
DW, DH = 144, 98
def board_frame(stage):
    im, d, (x0, y0, x1, y1) = window(DW, DH, 'BOARD.PNG')
    d.rectangle((x0, y0, x1, y1), fill=C['cork'])
    r = random.Random(2)
    for _ in range(140):
        d.point((r.randint(x0, x1), r.randint(y0, y1)), fill=C['corkD'])
    hub = (x0 + 69, y0 + 5)
    cards = []
    if stage >= 1: cards += [(x0 + 6, y0 + 8, 30, 20, hx('#f0d9b5'), 'BAKERY'), (x0 + 104, y0 + 8, 30, 20, hx('#bcd3b0'), 'BIKE')]
    if stage >= 2: cards += [(x0 + 8, y0 + 50, 34, 24, hx('#e6e0cc'), 'KESTREL'), (x0 + 50, y0 + 44, 40, 10, C['paper'], '555-0147')]
    if stage >= 3: cards += [(x0 + 100, y0 + 46, 32, 32, hx('#9a9a9a'), 'CROW?')]
    for (x, y, w, h, *_r) in cards: d.line((hub, (x + w // 2, y)), fill=C['string'])
    if stage >= 4: d.line((hub, (x0 + 72, y0 + 60)), fill=C['string'])
    for (x, y, w, h, fill, label) in cards:
        d.rectangle((x + 1, y + 1, x + w + 1, y + h + 1), fill=C['corkD'])
        d.rectangle((x, y, x + w, y + h), fill=fill)
        if label == 'CROW?': paste(im, face_dorian(24, 22), (x + 4, y + 3))
        elif label == 'KESTREL':
            d.line((x + 3, y + 6, x + w - 3, y + 9), fill=C['white'], width=2); d.ellipse((x + 14, y + 3, x + 18, y + 7), fill=C['red'])
        text(d, x + 2, y + h - 6, label, C['ink'])
        d.ellipse((x + w // 2 - 1, y - 1, x + w // 2 + 1, y + 1), fill=C['red'])
    paste(im, face_nora(22, 22, 'paper'), (x0 + 58, y0 + 6)); d.rectangle((x0 + 57, y0 + 5, x0 + 80, y0 + 28), outline=C['white'])
    d.ellipse((x0 + 68, y0 + 4, x0 + 70, y0 + 6), fill=C['red'])
    d.rectangle((x0 + 54, y0 + 30, x0 + 84, y0 + 36), fill=C['paper']); text(d, x0 + 56, y0 + 31, 'NORA', C['ink'])
    if stage >= 4:
        d.rectangle((x0 + 52, y0 + 60, x0 + 92, y0 + 84), fill=C['black'])
        d.ellipse((x0 + 62, y0 + 64, x0 + 82, y0 + 74), fill=C['white']); d.ellipse((x0 + 69, y0 + 65, x0 + 75, y0 + 73), fill=C['black'])
        text(d, x0 + 56, y0 + 77, 'WHO R U?', C['red'])
    if stage >= 5:
        d.line((x0 + 72, y0 + 84, x0 + 72, y1), fill=C['string'])
        d.rectangle((x0 + 2, y1 - 9, x0 + 48, y1 - 2), fill=C['paper']); text(d, x0 + 4, y1 - 8, 'RELAY: HERE', C['redD'])
    if stage == 6:
        d.line((x0 + 52, y0 + 2, x0 + 88, y0 + 38), fill=C['black'], width=2); d.line((x0 + 88, y0 + 2, x0 + 52, y0 + 38), fill=C['black'], width=2)
    return im
def board_frames():
    fr = [board_frame(s) for s in range(7)]
    return {('s%d' % i): [i] for i in range(7)}, fr

# --- task manager
KW_, KH_ = 112, 80
def taskmgr_frame(hl, popup):
    im, d, (x0, y0, x1, y1) = window(KW_, KH_, 'PROCESSES')
    d.rectangle((x0, y0, x1, y1), fill=C['bodyL'])
    text(d, x0 + 2, y0 + 2, 'NAME            CPU', C['grey'])
    rows = [('BROWSER', '12%'), ('TERMINAL', '1%'), ('MUSIC', '3%'), ('POC_RELAY.EXE', '7%'), ('MIC_HOOK', '2%'), ('CAM_HOOK', '0%')]
    for i, (n, cpu) in enumerate(rows):
        y = y0 + 10 + i * 8
        if hl and n in ('POC_RELAY.EXE', 'MIC_HOOK', 'CAM_HOOK'):
            d.rectangle((x0 + 1, y - 1, x1 - 1, y + 5), fill=C['redD'])
        text(d, x0 + 2, y, n, C['white'] if hl and i >= 3 else C['lgrey'])
        text(d, x1 - 14, y, cpu, C['lgrey'])
    if popup:
        d.rectangle((x0 + 12, y0 + 24, x1 - 12, y0 + 46), fill=C['paper'], outline=C['black'])
        d.rectangle((x0 + 12, y0 + 24, x1 - 12, y0 + 30), fill=C['red'])
        text(d, x0 + 15, y0 + 25, 'ERROR', C['white'])
        text(d, x0 + 15, y0 + 34, 'ACCESS DENIED.', C['ink'])
        text(d, x0 + 15, y0 + 40, 'OWNER: P.O.C.', C['ink'])
    return im
def taskmgr_frames():
    fr = [taskmgr_frame(False, False), taskmgr_frame(True, False), taskmgr_frame(True, True)]
    return {'list': [0], 'found': [1], 'denied': [2]}, fr

# --- webcam window
FW, FH = 84, 70
def cam_frames():
    def win(content, title='WEBCAM', rec=False):
        im, d, (x0, y0, x1, y1) = window(FW, FH, title)
        paste(im, content, (x0, y0))
        if rec:
            d.ellipse((x1 - 9, y0 + 2, x1 - 5, y0 + 6), fill=C['red']); text(d, x1 - 22, y0 + 3, 'REC', C['red'])
        return im
    cw, ch = FW - 4, FH - 13
    face = lambda mood='neutral', mask=False: override('cam', 'mask' if mask else {'neutral': 'face'}.get(mood, mood), (cw, ch)) or face_elias(cw, ch, mood, mask=mask)
    taped = new(cw, ch); td = ImageDraw.Draw(taped); td.rectangle((0, 0, cw, ch), fill=hx('#141414'))
    for y in range(0, ch, 3): td.line((0, y, cw, y + 1), fill=hx('#1c1c1c'))
    text(td, cw // 2 - text_w('NO SIGNAL') // 2, ch // 2 - 2, 'NO SIGNAL', C['grey'])
    empty = override('cam', 'empty', (cw, ch))
    if empty is None:
      empty = face_elias(cw, ch).copy(); ed = ImageDraw.Draw(empty)
    # empty chair: repaint the person area with the room and a chair back
      ed.rectangle((20, 0, cw - 24, ch), fill=C['bg1']); ed.rectangle((cw - 24, 16, cw, ch), fill=C['bg1']); ed.rectangle((0, 26, 20, ch), fill=C['bg1'])
      ed.rounded_rectangle((cw // 2 - 16, 18, cw // 2 + 16, ch), 5, fill=hx('#22252b')); ed.rounded_rectangle((cw // 2 - 13, 21, cw // 2 + 13, ch), 4, fill=hx('#2d3138'))
    fr = [win(face()), win(face('talk')), win(face('angry')), win(face('scared')),
          win(face(mask=True), 'RECORDING', True),
          # masked confession: talking frame keeps the mask on (was an unmasked face flickering through)
          win(override('cam', 'maskTalk', (cw, ch)) or face(mask=True), 'RECORDING', True),
          win(taped), win(empty)]
    anims = {'face': [0], 'talk': [1, 0, 1, 1, 0], 'angry': [2], 'scared': [3], 'mask': [4], 'recTalk': [5, 4, 5, 5, 4],
             'rec': [5], 'taped': [6], 'empty': [7]}
    return anims, fr


# ------------------------------------------------------------------ hand-made / generated replacements
OVERRIDE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'art_override')
def override(kind, name, size):
    """mod/art_override/<kind>/<name>.png, exactly `size` or an integer multiple of it (scaled down nearest-neighbour)."""
    path = os.path.join(OVERRIDE_DIR, kind, name + '.png')
    if not os.path.isfile(path): return None
    im = Image.open(path).convert('RGBA')
    w, h = size
    if im.size != (w, h):
        k = im.width // w
        if k < 1 or im.size != (w * k, h * k):
            raise SystemExit('art_override/%s/%s.png is %dx%d, expected %dx%d or a multiple' % (kind, name, im.width, im.height, w, h))
        im = im.resize((w, h), Image.NEAREST)
    print('override', kind, name)
    return im

# --- popups
PW, PH = 96, 34
def popup(title, lines, col='red'):
    im, d, (x0, y0, x1, y1) = window(PW, PH, title, theme='light')
    d.rectangle((x0, y0, x0 + 12, y1), fill=C[col])
    text(d, x0 + 5, y0 + (y1 - y0) // 2 - 2, '!', C['white'])
    for i, ln in enumerate(lines): text(d, x0 + 16, y0 + 3 + i * 7, ln, C['ink'])
    return im
def popup_frames():
    items = [('denied', 'SYSTEM', ['ACCESS DENIED'], 'red'), ('camOn', 'SYSTEM', ['WEBCAM IN USE', 'BY: ???'], 'yel'),
             ('paid', 'WALLET', ['+300 COINS', 'FROM: CROW'], 'grn'), ('sent', 'MAIL', ['MESSAGE SENT'], 'blue'),
             ('clicked', 'PHISH.PY', ['VICTIM CLICKED!', 'PASSWORD: ******'], 'grn'), ('battery', 'SYSTEM', ['MIC: ALWAYS ON?', 'BY: MIC_HOOK'], 'yel'),
             ('order', 'MART', ['ORDER PLACED', 'GIFT FOR: YOU'], 'blue'), ('pizza', 'PIZZA NOW', ['ORDER #4471', 'ETA 30 MIN'], 'red')]
    return {k: [i] for i, (k, *_r) in enumerate(items)}, [popup(t, l, c) for (_k, t, l, c) in items]

# --- post-it with Nora's phone number (clickable keyword)
PAD = 3   # transparent margin around clickable sprites: the game's outline shader draws into it

def pad(im, n=PAD):
    out = new(im.width + 2 * n, im.height + 2 * n); out.alpha_composite(im, (n, n)); return out

def postit():
    return pad(_postit())

def _postit():
    im = new(34, 24); d = ImageDraw.Draw(im)
    d.rectangle((1, 1, 33, 23), fill=hx('#7a6a2a', 120))
    d.rectangle((0, 0, 32, 22), fill=hx('#f1dc6a'))
    d.rectangle((0, 0, 32, 3), fill=hx('#e3c94e'))
    text(d, 3, 6, 'NORA', C['ink'])
    text(d, 3, 13, '5550147', C['redD'])
    return im

# --- small desktop label under the moth (clickable keyword m0th)
def label_m0th():
    im = new(40, 9); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, 39, 8), 2, fill=hx('#3a312a'))
    text(d, 20 - text_w('USER: M0TH') // 2, 2, 'USER: M0TH', C['mothL'])
    return pad(im)

# --- clock widget (anim per hour label)
def clock_frames(labels):
    fr = []
    for s in labels:
        im = new(26, 8); d = ImageDraw.Draw(im)
        text(d, 26 - text_w(s) - 1, 1, s, C['chrome4'])
        fr.append(im)
    return fr

# --- screensaver moth and black screen, signal lost noise, glass reflection (night vision only)
def black_screen():
    im = new(W, H, hx('#121012')); d = ImageDraw.Draw(im)
    return im

def saver_moth():
    return [ascii_sprite(MOTH, moth_pal()), ascii_sprite(MOTH2, moth_pal())]

def lost_frames():
    out = []
    for s in range(3):
        r = random.Random(100 + s)
        im = new(W, H, C['black']); px = im.load()
        for y in range(H):
            for x in range(W):
                v = r.randint(0, 90)
                px[x, y] = (v, v, v + 6, 255)
        d = ImageDraw.Draw(im)
        d.rectangle((W // 2 - 50, H // 2 - 10, W // 2 + 50, H // 2 + 10), fill=C['black'])
        s1 = 'SIGNAL LOST'; text_big(d, W // 2 - len(s1) * 4, H // 2 - 6, s1, C['red'] if s != 1 else C['white'])
        out.append(im)
    return out

def reflection(kind):
    """Faint reflection of the room on the dark monitor glass. Drawn with low alpha."""
    o = override('reflect', kind, (W, H))
    if o is not None: return o
    im = new(W, H); d = ImageDraw.Draw(im)
    a = 110
    g = lambda c: (c[0], c[1], c[2], a)
    # room: door frame and a lamp
    d.rectangle((200, 20, 236, 160), outline=g(hx('#6a6a7a')))
    d.line((30, 40, 30, 150), fill=g(hx('#5a5a6a')))
    cx = 120
    if kind in ('sleep', 'stare'):
        d.ellipse((cx - 40, 110, cx + 40, 190), fill=g(C['hood']))
        if kind == 'sleep':
            d.ellipse((cx - 18, 96, cx + 18, 130), fill=g(C['skinD']))  # head down on arms
            d.ellipse((cx - 20, 92, cx + 20, 112), fill=g(C['hair']))
            d.rectangle((cx - 50, 128, cx + 50, 140), fill=g(C['hoodD']))
        else:
            d.ellipse((cx - 16, 58, cx + 16, 98), fill=g(C['skin']))
            d.ellipse((cx - 18, 52, cx + 18, 72), fill=g(C['hair']))
            for ex in (cx - 7, cx + 6):
                d.ellipse((ex - 4, 74, ex + 4, 80), outline=g(C['black'])); d.point((ex, 77), fill=(255, 255, 255, 200))
            d.line((cx - 4, 89, cx + 4, 89), fill=g(C['skinDD']))
    if kind == 'empty':
        d.rounded_rectangle((cx - 26, 80, cx + 26, 174), 8, fill=g(hx('#2d3138')))
        d.rectangle((200, 20, 236, 160), fill=g(hx('#2a2a33')))  # open door: darker
    return im

# ------------------------------------------------------------------ build
CLOCKS = ['02:00', '09:00', '10:00', '11:00', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00', '19:00', '20:00', '21:00', '22:00', '23:00', '23:50']

def build(out):
    os.makedirs(out, exist_ok=True)
    L = {}
    def save(name, img): img.save(os.path.join(out, name + '.png'))
    def save_sheet(name, frames, anims, fps=6, loops=None):
        save(name, sheet(frames))
        w, h = frames[0].size
        L[name] = {'w': w, 'h': h, 'anims': anims, 'fps': fps}
    save('wall', wallpaper()); L['wall'] = {'w': W, 'h': H}
    save('overlay', club_overlay()); L['overlay'] = {'w': W, 'h': H}
    save('black', black_screen()); L['black'] = {'w': W, 'h': H}
    save('postit', postit()); L['postit'] = {'w': 34 + 2 * PAD, 'h': 24 + 2 * PAD}
    save('label', label_m0th()); L['label'] = {'w': 40 + 2 * PAD, 'h': 9 + 2 * PAD}
    save_sheet('cursor', cursor_frames(), {'default': [0], 'click': [1, 0], 'wait': [2, 3]})
    save_sheet('voice', voice_frames(), {'default': [0], 'habla': [1, 2, 3, 1, 4, 2], 'idle': [0, 4]})
    names, bf = browser_frames(); save_sheet('browser', bf, {n: [i] for i, n in enumerate(names)})
    a, f = term_frames(); save_sheet('term', f, a)
    a, f = video_frames(); save_sheet('video', f, a)
    a, f = chat_frames(); save_sheet('chat', f, a)
    a, f = notes_frames(); save_sheet('notes', f, a)
    a, f = board_frames(); save_sheet('board', f, a)
    a, f = taskmgr_frames(); save_sheet('taskmgr', f, a)
    a, f = cam_frames(); save_sheet('cam', f, a)
    a, f = popup_frames(); save_sheet('popup', f, a)
    save_sheet('clock', clock_frames(CLOCKS), {('t' + c.replace(':', '')): [i] for i, c in enumerate(CLOCKS)})
    save_sheet('saver', saver_moth(), {'default': [0, 1]})
    save_sheet('lost', lost_frames(), {'default': [0, 1, 2]})
    save_sheet('reflect', [reflection(k) for k in ('sleep', 'stare', 'empty')], {'sleep': [0], 'stare': [1], 'empty': [2]})
    return L

if __name__ == '__main__':
    import json
    L = build(sys.argv[1])
    print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk != 'anims'} | ({'anims': list(v['anims'])} if 'anims' in v else {}) for k, v in L.items()}, indent=1)[:3000])
