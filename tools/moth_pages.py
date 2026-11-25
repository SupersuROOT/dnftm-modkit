"""
Keywords of the Moth Screen cage and what the in-game browser shows when the player searches them:
Clickopedia wiki entries, custom web pages (DarkBoard, H4CK SCHOOL, FreeVPN, Sweet Crumb, Pizza Now, P.O.C.),
Metayou profiles, a map, a phone-book entry and news results. Images are the mod's own PNGs
("mods/MothScreen/web/<name>", loaded by ModLoader 0.5+).
"""
from moth_story import T, CAGE

MODID = 'MothScreen'
def img(name): return 'mods/%s/web/%s' % (MODID, name)

# id, english, chinese (short: they are drawn on the notebook page), extra
KEYWORDS = [
    # m0th himself
    ('m0th', 'm0th', 'm0th', {}), ('eliasKrumm', 'Elias Krumm', '埃利亚斯', {}), ('byte', 'Byte', '字节', {}),
    ('nightShift', 'night shift', '夜班', {}), ('mothAddress', '22 Gorse St', '戈尔斯街22号', {'isAddress': True}),
    # methods (circle 3: the identity deduction)
    ('h4ckSchool', 'H4CK SCHOOL', 'H4CK SCHOOL', {}), ('socialEngineering', 'social engineering', '社会工程学', {}),
    ('phishing', 'phishing', '诈骗邮件', {}), ('vpn', 'free VPN', '免费VPN', {}), ('dnsLeak', 'DNS leak', 'DNS泄漏', {}),
    ('fakeCourier', 'fake courier', '假快递员', {}), ('doxxing', 'doxxing', '人肉搜索', {}),
    # Nora (kestrelLane sits in her box with the name and the number; not an address: MART parcels would reach m0th's lines)
    ('noraVance', 'Nora Vance', '诺拉·万斯', {}), ('sweetCrumb', 'Sweet Crumb', '甜屑面包', {}), ('biscuit', 'Biscuit', '饼干', {}),
    ('bike', 'blue bike', '自行车', {}), ('kestrelLane', 'Kestrel Lane', '红鹰巷', {}), ('sister', 'sister', '姐姐', {}),
    ('noraPell', 'Nora Pell', '诺拉·佩尔', {}),
    # the full address only exists once m0th finds the house number (d3_number); it goes in Nora's box
    ('kestrel14', 'Kestrel Lane 14', '红鹰巷14号', {}),
    # Crow
    ('crow', 'Crow', '乌鸦', {}), ('bounty', 'bounty', '赏金', {}), ('dorianPell', 'Dorian Pell', '多里安·佩尔', {}),
    ('restrainingOrder', 'restraining order', '禁止令', {}), ('intruder', 'intruder', '闯入者', {}),
    # the observer
    ('pocRelay', 'poc_relay.exe', 'poc_relay', {}), ('observer', 'club member', '俱乐部会员', {}), ('webcamTape', 'tape', '胶带', {}),
    ('traceroute', 'traceroute', '追踪路由', {}), ('relayServer', 'relay server', '中继服务器', {}), ('mask', 'moth mask', '面具', {}),
    # phones
    ('noraPhone', '555-0147', '555-0147', {'phone': 'callNora'}),
    ('policeLine', '555-0110', '555-0110', {'phone': 'callPolice'}),
    ('cityPolice', 'City Police', '市警察局', {}),
    # misc
    ('darkBoard', 'DarkBoard', '暗板论坛', {}), ('pizzaNow', 'Pizza Now', '披萨现在', {}),
    ('phototaxis', 'phototaxis', '趋光性', {}),
    # deduction answers (notebook "?"): three per circle, picked by the player, usable in calls / chat
    ('mothHacker', 'amateur hacker', '业余黑客', {}), ('mothDetective', 'private eye', '私家探员', {}),
    ('mothCop', 'detective', '警探', {}),
    ('crowDebt', 'debt collector', '讨债人', {}), ('crowEx', 'her ex', '前任', {}),
    ('crowCop', 'a cop', '警察', {}),
    ('noraDebt', 'runs from debts', '躲债人', {}), ('noraHiding', 'separated', '离异分居', {}),
    ('noraFamous', 'a star', '明星', {}),
    ('mothWipe', 'delete it all', '删除', {}), ('mothComing', 'your door', '上门', {}),
    ('mothPolice', 'turn himself in', '自首', {}),
]

