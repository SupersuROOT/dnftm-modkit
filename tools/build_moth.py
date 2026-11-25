"""
Builds the "Moth Screen" mod folder (Mods/MothScreen) from moth_art.py and moth_story.py.

    python -I build_moth.py <out Mods dir>
"""
import json, os, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import moth_art as A
import moth_story as S
import moth_web as Wb
import moth_pages as Pg

OUT = os.path.join(sys.argv[1], 'MothScreen')
CAGE = S.CAGE
T = S.T

# ------------------------------------------------------------------ art
if os.path.isdir(OUT): shutil.rmtree(OUT)
artdir = os.path.join(OUT, 'art', CAGE)
L = A.build(artdir)
A.new(1, 1).save(os.path.join(artdir, 'dot.png'))
Wb.build(os.path.join(OUT, 'web'))
import moth_prize as Pz
Pz.build(os.path.join(OUT, 'web'))   # the gift's shelf pictures and popup (ModLoader 0.5.10 prizes)   # browser, newspaper, ending, chat and door images (ModLoader 0.5+)
rel = lambda n: 'art/%s/%s.png' % (CAGE, n)

FPS = {'cursor': 6, 'voice': 8, 'video': 4, 'term': 2, 'chat': 1.2, 'saver': 4, 'lost': 8}
LOOP = {('cursor', 'click'): False, ('voice', 'habla'): True}
# Clickable objects. Only small items that are never under another window: the game takes the first clickable
# collider under the mouse whatever is drawn in front, so a clue under a window could be clicked "through" it.
KW_OBJ = {'label': 'm0th', 'postit': 'noraPhone'}

objects = []
def obj(name, image=None):
    o = {'name': name, 'pivot': 'bottomLeft', 'z': S.Z[name]}
    o.update(S.pos(name))
    if name in KW_OBJ: o['keyword'] = KW_OBJ[name]
    lay = L.get(name)
    if lay and 'anims' in lay:
        o['sheet'] = {'image': rel(name), 'w': lay['w'], 'h': lay['h']}
        o['animations'] = {}
        for an, frames in lay['anims'].items():
            loop = LOOP.get((name, an))
            if loop is None:
                # progressive reveals (terminal / chat sequences) stop on their last frame
                loop = not (name in ('term', 'chat') and an not in ('idle',)) and len(frames) > 1
            o['animations'][an] = {'frames': frames, 'fps': FPS.get(name, 6), 'loop': loop}
        if 'default' not in o['animations']:
            first = next(iter(lay['anims']))
            o['animations']['default'] = {'frames': lay['anims'][first][:1], 'fps': 1, 'loop': False}
    else:
        o['image'] = rel(image or name)
    if name == 'reflect': o['role'] = 'nightVisionOnly'
    objects.append(o)

for n in ['wall', 'label', 'postit', 'notes', 'board', 'term', 'video', 'taskmgr', 'browser', 'chat', 'cam', 'popup',
          'black', 'saver', 'lost', 'cursor', 'voice', 'overlay', 'reflect']:
    obj(n)
obj('host', 'dot')

# ------------------------------------------------------------------ conversations, keywords, interactions
calls, chats, door = S.conversations()
# door options also carry the visit flag in option events (format used by the game's own door conversations)
for nid in ('1',):
    for o in door[nid]['texts']:
        if o.get('goto') in ('2', '3'): o['events'] = [{'type': 'setVar', 'name': 'mothVisited', 'value': 'true'}]
for sc in S.SCENES.values():
    for ev in sc.get('startEvents', []) + sc.get('finishEvents', []):
        if ev.get('conversation') == 'DOOR': ev['conversation'] = door
for evs in S.GENERIC.values():
    for ev in evs:
        if ev.get('conversation') == 'DOOR': ev['conversation'] = door
assert '"conversation": "DOOR"' not in json.dumps(S.SCENES) + json.dumps(S.GENERIC), 'door conversation placeholder left'

