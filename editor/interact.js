/* DNFTM Mod Editor - game events and interaction forms (news, email & missions, recordings, chat, phone, items). */
'use strict';

// ------------------------------------------------------------------ events

/** Field kinds: num, str, text (localized), bool, scene, news, email, chat, call, prize, generic, events (nested list). */
const EVENTS = {
  addMoney:      { label: '💰 金钱', fields: [['q', 'num', '金额（负数=扣钱）'], ['concept', 'text', '银行明细说明']] },
  modifyKarma:   { label: '☯ 业力', fields: [['q', 'num', '变化量（负数=变坏）']] },
  setVar:        { label: '🏷 设置变量', fields: [['name', 'str', '变量名'], ['value', 'str', '值（unset = 清除）']] },
  changeScene:   { label: '🎬 切换场景', fields: [['scene', 'scene', '场景'], ['force', 'bool', '立即强制切换']] },
  addNew:        { label: '📰 刊登新闻', fields: [['id', 'news', '新闻']] },
  removeNew:     { label: '📰 撤下新闻', fields: [['id', 'news', '新闻']] },
  addEmail:      { label: '✉ 寄出邮件', fields: [['id', 'email', '邮件']] },
  setChat:       { label: '💬 激活聊天对话', fields: [['id', 'chat', '对话'], ['showApp', 'bool', '自动打开聊天程序']] },
  removeChat:    { label: '💬 移除聊天对话', fields: [['id', 'chat', '对话']] },
  phoneCall:     { label: '📞 对方来电', fields: [['id', 'call', '通话']] },
  callTo:        { label: '📞 开放拨打', fields: [['id', 'call', '通话']] },
  addPrize:      { label: '🎁 获得物品', fields: [['id', 'prize', '物品']] },
  removePrize:   { label: '🎁 失去物品', fields: [['id', 'prize', '物品']] },
  mailman:       { label: '📦 邮差送货', fields: [['image', 'str', '包裹图片（例如 Cartero）'], ['events', 'events', '送达时发生的事件']] },
  endDiary:      { label: '🏁 笼子结案', fields: [] },
  pendingDiary:  { label: '⏳ 笼子待结案', fields: [] },
  cancelDiary:   { label: '↩ 取消结案', fields: [] },
  modifyHealth:  { label: '❤ 健康', fields: [['q', 'num', '变化量']] },
  modifySleep:   { label: '💤 睡眠', fields: [['q', 'num', '变化量']] },
  reduceHunger:  { label: '🍗 饥饿', fields: [['q', 'num', '变化量']] },
  addNeighbourPhrase: { label: '🗨 邻居闲聊', fields: [['text', 'text', '内容']] },
  openCam:       { label: '📷 打开摄影机', fields: [['cam', 'str', '笼子 id']] },
  playSound:     { label: '🔊 音效', fields: [['sound', 'str', '音效名称']] },
  addEnding:     { label: '📜 加入结局总结', fields: [['id', 'ending', '结局页']] },
  endGame:       { label: '☠ 游戏结局（结束游戏）', fields: [['ending', 'str', '结局 id（endings.json 的 frames）']] },
  knockDoor:     { label: '🚪 有人敲门', fields: [['image', 'door', '门外的人'], ['whenHome', 'bool', '玩家在家才敲'], ['whenAwake', 'bool', '玩家醒着才敲'], ['repeat', 'bool', '没开门就重复敲'], ['conversation', 'conv', '开门后的对话']] },
  addCalendarEvent: { label: '📅 日历事件', fields: [['text', 'text', '内容'], ['periodicity', 'str', '周期（daily / weekly，可留空）']] },
  addNote:       { label: '📝 冰箱便条', fields: [['text', 'text', '便条内容'], ['events', 'events', '玩家读便条时的事件']] },
  insertActions: { label: '🎬 插入剧情动作', fields: [['actions', 'json', '动作（JSON 数组）'], ['camera', 'str', '镜头（可留空）']] },
};
const EVENT_COMMON = ['type', 'if', 'ifNot', 'when', 'day', 'hour'];

function eventSources(d) {
  return {
    scene: Object.keys(d.script.scenes || {}), news: Object.keys(d.news || {}), email: Object.keys(d.emails || {}),
    chat: Object.keys(d.chats || {}), call: Object.keys(d.phoneCalls || {}), prize: Object.keys(d.prizes || {}),
    generic: Object.keys(d.genericEvents || {}),
    ending: Object.keys(((cageModOf(d) || {}).merges || {})['endings.json'] ? cageModOf(d).merges['endings.json'].frames || {} : {}),
    door: ['Policia', 'FBI', 'Testigos', 'TestigosPlanta', 'Domina', 'fake'],
  };
}

