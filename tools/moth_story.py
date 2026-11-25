"""
Story data for the "Moth Screen" cage (id mothScreen).

Elias Krumm, 19, handle m0th: a beginner hacker who takes a doxxing job from a DarkBoard user called Crow.
The player watches his desktop and hears his microphone through the Primate Observation Club relay.
Around day 4 he finds the relay process, traces it, and starts hunting the observer: the player.

Branch variables (set by the player's calls, chat answers and gifts):
  noraWarned   player phoned Nora and warned her                 -> she locks her account and moves out
  copsMoth     player reported m0th to the tip line              -> police raid, cage ends early
  copsDorian   player reported Dorian Pell (Crow)                -> Crow is arrested, Elias is safe from him
  chatClub / chatMirror / chatHelp / chatLie / chatThreat         -> the player's answer in m0th's chat
  mothVisited  player opened the door to him on day 7
"""
CAGE = 'mothScreen'
TXT = []   # (en, zh)

def T(en, zh):
    TXT.append((en, zh))
    return '%s_%d~%s' % (CAGE, len(TXT), en)

# ------------------------------------------------------------------ layout (image coords: top-left of the sprite)
H = 174
SIZE = {'browser': (166, 114), 'term': (126, 72), 'video': (108, 80), 'chat': (102, 106), 'notes': (80, 94), 'board': (146, 100),
        'taskmgr': (114, 82), 'cam': (86, 72), 'popup': (98, 36), 'postit': (40, 30), 'label': (46, 15), 'cursor': (9, 13),
        'voice': (40, 11), 'clock': (26, 8), 'saver': (15, 11), 'host': (1, 1),
        'wall': (252, 174), 'overlay': (252, 174), 'black': (252, 174), 'lost': (252, 174), 'reflect': (252, 174)}
SLOT = {'browser': (80, 6), 'term': (22, 92), 'video': (24, 8), 'chat': (146, 52), 'notes': (24, 12), 'board': (54, 24),
        'taskmgr': (96, 36), 'cam': (156, 10), 'popup': (78, 70), 'postit': (-1, 125), 'label': (145, 161), 'cursor': (126, 80),
        'voice': (106, 150), 'clock': (224, 165), 'saver': (118, 80), 'host': (78, 40),
        'wall': (0, 0), 'overlay': (0, 0), 'black': (0, 0), 'lost': (0, 0), 'reflect': (0, 0)}
Z = {'wall': 0, 'label': -2, 'postit': -35, 'notes': -10, 'board': -12, 'term': -14, 'video': -16, 'taskmgr': -18, 'browser': -20,
     'chat': -22, 'cam': -24, 'popup': -30, 'black': -60, 'saver': -62, 'lost': -64, 'clock': -66, 'cursor': -70,
     'voice': -80, 'host': -81, 'overlay': -90, 'reflect': -95}

def pos(name, L=None, Tp=None):
    """Script position (bottom-left pivot, y up) of a sprite whose top-left is at image coords (L, T)."""
    l, t = SLOT[name] if L is None else (L, Tp)
    w, h = SIZE[name]
    return {'x': l, 'y': H - (t + h)}

WINDOWS = ['browser', 'term', 'video', 'chat', 'notes', 'board', 'taskmgr', 'cam', 'popup', 'postit', 'black', 'saver', 'lost']

# ------------------------------------------------------------------ action helpers
def say(en, zh, who='voice', **c):
    a = {'action': 'say', 'id': who, 'text': T(en, zh)}
    if who == 'voice': a.update(subanimation='habla', endanimation='default')
    return cond(a, **c)

def host(en, zh, ep='ep7', **c):
    return [cond({'action': 'say', 'id': 'host', 'text': T(en, zh)}, **c)]

def wait(t, who='voice', **c): return cond({'action': 'wait', 'time': t, 'id': who}, **c)

def anim(obj, name, waitFinish=False, **c): return cond({'action': 'animation', 'id': obj, 'animation': name, 'waitFinish': waitFinish}, **c)

def on(obj, a=None, at=None, **c):
    out = [{'action': 'enable', 'id': obj}]
    if at is not None: out.append({'action': 'setin', 'id': obj, 'position': pos(obj, *at)})
    if a: out.append({'action': 'animation', 'id': obj, 'animation': a, 'waitFinish': False})
    return [cond(x, **c) for x in out]

def off(*objs, **c): return [cond({'action': 'disable', 'id': o}, **c) for o in objs]

def setv(name, value='true', **c): return cond({'action': 'setVar', 'id': 'voice', 'name': name, 'value': value}, **c)

def cur(x, y, t=1.0, **c):
    """Move the cursor tip to image coords (x, y)."""
    return cond({'action': 'move', 'id': 'cursor', 'position': {'x': x, 'y': H - y - 13}, 'time': t}, **c)

def click(**c): return [cond({'action': 'animation', 'id': 'cursor', 'animation': 'click', 'waitFinish': True}, **c),
                        cond({'action': 'animation', 'id': 'cursor', 'animation': 'default', 'waitFinish': False}, **c)]

def comment(s): return {'action': 'comment', 'text': s}

def cond(a, **c):
    if 'if_' in c and c['if_']: a['if'] = c['if_']
    if 'ifNot' in c and c['ifNot']: a['ifNot'] = c['ifNot']
    return a

def C(acts, if_=None, ifNot=None):
    """Applies a condition to every action of a list (recursively flattened)."""
    out = []
    for a in flat(acts):
        a = dict(a)
        if if_: a['if'] = ','.join(filter(None, [a.get('if'), if_]))
        if ifNot: a['ifNot'] = ','.join(filter(None, [a.get('ifNot'), ifNot]))
        out.append(a)
    return out

def flat(x):
    if isinstance(x, dict): return [x]
    out = []
    for i in x: out += flat(i)
    return out

def desk(clock, *shown):
    """Scene opening: the screen as it is when the scene starts. shown = (obj, anim) or obj."""
    names = {s if isinstance(s, str) else s[0] for s in shown}
    acts = [{'action': 'blinkLed', 'id': 'voice'}]
    acts += off(*[w for w in WINDOWS if w not in names])
    acts += on('label') + on('cursor', 'default')  # (clock param kept as a note of the on-screen time; the game UI shows the real clock)
    for s in shown:
        if isinstance(s, str): acts += on(s)
        else: acts += on(s[0], s[1])
    acts += [anim('voice', 'default'), anim('reflect', 'sleep')]
    return acts

def sleep_screen(reflect='sleep'):
    """Screen goes dark: black + bouncing moth screensaver; the reflection is only visible with night vision.
    The cage LED goes off here: nothing happens on a sleeping screen (it stayed lit for hours before, v2.0.2)."""
    return ([{'action': 'stopLed', 'id': 'voice'}] + off(*[w for w in WINDOWS if w not in ('black', 'saver')]) + off('cursor', 'label') + on('black') + on('saver', 'default', at=(118, 80))
            + [anim('reflect', reflect)]
            + [{'action': 'move', 'id': 'saver', 'position': pos('saver', 40, 40), 'time': 6},
               {'action': 'move', 'id': 'saver', 'position': pos('saver', 200, 120), 'time': 8},
               {'action': 'move', 'id': 'saver', 'position': pos('saver', 120, 20), 'time': 7},
               {'action': 'move', 'id': 'saver', 'position': pos('saver', 60, 130), 'time': 7}])

END = [{'action': 'stopLed', 'id': 'voice'}]

GENERIC = {}   # named event lists, run in the middle of a scene by ev()
def ev(name, events):
    GENERIC[name] = events
    return {'action': 'triggerEvents', 'events': name, 'id': 'voice'}

# ------------------------------------------------------------------ scenes
SCENES = {}
def scene(name, hour, modify, goto, *body, start=None, finish=None, comment_=None):
    s = {'camera': 1, 'hour': str(hour), 'modify': modify}
    if goto: s['goto'] = goto
    if comment_: s['_comment'] = comment_
    if start: s['startEvents'] = start
    if finish: s['finishEvents'] = finish
    s['script'] = flat(list(body))
    SCENES[name] = s

# start: everything hidden but the desktop, screen asleep
scene('start', 0, 'now', 'd1_boot',
      off(*WINDOWS), on('black'), on('saver', 'default'), off('cursor', 'label'), [anim('reflect', 'sleep')],
      comment_='Initial state: monitor asleep.')

# ================================================================== DAY 1
scene('d1_boot', 9, 'today', 'd1_tutorial',
      desk('09:00'),
      wait(1), off('black', 'saver'), on('cursor', 'wait'), wait(2),
      say('*yawn* ...Morning, machine. Well. Afternoon. Night shift life.', '*哈欠*...早啊，机器。好吧，是下午了。上夜班的人就这样。'),
      anim('cursor', 'default'),
      say('Meow.', '（猫叫声）'),
      say('Byte, get off the keyboard. No. Off.', '[byte]字节[/byte]，从键盘上下来。不行。下来。'),
      say('Twelve hours of sleep and I still feel like a deleted file.', '睡了十二个小时，我还是觉得自己像个被删掉的文件。'),
      cur(196, 104, 1.5), click(),
      say('"User: m0th." Yeah. That\'s me.', '“用户：[m0th]m0th[/m0th]。”对，就是我。'),
      say('m0th. Because moths go where the light is.', 'm0th。因为飞虫总是往有光的地方去。'),
      say('...And because "Shadow_Reaper" was taken. Twice.', '...也因为“暗影死神”这个名字被人用了。两次。'),
      say('Moths fly to light. It\'s called phototaxis. I looked it up. Very hacker.', '飞虫会飞向光。这叫趋光性。我查过的。很黑客。'),
      wait(2), END)

scene('d1_tutorial', 10.5, 'today', 'd1_job',
      desk('10:00'),
      cur(60, 40, 1.2), click(),
      on('video', 'ep7', at=(24, 8)), wait(1),
      say('Okay. Episode seven. Today I become dangerous.', '好。第七集。今天我要变成一个危险人物。'),
      anim('video', 'ep7talk'),
      host('Welcome back to H4CK SCHOOL.', '欢迎回到 [h4ckSchool]H4CK SCHOOL[/h4ckSchool]。'),
      host('Forget firewalls. The weakest part of any system...', '忘掉防火墙吧。任何系统最弱的部分...'),
      host('...is the human sitting in front of it.', '...都是坐在它前面的那个人。'),
      host('This is called social engineering.', '这就叫做[socialEngineering]社会工程学[/socialEngineering]。'),
      anim('video', 'ep7'),
      say('Social engineering. Sounds like a job. A real one.', '社会工程学。听起来像个正经职业。'),
      anim('video', 'ep7talk'),
      host('People post everything. Pets. Jobs. Their coffee.', '人们什么都往网上发。宠物、工作、他们的咖啡。'),
      host('Every photo is a door. You just walk in.', '每一张照片都是一扇门。你只要走进去。'),
      host('Like and subscribe. Stay invisible.', '记得点赞订阅。保持隐身。'),
      anim('video', 'ep7'),
      say('Stay invisible. Write that down, Byte.', '保持隐身。记下来，字节。'),
      say('...She is licking her butt. Fine. I\'ll remember it myself.', '...她在洗脸。行吧，我自己记。'),
      wait(1), cur(122, 12, 1), click(), off('video'),
      wait(2), END)

scene('d1_job', 13, 'today', 'd1_profile',
      desk('13:00'),
      cur(70, 160, 1), click(),
      on('chat', 'empty', at=(146, 52)), wait(1),
      say('DarkBoard, my second home. Anything for me today?', '[darkBoard]暗板论坛[/darkBoard]，我的第二个家。今天有活吗？'),
      anim('chat', 'job'),
      wait(2),
      say('Huh. Someone called Crow. Private message.', '嗯？一个叫[crow]乌鸦[/crow]的人。私信。'),
      say('"Got a job for you. Find where she lives."', '“有活给你。找出她住在哪。”'),
      say('"Nora Vance. 300 coins."', '“[noraVance]诺拉·万斯[/noraVance]。300币。”'),
      wait(1),
      say('Three hundred! That\'s rent. That\'s rent AND pizza.', '三百！这是房租。这是房租加披萨。'),
      say('Finding an address. How hard can that be?', '找个地址而已。能有多难？'),
      say('On DarkBoard they call this doxxing. Sounds cooler than "stalking".', '在暗板论坛上这叫人肉搜索。比“跟踪”好听多了。'),
      say('Typing... "Easy. Deal."', '打字...“小意思。成交。”'),
      anim('chat', 'jobFull'),
      say('My first [bounty]bounty[/bounty]. Mom said I\'d never earn money with "that computer".', '我的第一笔[bounty]赏金[/bounty]。妈妈说我用“那台电脑”永远赚不到钱。'),
      wait(1), on('notes', 'n0', at=(24, 12)), anim('notes', 'n1'),
      say('Target file. Very professional.', '目标档案。非常专业。'),
      wait(2), END)

scene('d1_profile', 16, 'today', 'd1_pizza',
      desk('16:00', ('notes', 'n1')),
      cur(150, 30, 1.2), click(), on('cursor', 'wait'),
      on('browser', 'meta', at=(80, 6)), anim('cursor', 'default'),
      say('There you are, Nora Vance. Public profile. Rookie.', '找到你了，诺拉·万斯。公开账号。菜鸟。'),
      say('"Baker. Artist. Cat mom." Okay, okay.', '“面包师。画画的。猫奴。”好好好。'),
      cur(110, 62, 1), say('Post one. An orange cat. "Biscuit turns five today!"', '第一条。一只橙色的猫。“[biscuit]饼干[/biscuit]今天五岁啦！”'),
      say('Byte, look. A cat. Your enemy.', '字节，看。一只猫。你的敌人。'),
      say('Mrrrrow.', '（猫叫声）'),
      cur(110, 82, 1), say('Post two. "Morning shift at Sweet Crumb again."', '第二条。“又是[sweetCrumb]甜屑面包店[/sweetCrumb]的早班。”'),
      say('So she works at a bakery. Note.', '所以她在面包店工作。记下。'),
      anim('notes', 'n3'),
      cur(110, 98, 1), say('Post three. A blue bike. "My baby. Don\'t you dare steal her."', '第三条。一辆蓝色自行车。“我的宝贝。谁敢偷试试。”'),
      say('Blue bike. She rides to work.', '[bike]蓝色自行车[/bike]。她骑车上班。'),
      anim('notes', 'n5'),
      say('This is too easy. People are insane.', '这也太简单了。人都疯了吧。'),
      say('...I mean. Lucky for me.', '...我是说。对我来说是好事。'),
      wait(2), END)

scene('d1_pizza', 20, 'today', 'd1_night',
      desk('20:00', ('browser', 'resetEmpty'), ('notes', 'n5')),
      say('Episode seven said: try the password reset.', '第七集说了：试试重设密码。'),
      say('"Name of your first pet." She told the whole world.', '“你第一只宠物的名字。”她已经告诉全世界了。'),
      cur(150, 60, 1), click(),
      say('F... L... U... F... F... Y.', 'F...L...U...F...F...Y。'),
      anim('browser', 'resetFail'),
      say('Wrong?! What kind of person doesn\'t call a cat Fluffy?', '错了？！哪有人养猫不叫毛毛的？'),
      say('Wait. The cat was Biscuit. I literally wrote it down.', '等等。猫叫饼干。我刚刚自己写下来的。'),
      say('...Two tries left. I\'ll do it tomorrow. With a plan.', '...还剩两次。明天再说。要有计划。'),
      wait(1), on('popup', 'pizza', at=(78, 70)),
      say('Hello, Pizza Now? Yeah. One large pepperoni.', '喂，披萨现在？对。一个大号意式香肠。'),
      say('Address: 22 Gorse Street, flat 3B.', '地址：[mothAddress]戈尔斯街22号3B[/mothAddress]。'),
      say('Phone? ...Yeah, this one. Buzzer\'s broken, just knock.', '电话？...对，就这个号码。门铃坏了，直接敲门。'),
      say('Name? Uh... m0th. With a zero. ...Yes, really.', '名字？呃...m0th。用零。...对，真的。'),
      off('popup'),
      say('Hackers need to eat too.', '黑客也要吃饭的。'),
      wait(2), END)