def kw_entry(k, en, zh, extra):
    e = {'text': T(en, zh)}
    if extra.get('isAddress'): e['isAddress'] = True
    if extra.get('addWords'): e['addWords'] = extra['addWords']
    ph = extra.get('phone')
    if ph in ('callNora', 'callPolice'):
        e['clickEvents'] = [{'type': 'callTo', 'id': ph}]
    elif ph == 'mothPhone':
        ring = [{'id': 'voice', 'action': 'say', 'text': T('*ring ring* ...Hello? Who is this?', '*铃铃*...喂？谁啊？'), 'subanimation': 'habla', 'endanimation': 'default'},
                {'id': 'voice', 'action': 'say', 'text': T('...Hello? Breathing. Great. Real mature.', '...喂？只有呼吸声。很好。真成熟。'), 'subanimation': 'habla', 'endanimation': 'default'}]
        ring2 = [{'id': 'voice', 'action': 'say', 'text': T('*ring* ...It\'s you, isn\'t it. Observer.', '*铃*...是你吧。观察者。'), 'subanimation': 'habla', 'endanimation': 'default'}]
        ring3 = [{'id': 'voice', 'action': 'say', 'text': T('*ring* *ring* ... *ring* (Nobody is home. Only Byte meows at the phone.)', '*铃* *铃*...*铃*（家里没人。只有字节对着电话叫。）'), 'subanimation': 'habla', 'endanimation': 'default'}]
        e['clickEvents'] = [{'type': 'fakeCall'},
                            {'type': 'insertActions', 'ifNot': 'guiltSeen,copsMoth,mothLeft', 'actions': ring},
                            {'type': 'insertActions', 'if': 'guiltSeen', 'ifNot': 'copsMoth,mothLeft', 'actions': ring2},
                            {'type': 'insertActions', 'if': 'mothLeft', 'ifNot': 'copsMoth', 'actions': ring3}]
    if k in PAGES: e['browser'] = {'data': PAGES[k]}
    return e

PAGES = Pg.pages()
keywords = {k: kw_entry(k, en, zh, extra) for k, en, zh, extra in Pg.KEYWORDS}
news = {}
for k, ((ten, tzh), (sen, szh), img) in S.NEWS.items():
    news[k] = {'title': T(ten, tzh), 'subtitle': T(sen, szh), 'image': img}

emails = {}
for k, m in S.EMAILS.items():
    emails[k] = {'email': T(*m['email']), 'subject': T(*m['subject']), 'text': T(*m['text'])}
club = ('Primate Observation Club', '灵长类动物观察俱乐部')
qen, qzh = S.MISSION['q']
emails['mission'] = {
    'subject': T('Routine observation study in Cage {%storyNumber}', '笼子{%storyNumber}的例行观察研究'),
    'text': T('Dear member,\nFor an important study of the Club, please answer the following question about Cage {%storyNumber}:\n\n- %s\n\nYour time will be rewarded with:\n- {%%reward}\n\nPrimate Observation Club'.replace('%s', qen).replace('{%%reward}', '{%reward}'),
              '亲爱的会员：\n为了俱乐部的一项重要研究，请回答以下关于笼子{%storyNumber}的问题：\n\n- ' + qzh + '\n\n你的时间将获得以下奖励：\n- {%reward}\n\n灵长类动物观察俱乐部'),
    'email': T(*club), 'caducity': 5,
    'reply': dict({a: [{'type': 'addEmail', 'id': 'missionCorrect', 'when': 'future', 'day': '0', 'hour': '+1'}] for a in S.MISSION['answers']},
                  default=[{'type': 'addEmail', 'id': 'missionFail', 'when': 'future', 'day': '0', 'hour': '+1'}])}
emails['missionCorrect'] = {'subject': T('RE: Observation study in Cage {%storyNumber}', '回复：笼子{%storyNumber}的观察研究'),
                            'text': T('Dear member,\nYour answer is correct. Here is the agreed reward:\n- {%reward}\n\nPrimate Observation Club',
                                      '亲爱的会员：\n你的回答是正确的。这是约定的奖励：\n- {%reward}\n\n灵长类动物观察俱乐部'), 'email': T(*club)}
emails['missionFail'] = {'subject': T('RE: Observation study in Cage {%storyNumber}', '回复：笼子{%storyNumber}的观察研究'),
                         'text': T('Dear member,\nUnfortunately the information you sent us is wrong.\n\nPrimate Observation Club',
                                   '亲爱的会员：\n很遗憾，你发给我们的信息是错误的。\n\n灵长类动物观察俱乐部'), 'email': T(*club)}