function eventList(list, mod, id, d, opts) {
  opts = opts || {};
  const box = h('div', {});
  const redraw = () => box.replaceWith(eventList(list, mod, id, d, opts));
  const src = eventSources(d);
  list.forEach((ev, i) => {
    const def = EVENTS[ev.type];
    const card = h('div', { class: 'action', style: 'border-left-color:#6fd08c' });
    const typeSel = h('select', { onchange: e => {
      const keep = {}; for (const k of ['if', 'ifNot', 'when', 'day', 'hour']) if (ev[k] !== undefined) keep[k] = ev[k];
      for (const k of Object.keys(ev)) delete ev[k];
      Object.assign(ev, { type: e.target.value }, keep);
      changed(); redraw();
    } }, Object.entries(EVENTS).map(([k, v]) => h('option', { value: k, selected: k === ev.type }, v.label)), def ? null : h('option', { value: ev.type, selected: true }, '其他：' + ev.type));
    card.append(h('div', { class: 'head' }, h('span', { class: 'num' }, (i + 1) + '.'), typeSel,
      h('div', { class: 'tools' },
        h('button', { class: 'small', onclick: () => { if (i > 0) { [list[i - 1], list[i]] = [list[i], list[i - 1]]; changed(); redraw(); } } }, '↑'),
        h('button', { class: 'small', onclick: () => { list.splice(i + 1, 0, clone(ev)); changed(); redraw(); } }, '⧉'),
        h('button', { class: 'small danger', onclick: () => { list.splice(i, 1); changed(); redraw(); } }, '✕'))));
    const body = h('div', { class: 'body' });
    for (const [k, kind, label] of (def ? def.fields : [])) {
      const f = h('div', { class: 'field', style: kind === 'text' || kind === 'events' ? 'width:100%' : '' }, h('label', {}, label));
      if (kind === 'num') f.append(h('input', { type: 'number', step: 'any', value: ev[k] ?? '', oninput: e => { ev[k] = e.target.value === '' ? undefined : +e.target.value; changed(); } }));
      else if (kind === 'str') f.append(h('input', { value: ev[k] ?? '', oninput: e => { ev[k] = e.target.value; changed(); } }));
      else if (kind === 'bool') f.append(h('input', { type: 'checkbox', checked: !!ev[k], onchange: e => { if (e.target.checked) ev[k] = true; else delete ev[k]; changed(); } }));
      else if (kind === 'text') f.append(textRef(mod, id, () => ev[k], v => { ev[k] = v; }));
      else if (kind === 'events') { ev[k] = ev[k] || []; f.append(h('div', { class: 'inner' }, eventList(ev[k], mod, id, d))); }
      else if (kind === 'conv') { ev[k] = ev[k] || { 1: { text: [{ text: '' }], texts: [] } }; f.append(h('div', { class: 'inner' }, conversationEditor(ev[k], mod, id, d, false))); }
      else if (kind === 'json') {
        const ta = h('textarea', { rows: 5 }); ta.value = JSON.stringify(ev[k] || [], null, 1);
        f.append(ta, h('button', { class: 'small', onclick: () => { try { ev[k] = parseLoose(ta.value); changed(); toast('已应用'); } catch (e) { toast('JSON 错误：' + e.message, true); } } }, '应用'));
      }
      else {
        const opts2 = src[kind] || [];
        f.append(h('select', { onchange: e => { ev[k] = e.target.value; changed(); } }, h('option', { value: '' }, '（选择）'),
          opts2.map(o => h('option', { value: o, selected: ev[k] === o }, o)),
          ev[k] && !opts2.includes(ev[k]) ? h('option', { value: ev[k], selected: true }, ev[k] + '（不存在）') : null));
      }
      body.append(f);
    }
    // timing and conditions
    const when = h('details', { style: 'width:100%' }, h('summary', { class: 'muted', style: 'font-size:12px;cursor:pointer' },
      '时间与条件' + (ev.when || ev.if || ev.ifNot ? '（已设置）' : '')));
    when.append(h('div', { class: 'row', style: 'margin:4px 0' },
      lbl('何时', 'ev.when'), h('select', { onchange: e => { if (e.target.value) ev.when = e.target.value; else { delete ev.when; delete ev.day; delete ev.hour; } changed(); redraw(); } },
        h('option', { value: '' }, '立刻'), h('option', { value: 'future', selected: ev.when === 'future' }, '之后（指定天数与时间）')),
      ev.when === 'future' ? [h('label', {}, '几天后'), h('input', { value: ev.day ?? '+1', style: 'width:60px', title: '+1 = 明天，0 = 今天', oninput: e => { ev.day = e.target.value; changed(); } }),
        h('label', {}, '几点'), h('input', { value: ev.hour ?? '10', style: 'width:60px', title: '10 = 10 点；+1 = 一小时后', oninput: e => { ev.hour = e.target.value; changed(); } })] : null),
      h('div', { class: 'row', style: 'margin:4px 0' },
        h('label', {}, 'if'), h('input', { value: ev.if || '', placeholder: '变量A,变量B', oninput: e => { if (e.target.value) ev.if = e.target.value; else delete ev.if; changed(); } }),
        h('label', {}, 'ifNot'), h('input', { value: ev.ifNot || '', oninput: e => { if (e.target.value) ev.ifNot = e.target.value; else delete ev.ifNot; changed(); } })));
    const known = new Set([...(def ? def.fields.map(f => f[0]) : []), ...EVENT_COMMON]);
    const extras = Object.keys(ev).filter(k => !known.has(k));
    if (extras.length || !def) {
      const ta = h('textarea', { rows: 3 }); const ex = {}; for (const k of extras) ex[k] = ev[k]; ta.value = JSON.stringify(ex, null, 1);
      when.append(h('label', {}, '其他字段（JSON）'), ta, h('button', { class: 'small', onclick: () => {
        try { const v = parseLoose(ta.value); for (const k of extras) delete ev[k]; Object.assign(ev, v); changed(); redraw(); } catch (e) { toast('JSON 错误：' + e.message, true); }
      } }, '套用'));
    }
    body.append(when);
    card.append(body);
    box.append(card);
  });
  const sel = h('select', {}, Object.entries(EVENTS).map(([k, v]) => h('option', { value: k }, v.label)));
  box.append(h('div', { class: 'row', style: 'margin-top:4px' }, sel, h('button', { class: 'small', onclick: () => { list.push({ type: sel.value }); changed(); redraw(); } }, '＋ 事件')));
  return box;
}

// ------------------------------------------------------------------ interaction tab

const INTERACT_SECTIONS = [
  ['news', '📰 新闻'], ['emails', '✉ 邮件与任务'], ['recordings', '🎥 录像投稿'], ['chat', '💬 聊天'],
  ['phone', '📞 电话'], ['prizes', '🎁 物品'], ['items', '📦 寄送商品'], ['endings', '📜 结局'], ['generic', '⚡ 自订事件'],
];

function interactTab(mod, id, d) {
  ui.isec = ui.isec || 'news';
  const wrap = h('div', {});
  wrap.append(h('div', { class: 'tabs', style: 'border-bottom:none' }, INTERACT_SECTIONS.map(([k, label]) =>
    h('button', { class: ui.isec === k ? 'sel' : '', onclick: () => { ui.isec = k; renderMain(); } }, label))));
  const fn = { news: newsSection, emails: emailSection, recordings: recordingSection, chat: chatSection, phone: phoneSection,
    prizes: prizeSection, items: itemSection, endings: endingSection, generic: genericSection }[ui.isec];
  wrap.append(fn(mod, id, d));
  return wrap;
}

/** Generic "map of id -> object" editor with add/rename/delete. */
function idMapEditor(map, title, makeNew, renderOne, opts) {
  opts = opts || {};
  const box = h('div', {});
  for (const key of Object.keys(map)) {
    const card = h('div', { class: 'card' });
    card.append(h('div', { class: 'row' }, h('b', { class: 'mono' }, key),
      opts.fixed && opts.fixed.includes(key) ? null : h('button', { class: 'small', onclick: () => {
        const nk = prompt('新的 id', key); if (!nk || nk === key || map[nk]) return;
        const entries = Object.entries(map); for (const k of Object.keys(map)) delete map[k];
        for (const [k, v] of entries) map[k === key ? nk : k] = v;
        changed(true);
      } }, '改名'),
      h('button', { class: 'small danger', onclick: () => { if (confirm('删除 ' + key + '？')) { delete map[key]; changed(true); } } }, '删除')));
    card.append(renderOne(key, map[key]));
    box.append(card);
  }
  box.append(h('button', { class: 'primary', onclick: () => {
    const k = prompt(title + ' id（英文和数字）', opts.suggest || '');
    if (!k) return; if (map[k]) { alert('已存在'); return; }
    map[k] = makeNew(k); changed(true);
  } }, '＋ ' + title));
  return box;
}