scene('d1_night', 23, 'today', 'd2_vpn',
      desk('23:00', ('browser', 'meta')),
      say('She has two hundred friends. I have Byte.', '她有两百个好友。我有字节。'),
      say('And Byte only loves me because I own the can opener.', '而字节爱我只是因为开罐器在我手上。'),
      wait(2),
      say('Mom left a voicemail. "Are you eating? Are you looking for work?"', '妈妈留了语音。“有没有好好吃饭？有没有在找工作？”'),
      say('I have work, Mom. Freelance. Very confidential.', '我有工作啊，妈。自由职业。高度机密。'),
      say('Shift starts at nine. My [nightShift]night shift[/nightShift] at the gas station. Glamorous.', '九点上班。加油站的[nightShift]夜班[/nightShift]。多光鲜。'),
      say('Tomorrow I quit. Maybe.', '明天我就辞职。大概吧。'),
      wait(2), say('See you later, internet.', '待会见，互联网。'),
      sleep_screen('sleep'), wait(10), END)

# ================================================================== DAY 2
scene('d2_vpn', 10, 'nextAvailable', 'd2_phish',
      desk('10:00'),
      cur(60, 40, 1), click(), on('video', 'ep12', at=(24, 8)),
      anim('video', 'ep12talk'),
      host('Episode twelve. Never touch a target from your real IP.', '第十二集。永远不要用你自己的IP碰目标。'),
      host('Use a VPN. A good one. Not a free one.', '用VPN。好的那种。不要用免费的。'),
      anim('video', 'ep12'),
      say('Good ones cost money. I have... 4 coins.', '好的要钱。我有...四个币。'),
      off('video'), on('term', 'vpn', at=(22, 92)),
      say('FreeVPN. It says "free" twice. Must be twice as good.', '[vpn]免费VPN[/vpn]。名字里写了两次“免费”。肯定好两倍。'),
      wait(2),
      say('"Warning: DNS leak." Leak? Like water? Whatever.', '“警告：DNS泄漏。”泄漏？像漏水那样？管他呢。'),
      say('I\'m a ghost now.', '我现在是幽灵了。'),
      wait(2), END,
      start=[{'type': 'addNew', 'id': 'newsTipLine'}])

scene('d2_phish', 11.5, 'today', 'd2_call',
      desk('11:00', ('term', 'idle')),
      say('Plan B. If she won\'t give me the password, she\'ll type it for me.', 'B计划。她不给我密码，那就让她亲手输给我。'),
      on('browser', 'phish', at=(80, 6)),
      say('From: security at metay-ZERO-u dot co. Genius.', '寄件人：security@metay零u.co。天才。'),
      say('"Dear user, someone tried to log in." Yes. Me.', '“亲爱的用户，有人试图登录。”对，就是我。'),
      say('"Click here to verify." And then the fake page eats her password.', '“点这里验证。”然后假页面就会吃掉她的密码。'),
      say('This is called [phishing]phishing[/phishing]. Like fishing. But with a PH. For... hacking?', '这叫[phishing]诈骗邮件[/phishing]。英文叫phishing，跟fishing（抓鱼）同音。PH代表...黑客？'),
      cur(222, 100, 1.5), click(), anim('browser', 'phishSent'),
      anim('term', 'phish'),
      say('Sent. Now we wait for the fish.', '发出去了。现在等鱼上钩。'),
      wait(2), END)

scene('d2_call', 13, 'today', 'd2_photo',
      desk('13:00', ('notes', 'n5'), ('browser', 'meta')),
      say('Okay. H4CK SCHOOL says: call them. Be confident.', '好。H4CK SCHOOL说：打电话。要自信。'),
      say('*cough* *cough* Deep voice. Deep voice.', '*咳* *咳* 低沉的声音。低沉的声音。'),
      say('Hello, Sweet Crumb? Fast Parcel delivery here.', '喂，甜屑面包店吗？这里是极速快递。'),
      say('I have a package for a Nora Vance. She\'s not answering.', '我有一个给诺拉·万斯的包裹。她不接电话。'),
      say('Could you give me her number? The one I have is wrong.', '能给我她的号码吗？我这个好像是错的。'),
      wait(2),
      say('Yes... yes... 555-0147. Thank you!', '是...是...555-0147。谢谢！'),
      say('Oh, she finishes at six? And she always takes the bike? Great, great.', '哦，她六点下班？她都骑车？很好，很好。'),
      say('Have a nice day, ma\'am!', '祝您愉快，女士！'),
      on('postit', at=(-1, 125)), anim('notes', 'n6'),
      say('I AM A [fakeCourier]FAKE COURIER[/fakeCourier]. AND IT WORKED.', '我是一个[fakeCourier]假快递员[/fakeCourier]。而且成功了！'),
      say('Post-it. Very important. Do not lose, m0th.', '贴张便利贴。非常重要。别弄丢了，m0th。'),
      wait(2), END)

scene('d2_photo', 17, 'today', 'd2_crow',
      desk('17:00', ('notes', 'n6'), 'postit'),
      cur(150, 30, 1), click(), on('browser', 'search', at=(80, 6)),
      say('"How to find an address from a photo." Easy, it says.', '“怎么从照片找出地址。”上面说很简单。'),
      say('"Reflections give you away." Interesting.', '“反光会出卖你。”有意思。'),
      say('H4CK SCHOOL calls this OSINT. Open-source intelligence. Free stuff people leave lying around.', 'H4CK SCHOOL把这叫做公开情报。人们自己乱丢在网上的免费资料。'),
      anim('browser', 'photo'),
      say('Her breakfast photo. Coffee, croissant, window.', '她的早餐照。咖啡、牛角包、窗户。'),
      wait(2),
      say('Wait. There. In the glass.', '等等。那里。玻璃上。'),
      anim('browser', 'photoMark'),
      say('A street sign. Backwards. L... N... L-E-R-T-S-E-K.', '一个路牌。反着的。L...N...L-E-R-T-S-E-K。'),
      say('Flip it. KESTREL LN. Kestrel Lane!', '反过来。KESTREL LN。[kestrelLane]红鹰巷[/kestrelLane]！'),
      anim('browser', 'map'), anim('notes', 'n7'),
      say('She eats breakfast at home. Facing the street. Kestrel Lane.', '她在家吃早餐。对着街。红鹰巷。'),
      say('I did it. I actually did it. I\'m Sherlock Holmes with a modem.', '我做到了。我真的做到了。我是带着调制解调器的福尔摩斯。'),
      wait(2), END)

scene('d2_crow', 21, 'today', 'd2_night',
      desk('21:00', ('notes', 'n7'), 'postit', ('browser', 'map')),
      on('chat', 'push', at=(146, 52)), wait(2),
      say('Crow again. "Progress?"', '乌鸦又来了。“进度？”'),
      say('Typing... "Got her street."', '打字...“找到她的街了。”'),
      say('"I need the number. And her schedule."', '“我要门牌号。还有她的作息。”'),
      wait(1),
      say('...Her schedule? Why would you need her schedule?', '...她的作息？你要她的作息干嘛？'),
      say('"She owes me."', '“她欠我的。”'),
      anim('chat', 'pushFull'),
      wait(2),
      say('She owes him. Okay. Money, probably.', '她欠他。好吧。大概是钱。'),
      say('People who owe money should pay it back. That\'s... fair.', '欠钱就该还。这...很公平。'),
      say('Right, Byte?', '对吧，字节？'),
      wait(2), say('...Byte?', '...字节？'),
      wait(2), END)

scene('d2_night', 23.5, 'today', 'd3_result',
      desk('23:00', ('notes', 'n7'), 'postit'),
      say('Still no fish.', '鱼还没上钩。'),
      say('Shift time. Normal people sleep at night. Not me.', '该上班了。正常人晚上睡觉。我不是。'),
      sleep_screen('sleep'), wait(10), END)

# ================================================================== DAY 3
scene('d3_result', 10, 'nextAvailable', 'd3_mom',
      desk('10:00', ('notes', 'n7'), 'postit', ('term', 'phish')),
      say('Morning, fish. Did we bite?', '早啊，小鱼。咬钩了吗？'),
      # warned: she locked everything
      C([on('browser', 'private', at=(80, 6)),
         say('What. "This account is private."', '什么。“此账号为私密账号。”'),
         say('Photos removed. Everything. Overnight.', '照片全删了。全部。一夜之间。'),
         anim('browser', 'resetLocked'),
         say('Two-step login?! She didn\'t even know what that was yesterday!', '两步验证？！她昨天连那是什么都不知道！'),
         on('popup', 'denied', at=(78, 70)),
         say('Somebody warned her. Somebody TOLD her.', '有人警告了她。有人告诉了她。'),
         say('But nobody knows about this. Nobody but me and Crow.', '可是没人知道这件事。只有我和乌鸦。'),
         off('popup'),
         say('...And Crow wouldn\'t. So who?', '...乌鸦不会说的。那是谁？'),
         ], if_='noraWarned'),
      # not warned: she clicked
      C([on('popup', 'clicked', at=(78, 70)),
         say('SHE CLICKED. SHE CLICKED!', '她点了。她点了！'),
         say('Password: "biscuit2019". Of course.', '密码：“biscuit2019”。当然了。'),
         off('popup'), on('browser', 'inbox', at=(80, 6)),
         say('I\'m in. I\'m inside a real person\'s account.', '我进去了。我进到一个真人的账号里了。'),
         wait(2),
         say('Messages... someone called Dorian.', '私信...一个叫多里安的人。'),
         say('"Answer me." "I know where you work." "You can\'t hide forever."', '“回答我。”“我知道你在哪上班。”“你不能永远躲着。”'),
         say('...That\'s not a friendly guy.', '...这人不太友善。'),
         say('And this one, from the court. "Order granted."', '还有这个，法院寄来的。“申请已批准。”'),
         say('"Report any contact to the police tip line, 555-0110."', '“如有任何联络，请拨打警方举报热线555-0110。”'),
         say('A [restrainingOrder]restraining order[/restrainingOrder]? Against... Dorian?', '[restrainingOrder]禁止令[/restrainingOrder]？针对...多里安？'),
         wait(1),
         say('Not my business. I\'m a professional. Professionals don\'t read.', '不关我的事。我是专业的。专业的人不看内容。'),
         say('...Okay, professionals read a little.', '...好吧，专业的人会看一点点。'),
         ], ifNot='noraWarned'),
      wait(2), END)

scene('d3_mom', 14, 'today', 'd3_number',
      desk('14:00', ('notes', 'n7'), 'postit'),
      say('*ring ring* ...Oh no. It\'s Mom.', '*铃铃铃*...完了。是妈妈。'),
      say('"Elias? Elias, are you eating?" ...She uses my real name like a weapon.', '“埃利亚斯？埃利亚斯，你有没有吃饭？”...她叫我真名的样子像在用武器。'),
      say('Hi Mom! Yes. Yes I\'m eating. Pizza is food.', '嗨妈！对。对我有吃饭。披萨也是饭。'),
      say('Work? I\'m... studying. Computer security.', '工作？我在...学习。电脑安全。'),
      say('No, Mom, I\'m not "hacking the bank". Nobody says it like that.', '不是啦妈，我没有在“黑银行”。没人这样说话的。'),
      say('...Yes, I know Dad says I\'m wasting my life.', '...对，我知道爸说我在浪费生命。'),
      say('I\'m good at this, Mom. For once I\'m good at something.', '我很擅长这个，妈。我终于有一件擅长的事了。'),
      wait(2),
      say('Love you too. Bye.', '我也爱你。拜。'),
      wait(1), say('[mom]Mom[/mom] always ends with "be a good boy".', '[mom]妈妈[/mom]总是用“要听话”结束对话。'),
      wait(2),
      say('BYTE. NO. NOT THE COFFEE.', '字节！不要！不要碰咖啡！'),
      say('*crash*', '*杯子倒了*'),
      say('...My keyboard smells like a latte now.', '...我的键盘现在一股拿铁味。'),
      wait(2), END)

scene('d3_number', 18, 'today', 'd3_paid',
      desk('18:00', ('notes', 'n7'), 'postit'),
      on('board', 's2', at=(54, 24)),
      say('Okay. Board time. Like in the movies.', '好。调查板时间。跟电影里一样。'),
      say('Bakery. Bike. Kestrel Lane. Phone number, 555-0147.', '面包店。自行车。红鹰巷。电话号码，555-0147。'),
      say('The only thing missing is the house number.', '只差门牌号了。'),
      say('Her old account from before she moved... "Nora Pell". Married name.', '她搬家前的旧账号...“诺拉·佩尔”。婚后的名字。'),
      say('Back to Vance now. Divorced, I guess. Good for her.', '现在改回万斯了。大概是离婚了。挺好的。'),
      C([on('browser', 'photo', at=(80, 6)),
         say('Her account is locked, but I saved the photo before.', '她的账号锁了，但我之前存了照片。'),
         say('The door across the street. A brass number. One... four.', '街对面的门。一个黄铜门牌。一...四。'),
         say('Fourteen. Her place is the one opposite. Kestrel Lane 14.', '十四。她家就在对面。红鹰巷14号。'),
         ], if_='noraWarned'),
      C([on('browser', 'inbox', at=(80, 6)),
         say('Her sister wrote: "Come stay at mine." And Nora said:', '她姐姐写：“来我这儿住吧。”诺拉回：'),
         say('"I\'m fine at number 14. I have a lock."', '“我在14号很好。我有锁。”'),
         say('Kestrel Lane 14.', '红鹰巷14号。'),
         ], ifNot='noraWarned'),
      anim('notes', 'n9'),
      wait(1),
      say('Shift ends at six. She\'s riding home right now.', '六点下班。她现在正骑车回家。'),
      say('...Weird feeling. Knowing where someone is.', '...感觉怪怪的。知道一个人现在在哪里。'),
      say('Like I\'m... standing behind her.', '好像我...站在她身后。'),
      wait(2), END)

scene('d3_paid', 22, 'today', 'd3_night',
      desk('22:00', ('notes', 'n9'), 'postit', ('board', 's2')),
      on('chat', 'paid', at=(146, 52)), wait(1),
      say('Typing: "Kestrel Lane 14." Send.', '打字：“红鹰巷14号。”发送。'),
      setv('addressSold'),
      say('"Good boy."', '“好孩子。”'),
      on('popup', 'paid', at=(78, 70)),
      say('Three hundred coins. Three hundred!', '三百币。三百啊！'),
      off('popup'), anim('chat', 'paidFull'),
      say('"Now delete it all."', '“现在全部删掉。”'),
      say('"Good boy." Mom says that. I hate when strangers say that.', '“好孩子。”妈妈也这么说。我讨厌陌生人这么说。'),
      on('term', 'wipe', at=(22, 92)), wait(2),
      say('Fine. Wiping the target file.', '好吧。抹掉目标档案。'),
      off('notes'), wait(2),
      on('popup', 'camOn', at=(78, 70)),
      say('...Huh?', '...嗯？'),
      say('"Webcam in use." In use by WHO? I\'m not using it.', '“摄像头使用中。”谁在用？我没在用啊。'),
      say('Probably the update thing. It\'s always the update thing.', '大概是更新程序。都是更新程序搞的。'),
      off('popup'),
      wait(2), END)

scene('d3_night', 23.9, 'today', 'd4_news',
      desk('23:50', 'postit'),
      say('I made money today. Real money.', '今天我赚到钱了。真正的钱。'),
      say('So why do I feel like I need a shower?', '那为什么我觉得自己好脏？'),
      sleep_screen('sleep'), wait(10),
      # Dorian goes to Kestrel Lane tonight (unless the police already took him): too late to warn Nora after this
      setv('breakIn', ifNot='dorianStopped'), END)