prizes = {k: {'id': k, 'name': T(*n), 'sellName': T(*n), 'description': T(*dsc), 'price': p,
              'events': [{'type': 'addMoney', 'q': p, 'concept': T(*n)}]} for k, (n, dsc, p) in S.PRIZES.items()}

items = {}
for k, lines in S.ITEMS.items():
    acts = [{'id': 'voice', 'action': 'blinkLed'}] + [{'id': 'voice', 'action': 'say', 'text': T(en, zh), 'subanimation': 'habla', 'endanimation': 'default'} for en, zh in lines] + [{'id': 'voice', 'action': 'stopLed'}]
    evs = [{'type': 'insertActions', 'ifNot': 'copsMoth,mothLeft', 'actions': acts}]   # nobody home after he left
    if k == 'dolly': evs.append({'type': 'modifyKarma', 'q': -2})
    if k == 'beer': evs.append({'type': 'modifyKarma', 'q': 2})
    items[k] = {'direccion': evs}

# Recording is disabled for this cage: the game's record button refuses a cage whose "recordings" table is empty
# (recCameraBtn: "recordingError"), so there is nothing to sell to Shock.tv.
recordings = {}

chat_config = {'mothContact': {'image': Pg.img('chat_avatar'), 'name': T('m0th', 'm0th'), 'relatedKeyword': '',   # no notebook chat button: ChatConversation.setImage crashes when diaryWord<kw>Action is missing
                               'availability': [{'type': 'availability', 'if': 'mothChatOn', 'ifNot': 'copsMoth', 'availability': True},
                                                {'type': 'availability', 'availability': False}]}}

# notebook: sayCheese page (55 slots, 7 circles). Slots that sit on top of each other and the page's Shock.tv
# video slots are skipped; inside each circle the longest words get the slots with the most room left and right.
import math, re as _re
_cat = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'editor', 'catalog.js'), encoding='utf-8').read()
_cat = json.loads(_cat[_cat.index('{'):].rstrip().rstrip(';'))
_page = next(p for p in _cat['diaryPages'] if p['id'] == 'sayCheese')['children']
_circles = {c['name']: c for c in _page if c['kind'] == 'circle'}
# phone boxes take fixed slots (see Pg.DIARY_BOXES); diaryCircle8 + its slots are copies of the diaryCircle7 box
_BOX8 = (Pg.POLICE_BOX_AT[0] - _circles['diaryCircle7']['x'], Pg.POLICE_BOX_AT[1] - _circles['diaryCircle7']['y'])
_reserved = {'diaryWord' + b[2] for b in Pg.DIARY_BOXES} | {'diaryWord' + b[4] for b in Pg.DIARY_BOXES}
# every stacked selector slot (deduction answers) and the slots taken by fixed words stay out of the automatic layout
_reserved |= {'diaryWord' + n for n in ('atico', 'sotano', 'garaje', 'vigilante', 'paparazzi', 'chofer', 'deportista', 'modelo',
                                        'actriz', 'ashleyApplegate', 'fotosRobadas', 'desnudosArtisticos', 'selfies',
                                        'fotosRobadasDeFamosas', 'fotosRobadasDeAshleyApplegate',
                                        'dinero', 'muchoDinero', 'muchisimoDinero')}
# the slot copied for a box's third line must not be handed out by the automatic layout either
_reserved |= {e[3] for e in Pg.BOX_EXTRA}
_reserved |= {'diaryWord' + slot for _, slot in Pg.DIARY_FIXED.values()}
_usable = []
for w in _page:
    if w['kind'] != 'word' or 'video' in w['name'].lower(): continue
    if any(math.hypot(w['x'] - u['x'], (w['y'] - u['y']) * 2.5) < 0.12 for u in _usable + [x for x in _page if x['name'] in _reserved]): continue
    if w['name'] in _reserved: continue
    _usable.append(w)
def _room(w):
    row = [u for u in _usable if u is not w and abs(u['y'] - w['y']) < 0.07]
    return min([abs(u['x'] - w['x']) for u in row] + [1.0])