function fieldRow(label, el, wide, key) { return h('div', { class: 'field', style: wide ? 'width:100%' : '' }, lbl(label, key), el); }

function imagePicker(obj, key, prefixes, label) {
  const listId = 'img-' + Math.random().toString(36).slice(2);
  return fieldRow(label || '图片', h('div', {}, h('input', { value: obj[key] || '', list: listId, style: 'width:420px', oninput: e => { obj[key] = e.target.value; changed(); } }),
    h('datalist', { id: listId }, modImagePaths().concat(CAT.images.filter(p => prefixes.some(pr => p.startsWith(pr)))).map(p => h('option', { value: p })))), true);
}

// --- news
function newsSection(mod, id, d) {
  d.news = d.news || {};
  const wrap = h('div', {});
  wrap.append(h('div', { class: 'help' }, '每天早上报纸（桌上的 The New Truth）会刊登新闻。用事件「📰 刊登新闻」在剧情中加入；标题与内文可以用 [关键字]…[/关键字] 标记，让玩家从报纸收集关键字。'));
  wrap.append(idMapEditor(d.news, '新闻', () => ({ title: '', subtitle: '', image: 'newspapper/generic/GEN-14-Ciencia' }), (k, n) => h('div', {},
    fieldRow('标题', textRef(mod, id, () => n.title, v => { n.title = v; }), true),
    fieldRow('内文', textRef(mod, id, () => n.subtitle, v => { n.subtitle = v; }, { multiline: true }), true),
    imagePicker(n, 'image', ['newspapper/'], '配图')), { suggest: 'news1' }));
  return wrap;
}

// --- emails & missions
function emailSection(mod, id, d) {
  d.emails = d.emails || {};
  const E = d.emails;
  const wrap = h('div', {});
  wrap.append(h('div', { class: 'help' },
    '邮件用事件「✉ 寄出邮件」寄出。任务是特殊邮件：只要有 id 为 mission 的邮件，游戏会在适当的日子自动寄给玩家；',
    '玩家用笔记本上的关键字回复，reply 依回复的关键字运行事件（default = 其他答案）。答对通常寄出 missionCorrect（游戏会发放奖励 {%reward}），答错寄出 missionFail。'));
  if (!E.mission) wrap.append(h('button', { class: 'primary', onclick: () => missionWizard(mod, id, d) }, '🧭 任务精灵：创建任务邮件'));
  wrap.append(idMapEditor(E, '邮件', () => ({ subject: '', text: '', email: '' }), (k, m) => {
    const box = h('div', {});
    box.append(fieldRow('寄件人', textRef(mod, id, () => m.email, v => { m.email = v; }), true),
      fieldRow('主旨', textRef(mod, id, () => m.subject, v => { m.subject = v; }), true),
      fieldRow('内文（可用 {%storyNumber} 笼子编号、{%reward} 奖励）', textRef(mod, id, () => m.text, v => { m.text = v; }, { multiline: true }), true),
      h('div', { class: 'row' },
        fieldRow('有效天数', h('input', { type: 'number', value: m.caducity ?? '', oninput: e => { if (e.target.value) m.caducity = +e.target.value; else delete m.caducity; changed(); } }), false, 'caducity'),
        k === 'mission' ? fieldRow('特殊任务', h('input', { type: 'checkbox', checked: !!m.specialMission, onchange: e => { if (e.target.checked) m.specialMission = true; else delete m.specialMission; changed(); } }), false, 'specialMission') : null));
    if (k === 'mission' || m.reply) {
      m.reply = m.reply || {};
      box.append(h('h3', {}, '回复（玩家用哪个关键字回答 → 发生什么事）'));
      const kws = Object.keys(d.keywords || {}).filter(x => !x.includes(',') && !x.includes('_'));
      for (const rk of Object.keys(m.reply)) {
        box.append(h('div', { class: 'card', style: 'background:var(--bg)' }, h('div', { class: 'row' }, h('b', {}, rk === 'default' ? '其他答案（default）' : '回答：' + rk),
          h('button', { class: 'small danger', onclick: () => { delete m.reply[rk]; changed(true); } }, '删除')), eventList(m.reply[rk], mod, id, d)));
      }
      const sel = h('select', {}, h('option', { value: 'default' }, '其他答案（default）'), kws.map(x => h('option', { value: x }, x)));
      box.append(h('div', { class: 'row' }, sel, h('button', { class: 'small', onclick: () => { if (!m.reply[sel.value]) { m.reply[sel.value] = []; changed(true); } } }, '＋ 回复')));
    }
    for (const [ek, label] of [['events', '收到时的事件'], ['onOpen', '打开时'], ['onDelete', '删除时'], ['onExpire', '过期时']]) {
      if (!m[ek] && !(k === 'mission' && ek !== 'events')) continue;
      m[ek] = m[ek] || [];
      box.append(h('h3', {}, label), eventList(m[ek], mod, id, d));
    }
    return box;
  }, { suggest: 'mail1' }));
  return wrap;
}