# ================================================================== DAY 4
scene('d4_news', 10, 'nextAvailable', 'd4_dorian',
      desk('10:00', 'postit'),
      cur(150, 30, 1), click(),
      C([on('browser', 'newsIntruder', at=(80, 6)),
         say('"Intruder on Kestrel Lane."', '“红鹰巷有人闯入。”'),
         say('"A young woman escaped through her kitchen window last night."', '“一名年轻女子昨晚从厨房窗户逃了出去。”'),
         say('"The man broke the lock of number 14."', '“男子弄坏了14号的门锁。”'),
         wait(2),
         say('No. No no no.', '不。不不不。'),
         say('That\'s her. That\'s... the address I sold.', '是她。那是...我卖掉的地址。'),
         ], ifNot='noraWarned,dorianStopped'),
      C([on('browser', 'newsEmpty', at=(80, 6)),
         say('"Break-in at empty Kestrel Lane flat."', '“红鹰巷空屋遭闯入。”'),
         say('"Nobody was home. The tenant had left two days ago."', '“当时无人在家。租客两天前已经离开。”'),
         wait(2),
         say('Number 14. Someone broke in. The night after I sent it.', '14号。有人闯进去了。就在我发出地址的那天晚上。'),
         say('She wasn\'t there. Thank God she wasn\'t there.', '她不在。谢天谢地她不在。'),
         ], if_='noraWarned', ifNot='dorianStopped'),
      C([on('browser', 'search', at=(80, 6)),
         say('"Man arrested on Kestrel Lane. Violated a restraining order."', '“男子在红鹰巷被捕，违反禁止令。”'),
         say('"He was carrying a crowbar. Police acted on an anonymous tip."', '“他身上带着铁棍。警方是接到匿名举报才出动的。”'),
         wait(2),
         say('Kestrel Lane. A crowbar. That\'s... the address I sold.', '红鹰巷。铁棍。那是...我卖掉的地址。'),
         say('Someone stopped him. Before he got to her door.', '有人挡住了他。在他走到她门口之前。'),
         ], if_='dorianStopped'),
      say('"Police ask anyone with information to call the tip line."', '“警方呼吁知情者拨打举报热线。”'),
      wait(2),
      say('This isn\'t about money. It was never about money.', '这跟钱无关。从来就跟钱无关。'),
      say('I did this. I opened the door. Like the video said.', '是我干的。是我开的门。就像影片里说的那样。'),
      say('Every photo is a door...', '每一张照片都是一扇门...'),
      setv('guiltSeen'),
      wait(2), END,
      start=[{'type': 'addNew', 'id': 'newsIntruder', 'ifNot': 'noraWarned,dorianStopped'},
             {'type': 'addNew', 'id': 'newsEmpty', 'if': 'noraWarned', 'ifNot': 'dorianStopped'}])

scene('d4_dorian', 13, 'today', 'd4_relay',
      desk('13:00', 'postit', ('board', 's2')),
      say('Who is Crow. Who ARE you.', '乌鸦是谁。你到底是谁。'),
      on('browser', 'search', at=(80, 6)),
      say('Crow\'s DarkBoard profile. Joined three weeks ago.', '乌鸦的暗板资料。三周前注册的。'),
      say('Same username on an old car forum. With a real name. Idiot.', '他在一个旧汽车论坛用一样的名字。还写了真名。白痴。'),
      anim('browser', 'dorian'),
      say('Dorian Pell.', '[dorianPell]多里安·佩尔[/dorianPell]。'),
      C([say('...The man they arrested. It\'s him. Somebody reported him.', '...就是被抓的那个人。是他。有人举报了他。')], if_='copsDorian'),
      say('"Restraining order granted against local man." It\'s him. Her Dorian.', '“法院对本地男子发出禁止令。”是他。她说的那个多里安。'),
      anim('board', 's3'),
      say('He\'s not allowed near her. So he paid someone to find her.', '他不准靠近她。所以他花钱找人帮他找到她。'),
      say('He paid me.', '他找的是我。'),
      wait(2),
      say('I\'m not a hacker. I\'m a tool. A cheap one.', '我不是黑客。我是工具。还是个便宜货。'),
      wait(2), END)

scene('d4_relay', 17, 'today', 'd4_trace',
      desk('17:00', 'postit', ('board', 's3')),
      say('My fan is screaming. Why is my computer so slow?', '风扇在狂叫。电脑怎么这么慢？'),
      on('taskmgr', 'list', at=(96, 36)),
      wait(2),
      say('Browser, terminal, music... what is this?', '浏览器、终端、音乐...这是什么？'),
      anim('taskmgr', 'found'),
      say('"poc_relay.exe." "mic_hook." "cam_hook."', '“[pocRelay]poc_relay.exe[/pocRelay]。”“mic_hook。”“cam_hook。”'),
      say('Mic hook. Cam hook.', '麦克风钩子。摄像头钩子。'),
      wait(1),
      say('Running for... four days.', '已经运行了...四天。'),
      say('Since the day I started this job.', '从我接下这个活的那天开始。'),
      anim('taskmgr', 'denied'),
      say('"Access denied. Owner: P.O.C." Who is P.O.C.?!', '“拒绝访问。拥有者：P.O.C.”P.O.C.是谁？！'),
      on('term', 'denied', at=(22, 92)),
      say('Kill it. Kill -9. KILL IT.', '杀掉它。kill -9。杀掉啊！'),
      say('"Operation not permitted." On MY computer.', '“操作不被允许。”这是我的电脑！'),
      on('popup', 'battery', at=(78, 70)),
      wait(2),
      say('If there\'s a mic hook... then someone hears this.', '如果有麦克风钩子...那就有人在听。'),
      say('Someone is hearing me RIGHT NOW.', '有人正在听我说话。现在。'),
      wait(3),
      say('...Hello?', '...喂？'),
      wait(3), END)

scene('d4_trace', 21, 'today', 'd4_dark',
      desk('21:00', 'postit', ('board', 's3')),
      on('cam', 'scared', at=(156, 10)),
      say('Step one. No eyes.', '第一步。不准看。'),
      say('Tape. Duct tape. Over the camera.', '胶带。大力胶。贴在摄像头上。'),
      anim('cam', 'taped'),
      say('There. [webcamTape]Taped[/webcamTape]. Look at that, watcher. Nothing.', '好了。[webcamTape]贴住了[/webcamTape]。看吧，偷窥的。什么都看不到。'),
      say('...But you can still see my screen, can\'t you.', '...但你还是看得到我的屏幕，对吧。'),
      on('term', 'trace', at=(22, 92)),
      say('Step two. Follow the wire. [traceroute]Traceroute[/traceroute].', '第二步。顺着线摸过去。[traceroute]追踪路由[/traceroute]。'),
      wait(3),
      say('My router... my provider... stars... and then...', '我的路由器...我的网络商...一堆星号...然后...'),
      say('"[relayServer]relay.primate-obs.club[/relayServer]."', '“[relayServer]relay.primate-obs.club[/relayServer]。”'),
      say('Primate. Observation. Club.', '灵长类。观察。俱乐部。'),
      wait(2),
      say('I\'m being observed. Like a monkey.', '我在被观察。像一只猴子。'),
      say('You put me in a cage.', '你们把我关进了笼子。'),
      anim('board', 's4'),
      wait(2), END)

scene('d4_dark', 2, 'nextAvailable', 'd5_poc',
      desk('02:00'),
      sleep_screen('stare'),
      {'action': 'blinkLed', 'id': 'voice'},   # he whispers to the dark screen: that is activity
      wait(4),
      say('(whisper) I know you\'re there.', '（低语）我知道你在那里。'),
      wait(4),
      say('(whisper) I called in sick. I\'m not going anywhere. I\'m looking at the screen.', '（低语）我请了病假。我哪都不去。我在看着屏幕。'),
      wait(3),
      say('(whisper) It\'s dark. So the glass is a mirror.', '（低语）屏幕黑了。玻璃就变成了镜子。'),
      say('(whisper) Can you see me? I can almost see you.', '（低语）你看得到我吗？我几乎可以看到你。'),
      wait(10), END)

# ================================================================== DAY 5
scene('d5_poc', 10, 'today', 'd5_chat',
      desk('10:00', ('board', 's4')),
      on('browser', 'poc', at=(80, 6)),
      say('primate-obs.club. A black page. An eye. "Members only."', 'primate-obs.club。黑色的页面。一只眼睛。“会员专用。”'),
      say('"Do not feed the monkeys." What does that even mean?', '“请勿喂食猴子。”这到底是什么意思？'),
      wait(2),
      say('It means don\'t touch. Don\'t help. Just watch.', '意思是不要碰。不要帮。只要看。'),
      say('That\'s you, isn\'t it. You\'re a [observer]member[/observer].', '那就是你，对吧。你是[observer]会员[/observer]。'),
      say('You watched me find her. You watched me sell her.', '你看着我找到她。你看着我把她卖掉。'),
      C([say('...No. Somebody warned her. Somebody called.', '...不对。有人警告了她。有人打了电话。'),
         say('Was that you? You don\'t just watch, do you?', '是你吗？你不只是看，对吧？')], if_='noraWarned'),
      C([say('And you did nothing. Just like me.', '而你什么都没做。就跟我一样。')], ifNot='noraWarned'),
      wait(1),
      say('Okay. Let\'s talk, observer.', '好。我们谈谈吧，观察者。'),
      say('Your relay has a mail port. And a chat port.', '你的中继有邮件端口。也有聊天端口。'),
      on('popup', 'sent', at=(78, 70)),
      say('Sent. Check your inbox. Then open your chat.', '发出去了。看看你的收件箱。然后打开你的聊天。'),
      off('popup'), setv('mothChatOn'),
      wait(2), END,
      finish=[{'type': 'addEmail', 'id': 'mothMail'}, {'type': 'setVar', 'name': 'mothChatOn', 'value': 'true'},
              {'type': 'setChat', 'id': 'mothChat', 'showApp': True}])

scene('d5_chat', 15, 'today', 'd5_crow',
      desk('15:00', ('board', 's4')),
      on('chat', 'empty', at=(146, 52)),
      say('Okay. Your answer.', '好。你的回答。'),
      C([say('"I\'m with the Club. You\'ve been selected."', '“我是俱乐部的人。你被选中了。”'),
         say('Selected. Like a lottery. Like... a job offer?', '被选中。像抽奖一样。像...工作邀请？'),
         say('People who watch. People who are never watched.', '看别人的人。永远不会被看的人。'),
         say('...That\'s all I ever wanted, honestly.', '...说实话，那正是我一直想要的。'),
         ], if_='chatClub'),
      C([say('"Just someone watching. Like you watched Nora."', '“只是个看着的人。就像你看着诺拉那样。”'),
         say('That\'s not the same.', '那不一样。'),
         wait(2), say('...It\'s exactly the same, isn\'t it.', '...一模一样，对吧。'),
         say('She felt like this. For days. Because of me.', '她就是这种感觉。好几天。因为我。'),
         ], if_='chatMirror'),
      C([say('"Dorian is using you. Go to the police."', '“多里安在利用你。去报警。”'),
         say('Police. Me. I\'d be the first one they arrest.', '报警。我去。他们第一个抓的就是我。'),
         say('...But she\'d be safe. Maybe.', '...但她会安全。也许吧。'),
         ], if_='chatHelp'),
      C([say('"Wrong person, kid." Nice try, observer.', '“找错人了，小子。”说得好，观察者。'),
         say('Your packets have your fingerprints on them.', '你的数据包上全是你的指纹。'),
         ], if_='chatLie'),
      C([say('"I know where you live." Yeah? Me too, soon.', '“我知道你住哪。”是吗？我很快也会知道。'),
         ], if_='chatThreat'),
      C([say('You read my mail and said nothing.', '你看了我的信，什么都没说。'),
         say('Silent. Like a real Club member.', '一句话都不说。真像个俱乐部会员。'),
         ], ifNot='chatClub,chatMirror,chatHelp,chatLie,chatThreat'),
      say('Closing the port. You had your chance.', '关掉端口了。你已经有过机会了。'),
      setv('mothChatOn', 'unset'), off('chat'),
      wait(2), END)

scene('d5_crow', 19, 'today', 'd5_video',
      desk('19:00', ('board', 's4')),
      C([on('chat', 'banned', at=(146, 52)),
         say('"User Crow was banned. Reason: arrested lol."', '“用户乌鸦已被封禁。原因：被抓了哈哈。”'),
         say('Arrested. Dorian Pell is arrested.', '被抓了。多里安·佩尔被抓了。'),
         say('Someone reported him. You?', '有人举报了他。是你吗？'),
         say('...Thank you. I think I\'m allowed to say thank you.', '...谢谢。我应该可以说声谢谢吧。'),
         ], if_='copsDorian'),
      C([on('chat', 'threat', at=(146, 52)),
         say('Typing: "You used me. You are Dorian Pell."', '打字：“你利用了我。你就是多里安·佩尔。”'),
         wait(2),
         say('"Careful, kid."', '“小心点，小子。”'),
         say('"I found her. I can find you."', '“我找得到她。我也找得到你。”'),
         wait(2),
         say('He knows where I live. Of course he does. I yelled it to Pizza Now.', '他知道我住哪。当然知道。我对着披萨现在大喊过。'),
         say('I told everyone. I\'m the worst hacker alive.', '我告诉了所有人。我是世界上最烂的黑客。'),
         setv('crowThreat'),
         ], ifNot='copsDorian'),
      wait(2), END)

scene('d5_video', 22, 'today', 'd5_night',
      desk('22:00', ('board', 's4')),
      on('cam', 'mask', at=(156, 10)),
      say('Tape off. [mask]Mask[/mask] on. Paper moth. I made it myself.', '拿掉胶带。戴上[mask]面具[/mask]。纸做的飞虫。我自己做的。'),
      say('This is a message for the Primate Observation Club.', '这是给灵长类动物观察俱乐部的讯息。'),
      say('My name is m0th. I\'m nineteen. I\'m a moron.', '我叫m0th。十九岁。我是个白痴。'),
      say('I sold a woman\'s address for three hundred coins.', '我用三百币卖掉了一个女人的地址。'),
      say('You watched me do it. You recorded it.', '你看着我做。你录了下来。'),
      anim('cam', 'recTalk'),
      say('So now you have a video of a monkey.', '所以现在你手上有一只猴子的录像。'),
      say('Sell it. Put it on TV. I don\'t care.', '卖掉吧。上电视吧。我不在乎。'),
      say('But remember: the moth always finds the light.', '但是记住：飞虫总会找到光。'),
      say('And your screen is a light, observer.', '而你的屏幕就是一个灯，观察者。'),
      say('Phototaxis. Look it up.', '趋光性。自己去查。'),
      anim('cam', 'mask'),
      wait(2), anim('cam', 'taped'),
      wait(2), END)

scene('d5_night', 23.9, 'today', 'd6_geo',
      desk('23:50', ('board', 's4'), ('cam', 'taped')),
      say('Not sleeping. Mapping.', '不睡了。画地图。'),
      sleep_screen('stare'), wait(10), END)

# ================================================================== DAY 6
scene('d6_geo', 10, 'nextAvailable', 'd6_call',
      desk('10:00', ('board', 's4'), ('cam', 'taped')),
      on('browser', 'geo0', at=(80, 6)),
      say('Your relay server IP. Accuracy: five kilometers.', '你的中继服务器IP。精确度：五公里。'),
      on('term', 'trace', at=(22, 92)),
      say('Traceroute again. Pinging every hop. Timing every answer.', '再跑一次追踪路由。ping每一跳。计算每一次回应的时间。'),
      anim('browser', 'geo1'),
      say('Eight hundred meters.', '八百米。'),
      wait(2),
      anim('browser', 'geo2'),
      say('Forty meters. A building. Your building.', '四十米。一栋楼。你的楼。'),
      anim('board', 's5'),
      say('Funny. You\'re not even far.', '好笑。你根本不远。'),
      say('We could have been neighbors. Maybe we are.', '我们说不定是邻居。也许就是。'),
      wait(2), END)

scene('d6_call', 12, 'today', 'd6_gift',
      desk('11:00', ('board', 's5'), ('cam', 'taped'), ('browser', 'geo2')),
      say('Your phone number was in the relay config. In plain text.', '你的电话号码就写在中继设定里。明文。'),
      say('You people are as bad at this as I am.', '你们跟我一样烂嘛。'),
      say('Calling...', '拨号中...'),
      ev('d6_ring', [{'type': 'phoneCall', 'id': 'mothCalls', 'ifNot': 'copsMoth'}]),
      wait(6), END)