# Notebook (sayCheese page): circle -> keywords, slots chosen by build_moth.py
DIARY_GROUPS = [
    ('diaryCircle3', ['h4ckSchool', 'socialEngineering', 'phishing', 'vpn', 'dnsLeak', 'fakeCourier', 'doxxing']),
    ('diaryCircle1', ['sweetCrumb', 'biscuit', 'bike', 'sister', 'noraPell']),
    ('diaryCircle2', ['eliasKrumm', 'byte', 'nightShift', 'pizzaNow']),
    ('diaryCircle5', ['pocRelay', 'observer', 'webcamTape', 'traceroute', 'relayServer', 'mask', 'phototaxis']),
    ('diaryCircle4', ['crow', 'bounty', 'dorianPell', 'restrainingOrder', 'intruder', 'darkBoard']),
]
# Words with a fixed slot outside the automatic layout: the street (Kestrel Lane, known from the photo on day 2) sits in
# Nora's circle in the free Shock.tv slot (moved into the circle below, DIARY_MOVES)
DIARY_FIXED = {'kestrelLane': ('diaryCircle1', 'videoCorrecto')}
# Deductions: the game's own word selector. When the condition holds a "?" appears on the circle; it offers the three
# words (in this order, top to bottom); picking one adds it to the notebook (the cross next to it allows another try).
# The three words sit in the circle's stacked selector slots of the sayCheese page.
# The Crow selector and its answer slots overlap m0th's box (diaryCircle7) on this page: shift them right, under the circle.
# ---- v2.4.1 layout (user's sketch): m0th's box under m0th's circle; the relay circle top right; the police box bottom
# right; Crow's circle bottom left, an arrow to Nora's (bigger) box with the "separated" answer written on it, and
# Nora's circle to the right of her box. Positions are planned in screen pixels of a 1280x720 game window
# (page unit = 268 px across, 266 px up; page (0, 0) = screen (632, 502)).
def U(dx_px, dy_px): return round(dx_px / 268.0, 3), round(-dy_px / 266.0, 3)
# circle -> shift of the circle with its "?", remove icon, word slots and answer slots (build_moth.py lists the slots)
CIRCLE_SHIFT = {'diaryCircle4': U(-10, 40), 'diaryCircle5': U(57, -144), 'diaryCircle1': U(276, -4)}
# answers that do not follow their circle: Nora's answer sits on the Crow -> Nora arrow
ANSWER_SHIFT = {'diaryCircle1': U(-151, 36)}
NORA_BOX = U(-296, -52)                     # Nora's box (circle 6) and its lines
DIARY_MOVES = [
    *[{'name': n, 'dx': U(-56, -158)[0], 'dy': U(-56, -158)[1]} for n in
      ('diaryCircle7', 'diaryWordleslieDooley', 'diaryWordleslieDooleyMail', 'diaryWordleslieDooleyMailAction')],
    {'name': 'diaryCircle4Selector', 'dx': 0.0, 'dy': 0.06},
    # Nora's box: bigger frame (loader 0.5.9 scale) holding the address, the number and the name
    {'name': 'diaryCircle6', 'dx': NORA_BOX[0], 'dy': NORA_BOX[1], 'sx': 1.2, 'sy': 1.6},
    {'name': 'diaryWordandrewHaynes', 'dx': NORA_BOX[0], 'dy': round(NORA_BOX[1] - 0.079, 3)},
    {'name': 'diaryWordtelefonoAndrewHaynes', 'dx': NORA_BOX[0], 'dy': round(NORA_BOX[1] - 0.068, 3)},
    {'name': 'diaryWordnoraAddress', 'dx': NORA_BOX[0], 'dy': round(NORA_BOX[1] - 0.034, 3)},
    # the street's slot: into Nora's circle (on top of the circle's own shift)
    {'name': 'diaryWordvideoCorrecto', 'dx': U(-250, -76)[0], 'dy': U(-250, -76)[1]},
    {'name': 'diaryWordtelefonoAndrewHaynesAction', 'dx': U(-278, -67)[0], 'dy': U(-278, -67)[1]},
]
# the Crow -> Nora arrow: a copy of the page's straight double arrow (arrow 5, circles 2-3)
ARROW_COPIES = [{'from': 'diaryArrow5', 'name': 'diaryArrow7', 'dx': U(136, 204)[0], 'dy': U(136, 204)[1]}]
DEDUCTIONS = [
    # who is m0th? The methods circle (3) gives the answer; the original page's arrow 5 links it to m0th's circle (2)
    ('diaryCircle3', ['mothHacker', 'mothDetective', 'mothCop'], ['fotosRobadas', 'desnudosArtisticos', 'selfies'],
     {'atLeast': 4, 'words': ['h4ckSchool', 'socialEngineering', 'phishing', 'vpn', 'dnsLeak', 'fakeCourier', 'doxxing'],
      'haveWord': 'h4ckSchool'}, None),
    ('diaryCircle4', ['crowDebt', 'crowEx', 'crowCop'], ['vigilante', 'paparazzi', 'chofer'],
     {'atLeast': 3, 'haveWord': 'restrainingOrder'},
     # The right answer also writes Dorian's name (keyword addWords). Not a zone "mainWord": a mainWord hides the
     # chosen answer, which looked like the clue vanished when the name was already known (v2.0 bug).
     None),
    # Kestrel Lane is in Nora's box now; the condition still needs it (haveWord checks the collected words)
    ('diaryCircle1', ['noraDebt', 'noraHiding', 'noraFamous'], ['atico', 'sotano', 'garaje'],
     {'atLeast': 3, 'words': ['sweetCrumb', 'biscuit', 'bike', 'sister', 'noraPell'], 'haveWord': 'kestrelLane'}, None),
    ('diaryCircle5', ['mothWipe', 'mothComing', 'mothPolice'], ['deportista', 'modelo', 'actriz'],
     {'atLeast': 4, 'words': ['pocRelay', 'observer', 'webcamTape', 'traceroute', 'relayServer', 'mask', 'phototaxis'],
      'haveWord': 'relayServer'}, None),
]
# Boxes like the game's phone box: a name (main word, can be picked in calls/chats/missions) and a second line
# (a number with a dial button, or an address). circle -> (name keyword, name slot, second keyword, second slot).
# diaryCircle8 is a copy of diaryCircle7. BOX_EXTRA adds a third line (a copied slot) to a box.
DIARY_BOXES = [
    ('diaryCircle6', 'noraVance', 'andrewHaynes', 'noraPhone', 'telefonoAndrewHaynes'),
    ('diaryCircle7', 'm0th', 'leslieDooley', 'mothAddress', 'leslieDooleyMail'),
    ('diaryCircle8', 'cityPolice', 'policeName', 'policeLine', 'policeNum'),
]
# third line of a box (a copy of a slot): Nora's address, written just above her box
BOX_EXTRA = [('diaryCircle6', 'kestrel14', 'noraAddress', 'diaryWordtelefonoAndrewHaynes', 0.0, 0.041)]
# notebook arrows of the source page (shown when both circles are shown)
DIARY_ARROWS = [{'haveCircle': 'diaryCircle2,diaryCircle3', 'arrow': 'diaryArrow5'},
                {'haveCircle': 'diaryCircle4,diaryCircle1', 'arrow': 'diaryArrow7'}]
