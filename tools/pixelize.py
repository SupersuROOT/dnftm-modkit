"""
Turns a large generated picture into game pixel art of an exact size.

    python -I pixelize.py <source.png> <out.png> <W>x<H> [colours=32] [--alpha] [--palette <palette.png>] [--fit]

Centre-crops the source to the target aspect ratio (or, with --fit, pads it with transparency instead of
cropping, for sprites whose source is not the same shape), scales it down with box filtering (each game pixel is
the average of its block), reduces it to a fixed number of colours, and makes edges hard. With --alpha the
transparency is kept as fully opaque / fully transparent (threshold 50%), for sprites.

--palette <png>: use exactly the colours of that image instead of picking new ones. Convert one finished frame
of a character first, then pass it as the palette for all the other frames of the same character, so the
colours stay identical across an animation.
"""
import sys
from PIL import Image

def pixelize(src, size, colours=32, alpha=False, palette=None, fit=False):
    im = Image.open(src).convert('RGBA')
    W, H = size
    r = W / H
    if fit:
        if im.width / im.height > r: nh = round(im.width / r); canvas = Image.new('RGBA', (im.width, nh)); canvas.paste(im, (0, nh - im.height))
        else: nw = round(im.height * r); canvas = Image.new('RGBA', (nw, im.height)); canvas.paste(im, ((nw - im.width) // 2, 0))
        im = canvas
    elif im.width / im.height > r:
        nw = round(im.height * r); x = (im.width - nw) // 2; im = im.crop((x, 0, x + nw, im.height))
    else:
        nh = round(im.width / r); y = (im.height - nh) // 2; im = im.crop((0, y, im.width, y + nh))
    small = im.resize((W, H), Image.BOX)
    a = small.getchannel('A').point(lambda v: 255 if v >= 128 else 0)
    rgb = small.convert('RGB')
    if palette:
        cols = sorted({c for c in Image.open(palette).convert('RGBA').getdata() if c[3] == 255})
        cols = [c[:3] for c in cols][:256]
        pal = Image.new('P', (1, 1)); flat = [v for c in cols for v in c]
        pal.putpalette(flat + flat[:3] * (256 - len(cols)))
        rgb = rgb.quantize(palette=pal, dither=Image.Dither.NONE).convert('RGB')
    else:
        rgb = rgb.quantize(colours, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).convert('RGB')
    out = rgb.convert('RGBA')
    if alpha: out.putalpha(a)
    return out

if __name__ == '__main__':
    argv = sys.argv[1:]
    pal = None
    if '--palette' in argv:
        i = argv.index('--palette'); pal = argv[i + 1]; del argv[i:i + 2]
    args = [a for a in argv if not a.startswith('--')]
    w, h = map(int, args[2].lower().split('x'))
    pixelize(args[0], (w, h), int(args[3]) if len(args) > 3 else 32, '--alpha' in argv, pal, '--fit' in argv).save(args[1])
    print('wrote', args[1], w, 'x', h)