scene('d6_gift', 15, 'today', 'd6_crowCheck',
      desk('15:00', ('board', 's5'), ('cam', 'taped')),
      on('popup', 'order', at=(78, 70)),
      say('I made you something. I\'ll bring it myself. Tonight.', '我给你做了个东西。我会亲手送过去。就今晚。'),
      say('Don\'t worry. It\'s not a bomb. I don\'t know how to make bombs.', '别担心。不是炸弹。我不会做炸弹。'),
      say('H4CK SCHOOL doesn\'t teach that. It\'s a family channel.', 'H4CK SCHOOL不教这个。那是个适合全家观看的频道。'),
      off('popup'),
      say('It\'s a moth. In a jar. So you know how it feels.', '是一只飞虫。装在罐子里。让你知道那是什么感觉。'),
      wait(2), END)

scene('d6_crowCheck', 19, 'today', 'd6_leave',
      desk('19:00', ('board', 's5'), ('cam', 'taped')),
      C([on('chat', 'threatFull', at=(146, 52)),
         say('Crow is online again. Watching the board.', '乌鸦又上线了。盯着论坛。'),
         say('If he comes here, I\'m not opening the door.', '如果他来这里，我绝对不开门。'),
         say('...Hah. Now I understand Nora\'s lock.', '...哈。现在我懂诺拉那把锁了。'),
         ], ifNot='copsDorian'),
      C([on('chat', 'bannedFull', at=(146, 52)),
         say('Crow\'s account is still banned. Good. Stay in your cage, bird.', '乌鸦的账号还在封禁中。很好。待在你的笼子里吧，鸟。'),
         ], if_='copsDorian'),
      C([say('Something came. From the Club. A key. A login.', '来了一样东西。俱乐部寄来的。一个钥匙。一个登录账号。'),
         on('browser', 'welcome', at=(80, 6)),
         say('"Welcome, new member."', '“欢迎，新会员。”'),
         say('Cages. Dozens of them. People who don\'t know.', '笼子。几十个。都是不知情的人。'),
         say('And this one... cage seven. Is that... you?', '还有这个...七号笼子。那是...你吗？'),
         say('Oh. Oh, this is beautiful.', '哦。哦，这太美了。'),
         setv('mothMember'),
         ], if_='chatClub'),
      wait(2), END)

scene('d6_leave', 23, 'today', 'd7_dawn',
      desk('23:00', ('board', 's5'), ('cam', 'taped')),
      setv('finalNight'),   # from here on the police no longer raid: the door visit is already scheduled
      C([say('I don\'t need to find you anymore.', '我不用再找你了。'),
         say('I\'m one of you now. Good night, colleague.', '我现在也是你们的一员。晚安，同事。'),
         sleep_screen('sleep')], if_='mothMember'),
      C([say('Backpack. Hoodie. Helmet, so the cameras don\'t get my face.', '背包。连帽衫。安全帽，这样摄像头拍不到我的脸。'),
         say('And the mask in my pocket. For later.', '面具放口袋。待会用。'),
         say('Byte, guard the house. If anyone comes, scratch them.', '字节，看家。有人来就抓他。'),
         say('I\'m going to see the light, observer.', '我要去看看那个灯了，观察者。'),
         say('Leave your door unlocked. Or don\'t. I\'ll knock.', '门别锁。锁了也行。我会敲门。'),
         wait(3), anim('cam', 'empty'),
         sleep_screen('empty'), setv('mothLeft')], ifNot='mothMember'),
      wait(10), END,
      start=[{'type': 'knockDoor', 'image': 'mods/MothScreen/web/door_guest', 'ifNot': 'mothMember,copsMoth', 'when': 'future', 'day': '+1', 'hour': '1',
               'whenHome': True, 'repeat': False, 'conversation': 'DOOR'}])

# ================================================================== DAY 7
scene('d7_dawn', 3, 'nextAvailable', 'd7_end',
      wait(10))   # merged into d6_leave: the screen is already asleep and the LED off

scene('d7_end', 12, 'today', None,
      desk('13:00', ('board', 's5')),
      off('black', 'saver'),
      # A: he visited and the player told him to go to the police -> he turns himself in
      C([on('cam', 'face', at=(156, 10)),
         say('I\'m back. You opened the door. You looked scared.', '我回来了。你开了门。你看起来很害怕。'),
         say('Good. Now we both know.', '很好。现在我们都知道了。'),
         say('You told me to go to the police. So I\'m going.', '你叫我去报警。所以我要去了。'),
         say('I\'ll tell them about Dorian. And about me.', '我会告诉他们多里安的事。还有我的事。'),
         anim('board', 's6'),
         say('And about you. They won\'t believe me. Nobody believes monkeys.', '还有你的事。他们不会信的。没人会信猴子说的话。'),
         ], if_='mothVisited,chatHelp'),
      # B: he visited, no help
      C([on('cam', 'face', at=(156, 10)),
         say('I\'m back. You opened the door.', '我回来了。你开了门。'),
         say('Now I know your door. Your face. Your bad coffee breath.', '现在我知道你家的门。你的脸。你那难闻的咖啡口气。'),
         say('We\'re even, observer.', '我们扯平了，观察者。'),
         on('term', 'wipe', at=(22, 92)),
         say('Wiping everything. M0th is dead. Elias Krumm is going to find a real job.', '全部抹掉。m0th已经死了。[eliasKrumm]埃利亚斯·克鲁姆[/eliasKrumm]要去找份正经工作。'),
         anim('board', 's6'),
         ], if_='mothVisited', ifNot='chatHelp'),
      # A2: told to go to the police, nobody opened -> he goes anyway
      C([on('cam', 'angry', at=(156, 10)),
         say('You didn\'t open. Fine. I didn\'t need your face.', '你没开门。行。我也不需要看你的脸。'),
         say('You told me to go to the police. So I\'m going. Alone.', '你叫我去报警。所以我要去了。一个人。'),
         anim('board', 's6'),
         ], if_='mothLeft,chatHelp', ifNot='mothVisited'),
      # C: he went, but nobody opened
      C([on('cam', 'angry', at=(156, 10)),
         say('You didn\'t open. I stood at your door for an hour.', '你没开门。我在你家门口站了一个小时。'),
         say('I heard you. Breathing behind the door.', '我听到了。你在门后面呼吸。'),
         say('Now you know how Nora felt.', '现在你知道诺拉是什么感觉了。'),
         on('term', 'wipe', at=(22, 92)),
         say('I\'m deleting all of it. Name: Elias Krumm. Remember it. I remember yours.', '我把一切都删了。名字：埃利亚斯·克鲁姆。记住它。我记得你的。'),
         ], if_='mothLeft', ifNot='mothVisited,chatHelp'),
      # D: he joined the Club
      C([on('browser', 'welcome', at=(80, 6)),
         say('Cage three: a man who talks to his plants.', '三号笼子：一个跟植物说话的男人。'),
         say('Cage five: a woman reading a black book.', '五号笼子：一个读黑色书本的女人。'),
         say('So this is how it feels. On this side.', '原来是这种感觉。在这一边。'),
         say('Byte, look. Monkeys.', '字节，你看。猴子。'),
         say('...Don\'t feed them.', '...别喂它们。'),
         ], if_='mothMember'),
      wait(2),
      say('Goodbye, observer.', '再见了，观察者。'),
      wait(1), off('cam', 'board', 'browser', 'term'), on('lost', 'default'),
      wait(4), END,
      finish=[
          {'type': 'addEnding', 'id': 'mothScreenTurnIn', 'if': 'mothVisited,chatHelp'},
          {'type': 'addEnding', 'id': 'mothScreenTurnIn', 'if': 'mothLeft,chatHelp', 'ifNot': 'mothVisited'},
          {'type': 'addEnding', 'id': 'mothScreenDoor', 'if': 'mothVisited', 'ifNot': 'chatHelp'},
          {'type': 'addEnding', 'id': 'mothScreenNoDoor', 'if': 'mothLeft', 'ifNot': 'mothVisited,chatHelp'},
          {'type': 'addEnding', 'id': 'mothScreenMember', 'if': 'mothMember'},
          {'type': 'addEnding', 'id': 'mothScreenNora', 'if': 'noraWarned'},
          {'type': 'addEnding', 'id': 'mothScreenDorian', 'if': 'copsDorian'},
          {'type': 'addEnding', 'id': 'mothScreenNoraFled', 'if': 'breakIn', 'ifNot': 'noraWarned'},
          {'type': 'addEnding', 'id': 'mothScreenNoraSpared', 'if': 'dorianStopped', 'ifNot': 'noraWarned'},
          {'type': 'addEnding', 'id': 'mothScreenDorianFree', 'ifNot': 'copsDorian'},
          {'type': 'addNew', 'id': 'newsTurnIn', 'if': 'mothVisited,chatHelp', 'when': 'future', 'day': '+1', 'hour': '8'},
          {'type': 'addNew', 'id': 'newsTurnIn', 'if': 'mothLeft,chatHelp', 'ifNot': 'mothVisited', 'when': 'future', 'day': '+1', 'hour': '8'},
          {'type': 'endDiary'}])

# ================================================================== police raid (reached only from the tip line call)
scene('raid', 23, 'today', None,
      desk('23:00'),
      off('black', 'saver'),
      say('Pizza? I didn\'t order pizza.', '披萨？我没点披萨啊。'),
      say('*BANG BANG BANG*', '*敲门声！很大声！*'),
      say('POLICE! OPEN THE DOOR!', '警察！开门！'),
      say('No. No no no. Delete. DELETE.', '不。不不不。删掉。快删掉！'),
      on('term', 'wipe', at=(22, 92)),
      say('*CRASH*', '*门被撞开*'),
      say('HANDS WHERE WE CAN SEE THEM!', '双手放在我们看得到的地方！'),
      say('Byte! Don\'t hurt my cat! She\'s just a cat!', '字节！别伤害我的猫！她只是只猫！'),
      say('Elias Krumm, you are under arrest for stalking and fraud.', '埃利亚斯·克鲁姆，你因跟踪和诈骗被捕了。'),
      say('Someone was watching me! Check the computer! There\'s a relay!', '有人在监视我！检查电脑！里面有中继！'),
      say('Sure, kid. Everyone is watching you.', '是啊，小子。全世界都在看着你。'),
      wait(2), off('term', 'board', 'browser', 'cam', 'chat', 'postit', 'notes'), on('lost', 'default'), off('cursor'),
      wait(4), END,
      finish=[{'type': 'addEnding', 'id': 'mothScreenArrest'}, {'type': 'addEnding', 'id': 'mothScreenNora', 'if': 'noraWarned'},
              {'type': 'addEnding', 'id': 'mothScreenDorian', 'if': 'copsDorian'},
              {'type': 'addEnding', 'id': 'mothScreenNoraFled', 'if': 'breakIn', 'ifNot': 'noraWarned'},
              {'type': 'addEnding', 'id': 'mothScreenNoraSpared', 'if': 'dorianStopped', 'ifNot': 'noraWarned'},
              {'type': 'addEnding', 'id': 'mothScreenDorianFree', 'ifNot': 'copsDorian'},
              {'type': 'addNew', 'id': 'newsArrest', 'when': 'future', 'day': '+1', 'hour': '8'}, {'type': 'endDiary'}])

# ------------------------------------------------------------------ conversations
def node(text_en, text_zh, opts=(), voice=None, init=None, kw=None, me=False, none=None):
    """kw: notebook options {keyword: ((en, zh), goto)}. The game then ignores 'texts' and opens the notebook;
    only 'main' notebook words can be picked, and 'none' ((en, zh), goto) is the red fallback / hang-up option."""
    n = {}
    if voice: n['voice'] = voice
    n['text'] = T(text_en, text_zh) if not me else T(text_en, text_zh)
    n['texts'] = [dict(text=T(*o[0]), goto=o[1]) if o[1] else dict(text=T(*o[0])) for o in opts]
    if not n['texts']:
        # an end node needs one empty option: the game shows it as the 'end conversation' button
        # (a node with no options leaves the chat/phone/door dialog stuck)
        n['texts'] = [{'text': ''}]
    if kw:
        n['keywords'] = {k: [dict(text=T(*o[0]), goto=o[1])] for k, o in kw.items()}
        assert none, 'keyword nodes need a none option'
        n['keywords']['none'] = [dict(text=T(*none[0]), goto=none[1])]
        n['showEndCall'] = True
        del n['texts']
    if init: n['onInitTalk'] = init
    return n

def chat_nodes(conv):
    """Chats read onInitTalk from the chosen line (ChatConversation.setChatWait: getText(node)["onInitTalk"]),
    not from the node like phone calls and door talks do, so move it into a one-entry text list."""
    for nid, n in conv.items():
        if nid == '1' or 'who' in n: continue
        entry = {'text': n['text']}
        if 'onInitTalk' in n: entry['onInitTalk'] = n.pop('onInitTalk')
        n['text'] = [entry]
    return conv

def SV(name): return {'type': 'setVar', 'name': name, 'value': 'true'}

