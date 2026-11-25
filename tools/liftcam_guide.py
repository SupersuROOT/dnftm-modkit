"""
Layout guide and pose references for the "Going Down" art brief (for Codex / image generation).

    python -I liftcam_guide.py <out folder>

Writes:
  layout_guide.png        the camera view (3x) with the door box, display, standing spots and sprite cells marked
  layout_clean.png        the same view without marks (perspective reference for car.png)
  poses/<name>.png        every pose of every character as the camera sees it, at sprite size (64x100, 4x),
                          rendered with simple 3D shapes: size / angle / silhouette guide only, NOT the style
  spec.json               names and sizes of every deliverable (also copied to mod/art_override/liftcam)
"""
import json, math, os, sys
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import liftcam_render as R
import liftcam_car as Car
import liftcam_people as Pp
from liftcam_people import Body, SLOTS, MID, DOOR, yaw_to_cam

W, H = R.W, R.H
CELL = (64, 100)            # character frames
FEET = (32, 96)             # feet point inside a character frame
DOOR_BOX = (84, 10, 172, 152)   # region the door variants are cut from (x0, y0, x1, y1)
DISPLAY = (112, 6, 131, 16)
def P(p): return tuple(round(v) for v in R.project(p))
SPOT = {'door': P((DOOR[0], 0, DOOR[1])), 'L': P((SLOTS['L'][0], 0, SLOTS['L'][1])), 'R': P((SLOTS['R'][0], 0, SLOTS['R'][1])),
        'C': P((SLOTS['C'][0], 0, SLOTS['C'][1])), 'midL': P((MID['L'][0], 0, MID['L'][1])), 'midR': P((MID['R'][0], 0, MID['R'][1]))}
DOG = (112, 138)
SIT_DY = 22                 # sitting frames are drawn higher in the cell: in the game they are placed 22 px lower

STD = ['back', 'back_talk', 'front', 'front_talk', 'walk_f1', 'walk_f2', 'walk_b1', 'walk_b2']
EXTRA = {
    'pruitt': ['sit', 'sit_talk'],
    'haldane': ['wave', 'wave_talk', 'sit', 'sit_talk'],
    'rafi': ['nobox', 'nobox_talk', 'sit', 'sit_talk'],
    'mila': ['dance1', 'dance2', 'dance3', 'dance4', 'fall', 'fall_talk', 'grimace1', 'grimace2'],
    'gus': ['mop1', 'mop2'],
    'toby': ['jump1', 'jump2', 'wave1', 'wave2'],
    'dev': ['carry', 'carry_talk', 'carry_walk_f1', 'carry_walk_f2', 'carry_walk_b1', 'carry_walk_b2'],
    'priya': ['carry', 'carry_talk', 'carry_walk_f1', 'carry_walk_f2', 'carry_walk_b1', 'carry_walk_b2'],
}
CHARS = ['pruitt', 'haldane', 'rafi', 'mila', 'gus', 'toby', 'mom', 'grey', 'tech', 'dev', 'priya']
def poses(name):
    ps = list(STD)
    if name == 'grey': ps = ['back', 'walk_f1', 'walk_f2', 'walk_b1', 'walk_b2']
    return ps + EXTRA.get(name, [])

def body_for(name, pose):
    """The 3D stand-in for a pose, placed where it is used (C spot for standing poses)."""
    base = {'haldane': 'phone', 'rafi': 'box'}.get(name, 'down')
    x, z = SLOTS['C']; yaw = 0.0; arms = base; talk = False; walk = 0; sit = False; up = False
    if pose.startswith('carry'): arms = 'carry'; pose = pose.replace('carry_', '').replace('carry', 'back')
    if pose in ('front', 'front_talk', 'wave', 'wave_talk', 'grimace1', 'grimace2', 'wave1', 'wave2', 'sit', 'sit_talk', 'fall', 'fall_talk', 'mop1', 'mop2'):
        yaw = yaw_to_cam(x, z); up = True
    if pose.startswith('walk_f'): x, z = DOOR; yaw = yaw_to_cam(x, z); walk = 1 if pose.endswith('1') else -1
    if pose.startswith('walk_b'): x, z = MID['L']; walk = 1 if pose.endswith('1') else -1
    if pose.endswith('talk') or pose in ('grimace1', 'dance4'): talk = True
    if pose.startswith('sit') or pose.startswith('fall'): sit = True
    if pose.startswith('nobox'): arms = 'down'
    if pose.startswith('wave') or pose.startswith('grimace'): arms = 'wave'
    if pose == 'dance1': arms = 'upL'
    if pose in ('dance2', 'dance4', 'jump1'): arms = 'up'
    if pose in ('dance3', 'jump2'): arms = 'upR'
    if pose.startswith('mop'): arms = 'mop'
    return Body(name, x, z, yaw=yaw, arms=arms, talk=talk, walk=walk, sit=sit, look_up=up), (x, z)