ZH = {k: zh for k, en, zh, extra in Pg.KEYWORDS}
words, zones = {}, []
for circle, ks in Pg.DIARY_GROUPS:
    near = [w for w in _usable if min([c for c, _ in Pg.DIARY_GROUPS], key=lambda c: math.hypot(_circles[c]['x'] - w['x'], _circles[c]['y'] - w['y'])) == circle]
    assert len(near) >= len(ks), (circle, len(near), len(ks))
    near.sort(key=_room, reverse=True)
    for k, w in zip(sorted(ks, key=lambda k: -len(ZH[k])), near): words[k] = w['name'][len('diaryWord'):]
    zone = {'circle': circle, 'words': list(ks)}
    for k, (c, slot) in Pg.DIARY_FIXED.items():
        if c == circle: words[k] = slot; zone['words'].append(k)
    for c, answers, slots, cond, main_word in Pg.DEDUCTIONS:
        if c != circle: continue
        for k, slot in zip(answers, slots): words[k] = slot
        zone['words'] += answers
        zone['selectableWords'] = answers
        zone['wordSelector'] = cond
        if main_word: zone['mainWord'] = main_word
    zones.append(zone)
for circle, name_kw, name_slot, num_kw, num_slot in Pg.DIARY_BOXES:
    words[name_kw], words[num_kw] = name_slot, num_slot
    z = {'circle': circle, 'words': [num_kw, name_kw]}
    # the police box has no other source for its name: knowing the number writes "City Police" in the box
    # (also for old saves that already have the number)
    if name_kw == 'cityPolice': z['mainWord'] = [{'haveWord': num_kw, 'word': name_kw}]
    for c, kw, slot, *_ in Pg.BOX_EXTRA:
        if c != circle: continue
        words[kw] = slot; z['words'].append(kw)
        # a deduction that needs the word only sees words of its own zone: list it there too
        # (like the original page lists leslieDooley in circle 4 and in its box)
        for zz in zones:
            if kw in json.dumps(zz.get('wordSelector', {})) and kw not in zz['words']: zz['words'].append(kw)
    zones.append(z)
assert set(words) == set(keywords), set(keywords) ^ set(words)
assert len(set(words.values())) == len(words)
DIARY_COPIES = [{'from': 'diaryCircle7', 'name': 'diaryCircle8', 'dx': round(_BOX8[0], 3), 'dy': round(_BOX8[1], 3)},
                {'from': 'diaryWordleslieDooley', 'name': 'diaryWordpoliceName', 'dx': round(_BOX8[0], 3), 'dy': round(_BOX8[1], 3)},
                {'from': 'diaryWordleslieDooleyMail', 'name': 'diaryWordpoliceNum', 'dx': round(_BOX8[0], 3), 'dy': round(_BOX8[1], 3)}]
DIARY_COPIES += [{'from': src, 'name': 'diaryWord' + slot, 'dx': dx, 'dy': dy} for c, kw, slot, src, dx, dy in Pg.BOX_EXTRA]
DIARY_COPIES += Pg.ARROW_COPIES
# circle groups: a shifted circle takes its "?", remove icon, word slots and answer slots along
_box_words = {k for b in Pg.DIARY_BOXES for k in (b[1], b[3])} | {e[1] for e in Pg.BOX_EXTRA}
_answers = {c: (ans, slots) for c, ans, slots, *_ in Pg.DEDUCTIONS}
DIARY_MOVES = list(Pg.DIARY_MOVES)
for c, (dx, dy) in Pg.CIRCLE_SHIFT.items():
    zone = next(z for z in zones if z['circle'] == c)
    ans, slots = _answers.get(c, ([], []))
    names = [c, c + 'Selector'] + ['diaryWord' + words[k] for k in zone['words'] if k not in _box_words and k not in ans]
    if c in Pg.ANSWER_SHIFT:
        adx, ady = Pg.ANSWER_SHIFT[c]
        DIARY_MOVES += [{'name': n, 'dx': adx, 'dy': ady} for n in ['diaryWord' + sl for sl in slots] + [c + 'iconPosition']]
    else:
        names += ['diaryWord' + sl for sl in slots] + [c + 'iconPosition']
    DIARY_MOVES += [{'name': n, 'dx': dx, 'dy': dy} for n in names]