def conversations():
    calls, chats = {}, {}
    def ct(en, zh, **c):
        d = {'text': T(en, zh)}; d.update({('if' if k == 'if_' else k): v for k, v in c.items()}); return d
    def kwopt(en, zh, goto, **c):
        d = dict(text=T(en, zh), goto=goto); d.update({('if' if k == 'if_' else k): v for k, v in c.items()}); return d
    F = 'femenina'
    # Nora answers differently before the break-in, after it (not warned: she barely escaped) and once warned.
    # Warning her is only possible before the break-in (breakIn is set the night the address was sold).
    calls['callNora'] = {
        '1': {'voice': F, 'showEndCall': True,
              'text': [ct('Hello? Who is this?', '喂？请问是谁？', ifNot='noraWarned,breakIn'),
                       ct('...Hello? Who is this? How did you get this number?', '...喂？你是谁？你怎么会有这个号码？', if_='breakIn', ifNot='noraWarned'),
                       ct('...It\'s you again. The voice from the other night.', '...又是你。那天晚上那个声音。', if_='noraWarned')],
              'texts': [{'text': '', 'gotoKeywords': '10', 'ifNot': 'noraWarned,breakIn'},
                        {'text': '', 'gotoKeywords': '20', 'if': 'breakIn', 'ifNot': 'noraWarned'},
                        {'text': '', 'gotoKeywords': '30', 'if': 'noraWarned'}]},
        # v2.4: a warning needs proof. Every warning leads to a proof question ("tell me something only someone
        # looking for me would know"); only her street or her married name convinces her. Public things from her
        # profile (bakery, cat, bike) do not: she hangs up, and the player can call again.
        '10': {'voice': F, 'text': '', 'keywords': {
            'noraVance': [kwopt('Nora Vance? Someone is collecting information about you online.', '诺拉·万斯？有人在网上收集你的资料。', 'P2')],
            'dorianPell': [kwopt('Dorian Pell paid someone to find your address.', '多里安·佩尔花钱找人查你的地址。', 'P3')],
            'kestrelLane': [kwopt('Somebody knows you live on Kestrel Lane.', '有人知道你住在红鹰巷。', '2')],
            'noraPell': [kwopt('Nora Pell? He is looking for you.', '诺拉·佩尔？他在找你。', '3')],
            'm0th': [kwopt('A hacker called m0th is looking for you.', '一个叫m0th的黑客在找你。', 'P2')],
            'mothHacker': [kwopt('An amateur hacker is digging into your life.', '一个业余黑客在查你。', 'P2')],
            'crow': [kwopt('Someone called Crow wants to know where you live.', '一个叫乌鸦的人想知道你住在哪。', 'P2')],
            'fakeCourier': [kwopt('If a courier knocks on your door, don\'t open.', '如果有快递员敲门，别开。', 'P2')],
            'crowEx': [kwopt('Your ex is paying someone to find you.', '你的前任在花钱找人找你。', 'P3')],
            'noraHiding': [kwopt('You left your husband and moved. He has found your street.', '你和前夫分开后搬了家。他已经找到你住的街了。', 'P3')],
            'crowDebt': [kwopt('Someone says you owe him money.', '有人说你欠他钱。', '6')],
            'noraDebt': [kwopt('Someone says you owe him money.', '有人说你欠他钱。', '6')],
            'noraFamous': [kwopt('Are you a star? Someone is very interested in you.', '你是明星吗？有人对你非常感兴趣。', '7')],
            'none': [kwopt('Sorry, wrong number.', '抱歉，打错了。', '5')]}},
        # proof questions (P2: she does not know who; P3: the claim already points at Dorian)
        'P2': {'voice': F, 'text': T('Who is this? Why should I believe you?|Tell me something only someone looking for me would know.',
                                     '你是谁？我凭什么相信你？|说一件只有在找我的人才会知道的事。'),
               'keywords': {'kestrelLane': [kwopt('You live on Kestrel Lane.', '你住在红鹰巷。', '2')],
                            'noraPell': [kwopt('Your married name. Nora Pell.', '你婚后的名字。诺拉·佩尔。', '3')],
                            'sweetCrumb': [kwopt('You work at Sweet Crumb.', '你在甜屑面包店上班。', '8')],
                            'biscuit': [kwopt('Your cat is called Biscuit.', '你的猫叫饼干。', '8')],
                            'bike': [kwopt('You ride a blue bike.', '你骑一辆蓝色自行车。', '8')],
                            'none': [kwopt('...I can\'t.', '...我说不出来。', '9')]}},
        'P3': {'voice': F, 'text': T('...How do you know about that? Who are you?|Prove it. Tell me something he would want to know.',
                                     '...你怎么知道这件事？你是谁？|证明给我看。说一件他会想知道的事。'),
               'keywords': {'kestrelLane': [kwopt('Where you live now. Kestrel Lane.', '你现在住哪。红鹰巷。', '3')],
                            'noraPell': [kwopt('The name you gave up. Nora Pell.', '你不再用的名字。诺拉·佩尔。', '3')],
                            'sweetCrumb': [kwopt('Where you work. Sweet Crumb.', '你在哪上班。甜屑面包店。', '8')],
                            'biscuit': [kwopt('Your cat\'s name. Biscuit.', '你的猫叫饼干。', '8')],
                            'bike': [kwopt('Your blue bike.', '你的蓝色自行车。', '8')],
                            'none': [kwopt('...I can\'t.', '...我说不出来。', '9')]}},
        '8': node('That\'s on my profile. Anyone can see that.|Nice try. Don\'t call me again.', '这在我主页上就有。谁都看得到。|想得美。别再打来了。', voice=F),
        '9': node('Then why should I listen to you? Goodbye.', '那我凭什么听你的？再见。', voice=F),
        '2': node('What? Who? ...How do you know that?', '什么？谁？...你怎么知道？', voice=F, opts=[
            (('Make your Metayou private. Change your passwords.', '把Metayou设成私密。改掉所有密码。'), '4'),
            (('I can\'t say. Just don\'t stay at home.', '我不能说。总之别待在家里。'), '4')]),
        '3': node('...Dorian. Oh my God. He promised the judge...', '...多里安。天啊。他明明向法官保证过...', voice=F, opts=[
            (('Don\'t stay at home. Change your passwords.', '别待在家。改掉你的密码。'), '4')]),
        '4': node('Okay. Okay. I\'ll go to my sister\'s tonight. ...Thank you. I think.', '好。好。我今晚就去我姐姐家。...谢谢你。应该吧。',
                  voice=F, init=[SV('noraWarned')]),
        '5': node('...Okay? Bye.', '...好吧？再见。', voice=F),
        '6': node('Money? I don\'t owe anyone anything. ...Is this Dorian\'s new trick? Don\'t call me again.',
                  '钱？我谁都不欠。...这是多里安的新花招吗？别再打来了。', voice=F),
        '7': node('A star? Ha. You\'re joking. ...Who is this?', '明星？哈哈，你可真会开玩笑。你是谁？', voice=F),
        # after the break-in, not warned: too late to warn her; she points the player to the police
        '20': {'voice': F, 'text': '', 'keywords': {
            'dorianPell': [kwopt('It was Dorian Pell, wasn\'t it?', '是多里安·佩尔干的，对吧？', '21')],
            'crow': [kwopt('The man who broke in hired a hacker to find you.', '闯进你家的人雇了黑客找你。', '21')],
            'noraVance': [kwopt('Nora? Are you okay?', '诺拉？你还好吗？', '22')],
            'kestrelLane': [kwopt('I saw the news about Kestrel Lane.', '我看到红鹰巷的新闻了。', '22')],
            'm0th': [kwopt('A hacker called m0th sold your address.', '一个叫m0th的黑客卖了你的地址。', '21')],
            'crowEx': [kwopt('It was your ex. He paid a hacker to find you.', '是你的前任。他花钱请黑客找你。', '21')],
            'noraPell': [kwopt('He still thinks you are Nora Pell.', '他还当你是诺拉·佩尔。', '21')],
            'fakeCourier': [kwopt('The man who broke in came as a courier?', '闯进来的人扮成了快递员？', '23')],
            'none': [kwopt('...Sorry. Wrong number.', '...抱歉。打错了。', '5')]}},
        '21': node('I knew it was him. The police say they can\'t prove it.|If you know something, call the tip line. 555-0110. Please.',
                   '我就知道是他。警察说他们没有证据。|如果你知道什么，打举报热线。555-0110。拜托了。', voice=F),
        '23': node('...Yes. "A parcel for Nora." I almost opened.|If you know who sent him, call the tip line. 555-0110.',
                   '...对。“诺拉的包裹。”我差点就开门了。|如果你知道是谁派他来的，打举报热线。555-0110。', voice=F),
        '22': node('I jumped out of my kitchen window in my socks.|I\'m at my sister\'s now. I don\'t sleep.|Please don\'t call this number again.',
                   '我光着脚从厨房窗户跳了出去。|我现在住在姐姐家。我睡不着。|请别再打这个号码了。', voice=F),
        # already warned: she is safe; no second warning
        '30': {'voice': F, 'text': '', 'keywords': {
            'dorianPell': [kwopt('Dorian is still out there. Be careful.', '多里安还在外面。小心点。', '31', ifNot='copsDorian'),
                           kwopt('Dorian Pell was arrested.', '多里安·佩尔被抓了。', '32', if_='copsDorian')],
            'kestrelLane': [kwopt('Someone broke into your flat.', '有人闯进了你的公寓。', '31', if_='breakIn'),
                            kwopt('Don\'t go back to Kestrel Lane yet.', '先别回红鹰巷。', '31', ifNot='breakIn')],
            'noraVance': [kwopt('Just checking that you\'re safe.', '只是确认你平安。', '31')],
            'sister': [kwopt('Are you at your sister\'s?', '你在姐姐家吗？', '31')],
            'fakeCourier': [kwopt('Don\'t open the door to couriers.', '别给快递员开门。', '31')],
            'none': [kwopt('Stay safe.', '保重。', '31')]}},
        '31': node('I\'m at my sister\'s. New passwords. New lock. I\'m okay.|Whoever you are... thank you. Please don\'t call again.',
                   '我在姐姐家。换了密码。换了锁。我没事。|不管你是谁...谢谢你。请别再打来了。', voice=F),
        '32': node('...They got him? Oh my God.|I can breathe. I can actually breathe.', '...他们抓到他了？天啊。|我终于能呼吸了。真的能呼吸了。', voice=F),
    }
    # Police tip line. Reporting m0th's address only works once he has sold an address (addressSold);
    # Dorian can be reported once. Reporting Dorian before the break-in stops it (dorianStopped).
    calls['callPolice'] = {
        '1': {'voice': F, 'showEndCall': True, 'text': T('Cybercrime tip line. What would you like to report?', '网络犯罪举报热线。请问您要举报什么？'),
              'texts': [{'text': '', 'gotoKeywords': '10'}]},
        '10': {'voice': F, 'text': '', 'keywords': {
            'mothAddress': [kwopt('A hacker at 22 Gorse Street, flat 3B, is selling people\'s addresses.', '戈尔斯街22号3B有个黑客在贩卖别人的地址。', '11', if_='addressSold,finalNight'),
                            kwopt('A hacker at 22 Gorse Street, flat 3B, is selling people\'s addresses.', '戈尔斯街22号3B有个黑客在贩卖别人的地址。', '11', if_='addressSold,mothLeft'),
                            kwopt('A hacker at 22 Gorse Street, flat 3B, is selling people\'s addresses.', '戈尔斯街22号3B有个黑客在贩卖别人的地址。', '2', if_='addressSold', ifNot='finalNight,mothLeft'),
                            kwopt('A hacker at 22 Gorse Street, flat 3B, is spying on a woman.', '戈尔斯街22号3B有个黑客在监视一个女人。', '8', ifNot='addressSold')],
            'eliasKrumm': [kwopt('A young man called Elias Krumm is doxxing people for money.', '一个叫埃利亚斯·克鲁姆的年轻人在收钱人肉别人。', '5')],
            'dorianPell': [kwopt('Dorian Pell is hunting a woman he has a restraining order for.', '多里安·佩尔在追踪一个对他下了禁止令的女人。', '3', ifNot='copsDorian'),
                           kwopt('About Dorian Pell...', '关于多里安·佩尔...', '9', if_='copsDorian')],
            'crow': [kwopt('Someone called Crow pays hackers to find women.', '一个叫乌鸦的人花钱请黑客找女人。', '4')],
            'm0th': [kwopt('Someone called m0th is stalking people online.', '有个叫m0th的人在网上跟踪别人。', '4')],
            'noraVance': [kwopt('A woman called Nora Vance is in danger.', '一个叫诺拉·万斯的女人有危险。', '6')],
            'noraHiding': [kwopt('A woman left her husband, and he is getting close.', '一个刚和丈夫分居的女人有危险，他快找到她了。', '6')],
            'kestrelLane': [kwopt('I know who did the Kestrel Lane break-in.', '我知道红鹰巷的案子是谁干的。', '6', if_='breakIn'),
                            kwopt('Someone is after a woman on Kestrel Lane.', '红鹰巷有个女人被人盯上了。', '6', ifNot='breakIn')],
            'intruder': [kwopt('About the Kestrel Lane intruder...', '关于红鹰巷的闯入者...', '6')],
            'fakeCourier': [kwopt('The Kestrel Lane intruder came as a fake courier.', '红鹰巷的闯入者扮成了快递员。', '6', if_='breakIn'),
                            kwopt('Someone plans to get into a woman\'s flat as a fake courier.', '有人打算扮成快递员闯进一个女人家。', '6', ifNot='breakIn')],
            'noraPell': [kwopt('A woman called Nora Pell is in danger. Vance now.', '一个叫诺拉·佩尔的女人有危险。现在姓万斯。', '18', ifNot='copsDorian'),
                         kwopt('A woman called Nora Pell is in danger. Vance now.', '一个叫诺拉·佩尔的女人有危险。现在姓万斯。', '9', if_='copsDorian')],
            'mothHacker': [kwopt('An amateur hacker is selling people\'s addresses.', '一个业余黑客在卖别人的地址。', '4')],
            'mothDetective': [kwopt('A private eye is tracking a woman.', '有个私家探员在追踪一个女人。', '19')],
            'mothCop': [kwopt('A detective is doxxing people for money.', '有个警探在收钱人肉别人。', '14')],
            'crowEx': [kwopt('A man with a restraining order hired a hacker to find his ex.', '一个被下了禁止令的男人雇黑客找他的前任。', '12', ifNot='copsDorian'),
                       kwopt('A man with a restraining order hired a hacker to find his ex.', '一个被下了禁止令的男人雇黑客找他的前任。', '9', if_='copsDorian')],
            'crowDebt': [kwopt('A debt collector is hunting a woman.', '有个讨债的在找一个女人。', '13')],
            'crowCop': [kwopt('A cop is stalking a woman. Off duty.', '有个警察在下班时间跟踪一个女人。', '14')],
            'mothComing': [kwopt('A hacker says he will come to my door tonight.', '有个黑客说他今晚要来我家门口。', '15')],
            'none': [kwopt('Nothing. Sorry.', '没事。抱歉。', '7')]}},
        '2': {'voice': F, 'texts': [{'text': ''}],
              'text': [ct('Gorse Street... that matches the Kestrel Lane break-in. We\'ll send a unit. Thank you.', '戈尔斯街...跟红鹰巷那宗闯入案对得上。我们会派人过去。谢谢您。', if_='breakIn'),
                       ct('Selling a woman\'s address... that\'s enough for a visit. We\'ll send a unit. Thank you.', '贩卖女性的住址...这足够我们上门了。我们会派人过去。谢谢您。', ifNot='breakIn')],
              # the game's PENDING state: notebook page disabled, "Cage N is now PENDING" notice, until the raid ends it
              'onInitTalk': [SV('copsMoth'), {'type': 'pendingDiary'},
                             {'type': 'changeScene', 'scene': 'raid', 'when': 'future', 'day': '0', 'hour': '+2'}]},
        '3': {'voice': F, 'texts': [{'text': ''}],
              'text': [ct('Pell. He already broke that order once. We\'ll pick him up tonight.', '佩尔。他已经违反过一次禁令了。我们今晚就去抓他。', ifNot='breakIn'),
                       ct('Pell... the Kestrel Lane break-in. That fits. We\'ll pick him up tonight.', '佩尔...红鹰巷闯入案。对得上。我们今晚就去抓他。', if_='breakIn')],
              'onInitTalk': [SV('copsDorian'), {'type': 'setVar', 'name': 'dorianStopped', 'value': 'true', 'ifNot': 'breakIn'},
                             {'type': 'addNew', 'id': 'newsDorian', 'when': 'future', 'day': '+1', 'hour': '8'}]},
        # follow-up questions: the officer asks, the player answers from the notebook in the same call
        '4': {'voice': F, 'text': T('An alias is not enough, caller. Do you have a real name or an address?', '光有网名是不够的。您有真实姓名或地址吗？'),
              'keywords': {'eliasKrumm': [kwopt('His real name is Elias Krumm.', '他的真名是埃利亚斯·克鲁姆。', '5')],
                           'mothAddress': [kwopt('He lives at 22 Gorse Street, flat 3B.', '他住在戈尔斯街22号3B。', '11', if_='addressSold,finalNight'),
                            kwopt('He lives at 22 Gorse Street, flat 3B.', '他住在戈尔斯街22号3B。', '11', if_='addressSold,mothLeft'),
                            kwopt('He lives at 22 Gorse Street, flat 3B. He sold a woman\'s address.', '他住在戈尔斯街22号3B。他卖了一个女人的地址。', '2', if_='addressSold', ifNot='finalNight,mothLeft'),
                            kwopt('He lives at 22 Gorse Street, flat 3B.', '他住在戈尔斯街22号3B。', '8', ifNot='addressSold')],
                           'dorianPell': [kwopt('His name is Dorian Pell.', '他叫多里安·佩尔。', '3', ifNot='copsDorian'),
                           kwopt('His name is Dorian Pell.', '他叫多里安·佩尔。', '9', if_='copsDorian')],
                           'none': [kwopt('I don\'t know.', '我不知道。', '16')]}},
        '5': {'voice': F, 'text': T('Krumm... Do you know where he lives?', '克鲁姆...您知道他住在哪吗？'),
              'keywords': {'mothAddress': [kwopt('He lives at 22 Gorse Street, flat 3B.', '他住在戈尔斯街22号3B。', '11', if_='addressSold,finalNight'),
                            kwopt('He lives at 22 Gorse Street, flat 3B.', '他住在戈尔斯街22号3B。', '11', if_='addressSold,mothLeft'),
                            kwopt('He lives at 22 Gorse Street, flat 3B. He sold a woman\'s address.', '他住在戈尔斯街22号3B。他卖了一个女人的地址。', '2', if_='addressSold', ifNot='finalNight,mothLeft'),
                            kwopt('He lives at 22 Gorse Street, flat 3B.', '他住在戈尔斯街22号3B。', '8', ifNot='addressSold')],
                           'none': [kwopt('I don\'t know.', '我不知道。', '16')]}},
        '6': {'voice': F,
              'text': [ct('Do you know who is threatening her? A name?', '您知道是谁在威胁她吗？有名字吗？', ifNot='breakIn'),
                       ct('The Kestrel Lane case. Do you know who did it? We need a name.', '红鹰巷的案子。您知道是谁干的吗？我们需要一个名字。', if_='breakIn')],
              'keywords': {'dorianPell': [kwopt('His name is Dorian Pell.', '他叫多里安·佩尔。', '3', ifNot='copsDorian'),
                           kwopt('His name is Dorian Pell.', '他叫多里安·佩尔。', '9', if_='copsDorian')],
                           'crow': [kwopt('He calls himself Crow online.', '他在网上自称乌鸦。', '17')],
                           'crowEx': [kwopt('Her ex. He has a restraining order.', '她的前任。他被下了禁止令。', '12', ifNot='copsDorian'),
                                      kwopt('Her ex. He has a restraining order.', '她的前任。他被下了禁止令。', '9', if_='copsDorian')],
                           'm0th': [kwopt('A hacker called m0th found her for him.', '一个叫m0th的黑客帮他找到了她。', '4')],
                           'eliasKrumm': [kwopt('A hacker, Elias Krumm, found her for him.', '一个叫埃利亚斯·克鲁姆的黑客帮他找到了她。', '5')],
                           'none': [kwopt('I don\'t know.', '我不知道。', '16')]}},
        '7': node('Alright. Call us if you see anything.', '好的。有发现请再打给我们。', voice=F),
        '8': node('Spying how? Has he hurt anyone? We can\'t knock on doors for a feeling. Call back with something concrete.',
                  '怎么监视？他伤害谁了吗？我们不能凭感觉去敲门。有具体的事再打来。', voice=F),
        '9': node('Mr. Pell is already in custody. Thank you, caller.', '佩尔先生已经被拘留了。谢谢您。', voice=F),
        '11': {'voice': F, 'texts': [{'text': ''}],
               'text': [ct('We sent a car to Gorse Street. Nobody home. Only a cat. We\'ll keep an eye on the place.',
                           '我们派车去了戈尔斯街。家里没人。只有一只猫。我们会盯着那里。', if_='mothLeft'),
                        ct('Noted. A car will pass by Gorse Street in the morning.', '记下了。明天早上会有车去戈尔斯街看看。', ifNot='mothLeft')]},
        '12': {'voice': F, 'text': T('A restraining order... then he has a file. What is his name, caller?', '禁止令...那他有案底。他叫什么名字？'),
               'keywords': {'dorianPell': [kwopt('His name is Dorian Pell.', '他叫多里安·佩尔。', '3', ifNot='copsDorian'),
                           kwopt('His name is Dorian Pell.', '他叫多里安·佩尔。', '9', if_='copsDorian')],
                            'crow': [kwopt('Online he is Crow.', '网上他叫乌鸦。', '17')],
                            'none': [kwopt('I don\'t know.', '我不知道。', '16')]}},
        '16': node('Without a name or an address we can only take a note. Call again when you know more.', '没有名字或地址，我们只能先记录。知道更多再打来。', voice=F),
        '17': {'voice': F, 'text': T('"Crow" is a nickname. Do you have his real name?', '“乌鸦”只是外号。您知道他的真名吗？'),
               'keywords': {'dorianPell': [kwopt('His name is Dorian Pell.', '他叫多里安·佩尔。', '3', ifNot='copsDorian'),
                           kwopt('His name is Dorian Pell.', '他叫多里安·佩尔。', '9', if_='copsDorian')],
                            'none': [kwopt('I don\'t know.', '我不知道。', '16')]}},
        '18': {'voice': F, 'texts': [{'text': T('Yes. He is the one looking for her.', '对。就是他在找她。'), 'goto': '3'}], 'text': T('Pell... Dorian Pell\'s ex-wife? He has a file.', '佩尔...多里安·佩尔的前妻？他有案底。')},
        '19': {'voice': F, 'text': T('A private eye needs a licence. Who hired him? Who is he?', '私家探员要有执照。谁雇的他？他是谁？'),
               'keywords': {'dorianPell': [kwopt('Dorian Pell hired him.', '是多里安·佩尔雇的。', '3', ifNot='copsDorian'),
                                           kwopt('Dorian Pell hired him.', '是多里安·佩尔雇的。', '9', if_='copsDorian')],
                            'm0th': [kwopt('He calls himself m0th.', '他自称m0th。', '4')],
                            'eliasKrumm': [kwopt('His name is Elias Krumm.', '他叫埃利亚斯·克鲁姆。', '5')],
                            'none': [kwopt('I don\'t know.', '我不知道。', '16')]}},
        '13': node('Debt collection is a civil matter, caller. Talk to a lawyer.', '讨债是民事问题。请找律师。', voice=F),
        '14': node('An officer? Name and badge number, or this goes nowhere.', '警察？给我名字和警号，不然没办法处理。', voice=F),
        '15': node('Lock your door. If anyone shows up, call emergency. We\'ll note your address.', '把门锁好。如果有人出现，打紧急电话。我们会记下您的地址。', voice=F),
    }
    calls['mothCalls'] = {
        '1': dict(node('Hi. It\'s me. The monkey.', '嗨。是我。那只猴子。', voice='masculina1', opts=[
            (('How did you get this number?', '你怎么拿到这个号码的？'), '2'),
            (('Leave me alone.', '别来烦我。'), '3'),
            (('...', '...'), '4')], init=[SV('mothCallDone')]),
            onMissingCall=[{'type': 'insertActions', 'actions': [say('Voicemail. Coward.', '语音信箱。胆小鬼。'),
                                                                 say('Fine. I don\'t need you to answer. I just need you to listen.', '行。我不需要你接。我只需要你听。')]}]),
        '2': node('Your relay leaks. Like my free VPN. We\'re both amateurs.', '你的中继会泄漏。跟我的免费VPN一样。我们都是业余的。', voice='masculina1', opts=[
            (('What do you want?', '你想怎样？'), '5')]),
        '3': node('Leave YOU alone? You lived in my computer for a week.', '别来烦你？你在我的电脑里住了一个星期。', voice='masculina1', opts=[
            (('What do you want?', '你想怎样？'), '5')]),
        '4': node('Breathing. Cool. I\'m recording this too, you know.', '只有呼吸声。很好。你知道吗，我也在录音。', voice='masculina1', opts=[
            (('...', '...'), '5')]),
        '5': node('I want you to look at your door. Tonight. I\'m bringing you something. In person.', '我要你看着你家的门。就今晚。我会亲手带个东西给你。', voice='masculina1', opts=[
            (('Don\'t come here.', '别过来。'), '6'),
            (('I\'ll be waiting.', '我会等你。'), '7'),
            (('...', '...'), '8')]),
        '6': node('Then stop watching me. ...You can\'t, can you? Bye.', '那就别再看我。...你做不到，对吧？拜。', voice='masculina1'),
        '7': node('Good. Leave the light on. Moths like light.', '很好。把灯开着。飞虫喜欢光。', voice='masculina1'),
        '8': node('Still breathing. Still there. Goodnight, observer.', '还在呼吸。还在那里。晚安，观察者。', voice='masculina1'),
    }
    # m0th's chat (day 5). Each first answer sets the variable d5_chat reacts to (chatClub/Mirror/Help/Lie/Threat),
    # then one more exchange. Chat end nodes have no options and "end": true, like the game's own chats
    # (an empty option keeps a chat waiting forever).
    def cn(en, zh, opts=(), init=None, end=False):
        e = {'text': T(en, zh)}
        if init: e['onInitTalk'] = init
        n = {'text': [e]}
        if opts: n['texts'] = [dict(text=T(*o[0]), goto=o[1]) for o in opts]
        if end: n['end'] = True
        return n
    chats['mothChat'] = {
        '1': {'config': 'mothContact', 'who': 'me', 'text': T('...', '...'), 'texts': [{'text': '', 'goto': '2'}]},
        '2': {'text': T('I know you\'re watching.|You read my mail.|So. Who are you?', '我知道你在看。|你看了我的信。|所以。你是谁？'),
              'texts': [dict(text=T('I\'m with the Club. You\'ve been selected.', '我是俱乐部的人。你被选中了。'), goto='3'),
                        dict(text=T('Just someone watching. Like you watched Nora.', '只是个看着的人。就像你看着诺拉那样。'), goto='4'),
                        dict(text=T('Dorian is using you. Go to the police.', '多里安在利用你。去报警。'), goto='5'),
                        dict(text=T('Wrong person, kid.', '找错人了，小子。'), goto='6'),
                        dict(text=T('(Notebook) I know things about you.', '（翻开笔记本）我知道你的一些事。'), gotoKeywords='8')]},
        '3': cn('Selected? For what?|...Okay. I\'m listening.', '被选中？选来干什么？|...好。我在听。', init=[SV('chatClub')], opts=[
            (('Members watch. They are never watched. There\'s a seat for you.', '会员只看别人，从不被看。这里有你的位子。'), '31'),
            (('For an experiment. You failed it.', '为了一个实验。你没通过。'), '32')]),
        '31': cn('A seat.|Like... a membership?|...Send it. I\'m in.|Don\'t tell my mom.', '一个位子。|像...会员资格？|...发给我。我加入。|别告诉我妈。', end=True),
        '32': cn('Failed.|Story of my life.|Then why are you still talking to me?|...Send the invitation anyway.', '没通过。|我的人生就是这样。|那你干嘛还在跟我说话？|...邀请还是发来吧。', end=True),
        '4': cn('That\'s not the same.|...|Is it?', '那不一样。|...|是吗？', init=[SV('chatMirror')], opts=[
            (('She didn\'t know she was watched either.', '她也不知道自己被人看着。'), '41'),
            (('It\'s exactly the same.', '一模一样。'), '41')]),
        '41': cn('...|I keep seeing that news photo.|The broken lock.|Okay. You made your point.', '...|我一直想到那张新闻照片。|被弄坏的门锁。|好。你说到重点了。', end=True),
        '5': cn('How do you know about Dor—|You\'ve seen everything. Haven\'t you.', '你怎么会知道多里...|你全都看到了。对吧。', init=[SV('chatHelp')], opts=[
            (('Go to the police. Tell them about Crow.', '去报警。把乌鸦的事告诉他们。'), '51'),
            (('Then delete everything and disappear.', '那就把一切删掉，消失吧。'), '52')]),
        '51': cn('They\'ll arrest me.|...|But they\'d arrest him too.|I\'ll think about it. Don\'t watch me think.', '他们会抓我。|...|但他们也会抓他。|我会考虑。别看着我考虑。', end=True),
        '52': cn('Disappear. Easy for you to say.|You\'re the one hiding behind a screen.', '消失。你说得倒轻松。|躲在屏幕后面的人是你。', end=True),
        '6': cn('Nice try.|I can see your packets.', '说得好。|我看得到你的数据包。', init=[SV('chatLie')], opts=[
            (('Packets lie.', '数据包会说谎。'), '61'),
            (('(Say nothing.)', '（什么都不说。）'), '62')]),
        '61': cn('Packets don\'t lie. People do.|You\'re a person. Somewhere. With a door.', '数据包不会说谎。人才会。|你也是个人。在某个地方。有一扇门。', end=True),
        '62': cn('Silence. Classic observer.|Fine. I\'ll find you myself.', '不说话。标准的观察者。|行。我自己找你。', end=True),
        '7': cn('Great.|Now I\'ll find where YOU live.', '很好。|那我也会找出你住哪。', init=[SV('chatThreat')], opts=[
            (('Try it.', '试试看啊。'), '71'),
            (('I\'m not your enemy, Elias.', '我不是你的敌人，埃利亚斯。'), '72')]),
        '71': cn('Oh, I will.|Moths are patient.', '哦，我会的。|飞虫很有耐心。', end=True),
        '72': cn('Then stop acting like one.|...|Gotta go. Byte is eating a cable.', '那就别表现得像敌人。|...|我得走了。字节在咬电线。', end=True),
        '9': cn('Nora.|...|She has a cat too. Did you know that?|Of course you know. You know everything.', '诺拉。|...|她也养猫。你知道吗？|你当然知道。你什么都知道。', init=[SV('chatMirror')], opts=[
            (('She\'s a real person, Elias.', '她是个真实的人，埃利亚斯。'), '41')]),
    }
    # gotoKeywords opens the notebook straight away; the node's own text is not shown
    chats['mothChat']['8'] = {'text': [{'text': ''}], 'keywords': {
        'mothAddress': [{'text': T('I know where you live. 22 Gorse Street.', '我知道你住哪。戈尔斯街22号。'), 'goto': '7'}],
        'eliasKrumm': [{'text': T('I know your name, Elias.', '我知道你的名字，埃利亚斯。'), 'goto': '7'}],
        'dorianPell': [{'text': T('Crow is Dorian Pell. He used you.', '乌鸦就是多里安·佩尔。他利用了你。'), 'goto': '5'}],
        'crow': [{'text': T('Crow is using you. Go to the police.', '乌鸦在利用你。去报警。'), 'goto': '5'}],
        'noraVance': [{'text': T('Remember Nora Vance?', '还记得诺拉·万斯吗？'), 'goto': '9'}],
        'crowEx': [{'text': T('Crow is not owed anything. He is her ex, and a judge banned him from her.', '乌鸦没被欠什么。他是她的前任，法官禁止他接近她。'), 'goto': '5'}],
        'noraHiding': [{'text': T('She left that man. You helped him find her.', '她离开了那个男人。你帮他找到了她。'), 'goto': '4'}],
        'noraPell': [{'text': T('She used to be Nora Pell. Pell, Elias.', '她以前叫诺拉·佩尔。佩尔，埃利亚斯。'), 'goto': '5'}],
        'mothComing': [{'text': T('You\'re going to come to my door, aren\'t you.', '你会来敲我家的门，对吧。'), 'goto': '12'}],
        'mothPolice': [{'text': T('You\'re going to turn yourself in. Good.', '你会去自首。很好。'), 'goto': '16'}],
        'crowDebt': [{'text': T('She owes Crow money. Right?', '她欠乌鸦钱。对吧？'), 'goto': '13'}],
        'noraDebt': [{'text': T('She\'s running from her debts. Right?', '她在躲债。对吧？'), 'goto': '13'}],
        'crowCop': [{'text': T('Crow is a cop.', '乌鸦是警察。'), 'goto': '14'}],
        'noraFamous': [{'text': T('She\'s secretly a star. That\'s why.', '她其实是明星。所以才这样。'), 'goto': '14'}],
        'mothWipe': [{'text': T('You\'re going to delete everything and run.', '你会删除一切然后跑掉。'), 'goto': '15'}],
        'mothHacker': [{'text': T('You\'re just an amateur hacker.', '你只是个业余黑客。'), 'goto': '18'}],
        'mothDetective': [{'text': T('You\'re a private eye.', '你是私家探员。'), 'goto': '19'}],
        'mothCop': [{'text': T('You\'re a detective.', '你是警探。'), 'goto': '19'}],
        'none': [{'text': T('...Never mind.', '...算了。'), 'goto': '6'}]}}
    chats['mothChat'].update({
        '12': cn('...How do you know that?|I haven\'t even decided yet.|Stop reading my mind. That\'s MY job.', '...你怎么知道的？|我自己都还没决定。|别读我的心。那是我的工作。', init=[SV('chatThreat')], end=True),
        '13': cn('Yeah. She owes him. That\'s what he said.|...Right?', '对。她欠他钱。他是这么说的。|...对吧？', init=[SV('chatLie')], end=True),
        '14': cn('What? No.|You don\'t know anything, do you.', '什么？不是。|你根本什么都不知道，对吧。', init=[SV('chatLie')], end=True),
        '16': cn('Turn myself in? I haven\'t decided that.|...You think I should?', '自首？我还没决定。|...你觉得我应该去？', init=[SV('chatHelp')], opts=[
            (('Yes. Tell them about Crow.', '对。把乌鸦的事告诉他们。'), '51')]),
        '18': cn('...I know.|I learned it all from videos.|And I still found her. That\'s the scary part, right?', '...我知道。|我全是看视频学的。|可我还是找到她了。可怕的就是这个，对吧？', init=[SV('chatMirror')], end=True),
        '19': cn('A private eye? A detective?|I don\'t even have a driving licence.|You don\'t know anything, do you.', '私家探员？警探？|我连驾照都没有。|你根本什么都不知道，对吧。', init=[SV('chatLie')], end=True),
        '15': cn('Delete everything and pretend it never happened.|...Tempting. But you\'d still have the recordings.', '删掉一切，假装什么都没发生。|...很诱人。但你手上还有录像。', init=[SV('chatMirror')], end=True),
    })
    # ---- the chat keeps going: every branch ends in a hub where the player can ask more, until "Goodbye"
    mc = chats['mothChat']
    for nid, n in mc.items():
        if n.get('end'):
            n.pop('end')
            n['texts'] = [dict(text=T('Wait. One more thing.', '等等。还有一件事。'), goto='H')]
    mc['H'] = {'text': [{'text': T('What?|Make it quick. Byte is chewing the router.', '什么事？|快说。字节在咬路由器。')}],
               'texts': [dict(text=T('Who is Crow, really?', '乌鸦到底是谁？'), goto='QC', ifNot='askCrow'),
                         dict(text=T('Why did you take the job?', '你为什么接这个活？'), goto='QJ', ifNot='askJob'),
                         dict(text=T('What are you going to do now?', '你接下来要做什么？'), goto='QN', ifNot='askNext'),
                         dict(text=T('(Notebook) Look at this.', '（翻开笔记本）你看看这个。'), gotoKeywords='KH'),
                         dict(text=T('Goodbye, Elias.', '再见，埃利亚斯。'), goto='BYE')]}
    back = [(('Go on.', '继续说。'), 'H')]
    mc['QC'] = cn('Dorian Pell. Her ex.|I found that out AFTER I sold her address.|I keep refreshing the news. Every hour.',
                  '多里安·佩尔。她的前任。|我是卖了她的地址之后才发现的。|我一直在刷新闻。每个小时都刷。', init=[SV('askCrow')], opts=back)
    mc['QJ'] = cn('Rent. Pizza. Pick one.|...And he said I was good at it.|Nobody ever says I\'m good at anything.',
                  '房租。披萨。随便选一个。|...而且他说我很厉害。|从来没有人说过我擅长什么。', init=[SV('askJob')], opts=back)
    mc['QN'] = cn('Find you. Or delete everything. Or both.|I haven\'t decided.|You\'ll probably see it before I do.',
                  '找到你。或者删光一切。或者两个都做。|我还没决定。|你大概会比我先看到。', init=[SV('askNext')], opts=back)
    mc['KH'] = {'text': [{'text': ''}], 'keywords': {
        'noraVance': [{'text': T('Nora Vance.', '诺拉·万斯。'), 'goto': 'KN'}],
        'dorianPell': [{'text': T('Dorian Pell.', '多里安·佩尔。'), 'goto': 'QC'}],
        'crowEx': [{'text': T('Crow is her ex.', '乌鸦是她的前任。'), 'goto': 'QC'}],
        'mothAddress': [{'text': T('22 Gorse Street.', '戈尔斯街22号。'), 'goto': 'KA'}],
        'eliasKrumm': [{'text': T('Elias Krumm.', '埃利亚斯·克鲁姆。'), 'goto': 'KE'}],
        'mothComing': [{'text': T('You want to come to my door.', '你想来敲我的门。'), 'goto': 'KC'}],
        'byte': [{'text': T('Your cat. Byte.', '你的猫。字节。'), 'goto': 'KB'}],
        'mothHacker': [{'text': T('Where did you learn all this?', '你这些都是在哪学的？'), 'goto': 'KX'}],
        'fakeCourier': [{'text': T('The fake courier trick.', '假快递员那一招。'), 'goto': 'KF'}],
        'noraPell': [{'text': T('Nora Pell.', '诺拉·佩尔。'), 'goto': 'QC'}],
        'mask': [{'text': T('The moth mask.', '那个面具。'), 'goto': 'KM'}],
        'webcamTape': [{'text': T('You taped your webcam.', '你把摄像头贴上了。'), 'goto': 'KT'}],
        'traceroute': [{'text': T('Your traceroute.', '你的追踪路由。'), 'goto': 'KR'}],
        'nightShift': [{'text': T('No night shift today?', '你今天不用上夜班？'), 'goto': 'KS'}],
        'none': [{'text': T('...Never mind.', '...算了。'), 'goto': 'H'}]}}
    mc['KN'] = cn('...I hope she changed her locks.|I hope she changed everything.', '...希望她换了锁。|希望她什么都换了。', opts=back)
    mc['KA'] = cn('Yeah, you know my address. Everybody does.|Pizza Now knows it. My mom knows it. Now you.', '对，你知道我的地址。大家都知道。|披萨现在知道。我妈知道。现在你也知道。', opts=back)
    mc['KE'] = cn('Don\'t call me that.|Only Mom calls me that.', '别那样叫我。|只有我妈会那样叫我。', opts=back)
    mc['KC'] = cn('...|Stop reading my mind. That\'s MY job.', '...|别读我的心。那是我的工作。', opts=back)
    mc['KB'] = cn('Leave Byte out of this.|She\'s the only one in this flat who did nothing wrong.', '别把字节扯进来。|她是这间屋子里唯一没做错事的。', opts=back)
    mc['KX'] = cn('H4CK SCHOOL, episode 7.|Everything I know, he taught me. In a ski mask.', 'H4CK SCHOOL，第七集。|我会的全是他教的。戴着头套教的。', opts=back)
    mc['KF'] = cn('I learned that one from H4CK SCHOOL.|...|Dorian used it too. Didn\'t he.', '那招是我在H4CK SCHOOL学的。|...|多里安也用了。对吧。', opts=back)
    mc['KM'] = cn('I made that mask when I was twelve.|It was supposed to be cool.', '那个面具是我十二岁做的。|本来应该很酷的。', opts=back)
    mc['KT'] = cn('Yeah. You can still see me, can\'t you?|Tape doesn\'t work on microphones.', '对。你还是看得到我，对吧？|胶带对麦克风没用。', opts=back)
    mc['KR'] = cn('It can\'t reach you.|...Yet.', '它到不了你那里。|...暂时。', opts=back)
    mc['KS'] = cn('I called in sick.|For you. Feel special.', '我请病假了。|为了你。觉得自己很特别吧。', opts=back)
    mc['BYE'] = cn('Bye, observer.|Don\'t blink.', '再见，观察者。|别眨眼。', end=True)

    door = {
        '1': node('Delivery for... the observer.', '快递...给观察者的。', opts=[
            (('I didn\'t order anything.', '我没订东西。'), '2'),
            (('I know who you are, Elias.', '我知道你是谁，埃利亚斯。'), '3'),
            ]),
        '2': node('No. But you watched everything I did. For a week.', '对。但你看了我做的每一件事。整整一个星期。', opts=[(('...', '...'), '4')], init=[SV('mothVisited')]),
        '3': node('Then we\'re even. Now I know your door. And your face.', '那我们扯平了。现在我知道你家的门。还有你的脸。', opts=[(('...', '...'), '4')], init=[SV('mothVisited')]),
        '4': node('I\'m not here to hurt you. I\'m here so you know how it feels.', '我不是来伤害你的。我只是要你知道那是什么感觉。', opts=[
            (('Do you want to come in?', '你要进来吗？'), '10'),
            (('Go home, Elias.', '回家吧，埃利亚斯。'), '11')]),
        '10': node('...No. I just wanted to see a real face. Not a screen.|Here. This is for you. Don\'t open it indoors.|Goodnight, observer.',
                   '...不用。我只是想看一张真的脸。不是屏幕。|拿着。这是给你的。别在屋里打开。|晚安，观察者。'),
        '11': node('...Yeah. Home. Byte is waiting.|Oh. Take this. I said I\'d bring it myself.|Goodnight.',
                   '...嗯。回家。字节在等我。|哦。这个给你。我说过要亲手送来。|晚安。'),
    }
    # ---------------------------------------------------------------- v2.5: more to say in every conversation
    M = 'masculina1'
    # m0th's call on day 6: the player can answer with the notebook too
    calls['mothCalls']['5']['texts'].append({'text': T('(Notebook) I know what you\'re planning.', '（翻开笔记本）我知道你在打什么主意。'), 'gotoKeywords': '9'})
    calls['mothCalls']['9'] = {'voice': M, 'text': '', 'keywords': {
        'mothComing': [kwopt('You\'re coming to my door.', '你要来我家门口。', '91')],
        'eliasKrumm': [kwopt('Go home, Elias. Stay home.', '回家吧，埃利亚斯。待在家里。', '92')],
        'byte': [kwopt('Who feeds Byte while you\'re out?', '你出门的时候谁喂字节？', '93')],
        'mask': [kwopt('Are you coming in that mask?', '你会戴着那个面具来吗？', '94')],
        'kestrelLane': [kwopt('Like Dorian went to Kestrel Lane?', '就像多里安去红鹰巷那样？', '95')],
        'fakeCourier': [kwopt('Dressed as a courier?', '扮成快递员？', '96')],
        'none': [kwopt('...Nothing.', '...没什么。', '8')]}}
    calls['mothCalls'].update({
        '91': node('Of course you know. I wanted you to know.|That\'s the whole point.', '你当然知道。我就是要你知道。|这才是重点。', voice=M),
        '92': node('...Only Mom says it like that.|I\'ll go home. After.', '...只有我妈会这样说。|我会回家的。之后。', voice=M),
        '93': node('Mom has a key. Byte likes her more anyway.', '我妈有钥匙。反正字节比较喜欢她。', voice=M),
        '94': node('No. Real face this time.|You\'ve seen the mask enough.', '不戴。这次用真脸。|面具你看够了。', voice=M),
        '95': node('That\'s not— I\'m not him.|I just want to see you. Then I go.', '那不一样——我不是他。|我只是想看看你。看完就走。', voice=M),
        '96': node('Ha. H4CK SCHOOL, episode 9.|No. I\'ll just knock. Like a person.', '哈。H4CK SCHOOL第九集。|不。我会直接敲门。像个正常人。', voice=M),
    })
    # Nora: more of her life reacts (phase A: the creepy details make her suspicious; warned: small talk)
    nA = calls['callNora']['10']['keywords']
    nA.update({
        'sister': [kwopt('Your sister would want you to stay with her.', '你姐姐会希望你去她那住几天。', 'P2')],
        'sweetCrumb': [kwopt('Someone has been asking about you at Sweet Crumb.', '有人在甜屑面包店打听你。', 'P2')],
        'biscuit': [kwopt('Is Biscuit okay?', '饼干还好吗？', '11')],
        'bike': [kwopt('Don\'t ride the blue bike home tonight.', '今晚别骑那辆蓝色自行车回家。', '11')],
        'mothHacker': nA.get('mothHacker', []),
    })
    calls['callNora']['11'] = node('...How do you know about that?|Who is this? I\'m hanging up. I\'m calling the police.', '...你怎么会知道这个？|你是谁？我要挂了。我要报警。', voice=F)
    nW = calls['callNora']['30']['keywords']
    nW.update({
        'biscuit': [kwopt('How is Biscuit?', '饼干怎么样？', '33')],
        'noraPell': [kwopt('Nora Pell...', '诺拉·佩尔...', '34')],
        'sweetCrumb': [kwopt('Are you going back to Sweet Crumb?', '你还会回甜屑面包店吗？', '35')],
    })
    calls['callNora'].update({
        '33': node('Asleep on my sister\'s sofa. He hates her dog.|...Why am I telling you this.', '在我姐姐家的沙发上睡觉。它讨厌她的狗。|...我干嘛跟你说这些。', voice=F),
        '34': node('Don\'t. That name is gone.|I\'m Vance. I was always Vance.', '别这样叫。那个名字已经没了。|我姓万斯。我一直都姓万斯。', voice=F),
        '35': node('Next month. Morning shift. New bike, new route.|The bread doesn\'t care who\'s watching.', '下个月吧。早班。新车子，新路线。|面包才不管谁在看。', voice=F),
    })
    nC = calls['callNora']['20']['keywords']
    nC.update({
        'sister': [kwopt('Are you at your sister\'s?', '你在姐姐家吗？', '22')],
        'biscuit': [kwopt('Did Biscuit get out?', '饼干逃出来了吗？', '24')],
    })
    calls['callNora']['24'] = node('He was under the bed. A neighbour found him in the morning.|He\'s fine. I\'m not.', '它躲在床底下。邻居早上找到它的。|它没事。我有事。', voice=F)
    # Police: more reports get a real answer instead of nothing
    pol = calls['callPolice']['10']['keywords']
    pol.update({
        'darkBoard': [kwopt('People sell addresses on a site called DarkBoard.', '有人在一个叫暗板论坛的网站上卖地址。', '20')],
        'bounty': [kwopt('Someone put a bounty on a woman\'s address.', '有人悬赏一个女人的住址。', '6')],
        'h4ckSchool': [kwopt('A video channel teaches kids to hack people.', '有个视频频道在教小孩黑别人。', '21')],
        'pizzaNow': [kwopt('Pizza Now gave out a customer\'s address online.', '披萨现在在网上泄漏了顾客的地址。', '22')],
        'byte': [kwopt('There\'s a cat in danger. Sort of.', '有一只猫有危险。算是吧。', '23')],
        'vpn': [kwopt('A free VPN is leaking its users\' addresses.', '有个免费VPN在泄漏用户的地址。', '24')],
        'relayServer': [kwopt('Someone is watching people through their webcams.', '有人透过摄像头在监视别人。', '25')],
    })
    calls['callPolice'].update({
        '20': {'voice': F, 'text': T('We know DarkBoard. We need a person, caller. A name or an address.', '我们知道暗板论坛。我们需要一个人。名字或地址。'),
               'keywords': {k: v for k, v in calls['callPolice']['4']['keywords'].items()}},
        '21': node('We can\'t arrest a video channel. If one of its viewers hurt someone, call us about him.', '我们没办法逮捕一个视频频道。如果它的观众伤害了谁，再打来说那个人。', voice=F),
        '22': node('That\'s for the data protection office. Unless someone used that address. Did they?', '那归资料保护单位管。除非有人用了那个地址。有吗？', voice=F),
        '23': node('...Animal control is another number, caller.', '...动物管制是另一个号码。', voice=F),
        '24': node('Write to the cybercrime unit. We take people, not software.', '请写信给网络犯罪组。我们抓的是人，不是软件。', voice=F),
        '25': node('Whose webcam? Yours? Put tape on it and call us with a name.', '谁的摄像头？您的吗？先用胶带贴起来，有名字再打给我们。', voice=F),
    })
    # Chat hub: more of the notebook gets an answer
    mc = chats['mothChat']
    mc['KH']['keywords'].update({
        'pizzaNow': [{'text': T('Pizza Now.', '披萨现在。'), 'goto': 'KP'}],
        'h4ckSchool': [{'text': T('H4CK SCHOOL.', 'H4CK SCHOOL。'), 'goto': 'KX'}],
        'darkBoard': [{'text': T('DarkBoard.', '暗板论坛。'), 'goto': 'KD'}],
        'vpn': [{'text': T('Your free VPN.', '你的免费VPN。'), 'goto': 'KV'}],
        'kestrelLane': [{'text': T('Kestrel Lane.', '红鹰巷。'), 'goto': 'KK'}],
        'phototaxis': [{'text': T('Phototaxis.', '趋光性。'), 'goto': 'KT2'}],
        'observer': [{'text': T('I\'m a club member.', '我是俱乐部会员。'), 'goto': 'KO'}],
        'restrainingOrder': [{'text': T('The restraining order.', '那张禁止令。'), 'goto': 'QC'}],
    })
    back = [(('Go on.', '继续说。'), 'H')]
    mc.update({
        'KP': cn('Pepperoni. Large. Every Friday.|That\'s how you found me, isn\'t it. I yelled my address at a pizza place.', '意式香肠。大号。每个星期五。|你就是这样找到我的，对吧。我对着披萨店大喊我的地址。', opts=back),
        'KD': cn('DarkBoard is where I found the job. And where Crow found me.|I deleted my account. It\'s still there in the cache.', '我在暗板论坛找到这个活。乌鸦也是在那里找到我的。|我删了帐号。缓存里还在。', opts=back),
        'KV': cn('Free. Leaky. Like me.|I paid for a real one yesterday. Too late, right?', '免费的。会漏的。跟我一样。|我昨天买了个正版的。太晚了，对吧？', opts=back),
        'KK': cn('Don\'t.|I typed it. Fourteen letters and a number. That\'s all it took.', '别提。|我打出来的。几个字加一个门牌号。就这么简单。', opts=back),
        'KT2': cn('Moths fly to the light until they burn.|I picked the name because it sounded cool. Then I read the article.', '飞虫往光里飞，直到烧死。|我取这个名字是因为听起来很酷。后来才读完那篇文章。', opts=back),
        'KO': cn('A member. Of a club that watches people.|And you think I\'m the creep?', '会员。一个专门看别人的俱乐部的会员。|而你觉得我才是变态？', opts=back),
    })
    # the gift: handed over at the door. Like the game's own door gifts (Wylon's visitors) it is given when the
    # talk ends; only if the player opened and talked (mothVisited). The prize has its own shelf object
    # (ModLoader 0.5.10 "prizes"), so the shelf is never "full" for it.
    door['1']['onCallEnd'] = [{'type': 'addPrize', 'id': 'mothJar', 'if': 'mothVisited'}]
    # the full address (Kestrel Lane 14) works wherever the street does
    import copy
    for conv in list(calls.values()) + list(chats.values()) + [door]:
        for n in conv.values():
            kw = n.get('keywords')
            if kw and 'kestrelLane' in kw and 'kestrel14' not in kw: kw['kestrel14'] = copy.deepcopy(kw['kestrelLane'])
    return calls, chats, door

