"""
Newspaper and ending pictures for the "Going Down" cage (110 x 80, loaded as "mods/LiftCam/web/<name>"),
in the same flat-shaded, colour-outlined style as the cage art.
Replacement art: mod/art_override/liftcam/web/<name>.png (exact size or an integer multiple).
"""
import os
from PIL import Image, ImageDraw
import liftcam_art as A
from liftcam_art import C, new, text, text_w, paint, ell, rect, poly, dk, lt, hx, override

PW, PH = 110, 80

def frame(im):
    ImageDraw.Draw(im).rectangle((0, 0, im.width - 1, im.height - 1), outline=C['black']); return im

def lobby(im, sign=False, tape=False):
    """Front view of the elevator doors in the ground-floor lobby."""
    paint(im, [rect(0, 0, PW, 60)], C['cream'], C['cream'], None, C['paperD'], outline=False)
    d = ImageDraw.Draw(im)
    for x in range(0, PW, 14): d.line((x, 0, x, 58), fill=C['paperD'])
    paint(im, [rect(0, 60, PW, PH)], C['floor'], C['floorD'], None, C['floorDD'], outline=False, split=0.7)
    paint(im, [rect(28, 6, 82, 63)], C['steelL'], C['steel'], None, C['steelDD'])
    paint(im, [rect(33, 14, 54, 63)], C['steel'], C['steelD'], C['steelL'], C['steelDD'], split=0.8)
    paint(im, [rect(56, 14, 77, 63)], C['steel'], C['steelD'], C['steelL'], C['steelDD'], split=0.8)
    paint(im, [rect(46, 7, 64, 12)], C['lcd'], None, None, C['black'])
    if tape:
        for y, s in ((28, 1), (46, -1)):
            d.line((22, y - 6 * s, 88, y + 6 * s), fill=C['yel'], width=4)
            for x in range(24, 88, 8): d.line((x, y - 6 * s + (x - 22) * 12 * s // 66, x + 3, y - 6 * s + (x - 22) * 12 * s // 66), fill=C['black'], width=2)
    if sign:
        paint(im, [rect(38, 28, 72, 44)], C['white'], C['paper'], None, C['red'], split=0.9)
        text(d, 43, 31, 'OUT OF', C['red']); text(d, 45, 37, 'ORDER', C['red'])

def news_contract():
    im = new(PW, PH, C['cream'])
    paint(im, [rect(0, 0, PW, 50)], hx('#9fc0dc'), hx('#9fc0dc'), None, hx('#9fc0dc'), outline=False)
    paint(im, [poly((8, 18), (55, 3), (102, 18))], C['cream'], C['paperD'], None, C['paperD'])
    paint(im, [rect(14, 18, 96, 52)], C['paper'], C['paperD'], None, C['paperD'])
    for x in range(20, 92, 12): paint(im, [rect(x, 22, x + 5, 52)], C['white'], C['paper'], None, C['paperD'])
    paint(im, [rect(0, 52, PW, PH)], C['greyD'], dk(C['greyD']), None, dk(C['greyD']), outline=False)
    for cx, col in ((32, C['navy']), (78, C['charcoal'])):
        paint(im, [ell(cx, 76, 15, 14)], col, dk(col, 0.82), lt(col), dk(col, 0.55))
        paint(im, [ell(cx, 52, 7, 8)], C['skin'], C['skinS'], None, C['skinD'])
        paint(im, [ell(cx, 47, 7, 4)], C['hairBr'], dk(C['hairBr']), None, dk(C['hairBr'], 0.5))
    paint(im, [rect(44, 62, 66, 66)], C['skin'], C['skinS'], None, C['skinD'])
    paint(im, [rect(60, 68, 94, 77)], C['white'], C['paper'], None, C['blueD'] if 'blueD' in C else C['navy'])
    text(ImageDraw.Draw(im), 63, 70, 'UPRIGHT', C['navy'])
    return frame(im)

def news_shutdown():
    im = new(PW, PH); lobby(im, tape=True)
    d = ImageDraw.Draw(im)
    d.polygon([(96, 6), (110, 0), (110, 44)], fill=(255, 238, 180, 200))
    paint(im, [ell(14, 72, 11, 9)], C['red'], C['redD'], C['redL'], dk(C['redD'], 0.7))      # firefighter helmet
    paint(im, [rect(4, 72, 24, 76)], C['redD'], None, None, dk(C['redD'], 0.7))
    return frame(im)

def news_stairs():
    im = new(PW, PH, C['greyL'])
    for i in range(8):
        y = 74 - i * 9; x = 6 + i * 12
        paint(im, [rect(x, y, x + 44, y + 9)], C['grey'], C['greyD'], C['greyL'], C['greyD'], split=0.9)
    ImageDraw.Draw(im).line((8, 42, 104, 2), fill=C['brass'], width=2)
    paint(im, [ell(60, 46, 11, 14)], C['mustard'], dk(C['mustard'], 0.82), lt(C['mustard']), dk(C['mustard'], 0.55))   # Mrs Pruitt
    paint(im, [ell(60, 30, 9, 4)], C['pink'], dk(C['pink'], 0.82), None, dk(C['pink'], 0.55))
    paint(im, [ell(60, 24, 6, 7)], C['skin'], C['skinS'], None, C['skinD'])
    paint(im, [ell(60 + x, 20 + y, 3.5, 3.5) for x, y in ((-5, -2), (0, -5), (5, -2), (-6, 2), (6, 2))], C['lilac'], dk(C['lilac'], 0.82), None, dk(C['lilac'], 0.55))
    paint(im, [ell(67, 42, 7, 5)], C['white'], hx('#cfc6b6'), None, hx('#8f877a'))                        # the dog in her arms
    paint(im, [ell(72, 37, 4, 4)], C['white'], hx('#cfc6b6'), None, hx('#8f877a'))
    ImageDraw.Draw(im).point((73, 37), fill=C['black'])
    paint(im, [rect(54, 58, 66, 66)], hx('#5d6f8f'), dk(hx('#5d6f8f')), None, dk(hx('#5d6f8f'), 0.55))
    return frame(im)

def end_dark():
    im = new(PW, PH); lobby(im, sign=True)
    px = im.load()
    for y in range(PH):
        for x in range(PW):
            r, g, b, a = px[x, y]; px[x, y] = (r // 4 + 2, g // 4 + 2, b // 3 + 4, 255)
    d = ImageDraw.Draw(im)
    d.line((55, 14, 55, 63), fill=(92, 88, 72)); d.rectangle((38, 28, 72, 44), outline=(124, 44, 36))
    return frame(im)

def end_viral():
    im = new(PW, PH, C['navy'])
    paint(im, [rect(30, 3, 80, 77)], C['black'], C['black'], None, C['greyD'])
    paint(im, [rect(33, 9, 77, 70)], C['wood'], C['woodD'], None, C['woodDD'], split=0.85)
    paint(im, [rect(44, 9, 66, 30)], C['steel'], C['steelD'], None, C['steelDD'])
    paint(im, [ell(55, 66, 20, 12)], C['teal'], dk(C['teal'], 0.82), lt(C['teal']), dk(C['teal'], 0.55))     # tiny Mila from above
    paint(im, [ell(55, 50, 9, 10)], C['hairDk'], dk(C['hairDk'], 0.8), lt(C['hairDk'], 1.4), C['black'])
    for side in (-1, 1): paint(im, [ell(55 + side * 9, 51, 3, 4)], C['redL'], C['red'], None, C['black'])
    for side in (-1, 1): paint(im, [poly((55 + side * 16, 60), (55 + side * 20, 60), (55 + side * 14, 36), (55 + side * 11, 36))], C['teal'], dk(C['teal'], 0.82), None, dk(C['teal'], 0.55))
    d = ImageDraw.Draw(im)
    d.polygon([(51, 40), (51, 52), (61, 46)], fill=(255, 255, 255, 220))
    for i, x in enumerate((8, 16, 88, 96, 12, 92)):
        y = 12 + i * 10
        paint(im, [poly((x, y + 2), (x + 3, y), (x + 6, y + 2), (x + 3, y + 6))], C['redL'], C['red'], None, C['redD'])
    text(d, 35, 72, '9.8M', C['white'])
    return frame(im)

def build(out):
    os.makedirs(out, exist_ok=True)
    spec = {}
    for name, fn in (('news_contract', news_contract), ('news_shutdown', news_shutdown), ('news_stairs', news_stairs),
                     ('end_dark', end_dark)):
        im = fn().convert('RGBA')
        assert im.size == (PW, PH), (name, im.size)
        im = override('web', name, im.size) or im
        p = os.path.join(out, name + '.png'); im.save(p)
        spec['web/' + name] = {'size': [PW, PH], 'transparent': False, 'current': p}
    return spec