# the police box (a copy of m0th's box) goes to the bottom right corner: page position of its centre
POLICE_BOX_AT = (round((1085 - 632) / 268.0, 3), round((502 - 688) / 266.0, 3))

# ------------------------------------------------------------------ helpers
def block(x, y, w, h, en, zh, size=61, color=(40, 34, 28), font='tempesta', align='left', z=-3):
    """Text block on a custom web page. (x, y) is the centre of the wrap box, page centre = (0, 0), y up."""
    return {'pos': {'x': x, 'y': y, 'z': z}, 'alignment': align, 'verticalAlignment': 'top', 'color': {'r': color[0], 'g': color[1], 'b': color[2]},
            'size': size, 'font': font, 'wrap': {'width': w, 'height': h}, 'text': T(en, zh)}

def web(url_en, background, *blocks):
    return {'type': 'web', 'url': T(url_en, url_en), 'struct': [{'pos': {'x': 0, 'y': 0, 'z': -1}, 'image': img(background)}] + list(blocks)}

def wiki(name, cat, header, fields, text, ih, ib=''):
    r = {'type': 'wiki', 'pageName': T(*name), 'pageCategory': T(*cat), 'dataHeader': T(*header), 'pageText': T(*text),
         'imageHeader': img(ih), 'imageBottom': img(ib) if ib else ''}
    for i in range(4):
        r['dataField%d' % (i + 1)] = T(*fields[i]) if i < len(fields) else ''
    return r

def news_result(source, title, subtitle, text, image):
    return {'type': 'new', 'source': T(*source), 'title': T(*title), 'subtitle': T(*subtitle), 'text': T(*text), 'image': img(image)}

def meta(name, status, job, image, posts):
    return {'type': 'meta', 'name': T(*name), 'status': T(*status), 'job': T(*job), 'phone': '', 'email': '', 'image': img(image),
            'posts': [{'text': T(*t), 'image': img(i)} for t, i in posts]}