# ------------------------------------------------------------------ keywords (id -> en, zh, extra)
KEYWORDS = [
    ('m0th', 'm0th', 'm0th', {}), ('eliasKrumm', 'Elias Krumm', '埃利亚斯·克鲁姆', {}), ('byte', 'Byte', '字节', {}),
    ('mom', 'Mom', '妈妈', {}), ('nightShift', 'night shift', '夜班', {}),
    ('h4ckSchool', 'H4CK SCHOOL', 'H4CK SCHOOL', {'browser': 'school'}), ('socialEngineering', 'social engineering', '社会工程学', {}),
    ('phishing', 'phishing', '诈骗邮件', {}), ('vpn', 'free VPN', '免费VPN', {}), ('fakeCourier', 'fake courier', '假快递员', {}),
    ('noraVance', 'Nora Vance', '诺拉·万斯', {'browser': 'nora'}), ('sweetCrumb', 'Sweet Crumb', '甜屑面包店', {'browser': 'bakery'}),
    ('biscuit', 'Biscuit', '饼干', {}), ('bike', 'blue bike', '蓝色自行车', {}), ('kestrelLane', 'Kestrel Lane', '红鹰巷', {}),
    ('crow', 'Crow', '乌鸦', {}), ('bounty', 'bounty', '赏金', {}), ('dorianPell', 'Dorian Pell', '多里安·佩尔', {'browser': 'dorian'}),
    ('restrainingOrder', 'restraining order', '禁止令', {}), ('intruder', 'intruder', '闯入者', {}),
    ('pocRelay', 'poc_relay.exe', 'poc_relay.exe', {}), ('observer', 'Club member', '会员', {}), ('webcamTape', 'taped webcam', '贴住的摄像头', {}),
    ('traceroute', 'traceroute', '追踪路由', {}), ('relayServer', 'relay server', '中继服务器', {}), ('mask', 'moth mask', '飞虫面具', {}),
    ('darkBoard', 'DarkBoard', '暗板论坛', {}), ('noraPhone', '555-0147', '555-0147', {'phone': 'callNora'}),
    ('mothAddress', '22 Gorse St, 3B', '戈尔斯街22号3B', {'isAddress': True}), ('mothPhone', '555-0193', '555-0193', {'phone': 'mothPhone'}),
    ('policeLine', '555-0110', '555-0110', {'phone': 'callPolice'}), ('sister', 'sister', '姐姐', {}),
]