diary_config = {'zones': zones, 'arrows': Pg.DIARY_ARROWS, 'images': []}

# Scene start/finish events -> named generic events run by a "triggerEvents" action inside the script.
# finishEvents/startEvents are re-run by the game while it is paused (an event that opens the chat pauses it),
# which sent the same mail and re-opened the chat every frame. An action in the script runs exactly once.
generic = dict(S.GENERIC)
for name, sc in S.SCENES.items():
    script = sc['script']
    if sc.get('startEvents'):
        generic[name + '_start'] = sc.pop('startEvents')
        at = 1 if script and script[0].get('action') == 'blinkLed' else 0
        script.insert(at, {'action': 'triggerEvents', 'events': name + '_start', 'id': 'voice'})
    if sc.get('finishEvents'):
        generic[name + '_finish'] = sc.pop('finishEvents')
        at = len(script) - 1 if script and script[-1].get('action') == 'stopLed' else len(script)
        script.insert(at, {'action': 'triggerEvents', 'events': name + '_finish', 'id': 'voice'})

# Two-keyword searches: PAGES entries named "a_b" become keywords entries the browser finds when both are searched
# together (BrowserController.openSearchTerms). They are not notebook words.
for _k, _v in PAGES.items():
    if '_' in _k:
        assert all(x in keywords for x in _k.split('_')), _k
        keywords[_k] = {'browser': {'data': _v}}

cage = {
    'metadata': {'id': CAGE, 'hint': '', 'tmpContainer': CAGE, 'difficulty': 45, 'interest': 70},
    'items': items, 'prizes': prizes, 'chatConfig': chat_config, 'chats': chats, 'phoneCalls': calls, 'emails': emails, 'news': news,
    'recordings': recordings, 'keywords': keywords, 'diaryConfig': diary_config, 'genericEvents': generic,
    'script': {'metadata': {'cameras': 1, 'id': CAGE, 'startScene': 'start'}, 'predefinedActions': {}, 'scenes': S.SCENES},
}

endings = {'frames': {k: {'text': T(en, zh), 'image': img} for k, (en, zh, img) in S.ENDINGS.items()}}

PRIZE_AT = (-2.27, -0.85)   # on the small cabinet left of the door: no original prize uses that spot
manifest = {
    'name': 'Moth Screen',
    'minLoader': '0.5.10',
    'cages': [{'id': CAGE, 'insertAt': 0}],
    # the gift gets its own object on the prize shelf: a copy of an original prize object (position in shelf units)
    'prizes': [{'id': 'mothJar', 'template': 'coca', 'x': PRIZE_AT[0], 'y': PRIZE_AT[1], 'image': 'web/prize_jar',
                'selected': 'web/prize_jar_sel', 'popup': 'web/prize_jar_popup'}],
    'sceneTemplates': [{'id': CAGE, 'cloneFrom': '3', 'keepCameras': 1, 'art': {'cameras': [{'clear': True, 'objects': objects}]}}],
    'cameraEffects': [{'story': CAGE, 'cloneFrom': 'redFred'}],
    'diaryPages': [{'story': CAGE, 'cloneFrom': 'sayCheese', 'words': words, 'keep': sorted(_circles) + sorted({a['arrow'] for a in Pg.DIARY_ARROWS} - {c['name'] for c in Pg.ARROW_COPIES}),
                    # dial buttons next to the phone numbers, copied from sayCheese's phone number button (ModLoader 0.5.3)
                    'actions': {'noraPhone': 'telefonoAndrewHaynes', 'policeLine': 'leslieDooleyMail'},
                    # ModLoader 0.5.4: every word can be chosen in calls, chats and the Club mission (the game only accepts
                    # "main" words there); names are written in capitals like the game's own names
                    'main': sorted(words), 'upper': ['noraVance', 'eliasKrumm', 'dorianPell', 'crow', 'cityPolice'],
                    'copies': DIARY_COPIES,
                    # ModLoader 0.5.5: deduction "?" per circle with its three answers
                    'selectors': {c: answers for c, answers, *_ in Pg.DEDUCTIONS},
                    'moves': DIARY_MOVES}],
}

