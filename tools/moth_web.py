"""
Browser / newspaper / ending art for the Moth Screen cage (needs ModLoader 0.5+, which loads "mods/<Mod>/<file>").

Sizes match the game's own images:
  photos (news, Metayou avatar and posts, wiki pictures, endings)  110 x 80
  web page backgrounds (text is laid over them by the "struct")    376 x 157
  map                                                              364 x 107
  chat avatar                                                      18 x 17
  door guest                                                       120 x 210
"""
import math, os, random
from PIL import Image, ImageDraw
import moth_art as A
from moth_art import C, hx, new, text, text_w, text_big, outline, ascii_sprite, MOTH, MOTH2, moth_pal, dither_v, paste, stack, layer, scribble

PW, PH = 110, 80

def photo():
    im, d = layer(PW, PH); return im, d

def frame_out(im):
    """Thin warm-dark border like printed photos in the game."""
    d = ImageDraw.Draw(im); d.rectangle((0, 0, im.width - 1, im.height - 1), outline=C['out']); return im

def sky_night(d, box): dither_v(d, box, hx('#1b2033'), hx('#3a4566'))
def sky_day(d, box): dither_v(d, box, hx('#8fb3d4'), hx('#cfe0ea'))

def person(w, h, body, head=None, hair=None, cap=None, back=False):
    """Simple outlined figure (bust/half body) for small news photos."""
    L, d = layer(w, h)
    cx = w // 2
    d.ellipse((cx - w // 3, h // 2, cx + w // 3, h + h // 3), fill=body)
    d.ellipse((cx - w // 6, h // 5, cx + w // 6, h // 2 + 3), fill=head or C['skin'])
    if hair: d.chord((cx - w // 6 - 1, h // 5 - 2, cx + w // 6 + 1, h // 2), 180, 360, fill=hair)
    if cap: d.rectangle((cx - w // 6 - 1, h // 5 - 2, cx + w // 6 + 1, h // 5 + 2), fill=cap)
    if back and hair: d.ellipse((cx - w // 6, h // 5, cx + w // 6, h // 2 + 3), fill=hair)
    outline(L, C['out'])
    if not back:
        ey = h // 5 + (h // 2 + 3 - h // 5) // 2
        dd = ImageDraw.Draw(L); dd.point((cx - 2, ey), fill=C['out']); dd.point((cx + 2, ey), fill=C['out'])
        dd.line((cx - 1, ey + 3, cx + 1, ey + 3), fill=C['skinDD'])
    return L

# ------------------------------------------------------------------ news photos
def news_intruder():
    im, d = photo()
    sky_night(d, (0, 0, PW, 40))
    d.rectangle((0, 18, PW, 80), fill=hx('#5b5560'))                                   # house front
    for x in range(0, PW, 8): d.line((x, 18, x, 80), fill=hx('#524c57'))
    d.rectangle((38, 26, 70, 72), fill=C['out']); d.rectangle((40, 28, 68, 72), fill=hx('#6b3f2c'))   # door
    d.polygon([(54, 28), (68, 28), (68, 72), (60, 70)], fill=hx('#2a2026'))            # door ajar, dark inside
    d.line((47, 46, 51, 52), fill=C['yel']); d.line((49, 44, 52, 47), fill=C['yel'])  # broken lock splinters
    d.rectangle((44, 32, 52, 38), fill=C['gold']); text(d, 45, 33, '14', C['out'])
    d.rectangle((0, 72, PW, 80), fill=hx('#3a3638'))
    for i in range(0, PW + 20, 14):                                                    # police tape
        d.polygon([(i - 10, 58), (i, 54), (i + 7, 54), (i - 3, 58)], fill=C['yel'])
        d.polygon([(i, 54), (i + 7, 54), (i + 4, 55), (i - 2, 56)], fill=C['out'])
    d.line((0, 56, PW, 54), fill=C['out'])
    for (x, c) in ((10, C['red']), (96, C['blue'])):                                    # siren light wash
        for r in range(16, 2, -2):
            d.ellipse((x - r, 10 - r // 2, x + r, 10 + r // 2), outline=(c[0], c[1], c[2], 40 + (16 - r) * 8))
    d.rectangle((78, 30, 92, 44), fill=C['out']); d.rectangle((79, 31, 91, 43), fill=hx('#9fb6c9'))
    d.line((79, 31, 91, 43), fill=C['white']); d.line((85, 31, 79, 37), fill=C['white'])  # shattered window
    return frame_out(im)

def news_empty():
    im, d = photo()
    d.rectangle((0, 0, PW, PH), fill=hx('#c9c0a8'))
    d.rectangle((0, 56, PW, PH), fill=hx('#8a6a4a')); d.line((0, 56, PW, 56), fill=hx('#6e5238'))
    for x in range(0, PW, 12): d.line((x, 56, x - 8, PH), fill=hx('#7b5d40'))
    d.rectangle((12, 10, 40, 58), fill=C['out']); d.rectangle((14, 12, 38, 58), fill=hx('#2e2a2c'))  # open door
    d.polygon([(38, 12), (48, 16), (48, 62), (38, 58)], fill=hx('#7a4a30')); d.line((38, 12, 48, 16), fill=C['out'])
    for (x, y, w, h) in ((60, 40, 22, 18), (70, 26, 18, 14), (86, 44, 18, 14)):        # boxes
        d.rectangle((x - 1, y - 1, x + w + 1, y + h + 1), fill=C['out']); d.rectangle((x, y, x + w, y + h), fill=hx('#c79a5e'))
        d.line((x, y + 3, x + w, y + 3), fill=hx('#a57c45')); d.line((x + w // 2, y, x + w // 2, y + 3), fill=C['chrome0'])
    d.rectangle((52, 14, 72, 22), fill=C['out']); d.rectangle((53, 15, 71, 21), fill=C['paper']); text(d, 55, 16, 'SOLD', C['redD'])
    return frame_out(im)

def mugshot(face, label):
    im, d = photo()
    d.rectangle((0, 0, PW, PH), fill=hx('#b9b4a6'))
    for i, y in enumerate(range(8, PH, 10)):
        d.line((0, y, PW, y), fill=hx('#8d887b')); text(d, 2, y + 2, str(19 - i), hx('#6f6a60'))
    paste(im, face, (PW // 2 - face.width // 2, 6))
    d.rectangle((30, 62, 80, 76), fill=C['out']); d.rectangle((31, 63, 79, 75), fill=hx('#202020'))
    text(d, 55 - text_w(label) // 2, 66, label, C['white'])
    return frame_out(im)

def news_dorian():
    return mugshot(A.face_dorian(56, 58), 'PELL D.')

def news_arrest():
    im, d = photo()
    sky_night(d, (0, 0, PW, PH))
    d.rectangle((0, 58, PW, PH), fill=hx('#2c2a30'))
    d.rectangle((54, 30, 108, 62), fill=C['out']); d.rectangle((56, 34, 106, 58), fill=hx('#d8d8d0'))  # police car
    d.rectangle((56, 44, 106, 50), fill=C['blueD']); text(d, 62, 45, 'POLICE', C['white'])
    d.rectangle((70, 28, 80, 33), fill=C['red']); d.rectangle((81, 28, 91, 33), fill=C['blue'])
    d.ellipse((60, 54, 72, 66), fill=C['out']); d.ellipse((90, 54, 102, 66), fill=C['out'])
    cop = person(30, 50, hx('#2c3a5a'), cap=hx('#1d2740')); paste(im, cop, (6, 28))
    kid = person(30, 50, C['hood'], hair=C['hair'], back=True); paste(im, kid, (28, 30))
    d.rectangle((38, 64, 46, 67), fill=C['lgrey']); d.line((38, 66, 46, 66), fill=C['out'])  # cuffs
    for x, c in ((75, C['red']), (86, C['blue'])):
        for r in range(14, 2, -2): d.ellipse((x - r, 30 - r // 2, x + r, 30 + r // 2), outline=(c[0], c[1], c[2], 30 + (14 - r) * 8))
    return frame_out(im)

def news_turnin():
    im, d = photo()
    sky_day(d, (0, 0, PW, 30))
    d.rectangle((6, 14, 104, 66), fill=C['out']); d.rectangle((8, 16, 102, 66), fill=hx('#b7a78a'))   # station
    d.rectangle((8, 16, 102, 24), fill=C['blueD']); text(d, 55 - text_w('POLICE STATION') // 2, 18, 'POLICE STATION', C['white'])
    for x in (16, 30, 72, 86): d.rectangle((x, 30, x + 8, 42), fill=C['out']); d.rectangle((x + 1, 31, x + 7, 41), fill=hx('#9fb6c9'))
    d.rectangle((44, 32, 66, 66), fill=C['out']); d.rectangle((46, 34, 64, 66), fill=hx('#5a4a3a'))
    d.rectangle((0, 66, PW, PH), fill=hx('#9a9488'))
    for i in range(3): d.rectangle((40 - i * 4, 66 + i * 4, 70 + i * 4, 69 + i * 4), fill=hx('#b3ad9f'))
    kid = person(18, 30, C['hood'], hair=C['hair'], back=True); paste(im, kid, (46, 44))
    return frame_out(im)

# ------------------------------------------------------------------ Metayou: Nora avatar and posts
def nora_profile():
    im, d = photo()
    dither_v(d, (0, 0, PW, PH), hx('#f0d9b5'), hx('#d9b98a'))
    for x in range(4, PW, 16): d.rectangle((x, 4, x + 10, 14), fill=hx('#e8caa0'))      # bakery shelves behind
    f = A.face_nora(60, 66, 'paper'); f2 = f.copy()
    px = f2.load()
    for y in range(f2.height):
        for x in range(f2.width):
            if px[x, y][:3] == C['paper'][:3]: px[x, y] = (0, 0, 0, 0)
    paste(im, f2, (25, 14))
    return frame_out(im)

def post_cat():
    im, d = photo()
    d.rectangle((0, 0, PW, PH), fill=hx('#d7c8a8')); d.rectangle((0, 52, PW, PH), fill=hx('#b78f62'))
    cat, cd = layer(PW, PH)
    cd.ellipse((30, 34, 80, 70), fill=hx('#e39a52')); cd.ellipse((40, 18, 70, 46), fill=hx('#e39a52'))
    cd.polygon([(42, 24), (44, 10), (52, 20)], fill=hx('#e39a52')); cd.polygon([(58, 20), (66, 10), (68, 24)], fill=hx('#e39a52'))
    cd.ellipse((76, 52, 96, 62), fill=hx('#e39a52'))
    outline(cat, C['out']); paste(im, cat, (0, 0))
    d = ImageDraw.Draw(im)
    for x in (36, 46, 56): d.line((x + 10, 36, x + 12, 44), fill=hx('#c27a3a'))
    d.point((49, 31), fill=C['out']); d.point((61, 31), fill=C['out']); d.point((55, 36), fill=hx('#c0605a'))
    d.polygon([(44, 10), (36, 2), (60, 2), (66, 10)], fill=C['red']); d.ellipse((47, 0, 53, 4), fill=C['yel'])   # party hat
    text(d, 4, 4, '5!', C['redD'])
    return frame_out(im)

def post_bakery():
    im, d = photo()
    sky_day(d, (0, 0, PW, 20))
    d.rectangle((6, 12, 104, 70), fill=C['out']); d.rectangle((8, 14, 102, 70), fill=hx('#f0d9b5'))
    for i in range(8, 102, 10):
        d.rectangle((i, 14, i + 4, 24), fill=hx('#c0607a')); d.rectangle((i + 5, 14, i + 9, 24), fill=C['white'])
    d.line((8, 24, 102, 24), fill=C['out'])
    d.rectangle((14, 28, 60, 60), fill=C['out']); d.rectangle((15, 29, 59, 59), fill=hx('#a9cad6'))
    for (x, y) in ((20, 50), (32, 48), (44, 50)): d.ellipse((x, y, x + 10, y + 7), fill=hx('#c9893e')); d.ellipse((x, y, x + 10, y + 7), outline=C['out'])
    d.rectangle((70, 30, 94, 70), fill=C['out']); d.rectangle((72, 32, 92, 70), fill=hx('#7a4a30'))
    d.rectangle((24, 2, 86, 10), fill=C['out']); d.rectangle((25, 3, 85, 9), fill=C['white']); text(d, 55 - text_w('SWEET CRUMB') // 2, 4, 'SWEET CRUMB', hx('#c0607a'))
    d.rectangle((0, 70, PW, PH), fill=hx('#9a9488'))
    return frame_out(im)

def post_bike():
    im, d = photo()
    d.rectangle((0, 0, PW, PH), fill=hx('#bcd3b0')); d.rectangle((0, 58, PW, PH), fill=hx('#9a9488'))
    d.rectangle((0, 20, PW, 58), fill=hx('#c9b89a'))
    for x in range(0, PW, 10): d.line((x, 20, x, 58), fill=hx('#b3a284'))
    bike, bd = layer(PW, PH)
    for cx in (28, 82):
        bd.ellipse((cx - 15, 46, cx + 15, 76), outline=C['out'], width=2); bd.ellipse((cx - 2, 59, cx + 2, 63), fill=C['grey'])
    bd.line((28, 61, 50, 40, 82, 61), fill=C['blue'], width=3); bd.line((50, 40, 58, 61, 28, 61), fill=C['blue'], width=3)
    bd.line((50, 40, 46, 32), fill=C['blueD'], width=2); bd.rectangle((40, 30, 52, 33), fill=C['out'])
    bd.line((72, 36, 82, 61), fill=C['blue'], width=3); bd.line((66, 34, 76, 34), fill=C['out'], width=2)
    bd.rectangle((72, 36, 92, 44), fill=hx('#b07a3a'))                                 # basket
    paste(im, bike, (0, 0))
    return frame_out(im)

# ------------------------------------------------------------------ wiki pictures
def wiki_social():
    im, d = photo()
    d.rectangle((0, 0, PW, PH), fill=hx('#e6e0cc'))
    a = person(46, 70, C['blueD'], hair=C['hair']); b = person(46, 70, hx('#8a5a8a'), hair=C['nhair'])
    paste(im, a, (8, 12)); paste(im, b, (58, 12))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((34, 8, 76, 24), 4, fill=C['white'], outline=C['out']); text(d, 38, 13, 'TRUST ME', C['ink'])
    d.polygon([(44, 24), (40, 30), (50, 24)], fill=C['white'])
    d.rectangle((24, 28, 34, 34), fill=C['out'])                                       # mask held behind back
    return frame_out(im)

def wiki_phishing():
    im, d = photo()
    dither_v(d, (0, 0, PW, PH), hx('#8fb3d4'), hx('#4a6d94'))
    d.rectangle((28, 34, 82, 70), fill=C['out']); d.rectangle((30, 36, 80, 68), fill=C['white'])
    d.polygon([(30, 36), (55, 54), (80, 36)], fill=C['paperD']); d.line((30, 36, 55, 54, 80, 36), fill=C['out'])
    d.line((55, 0, 55, 30), fill=C['grey']); d.arc((48, 22, 62, 36), 0, 200, fill=C['lgrey'], width=2)
    d.ellipse((52, 50, 58, 56), fill=C['red'])
    return frame_out(im)

def wiki_doxxing():
    im, d = photo()
    d.rectangle((0, 0, PW, PH), fill=C['cork'])
    for _ in range(60): d.point((random.randrange(PW), random.randrange(PH)), fill=C['corkD'])
    f = A.face_nora(26, 26, 'paper'); paste(im, f, (42, 6))
    for (x, y, c) in ((8, 40, hx('#e6e0cc')), (74, 40, hx('#f0d9b5')), (40, 52, C['paper'])):
        d.line((55, 8, x + 12, y), fill=C['string'])
        d.rectangle((x, y, x + 24, y + 18), fill=c); d.rectangle((x, y, x + 24, y + 18), outline=C['out'])
        scribble(d, x + 3, y + 6, 18, C['inkL'], x); scribble(d, x + 3, y + 10, 14, C['inkL'], y)
    d.ellipse((53, 4, 57, 8), fill=C['red'])
    return frame_out(im)

def wiki_osint():
    im, d = photo()
    A.street_map(d, (0, 0, PW - 1, PH - 1), pin=(70, 40), seed=9)
    d.ellipse((24, 12, 66, 54), fill=(255, 255, 255, 60), outline=C['out'], width=3)
    d.line((60, 48, 80, 70), fill=C['out'], width=5); d.line((61, 49, 79, 69), fill=hx('#6e4a24'), width=3)
    return frame_out(im)

def wiki_vpn():
    im, d = photo()
    d.rectangle((0, 0, PW, PH), fill=hx('#2b3550'))
    for r in range(36, 6, -6): d.ellipse((55 - r, 40 - r * 0.7, 55 + r, 40 + r * 0.7), outline=hx('#3d4a6a'))
    d.ellipse((40, 26, 70, 56), fill=C['blue'], outline=C['out']); d.line((40, 41, 70, 41), fill=C['blueL']); d.ellipse((50, 26, 60, 56), outline=C['blueL'])
    d.polygon([(55, 8), (72, 14), (70, 30), (55, 38), (40, 30), (38, 14)], outline=C['yel'])
    text(d, 4, 70, 'FREE!!', C['yel'])
    for x in (12, 92): d.line((x, 60, x + 4, 66), fill=C['red'], width=2)                 # leaks
    return frame_out(im)

def wiki_twostep():
    im, d = photo()
    d.rectangle((0, 0, PW, PH), fill=hx('#e6e0cc'))
    d.rounded_rectangle((38, 6, 72, 76), 5, fill=C['out']); d.rectangle((41, 12, 69, 66), fill=hx('#a9cad6'))
    text(d, 43, 22, 'CODE:', C['ink']); text_big(d, 42, 32, '4471', C['ink'])
    d.ellipse((53, 69, 57, 73), fill=C['grey'])
    d.rectangle((78, 30, 102, 50), fill=C['out']); d.rectangle((80, 34, 100, 48), fill=C['yel'])
    d.arc((82, 22, 98, 40), 180, 360, fill=C['out'], width=3)
    return frame_out(im)

def wiki_moth():
    im, d = photo()
    dither_v(d, (0, 0, PW, PH), hx('#1b2033'), hx('#303849'))
    for r in range(30, 4, -2):
        d.ellipse((30 - r, 16 - r // 2, 30 + r, 16 + r // 2), fill=(240, 212, 138, 6 + (30 - r) * 3))
    d.ellipse((24, 10, 36, 22), fill=C['lamp0'])
    big = ascii_sprite(MOTH, moth_pal()).resize((45, 33), Image.NEAREST); outline(big, C['out']); paste(im, big, (50, 30))
    sm = ascii_sprite(MOTH2, moth_pal()); outline(sm, C['out']); paste(im, sm, (40, 20))
    return frame_out(im)

def wiki_court():
    im, d = photo()
    d.rectangle((0, 0, PW, PH), fill=hx('#e6e0cc'))
    d.rectangle((16, 20, 70, 74), fill=C['out']); d.rectangle((18, 22, 68, 72), fill=C['paper'])
    text(d, 22, 26, 'ORDER', C['ink'])
    for y in range(36, 64, 5): scribble(d, 22, y, 40, C['inkL'], y)
    d.ellipse((48, 60, 62, 70), outline=C['red'], width=2)
    d.rectangle((70, 30, 100, 40), fill=C['out']); d.rectangle((72, 32, 98, 38), fill=hx('#8a5a32'))     # gavel
    d.line((84, 40, 92, 66), fill=C['out'], width=4); d.line((84, 40, 92, 66), fill=hx('#a87a48'), width=2)
    return frame_out(im)

def wiki_dns():
    im, d = photo()
    d.rectangle((0, 0, PW, PH), fill=hx('#c9c0a8'))
    d.rectangle((0, 24, PW, 40), fill=C['out']); d.rectangle((0, 26, PW, 38), fill=C['chrome2'])
    d.rectangle((50, 20, 62, 44), fill=C['out']); d.rectangle((52, 22, 60, 42), fill=C['chrome3'])
    for (x, y, s) in ((54, 50, 'IP'), (60, 60, 'WWW'), (50, 70, 'DNS')):
        text(d, x, y, s, C['blue'])
    d.line((56, 44, 56, 48), fill=C['blue'])
    return frame_out(im)

# ------------------------------------------------------------------ endings
def end_door():
    im, d = photo()
    d.rectangle((0, 0, PW, PH), fill=hx('#6a5a4a'))
    d.rectangle((30, 0, 80, PH), fill=C['out']); d.rectangle((32, 0, 78, PH), fill=hx('#8a6a4a'))
    d.ellipse((44, 22, 66, 44), fill=C['out']); d.ellipse((46, 24, 64, 42), fill=hx('#1b2033'))     # peephole view
    d.ellipse((50, 28, 60, 40), fill=hx('#3a3a3a')); d.rectangle((50, 32, 60, 35), fill=hx('#4a5a6a'))  # helmet
    d.ellipse((70, 44, 74, 48), fill=C['gold'])
    return frame_out(im)

def end_watch():
    im, d = photo()
    d.rectangle((0, 0, PW, PH), fill=hx('#1d2a1e'))
    r = random.Random(3)
    for i in range(9):
        x, y = 4 + (i % 3) * 36, 4 + (i // 3) * 25
        d.rectangle((x, y, x + 32, y + 21), fill=C['out'])
        dither_v(d, (x + 1, y + 1, x + 31, y + 20), hx('#4d4436'), hx('#2a2620'))
        for _ in range(2):
            bx, by = r.randint(x + 3, x + 24), r.randint(y + 6, y + 15)
            d.rectangle((bx, by, bx + 4, by + 5), fill=r.choice((C['hood'], C['redD'], C['blueD'])))
    m = ascii_sprite(MOTH, moth_pal()); outline(m, C['out']); paste(im, m, (47, 33))
    return frame_out(im)

def end_sisters():
    im, d = photo()
    sky_day(d, (0, 0, PW, PH))
    d.rectangle((10, 10, 100, 70), fill=C['out']); d.rectangle((12, 12, 98, 68), fill=hx('#e8d8b8'))
    a = person(36, 50, C['nshirt'], hair=C['nhair']); b = person(36, 50, C['grn'], hair=hx('#8a4a2a'))
    paste(im, a, (22, 22)); paste(im, b, (52, 22))
    d = ImageDraw.Draw(im)
    d.rectangle((12, 60, 98, 68), fill=hx('#b78f62')); d.ellipse((70, 56, 84, 64), fill=hx('#e39a52'))
    return frame_out(im)

def end_bars():
    im = news_dorian().copy(); d = ImageDraw.Draw(im)
    for x in range(6, PW, 12): d.rectangle((x, 0, x + 3, PH), fill=hx('#3a3a40')); d.line((x, 0, x, PH), fill=hx('#6a6a70'))
    return im

# ------------------------------------------------------------------ chat avatar, door guest, map
def chat_avatar():
    im, d = layer(18, 17)
    d.rectangle((0, 0, 17, 16), fill=C['bg2'])
    m = ascii_sprite(MOTH, moth_pal()); paste(im, m, (1, 3))
    return im

def door_guest():
    """Elias at the door: motorbike helmet with the visor down, olive hoodie, backpack straps, a jar in his hand."""
    w, h = 120, 210
    im, d = layer(w, h)
    body, bd = layer(w, h)
    bd.rounded_rectangle((22, 92, 98, 210), 18, fill=C['hood'])
    bd.rounded_rectangle((22, 92, 48, 210), 12, fill=C['hoodL'])
    bd.rounded_rectangle((78, 96, 98, 210), 10, fill=C['hoodD'])
    bd.rectangle((44, 150, 76, 176), fill=C['hoodD'])                                  # pocket
    arm, ad = layer(w, h)
    ad.rounded_rectangle((84, 110, 104, 180), 8, fill=C['hoodD'])
    ad.ellipse((84, 172, 104, 190), fill=C['skin'])
    jar, jd = layer(w, h)
    jd.rounded_rectangle((82, 160, 104, 186), 3, fill=(200, 220, 230, 170)); jd.rectangle((82, 158, 104, 162), fill=C['gold'])
    head, hd = layer(w, h)
    hd.ellipse((30, 24, 90, 96), fill=hx('#2e2e34'))
    hd.ellipse((30, 24, 58, 90), fill=hx('#45454d'))
    hd.rounded_rectangle((36, 46, 86, 74), 10, fill=hx('#1a1c24'))                    # visor
    stack(im, body, head, arm, jar)
    d = ImageDraw.Draw(im)
    d.line((40, 50, 60, 48), fill=(160, 190, 210, 160), width=2)                         # visor glare
    d.line((36, 96, 30, 160), fill=C['out'], width=3); d.line((84, 96, 90, 140), fill=C['out'], width=3)  # backpack straps
    d.line((52, 98, 50, 130), fill=C['chrome1']); d.line((68, 98, 70, 130), fill=C['chrome1'])
    m = ascii_sprite(MOTH, moth_pal()).resize((12, 9), Image.NEAREST); paste(im, m, (87, 168))
    return im

def map_kestrel():
    im, d = layer(364, 107)
    A.street_map(d, (0, 0, 363, 106), seed=21)
    for x in range(0, 364, 60): d.line((x, 0, x + 30, 106), fill=C['white'], width=3)
    d.line((0, 50, 363, 56), fill=C['white'], width=5)
    d.rectangle((150, 38, 222, 48), fill=C['white']); text(d, 154, 40, 'KESTREL LANE', C['ink'])
    d.ellipse((240, 40, 250, 52), fill=C['red'], outline=C['out']); d.point((245, 45), fill=C['white'])
    d.rectangle((252, 38, 268, 46), fill=C['white']); text(d, 254, 40, '14', C['redD'])
    return im

# ------------------------------------------------------------------ web page backgrounds (376 x 157)
WW, WH = 376, 157

def web_darkboard():
    im, d = layer(WW, WH)
    d.rectangle((0, 0, WW, WH), fill=hx('#17131c'))
    d.rectangle((0, 0, WW, 26), fill=hx('#221c29')); d.line((0, 26, WW, 26), fill=C['redD'])
    text_big(d, 8, 8, 'DARKBOARD', C['red'])
    sk = ascii_sprite(MOTH, {'m': C['lgrey'], 'M': C['grey'], 'L': C['white'], 'e': C['red'], 'b': C['out'], '.': None})
    paste(im, sk, (86, 7))
    text(d, WW - 92, 11, 'ANONYMOUS SINCE 2009', C['grey'])
    # left nav: boards
    d.rectangle((6, 32, 80, 150), fill=hx('#1d1824')); d.rectangle((6, 32, 80, 150), outline=hx('#3a2f44'))
    for i, b in enumerate(('#JOBS', '#TOOLS', '#OSINT', '#LEAKS', '#OFFTOPIC', '#BANNED')):
        y = 38 + i * 13
        if i == 0: d.rectangle((8, y - 2, 78, y + 7), fill=hx('#3a2030'))
        text(d, 12, y, b, C['red'] if i == 0 else C['lgrey'])
    # thread panel (text is laid over it)
    d.rectangle((88, 32, 370, 150), fill=hx('#1d1824')); d.rectangle((88, 32, 370, 150), outline=hx('#3a2f44'))
    for y in range(52, 150, 24): d.line((90, y, 368, y), fill=hx('#2c2434'))
    return im

def ov(name, fn):
    """A picture used inside a page background: the generated replacement when there is one (art_override/web)."""
    im = fn()
    return A.override('web', name, im.size) or im

def web_h4ck():
    im, d = layer(WW, WH)
    d.rectangle((0, 0, WW, WH), fill=hx('#e9e5da'))
    d.rectangle((0, 0, WW, 22), fill=hx('#2b2b2b')); text_big(d, 8, 5, 'H4CK SCHOOL', C['yel'])
    d.rectangle((WW - 64, 6, WW - 8, 16), fill=C['red']); text(d, WW - 58, 9, 'SUBSCRIBE', C['white'])
    thumb = A.override('web', 'school_thumb', (110, 80))
    if thumb is not None:   # the generated video still, letterboxed into the player
        host = Image.new('RGBA', (170, 104), (12, 12, 14, 255)); t = thumb.resize((143, 104), Image.NEAREST); host.alpha_composite(t, (13, 0))
    else:
        host = A.host_frame(85, 52, True).resize((170, 104), Image.NEAREST)
    d.rectangle((6, 28, 178, 134), fill=C['out']); paste(im, host, (7, 29))
    d.polygon([(84, 70), (84, 92), (102, 81)], fill=(255, 255, 255, 180))
    d.rectangle((6, 138, 178, 141), fill=C['dgrey']); d.rectangle((6, 138, 110, 141), fill=C['red'])
    d.rectangle((186, 28, 370, 150), fill=C['white']); d.rectangle((186, 28, 370, 150), outline=C['lgrey'])
    return im

def web_freevpn():
    im, d = layer(WW, WH)
    for y in range(WH):
        c = (int(250 - y * 0.4), int(220 - y * 0.6), int(60 + y * 0.3), 255); d.line((0, y, WW, y), fill=c)
    text_big(d, 10, 8, 'FREEVPN', C['redD'])
    for i, s in enumerate(('100% FREE', 'NO LOGS*', 'FAST?')):
        d.ellipse((240 + i * 44, 4, 280 + i * 44, 30), fill=C['red'], outline=C['out']); text(d, 260 + i * 44 - text_w(s) // 2, 15, s, C['white'])
    d.rectangle((10, 36, 160, 150), fill=(255, 255, 255, 200)); d.rectangle((10, 36, 160, 150), outline=C['out'])
    paste(im, ov('wiki_vpn', wiki_vpn), (30, 50))
    d.rectangle((170, 36, 370, 150), fill=(255, 255, 255, 220)); d.rectangle((170, 36, 370, 150), outline=C['out'])
    text(d, 12, 140, '*SOME LOGS', C['inkL'])
    return im

def web_bakery():
    im, d = layer(WW, WH)
    d.rectangle((0, 0, WW, WH), fill=hx('#f6e6cf'))
    for i in range(0, WW, 16):
        d.rectangle((i, 0, i + 7, 18), fill=hx('#c0607a')); d.rectangle((i + 8, 0, i + 15, 18), fill=C['white'])
    d.line((0, 18, WW, 18), fill=C['out'])
    paste(im, ov('post_bakery', post_bakery), (14, 30)); paste(im, ov('post_cat', post_cat), (130, 30))
    d.rectangle((246, 26, 370, 150), fill=C['white']); d.rectangle((246, 26, 370, 150), outline=hx('#d9b98a'))
    d.rectangle((14, 116, 240, 150), fill=C['white']); d.rectangle((14, 116, 240, 150), outline=hx('#d9b98a'))
    return im

def web_poc():
    im, d = layer(WW, WH)
    d.rectangle((0, 0, WW, WH), fill=hx('#1d2a1e'))
    cx = 70
    d.ellipse((cx - 40, 30, cx + 40, 90), fill=hx('#c9b58a'), outline=C['out'])
    d.ellipse((cx - 18, 40, cx + 18, 80), fill=hx('#6b4a2a')); d.ellipse((cx - 8, 50, cx + 8, 70), fill=C['out'])
    d.point((cx - 4, 53), fill=C['white']); d.point((cx - 3, 53), fill=C['white'])
    s = 'P.O.C.'; text_big(d, cx - len(s) * 4, 100, s, hx('#c9b58a'))
    d.rectangle((150, 20, 368, 148), fill=hx('#16201a')); d.rectangle((150, 20, 368, 148), outline=hx('#3d4f3a'))
    return im

def web_pizza():
    im, d = layer(WW, WH)
    d.rectangle((0, 0, WW, WH), fill=hx('#f3e3c0'))
    for x in range(0, WW, 12):
        for y in range(0, 24, 12): d.rectangle((x + (y // 12 % 2) * 6, y, x + 5 + (y // 12 % 2) * 6, y + 5), fill=C['red'])
    d.rectangle((0, 24, WW, 26), fill=C['out'])
    text_big(d, 10, 32, 'PIZZA NOW', C['redD'])
    pz, pd = layer(120, 120)
    pd.ellipse((4, 4, 116, 116), fill=hx('#d79a4e')); pd.ellipse((12, 12, 108, 108), fill=hx('#e6c25a'))
    for (x, y) in ((30, 30), (70, 26), (50, 60), (80, 70), (30, 76), (60, 92)): pd.ellipse((x, y, x + 14, y + 14), fill=C['red'])
    outline(pz, C['out']); paste(im, pz, (20, 40))
    d.rectangle((160, 34, 370, 150), fill=C['white']); d.rectangle((160, 34, 370, 150), outline=C['out'])
    return im

# ------------------------------------------------------------------ build
IMAGES = {
    'news_intruder': news_intruder, 'news_empty': news_empty, 'news_dorian': news_dorian, 'news_arrest': news_arrest,
    'news_turnin': news_turnin, 'nora_profile': nora_profile, 'post_cat': post_cat, 'post_bakery': post_bakery,
    'post_bike': post_bike, 'wiki_social': wiki_social, 'wiki_phishing': wiki_phishing, 'wiki_doxxing': wiki_doxxing,
    'wiki_osint': wiki_osint, 'wiki_vpn': wiki_vpn, 'wiki_twostep': wiki_twostep, 'wiki_moth': wiki_moth,
    'wiki_court': wiki_court, 'wiki_dns': wiki_dns, 'end_door': end_door, 'end_watch': end_watch,
    'end_sisters': end_sisters, 'end_bars': end_bars, 'chat_avatar': chat_avatar, 'door_guest': door_guest,
    'map_kestrel': map_kestrel, 'web_darkboard': web_darkboard, 'web_h4ck': web_h4ck, 'web_freevpn': web_freevpn,
    'web_bakery': web_bakery, 'web_poc': web_poc, 'web_pizza': web_pizza,
    'school_thumb': lambda: frame_out(A.host_frame(PW, PH, True)),
    'moth_ad': lambda: (lambda im: (paste(im, (lambda s: (outline(s, C['out']), s)[1])(ascii_sprite(MOTH, moth_pal()).resize((60, 44), Image.NEAREST)), (25, 18)), frame_out(im))[1])(
        (lambda: (lambda im, d: (dither_v(d, (0, 0, PW, PH), hx('#17131c'), hx('#3a2030')), im)[1])(*layer(PW, PH)))()),
}

def build(out):
    random.seed(1)
    os.makedirs(out, exist_ok=True)
    for name, fn in IMAGES.items():
        im = fn()
        im = A.override('web', name, im.size) or im
        im.save(os.path.join(out, name + '.png'))
    return sorted(IMAGES)

if __name__ == '__main__':
    import sys
    print(build(sys.argv[1]))

# ------------------------------------------------------------------ Elias' abandoned Metayou profile
def elias_profile():
    im, d = photo()
    f = A.face_elias(80, 57); paste(im, f, (15, 12)); dither_v(d, (0, 0, PW, 11), C['bg2'], C['bg1'])
    d.rectangle((0, 69, PW, PH), fill=C['bg1'])
    return frame_out(im)

def post_byte():
    im, d = photo()
    d.rectangle((0, 0, PW, PH), fill=C['bg2'])
    d.rectangle((6, 44, 104, 74), fill=C['out']); d.rectangle((8, 46, 102, 72), fill=C['chrome2'])     # keyboard
    for y in range(48, 70, 6):
        for x in range(10, 100, 7): d.rectangle((x, y, x + 5, y + 4), fill=C['chrome1'])
    cat, cd = layer(PW, PH)
    cd.ellipse((30, 28, 84, 62), fill=hx('#26222a')); cd.ellipse((24, 14, 52, 40), fill=hx('#26222a'))
    cd.polygon([(26, 20), (28, 6), (36, 16)], fill=hx('#26222a')); cd.polygon([(42, 16), (50, 6), (52, 20)], fill=hx('#26222a'))
    outline(cat, C['lgrey']); paste(im, cat, (0, 0))
    d = ImageDraw.Draw(im); d.point((33, 26), fill=C['yel']); d.point((44, 26), fill=C['yel'])
    return frame_out(im)

def post_gas():
    im, d = photo()
    sky_night(d, (0, 0, PW, PH))
    d.rectangle((0, 62, PW, PH), fill=hx('#2c2a30'))
    d.rectangle((4, 14, 106, 22), fill=C['out']); d.rectangle((6, 16, 104, 20), fill=C['red'])        # canopy
    d.rectangle((14, 22, 18, 62), fill=C['lgrey']); d.rectangle((92, 22, 96, 62), fill=C['lgrey'])
    d.rectangle((40, 34, 56, 62), fill=C['out']); d.rectangle((42, 36, 54, 60), fill=C['chrome1']); d.rectangle((44, 38, 52, 44), fill=C['termB'])
    d.rectangle((62, 30, 100, 62), fill=C['out']); d.rectangle((64, 32, 98, 60), fill=hx('#e8d8a8'))     # kiosk lit
    kid = person(16, 22, C['hood'], hair=C['hair']); paste(im, kid, (74, 36))
    for x in range(6, 104, 8): d.point((x, 21), fill=C['lamp0'])
    return frame_out(im)

def post_cake():
    im, d = photo()
    d.rectangle((0, 0, PW, PH), fill=hx('#e6d6b8')); d.rectangle((0, 56, PW, PH), fill=hx('#b78f62'))
    cake, kd = layer(PW, PH)
    kd.rectangle((30, 36, 80, 62), fill=hx('#f0e0d0')); kd.rectangle((30, 36, 80, 42), fill=hx('#d07a8a'))
    outline(cake, C['out']); paste(im, cake, (0, 0))
    d = ImageDraw.Draw(im)
    for x in (40, 55, 70): d.rectangle((x, 28, x + 1, 36), fill=C['blue']); d.point((x, 26), fill=C['yel']); d.point((x + 1, 25), fill=C['lamp0'])
    text(d, 40, 48, 'MOM', C['redD'])
    return frame_out(im)

IMAGES.update({'elias_profile': elias_profile, 'post_byte': post_byte, 'post_gas': post_gas, 'post_cake': post_cake})

# ------------------------------------------------------------------ v2.1: generic "Crow" search result (a bird on a wire)
def wiki_crow():
    im, d = photo()
    sky_day(d, (0, 0, PW, PH))
    d.line((0, 52, PW, 46), fill=C['out'], width=1)                      # power line
    b = hx('#1e1f26'); hi = hx('#3a3d4a')
    d.ellipse((40, 28, 70, 48), fill=b)                                  # body
    d.ellipse((62, 22, 76, 34), fill=b)                                  # head
    d.polygon([(75, 27), (84, 29), (75, 31)], fill=hx('#2a2a30'))        # beak
    d.polygon([(42, 40), (24, 50), (44, 46)], fill=b)                    # tail
    d.arc((44, 30, 66, 46), 200, 320, fill=hi)                           # wing highlight
    d.point((70, 26), fill=hx('#e8e0c0'))                                # eye
    d.line((52, 47, 52, 50), fill=b); d.line((58, 47, 58, 50), fill=b)   # feet
    return frame_out(im)
IMAGES['wiki_crow'] = wiki_crow

def news_tipline():
    """Day-2 news: the police tip line (placeholder until the generated picture arrives)."""
    im, d = photo()
    dither_v(d, (0, 0, PW, PH), hx('#2f4a78'), hx('#1c2c4c'))
    d.rectangle((14, 18, 96, 62), fill=C['white']); d.rectangle((14, 18, 96, 62), outline=C['out'])
    d.rectangle((14, 18, 96, 28), fill=hx('#2f4a78')); text(d, 20, 21, 'CITY POLICE', C['white'])
    text(d, 30, 38, '555-0110', C['ink']); text(d, 22, 50, 'TIP LINE', C['red'])
    return frame_out(im)
IMAGES['news_tipline'] = news_tipline

IMAGES['wiki_stalking'] = wiki_doxxing   # "hiding" encyclopedia page; generated replacement in art_override/web
# v2.5 placeholders until the art arrives (art_override/web/<name>.png replaces them):
# the wedding notice reuses Nora's portrait, the M0TH band article the moth picture
IMAGES['news_wedding'] = lambda: (A.override('web', 'nora_profile', (110, 80)) or nora_profile()).convert('RGBA')
IMAGES['wiki_band'] = lambda: (A.override('web', 'wiki_moth', (110, 80)) or wiki_moth()).convert('RGBA')