function missionWizard(mod, id, d) {
  const kws = Object.keys(d.keywords || {}).filter(x => !x.includes(',') && !x.includes('_'));
  const qEn = h('input', { value: 'What is the name of the book the observed subject is reading?', style: 'width:100%' });
  const qZh = h('input', { value: '被观察对象正在读的书叫什幺名字？', style: 'width:100%' });
  const ans = h('select', { multiple: true, size: Math.min(6, Math.max(2, kws.length)) }, kws.map(k => h('option', { value: k }, k)));
  modal('任务精灵', h('div', { style: 'width:min(640px,80vw)' },
    h('div', { class: 'help' }, '会创建 mission（问题）、missionCorrect（答对）、missionFail（答错）三封邮件。游戏会自动寄出 mission，玩家用笔记本关键字回复。'),
    fieldRow('问题（English）', qEn, true), fieldRow('问题（简体中文）', qZh, true),
    fieldRow('正确答案（按住 Ctrl 可复选关键字）', ans, true)), [
    { label: '取消' },
    { label: '创建', primary: true, onClick: () => {
      const answers = Array.from(ans.selectedOptions).map(o => o.value);
      if (!answers.length) { alert('请至少选一个正确答案关键字（先到「关键字」分页创建）'); return false; }
      const sender = newRef(mod, id, 'Primate Observation Club', '灵长类动物观察俱乐部');
      const reply = {};
      for (const a of answers) reply[a] = [{ type: 'addEmail', id: 'missionCorrect', when: 'future', day: '0', hour: '+1' }];
      reply.default = [{ type: 'addEmail', id: 'missionFail', when: 'future', day: '0', hour: '+1' }];
      d.emails.mission = {
        subject: newRef(mod, id, 'Routine observation study in Cage {%storyNumber}', '笼子{%storyNumber}的例行观察研究'),
        text: newRef(mod, id, `Dear member,\nFor an important study of the Club, please answer the following question about Cage {%storyNumber}:\n\n- ${qEn.value}\n\nYour time will be rewarded with:\n- {%reward}\n\nPrimate Observation Club`,
          `亲爱的会员：\n为了俱乐部的一项重要研究，请回答以下关于笼子{%storyNumber}的问题：\n\n- ${qZh.value}\n\n你的时间将获得以下奖励：\n- {%reward}\n\n灵长类动物观察俱乐部`),
        email: sender, caducity: 5, reply,
      };
      d.emails.missionCorrect = {
        subject: newRef(mod, id, 'RE: Observation study in Cage {%storyNumber}', '回复：笼子{%storyNumber}的观察研究'),
        text: newRef(mod, id, 'Dear member,\nYour answer is correct. Here is the agreed reward:\n- {%reward}\n\nPrimate Observation Club', '亲爱的会员：\n你的回答是正确的。这是约定的奖励：\n- {%reward}\n\n灵长类动物观察俱乐部'),
        email: sender,
      };
      d.emails.missionFail = {
        subject: newRef(mod, id, 'RE: Observation study in Cage {%storyNumber}', '回复：笼子{%storyNumber}的观察研究'),
        text: newRef(mod, id, 'Dear member,\nUnfortunately the information you sent us is wrong.\n\nPrimate Observation Club', '亲爱的会员：\n很遗憾，你发给我们的信息是错误的。\n\n灵长类动物观察俱乐部'),
        email: sender,
      };
      changed(true);
    } }]);
}

// --- recordings
function recordingSection(mod, id, d) {
  // A cage without "recordings" cannot be recorded; only create the table when the author adds a result.
  const R = d.recordings || {};
  const wrap = h('div', {});
  wrap.append(h('div', { class: 'help' },
    '玩家可以录下摄影机画面寄给 Shock.tv。在剧情中用动作「🎥 标记可投稿」（setValidVideo）开始、「取消可投稿」结束，这段时间录到的视频算「有价值」，',
    '投稿时会使用 isValid 的结果；其他时候用 default。勾选 night 代表只有开夜视录到才算。'));
  if (!R.isValid) wrap.append(h('button', { onclick: () => { R.isValid = { success: true, text: newRef(mod, id, 'Your video is a BOMB! It will be on tonight\'s show.', '你的视频太劲爆了！今晚的节目会播出。'), events: [{ type: 'addMoney', q: 50, concept: newRef(mod, id, 'Shock.tv', 'Shock.tv') }] }; changed(true); } }, '＋ 创建 isValid（有价值的录像）'));
  if (!R.default) wrap.append(h('button', { onclick: () => { R.default = { success: false, text: newRef(mod, id, 'Your video is IRRELEVANT. No sex, no violence... why did you send this?', '你的视频毫无价值。没有暴力......你为什幺要发给我们？') }; changed(true); } }, '＋ 创建 default（没价值）'));
  wrap.append(idMapEditor(R, '录像结果', () => { d.recordings = R; return { success: false, text: '' }; }, (k, r) => {
    const box = h('div', {});
    box.append(fieldRow('会被播出（成功）', h('input', { type: 'checkbox', checked: r.success === true, disabled: Array.isArray(r.success), onchange: e => { r.success = e.target.checked; changed(); } }), false, 'recSuccess'),
      Array.isArray(r.success) ? h('div', { class: 'muted' }, '（success 使用条件清单，请在原始 JSON 编辑）') : null,
      Array.isArray(r.text) ? h('div', { class: 'muted' }, '（text 使用条件清单，请在原始 JSON 编辑）') : fieldRow('Shock.tv 回复', textRef(mod, id, () => r.text, v => { r.text = v; }, { multiline: true }), true));
    r.events = r.events || [];
    box.append(h('h3', {}, '投稿后的事件'), eventList(r.events, mod, id, d));
    return box;
  }, { fixed: ['isValid', 'default'], suggest: 'special' }));
  return wrap;
}