# ------------------------------------------------------------------ keyword markup
# Every say line, news item, browser page and NPC line gets the first untagged mention of each keyword marked,
# so important clues can be collected in many places (not only the first time they are mentioned).
FORMS = {
    # first: "Nora Pell" must be tagged before Nora's and Dorian's short forms grab its halves
    'noraPell': (['Nora Pell'], ['诺拉·佩尔']),
    'kestrel14': (['Kestrel Lane 14', 'number 14, Kestrel Lane'], ['红鹰巷14号']),
    'm0th': (['m0th', 'M0th', 'M0TH'], ['m0th']), 'noraVance': (['Nora Vance', 'Nora'], ['诺拉·万斯', '诺拉']), 'crow': (['Crow'], ['乌鸦']),
    'dorianPell': (['Dorian Pell', 'Dorian', 'Pell'], ['多里安·佩尔', '多里安', '佩尔']), 'kestrelLane': (['Kestrel Lane', 'KESTREL LANE', 'KESTREL LN', 'Kestrel'], ['红鹰巷']),
    'sweetCrumb': (['Sweet Crumb', 'SWEET CRUMB'], ['甜屑面包店', '甜屑']), 'biscuit': (['Biscuit'], ['饼干']), 'byte': (['Byte', 'BYTE'], ['字节']),
    'h4ckSchool': (['H4CK SCHOOL'], ['H4CK SCHOOL']), 'darkBoard': (['DarkBoard'], ['暗板论坛', '暗板']),
    'vpn': (['FreeVPN', 'free VPN', 'VPN'], ['免费VPN', 'VPN']), 'dnsLeak': (['DNS leak'], ['DNS泄漏']),
    'phishing': (['phishing'], ['诈骗邮件']),
    'socialEngineering': (['social engineering', 'Social engineering'], ['社会工程学']), 'doxxing': (['doxxing', 'dox'], ['人肉搜索']),
    'phototaxis': (['phototaxis'], ['趋光性']), 'pizzaNow': (['Pizza Now'], ['披萨现在']),
    'eliasKrumm': (['Elias Krumm', 'Elias'], ['埃利亚斯·克鲁姆', '埃利亚斯']), 'pocRelay': (['poc_relay.exe', 'poc_relay'], ['poc_relay.exe', 'poc_relay']),
    'relayServer': (['relay.primate-obs.club', 'relay server'], ['relay.primate-obs.club', '中继服务器']),
    'observer': (['Club member', 'Members', 'member'], ['会员']), 'restrainingOrder': (['restraining order', 'Restraining order'], ['禁止令']), 'intruder': (['Intruders', 'intruders', 'intruder', 'Intruder', 'INTRUDER'], ['闯入者', '闯入']),
    'bounty': (['bounty'], ['赏金']), 'webcamTape': (['Tape', 'tape'], ['胶带']), 'traceroute': (['Traceroute', 'traceroute'], ['追踪路由', '追踪']),
    'mask': (['Mask', 'mask'], ['面具']), 'fakeCourier': (['FAKE COURIER', 'fake courier', 'delivery men', 'courier'], ['假快递员', '快递员']),
    'nightShift': (['night shift', 'Night shift'], ['夜班']), 'sister': (['sister'], ['姐姐']), 'bike': (['blue bike', 'bike', 'Bike'], ['蓝色自行车', '自行车', '骑车']),
    'mothAddress': (['22 Gorse Street, flat 3B', '22 Gorse Street', 'Gorse Street'], ['戈尔斯街22号3B', '戈尔斯街22号', '戈尔斯街']),
    'noraPhone': (['555-0147'], ['555-0147']), 'policeLine': (['555-0110'], ['555-0110']),
    'cityPolice': (['City Police'], ['市警察局']),
    # deduction answers only come from the notebook "?", never from texts
    **{k: ([], []) for _, answers, *_ in Pg.DEDUCTIONS for k in answers},
}
assert set(FORMS) == {k for k in keywords if '_' not in k}, set(FORMS) ^ set(keywords)