# Words that only appear later in texts (news) also need to exist: intruder (news), sister (news), mask (cam object)

NEWS = {
    'newsTipLine': (('POLICE OPEN CYBERCRIME TIP LINE', '警方开通网络犯罪举报热线'),
                    ('Stalking, scams, stolen accounts: call [policeLine]555-0110[/policeLine]. "Most victims never report," says the chief.',
                     '跟踪、诈骗、被盗账号：请拨打[policeLine]555-0110[/policeLine]。局长说：“大多数受害者从不报案。”'),
                    'mods/MothScreen/web/news_tipline'),
    'newsIntruder': (('INTRUDER ON KESTREL LANE', '红鹰巷深夜闯入事件'),
                     ('A young woman escaped through a window when an [intruder]intruder[/intruder] broke into her home at number 14. Police ask for information: call [policeLine]555-0110[/policeLine].',
                      '一名[intruder]闯入者[/intruder]弄坏14号住宅的门锁，年轻女屋主从窗户逃生。警方呼吁知情者拨打[policeLine]555-0110[/policeLine]。'),
                     'mods/MothScreen/web/news_intruder'),
    'newsEmpty': (('BREAK-IN AT EMPTY FLAT', '空屋遭人闯入'),
                  ('An [intruder]intruder[/intruder] forced the door of number 14, Kestrel Lane. The tenant was staying with her [sister]sister[/sister]. Tip line: [policeLine]555-0110[/policeLine].',
                   '红鹰巷14号的大门被一名[intruder]闯入者[/intruder]弄坏。租客当时住在[sister]姐姐[/sister]家。举报热线：[policeLine]555-0110[/policeLine]。'),
                  'mods/MothScreen/web/news_empty'),
    'newsDorian': (('STALKER BACK BEHIND BARS', '跟踪狂再度入狱'),
                   ('Dorian Pell was arrested for violating a [restrainingOrder]restraining order[/restrainingOrder]. He had paid an online "researcher" to locate the victim.',
                    '多里安·佩尔因违反[restrainingOrder]禁止令[/restrainingOrder]被捕。他曾花钱请网上的“调查员”找出受害者的住址。'),
                   'mods/MothScreen/web/news_dorian'),
    'newsArrest': (('TEEN HACKER "M0TH" ARRESTED', '少年黑客“m0th”落网'),
                   ('Elias Krumm, 19, was arrested in his Gorse Street flat. He insists "a club of monkeys" was watching him. Police found only a cat.',
                    '十九岁的埃利亚斯·克鲁姆在戈尔斯街的住处被捕。他坚称有“一个猴子俱乐部”在监视他。警方只找到一只猫。'),
                   'mods/MothScreen/web/news_arrest'),
    'newsTurnIn': (('YOUNG MAN TURNS HIMSELF IN', '年轻人主动投案'),
                   ('A 19-year-old confessed to selling a woman\'s address online. His statement about "being watched" is being investigated.',
                    '一名十九岁青年承认在网上贩卖一名女子的住址。他关于“自己被监视”的说法正在调查中。'),
                   'mods/MothScreen/web/news_turnin'),
}

