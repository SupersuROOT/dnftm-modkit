"""
Story data for the "Going Down" cage (id liftCam): a CCTV camera in the elevator of Larkspur Court.
A fake cage: people come and go every day, but there is not a single keyword to collect.
Day 6 the elevator gets stuck with two residents inside; day 7 it is sealed and the camera only shows a dark
car and signal glitches. The news explains why: the maintenance firm UpRight Lifts faked inspections.

Variables: none. The cage cannot be recorded at all: the game sets storyController.recordable from the cage
data's "recordings" table (setStory: recordable = ToBool(storyData["recordings"])), and this cage has none.
"""
import os
import liftcam_sprites as Sp

CAGE = 'liftCam'
TXT = []   # (en, zh)

def T(en, zh):
    TXT.append((en, zh))
    return '%s_%d~%s' % (CAGE, len(TXT), en)

H = 174
DOOR_TL = (Sp.DOOR_BOX[0], Sp.DOOR_BOX[1])
DISPLAY_TL = (Sp.DISPLAY_BOX[0], Sp.DISPLAY_BOX[1])
SFX_TL = (121, 6)       # elevator noises come from the display
OUT_TL = (126, 60)      # voices behind the closed doors (day 7)

# Where people stand (feet, image coordinates). The camera hangs in the back-left corner of the car:
# L is close to the lens (left, partly below the frame), R on the right, C at the back in front of the doors.
# v0.3: L and R moved inwards. R used to stand by the right-hand bumper rail and L on the left wall's edge, so
# people looked as if they stood in the wall.
# v0.5: hall / door / mid sit on the doorway's centre line (x 121 at the sill; it was 126, so shoulders covered the
# right-hand post), and P moved 2 px forward so Toby stands where people are still full size.
SPOTS = {'hall': (121, 113), 'door': (121, 128), 'mid': (124, 145), 'L': (112, 165), 'R': (154, 156), 'C': (134, 140),
         'sideL': (66, 112), 'sideR': (184, 112),   # on the landing, hidden behind the door jambs
         'P': (138, 136), 'dogspot': (102, 144),
         'midL': (110, 148), 'midR': (142, 150), 'midF': (120, 155)}
# P: right under the button panel, a raised hand reaches the buttons. dogspot: beside Mrs Pruitt, off everybody's
# path (v0.5). midL / midR / midF (v0.7): detours round people already standing in the car (see waypoint()); midF
# passes in front of somebody standing at C.
WALK_SPEED = 26.0     # px per second on screen (a slow elevator shuffle)
DOG = (102, 144)

# z: more negative = in front. People near the lens (L/R) are drawn over the ones at the back (C).
# 'jamb' is the car again with the doorway cut out; the <name>H twins walk on the landing between the doors and the jamb
Z = {'car': 0, 'doors': -2, 'jamb': -4, 'display': -5, 'bucket': -5, 'toolbox': -5, 'dog': -6, 'grey': -16, 'gus': -14, 'tech': -12,
     'dev': -15, 'priya': -17, 'rafi': -14, 'mila': -15, 'haldane': -16, 'mom': -17, 'pruitt': -18, 'toby': -11,
     'dark': -60, 'darkNV': -61, 'ghost': -62, 'glitch': -70, 'sfx': -81, 'outside': -82}
PEOPLE = ['pruitt', 'haldane', 'rafi', 'mila', 'gus', 'toby', 'mom', 'grey', 'tech', 'dev', 'priya', 'dog']
PROPS = ['bucket', 'toolbox']
WALKERS = ('pruitt', 'haldane', 'rafi', 'mila', 'gus', 'toby', 'mom', 'grey', 'tech', 'dev', 'priya', 'dog')
TWINS = tuple(w + 'H' for w in WALKERS)
for _t in TWINS: Z[_t] = -3
CHARS = ('pruitt', 'haldane', 'rafi', 'mila', 'gus', 'toby', 'mom', 'grey', 'tech', 'dev', 'priya', 'ghost') + tuple(t for t in TWINS if t != 'dogH')
SIZES = {n: Sp.CELL for n in CHARS}
SIZES['dogH'] = Sp.DOG_CELL
SIZES.update(dog=Sp.DOG_CELL, bucket=(20, 18), toolbox=(26, 16),
             doors=(Sp.DOOR_BOX[2] - Sp.DOOR_BOX[0] + 1, Sp.DOOR_BOX[3] - Sp.DOOR_BOX[1] + 1),
             display=(Sp.DISPLAY_BOX[2] - Sp.DISPLAY_BOX[0] + 1, Sp.DISPLAY_BOX[3] - Sp.DISPLAY_BOX[1] + 1), sfx=(1, 1), outside=(1, 1))

# v0.7: draw order follows depth. Every person's z is set from the feet's row whenever they are placed or move
# (fixed z per character drew Priya at the back in front of Dev, 16.png). Closer to the lens (bigger y) = in front.
ORDER = {n: i for i, n in enumerate(WALKERS)}
def zf(who, y): return round(-10 - (y - 100) / 10.0 - ORDER.get(who, 0) * 0.01, 3)
def setz(who, y): return {'action': 'setz', 'id': who, 'z': zf(who, y)}

def tl_pos(name, left, top):
    w, h = SIZES[name]
    return {'x': left, 'y': H - (top + h)}