def tag_text(t):
    spans = [(m.start(), m.end()) for m in _re.finditer(r'\[([A-Za-z0-9_]+)\].*?\[/?\1\]', t)]
    for k, (fen, fzh) in FORMS.items():
        if ('[%s]' % k) in t: continue
        for f in sorted(fen + fzh, key=len, reverse=True):
            ascii_ = all(ord(ch) < 128 for ch in f)
            pat = (r'(?<![A-Za-z0-9_])' + _re.escape(f) + r'(?![A-Za-z0-9_])') if ascii_ else _re.escape(f)
            m = next((m for m in _re.finditer(pat, t) if not any(a <= m.start() < b for a, b in spans)), None)
            if m:
                t = t[:m.start()] + '[%s]%s[/%s]' % (k, m.group(0), k) + t[m.end():]
                spans = [(m2.start(), m2.end()) for m2 in _re.finditer(r'\[([A-Za-z0-9_]+)\].*?\[/?\1\]', t)]
                break
    return t

# keywords removed in v2.4 (mom, twoStep, osint, mothPhone) may still be tagged by hand in old lines: drop those tags
_known = {k for k, *_ in Pg.KEYWORDS}
def _strip_unknown(t):
    return _re.sub(r'\[([A-Za-z0-9_]+)\](.*?)\[/?\1\]', lambda m: m.group(0) if m.group(1) in _known else m.group(2), t)
S.TXT[:] = [(_strip_unknown(en), _strip_unknown(zh)) for en, zh in S.TXT]

TAG_IDS = set()
def _collect(x, field=None):
    if isinstance(x, dict):
        is_say = x.get('action') == 'say'
        for f, v in x.items():
            if isinstance(v, str) and v.startswith(CAGE + '_') and (is_say or f in ('title', 'subtitle', 'pageText', 'status', 'job', 'source')
                                                                    or (f == 'text' and field in ('news', 'node', 'post', 'block'))):
                TAG_IDS.add(int(v.split('~')[0].split('_')[1]))
            elif isinstance(v, (dict, list)):
                _collect(v, None if f in ('texts', 'keywords', 'conversation') and False else None if f in ('texts', 'keywords') else 'node' if f.isdigit() else ('post' if f == 'posts' else ('block' if f == 'struct' else ('news' if f == 'news' else field))))
    elif isinstance(x, list):
        for v in x: _collect(v, field)
_collect(cage['script']); _collect(news, 'news'); _collect(PAGES); _collect(chats); _collect(calls); _collect(items)
_collect(generic)
for n in TAG_IDS:
    en, zh = S.TXT[n - 1]
    S.TXT[n - 1] = (tag_text(en), tag_text(zh))

# One tag per keyword per document: the game greys a collected keyword only inside the text block that was
# clicked, so a second mark of the same keyword elsewhere on the same page/news item would stay "new".
def _ref_id(v):
    return int(v.split('~')[0].split('_')[1]) if isinstance(v, str) and v.startswith(CAGE + '_') else None

def _untag_dupes(t, seen):
    out, pos = [], 0
    for m in _re.finditer(r'\[([A-Za-z0-9_]+)\](.*?)\[/?\1\]', t):
        out.append(t[pos:m.start()])
        k = m.group(1)
        if k in keywords and k in seen: out.append(m.group(2))
        else: out.append(m.group(0)); seen.add(k)
        pos = m.end()
    out.append(t[pos:])
    return ''.join(out)

def dedupe_doc(refs):
    seen_en, seen_zh, done = set(), set(), set()
    for r in refs:
        n = _ref_id(r)
        if n is None or n in done: continue
        done.add(n)
        en, zh = S.TXT[n - 1]
        S.TXT[n - 1] = (_untag_dupes(en, seen_en), _untag_dupes(zh, seen_zh))

DOC_FIELDS = ['url', 'name', 'pageName', 'pageCategory', 'dataHeader', 'dataField1', 'dataField2', 'dataField3', 'dataField4',
              'status', 'job', 'source', 'title', 'subtitle', 'text', 'pageText', 'address', 'phone']
for results in PAGES.values():
    for r in results:
        refs = [r.get(f) for f in DOC_FIELDS] + [p.get('text') for p in r.get('posts', [])] + [b.get('text') for b in r.get('struct', [])]
        dedupe_doc(refs)
for n in news.values(): dedupe_doc([n['title'], n['subtitle']])