LIGHT = (232, 222, 200); RED = (200, 80, 66); GREEN = (178, 204, 114); DARK = (40, 34, 28); GOLD = (201, 181, 138)

# ------------------------------------------------------------------ pages
def pages():
    P = {}
    # --- custom web pages
    P['darkBoard'] = [web('http://darkboard.onion/jobs', 'web_darkboard',
        block(41, 34, 270, 22, 'JOB: Find a girl\'s home address. 300 coins. DM me.   - [crow]Crow[/crow]',
                               '工作：找出一个女孩的住址。300币。私信我。   —— [crow]乌鸦[/crow]', color=LIGHT),
        block(41, 10, 270, 22, '[m0th]m0th[/m0th]: I find anyone. Cheap. Fast. Please, I need rent.',
                               '[m0th]m0th[/m0th]：什么人都找得到。便宜。快。拜托，我要交房租。', color=GREEN),
        block(41, -14, 270, 22, '[h4ckSchool]H4CK SCHOOL[/h4ckSchool] ep.12 leaked. Rule 1: never use a [vpn]free VPN[/vpn].',
                                '[h4ckSchool]H4CK SCHOOL[/h4ckSchool] 第十二集外流。守则一：永远别用[vpn]免费VPN[/vpn]。', color=LIGHT),
        block(41, -38, 270, 22, 'Guide: how to [doxxing]dox[/doxxing] anyone in 10 minutes. No skills needed.',
                                '教学：十分钟[doxxing]人肉搜索[/doxxing]任何人。不需要技术。', color=LIGHT),
        block(41, -62, 270, 22, 'WARNING: someone is reading this board. Not the cops. Something else.',
                                '警告：有人在看这个论坛。不是警察。是别的东西。', color=RED))]
    # Searches: a general word gives a general page; the specific page needs two keywords ("a_b", either order).
    P['crow'] = [wiki(('Crow', '乌鸦'), ('Animals', '动物'), ('Common crow', '小嘴乌鸦'),
        [('Family: corvids', '科：鸦科'), ('Intelligence: high', '智力：高')],
        ('A black bird found in every city. Crows recognise human faces, remember people who wronged them for years and tell other crows about them. Not to be confused with users of the same name on internet forums.',
         '城市里随处可见的黑色鸟类。乌鸦认得人脸，会把伤害过它们的人记上好几年，还会告诉其他乌鸦。别和网络论坛上同名的用户搞混。'),
        'wiki_crow')]
    P['crow_darkBoard'] = [web('http://darkboard.onion/user/crow', 'web_darkboard',
        block(41, 34, 270, 22, 'USER: [crow]Crow[/crow]   Joined: 3 weeks ago   Posts: 1', '用户：[crow]乌鸦[/crow]   注册：三周前   发文：1', color=RED),
        block(41, 10, 270, 22, 'Signature: "Everyone pays their debts."', '签名档：“欠的总要还。”', color=LIGHT),
        block(41, -14, 270, 22, 'Only post: "JOB: find a girl", 300 coins [bounty]bounty[/bounty].', '唯一的发文：“工作：找一个女孩”，300币[bounty]赏金[/bounty]。', color=LIGHT),
        block(41, -38, 270, 22, 'Same avatar as a user on an old car forum.', '和一个旧汽车论坛上的用户用同一个头像。', color=LIGHT))]
    P['h4ckSchool'] = [web('http://vidtube.web/h4ckschool', 'web_h4ck',
        block(90, 58, 176, 24, 'H4CK SCHOOL', 'H4CK SCHOOL', size=128, font='tempestaBold', color=DARK),
        block(90, 34, 176, 30, 'EP.7: [socialEngineering]social engineering[/socialEngineering]. "Every photo is a door."',
                               '第七集：[socialEngineering]社会工程学[/socialEngineering]。“每一张照片都是一扇门。”', color=DARK),
        block(90, 2, 176, 30, '2,000,000 subscribers. Comments are off "for safety".', '两百万订阅。留言功能“为了安全”已关闭。', color=DARK),
        block(90, -30, 176, 40, 'Top comment: "[m0th]m0th[/m0th]: first!! ep.7 changed my life"',
                                '热门留言：“[m0th]m0th[/m0th]：第一！！第七集改变了我的人生”', color=(80, 100, 60)))]
    P['vpn'] = [web('http://freevpn.leak', 'web_freevpn',
        block(82, 50, 196, 30, 'Hide from EVERYONE. (Except us.)', '躲过所有人。（除了我们。）', size=90, font='tempestaBold', color=DARK),
        block(82, 14, 196, 40, 'Free forever! We only sell your data a little bit.', '永久免费！我们只会卖掉你一点点数据。', color=DARK),
        block(82, -28, 196, 40, 'Known issue: [dnsLeak]DNS leak[/dnsLeak]. Your real address may be visible. Working on it!',
                                '已知问题：[dnsLeak]DNS泄漏[/dnsLeak]。你的真实地址可能被看到。正在修复中！', color=(150, 50, 40)))]
    P['sweetCrumb'] = [web('http://sweetcrumb.web', 'web_bakery',
        # text sits inside the page's white panels (right panel: y 52..-72, lower-left panel: y -38..-72)
        block(120, 46, 118, 22, 'SWEET CRUMB', '甜屑面包店', size=80, font='tempestaBold', color=(192, 96, 122)),
        block(120, 2, 118, 44, 'Open 7:00-18:00. 3 Mill Road. Tel 555-0122.', '营业时间 7:00-18:00。米尔路3号。电话 555-0122。', color=DARK),
        block(120, -36, 118, 44, 'Staff of the month: [noraVance]Nora[/noraVance]! (and her cat [biscuit]Biscuit[/biscuit], our mascot)',
                                 '本月最佳员工：[noraVance]诺拉[/noraVance]！（还有她的猫[biscuit]饼干[/biscuit]，我们的吉祥物）', color=DARK),
        block(-61, -56, 214, 28, 'Fresh croissants every morning. Delivery by bike!', '每天早上新鲜牛角包。骑自行车外送！', color=DARK))]
    # text inside the white panel (page y 44..-72): the striped banner above it stays clear
    P['pizzaNow'] = [web('http://pizzanow.web', 'web_pizza',
        block(77, 32, 204, 24, 'WELCOME!', '欢迎！', size=100, font='tempestaBold', color=(150, 50, 40)),
        block(77, 8, 204, 30, 'Hot pizza in 30 minutes or it\'s... still pizza.', '三十分钟送达，不然...也还是披萨。', color=DARK),
        block(77, -18, 204, 30, 'Open until 2 AM. Night owls welcome.', '营业到凌晨两点。欢迎夜猫子。', color=DARK),
        block(77, -44, 204, 40, 'Track your order: search with the name or phone number you gave us.', '查询订单：用您留下的名字或电话号码搜索。', color=(90, 80, 70)))]
    P['pizzaNow_m0th'] = [web('http://pizzanow.web/track/4471', 'web_pizza',
        block(77, 32, 204, 24, 'ORDER #4471', '订单 #4471', size=100, font='tempestaBold', color=(150, 50, 40)),
        block(77, 8, 204, 30, 'Status: DELIVERED. 1 large pepperoni.', '状态：已送达。大号意式香肠一份。', color=DARK),
        block(77, -18, 204, 30, 'Address: [mothAddress]22 Gorse St, flat 3B[/mothAddress]. Phone: on file.',
                              '地址：[mothAddress]戈尔斯街22号3B[/mothAddress]。电话：已登记。', color=DARK),
        block(77, -44, 204, 40, 'Customer note: "Buzzer broken, knock. Ask for [m0th]m0th[/m0th], with a zero."',
                                '顾客备注：“门铃坏了，请敲门。找[m0th]m0th[/m0th]，用零。”', color=(90, 80, 70)))]
    # The relay server is the Club's own: no search finds it (v2.4). "Club member" alone is too general too.
    # --- Clickopedia entries
    P['socialEngineering'] = [wiki(('Social engineering', '社会工程学'), ('Security', '信息安全'), ('Social engineering', '社会工程学'),
        [('Target: people', '目标：人'), ('Tools: a phone, a smile', '工具：电话、笑容'), ('Also called: "hacking humans"', '又称：“黑进人心”')],
        ('Getting information by fooling people instead of computers. Typical tricks: calling as a [fakeCourier]fake courier[/fakeCourier], [phishing]phishing[/phishing] mails, and reading what people post about themselves until you can [doxxing]dox[/doxxing] them. Most data leaks begin with someone being polite to a stranger.',
         '通过欺骗人而不是电脑来获取信息。常见手法：假装成[fakeCourier]假快递员[/fakeCourier]打电话、[phishing]诈骗邮件[/phishing]、阅读人们自己公开的内容，直到能[doxxing]人肉搜索[/doxxing]出对方。大部分信息泄露，都从某人对陌生人有礼貌开始。'),
        'wiki_social')]
    P['phishing'] = [wiki(('Phishing', '诈骗邮件'), ('Security', '信息安全'), ('Phishing', '诈骗邮件'),
        [('Bait: a fake login page', '手法：假的登录页面'), ('Defence: 2-step login', '防御：两步验证')],
        ('A fake message that looks like it comes from a bank or a social network ("Unusual login! Click here"). The link leads to a copy of the real page that steals the password. Spelling mistakes such as "metay0u" are a classic sign.',
         '伪装成银行或社交网站寄来的假讯息（“异常登录！点这里”）。链接会通往一个仿冒的页面，偷走你输入的密码。像“metay0u”这样的拼写错误是典型特征。'),
        'wiki_phishing')]
    P['doxxing'] = [wiki(('Doxxing', '人肉搜索'), ('Internet culture', '网络文化'), ('Doxxing', '人肉搜索'),
        [('Result: name, address, routine', '结果：姓名、地址、作息'), ('Legal? Often not', '合法吗？通常不')],
        ('Collecting and publishing someone\'s private details (real name, home, workplace, phone). It is often paid for by people who are not allowed near the victim, such as someone with a [restrainingOrder]restraining order[/restrainingOrder]. Board users call it a "[bounty]bounty[/bounty]".',
         '收集并公开某人的私人资料（真名、住址、工作地点、电话）。花钱请人做这件事的，常常是不被允许接近受害者的人，例如被下了[restrainingOrder]禁止令[/restrainingOrder]的人。论坛用户把它叫做“[bounty]赏金[/bounty]”。'),
        'wiki_doxxing')]
    P['dnsLeak'] = [wiki(('DNS leak', 'DNS泄漏'), ('Networks', '网络'), ('DNS leak', 'DNS泄漏'),
        [('Common in: [vpn]free VPNs[/vpn]', '常见于：[vpn]免费VPN[/vpn]'), ('Reveals: your real IP', '暴露：你的真实IP')],
        ('When a VPN sends your address questions ("where is metayou.com?") outside the tunnel. Anyone watching the network can see who you really are and roughly where you live. Works in both directions: a watcher\'s relay can leak too.',
         'VPN把你的域名查询（“metayou.com在哪？”）送到隧道外面。任何在监看网络的人都能看到你是谁，以及你大概住在哪。这是双向的：监视者的中继也一样会泄漏。'),
        'wiki_dns')]
    P['phototaxis'] = [wiki(('Phototaxis', '趋光性'), ('Biology', '生物学'), ('Phototaxis', '趋光性'),
        [('Example: moths', '例子：飞虫'), ('Cause: still debated', '原因：仍有争议')],
        ('The movement of an animal towards (or away from) light. Moths circle street lamps and screens until they are exhausted. Some hackers choose the moth as a symbol; few of them read the end of the article.',
         '动物朝光源（或远离光源）移动的行为。飞虫会绕着路灯和屏幕打转，直到累死为止。有些黑客把飞虫当作自己的标志；很少人读到这篇文章的结尾。'),
        'wiki_moth')]
    P['restrainingOrder'] = [wiki(('Restraining order', '禁止令'), ('Law', '法律'), ('Restraining order', '禁止令'),
        [('Distance: usually 500 m', '距离：通常五百米'), ('Breaking it: arrest', '违反：逮捕')],
        ('A court order that forbids a person to approach or contact someone. Breaking it, even through a hired third party, is a crime. Victims are advised to report any new contact to the police tip line [policeLine]555-0110[/policeLine].',
         '法院禁止某人接近或联络另一人的命令。即使是透过雇用的第三方违反，也属于犯罪。受害者若再被联络，建议拨打警方举报热线[policeLine]555-0110[/policeLine]。'),
        'wiki_court')]
    # --- Metayou profiles
    P['noraVance'] = [meta(('[noraVance]Nora Vance[/noraVance]', '[noraVance]诺拉·万斯[/noraVance]'),
        ('Baker at [sweetCrumb]Sweet Crumb[/sweetCrumb]. Draws cats. Lives on coffee.', '[sweetCrumb]甜屑面包店[/sweetCrumb]的面包师。爱画猫。靠咖啡活着。'),
        ('Baker / artist', '面包师、画画'), 'nora_profile',
        [(('[biscuit]Biscuit[/biscuit] is five!', '[biscuit]饼干[/biscuit]五岁啦！'), 'post_cat'),
         (('Morning shift again.', '又是早班。'), 'post_bakery'),
         (('My [bike]blue bike[/bike].', '我的[bike]自行车[/bike]。'), 'post_bike')])]
    P['eliasKrumm'] = [meta(('[eliasKrumm]Elias Krumm[/eliasKrumm]', '[eliasKrumm]埃利亚斯·克鲁姆[/eliasKrumm]'),
        ('Last active 2 years ago. "Online as [m0th]m0th[/m0th] now. Don\'t look for me here."', '两年前最后上线。“现在网名是[m0th]m0th[/m0th]。别在这里找我。”'),
        ('[nightShift]Night shift[/nightShift], gas station', '加油站[nightShift]夜班[/nightShift]'), 'elias_profile',
        [(('My cat [byte]Byte[/byte] owns my keyboard.', '我的猫[byte]字节[/byte]霸占了我的键盘。'), 'post_byte'),
         (('Night shift. Again.', '又是夜班。'), 'post_gas'),
         (('Happy birthday Mom!', '妈妈生日快乐！'), 'post_cake')])]
    # --- map, phone book, news results
    P['kestrelLane'] = [{'type': 'map', 'image': img('map_kestrel'), 'text': T('[kestrelLane]Kestrel Lane[/kestrelLane]', '[kestrelLane]红鹰巷[/kestrelLane]'), 'position': ''}]
    P['policeLine'] = P['cityPolice'] = [{'type': 'guide', 'name': T('[cityPolice]City Police[/cityPolice] - Cybercrime tip line', '[cityPolice]市警察局[/cityPolice] —— 网络犯罪举报热线'),
                        'address': T('Central Station', '中央警局'), 'phone': T('[policeLine]555-0110[/policeLine]', '[policeLine]555-0110[/policeLine]')}]
    P['dorianPell'] = [news_result(('City Courier (2 months ago)', '城市快报（两个月前）'),
        ('Restraining order against local man', '法院对本地男子发出禁止令'),
        ('[dorianPell]Dorian Pell[/dorianPell] must stay 500 m from his ex.', '[dorianPell]多里安·佩尔[/dorianPell]必须远离前伴侣五百米。'),
        ('Pell followed the woman to her workplace for months. A [restrainingOrder]restraining order[/restrainingOrder] was granted on Monday.',
         '佩尔几个月来一直跟踪该女子到她工作的地方。法院于周一批准了[restrainingOrder]禁止令[/restrainingOrder]。'), 'news_dorian')]
    # the deduction "her ex" + the restraining order finds the same court record (another route to his name)
    P['crowEx_restrainingOrder'] = P['dorianPell']
    P['crow_dorianPell'] = [web('http://oldcars.web/forum/user/crow', 'web_darkboard',
        block(41, 34, 270, 22, 'OLD CARS FORUM - user "[crow]Crow[/crow]"', '老爷车论坛 —— 用户“[crow]乌鸦[/crow]”', color=RED),
        block(41, 10, 270, 22, 'Signature: "[dorianPell]D. Pell[/dorianPell] - restoring a \'79 coupe"', '签名档：“[dorianPell]D.佩尔[/dorianPell] —— 修复一辆79年的双门车”', color=LIGHT),
        block(41, -14, 270, 22, 'Last post: "A [restrainingOrder]court order[/restrainingOrder] won\'t keep me from what\'s mine."', '最后一篇：“一张[restrainingOrder]法院命令[/restrainingOrder]挡不住我拿回属于我的东西。”', color=LIGHT),
        block(41, -38, 270, 22, 'Same avatar as the DarkBoard user [crow]Crow[/crow].', '和暗板论坛用户[crow]乌鸦[/crow]用同一个头像。', color=(200, 90, 70)))]
    # "her ex" alone: the general stalking article (the court record needs his name, or "her ex" + "restraining order")
    P['noraHiding'] = [wiki(('Stalking', '跟踪骚扰'), ('Law', '法律'), ('Stalking', '跟踪骚扰'),
        [('Typical stalker: an ex-partner', '常见的跟踪者：前任'), ('Help: [policeLine]555-0110[/policeLine]', '求助：[policeLine]555-0110[/policeLine]')],
        ('Repeatedly following, watching or contacting someone against their will. Most victims know their stalker; many move house and hide their routines online. Hired "researchers" who find the new address are a growing problem.',
         '违背对方意愿，反复跟随、监视或联络对方。大部分受害者认识跟踪者；很多人会搬家，并在网上隐藏自己的作息。被雇来找出新住址的“调查员”是越来越严重的问题。'),
        'wiki_stalking')]
    P['mothComing'] = [wiki(('Doorstep safety', '门口安全'), ('Home', '居家'), ('Doorstep safety', '门口安全'),
        [('At night: do not open', '夜里：不要开门'), ('Use: the peephole', '使用：猫眼')],
        ('Most unwanted visitors knock first. Look through the peephole, keep the chain on and talk through the door. If a visitor knows things about you that they should not, do not let them in.',
         '大部分不速之客会先敲门。先从猫眼看，挂上门链，隔着门说话。如果来访的人知道一些他不该知道的事，不要让他进来。'),
        'end_door')]
    P['crowEx'] = P['noraHiding']
    # the deduction "separated" + the bakery: a notice that gives the police line early
    P['noraHiding_sweetCrumb'] = [web('http://sweetcrumb.web/notice', 'web_bakery',
        block(120, 58, 118, 30, 'NOTICE', '公告', size=110, font='tempestaBold', color=(192, 96, 122)),
        block(120, 26, 118, 60, 'We removed our staff photos at [noraVance]Nora[/noraVance]\'s request.', '应[noraVance]诺拉[/noraVance]的要求，我们已撤下员工照片。', color=DARK),
        block(120, -20, 118, 60, 'If a man asks about our staff, please call [policeLine]555-0110[/policeLine].', '如果有男人打听我们的员工，请拨打[policeLine]555-0110[/policeLine]。', color=DARK))]
    # m0th alone is just a name shared with a garage band; with "amateur hacker" the search finds his DarkBoard ad
    P['m0th'] = [wiki(('M0TH (band)', 'M0TH（乐队）'), ('Music', '音乐'), ('M0TH', 'M0TH'),
        [('Genre: garage rock', '类型：车库摇滚'), ('Songs released: 1', '发行歌曲：1首')],
        ('A garage band from the north side that released one song, "Lamp", and broke up the same week. Not to be confused with the many internet users who took the same name.',
         '北区的一支车库乐队，只发过一首歌“灯”，同一周就解散了。别和许多用了同样网名的网友搞混。'),
        'wiki_band')]
    P['mothHacker'] = [wiki(('Amateur hacker', '业余黑客'), ('Internet culture', '网络文化'), ('Script kiddie', '脚本小子'),
        [('Learns from: videos', '学习来源：视频'), ('Typical mistake: a [vpn]free VPN[/vpn]', '常见错误：[vpn]免费VPN[/vpn]')],
        ('Someone who uses other people\'s tools and tutorials without really understanding them. They are cheap to hire, and easy to trace: most of them are caught because of their own leaks.',
         '用别人的工具和教学视频，却不太懂原理的人。雇他们很便宜，追查他们也很容易：大部分人都是因为自己泄漏了信息而被抓。'),
        'wiki_dns')]
    # Nora's married name: an old wedding notice that links her to Dorian
    P['noraPell'] = [news_result(('City Courier (6 years ago)', '城市快报（六年前）'),
        ('Weddings this week', '本周婚讯'),
        ('[noraPell]Nora Pell[/noraPell] (née Vance) and [dorianPell]Dorian Pell[/dorianPell].', '[noraPell]诺拉·佩尔[/noraPell]（原姓万斯）与[dorianPell]多里安·佩尔[/dorianPell]。'),
        ('The couple met at a car show. "He never lets me out of his sight," the bride laughed.',
         '两人在一次车展上认识。新娘笑着说：“他从来不让我离开他的视线。”'), 'news_wedding')]
    P['m0th_mothHacker'] = [news_result(('DarkBoard #jobs', '暗板论坛 #工作'), ('m0th: "I find anyone. Cheap."', 'm0th：“什么人都找得到。便宜。”'),
        ('Posted through a [vpn]free VPN[/vpn].', '透过[vpn]免费VPN[/vpn]发出。'),
        ('Reply fast, pay in coins. No questions. Contact on [darkBoard]DarkBoard[/darkBoard].',
         '回复快，用币付款。不问问题。联系方式：[darkBoard]暗板论坛[/darkBoard]。'), 'moth_ad')]
    P['intruder'] = [news_result(('The New Truth', '新真相报'), ('Intruders: the new "delivery men"', '闯入者：新型“快递员”'),
        ('Police warn of strangers who know too much.', '警方提醒：小心知道太多的陌生人。'),
        ('Most [intruder]intruders[/intruder] this year found their victims online. Police ask anyone with information to call [policeLine]555-0110[/policeLine].',
         '今年大部分[intruder]闯入者[/intruder]都是在网上找到受害者的。警方呼吁知情者拨打[policeLine]555-0110[/policeLine]。'), 'news_intruder')]
    return P