// --- conversation trees (chat & phone)
function conversationEditor(conv, mod, id, d, isChat) {
  const box = h('div', {});
  const nodeIds = () => Object.keys(conv).filter(k => k !== 'comments');
  const kws = Object.keys(d.keywords || {}).filter(x => !x.includes(',') && !x.includes('_'));
  for (const nid of nodeIds()) {
    const n = conv[nid];
    const card = h('div', { class: 'card', style: 'background:var(--bg)' });
    card.append(h('div', { class: 'row' }, h('b', {}, '节点 ' + nid), nid === '1' ? h('span', { class: 'muted' }, '（对话从这里开始）') : null,
      h('button', { class: 'small danger', onclick: () => { delete conv[nid]; changed(true); } }, '删除')));
    if (isChat && nid === '1') {
      const cfgs = Object.keys(d.chatConfig || {});
      card.append(h('div', { class: 'row' }, fieldRow('聊天对象（chatConfig）', h('select', { onchange: e => { n.config = e.target.value; n.who = n.who || 'me'; changed(); } },
        h('option', { value: '' }, '（选择）'), cfgs.map(c => h('option', { value: c, selected: n.config === c }, c))))));
    }
    // NPC lines: string or [{text, if, ifNot}]
    if (typeof n.text === 'string' || n.text === undefined) {
      card.append(fieldRow('对方说（用 | 分成多个泡泡）', textRef(mod, id, () => n.text, v => { n.text = v; }, { multiline: true }), true));
    } else {
      n.text.forEach((t, ti) => card.append(h('div', { class: 'row' },
        h('div', { style: 'flex:1' }, textRef(mod, id, () => t.text, v => { t.text = v; }, { multiline: true })),
        h('input', { value: t.if || '', placeholder: 'if', style: 'width:90px', oninput: e => { if (e.target.value) t.if = e.target.value; else delete t.if; changed(); } }),
        h('input', { value: t.ifNot || '', placeholder: 'ifNot', style: 'width:90px', oninput: e => { if (e.target.value) t.ifNot = e.target.value; else delete t.ifNot; changed(); } }),
        h('button', { class: 'small danger', onclick: () => { n.text.splice(ti, 1); changed(true); } }, '✕'))));
      card.append(h('button', { class: 'small', onclick: () => { n.text.push({ text: '' }); changed(true); } }, '＋ 条件台词'));
    }
    const optEditor = (list, label) => {
      const ob = h('div', {}, h('label', {}, label));
      list.forEach((o, oi) => ob.append(h('div', { class: 'row' },
        h('div', { style: 'flex:1' }, textRef(mod, id, () => o.text, v => { o.text = v; })),
        h('label', {}, '→'), h('select', { onchange: e => { if (e.target.value) o.goto = e.target.value; else delete o.goto; changed(); } },
          h('option', { value: '' }, '（结束）'), nodeIds().map(x => h('option', { value: x, selected: o.goto === x }, '节点 ' + x))),
        h('input', { value: o.if || '', placeholder: 'if', style: 'width:80px', oninput: e => { if (e.target.value) o.if = e.target.value; else delete o.if; changed(); } }),
        h('input', { value: o.ifNot || '', placeholder: 'ifNot', style: 'width:80px', oninput: e => { if (e.target.value) o.ifNot = e.target.value; else delete o.ifNot; changed(); } }),
        h('label', { title: '选这个选项会打开笔记本，玩家选的关键字决定接下来去哪（目标节点要设置「关键字提问」）' }, '📓'),
        h('select', { title: '打开笔记本（gotoKeywords）', onchange: e => { if (e.target.value) { o.gotoKeywords = e.target.value; delete o.goto; } else delete o.gotoKeywords; changed(true); } },
          h('option', { value: '' }, '—'), nodeIds().map(x => h('option', { value: x, selected: o.gotoKeywords === x }, '笔记本→' + x))),
        h('button', { class: 'small danger', onclick: () => { list.splice(oi, 1); changed(true); } }, '✕'))));
      ob.append(h('button', { class: 'small', onclick: () => { list.push({ text: '', goto: '' }); changed(true); } }, '＋ 选项'));
      return ob;
    };
    n.texts = n.texts || [];
    card.append(optEditor(n.texts, '玩家的回答选项'));
    if (kws.length) {
      // A node with "keywords" opens the notebook and ignores its normal options, so the dict is only created
      // when the first keyword answer is added (an empty one used to be written into every node).
      if (n.keywords && !Object.keys(n.keywords).length) delete n.keywords;
      const nk = n.keywords || {};
      const kb = h('div', {}, h('label', {}, '玩家拿笔记本关键字回答（可选）', tip('convKeywords')));
      for (const kw of Object.keys(nk)) kb.append(h('div', { class: 'inner' }, h('b', {}, kw === 'none' ? 'none（不选／挂断）' : kw),
        h('button', { class: 'small danger', onclick: () => { delete nk[kw]; if (!Object.keys(nk).length) delete n.keywords; changed(true); } }, '移除'), optEditor(nk[kw], '')));
      const ks = h('select', {}, ['none'].concat(kws).filter(k => !nk[k]).map(k => h('option', { value: k }, k === 'none' ? 'none（玩家不选／挂断，必加）' : k)));
      kb.append(h('div', { class: 'row' }, ks, h('button', { class: 'small', onclick: () => { if (ks.value) { n.keywords = nk; nk[ks.value] = [{ text: '', goto: '' }]; changed(true); } } }, '＋ 关键字回答')));
      if (n.keywords && !n.keywords.none) kb.append(h('div', { class: 'muted', style: 'color:var(--warn)' }, '要加一个 none：玩家不选任何字时的回答，否则对话可能卡住。'));
      card.append(kb);
    }
    if (isChat) card.append(h('label', { style: 'color:var(--text)' }, h('input', { type: 'checkbox', checked: !!n.end, onchange: e => { if (e.target.checked) n.end = true; else delete n.end; changed(); } }),
      ' 聊天在这里结束（没有选项的最后一个节点要勾选，否则聊天会卡住）'));
    const evKeys = [['onInitTalk', '进入此节点时的事件'], ['onFinishTalk', '离开此节点时的事件']];
    if (nid === '1' && !isChat) evKeys.push(['onCallEnd', '整段对话结束时的事件（例如上门送礼：🎁 获得物品）']);
    for (const [ek, label] of evKeys) {
      const det = h('details', {}, h('summary', { class: 'muted', style: 'cursor:pointer;font-size:12px' }, label + (n[ek] && n[ek].length ? `（${n[ek].length}）` : '')));
      n[ek] = n[ek] || [];
      det.append(eventList(n[ek], mod, id, d));
      card.append(det);
    }
    box.append(card);
  }
  box.append(h('button', { onclick: () => { const ids = nodeIds().map(Number).filter(x => !isNaN(x)); conv[String((ids.length ? Math.max(...ids) : 0) + 1)] = { text: '', texts: [] }; changed(true); } }, '＋ 节点'));
  return box;
}