# report: keywords tagged in only one language of the same text
_mis = 0
for i, (en, zh) in enumerate(S.TXT):
    a = set(_re.findall(r'\[([A-Za-z0-9_]+)\]', en)); b = set(_re.findall(r'\[([A-Za-z0-9_]+)\]', zh))
    if a != b and (a | b) & set(keywords):
        _mis += 1
        if _mis <= 25: print('TAG MISMATCH', i + 1, sorted(a ^ b), '|', en[:60], '|', zh[:40])
print('tag mismatches:', _mis)
mentions = {k: sum(1 for en, zh in S.TXT if ('[%s]' % k) in zh) for k in keywords}
print('mentions (zh):', sorted(mentions.items(), key=lambda kv: kv[1]))

# Text ids stay stable between versions: saves keep text ids (collected keywords, mails, news), so a line that
# existed in the previous build keeps its number; new lines get numbers after the highest one. The previous
# build's ids are read from mod/data/MothScreen/merge/loc/en.json (+ ch.json to tell same-English lines apart).
def _stable_ids():
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'MothScreen', 'merge', 'loc')
    try:
        old_en = json.load(open(os.path.join(base, 'en.json'), encoding='utf-8'))[CAGE]
        old_ch = json.load(open(os.path.join(base, 'ch.json'), encoding='utf-8'))[CAGE]
        # old lines that still carry tags of removed keywords: compare (and keep for old saves) without those tags
        old_en = {k: _strip_unknown(v) for k, v in old_en.items()}
        old_ch = {k: _strip_unknown(v) for k, v in old_ch.items()}
    except (OSError, KeyError, ValueError):
        return {i + 1: i + 1 for i in range(len(S.TXT))}, {}, {}
    free = {}
    for k in sorted(old_en, key=int): free.setdefault((old_en[k], old_ch.get(k)), []).append(int(k))
    by_en = {}
    for k in sorted(old_en, key=int): by_en.setdefault(old_en[k], []).append(int(k))
    used, out, nxt = set(), {}, max(map(int, old_en)) + 1 if old_en else 1
    pending = []
    for i, (en, zh) in enumerate(S.TXT):
        c = [x for x in free.get((en, zh), []) if x not in used]
        if c: out[i + 1] = c[0]; used.add(c[0])
        else: pending.append(i)
    for i in pending:
        en, zh = S.TXT[i]
        c = [x for x in by_en.get(en, []) if x not in used]   # same English, retouched Chinese
        if c: out[i + 1] = c[0]; used.add(c[0])
        else: out[i + 1] = nxt; nxt += 1
    # lines no longer used stay in the tables, in case a save still points at them
    return out, {k: v for k, v in old_en.items() if int(k) not in used}, {k: v for k, v in old_ch.items() if int(k) not in used}
ID, OLD_EN, OLD_CH = _stable_ids()
_idre = _re.compile(r'(?<![A-Za-z0-9])%s_(\d+)~' % CAGE)
def _renum(x):
    if isinstance(x, str): return _idre.sub(lambda m: '%s_%d~' % (CAGE, ID[int(m.group(1))]), _strip_unknown(x) if x.startswith(CAGE + '_') else x)
    if isinstance(x, dict): return {k: _renum(v) for k, v in x.items()}
    if isinstance(x, list): return [_renum(v) for v in x]
    return x

def dump(path, data):
    p = os.path.join(OUT, path); os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8') as f: json.dump(_renum(data), f, ensure_ascii=False, indent=1)

dump('mod.json', manifest)
dump('files/%s.json' % CAGE, cage)
dump('merge/loc/en.json', {CAGE: dict(OLD_EN, **{str(ID[i + 1]): en for i, (en, zh) in enumerate(S.TXT)})})
dump('merge/loc/ch.json', {CAGE: dict(OLD_CH, **{str(ID[i + 1]): zh for i, (en, zh) in enumerate(S.TXT)})})
dump('merge/endings.json', endings)

says = sum(1 for s in S.SCENES.values() for a in s['script'] if a.get('action') == 'say')
print('scenes', len(S.SCENES), 'says', says, 'texts', len(S.TXT), 'keywords', len(keywords), 'objects', len(objects))
