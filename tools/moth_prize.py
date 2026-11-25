"""
The day-7 gift: "Moth in a jar". The game shows a prize as its own object on the prize shelf (ModLoader 0.5.10
"prizes" copies an original one) with three pictures:
  web/prize_jar.png        shelf picture (24x32)
  web/prize_jar_sel.png    the picture the shelf shows: the same with one more 1 px dark outline (26x34)
  web/prize_jar_popup.png  the info popup (289x183, the game's popup sprite size): the game's grey panel with the prize drawn large on the left,
                           drawn from its bottom-left corner like the game's popups
Placeholders drawn here; art_override/prize/<name>.png (same size) replaces them.
"""
import os
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
OVERRIDE = os.path.join(HERE, '..', 'art_override', 'prize')
SIZES = {'prize_jar': (24, 32), 'prize_jar_sel': (26, 34), 'prize_jar_popup': (289, 183)}

INK = (40, 34, 40, 255); GLASS = (168, 200, 206, 255); GLASS_D = (120, 156, 166, 255); SHINE = (236, 248, 250, 255)
LID = (150, 150, 158, 255); LID_D = (96, 96, 106, 255); WING = (222, 204, 160, 255); WING_D = (170, 146, 104, 255)
BODY = (96, 76, 60, 255); PAPER = (240, 232, 204, 255)

def jar(scale):
    """The jar at 1x (24x32) or larger, as flat pixel art with a dark outline."""
    w, h = 24, 32
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rectangle((4, 7, 19, 30), fill=GLASS, outline=INK)                  # glass body
    d.rectangle((5, 25, 18, 29), fill=GLASS_D)                            # darker bottom
    d.rectangle((6, 2, 17, 6), fill=LID, outline=INK)                     # lid
    d.line((7, 5, 16, 5), fill=LID_D)
    d.line((6, 9, 6, 22), fill=SHINE); d.point((7, 9), fill=SHINE)       # glass highlight
    # the moth inside: two wings and a body
    d.polygon([(11, 15), (7, 12), (7, 19)], fill=WING, outline=WING_D)
    d.polygon([(12, 15), (16, 12), (16, 19)], fill=WING, outline=WING_D)
    d.line((11, 13, 11, 19), fill=BODY); d.line((12, 13, 12, 19), fill=BODY)
    d.rectangle((13, 22, 18, 25), fill=PAPER, outline=INK)                # the note "Now you know."
    if scale != 1: im = im.resize((w * scale, h * scale), Image.NEAREST)
    return im

def outline(im, color=(255, 255, 255, 255)):
    """The game's hover version: 1 px larger on every side, white around the opaque pixels."""
    w, h = im.size
    out = Image.new('RGBA', (w + 2, h + 2), (0, 0, 0, 0)); a = im.split()[3]
    sil = Image.new('RGBA', im.size, color); sil.putalpha(a)
    for dx, dy in ((0, 1), (2, 1), (1, 0), (1, 2)): out.alpha_composite(sil, (dx, dy))
    out.alpha_composite(im, (1, 1))
    return out

def popup():
    """289x183, the size of the game's popup sprite, drawn from its bottom-left corner. Measured in game: the title
    sits at about (199, 62), the description at x 140..258 / y 69..92, the price at y 114 and the buttons at
    x 196..259 / y 124..141 of this canvas, so the panel is x 62..272, y 50..160 (white edge, fill, 2 px light inner
    border, 1 px dark shadow right and bottom). The prize is drawn large on the left over the panel's edge."""
    W, H = SIZES['prize_jar_popup']
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = 62, 50, 272, 160
    d.rectangle((x0 + 1, y0 + 1, x1 + 1, y1 + 1), fill=(0, 0, 0, 153))   # shadow
    d.rectangle((x0, y0, x1, y1), fill=(255, 255, 255, 255))
    d.rectangle((x0 + 1, y0 + 1, x1 - 1, y1 - 1), fill=(62, 67, 65, 255))
    d.rectangle((x0 + 2, y0 + 2, x1 - 2, y1 - 2), outline=(112, 119, 117, 255))
    d.rectangle((x0 + 3, y0 + 3, x1 - 3, y1 - 3), outline=(112, 119, 117, 255))
    d.rectangle((x0 + 4, y0 + 4, x1 - 4, y1 - 4), fill=(62, 67, 65, 255))
    big = outline(jar(3))                                                 # 74x98
    im.alpha_composite(big, (10, 64))
    return im

def build(outdir):
    os.makedirs(outdir, exist_ok=True)
    # the shelf object shows the 'selected' picture: like the game's (CocaSeleccionado...) one more dark outline
    made = {'prize_jar': jar(1), 'prize_jar_sel': outline(jar(1), (58, 44, 50, 255)), 'prize_jar_popup': popup()}
    for name, im in made.items():
        ov = os.path.join(OVERRIDE, name + '.png')
        if os.path.exists(ov):
            o = Image.open(ov).convert('RGBA')
            if o.size == SIZES[name]: im = o; print('override prize', name)
            else: print('WARNING: %s is %dx%d, needs %dx%d; using the placeholder' % (ov, o.width, o.height, *SIZES[name]))
        im.save(os.path.join(outdir, name + '.png'))