def cell_of(img, feet):
    fx, fy = feet
    box = (fx - FEET[0], fy - FEET[1], fx - FEET[0] + CELL[0], fy - FEET[1] + CELL[1])
    out = Image.new('RGBA', CELL, (0, 0, 0, 0))
    out.alpha_composite(img.crop(box))
    return out

def font(size=12):
    for f in ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', '/usr/share/fonts/dejavu/DejaVuSans.ttf'):
        if os.path.isfile(f): return ImageFont.truetype(f, size)
    return ImageFont.load_default()

def main(out):
    os.makedirs(os.path.join(out, 'poses'), exist_ok=True)
    bg = Car.draw_car('day')
    bg.resize((W * 3, H * 3), Image.NEAREST).save(os.path.join(out, 'layout_clean.png'))
    # ---- layout guide
    g = bg.copy()
    sample = Image.new('RGBA', (W, H)); sample.alpha_composite(Pp.render([Body('haldane', *SLOTS['L'], arms='phone'), Body('mila', *SLOTS['R'])]))
    g.alpha_composite(sample)
    g = g.resize((W * 3, H * 3), Image.NEAREST); d = ImageDraw.Draw(g); f = font(13)
    def box(b, col, label):
        d.rectangle([v * 3 for v in b], outline=col, width=2); d.text((b[0] * 3 + 4, b[1] * 3 + 2), label, fill=col, font=f)
    box(DOOR_BOX, (255, 220, 0), 'DOOR_BOX (doors variants are cut from here)')
    box(DISPLAY, (255, 80, 80), 'DISPLAY')
    for k, (fx, fy) in SPOT.items():
        col = {'door': (0, 220, 255), 'L': (90, 255, 90), 'R': (90, 255, 90), 'C': (90, 255, 90)}.get(k, (200, 140, 255))
        b = (fx - FEET[0], fy - FEET[1], fx - FEET[0] + CELL[0], fy - FEET[1] + CELL[1])
        d.rectangle([v * 3 for v in b], outline=col, width=1)
        d.ellipse((fx * 3 - 5, fy * 3 - 5, fx * 3 + 5, fy * 3 + 5), fill=col)
        d.text((fx * 3 + 8, fy * 3 - 8), '%s feet (%d,%d)' % (k, fx, fy), fill=col, font=f)
    d.ellipse((DOG[0] * 3 - 5, DOG[1] * 3 - 5, DOG[0] * 3 + 5, DOG[1] * 3 + 5), fill=(255, 140, 0))
    d.text((DOG[0] * 3 - 70, DOG[1] * 3 + 6), 'dog (%d,%d)' % DOG, fill=(255, 140, 0), font=f)
    d.rectangle((0, (H - 22) * 3, 70 * 3, H * 3 - 1), outline=(255, 255, 255), width=2)
    d.text((6, (H - 20) * 3), 'keep dark: game writes RECORDING here', fill=(255, 255, 255), font=f)
    g.save(os.path.join(out, 'layout_guide.png'))
    # ---- pose references
    spec = {'bg/car': {'size': [W, H], 'transparent': False}}
    for v in ('door_open1', 'door_open2', 'door_open', 'door_pried', 'door_sign'): spec['bg/' + v] = {'size': [W, H], 'transparent': False}
    for name in CHARS:
        ps = poses(name)
        cols = 8; rows = (len(ps) + cols - 1) // cols
        sh = Image.new('RGBA', (cols * (CELL[0] + 6), rows * (CELL[1] + 18)), (150, 150, 150, 255)); sd = ImageDraw.Draw(sh)
        for i, pose in enumerate(ps):
            b, (x, z) = body_for(name, pose)
            img = Pp.render([b])
            fx, fy = P((x, 0, z))
            c = cell_of(img, (fx, fy + SIT_DY if pose.startswith(('sit', 'fall')) else fy))
            X, Y = (i % cols) * (CELL[0] + 6), (i // cols) * (CELL[1] + 18)
            sh.alpha_composite(c, (X, Y + 16)); sd.text((X + 1, Y + 2), pose, fill=(0, 0, 0), font=font(10))
            spec['people/%s/%s' % (name, pose)] = {'size': list(CELL), 'transparent': True}
        sh.resize((sh.width * 3, sh.height * 3), Image.NEAREST).save(os.path.join(out, 'poses', name + '.png'))
    for k in ('sit', 'walk1', 'walk2', 'sniff', 'sleep', 'bark'): spec['people/dog/' + k] = {'size': [28, 24], 'transparent': True}
    spec['props/bucket'] = {'size': [20, 18], 'transparent': True}
    spec['props/toolbox'] = {'size': [26, 16], 'transparent': True}
    spec['props/wardrobe'] = {'size': [120, 70], 'transparent': True}
    for k in ('news_contract', 'news_shutdown', 'news_stairs', 'end_dark', 'end_viral'): spec['web/' + k] = {'size': [110, 80], 'transparent': False}
    json.dump(spec, open(os.path.join(out, 'spec.json'), 'w'), indent=1)
    print(len(spec), 'deliverables;', 'spots', SPOT)

if __name__ == '__main__':
    main(sys.argv[1])