function chatSection(mod, id, d) {
  d.chatConfig = d.chatConfig || {}; d.chats = d.chats || {};
  const wrap = h('div', {});
  wrap.append(h('div', { class: 'help' },
    '聊天分两部分：「聊天对象」设置头像、名称、什么时候在线；玩家收集到「解锁关键字」后就能在聊天程序找到对方。',
    '「对话」是一棵对话树，用事件「💬 激活聊天对话」决定目前要用哪一段。对话第一个节点要选聊天对象。'));
  wrap.append(h('h3', {}, '聊天对象'));
  const kws = Object.keys(d.keywords || {}).filter(x => !x.includes(',') && !x.includes('_'));
  wrap.append(idMapEditor(d.chatConfig, '聊天对象', () => ({ image: 'avatares chat/cazador - avatar', name: '', relatedKeyword: '', availability: [{ type: 'availability', hourBetween: '9-23', availability: true }, { type: 'availability', availability: false }] }), (k, c) => {
    const box = h('div', {});
    box.append(fieldRow('暱称', textRef(mod, id, () => c.name, v => { c.name = v; }), true), imagePicker(c, 'image', ['avatares chat/'], '头像'),
      fieldRow('解锁关键字', h('select', { onchange: e => { c.relatedKeyword = e.target.value; changed(); } }, h('option', { value: '' }, '（选择）'), kws.map(x => h('option', { value: x, selected: c.relatedKeyword === x }, x))), false, 'relatedKeyword'));
    c.availability = c.availability || [];
    const av = h('div', {}, lbl('在线规则', 'availability'));
    c.availability.forEach((r, ri) => av.append(h('div', { class: 'row' },
      h('select', { onchange: e => { r.availability = e.target.value === '1'; changed(); } }, h('option', { value: '1', selected: r.availability }, '在线'), h('option', { value: '0', selected: !r.availability }, '脱机')),
      h('label', {}, '时段'), h('input', { value: r.hourBetween || '', placeholder: '9-23', style: 'width:70px', oninput: e => { if (e.target.value) r.hourBetween = e.target.value; else delete r.hourBetween; changed(); } }),
      h('label', {}, 'if'), h('input', { value: r.if || '', style: 'width:90px', oninput: e => { if (e.target.value) r.if = e.target.value; else delete r.if; changed(); } }),
      h('label', {}, 'ifNot'), h('input', { value: r.ifNot || '', style: 'width:90px', oninput: e => { if (e.target.value) r.ifNot = e.target.value; else delete r.ifNot; changed(); } }),
      h('button', { class: 'small danger', onclick: () => { c.availability.splice(ri, 1); changed(true); } }, '✕'))));
    av.append(h('button', { class: 'small', onclick: () => { c.availability.push({ type: 'availability', availability: true }); changed(true); } }, '＋ 规则'));
    box.append(av);
    return box;
  }, { suggest: 'contact' }));
  wrap.append(h('h3', {}, '对话'));
  wrap.append(idMapEditor(d.chats, '对话', () => ({ 1: { config: Object.keys(d.chatConfig)[0] || '', who: 'me', text: '', texts: [] } }), (k, conv) => conversationEditor(conv, mod, id, d, true), { suggest: 'chat1' }));
  return wrap;
}

function phoneSection(mod, id, d) {
  d.phoneCalls = d.phoneCalls || {};
  const wrap = h('div', {});
  wrap.append(h('div', { class: 'help' }, '电话也是对话树。用事件「📞 对方来电」让对方打给玩家，或「📞 开放拨打」让玩家可以打给对方（需要在电话簿中有对方的号码）。'));
  wrap.append(idMapEditor(d.phoneCalls, '通话', () => ({ 1: { text: [{ text: '' }], texts: [] } }), (k, conv) => conversationEditor(conv, mod, id, d, false), { suggest: 'call1' }));
  return wrap;
}

// --- prizes and shop deliveries
function prizeSection(mod, id, d) {
  d.prizes = d.prizes || {};
  const wrap = h('div', {});
  wrap.append(h('div', { class: 'help' }, '物品（prizes）是玩家可以拿到、之后能卖掉的东西（例如寄来的包裹里的骷髅头）。用事件「🎁 获得物品」给玩家；卖掉时运行「卖出时的事件」。'));
  wrap.append(idMapEditor(d.prizes, '物品', k => ({ id: k, name: '', sellName: '', description: '', price: 50, events: [] }), (k, p) => {
    const box = h('div', {});
    p.id = k;
    box.append(fieldRow('名称', textRef(mod, id, () => p.name, v => { p.name = v; }), true),
      fieldRow('说明', textRef(mod, id, () => p.description, v => { p.description = v; }, { multiline: true }), true),
      fieldRow('卖出时银行明细', textRef(mod, id, () => p.sellName, v => { p.sellName = v; }), true),
      fieldRow('价格', h('input', { type: 'number', value: p.price ?? 0, oninput: e => { p.price = +e.target.value; changed(); } })));
    p.events = p.events || [];
    box.append(h('h3', {}, '卖出时的事件'), eventList(p.events, mod, id, d));
    box.append(shelfEditor(mod, k));
    return box;
  }, { suggest: 'prize1' }));
  return wrap;
}

/** ModLoader 0.5.10 "prizes": the prize's own object on the room's prize shelf. Without one the game freezes when the
 * player receives the prize (the info popup cannot close). */