def feet_pos(name, fx, fy):
    """Script position (bottom-left pivot) of a sprite whose feet stand at image point (fx, fy)."""
    w, h = SIZES[name]
    if name in CHARS: return {'x': fx - Sp.FEET[0], 'y': H - (fy - Sp.FEET[1] + h)}
    if name in ('dog', 'dogH'): return {'x': fx - w // 2, 'y': H - fy - 1}
    return {'x': fx - w // 2, 'y': H - fy}

def spot_of(p):
    """Staging names used in the scenes -> a standing spot."""
    if isinstance(p, tuple): return 'L' if p[0] < 112 else 'R' if p[0] > 140 else 'C'
    return {'BL': 'L', 'FL': 'C', 'BR': 'R', 'FR': 'C', 'corner': 'R'}.get(p, p)

def pt(p):
    return SPOTS[spot_of(p)] if not isinstance(p, tuple) or p is None else SPOTS[spot_of(p)]

# ------------------------------------------------------------------ action helpers
def cond(a, if_=None, ifNot=None):
    if if_: a['if'] = if_
    if ifNot: a['ifNot'] = ifNot
    return a

def flat(x):
    if isinstance(x, dict): return [x]
    out = []
    for i in x: out += flat(i)
    return out

CUR = {}      # per person while the scenes are generated in order: (spot, carrying the wardrobe)
NIGHT = [False]

COUPLE_SUB = {'hablaDev': 'dev', 'hablaPriya': 'priya'}
PRESENT = {}   # who is in the car right now (while generating a scene): name -> spot
LAST = [None]  # the last person who spoke in this scene
BACK_TALK = {'habla': 'hablaL', 'noboxHabla': 'noboxHablaL', 'carryHabla': 'carryHablaL'}
def say(who, en, zh, front=False, sub=None, end=None, **c):
    # v0.4: no narration. Lines in brackets that describe what happens are dropped (the pause stays);
    # "(Behind the doors) ..." keeps the spoken words without the stage direction.
    if en.startswith('('):
        if en.startswith('(Behind the doors) '):
            en, zh = en[len('(Behind the doors) '):], zh[len('（门外）'):]
        else:
            return wait(2.0)
    if who == 'couple':   # Dev and Priya are two objects now; the old animation name says who speaks
        who = COUPLE_SUB[sub]
        carrying = CUR.get(who, ('C', False))[1]
        sub, end = ('carryHabla', 'carry') if carrying else ('habla', 'default')
    if who in WALKERS and not front and (sub or 'habla') in BACK_TALK:
        # with the back to the camera the head turns towards whoever they talk to (the art turns right)
        # the listener: whoever spoke last (if still here), otherwise the nearest person
        others = [p for p in PRESENT if p != who and p != 'dog']
        if others and who in PRESENT:
            mx = SPOTS[PRESENT[who]][0]
            near = LAST[0] if LAST[0] in others else min(others, key=lambda p: abs(SPOTS[PRESENT[p]][0] - mx))
            if SPOTS[PRESENT[near]][0] < mx: sub = BACK_TALK[sub or 'habla']
    if who in WALKERS: LAST[0] = who
    a = {'action': 'say', 'id': who, 'text': T(en, zh)}
    if who not in ('sfx', 'outside'):
        a['subanimation'] = sub or ('hablaF' if front else 'habla')
        a['endanimation'] = end or ('front' if front else 'default')
        POSE[who] = a['endanimation']
    # v0.7: people on the speaker's right who have a "listening to the left" pose (drawn on request) turn an ear to
    # the speaker for the line, then face the doors again
    turn = []
    if who in PRESENT and not c:
        sx = SPOTS[PRESENT[who]][0]
        turn = [p for p in PRESENT if p != who and p in LISTEN_LEFT and POSE.get(p, 'default') == 'default'
                and 0 < SPOTS[PRESENT[p]][0] - sx <= 60]
    if not turn: return cond(a, **c)
    return [anim(p, 'listenL') for p in turn] + [cond(a, **c)] + [anim(p, 'default') for p in turn]

POSE = {}         # last standing pose given to each person (listening turns only interrupt 'default')
LISTEN_LEFT = {n for n in ('pruitt', 'haldane', 'rafi', 'mila', 'gus', 'toby', 'mom', 'grey', 'tech', 'dev', 'priya')
               if os.path.isfile(os.path.join(Sp.ROOT, 'people', n, 'listen_left.png'))}

def sfx(en, zh, **c): return say('sfx', en, zh, **c)
def wait(t, **c): return cond({'action': 'wait', 'time': t, 'id': 'sfx'}, **c)
DOORSTATE = ['closed']
SETTLED = {'open': 'isOpen', 'close': 'closed'}
def anim(obj, name, waitFinish=False, **c):
    if obj == 'doors' and name in ('closed', 'open', 'close', 'isOpen', 'pried', 'sign'):
        DOORSTATE[0] = SETTLED.get(name, name)
        if NIGHT[0]: name += 'N'
    if obj == 'car' and name in ('day', 'night') and not c:
        # the door sprite is cut from the lit or the night background: it follows the car's lighting (so does the jamb)
        NIGHT[0] = name == 'night'
        return [cond({'action': 'animation', 'id': 'car', 'animation': name, 'waitFinish': False}),
                cond({'action': 'animation', 'id': 'jamb', 'animation': name, 'waitFinish': False}),
                cond({'action': 'animation', 'id': 'doors', 'animation': DOORSTATE[0] + ('N' if NIGHT[0] else ''), 'waitFinish': False})]
    if obj == 'couple':
        return [anim('dev', name, waitFinish, **c), anim('priya', name, waitFinish, **c)]
    if not c: POSE[obj] = name
    return cond({'action': 'animation', 'id': obj, 'animation': name, 'waitFinish': waitFinish}, **c)
def on(obj, **c): return cond({'action': 'enable', 'id': obj}, **c)
def off(*objs): return [{'action': 'disable', 'id': o} for o in objs]
def setin(obj, p):
    if obj == 'dog':
        at = SPOTS[p] if p in SPOTS and p not in ('L', 'R', 'C') else DOG
        return [{'action': 'setin', 'id': obj, 'position': feet_pos(obj, *at)}, setz(obj, at[1])]
    if obj in WALKERS and obj in SIZES:
        at = SPOTS[p] if p in SPOTS else pt(p)
        return [{'action': 'setin', 'id': obj, 'position': feet_pos(obj, *at)}, setz(obj, at[1])]
    if obj == 'dogH': return {'action': 'setin', 'id': obj, 'position': feet_pos(obj, *(SPOTS[p] if p in SPOTS and p not in ('L', 'R', 'C') else DOG))}
    if obj == 'bucket': return {'action': 'setin', 'id': obj, 'position': feet_pos(obj, 160, 152)}
    if obj == 'toolbox': return {'action': 'setin', 'id': obj, 'position': feet_pos(obj, 113, 156)}
    return {'action': 'setin', 'id': obj, 'position': feet_pos(obj, *(SPOTS[p] if p in SPOTS else pt(p)))}
def move(obj, p, t, sub=None):
    where = (SPOTS[p] if p in SPOTS and p not in ('L', 'R', 'C') else DOG) if obj in ('dog', 'dogH') else (SPOTS[p] if p in SPOTS else pt(p))
    a = {'action': 'move', 'id': obj, 'position': feet_pos(obj, *where), 'time': t}
    if sub:
        # Without an end animation the game plays 'default' when the move ends: a one-frame flash of the full-size
        # standing frame between two walking pieces (v0.5 flicker). Keep walking; the caller sets the next pose.
        a['subanimation'] = sub; a['endAnimation'] = sub
    return a
def setv(name, value='true'): return {'action': 'setVar', 'id': 'sfx', 'name': name, 'value': value}

def floor(f): return anim('display', 'f' + str(f).replace('-', 'err'))

def travel(a, b, step=0.8):
    """Floor display counting from a to b (G = 0)."""
    n = lambda f: 0 if f == 'G' else int(f)
    a_, b_ = n(a), n(b)
    rng = range(a_, b_ + 1) if b_ >= a_ else range(a_, b_ - 1, -1)
    out = []
    for i in list(rng)[1:]:
        out += [wait(step), floor('G' if i == 0 else i)]
    return out

def door_open(): return [sfx('*ding*', '*叮*'), anim('doors', 'open', True), anim('doors', 'isOpen')]
def door_close(): return [anim('doors', 'close', True), anim('doors', 'closed')]

def scale_at(y):
    """Walking-frame size (percent) for feet at image row y: full size from spot C forward, 80 % on the sill (the doorway
    is ~31 px wide there), 60 % out on the landing. Snapped to the sizes liftcam_sprites makes."""
    if y >= 140: k = 100
    elif y >= 128: k = 80 + (y - 128) / 12 * 20
    else: k = max(60, 60 + (y - 113) / 15 * 20)
    return min((100,) + Sp.SCALES, key=lambda s: abs(s - k))

def sized(base, pct): return base if pct == 100 else '%s%d' % (base, pct)

def leg(who, a, b, sub):
    """Walk from spot a to spot b at a steady pace. Near the doors the walking frames get smaller as the feet move
    back (and bigger coming in); a person in the car also gets their draw order (z) updated as they go, so they pass
    in front of people further back and behind people closer to the lens."""
    (x0, y0), (x1, y1) = SPOTS[a], SPOTS[b]
    dist = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
    total = max(0.35, dist / WALK_SPEED)
    depth = who in WALKERS                       # real people and the dog (not the landing twins)
    scaled = not (scale_at(y0) == scale_at(y1) == 100)
    if not scaled and not depth:
        return move(who, b, round(total, 2), sub=sub)
    # equal pieces (0.1 s near the doors, 0.25 s elsewhere), each at the size of its middle; the ends take the size of
    # the spot itself so legs, and a twin and its person swapping at the door, meet at the same size. Neighbouring
    # pieces with the same size and depth step are merged. Every piece gets its share of the time: steady pace.
    n = max(1, int(round(total / (0.1 if scaled else 0.25))))
    pts = [(x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n) for i in range(n + 1)]
    sizes = [scale_at((pts[i][1] + pts[i + 1][1]) / 2) for i in range(n)]
    sizes[0], sizes[-1] = scale_at(y0), scale_at(y1)
    zs = [max(pts[i][1], pts[i + 1][1]) for i in range(n)]       # the closer end decides the draw order
    zkey = [int(z // 3) for z in zs]
    out, i = [], 0
    while i < n:
        j = i
        while j + 1 < n and sizes[j + 1] == sizes[i] and zkey[j + 1] == zkey[i]: j += 1
        bx, by = pts[j + 1]
        an = sized(sub, sizes[i])
        if depth: out.append(setz(who, max(zs[i:j + 1])))
        out.append({'action': 'move', 'id': who, 'position': feet_pos(who, round(bx), round(by)),
                    'time': round(total * (j + 1 - i) / n, 2), 'subanimation': an, 'endAnimation': an})
        i = j + 1
    return out

SIDE = {'pruitt': 'sideL', 'mila': 'sideL', 'mom': 'sideL', 'toby': 'sideL', 'gus': 'sideL', 'dev': 'sideL',
        'haldane': 'sideR', 'rafi': 'sideR', 'priya': 'sideR', 'grey': 'sideR', 'tech': 'sideR', 'dog': 'sideL'}

WAYPOINTS = ('direct', 'mid', 'midL', 'midR', 'midF')
def _segdist(p, a, b):
    (px, py), (ax, ay), (bx, by) = p, a, b
    dx, dy = bx - ax, by - ay
    k = 0.0 if dx == dy == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / float(dx * dx + dy * dy)))
    return ((px - ax - k * dx) ** 2 + (py - ay - k * dy) ** 2) ** 0.5

def waypoint(who, spot):
    """v0.7: the point inside the car a person walks through between the door and their spot, chosen to keep clear of
    the people already standing there (walking straight through someone at C read as two sprites merging)."""
    others = [SPOTS[PRESENT[p]] if p != 'dog' else DOG for p in PRESENT if p != who]
    # spots by the doors (C, P) are walked to directly; the others via the middle of the car
    usual = 'direct' if SPOTS[spot][1] < 145 else 'mid'
    if not others: return usual
    def clearance(wp):
        path = [(SPOTS['door'], SPOTS[spot])] if wp == 'direct' else [(SPOTS['door'], SPOTS[wp]), (SPOTS[wp], SPOTS[spot])]
        return min(_segdist(o, a, b) for o in others for a, b in path)
    return max(WAYPOINTS, key=lambda wp: (min(clearance(wp), 14) // 2, wp == usual))

def route(who, a, wp, b, sub):
    return leg(who, a, b, sub) if wp == 'direct' else [leg(who, a, wp, sub), leg(who, wp, b, sub)]

def walk_in(who, to, t, carry=False):
    """The <who>H twin steps out from behind the door jamb on the landing (small: it is further away), walks to the
    doorway and swaps with <who> on the threshold (same place, same frame: invisible); <who> walks via the middle of
    the car to the spot, growing to full size, and turns round in steps (facing the camera, head half turned, back to
    the camera) to face the doors."""
    spot = spot_of(to)
    wp = waypoint(who, spot)
    CUR[who] = (spot, carry); PRESENT[who] = spot
    wf, turn, idle = ('carryWalkF', 'carryTurn', 'carry') if carry else ('walkF', 'turn', 'default')
    tw, side = who + 'H', SIDE[who]
    at_door = sized(wf, scale_at(SPOTS['door'][1]))
    acts = [setin(tw, side), anim(tw, sized(wf, scale_at(SPOTS[side][1]))), on(tw),
            leg(tw, side, 'hall', wf), leg(tw, 'hall', 'door', wf),
            setin(who, 'door'), anim(who, at_door), on(who), off(tw)[0],
            route(who, 'door', wp, spot, wf), setz(who, SPOTS[spot][1]), anim(who, wf)]
    if not carry: acts += [anim(who, 'front'), wait(0.45)]
    return acts + [anim(who, turn), wait(0.35), anim(who, idle)]

def walk_out(who, t):
    """Back to the doorway (shrinking), swap with the twin on the threshold, out onto the landing and behind the jamb."""
    spot, carry = CUR.get(who, ('C', False)); PRESENT.pop(who, None)
    wp = waypoint(who, spot)
    wb = 'carryWalkB' if carry else 'walkB'
    tw, side = who + 'H', SIDE[who]
    at_door = sized(wb, scale_at(SPOTS['door'][1]))
    return [anim(who, wb), route(who, spot, wp, 'door', wb),
            setin(tw, 'door'), anim(tw, at_door), on(tw), off(who)[0],
            leg(tw, 'door', 'hall', wb), leg(tw, 'hall', side, wb), off(tw)[0]]

def enter(who, to, t=2.0, face='default'):
    if who == 'dog':
        PRESENT['dog'] = 'C'
        return [setin('dogH', 'sideL'), anim('dogH', sized('walk', scale_at(SPOTS['sideL'][1]))), on('dogH'),
                leg('dogH', 'sideL', 'hall', 'walk'), leg('dogH', 'hall', 'door', 'walk'),
                setin('dog', 'door'), anim('dog', sized('walk', scale_at(SPOTS['door'][1]))), on('dog'), off('dogH')[0],
                leg('dog', 'door', 'dogspot', 'walk'), anim('dog', 'default')]
    if who == 'couple':   # Priya on the left (at the back when somebody already stands at L, day 5), Dev on the right
        return walk_in('priya', 'C' if spot_of(to) == 'R' else 'L', t * 0.5) + walk_in('dev', 'R', t * 0.5)
    out = walk_in(who, to, t)
    if face != 'default': out.append(anim(who, face))
    return out

def leave(who, t=1.6):
    if who == 'dog':
        PRESENT.pop('dog', None)
        return [anim('dog', 'walk'), leg('dog', 'dogspot', 'door', 'walk'),
                setin('dogH', 'door'), anim('dogH', sized('walk', scale_at(SPOTS['door'][1]))), on('dogH'), off('dog')[0],
                leg('dogH', 'door', 'hall', 'walk'), leg('dogH', 'hall', 'sideL', 'walk'), off('dogH')[0]]
    if who == 'couple':
        return walk_out('dev', t * 0.5) + walk_out('priya', t * 0.5)
    return walk_out(who, t)

ALL = PEOPLE + list(TWINS) + PROPS + ['dark', 'darkNV', 'ghost']
def reset(display='G', night=False):
    """Scene opening: empty car, doors closed, lights on (night lighting after 22h)."""
    NIGHT[0] = night; DOORSTATE[0] = 'closed'; PRESENT.clear(); LAST[0] = None
    return ([{'action': 'blinkLed', 'id': 'sfx'}] + off(*ALL)
            + [on('car'), anim('car', 'night' if night else 'day'), on('jamb'), anim('jamb', 'night' if night else 'day'),
               on('doors'), anim('doors', 'closed'),
               on('display'), floor(display), on('glitch'), anim('glitch', 'off')])

def glitch(kind='burst'): return [anim('glitch', kind, True), anim('glitch', 'off')]

END = [{'action': 'stopLed', 'id': 'sfx'}]

GENERIC = {}
def ev(name, events):
    GENERIC[name] = events
    return {'action': 'triggerEvents', 'events': name, 'id': 'sfx'}

SCENES = {}
def scene(name, hour, modify, goto, *body, start=None, finish=None, note=None):
    s = {'camera': 1, 'hour': str(hour), 'modify': modify}
    if goto: s['goto'] = goto
    if note: s['_comment'] = note
    if start: s['startEvents'] = start
    if finish: s['finishEvents'] = finish
    s['script'] = flat(list(body))
    SCENES[name] = s

VALID = []      # no recordings in this cage (see the module docstring): the old markers are kept as no-ops
UNVALID = []

# ------------------------------------------------------------------ scenes
scene('start', 0, 'now', 'd1_dog', reset('G', night=True), END, note='Initial state: empty car at night.')

# ================================================================== DAY 1: meet everybody
scene('d1_dog', 7.5, 'today', 'd1_phone',
      reset('G'), travel('G', 9, 0.5), door_open(),
      enter('dog', (90, 128), 1.2, face='default'), enter('pruitt', 'L', 2.2),
      door_close(), travel(9, 7),
      say('pruitt', 'Ground floor, Duchess. Again. Always the ground floor.', '一楼，公主。又是一楼。永远是一楼。'),
      anim('dog', 'sniff'),
      say('pruitt', 'Don\'t sniff the corner. We don\'t know who has been in that corner.', '别闻那个角落。我们不知道谁在那个角落待过。'),
      travel(7, 4),
      say('pruitt', 'Listen to it. It\'s humming again. A building should not hum.', '你听。它又在哼歌了。一栋楼不应该哼歌。'),
      sfx('*mmmmmmmm*', '*呜呜呜呜*'),
      say('pruitt', 'In my day elevators had a man in a hat. He hummed. That was allowed.', '我年轻的时候电梯里有个戴帽子的人。他哼歌。那是可以的。'),
      travel(4, 'G'), door_open(), leave('pruitt', 1.8), leave('dog', 1.0), door_close(),
      wait(2), END)

scene('d1_phone', 9.5, 'today', 'd1_parcel',
      reset('G'), travel('G', 11, 0.5), door_open(),
      enter('haldane', 'R', 2.0),
      say('haldane', 'Yes. Yes. No, I\'m listening, Gary. I\'m in the elevator.', '对。对。不，我在听，加里。我在电梯里。'),
      door_close(), travel(11, 9),
      say('haldane', 'If I cut out, it\'s the elevator. Not me. I would never hang up on you.', '如果断线，是电梯的问题。不是我。我绝不会挂你电话。'),
      travel(9, 6),
      say('haldane', 'Gary? Gary. ...Hello?', '加里？加里。...喂？'),
      wait(1),
      say('haldane', 'Unbelievable. Eleven floors and not one bar.', '真不敢相信。十一层楼，一格信号都没有。'),
      anim('haldane', 'front'), wait(1),
      say('haldane', '...Is that a camera?', '...那是摄像头吗？', front=True),
      say('haldane', '(He pats the hair across the top of his head. Twice.)', '（他把头顶的头发往中间拨了拨。两次。）', front=True),
      anim('haldane', 'default'), travel(6, 'G'), door_open(), leave('haldane'), door_close(),
      wait(2), END)

scene('d1_parcel', 12, 'today', 'd1_mila',
      reset('G'), door_open(),
      enter('rafi', 'C', 2.0),
      say('rafi', 'Eleven B. Eleven B. Who lives in Eleven B and orders a box this heavy?', '11楼B。11楼B。谁住11楼B还订这么重的箱子？'),
      door_close(), travel('G', 9),
      say('rafi', 'Ninth floor? I didn\'t press nine.', '九楼？我没按九楼啊。'),
      door_open(), wait(2),
      say('rafi', 'Hello? ...Nobody. The building is pranking me.', '有人吗？...没人。这栋楼在整我。'),
      door_close(), travel(9, 11), door_open(),
      say('rafi', 'Okay, box. This is it. Be brave.', '好了，箱子。就是这里了。勇敢点。'),
      leave('rafi'), door_close(),
      wait(1), travel(11, 'G'), wait(2), END)

scene('d1_mila', 16, 'today', 'd1_evening',
      reset('G'), door_open(),
      enter('mila', 'C', 1.8),
      door_close(),
      say('mila', '(Muffled music from her headphones.) *tss tss tss*', '（耳机里传出闷闷的音乐。）*嚓 嚓 嚓*'),
      travel('G', 3),
      anim('mila', 'dance'), wait(1.5), anim('mila', 'default'),
      travel(3, 5),
      anim('mila', 'dance'), wait(1.2),
      door_open(), anim('mila', 'default'),
      say('mila', '...', '...'),
      say('mila', 'Wrong floor. Obviously. I wasn\'t doing anything.', '按错楼层了。当然。我又没在干嘛。'),
      door_close(), travel(5, 6), door_open(), leave('mila'), door_close(),
      wait(2), END)

scene('d1_evening', 19, 'today', 'd1_night',
      reset('G'), door_open(),
      enter('dog', (106, 150), 1.0), enter('pruitt', 'BL', 2.0),
      enter('haldane', 'R', 1.6),
      door_close(),
      say('pruitt', 'Evening.', '晚上好。'),
      say('haldane', 'Evening.', '晚上好。'),
      travel('G', 2, 1.0),
      say('pruitt', 'Cold out.', '外面挺冷的。'),
      say('haldane', 'Very cold.', '很冷。'),
      travel(2, 5, 1.0),
      say('pruitt', 'Supposed to get colder.', '听说还会更冷。'),
      say('haldane', 'That\'s what they say.', '他们是这么说的。'),
      travel(5, 9, 1.2),
      door_open(),
      say('pruitt', 'Well. Goodnight.', '那么。晚安。'),
      leave('pruitt', 2.0), leave('dog', 1.0), door_close(),
      say('haldane', '(He lets out a breath he has held for nine floors.)', '（他长长地呼了一口气。九层楼都没敢呼吸。）'),
      travel(9, 11), door_open(), leave('haldane'), door_close(),
      wait(2), END)

scene('d1_night', 22, 'today', 'd2_gus',
      reset(11, night=True),
      wait(3),
      sfx('*click*', '*咔哒*'),
      travel(11, 1, 0.5), wait(1), travel(1, 12, 0.4),
      wait(1), door_open(), wait(4),
      sfx('(Nobody gets in.)', '（没有人进来。）'),
      door_close(), travel(12, 'G', 0.5),
      wait(3), END, note='The elevator rides on its own. Never explained.')

# ================================================================== DAY 2: buttons
scene('d2_gus', 7, 'nextAvailable', 'd2_toby',
      reset('G'), door_open(),
      enter('gus', 'R', 2.0), [setin('bucket', (146, 100)), on('bucket')],
      anim('gus', 'mop'),
      say('gus', 'Morning, old girl.', '早啊，老姑娘。', sub='mop', end='mop'),
      say('gus', 'You were up all night again. I heard you. Up, down, up, down.', '你昨晚又一夜没睡。我听到了。上去，下来，上去，下来。', sub='mop', end='mop'),
      sfx('*creak*', '*咯咯*'),
      say('gus', 'And that noise. That\'s new. Don\'t make new noises at your age.', '还有那个声音。那是新的。你这把年纪别发出新的声音。', sub='mop', end='mop'),
      wait(2), anim('gus', 'default'),
      say('gus', 'There. Shiny. Nobody will notice, but I will.', '好了。亮晶晶。没人会注意到，但我会。'),
      leave('gus'), off('bucket'), door_close(),
      wait(2), END)

scene('d2_toby', 10, 'today', 'd2_parcel',
      reset('G'), travel('G', 3, 0.6), door_open(),
      enter('toby', 'P', 1.4), enter('mom', 'BL', 2.0),
      say('mom', 'Ground floor, Toby. Just the G. Only the G.', '一楼，托比。只按G。只能按G。'),
      anim('toby', 'jump'), sfx('*beep beep beep beep beep beep beep beep*', '*滴滴滴滴滴滴滴滴*'),
      door_close(),
      say('toby', 'I pressed ALL of them!', '我全部都按了！', sub='jump', end='default'),
      say('mom', 'Of course you did.', '你当然会。'),
      travel(3, 2), door_open(), wait(1), door_close(),
      say('toby', 'Hello, floor two!', '你好，二楼！', sub='jump', end='default'),
      travel(2, 1), door_open(), wait(1), door_close(),
      travel(1, 'G'), door_open(),
      say('mom', 'Out. Out out out.', '出去。出去出去出去。'),
      leave('toby', 1.2), leave('mom'), door_close(),
      travel('G', 4, 0.6), door_open(), wait(0.6), door_close(),
      travel(4, 8, 0.6), door_open(), wait(0.6), door_close(),
      travel(8, 12, 0.6), door_open(), wait(0.6), door_close(),
      sfx('(Every floor. To the very top. Empty.)', '（每层都停。一直到顶楼。没有人。）'),
      wait(2), END)

scene('d2_parcel', 13, 'today', 'd2_phone',
      reset('G'), door_open(),
      enter('rafi', 'R', 1.8),
      wait(0.5), door_close(), door_open(),
      enter('dog', (96, 136), 1.0), enter('pruitt', 'L', 2.0),
      door_close(), travel('G', 3),
      say('pruitt', 'Is that box for nine?', '那箱子是九楼的吗？'),
      say('rafi', 'Twelve.', '十二楼的。', front=False),
      say('pruitt', 'I\'m expecting a box.', '我在等一个箱子。'),
      say('rafi', 'This one says twelve, ma\'am.', '这个写的是十二楼，女士。'),
      travel(3, 6),
      say('pruitt', 'Boxes get confused. Let me just look inside.', '箱子会搞混的。让我看一下里面就好。'),
      say('rafi', 'Please don\'t open the box.', '请不要打开箱子。'),
      anim('dog', 'bark'), sfx('*Yip!*', '*呜哇！*'),
      say('pruitt', 'Duchess says it smells like my box.', '公主说它闻起来像我的箱子。'),
      travel(6, 9), door_open(),
      say('rafi', 'Your floor, ma\'am. Have a nice day. Far away from this box.', '您的楼层到了，女士。祝您愉快。离这个箱子远一点。'),
      leave('pruitt'), leave('dog', 1.0), door_close(), travel(9, 12), door_open(), leave('rafi'), door_close(),
      wait(2), END)

scene('d2_phone', 18.5, 'today', 'd2_grey',
      reset('G'), door_open(),
      enter('haldane', 'C', 1.8), door_close(),
      say('haldane', 'No, Gary, YOU listen. I made that spreadsheet. With my hands.', '不，加里，你听着。那个表格是我做的。用我的双手。'),
      travel('G', 4),
      say('haldane', 'Twelve years. Twelve years and they give the window desk to Kevin.', '十二年。十二年了，他们把靠窗的位子给了凯文。'),
      say('haldane', 'Kevin has a ponytail, Gary.', '凯文绑马尾啊，加里。'),
      travel(4, 8),
      anim('haldane', 'front'), wait(1),
      say('haldane', '...Hang on.', '...等一下。', front=True),
      anim('haldane', 'wave', True), anim('haldane', 'wave', True),
      say('haldane', 'Hi. Hello. Sorry. Just a normal man on a normal call.', '嗨。你好。抱歉。只是一个普通人在打普通的电话。', front=True),
      anim('haldane', 'default'), travel(8, 11), door_open(), leave('haldane'), door_close(),
      wait(2), END)

scene('d2_grey', 22, 'today', 'd3_dog',
      reset(5, night=True), travel(5, 'G', 0.6), door_open(),
      enter('grey', 'corner', 2.6), door_close(),
      wait(2),
      sfx('(He presses a button. Just one.)', '（他按了一个按钮。只按了一个。）'),
      floor(13), wait(3),
      anim('car', 'day'), wait(0.2), anim('car', 'night'), wait(0.15), anim('car', 'day'), wait(0.1), anim('car', 'night'),
      wait(4),
      door_open(), wait(1), leave('grey', 2.4), door_close(),
      floor(12), wait(3), END,
      finish=[{'type': 'addNew', 'id': 'newsContract', 'when': 'future', 'day': '+1', 'hour': '8'}],
      note='The man in the grey coat. The display says 13. The building has twelve floors. Never explained.')

# ================================================================== DAY 3: moving day
scene('d3_dog', 8, 'nextAvailable', 'd3_parcel',
      reset('G'), travel('G', 9, 0.5), door_open(),
      enter('pruitt', 'C', 2.0),
      say('pruitt', 'Duchess. Come.', '公主。过来。', front=False),
      sfx('*Yip! Yip yip yip!*', '*呜哇！呜哇呜哇呜哇！*'),
      say('pruitt', 'Duchess, it is a perfectly good elevator.', '公主，这是一部好好的电梯。'),
      sfx('*Yip yip yip yip!*', '*呜哇呜哇呜哇呜哇！*'),
      say('pruitt', 'She has never done this. Eleven years and she has never done this.', '她从来没这样过。十一年了，她从来没这样过。'),
      leave('pruitt', 1.4), wait(1),
      enter('pruitt', 'C', 1.4), [setin('dog', (126, 112)), on('dog'), anim('dog', 'sit')],
      say('pruitt', 'There. Carried like a queen. Happy?', '好了。像女王一样被抱进来。开心了吧？'),
      door_close(), travel(9, 'G', 0.6),
      anim('dog', 'bark'), sfx('*grrrr*', '*呜呜呜*'),
      say('pruitt', 'Growling at the floor. Wonderful.', '对着地板低吼。真棒。'),
      door_open(), leave('pruitt'), leave('dog', 0.8), door_close(),
      wait(2), END)

# v0.7: the wardrobe scene (d3_move, the couple carrying a flat-pack wardrobe in) was removed on request: a prop that
# big could not be handled convincingly in this view. Rafi's parcel (d3_parcel) still brings up "step fourteen", and
# day 4 repeats the panel F joke, so the running gag keeps its setup.

scene('d3_parcel', 14, 'today', 'd3_dance',
      reset('G'), door_open(),
      enter('rafi', 'C', 1.8), door_close(),
      say('rafi', 'Four A. "Wardrobe, part two of two." Who sends a wardrobe in two parts?', '4楼A。“衣柜，第二件共两件。”谁会把衣柜分两次寄？'),
      travel('G', 4),
      say('rafi', '...It says "step fourteen" on the side. In marker.', '...侧面用马克笔写着“第十四步”。'),
      door_open(), wait(1.5),
      say('rafi', 'I\'m leaving it at the door. I don\'t want to be part of step fourteen.', '我放门口就好。我不想参与第十四步。'),
      leave('rafi'), door_close(),
      wait(2), END)

scene('d3_dance', 16.5, 'today', 'd3_night',
      reset('G'), door_open(),
      enter('mila', 'C', 1.8), door_close(),
      say('mila', '(She looks at the doors. Then at the corner. Nobody.)', '（她看看门。再看看角落。没人。）'),
      travel('G', 1, 1.0),
      VALID,
      anim('mila', 'dance'), sfx('*tss tss TSS tss*', '*嚓 嚓 嚓 嚓*'),
      wait(2), travel(1, 3, 1.0), wait(1),
      say('mila', '...and SPIN, and point, and—', '...然后转圈，指一下，然后——', sub='dance', end='dance'),
      travel(3, 5, 1.0), wait(1.5),
      door_open(), anim('mila', 'default'), UNVALID,
      say('mila', '(She stands perfectly still. Nobody gets in.)', '（她站得笔直。没有人进来。）'),
      door_close(), travel(5, 6), door_open(), leave('mila'), door_close(),
      wait(2), END)

scene('d3_night', 21.5, 'today', 'd4_couple',
      reset(11, night=True), travel(11, 'G', 0.5), door_open(),
      enter('haldane', 'L', 1.8),
      enter('gus', 'BR', 2.0), door_close(),
      say('gus', 'Late night, Mr. Haldane.', '这么晚啊，霍尔丹先生。'),
      say('haldane', 'Kevin\'s spreadsheet crashed. Guess who fixed it.', '凯文的表格崩了。猜猜是谁修好的。'),
      travel('G', 3, 1.0),
      say('gus', 'Did you feel that last week? She dropped. Half a floor.', '你上礼拜有没有感觉到？她掉了一下。半层楼。'),
      say('haldane', 'Elevators don\'t drop. They have brakes. And inspections.', '电梯不会掉。电梯有刹车。还有检验。'),
      say('gus', 'Mm. Inspections.', '嗯。检验。'),
      travel(3, 7, 1.0),
      say('haldane', 'Companies get checked, Gus. There are rules.', '公司都要被检查的，格斯。有规定的。'),
      say('gus', 'Sure. And Kevin gets the window desk.', '是啊。然后凯文拿到了靠窗的位子。'),
      travel(7, 11), door_open(), leave('haldane'), door_close(),
      say('gus', 'Goodnight, old girl. Behave.', '晚安，老姑娘。听话点。'),
      travel(11, 'G'), door_open(), leave('gus'), door_close(),
      wait(2), END)

# ================================================================== DAY 4: the Club writes
scene('d4_couple', 9, 'nextAvailable', 'd4_gus',
      reset('G'), travel('G', 4, 0.6), door_open(),
      enter('couple', (128, 138), 2.6, face='nobox'), door_close(),
      say('couple', 'It stands. It actually stands.', '它立起来了。它真的立起来了。', sub='hablaDev', end='nobox'),
      say('couple', 'There are six screws left over, Dev.', '还多了六个零件，戴夫。', sub='hablaPriya', end='nobox'),
      say('couple', 'Spare screws. For the future.', '备用零件。留给未来。', sub='hablaDev', end='nobox'),
      say('couple', 'Step fourteen says "attach panel F to panel F".', '第十四步写“把F板装到F板上”。', sub='hablaDev', end='nobox'),
      say('couple', 'There is one panel F, Dev.', '只有一块F板，戴夫。', sub='hablaPriya', end='nobox'),
      travel(4, 'G', 0.9),
      say('couple', 'It leans, Dev. The wardrobe leans.', '它是歪的，戴夫。衣柜是歪的。', sub='hablaPriya', end='nobox'),
      say('couple', 'It\'s an old building. Everything here leans.', '这栋楼很老了。这里的东西都是歪的。', sub='hablaDev', end='nobox'),
      door_open(), leave('couple', 2.2), door_close(),
      wait(2), END)

scene('d4_gus', 13, 'today', 'd4_mila',
      reset('G'), door_open(),
      enter('gus', 'FL', 1.6), door_close(),
      say('gus', 'New sticker. "Inspected and approved."', '新贴纸。“检验合格。”'),
      say('gus', '(He presses it onto the frame by the door. Smooths it with his thumb.)', '（他把贴纸贴在门边的框上。用手指压平。）'),
      wait(1),
      say('gus', '"Next inspection: March 2019."', '“下次检验：2019年3月。”'),
      wait(2),
      say('gus', '...Well. It\'s a sticker. Stickers don\'t lie.', '...嗯。是贴纸嘛。贴纸不会说谎。'),
      sfx('*creeeak*', '*咯——咯——*'),
      say('gus', 'You hush.', '你安静。'),
      door_open(), leave('gus'), door_close(),
      wait(2), END)

scene('d4_mila', 16.5, 'today', 'd4_grey',
      reset('G'), door_open(),
      enter('mila', 'C', 1.8), door_close(),
      say('mila', 'No, I\'m in the elevator. Yeah, the creepy one.', '没有，我在电梯里。对，就是那部很吓人的。'),
      travel('G', 3),
      say('mila', 'There\'s a camera. I bet some old guy watches it all day.', '这里有个摄像头。我赌有个老头整天在看。'),
      anim('mila', 'front'),
      say('mila', 'Hi, old guy. Get a hobby.', '嗨，老头。找点爱好吧。', front=True, sub='grimace', end='front'),
      travel(3, 6),
      say('mila', 'Kidding. Nobody watches these. They\'re not even plugged in.', '开玩笑的。没人看这种东西。它们根本没插电。', front=True),
      door_open(), leave('mila'), door_close(),
      wait(2), END)

scene('d4_grey', 21.5, 'today', 'd5_toby',
      reset(9, night=True), travel(9, 'G', 0.5), door_open(),
      enter('grey', 'corner', 2.6),
      enter('pruitt', 'BL', 2.0), door_close(),
      say('pruitt', 'Good evening.', '晚上好。'),
      wait(2),
      say('pruitt', 'Do you live here? I know everybody. I don\'t know you.', '你住这里吗？这里的人我都认识。我不认识你。'),
      wait(3),
      say('pruitt', 'Well. Some people were raised in barns.', '好吧。有些人是在谷仓里长大的。'),
      travel('G', 9, 0.7), door_open(), leave('pruitt'), door_close(),
      wait(2), floor(13), anim('display', 'blink13'), wait(4),
      door_open(), leave('grey', 2.4), door_close(), floor(12),
      wait(3), END)

# ================================================================== DAY 5: an ordinary day
scene('d5_toby', 10, 'nextAvailable', 'd5_parcel',
      reset('G'), travel('G', 3, 0.6), door_open(),
      enter('toby', 'C', 1.6), door_close(),
      anim('toby', 'front'),
      say('toby', 'Hello, TV people!', '你好，电视里的人！', front=True, sub='waveF', end='front'),
      say('toby', 'I\'m Toby. I\'m seven. I am NOT allowed in here alone.', '我是托比。我七岁。我不准一个人进来。', front=True, sub='waveF', end='front'),
      travel(3, 1),
      say('toby', 'If you see my mom, I\'m not here.', '如果你看到我妈妈，我不在这里。', front=True, sub='waveF', end='front'),
      door_open(),
      enter('mom', 'BL', 1.2),
      say('mom', 'TOBY.', '托比！'),
      say('toby', 'I was saying hi to the TV.', '我在跟电视打招呼。', front=True),
      say('mom', 'It\'s not a TV. Out.', '那不是电视。出来。'),
      leave('toby', 1.0), leave('mom'), door_close(),
      wait(2), END)

scene('d5_parcel', 12.5, 'today', 'd5_dance',
      reset('G'), door_open(),
      enter('rafi', 'C', 1.8), door_close(), travel('G', 12, 0.5),
      anim('rafi', 'sit'),
      say('rafi', 'Top floor. Nobody presses twelve at lunchtime. Best restaurant in town.', '顶楼。午餐时间没人按十二楼。全城最好的餐厅。', sub='sitHabla', end='sit'),
      wait(2),
      sfx('*CLUNK*', '*轰隆*'),
      wait(2),
      say('rafi', '...Did we stop? We were already stopped.', '...我们停了吗？我们本来就停着啊。', sub='sitHabla', end='sit'),
      sfx('*mmmmmMMMMM*', '*呜呜呜呜呜*'),
      anim('rafi', 'nobox'),
      say('rafi', '(He knocks twice on the button panel. Politely.)', '（他在按钮面板上敲了两下。很有礼貌。）', sub='noboxHabla', end='nobox'),
      sfx('*click*', '*咔哒*'),
      say('rafi', 'Okay. Thank you. Lunch is over.', '好。谢谢。午餐结束了。', sub='noboxHabla', end='nobox'),
      travel(12, 'G', 0.5), door_open(), leave('rafi'), door_close(),
      wait(2), END)

scene('d5_dance', 16.5, 'today', 'd5_evening',
      reset('G'), door_open(),
      enter('mila', 'C', 1.8), door_close(),
      VALID,
      anim('mila', 'dance'),
      say('mila', 'Okay. Full routine. From the top.', '好。完整版。从头来。', sub='dance', end='dance'),
      travel('G', 2, 1.0), wait(1.5),
      sfx('*CLUNK*', '*轰隆*'),
      anim('mila', 'fall'), glitch('burst'),
      wait(1.5),
      say('mila', '...Ow.', '...好痛。', sub='fallHabla', end='fall'),
      wait(1),
      say('mila', '(She laughs. Alone, on the floor of the elevator, for a long time.)', '（她笑了出来。一个人坐在电梯地板上，笑了很久。）', sub='fallHabla', end='fall'),
      travel(2, 6, 1.0), UNVALID,
      anim('mila', 'default'), door_open(), leave('mila'), door_close(),
      wait(2), END)

scene('d5_evening', 19.5, 'today', 'd6_gus',
      reset('G'), door_open(),
      enter('dog', (96, 136), 1.0), enter('pruitt', 'L', 2.0),
      enter('couple', (156, 146), 2.2, face='nobox'), door_close(),
      say('pruitt', 'You\'re the new ones. Four A.', '你们是新来的。4楼A。'),
      say('couple', 'That\'s us! Dev and Priya.', '就是我们！戴夫和普莉雅。', sub='hablaPriya', end='nobox'),
      say('pruitt', 'You were very loud on Wednesday. Something about a step.', '你们礼拜三很吵。好像跟第几步有关。'),
      travel('G', 2, 1.0),
      anim('car', 'night'), wait(0.15), anim('car', 'day'), wait(0.2), anim('car', 'night'), wait(0.1), anim('car', 'day'),
      say('couple', 'Step fourteen. We don\'t talk about step fourteen.', '第十四步。我们不谈第十四步。', sub='hablaDev', end='nobox'),
      say('pruitt', 'Everyone in this building has a step fourteen, dear.', '这栋楼里每个人都有自己的第十四步，亲爱的。'),
      travel(2, 4, 1.0), door_open(), leave('couple', 2.0), door_close(),
      travel(4, 9), door_open(), leave('pruitt'), leave('dog', 1.0), door_close(),
      wait(2), END)

# ================================================================== DAY 6: stuck
scene('d6_gus', 7, 'nextAvailable', 'd6_haldane',
      reset('G'), door_open(),
      enter('gus', 'R', 1.8), [setin('bucket', (146, 100)), on('bucket')], door_close(),
      say('gus', 'Don\'t you start today, old girl.', '老姑娘，你今天别闹。'),
      say('gus', '(He dials a number on an old phone.)', '（他用一部旧手机拨了个号码。）'),
      say('gus', 'UpRight Lifts? Larkspur Court. The elevator\'s dropping. Again.', 'UpRight电梯公司？拉克斯伯公寓。电梯又在往下掉了。'),
      wait(2),
      say('gus', 'Next month? She\'s been "next month" since 2019.', '下个月？她从2019年开始就一直是“下个月”。'),
      wait(1),
      say('gus', 'They hung up.', '他们挂了。'),
      anim('gus', 'mop'),
      say('gus', 'Just get through today. Then we\'ll see.', '先熬过今天。然后再说。', sub='mop', end='mop'),
      anim('gus', 'default'), door_open(), off('bucket'), leave('gus'), door_close(),
      wait(2), END)

scene('d6_haldane', 9, 'today', 'd6_stuck',
      reset('G'), travel('G', 11, 0.5), door_open(),
      enter('haldane', 'R', 1.8), door_close(),
      say('haldane', 'Gary. Big news. Kevin\'s leaving. The window desk is mine.', '加里。大消息。凯文要走了。靠窗的位子是我的了。'),
      travel(11, 7),
      say('haldane', 'Today, Gary. Today is my day.', '今天，加里。今天是我的日子。'),
      sfx('*CLUNK*', '*轰隆*'), wait(1),
      say('haldane', 'Gary? ...Of course.', '加里？...当然了。'),
      travel(7, 'G'), door_open(), leave('haldane'), door_close(),
      wait(2), END)

scene('d6_stuck', 16.5, 'today', 'd6_tech',
      reset('G'), door_open(),
      enter('haldane', 'R', 1.8),
      enter('dog', (98, 138), 1.0), enter('pruitt', 'L', 2.0),
      door_close(), travel('G', 7, 0.9),
      sfx('*CLUNK*', '*轰隆——*'),
      VALID,
      floor('--'), anim('display', 'errBlink'),
      anim('car', 'night'), wait(0.2), anim('car', 'day'), wait(0.15), anim('car', 'night'),
      glitch('burst'),
      say('pruitt', 'Oh.', '哦。'),
      say('haldane', 'It\'s fine. It does this.', '没事。它常这样。'),
      wait(3),
      say('haldane', 'It doesn\'t do this.', '它不常这样。'),
      say('pruitt', 'Press the bell, young man.', '按铃啊，年轻人。'),
      sfx('*BZZZZT* "Emergency line, please hold."', '*滴——* “紧急线路，请稍候。”'),
      say('haldane', 'Hold. They want us to hold. We ARE holding. Between floors.', '稍候。他们要我们稍候。我们就是在“稍候”啊。卡在两层楼中间。'),
      wait(2),
      anim('pruitt', 'sit'),
      say('pruitt', 'Sit down. My husband used to say: panic standing, you panic twice.', '坐下吧。我先生以前常说：站着慌，等于慌两次。', sub='sitHabla', end='sit'),
      anim('dog', 'sleep'),
      anim('haldane', 'sit'),
      say('haldane', 'Your husband sounds like a wise man.', '你先生听起来是个有智慧的人。', sub='sitHabla', end='sit'),
      say('pruitt', 'He was an elevator man. In a hat. He hummed.', '他是开电梯的。戴着帽子。会哼歌。', sub='sitHabla', end='sit'),
      wait(2),
      say('haldane', 'Can I tell you something? I don\'t have a window desk. I lied to Gary.', '我能跟你说件事吗？我没有拿到靠窗的位子。我骗了加里。', sub='sitHabla', end='sit'),
      say('pruitt', 'Who is Gary?', '加里是谁？', sub='sitHabla', end='sit'),
      say('haldane', 'Gary is my brother. He has a boat.', '加里是我哥。他有一艘船。', sub='sitHabla', end='sit'),
      wait(2),
      say('pruitt', 'And the hair? Is that for Gary too?', '那头发呢？也是为了加里？', sub='sitHabla', end='sit'),
      say('haldane', '...You can see it from up here?', '...从上面看得出来？', sub='sitHabla', end='sit'),
      say('pruitt', 'Dear, the camera can see it.', '亲爱的，连摄像头都看得出来。', sub='sitHabla', end='sit'),
      wait(3),
      sfx('(Two hours later.)', '（两个小时后。）'),
      say('pruitt', '...and that is why I never speak to the woman in six B.', '...所以我再也不跟6楼B那个女人说话了。', sub='sitHabla', end='sit'),
      say('haldane', 'She took your parking space for eleven years?', '她占了你的车位十一年？', sub='sitHabla', end='sit'),
      say('pruitt', 'And I don\'t even have a car.', '而且我根本没有车。', sub='sitHabla', end='sit'),
      sfx('*CRACK* *screech*', '*咔啦* *咯咯咯*'),
      anim('doors', 'pried'),
      sfx('"Fire brigade! Anyone in there?"', '“消防队！里面有人吗？”'),
      anim('haldane', 'default'), anim('pruitt', 'default'), anim('dog', 'bark'),
      say('haldane', 'Two! And a dog!', '两个人！还有一只狗！', sub='default', end='default'),
      say('pruitt', 'And a camera. Don\'t forget the camera.', '还有一个摄像头。别忘了摄像头。', sub='default', end='default'),
      sfx('*CRRRK*', '*咔啦啦*'), anim('doors', 'open', True), anim('doors', 'isOpen'),
      leave('pruitt', 1.8), leave('dog', 1.0), leave('haldane', 1.8),
      UNVALID,
      wait(2), anim('car', 'night'), floor('--'),
      wait(2), END,
      note='Stuck between 7 and 8 for three hours. Rescue through pried doors. Valid video.')

scene('d6_tech', 22.5, 'today', 'd7_dark',
      reset('--', night=True), anim('doors', 'isOpen'),
      enter('tech', 'C', 2.2), [setin('toolbox', (106, 100)), on('toolbox')],
      say('tech', '(He opens the button panel. Looks inside for a long time.)', '（他打开按钮面板。往里面看了很久。）'),
      wait(2),
      say('tech', 'Yeah. It\'s me. Larkspur Court.', '喂。是我。拉克斯伯公寓。'),
      say('tech', 'The brake pads are from... I don\'t know. Before me. Before you.', '刹车片是...我不知道。比我还老。比你还老。'),
      say('tech', 'Logbook says we inspected it every year. Signed by us.', '记录簿上写我们每年都有检验。是我们签的名。'),
      say('tech', 'Nobody\'s been in this shaft since 2019, boss.', '老板，2019年以后就没人进过这台电梯里面。'),
      wait(2),
      say('tech', 'This one should not still be running. We\'re shutting it down.', '这台根本不该还在运转。我们要停掉它。'),
      say('tech', 'And boss? It\'s not the only one.', '还有，老板？不只这一台。'),
      off('toolbox'), leave('tech', 2.0),
      anim('doors', 'sign'), wait(1),
      anim('display', 'foff'), anim('car', 'night'), wait(1),
      on('dark'), on('darkNV'), wait(3), END,
      finish=[{'type': 'addNew', 'id': 'newsShutdown', 'when': 'future', 'day': '+1', 'hour': '8'}],
      note='The tech seals the car: OUT OF ORDER sign on the inside of the doors, lights off.')

# ================================================================== DAY 7: lights off
def dark_open():
    return (reset('off') + [anim('display', 'foff'), anim('doors', 'sign'), on('dark'), on('darkNV'), on('ghost')])

scene('d7_dark', 9, 'nextAvailable', 'd7_voices',
      dark_open(),
      wait(6), glitch('burst'), wait(8), glitch('roll'), wait(6),
      say('outside', '(Behind the doors) Nine floors, Duchess. Nine.', '（门外）九层楼，公主。九层。'),
      wait(8), glitch('burst'), wait(10),
      END, note='Dark car. Nobody gets in. The ghost object is visible with night vision only.')

scene('d7_voices', 12.5, 'today', 'd7_late',
      dark_open(),
      wait(5),
      say('outside', '(Behind the doors) Eleven B. On foot. Okay, box. Be brave.', '（门外）11楼B。走楼梯。好了，箱子。勇敢点。'),
      wait(6), anim('glitch', 'static'), wait(2), anim('glitch', 'off'), wait(6),
      say('outside', '(Behind the doors) Gary? I\'m on the stairs. Yes, I have signal. Every bar.', '（门外）加里？我在楼梯上。对，有信号。满格。'),
      wait(8), glitch('roll'), wait(6),
      END)

scene('d7_late', 15.5, 'today', 'd7_end',
      dark_open(),
      wait(4),
      say('outside', '(Behind the doors, muffled music. Footsteps going up. A small laugh. Gone.)', '（门外，闷闷的音乐。上楼的脚步声。一声轻笑。远了。）'),
      wait(8), glitch('burst'), wait(4), glitch('burst'), wait(8),
      say('outside', '(Behind the doors) Night, old girl.', '（门外）晚安，老姑娘。'),
      wait(8),
      END)

scene('d7_end', 18, 'today', None,
      dark_open(),
      wait(5), glitch('burst'), wait(3), glitch('roll'), wait(2),
      anim('glitch', 'snow'), wait(3),
      anim('glitch', 'nosignal'), off('ghost'),
      wait(6), END,
      finish=[{'type': 'addEnding', 'id': 'liftCamDark'},
              {'type': 'addNew', 'id': 'newsStairs', 'when': 'future', 'day': '+1', 'hour': '8'},
              {'type': 'endDiary'}])

# ------------------------------------------------------------------ news, mails, endings (no keyword tags anywhere)
NEWS = {
    'newsContract': (('CITY RENEWS ELEVATOR CONTRACT', '市政府续签电梯维护合约'),
                     ('UpRight Lifts will keep maintaining 40 public housing elevators. "Our record is spotless," says the company.',
                      'UpRight电梯公司将继续维护40部公共住宅电梯。公司表示：“我们的记录无懈可击。”'),
                     'mods/LiftCam/web/news_contract'),
    'newsShutdown': (('40 ELEVATORS SEALED OVERNIGHT', '一夜之间，40部电梯被封'),
                     ('Two residents of Larkspur Court were trapped for three hours. Inspectors found UpRight Lifts had signed yearly checks without visiting since 2019.',
                      '拉克斯伯公寓两名住户被困三小时。调查发现，UpRight电梯公司自2019年起从未到场，却每年签署检验报告。'),
                     'mods/LiftCam/web/news_shutdown'),
    'newsStairs': (('LARKSPUR COURT TAKES THE STAIRS', '拉克斯伯公寓改走楼梯'),
                   ('The elevator will stay closed "for months". A tenant, 78, carries her dog up nine floors twice a day: "She refuses to walk past the doors."',
                    '电梯将关闭“数个月”。一位78岁的住户每天两次抱着她的狗爬九层楼：“它不肯从电梯门前走过去。”'),
                   'mods/LiftCam/web/news_stairs'),
}

ENDINGS = {
    'liftCamDark': ('The elevator of Larkspur Court never opened again. The residents learned each other\'s names on the stairs. Nobody ever found out who pressed thirteen.',
                    '拉克斯伯公寓的电梯再也没有打开过。住户们在楼梯间里记住了彼此的名字。没有人知道是谁按了十三楼。',
                    'mods/LiftCam/web/end_dark'),
}

# v0.7: the Club sends no mails about this cage. Nothing sends the two mails below any more ("About Cage N" on day 4,
# "end of broadcast" at the end were removed on request); their texts stay defined only so a save that already
# received one can still open it.
CLUB = ('Primate Observation Club', '灵长类动物观察俱乐部')
EMAILS = {
    'clubPatience': {'email': CLUB, 'subject': ('About Cage {%storyNumber}', '关于笼子{%storyNumber}'),
                     'text': ('Dear member,\n\nSome members have reported that Cage {%storyNumber} "contains no relevant information".\n\nWe remind you that every cage is selected with great care. Observation requires patience.\n\nKeep watching.\n\nPrimate Observation Club',
                              '亲爱的会员：\n\n有些会员反映笼子{%storyNumber}“没有任何有价值的信息”。\n\n我们提醒您，每一个笼子都经过精心挑选。观察需要耐心。\n\n请继续观看。\n\n灵长类动物观察俱乐部')},
    'clubRemoved': {'email': CLUB, 'subject': ('Cage {%storyNumber}: end of broadcast', '笼子{%storyNumber}：停止转播'),
                    'text': ('Dear member,\n\nDue to technical problems at the location, Cage {%storyNumber} is no longer broadcasting.\n\nNo refunds will be issued.\n\nPrimate Observation Club',
                             '亲爱的会员：\n\n由于现场的技术问题，笼子{%storyNumber}已停止转播。\n\n不予退款。\n\n灵长类动物观察俱乐部')},
}


# ------------------------------------------------------------------ late-night merges (see pitfalls: a scene that ends after
# midnight makes the next "today" scene skip a day). Night scenes here start at 21:30-22:30 and are short; d1_night is
# merged into nothing because the first scene of each morning is "nextAvailable".
for _m in ('d2_gus', 'd3_dog', 'd4_couple', 'd5_toby', 'd6_gus', 'd7_dark'):
    SCENES[_m]['modify'] = 'nextAvailable'