ENDINGS = {
    'mothScreenArrest': ('m0th was arrested in his pajamas. He told the police someone had been watching him through his own computer. Nobody believed him. Byte went to live with his mom.',
                         'm0th穿着睡衣被捕了。他告诉警察有人一直透过他的电脑监视他。没人相信他。字节被送去跟他妈妈住了。', 'mods/MothScreen/web/news_arrest'),
    'mothScreenTurnIn': ('Elias Krumm walked into a police station and told them everything: Crow, the address, the Club. They wrote down the first two.',
                         '埃利亚斯·克鲁姆走进警察局，把一切都说了：乌鸦、地址、俱乐部。警察只记下了前两样。', 'mods/MothScreen/web/news_turnin'),
    'mothScreenDoor': ('A boy in a helmet came to your door and left. You never saw m0th online again. Sometimes, at night, you still check your webcam light.',
                       '一个戴安全帽的男孩来到你家门口，又走了。你再也没在网上见过m0th。有时深夜里，你还是会看看自己的摄像头灯。', 'mods/MothScreen/web/end_door'),
    'mothScreenNoDoor': ('You never opened the door. m0th never came back online. But someone, somewhere, knows your building.',
                         '你始终没有开门。m0th再也没上线。但某个地方，有个人知道你住在哪栋楼。', 'mods/MothScreen/web/end_door'),
    'mothScreenMember': ('m0th became a member of the Primate Observation Club. Somewhere, a new camera light blinks.',
                         'm0th成为了灵长类动物观察俱乐部的会员。在某个地方，一个新的摄像头灯亮了起来。', 'mods/MothScreen/web/end_watch'),
    'mothScreenNora': ('Nora Vance moved in with her sister and changed every password. She never found out who called her that night.',
                       '诺拉·万斯搬去和姐姐一起住，换掉了所有密码。她始终不知道那晚是谁打电话给她。', 'mods/MothScreen/web/end_sisters'),
    'mothScreenNoraFled': ('Nora Vance jumped out of her kitchen window in her socks. She never went back to Kestrel Lane, and she still checks every car that slows down.',
                           '诺拉·万斯光着脚从厨房窗户跳了出去。她再也没回过红鹰巷，到现在还会盯着每一辆放慢速度的车。', 'mods/MothScreen/web/news_intruder'),
    'mothScreenNoraSpared': ('The police stopped Dorian Pell one street before Kestrel Lane. Nora Vance never knew how close he came.',
                             '警察在离红鹰巷一条街的地方挡下了多里安·佩尔。诺拉·万斯始终不知道他离她有多近。', 'mods/MothScreen/web/end_sisters'),
    'mothScreenDorianFree': ('Nobody reported Dorian Pell. He is still out there, and he has learned to pay better hackers.',
                             '没有人举报多里安·佩尔。他还在外面，而且学会了花钱请更好的黑客。', 'mods/MothScreen/web/news_dorian'),
    'mothScreenDorian': ('Dorian Pell went back to jail. In his cell he keeps asking who reported him. Nobody tells him.',
                         '多里安·佩尔回到了监狱。他在牢房里一直问是谁举报了他。没人告诉他。', 'mods/MothScreen/web/end_bars'),
}

EMAILS = {
    'mothMail': {'email': ('m0th@freevpn.leak', 'm0th@freevpn.leak'),
                 'subject': ('I can see you too', '我也看得到你'),
                 'text': ('Hi observer.\n\nI found poc_relay.exe. I found your relay. I found your Club.\n\nYou watched me sell a woman\'s address and you watched me cry about it.\n\nI opened a chat port on your relay. Talk to me. Or don\'t, and I\'ll keep looking.\n\nThe moth always finds the light.\n\n- m0th',
                          '你好，观察者。\n\n我找到了poc_relay.exe。我找到了你的中继。我找到了你的俱乐部。\n\n你看着我卖掉一个女人的地址，也看着我为此哭泣。\n\n我在你的中继上开了一个聊天端口。跟我说话。或者不说，那我就继续找。\n\n飞虫总会找到光。\n\n——m0th')},
}
MISSION = {
    'q': ('What alias does the subject of Cage {%storyNumber} use on the internet?', '笼子{%storyNumber}的观察对象在网上用什么网名？'),
    'answers': ['m0th'],
}
PRIZES = {
    'mothJar': (('Moth in a jar', '罐子里的飞虫'), ('A live moth in a jam jar. He handed it over at your door at one in the morning. A note: "Now you know."',
                                                   '果酱罐里装着一只活的飞虫，是他凌晨一点在你家门口亲手交给你的。纸条上写着：“现在你懂了。”'), 15),
}
# MART deliveries to 22 Gorse Street (keyword mothAddress)
ITEMS = {
    'beer': [('A box of Bulky Cola? I didn\'t order this.', '一箱批量可乐？我没订这个。'), ('...Free cola is free cola. Thank you, mysterious stranger.', '...免费的可乐就是免费的可乐。谢谢你，神秘人。')],
    'laxative': [('"Happy Mornings"? Somebody sent me... medicine?', '“清晨乐”？有人寄给我...药？'), ('It says "for a happy tummy". I\'ll try one.', '上面写“让肚子开心”。我试一颗。'),
                 ('...', '...'), ('Oh no. Oh NO. BRB.', '哦不。哦不！马上回来。')],
    'dolly': [('A doll. With big glass eyes.', '一个娃娃。眼睛是大大的玻璃珠。'), ('...Are those cameras? ARE THOSE CAMERAS?', '...那是摄像头吗？那是摄像头吗？！'),
              ('Into the closet. Facing the wall.', '丢进衣柜。脸朝墙。')],
    'default': [('A package. No sender.', '一个包裹。没有寄件人。'), ('Somebody knows my address. Of course they do. I yelled it to a pizza place.', '有人知道我的地址。当然啦。我对着披萨店大喊过。')],
}

# ------------------------------------------------------------------ daily schedule
# m0th sleeps in the morning and works night shifts, so each day plays between 14:00 and about 21:00.
HOURS = {'d1_boot': 14, 'd1_tutorial': 15, 'd1_job': 16.5, 'd1_profile': 17.75, 'd1_pizza': 19, 'd1_night': 20.5,
         'd2_vpn': 14, 'd2_phish': 15, 'd2_call': 16, 'd2_photo': 17.25, 'd2_crow': 19.5, 'd2_night': 20.5,
         'd3_result': 14, 'd3_mom': 16, 'd3_number': 18, 'd3_paid': 19.5, 'd3_night': 20.5,
         'd4_news': 14, 'd4_dorian': 16.25, 'd4_relay': 17.5, 'd4_trace': 19, 'd4_dark': 20.5,
         'd5_poc': 14, 'd5_chat': 17, 'd5_crow': 19, 'd5_video': 20.25, 'd5_night': 21,
         'd6_geo': 14, 'd6_call': 15, 'd6_gift': 16.5, 'd6_crowCheck': 18.5, 'd6_leave': 21, 'd7_dawn': 22,
         'd7_end': 14}
for _n, _h in HOURS.items():
    SCENES[_n]['hour'] = str(_h)
for _n in ('d2_night', 'd3_night', 'd4_dark', 'd5_night', 'd7_dawn'):
    SCENES[_n]['modify'] = 'today'

# ------------------------------------------------------------------ late-night merges
# A scene's "today"/"nextAvailable" is resolved when the previous scene ENDS. A long scene that starts at 21-22h
# can end after midnight, and a following "today 23:54" scene would then be scheduled for the NEXT evening,
# skipping a whole day. So the short night scenes are appended to the scene before them.
def _merge(first, second):
    a, b = SCENES[first], SCENES.pop(second)
    # only the first scene's final stopLed goes (the merged part continues the scene); the LED-off actions inside
    # (sleep_screen) must stay, or the LED burns all night on a sleeping screen (v2.1 bug on every merged night)
    body = a['script'][:-1] if a['script'] and a['script'][-1].get('action') == 'stopLed' else a['script']
    a['script'] = body + b['script']
    if 'goto' in b: a['goto'] = b['goto']
    else: a.pop('goto', None)
    for k in ('startEvents', 'finishEvents'):
        if b.get(k): a.setdefault('finishEvents' if k == 'finishEvents' else 'startEvents', []).extend(b[k])

for _first, _second in (('d2_crow', 'd2_night'), ('d3_paid', 'd3_night'), ('d5_video', 'd5_night'),
                        ('d4_trace', 'd4_dark'), ('d6_leave', 'd7_dawn')):
    _merge(_first, _second)
# the first scene of every morning: 'nextAvailable' works whether the night scene ended before or after midnight
for _m in ('d2_vpn', 'd3_result', 'd4_news', 'd5_poc', 'd6_geo', 'd7_end'):
    SCENES[_m]['modify'] = 'nextAvailable'