function shelfEditor(mod, k) {
  const M = mod.manifest;
  const sp = (M.prizes || []).find(x => x.id === k);
  const box = h('div', { class: 'inner' });
  box.append(h('h3', {}, '物品架上的物件', tip('prizeShelf')));
  if (GAME_PRIZE_OBJECTS.includes(k)) { box.append(h('div', { class: 'muted' }, '这个 id 和游戏原有的物品相同，会直接用原版的物件。')); return box; }
  if (!sp) {
    box.append(h('div', { class: 'help' }, '游戏要在物品架上找到这个物品自己的物件才能显示它；没有的话，玩家收到时游戏会卡住。'));
    box.append(h('button', { class: 'primary', onclick: () => {
      M.prizes = M.prizes || [];
      M.prizes.push({ id: k, template: 'coca', x: -2.27, y: -0.85, image: '', selected: '', popup: '' });
      changed(true);
    } }, '＋ 在物品架上放这个物品'));
    return box;
  }
  const imgs = modImagePaths().map(p => p.replace(/^mods\/[^/]+\//, ''));
  const listId = 'prizeimgs-' + k;
  const imgIn = (key, label) => fieldRow(label, h('input', { value: sp[key] || '', list: listId, style: 'width:260px', oninput: e => { sp[key] = e.target.value.trim(); changed(); } }), false, 'prize_' + key);
  box.append(h('datalist', { id: listId }, imgs.map(p => h('option', { value: p }))));
  box.append(h('div', { class: 'row' },
    fieldRow('复制哪个原版物件的外形', h('select', { onchange: e => { sp.template = e.target.value; changed(); } },
      GAME_PRIZE_OBJECTS.map(n => h('option', { value: n, selected: sp.template === n }, n))), false, 'prize_template'),
    fieldRow('位置 x', numIn(sp, 'x')), fieldRow('位置 y', numIn(sp, 'y')),
    h('div', { class: 'muted' }, '门左边的小柜子 (-2.27, -0.85) 没有任何原版物品。1 单位约为画面的 244 像素。')));
  box.append(h('div', { class: 'row' }, imgIn('image', '物品架上的图'), imgIn('selected', '实际显示的图（多一圈深色外框）'), imgIn('popup', '说明大图 289×183')));
  box.append(h('button', { class: 'small danger', onclick: () => { M.prizes = M.prizes.filter(x => x.id !== k); if (!M.prizes.length) delete M.prizes; changed(true); } }, '移除物品架物件'));
  return box;
}

function itemSection(mod, id, d) {
  d.items = d.items || {};
  const wrap = h('div', {});
  wrap.append(h('div', { class: 'help' }, '玩家可以在 MART 商店买东西寄到笼子的地址（需要先在笔记本找出地址）。这里设置寄到这个笼子时会发生什么事。default = 寄其他东西时。'));
  const items = CAT.shopItems || [];
  for (const key of Object.keys(d.items)) {
    const it = d.items[key];
    it.direccion = it.direccion || [];
    const info = items.find(x => x.id === key);
    wrap.append(h('div', { class: 'card' }, h('div', { class: 'row' }, h('b', {}, key === 'default' ? '其他商品（default）' : `${key}（${info ? info.ch + ' / ' + info.en : '未知商品'}）`),
      h('button', { class: 'small danger', onclick: () => { delete d.items[key]; changed(true); } }, '删除')), eventList(it.direccion, mod, id, d)));
  }
  const sel = h('select', {}, h('option', { value: 'default' }, '其他商品（default）'), items.map(x => h('option', { value: x.id }, `${x.ch} / ${x.en}（$${x.price}）`)));
  wrap.append(h('div', { class: 'row' }, sel, h('button', { class: 'primary', onclick: () => { if (!d.items[sel.value]) { d.items[sel.value] = { direccion: [] }; changed(true); } } }, '＋ 寄送反应')));
  return wrap;
}

function genericSection(mod, id, d) {
  d.genericEvents = d.genericEvents || {};
  const wrap = h('div', {});
  wrap.append(h('div', { class: 'help' }, '自订事件是有名字的一组事件，可以在剧情动作「⚡ 触发自订事件」（triggerEvents）中重复使用。'));
  wrap.append(idMapEditor(d.genericEvents, '自订事件', () => [], (k, list) => eventList(list, mod, id, d), { suggest: 'myEvents' }));
  return wrap;
}

// ------------------------------------------------------------------ validation

function validateInteractions(mod, mi, id, d, add) {
  const nav = sec => ({ mod: mi, cage: id, tab: 'interact', isec: sec });
  const src = eventSources(d);
  const checkEvents = (list, where, sec) => (list || []).forEach((ev, i) => {
    const w = `${where} 事件 #${i + 1}`;
    const ref = { changeScene: ['scene', 'scene'], addNew: ['id', 'news'], removeNew: ['id', 'news'], addEmail: ['id', 'email'], setChat: ['id', 'chat'],
      removeChat: ['id', 'chat'], phoneCall: ['id', 'call'], callTo: ['id', 'call'], addPrize: ['id', 'prize'], removePrize: ['id', 'prize'], addEnding: ['id', 'ending'] }[ev.type];
    if (ref && ev[ref[0]] && !src[ref[1]].includes(ev[ref[0]]) && !(ev.type === 'addEmail' && /^mission/.test(ev[ref[0]]) && false))
      add('err', `${w}：找不到「${ev[ref[0]]}」。`, id, nav(sec));
    if (ref && !ev[ref[0]]) add('err', `${w}：还没选择目标。`, id, nav(sec));
    if (ev.events) checkEvents(ev.events, w, sec);
    if (ev.conversation) for (const [nid, n] of Object.entries(ev.conversation)) {
      if (!n || typeof n !== 'object') continue;
      for (const o of n.texts || []) if (o.goto && !ev.conversation[o.goto]) add('err', `${w}：对话选项跳到不存在的节点 ${o.goto}。`, id, nav(sec));
    }
  });
  for (const [k, m] of Object.entries(d.emails || {})) {
    for (const ek of ['events', 'onOpen', 'onDelete', 'onExpire']) checkEvents(m[ek], `邮件「${k}」`, 'emails');
    for (const [rk, list] of Object.entries(m.reply || {})) checkEvents(list, `邮件「${k}」回复 ${rk}`, 'emails');
  }
  if ((d.emails || {}).mission) for (const need of ['missionCorrect', 'missionFail'])
    if (!d.emails[need]) add('warn', `有任务邮件但缺少 ${need}。`, id, nav('emails'));
  for (const [k, r] of Object.entries(d.recordings || {})) checkEvents(r.events, `录像「${k}」`, 'recordings');
  for (const [k, p] of Object.entries(d.prizes || {})) checkEvents(p.events, `物品「${k}」`, 'prizes');
  for (const [k, it] of Object.entries(d.items || {})) checkEvents(it.direccion, `寄送「${k}」`, 'items');
  for (const [k, list] of Object.entries(d.genericEvents || {})) checkEvents(list, `自订事件「${k}」`, 'generic');
  const convCheck = (convs, label, sec) => {
    for (const [ck, conv] of Object.entries(convs || {})) {
      if (!conv['1']) add('err', `${label}「${ck}」没有节点 1。`, id, nav(sec));
      for (const [nid, n] of Object.entries(conv)) {
        if (nid === 'comments' || !n || typeof n !== 'object') continue;
        const opts = (n.texts || []).concat(...Object.values(n.keywords || {}));
        for (const o of opts) if (o.goto && !conv[o.goto]) add('err', `${label}「${ck}」节点 ${nid}：选项跳到不存在的节点 ${o.goto}。`, id, nav(sec));
        checkEvents(n.onInitTalk, `${label}「${ck}」节点 ${nid}`, sec); checkEvents(n.onFinishTalk, `${label}「${ck}」节点 ${nid}`, sec);
      }
      if (sec === 'chat' && conv['1'] && !(d.chatConfig || {})[conv['1'].config]) add('err', `聊天「${ck}」第一个节点没有选择聊天对象。`, id, nav(sec));
    }
  };
  convCheck(d.chats, '聊天', 'chat');
  convCheck(d.phoneCalls, '电话', 'phone');
  for (const sc of Object.values(d.script.scenes || {})) for (const ek of ['startEvents', 'finishEvents']) checkEvents(sc[ek], '场景', 'generic');
}

// ------------------------------------------------------------------ helpers for v0.4 additions

/** The mod that owns a cage data object (events need the mod's endings table). */
function cageModOf(d) { return project.mods.find(m => Object.values(m.files).includes(d)); }

// --- endings (merge/endings.json frames)
function endingSection(mod, id, d) {
  const E = mod.merges['endings.json'] = mod.merges['endings.json'] || {};
  E.frames = E.frames || {};
  const wrap = h('div', {});
  wrap.append(h('div', { class: 'help' },
    '游戏结束时会逐页显示每个笼子的结局总结。在这里定义结局页（文字 + 插图），再在剧情里用事件「📜 加入结局总结」把它加进去，',
    '通常放在笼子结案的时候；根据玩家的选择可以加入不同的结局页。插图可用游戏内置的结局插图，或 mod 自己的 PNG（mods/<Mod>/<文件>，需要 ModLoader 0.5）。'));
  wrap.append(idMapEditor(E.frames, '结局页', () => ({ text: '', image: '' }), (k, fr) => h('div', {},
    fieldRow('结局文字', textRef(mod, id, () => fr.text, v => { fr.text = v; }, { multiline: true }), true),
    imagePickerEndings(fr)), { suggest: id + '1' }));
  return wrap;
}

function imagePickerEndings(fr) {
  const listId = 'end-' + Math.random().toString(36).slice(2);
  // EndController loads "endingsImg/" + image
  return fieldRow('插图（游戏内置结局插图）', h('div', {}, h('input', { value: fr.image || '', list: listId, style: 'width:420px', oninput: e => { fr.image = e.target.value; changed(); } }),
    h('datalist', { id: listId }, modImagePaths().concat([...new Set(CAT.images.filter(p => p.startsWith('endingsimg/')).map(p => p.slice('endingsimg/'.length)))]).map(p => h('option', { value: p })))), true);
}

// --- browser result types
const BROWSER_TYPES = {
  new:   { label: '📰 新闻', make: () => ({ type: 'new', source: '', title: '', subtitle: '', text: '', image: '' }) },
  wiki:  { label: '📚 百科页面', make: () => ({ type: 'wiki', pageName: '', pageCategory: '', dataHeader: '', dataField1: '', dataField2: '', dataField3: '', dataField4: '', pageText: '', imageHeader: '', imageBottom: '' }) },
  meta:  { label: '👤 Metayou 社交主页', make: () => ({ type: 'meta', name: '', status: '', job: '', phone: '', image: '', email: '', posts: [] }) },
  guide: { label: '☎ 电话簿条目', make: () => ({ type: 'guide', name: '', address: '', phone: '' }) },
  map:   { label: '🗺 地图', make: () => ({ type: 'map', image: '', text: '', position: '' }) },
  web:   { label: '🌐 网页（自由排版）', make: () => ({ type: 'web', url: '', title: '', struct: [{ pos: { x: 0, y: 0, z: -1 }, image: 'newspapper/generic/GEN-14-Ciencia' }, { pos: { x: 0, y: 40, z: -20 }, size: 60, wrap: { width: 200, height: 60 }, alignment: 'center', font: 'blrrpixt', text: '' }] }) },
};

function browserResultEditor(mod, id, results, r, ri) {
  const rc = h('div', { class: 'card', style: 'background:var(--bg)' });
  const T = (f, label, multi) => fieldRow(label, textRef(mod, id, () => r[f], v => { r[f] = v; }, { multiline: multi }), true);
  rc.append(h('div', { class: 'row' }, h('b', {}, `结果 ${ri + 1}`), h('span', { class: 'muted' }, (BROWSER_TYPES[r.type] || { label: r.type }).label),
    h('button', { class: 'small', onclick: () => { if (ri > 0) { [results[ri - 1], results[ri]] = [results[ri], results[ri - 1]]; changed(true); } } }, '↑'),
    h('button', { class: 'small danger', onclick: () => { results.splice(ri, 1); changed(true); } }, '删除')));
  if (r.type === 'new' || !r.type) {
    rc.append(T('source', '来源'), T('title', '标题'), T('subtitle', '副标'), T('text', '内文', true), imageField(r));
  } else if (r.type === 'wiki') {
    rc.append(h('div', { class: 'help' }, '百科页面：页面名称、分类、右侧资料框（标题 + 4 行资料）、正文与插图。'),
      T('pageName', '页面名称'), T('pageCategory', '分类'), T('dataHeader', '资料框标题'),
      T('dataField1', '资料 1'), T('dataField2', '资料 2'), T('dataField3', '资料 3'), T('dataField4', '资料 4'), T('pageText', '正文', true),
      imagePicker(r, 'imageHeader', ['newspapper/'], '资料框插图'), imagePicker(r, 'imageBottom', ['newspapper/'], '底部插图'));
  } else if (r.type === 'meta') {
    rc.append(h('div', { class: 'help' }, 'Metayou 是游戏里的社交网站：头像、状态、职业、联络方式与贴文。'),
      T('name', '名字'), T('status', '状态'), T('job', '职业'), T('phone', '电话'), T('email', '邮箱'), imagePicker(r, 'image', ['newspapper/', 'avatares chat/'], '头像'));
    r.posts = r.posts || [];
    const pb = h('div', {}, h('label', {}, '贴文'));
    r.posts.forEach((p, pi) => pb.append(h('div', { class: 'card' }, h('div', { class: 'row' }, h('b', {}, '贴文 ' + (pi + 1)), h('button', { class: 'small danger', onclick: () => { r.posts.splice(pi, 1); changed(true); } }, '删除')),
      fieldRow('内容', textRef(mod, id, () => p.text, v => { p.text = v; }, { multiline: true }), true), imagePicker(p, 'image', ['newspapper/'], '图片'))));
    pb.append(h('button', { class: 'small', onclick: () => { r.posts.push({ text: '', image: '' }); changed(true); } }, '＋ 贴文'));
    rc.append(pb);
  } else if (r.type === 'guide') {
    rc.append(h('div', { class: 'help' }, '电话簿条目。把电话号码标成关键字（例如 [phoneAnna]555-0123[/phoneAnna]），玩家收集后就能在电话上拨打；拨打时的通话用事件「📞 开放拨打」设置。'),
      T('name', '名字'), T('address', '地址'), T('phone', '电话'));
  } else if (r.type === 'map') {
    rc.append(T('text', '地图标题'), imagePicker(r, 'image', ['newspapper/'], '地图图片'), fieldRow('标记位置（可留空）', h('input', { value: r.position || '', oninput: e => { r.position = e.target.value; changed(); } })));
  } else {
    rc.append(h('div', { class: 'help' }, '网页是自由排版：struct 里每个元素是背景图（image）或文字块（text、font、size、wrap、alignment、color）。pos 是位置，z 越小越前面。可用字体：blrrpixt、loxicaR、loxicaL、arpegius、tempesta、tempestaBold、blocktopia、western。'),
      T('url', '网址'), T('title', '网页标题'));
    const ta = h('textarea', { rows: 10 }); ta.value = JSON.stringify(r.struct || [], null, 1);
    rc.append(fieldRow('版面 struct（JSON）', ta, true), h('button', { class: 'small', onclick: () => { try { r.struct = parseLoose(ta.value); changed(); toast('已应用'); } catch (e) { toast('JSON 错误：' + e.message, true); } } }, '应用'));
  }
  return rc;
}
