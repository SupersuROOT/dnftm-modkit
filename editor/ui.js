/* DNFTM Mod Editor - user interface. */
'use strict';

const ui = { mod: -1, view: 'welcome', cage: null, tab: 'basic', scene: null, predef: null, dirty: false, issues: [] };

// ------------------------------------------------------------------ tiny DOM helper

function h(tag, props, ...kids) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(props || {})) {
    if (v === undefined || v === null || v === false) continue;
    if (k === 'class') el.className = v;
    else if (k === 'style') el.style.cssText = v;
    else if (k.startsWith('on')) el.addEventListener(k.slice(2), v);
    else if (k === 'value') el.value = v;
    else if (k === 'checked') el.checked = !!v;
    else if (k === 'html') el.innerHTML = v;
    else el.setAttribute(k, v === true ? '' : v);
  }
  for (const c of kids.flat(Infinity)) if (c !== null && c !== undefined && c !== false) el.append(c instanceof Node ? c : document.createTextNode(String(c)));
  return el;
}
const $ = sel => document.querySelector(sel);

function toast(msg, isErr) {
  const s = $('#status');
  s.textContent = msg;
  s.style.color = isErr ? 'var(--err)' : 'var(--ok)';
  clearTimeout(toast.t);
  toast.t = setTimeout(updateStatus, 6000);
}

function updateStatus() {
  const s = $('#status');
  s.style.color = '';
  if (!project.mods.length && !project.dir) { s.textContent = '尚未打开文件夹'; return; }
  const where = project.dir ? '文件夹：' + project.dir.name : project.readOnly ? '唯读导入（请用「导出 zip」）' : '尚未选择保存位置';
  s.textContent = where + (ui.dirty ? ' · 有未保存的变更' : ' · 已保存');
}

let validateTimer = null;
function changed(structural) {
  ui.dirty = true;
  updateStatus();
  if (structural) render();
  clearTimeout(validateTimer);
  validateTimer = setTimeout(() => {
    ui.issues = validateAll(); renderIssues(); renderSidebar();
    document.querySelectorAll('.livepreview').forEach(p => p.refresh && p.refresh());
  }, 250);
}

// ------------------------------------------------------------------ modal

function modal(title, body, buttons) {
  const back = h('div', { class: 'modal-back' });
  const close = () => back.remove();
  const box = h('div', { class: 'modal' }, h('h2', {}, title), body,
    h('div', { class: 'actions' }, (buttons || [{ label: '关闭' }]).map(b =>
      h('button', { class: b.primary ? 'primary' : '', onclick: () => { if (b.onClick && b.onClick() === false) return; close(); } }, b.label))));
  back.append(box);
  back.addEventListener('mousedown', e => { if (e.target === back) close(); });
  document.body.append(back);
  return close;
}

// ------------------------------------------------------------------ top level render

function render() {
  renderSidebar();
  renderMain();
  renderIssues();
  updateStatus();
}

function badgeFor(filter) {
  const list = ui.issues.filter(filter);
  const e = list.filter(i => i.level === 'err').length, w = list.filter(i => i.level === 'warn').length;
  if (e) return h('span', { class: 'badge err' }, e);
  if (w) return h('span', { class: 'badge warn' }, w);
  return null;
}

function renderSidebar() {
  const sb = $('#sidebar');
  sb.innerHTML = '';
  const tree = h('div', { class: 'tree' });
  if (!project.mods.length) tree.append(h('div', { class: 'muted', style: 'padding:8px' }, '还没有 mod。用上方按钮打开 Mods 文件夹，或添加一个 mod。'));
  project.mods.forEach((mod, mi) => {
    const m = h('div', { class: 'mod' });
    m.append(h('div', { class: 'item modname' + (ui.view === 'mod' && ui.mod === mi ? ' sel' : ''), onclick: () => nav({ mod: mi, view: 'mod' }) },
      h('span', {}, '📦 ' + mod.folder), badgeFor(i => i.nav && i.nav.mod === mi)));
    const sub = h('div', { class: 'sub' });
    for (const id of modCages(mod)) {
      sub.append(h('div', { class: 'item' + (ui.view === 'cage' && ui.mod === mi && ui.cage === id ? ' sel' : ''), onclick: () => nav({ mod: mi, cage: id, tab: ui.cage === id ? ui.tab : 'basic' }) },
        h('span', {}, '🐒 ' + id), badgeFor(i => i.nav && i.nav.mod === mi && i.nav.cage === id)));
    }
    sub.append(h('div', { class: 'item muted', onclick: () => newCageWizard(mi) }, '＋ 添加笼子'));
    m.append(sub);
    tree.append(m);
  });
  sb.append(tree);
}

function nav(n) {
  if (n.mod !== undefined) ui.mod = n.mod;
  if (n.cage) { ui.view = 'cage'; ui.cage = n.cage; ui.tab = n.tab || 'basic'; }
  else if (n.view) ui.view = n.view;
  else if (n.mod !== undefined) ui.view = 'mod';
  if (n.tab && !n.cage) ui.tab = n.tab;
  if (n.tab === 'mod') ui.view = 'mod';
  if (n.scene) ui.scene = n.scene;
  if (n.isec) ui.isec = n.isec;
  render();
}

function renderIssues() {
  const box = $('#issues');
  box.innerHTML = '';
  const errs = ui.issues.filter(i => i.level === 'err').length, warns = ui.issues.filter(i => i.level === 'warn').length;
  box.append(h('h3', { style: 'margin-top:0' }, `检查结果　❌ ${errs}　⚠️ ${warns}`));
  if (!ui.issues.length) box.append(h('div', { class: 'muted' }, project.mods.length ? '没有发现问题 👍' : '打开 mod 后会在这里即时检查。'));
  const order = { err: 0, warn: 1, info: 2 };
  for (const i of [...ui.issues].sort((a, b) => order[a.level] - order[b.level]))
    box.append(h('div', { class: 'issue ' + i.level, onclick: () => i.nav && nav(i.nav) },
      (i.level === 'err' ? '❌ ' : i.level === 'warn' ? '⚠️ ' : 'ℹ️ ') + i.msg, h('span', { class: 'where' }, i.where || '')));
}

function renderMain() {
  const main = $('#main');
  main.innerHTML = '';
  const mod = project.mods[ui.mod];
  if (ui.view === 'welcome' || !mod) { main.append(welcomeView()); return; }
  if (ui.view === 'mod') { main.append(modView(mod)); return; }
  if (!cageData(mod, ui.cage)) { ui.view = 'mod'; main.append(modView(mod)); return; }
  main.append(cageView(mod, ui.cage));
}

// ------------------------------------------------------------------ welcome

function welcomeView() {
  const fsOk = 'showDirectoryPicker' in window;
  return h('div', { class: 'welcome' },
    h('h2', {}, 'Do Not Feed the Monkeys — Mod 编辑器 v0.5.0'),
    h('div', { class: 'muted' }, '支持 ModLoader ' + LOADER_LATEST + ' 的全部功能'),
    CAT.noPreviews ? h('div', { class: 'help' }, '这个版本的编辑器不含游戏画面（场景预览图是游戏本身的美术，不能公开散布）。编辑功能都能用，只是挑场景时看不到画面。',
      '有游戏的话，可以照 Editor 文件夹里「README_從遊戲提取預覽圖.txt」的步骤，从你自己的游戏重新产生完整的 catalog.js。') : null,
    h('p', {}, '用来制作新笼子（监视摄影机）的可视化编辑器。编辑完的文件放进游戏的 Mods 文件夹，搭配 DNFTM Mod 安装器即可在游戏里游玩。'),
    h('ol', {},
      h('li', {}, '按「打开文件夹」，选择游戏文件夹（dnftm.exe 所在处）或其中的 Mods 文件夹。', fsOk ? '' : h('b', { style: 'color:var(--warn)' }, '（你的浏览器不支持直接写入，请用 Chrome 或 Edge；或用「导入」+「导出 zip」。）')),
      h('li', {}, '在左侧选择 mod，或按「＋ 添加笼子」用精灵创建一个新笼子。'),
      h('li', {}, '在「剧情」分页编排每个场景的动作；在「文本」分页填英文与简体中文。'),
      h('li', {}, '右侧「检查结果」会即时列出会让游戏出错的问题，全部 ❌ 清除后再保存。'),
      h('li', {}, '按「保存」写回文件夹。'),
      h('li', {}, '启动游戏，在主菜单笔记本上点「模组」，勾选你的模组，再开始新游戏。没有勾选任何模组时就是原版游戏；继续游戏会自动使用存档当时的模组。')),
    h('div', { class: 'row', style: 'margin-top:16px' },
      fsOk ? h('button', { class: 'primary', onclick: doOpen }, '📂 打开文件夹') : null,
      h('button', { onclick: () => $('#importInput').click() }, '📥 导入（唯读）'),
      h('button', { onclick: doNewMod }, '＋ 添加 Mod'),
      h('button', { onclick: () => loadExample(0) }, '📖 范例：夜读者（用内置场景）'),
      h('button', { onclick: () => loadExample(1) }, '👻 范例：幽灵房间（自订素材）')),
    h('div', { class: 'help' },
      '小提示：游戏的中文本型只有简体字（约 2600 字）。编辑器会标出画不出来的字，并可一键把繁体转成简体。',
      h('br'), '座标系统：每个镜头画面是 252×174 像素，x 从左到右、y 从下往上。在动作的「📍」按钮可以直接在画面上点击位置。'));
}

async function doOpen() {
  try {
    if (ui.dirty && !confirm('有未保存的变更，确定要打开其他文件夹吗？')) return;
    await openFolderRW();
    ui.dirty = false; ui.mod = project.mods.length ? 0 : -1; ui.view = project.mods.length ? 'mod' : 'welcome';
    ui.issues = validateAll();
    render();
    toast(`已打开 ${project.dir.name}，共 ${project.mods.length} 个 mod`);
  } catch (e) { if (e.name !== 'AbortError') toast(e.message, true); }
}

async function doImport(files) {
  try {
    await importFromFileList(files);
    ui.dirty = false; ui.mod = project.mods.length ? 0 : -1; ui.view = project.mods.length ? 'mod' : 'welcome';
    ui.issues = validateAll(); render();
    toast(`已导入 ${project.mods.length} 个 mod（唯读，请用导出 zip 保存）`);
  } catch (e) { toast(e.message, true); }
}

async function doSave() {
  try {
    if (!project.dir) {
      if ('showDirectoryPicker' in window && confirm('还没有选择要写入的 Mods 文件夹。要现在选择吗？（选「取消」改为导出 zip）')) {
        const keep = project.mods;
        await openFolderRW();
        // keep the in-memory mods, merging with what is on disk by folder name
        for (const m of keep) { const i = project.mods.findIndex(x => x.folder === m.folder); if (i >= 0) project.mods[i] = m; else project.mods.push(m); }
      } else { exportZip(project.mods); return; }
    }
    const errs = ui.issues.filter(i => i.level === 'err').length;
    if (errs && !confirm(`还有 ${errs} 个错误，游戏可能会出问题。仍要保存吗？`)) return;
    await saveToFolder();
    ui.dirty = false; render();
    toast('已保存到 ' + project.dir.name);
  } catch (e) { if (e.name !== 'AbortError') toast(e.message, true); }
}

function doNewMod() {
  const input = h('input', { value: 'MyMod', style: 'width:100%' });
  modal('添加 Mod', h('div', {}, h('label', {}, '文件夹名称（英文、数字、底线）'), input), [
    { label: '取消' },
    { label: '创建', primary: true, onClick: () => {
      const name = input.value.trim();
      if (!/^[A-Za-z0-9_-]+$/.test(name)) { alert('只能使用英文、数字、底线和减号'); return false; }
      if (project.mods.some(m => m.folder.toLowerCase() === name.toLowerCase())) { alert('已经有同名的 mod'); return false; }
      project.mods.push(newMod(name));
      ui.mod = project.mods.length - 1; ui.view = 'mod';
      changed(true);
    } }]);
}

function loadExample(index) {
  const ex = (window.DNFTM_EXAMPLES || [])[index || 0];
  if (!ex) { toast('找不到范例数据', true); return; }
  const mod = newMod(ex.folder);
  mod.manifest = clone(ex.manifest); ensureManifestArrays(mod.manifest);
  mod.files = clone(ex.files); mod.merges = clone(ex.merges);
  for (const [p, b64] of Object.entries(ex.assets || {})) mod.assets[p] = Uint8Array.from(atob(b64), c => c.charCodeAt(0));
  let folder = ex.folder, n = 2;
  while (project.mods.some(m => m.folder === folder)) folder = ex.folder + n++;
  mod.folder = folder;
  project.mods.push(mod);
  ui.mod = project.mods.length - 1; ui.view = 'cage'; ui.cage = modCages(mod)[0]; ui.tab = Object.keys(ex.assets || {}).length ? 'art' : 'scenes';
  changed(true);
}

// ------------------------------------------------------------------ mod settings view

function modView(mod) {
  const M = mod.manifest;
  const wrap = h('div', {});
  wrap.append(h('h2', {}, '📦 ' + mod.folder));
  wrap.append(h('div', { class: 'row' },
    h('div', { class: 'field' }, h('label', {}, 'Mod 显示名称'), h('input', { value: M.name || '', style: 'width:360px', oninput: e => { M.name = e.target.value; changed(); } })),
    h('button', { onclick: () => newCageWizard(ui.mod) }, '＋ 添加笼子'),
    h('button', { onclick: () => exportZip([mod]) }, '⬇ 导出这个 mod 的 zip')));
  const needs = loaderNeeds(mod), need = requiredLoader(mod);
  wrap.append(h('div', { class: 'row' },
    h('div', { class: 'field' }, lbl('最低 ModLoader 版本（minLoader）', 'minLoader'),
      h('input', { value: M.minLoader || '', placeholder: need, style: 'width:120px', oninput: e => { if (e.target.value.trim()) M.minLoader = e.target.value.trim(); else delete M.minLoader; changed(); } })),
    h('div', { class: 'muted' }, `用到的功能需要 ${need}（最新版 ${LOADER_LATEST}）：` + [...new Set(needs.filter(n => n[0] === need).map(n => n[1]))].join('、') + '。保存时会自动调高。')));

  wrap.append(h('h3', {}, '笼子'));
  wrap.append(h('div', { class: 'help' }, '「插入位置」决定新笼子在摄影机购买顺序中的位置：0 = 开局就有的第一台摄影机；数字越大越晚才能买到。游戏开局会给 4 台。'));
  const cages = M.cages;
  if (!cages.length) wrap.append(h('div', { class: 'muted' }, '还没有笼子。'));
  cages.forEach(c => wrap.append(h('div', { class: 'card row' },
    h('b', { style: 'width:160px' }, '🐒 ' + c.id),
    h('label', {}, '插入位置'), h('input', { type: 'number', min: 0, value: c.insertAt || 0, oninput: e => { c.insertAt = +e.target.value || 0; changed(); } }),
    h('button', { onclick: () => nav({ mod: ui.mod, cage: c.id, tab: 'basic' }) }, '编辑'),
    h('button', { class: 'danger', onclick: () => { if (confirm(`删除笼子「${c.id}」与它的所有文本？`)) { deleteCage(mod, c.id); changed(true); } } }, '删除'))));

  wrap.append(h('h3', {}, '高端：mod.json'));
  wrap.append(h('div', { class: 'help' }, 'sceneTemplates（场景模板）、cameraEffects（摄影机特效）、diaryPages（笔记本页）通常由各笼子的分页自动维护。直接修改 JSON 后按「套用」。'));
  const ta = h('textarea', { rows: 18 });
  ta.value = pretty(M);
  wrap.append(ta, h('div', { class: 'row', style: 'margin-top:6px' }, h('button', { onclick: () => {
    try { const v = parseLoose(ta.value); ensureManifestArrays(v); mod.manifest = v; changed(true); toast('已套用 mod.json'); }
    catch (e) { toast('JSON 错误：' + e.message, true); }
  } }, '套用')));
  return wrap;
}

// ------------------------------------------------------------------ new cage wizard

function newCageWizard(mi) {
  const mod = project.mods[mi];
  const st = { id: '', template: '3', cameras: 1, effect: '', diary: '' };
  const pickDefaults = () => {
    const used = cagesUsingTemplate(st.template);
    st.effect = used.find(c => CAT.effects.includes(c)) || '';
    st.diary = used.find(c => DIARY_BY_ID[c]) || st.diary || CAT.diaryPages[0].id;
    st.cameras = Math.min(st.cameras, TEMPLATE_BY_ID[st.template].cameras.length) || 1;
  };
  pickDefaults();
  const body = h('div', { style: 'width:min(1100px,88vw)' });
  const draw = () => {
    body.innerHTML = '';
    const tpl = TEMPLATE_BY_ID[st.template];
    body.append(h('div', { class: 'row' },
      h('div', { class: 'field' }, lbl('笼子 id（英文字母开头，只用英文和数字）', 'cageId'),
        h('input', { value: st.id, placeholder: 'myCage', oninput: e => { st.id = e.target.value.trim(); } })),
      h('div', { class: 'field' }, lbl('镜头数', 'cameras'),
        h('select', { onchange: e => { st.cameras = +e.target.value; } }, tpl.cameras.map((c, i) => h('option', { value: i + 1, selected: st.cameras === i + 1 }, (i + 1) + ' 个')))),
      h('div', { class: 'field' }, lbl('摄像头画面风格', 'cameraEffect'),
        h('select', { onchange: e => { st.effect = e.target.value; } },
          h('option', { value: '' }, '随机（可能是黑白）'), CAT.effects.map(e => h('option', { value: e, selected: st.effect === e }, '同 ' + e))), note('cameraEffectShort')),
      h('div', { class: 'field' }, lbl('笔记本页版型（拷贝自）', 'diaryTemplate'),
        h('select', { onchange: e => { st.diary = e.target.value; } }, CAT.diaryPages.map(p => h('option', { value: p.id, selected: st.diary === p.id },
          p.id + `（${p.children.filter(c => c.kind === 'word').length} 个字段）`))))));
    body.append(h('div', { class: 'help' }, '选择场景模板：新笼子会拷贝这个场景（背景与角色）。目前的美术都来自游戏内置笼子，之后可替换成自己的美术。'));
    const grid = h('div', { class: 'grid' });
    for (const t of USABLE_TEMPLATES) {
      const used = cagesUsingTemplate(t.id);
      const chars = t.cameras[0].objects.filter(o => o.anims && o.depth === 0).length;
      grid.append(h('div', { class: 'tpl' + (st.template === t.id ? ' sel' : ''), onclick: () => { st.template = t.id; pickDefaults(); draw(); } },
        h('img', { src: previewSrc(t.cameras[0].full), loading: 'lazy' }),
        h('div', { class: 'cap' }, h('b', {}, 'Story' + t.id), ` · ${t.cameras.length} 镜头 · ${chars} 个可动角色`, h('br'),
          h('span', { class: 'muted' }, used.length ? '原用于：' + used.join(', ') : '（未被使用）'))));
    }
    body.append(grid);
  };
  draw();
  modal('添加笼子', body, [{ label: '取消' }, { label: '创建', primary: true, onClick: () => {
    if (!/^[A-Za-z][A-Za-z0-9]*$/.test(st.id)) { alert('笼子 id 必须以英文字母开头，只能用英文字母和数字。'); return false; }
    if (BUILTIN_CAGES.has(st.id.toLowerCase()) || project.mods.some(m => m.manifest.cages.some(c => c.id.toLowerCase() === st.id.toLowerCase()))) { alert('这个 id 已经被使用。'); return false; }
    scaffoldCage(mod, { id: st.id, templateId: st.template, cameras: st.cameras, effectFrom: st.effect, diaryFrom: st.diary });
    ui.mod = mi; ui.view = 'cage'; ui.cage = st.id; ui.tab = 'basic'; ui.scene = 'day1';
    changed(true);
  } }]);
}

// ------------------------------------------------------------------ cage view

const CAGE_TABS = [['basic', '基本信息'], ['art', '素材'], ['scenes', '剧情'], ['predef', '预设动作'], ['keywords', '关键字'], ['diary', '笔记本'], ['interact', '互动'], ['strings', '文本'], ['raw', '原始 JSON']];

function cageView(mod, id) {
  const wrap = h('div', {});
  wrap.append(h('h2', {}, '🐒 ' + id, h('span', { class: 'muted', style: 'font-size:13px;margin-left:10px' }, mod.folder)));
  const tabs = h('div', { class: 'tabs' }, CAGE_TABS.map(([k, label]) => h('button', { class: ui.tab === k ? 'sel' : '', onclick: () => { ui.tab = k; renderMain(); } },
    label, ' ', badgeFor(i => i.nav && i.nav.mod === ui.mod && i.nav.cage === id && i.nav.tab === k))));
  wrap.append(tabs);
  const d = cageData(mod, id);
  const body = { basic: basicTab, art: artTab, scenes: scenesTab, predef: predefTab, keywords: keywordsTab, diary: diaryTab, interact: interactTab, strings: stringsTab, raw: rawTab }[ui.tab] || basicTab;
  wrap.append(body(mod, id, d));
  return wrap;
}

function cameraPreview(cam, scale, extra) {
  if (cam.artDef) return cameraCanvas(cam, scale, extra);
  const W = CAT.view.w, H = CAT.view.h;
  const box = h('div', { class: 'preview', style: `width:${W * scale}px;height:${H * scale}px` });
  box.append(h('img', { src: previewSrc(cam.full), width: W * scale, height: H * scale, draggable: 'false' }));
  for (const o of cam.objects) {
    if (o.depth !== 0 || !(o.anims || o.clickable)) continue;
    if (o.x < 0 || o.x > W || o.y < 0 || o.y > H) continue;
    box.append(h('div', { class: 'mk ' + (o.anims ? 'anim' : 'click'), style: `left:${o.x * scale}px;top:${(H - o.y) * scale}px` }, o.name));
  }
  if (extra) extra(box, scale);
  return box;
}

function basicTab(mod, id, d) {
  const M = mod.manifest;
  const md = d.metadata, smd = d.script.metadata;
  const tpl = resolveTemplate(mod, md.tmpContainer);
  const own = M.sceneTemplates.find(t => t.id === md.tmpContainer);
  const wrap = h('div', {});
  const cage = M.cages.find(c => c.id === id) || {};
  wrap.append(h('div', { class: 'row' },
    h('div', { class: 'field' }, lbl('难度', 'difficulty'), h('input', { type: 'number', value: md.difficulty ?? 30, oninput: e => { md.difficulty = +e.target.value; changed(); } })),
    h('div', { class: 'field' }, lbl('趣味度', 'interest'), h('input', { type: 'number', value: md.interest ?? 50, oninput: e => { md.interest = +e.target.value; changed(); } })),
    h('div', { class: 'field' }, lbl('购买顺序插入位置', 'insertAt'), h('input', { type: 'number', min: 0, value: cage.insertAt || 0, oninput: e => { cage.insertAt = +e.target.value || 0; changed(); } })),
    h('div', { class: 'field' }, lbl('起始场景', 'startScene'), h('select', { onchange: e => { smd.startScene = e.target.value; changed(); } },
      Object.keys(d.script.scenes).map(s => h('option', { value: s, selected: smd.startScene === s }, s)))),
    h('div', { class: 'field' }, lbl('摄像头画面风格', 'cameraEffect'), h('select', { onchange: e => {
      M.cameraEffects = M.cameraEffects.filter(x => x.story !== id);
      if (e.target.value) M.cameraEffects.push({ story: id, cloneFrom: e.target.value });
      changed();
    } }, h('option', { value: '' }, '随机'), CAT.effects.map(x => h('option', { value: x, selected: (M.cameraEffects.find(c => c.story === id) || {}).cloneFrom === x }, '同 ' + x))), note('cameraEffectShort'))));

  wrap.append(h('h3', {}, '场景模板'));
  if (!tpl) { wrap.append(h('div', { class: 'help' }, '找不到模板「' + md.tmpContainer + '」。')); return wrap; }
  wrap.append(h('div', { class: 'help' }, `使用 Story${tpl.base.id} 的场景` + (own ? `（衍生模板 Story${own.id}）` : '') +
    `。镜头数必须等于模板的镜头数，否则游戏存盘会出错；调整下方「镜头数」会同时更新两者。`));
  wrap.append(h('div', { class: 'row' },
    lbl('镜头数', 'cameras'),
    h('select', { disabled: !own, onchange: e => {
      const n = +e.target.value;
      own.keepCameras = n; smd.cameras = n;
      for (let c = 2; c <= 4; c++) { if (c > n) delete smd['startScene' + c]; }
      changed(true);
    } }, tpl.base.cameras.map((c, i) => h('option', { value: i + 1, selected: tpl.cameras.length === i + 1 }, i + 1))),
    own ? h('button', { onclick: () => changeTemplate(mod, id) }, '更换场景模板…') : h('span', { class: 'muted' }, '（直接使用内置模板，无法调整）')));
  tpl.cameras.forEach((cam, ci) => {
    wrap.append(h('div', { class: 'card' }, h('b', {}, `镜头 ${ci + 1}`),
      ci > 0 ? h('span', { class: 'muted' }, `　起始场景：`, h('select', { onchange: e => { smd['startScene' + (ci + 1)] = e.target.value; changed(); } },
        h('option', { value: '' }, '（无）'), Object.keys(d.script.scenes).map(s => h('option', { value: s, selected: smd['startScene' + (ci + 1)] === s }, s)))) : null,
      h('div', { class: 'row', style: 'align-items:flex-start;margin-top:6px' }, cameraPreview(cam, 2),
        h('div', { style: 'flex:1;min-width:260px;max-height:360px;overflow:auto' },
          h('table', { class: 'strings' }, h('tr', {}, h('th', {}, '对象'), h('th', {}, '动画'), h('th', {}, '位置')),
            cam.objects.filter(o => o.depth === 0).map(o => h('tr', {},
              h('td', { class: 'mono' }, o.name, o.clickable ? ' 🔍' : '', o.active ? '' : h('span', { class: 'muted' }, ' (默认隐藏)')),
              h('td', { class: 'muted', style: 'font-size:12px' }, (o.anims || []).join(', ')),
              h('td', { class: 'muted mono', style: 'font-size:11px' }, `${o.x},${o.y}`))))))));
  });
  wrap.append(h('div', { class: 'help' }, '🔍 = 可点击的对象（玩家点了会取得关键字的那种）。标黄字的是有动画的角色。'));
  return wrap;
}

function changeTemplate(mod, id) {
  const d = cageData(mod, id);
  const own = mod.manifest.sceneTemplates.find(t => t.id === d.metadata.tmpContainer);
  let sel = own.cloneFrom;
  const grid = h('div', { class: 'grid', style: 'width:min(1000px,85vw)' });
  const draw = () => {
    grid.innerHTML = '';
    for (const t of USABLE_TEMPLATES) grid.append(h('div', { class: 'tpl' + (sel === t.id ? ' sel' : ''), onclick: () => { sel = t.id; draw(); } },
      h('img', { src: previewSrc(t.cameras[0].full), loading: 'lazy' }), h('div', { class: 'cap' }, 'Story' + t.id + ' · ' + t.cameras.length + ' 镜头')));
  };
  draw();
  modal('更换场景模板', h('div', {}, h('div', { class: 'help' }, '更换后，剧情中引用的对象名称可能不存在，检查结果会列出需要修改的动作。'), grid), [
    { label: '取消' }, { label: '更换', primary: true, onClick: () => {
      own.cloneFrom = sel;
      const n = Math.min(own.keepCameras || 1, TEMPLATE_BY_ID[sel].cameras.length);
      own.keepCameras = n; d.script.metadata.cameras = n;
      changed(true);
    } }]);
}

// ------------------------------------------------------------------ text reference widget

function textRef(mod, section, get, set, opts) {
  opts = opts || {};
  const raw = get();
  const ref = parseRef(raw);
  const box = h('div', { class: 'textref' });
  const warnLine = h('div', {});
  const updateWarn = zh => {
    warnLine.innerHTML = '';
    const bad = missingGlyphs(zh), tw = traditionalChars(zh);
    if (tw.length) warnLine.append(h('div', { class: 'tw' }, `含繁体字：${tw.join('')} `, h('button', { class: 'small', onclick: () => {
      const s = toSimplified(zhInput.value); zhInput.value = s; applyZh(s);
    } }, '繁→简')));
    if (bad.length) warnLine.append(h('div', { class: 'bad' }, `游戏字体画不出来：${bad.join(' ')}（请换字）`));
  };
  let zhInput;
  const applyZh = v => {
    const r = parseRef(get());
    if (r) setLoc(mod, 'ch', r.section, r.num, v);
    else set(newRef(mod, section, '', v));
    updateWarn(v); changed();
  };
  if (raw && !ref) {
    // Literal (non-translated) text.
    box.append(h('span', { class: 'key' }, '纯文本'), h('div', { class: 'row', style: 'margin:0' },
      h('input', { value: raw, style: 'flex:1', oninput: e => { set(e.target.value); changed(); } }),
      h('button', { class: 'small', onclick: () => { set(newRef(mod, section, raw, '')); changed(true); } }, '转成可翻译')));
    return box;
  }
  if (ref && ref.section !== section) {
    box.append(h('span', { class: 'key' }, ref.section + '_' + ref.num), h('div', {},
      h('span', { class: 'muted' }, '使用游戏原有文本：' + ref.fallback + ' '),
      h('button', { class: 'small', onclick: () => { set(newRef(mod, section, ref.fallback, '')); changed(true); } }, '改成自订文本')));
    return box;
  }
  const en = ref ? (getLoc(mod, 'en', ref.section, ref.num) || ref.fallback) : '';
  const zh = ref ? getLoc(mod, 'ch', ref.section, ref.num) : '';
  const tag = opts.multiline ? 'textarea' : 'input';
  box.append(h('span', { class: 'key' }, ref ? ref.section + '_' + ref.num : '（新文本）', h('br'), 'English'),
    h(tag, { value: en, rows: opts.multiline ? 2 : undefined, style: opts.multiline ? 'font-family:inherit;font-size:13px' : '', placeholder: opts.placeholder || '', oninput: e => {
      const v = e.target.value; const r = parseRef(get());
      if (r) { setLoc(mod, 'en', r.section, r.num, v); set(r.section + '_' + r.num + '~' + v); }
      else set(newRef(mod, section, v, ''));
      changed();
    } }));
  zhInput = h(tag, { value: zh, rows: opts.multiline ? 2 : undefined, style: opts.multiline ? 'font-family:inherit;font-size:13px' : '', placeholder: '简体中文', oninput: e => applyZh(e.target.value) });
  box.append(h('span', { class: 'key' }, '简体中文'), zhInput, h('span', {}), warnLine);
  updateWarn(zh);
  return box;
}

// ------------------------------------------------------------------ actions

const ACTIONS = {
  say:              { label: '💬 说话', fields: [['id', 'obj', '角色'], ['text', 'text', '对白'], ['subanimation', 'anim', '说话时动画'], ['endanimation', 'anim', '说完后动画']] },
  animation:        { label: '🎞 播放动画', fields: [['id', 'obj', '对象'], ['animation', 'anim', '动画'], ['waitFinish', 'bool', '等播完再继续']] },
  move:             { label: '🚶 移动', fields: [['id', 'obj', '对象'], ['position', 'pos', '目的地'], ['time', 'num', '秒数'], ['flip', 'dir', '面向'], ['subanimation', 'anim', '移动时动画'], ['endAnimation', 'anim', '到达后动画']] },
  setin:            { label: '📍 瞬间定位', fields: [['id', 'obj', '对象'], ['position', 'pos', '位置']] },
  enable:           { label: '👁 显示', fields: [['id', 'obj', '对象']] },
  disable:          { label: '🙈 隐藏', fields: [['id', 'obj', '对象']] },
  wait:             { label: '⏱ 等待', fields: [['time', 'num', '秒数'], ['id', 'obj', '队列对象']] },
  flip:             { label: '↔ 转向', fields: [['id', 'obj', '对象'], ['direction', 'dir', '方向']] },
  predefinedAction: { label: '📋 运行预设动作', fields: [['name', 'predef', '预设动作'], ['id', 'obj', '队列对象']] },
  setVar:           { label: '🏷 设置变量', fields: [['name', 'str', '变量名'], ['value', 'str', '值'], ['id', 'obj', '队列对象']] },
  blinkLed:         { label: '🔴 镜头灯闪烁', fields: [['id', 'obj', '队列对象']] },
  stopLed:          { label: '⚫ 停止闪烁', fields: [['id', 'obj', '队列对象']] },
  setz:             { label: '🧱 前后顺序', fields: [['id', 'obj', '对象'], ['z', 'num', 'z（越小越前）']] },
  setInternalVar:   { label: '🔧 内部变量', fields: [['id', 'obj', '对象'], ['value', 'str', '值']] },
  comment:          { label: '📝 注解', fields: [['text', 'str', '内容']] },
  triggerEvents:    { label: '⚡ 触发自订事件', fields: [['events', 'generic', '自订事件'], ['id', 'obj', '队列对象']] },
  setValidVideo:    { label: '🎥 标记可投稿', fields: [['id', 'obj', '队列对象'], ['night', 'bool', '需要夜视']] },
  unsetValidVideo:  { label: '🎥 取消可投稿', fields: [['id', 'obj', '队列对象']] },
};
const COMMON_KEYS = ['action', 'if', 'ifNot'];
const ACTION_HELP = {
  say: '角色说一句话（游戏里会显示对话泡泡）。对白中用 [关键字id]文字[/关键字id] 标出可点击的关键字。',
  animation: '播放物件的一段动画，例如坐下、拿书、唱歌。',
  move: '让物件花几秒走到目的地，途中播放「移动时动画」（通常是走路）。',
  setin: '瞬间把物件放到某个位置（不播放走路），常用来把角色放到画面外准备进场。',
  enable: '让物件出现。',
  disable: '让物件消失（隐藏）。开场场景常用它把模板原本的角色藏起来。',
  wait: '暂停一段时间（秒，游戏时间会随加速而缩短）。',
  flip: '让角色转身面向左或右。',
  predefinedAction: '执行一组在「预设动作」分页定义好的动作，适合重复使用的片段（例如「坐下看书」）。',
  setVar: '设置剧情变量，之后的动作可以用「条件 if / ifNot」判断。',
  blinkLed: '让这个笼子的摄像头指示灯闪烁，提醒玩家「有事发生，快来看」。通常放在场景开头。',
  stopLed: '停止摄像头指示灯闪烁。通常放在场景结尾。',
  setz: '调整物件的前后层次（谁挡住谁）。',
  setInternalVar: '设置物件的内部变量（进阶用法：原版用来切换角色的服装版本等）。',
  comment: '备注，游戏不会执行。',
  triggerEvents: '执行「互动 → 自订事件」里的一组事件（加钱、寄信、刊新闻……）。',
  setValidVideo: '从这里开始录到的影片算「有价值」，玩家投稿给 Shock.tv 时会用「互动 → 录像投稿」的 isValid 结果，直到「取消可投稿」。',
  unsetValidVideo: '结束「可投稿」的片段。',
};

function newAction(type, cam) {
  const firstChar = (cam && cam.objects.find(o => o.depth === 0 && o.anims)) || {};
  const a = { action: type };
  for (const [k, kind] of ACTIONS[type].fields) {
    if (kind === 'obj') a[k] = firstChar.name || '';
    if (kind === 'pos') a[k] = { x: 126, y: 20 };
    if (kind === 'num') a[k] = type === 'wait' ? 2 : type === 'move' ? 3 : 0;
    if (kind === 'bool') a[k] = true;
    if (kind === 'dir') a[k] = 'right';
  }
  if (type === 'say' && firstChar.anims) { a.subanimation = firstChar.anims.find(x => /habla/i.test(x)) || ''; a.endanimation = firstChar.anims.find(x => /quiet/i.test(x)) || ''; }
  return a;
}

/**
 * ctx = { mod, section, cams: [camera], camIndex: () => 0-based, predefNames: [], onPick }
 */
function actionList(list, ctx, depth) {
  depth = depth || 0;
  const box = h('div', {});
  const redraw = () => { box.replaceWith(actionList(list, ctx, depth)); };
  list.forEach((a, i) => box.append(actionItem(list, i, ctx, redraw, depth)));
  const addSel = h('select', {}, Object.entries(ACTIONS).map(([k, v]) => h('option', { value: k }, v.label)), h('option', { value: '__group' }, '⏩ 同时运行（群组）'));
  box.append(h('div', { class: 'row', style: 'margin-top:6px' }, addSel, h('button', { onclick: () => {
    const cam = ctx.cams[ctx.camIndex()];
    list.push(addSel.value === '__group' ? { actions: [] } : newAction(addSel.value, cam));
    changed(); redraw();
  } }, '＋ 添加动作')));
  return box;
}

function actionItem(list, i, ctx, redraw, depth) {
  const a = list[i];
  const isGroup = Array.isArray(a.actions) && !a.action;
  const type = isGroup ? 'group' : a.action;
  const def = ACTIONS[type];
  const cam = ctx.cams[ctx.camIndex()];
  const card = h('div', { class: 'action ' + type });
  const tools = h('div', { class: 'tools' },
    h('button', { class: 'small', title: '上移', onclick: () => { if (i > 0) { [list[i - 1], list[i]] = [list[i], list[i - 1]]; changed(); redraw(); } } }, '↑'),
    h('button', { class: 'small', title: '下移', onclick: () => { if (i < list.length - 1) { [list[i + 1], list[i]] = [list[i], list[i + 1]]; changed(); redraw(); } } }, '↓'),
    h('button', { class: 'small', title: '拷贝', onclick: () => { list.splice(i + 1, 0, clone(a)); changed(); redraw(); } }, '⧉'),
    h('button', { class: 'small danger', title: '删除', onclick: () => { list.splice(i, 1); changed(); redraw(); } }, '✕'));
  const typeSel = isGroup ? h('b', {}, '⏩ 同时运行（群组）') :
    h('select', { onchange: e => {
      const t = e.target.value;
      const keep = {}; for (const k of ['id', 'if', 'ifNot']) if (a[k] !== undefined) keep[k] = a[k];
      const fresh = newAction(t, cam);
      for (const k of Object.keys(a)) delete a[k];
      Object.assign(a, fresh, keep, { action: t });
      changed(); redraw();
    } }, Object.entries(ACTIONS).map(([k, v]) => h('option', { value: k, selected: k === type }, v.label)), def ? null : h('option', { value: type, selected: true }, '其他：' + type));
  card.append(h('div', { class: 'head' }, h('span', { class: 'num' }, (i + 1) + '.'), typeSel, summary(a, ctx), tools));
  const body = h('div', { class: 'body' });
  if (isGroup) {
    body.append(h('div', { class: 'inner' }, h('div', { class: 'muted', style: 'font-size:12px;margin-bottom:4px' }, '群组内的动作会同时开始（例如两个角色一起走）。'), actionList(a.actions, ctx, depth + 1)));
  } else if (def) {
    for (const [k, kind, label] of def.fields) body.append(field(a, k, kind, label, ctx, cam, redraw));
  }
  // Conditions and unknown keys.
  const known = new Set([...(def ? def.fields.map(f => f[0]) : []), ...COMMON_KEYS, 'actions']);
  const extras = Object.keys(a).filter(k => !known.has(k));
  const condBox = h('div', { class: 'row', style: 'width:100%;margin:0' },
    lbl('条件 if', 'cond'), h('input', { value: a.if || '', placeholder: '变量A,变量B', style: 'width:150px', oninput: e => { if (e.target.value) a.if = e.target.value; else delete a.if; changed(); } }),
    h('label', {}, 'ifNot'), h('input', { value: a.ifNot || '', placeholder: '变量', style: 'width:150px', oninput: e => { if (e.target.value) a.ifNot = e.target.value; else delete a.ifNot; changed(); } }));
  const hasCond = a.if || a.ifNot;
  const more = h('details', { style: 'width:100%' }, h('summary', { class: 'muted', style: 'font-size:12px;cursor:pointer' }, '条件与其他字段' + (hasCond ? '（有条件）' : '') + (extras.length ? `（${extras.join(', ')}）` : '')));
  if (hasCond || extras.length) more.open = !!hasCond;
  more.append(condBox);
  if (!isGroup) {
    const extraObj = {}; for (const k of extras) extraObj[k] = a[k];
    const ta = h('textarea', { rows: Math.min(8, 2 + extras.length) });
    ta.value = JSON.stringify(extraObj, null, 1);
    more.append(h('div', { style: 'width:100%' }, h('label', {}, '其他字段（JSON）'), ta, h('button', { class: 'small', onclick: () => {
      try { const v = parseLoose(ta.value); for (const k of extras) delete a[k]; Object.assign(a, v); changed(); redraw(); }
      catch (e) { toast('JSON 错误：' + e.message, true); }
    } }, '套用')));
  }
  body.append(more);
  if (ACTION_HELP[type]) body.append(h('div', { class: 'muted', style: 'font-size:12px;width:100%' }, 'ℹ️ ' + ACTION_HELP[type]));
  card.append(body);
  return card;
}

function summary(a, ctx) {
  if (a.action === 'say') {
    const r = parseRef(a.text);
    const t = r ? (getLoc(ctx.mod, 'ch', r.section, r.num) || getLoc(ctx.mod, 'en', r.section, r.num) || r.fallback) : a.text || '';
    return h('span', { class: 'muted', style: 'font-size:12px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:420px' }, (a.id || '') + '：' + stripMarkup(t));
  }
  return h('span', { class: 'muted', style: 'font-size:12px' }, a.id ? a.id : '');
}

function field(a, k, kind, label, ctx, cam, redraw) {
  const wrap = h('div', { class: 'field', style: kind === 'text' ? 'width:100%' : '' }, lbl(label, 'act.' + k));
  const objs = cam ? cam.objects : [];
  if (kind === 'obj') {
    const sel = h('select', { onchange: e => { if (e.target.value) a[k] = e.target.value; else delete a[k]; changed(); redraw(); } });
    sel.append(h('option', { value: '' }, '（无）'));
    const names = new Set();
    for (const o of objs) {
      if (o.depth > 1) continue;
      names.add(o.name);
      sel.append(h('option', { value: o.name, selected: a[k] === o.name }, (o.depth ? '　' : '') + o.name + (o.anims ? ' 🎞' : '') + (o.clickable ? ' 🔍' : '')));
    }
    if (a[k] && !names.has(a[k])) sel.append(h('option', { value: a[k], selected: true }, a[k] + '（不在模板中）'));
    wrap.append(sel);
  } else if (kind === 'anim') {
    const obj = objs.find(o => o.name === a.id);
    const listId = 'anims-' + Math.random().toString(36).slice(2);
    wrap.append(h('input', { value: a[k] || '', list: listId, style: 'width:150px', oninput: e => { if (e.target.value) a[k] = e.target.value; else delete a[k]; changed(); } }),
      h('datalist', { id: listId }, ((obj && obj.anims) || []).map(n => h('option', { value: n }))));
  } else if (kind === 'text') {
    wrap.append(textRef(ctx.mod, ctx.section, () => a[k], v => { a[k] = v; }, { multiline: true }));
    const kws = Object.keys(cageData(ctx.mod, ctx.section).keywords || {}).filter(x => !x.includes(',') && !x.includes('_'));
    if (kws.length) wrap.append(h('div', { class: 'muted', style: 'font-size:11px' }, '可用关键字标记：' + kws.map(x => `[${x}]…[/${x}]`).join('　')));
  } else if (kind === 'num') {
    wrap.append(h('input', { type: 'number', step: 'any', value: a[k] ?? '', oninput: e => { if (e.target.value === '') delete a[k]; else a[k] = +e.target.value; changed(); } }));
  } else if (kind === 'str') {
    wrap.append(h('input', { value: a[k] ?? '', style: 'width:160px', oninput: e => { a[k] = e.target.value; changed(); } }));
  } else if (kind === 'bool') {
    wrap.append(h('input', { type: 'checkbox', checked: !!a[k], onchange: e => { a[k] = e.target.checked; changed(); } }));
  } else if (kind === 'dir') {
    wrap.append(h('select', { onchange: e => { if (e.target.value) a[k] = e.target.value; else delete a[k]; changed(); } },
      h('option', { value: '' }, '（不变）'), h('option', { value: 'left', selected: a[k] === 'left' }, '← 左'), h('option', { value: 'right', selected: a[k] === 'right' }, '→ 右')));
  } else if (kind === 'generic') {
    const names = Object.keys(cageData(ctx.mod, ctx.section).genericEvents || {});
    wrap.append(h('select', { onchange: e => { a[k] = e.target.value; changed(); } }, h('option', { value: '' }, '（选择）'),
      names.map(n => h('option', { value: n, selected: a[k] === n }, n)), a[k] && !names.includes(a[k]) ? h('option', { value: a[k], selected: true }, a[k] + '（不存在）') : null));
  } else if (kind === 'predef') {
    wrap.append(h('select', { onchange: e => { a[k] = e.target.value; changed(); } },
      h('option', { value: '' }, '（选择）'), ctx.predefNames.map(n => h('option', { value: n, selected: a[k] === n }, n)),
      a[k] && !ctx.predefNames.includes(a[k]) ? h('option', { value: a[k], selected: true }, a[k] + '（不存在）') : null));
  } else if (kind === 'pos') {
    const p = a[k] = a[k] || { x: 126, y: 20 };
    const xi = h('input', { type: 'number', step: 'any', value: p.x, oninput: e => { p.x = +e.target.value; changed(); } });
    const yi = h('input', { type: 'number', step: 'any', value: p.y, oninput: e => { p.y = +e.target.value; changed(); } });
    wrap.append(h('div', { class: 'row', style: 'margin:0' }, 'x', xi, 'y', yi,
      h('button', { class: 'small', disabled: !cam, onclick: () => pickPosition(cam, p, a.id, () => { xi.value = p.x; yi.value = p.y; changed(); }) }, '📍 在画面上选')));
  }
  return wrap;
}

function pickPosition(cam, p, objName, done) {
  const scale = 3, H = CAT.view.h;
  let cur = { x: p.x, y: p.y };
  const info = h('div', { class: 'muted' });
  const marker = h('div', { class: 'pick' });
  const place = () => { marker.style.left = cur.x * scale + 'px'; marker.style.top = (H - cur.y) * scale + 'px'; info.textContent = `x = ${cur.x}, y = ${cur.y}（画面外的值请直接输入，例如 -40 代表从左边画面外）`; };
  const prev = cameraPreview(cam, scale, box => box.append(marker));
  prev.style.cursor = 'crosshair';
  prev.addEventListener('click', e => {
    const r = prev.getBoundingClientRect();
    cur = { x: Math.round((e.clientX - r.left) / scale), y: Math.round(H - (e.clientY - r.top) / scale) };
    place();
  });
  place();
  const o = objName && cam.objects.find(x => x.name === objName);
  modal('选择位置' + (objName ? '：' + objName : ''), h('div', {},
    h('div', { class: 'help' }, '点画面选择角色脚底（或对象锚点）要到的位置。', o ? ` ${objName} 在模板中的默认位置是 (${o.x}, ${o.y})。` : ''), prev, info),
    [{ label: '取消' }, { label: '确定', primary: true, onClick: () => { p.x = cur.x; p.y = cur.y; done(); } }]);
}

// ------------------------------------------------------------------ scenes tab

function sceneOrder(d) {
  const scenes = d.script.scenes, smd = d.script.metadata;
  const order = [], seen = new Set();
  const starts = [smd.startScene, smd.startScene2, smd.startScene3, smd.startScene4].filter(Boolean);
  for (const s of starts) { let cur = s; while (cur && scenes[cur] && !seen.has(cur)) { seen.add(cur); order.push(cur); cur = scenes[cur].goto; } }
  for (const k of Object.keys(scenes)) if (!seen.has(k)) order.push(k);
  return order;
}

const MODIFY = { now: '立刻', today: '今天', nextAvailable: '下一个 hour 点（推荐用于跨日）', nextDay: '隔天（小心：从上个场景结束时算）' };

function scenesTab(mod, id, d) {
  const scenes = d.script.scenes;
  const tpl = resolveTemplate(mod, d.metadata.tmpContainer);
  const cams = tpl ? tpl.cameras : [];
  const order = sceneOrder(d);
  if (!scenes[ui.scene]) ui.scene = order[0];
  const wrap = h('div', {});
  wrap.append(h('div', { class: 'help' }, '剧情由「场景」串成：每个场景在指定时间（hour 点）开始，依序运行动作，做完后等待并接到「下一个场景」。',
    '时间模式：「立刻」= 上一个场景做完马上开始；「今天」= 今天到了 hour 点；「下一个 hour 点」= 还没到就今天、已经过了就明天；「隔天」= 隔天到了 hour 点。最后一个场景没有下一个时，画面就停在那里。',
    h('br'), h('b', {}, '注意：'), '日期是在「上一个场景做完」的那一刻决定的。深夜场景常常会跑过午夜，这时「隔天」会变成后天、「今天 23 点」会变成明晚，结果整天没动静。',
    '每天早上的第一个场景请用「下一个 hour 点」；深夜的短场景直接并进前一个场景。'));
  const list = h('div', { class: 'scenelist' });
  for (const name of order) {
    const sc = scenes[name];
    list.append(h('div', { class: 'item' + (ui.scene === name ? ' sel' : ''), onclick: () => { ui.scene = name; renderMain(); } },
      h('b', {}, name), h('small', {}, `镜头${sc.camera} · ${MODIFY[sc.modify] || sc.modify || ''} ${sc.hour}:00 · ${(sc.script || []).length} 个动作` + (sc.goto ? ' → ' + sc.goto : ' ⏹'))));
  }
  list.append(h('div', { class: 'row', style: 'margin-top:8px' },
    h('button', { onclick: () => {
      const name = prompt('新场景名称（英文）', 'scene' + (order.length + 1));
      if (!name) return;
      if (scenes[name]) { alert('已经有同名场景'); return; }
      const prevName = ui.scene;
      scenes[name] = { camera: scenes[prevName] ? scenes[prevName].camera : 1, hour: '10', modify: 'nextAvailable', script: [] };
      if (prevName && scenes[prevName] && !scenes[prevName].goto && confirm(`要把「${prevName}」的下一个场景设成「${name}」吗？`)) scenes[prevName].goto = name;
      ui.scene = name; changed(true);
    } }, '＋ 场景')));
  const edit = h('div', { class: 'sceneedit' });
  const sc = scenes[ui.scene];
  if (sc) edit.append(sceneEditor(mod, id, d, ui.scene, sc, cams));
  wrap.append(h('div', { class: 'scenes' }, list, edit));
  return wrap;
}

function sceneEditor(mod, id, d, name, sc, cams) {
  const scenes = d.script.scenes;
  const box = h('div', {});
  const camCount = +d.script.metadata.cameras || 1;
  box.append(h('div', { class: 'row' },
    h('div', { class: 'field' }, h('label', {}, '场景名称'), h('div', { class: 'row', style: 'margin:0' }, h('b', { style: 'font-size:16px' }, name),
      h('button', { class: 'small', onclick: () => {
        const nn = prompt('新的场景名称', name);
        if (!nn || nn === name) return;
        if (scenes[nn]) { alert('已经有同名场景'); return; }
        scenes[nn] = sc; delete scenes[name];
        for (const s of Object.values(scenes)) if (s.goto === name) s.goto = nn;
        const smd = d.script.metadata;
        for (const k of ['startScene', 'startScene2', 'startScene3', 'startScene4']) if (smd[k] === name) smd[k] = nn;
        ui.scene = nn; changed(true);
      } }, '改名'),
      h('button', { class: 'small', onclick: () => { const nn = name + '_copy'; scenes[nn] = clone(sc); delete scenes[nn].goto; ui.scene = nn; changed(true); } }, '拷贝'),
      h('button', { class: 'small danger', onclick: () => {
        if (!confirm(`删除场景「${name}」？`)) return;
        for (const s of Object.values(scenes)) if (s.goto === name) s.goto = sc.goto || undefined;
        delete scenes[name]; ui.scene = null; changed(true);
      } }, '删除'))),
    h('div', { class: 'field' }, lbl('镜头', 'sceneCamera'), h('select', { onchange: e => { sc.camera = +e.target.value; changed(true); } },
      Array.from({ length: camCount }, (_, i) => h('option', { value: i + 1, selected: +sc.camera === i + 1 }, i + 1)))),
    h('div', { class: 'field' }, lbl('时间模式', 'modify'), h('select', { onchange: e => { sc.modify = e.target.value; changed(true); } },
      Object.entries(MODIFY).map(([k, v]) => h('option', { value: k, selected: sc.modify === k }, v)))),
    h('div', { class: 'field' }, lbl('几点开始（0-23）', 'hour'), h('input', { type: 'number', min: 0, max: 23, value: sc.hour, oninput: e => { sc.hour = String(e.target.value); changed(); } })),
    h('div', { class: 'field' }, lbl('下一个场景', 'goto'), h('select', { onchange: e => { if (e.target.value) sc.goto = e.target.value; else delete sc.goto; changed(true); } },
      h('option', { value: '' }, '（结束）'), Object.keys(scenes).filter(s => s !== name).map(s => h('option', { value: s, selected: sc.goto === s }, s))))));
  box.append(h('div', { class: 'field', style: 'margin-bottom:8px' }, lbl('备注', 'comment'),
    h('input', { value: sc._comment || '', style: 'width:100%', oninput: e => { if (e.target.value) sc._comment = e.target.value; else delete sc._comment; changed(); } })));
  const cam = cams[(+sc.camera || 1) - 1];
  if (cam) {
    const pv = scenePreview(mod, id, d, name, cams);
    pv.classList.add('livepreview');
    box.append(pv);
  }
  const hasLight = list => (list || []).some(a => a.action === 'blinkLed' || (Array.isArray(a.actions) && hasLight(a.actions)) ||
    (a.action === 'predefinedAction' && hasLight((d.script.predefinedActions || {})[a.name])));
  const charName = () => { const c = cams[(+sc.camera || 1) - 1]; const o = c && c.objects.find(x => x.depth === 0 && (x.anims || x.custom)); return o ? o.name : ''; };
  box.append(h('h3', {}, '动作', tip('light'),
    h('button', { class: 'small', style: 'margin-left:10px', title: '在开头加入「镜头灯闪烁」、结尾加入「停止闪烁」', disabled: hasLight(sc.script), onclick: () => {
      sc.script.unshift({ id: charName(), action: 'blinkLed' });
      sc.script.push({ id: charName(), action: 'stopLed' });
      changed(true);
    } }, hasLight(sc.script) ? '💡 已有镜头灯' : '💡 一键加入镜头灯')));
  sc.script = sc.script || [];
  box.append(actionList(sc.script, { mod, section: id, cams, camIndex: () => (+sc.camera || 1) - 1, predefNames: Object.keys(d.script.predefinedActions || {}) }));
  const evBox = h('details', {}, h('summary', { class: 'muted', style: 'cursor:pointer;margin-top:10px' },
    '场景开始 / 结束时的游戏事件' + ((sc.startEvents || []).length + (sc.finishEvents || []).length ? '（已设置）' : ''), tip('startEvents')));
  for (const [k, label] of [['startEvents', '场景开始时'], ['finishEvents', '场景结束时']]) {
    sc[k] = sc[k] || [];
    evBox.append(h('h3', {}, label), eventList(sc[k], mod, id, d));
  }
  box.append(evBox);
  return box;
}

// ------------------------------------------------------------------ predefined actions tab

function predefTab(mod, id, d) {
  const pd = d.script.predefinedActions = d.script.predefinedActions || {};
  const tpl = resolveTemplate(mod, d.metadata.tmpContainer);
  const cams = tpl ? tpl.cameras : [];
  const names = Object.keys(pd);
  if (!pd[ui.predef]) ui.predef = names[0];
  const wrap = h('div', {});
  wrap.append(h('div', { class: 'help' }, '预设动作是可重复使用的一串动作（例如「坐下看书」），在剧情中用「📋 运行预设动作」调用。'));
  const list = h('div', { class: 'scenelist' });
  for (const n of names) list.append(h('div', { class: 'item' + (ui.predef === n ? ' sel' : ''), onclick: () => { ui.predef = n; renderMain(); } }, h('b', {}, n), h('small', {}, pd[n].length + ' 个动作')));
  list.append(h('div', { class: 'row', style: 'margin-top:8px' }, h('button', { onclick: () => {
    const n = prompt('预设动作名称（英文）', 'myAction');
    if (!n || pd[n]) return;
    pd[n] = []; ui.predef = n; changed(true);
  } }, '＋ 预设动作')));
  const edit = h('div', { class: 'sceneedit' });
  if (ui.predef && pd[ui.predef]) {
    const n = ui.predef;
    let camIdx = 0;
    edit.append(h('div', { class: 'row' }, h('b', { style: 'font-size:16px' }, n),
      h('button', { class: 'small', onclick: () => {
        const nn = prompt('新名称', n); if (!nn || nn === n || pd[nn]) return;
        pd[nn] = pd[n]; delete pd[n];
        const walk = l => (l || []).forEach(a => { if (a.action === 'predefinedAction' && a.name === n) a.name = nn; if (a.actions) walk(a.actions); });
        Object.values(d.script.scenes).forEach(s => walk(s.script)); Object.values(pd).forEach(walk);
        ui.predef = nn; changed(true);
      } }, '改名'),
      h('button', { class: 'small danger', onclick: () => { if (confirm('删除？')) { delete pd[n]; ui.predef = null; changed(true); } } }, '删除'),
      cams.length > 1 ? h('span', {}, h('label', {}, '　对象清单用镜头 '), h('select', { onchange: e => { camIdx = +e.target.value; renderMain(); } }, cams.map((c, i) => h('option', { value: i }, i + 1)))) : null));
    edit.append(actionList(pd[n], { mod, section: id, cams, camIndex: () => camIdx, predefNames: Object.keys(pd).filter(x => x !== n) }));
  }
  wrap.append(h('div', { class: 'scenes' }, list, edit));
  return wrap;
}

// ------------------------------------------------------------------ keywords tab

function keywordsTab(mod, id, d) {
  const kws = d.keywords = d.keywords || {};
  const wrap = h('div', {});
  wrap.append(h('div', { class: 'help' }, '关键字是玩家在对白中点击、写进笔记本、再拿去浏览器搜索的词。',
    'id 只能用英文和数字；在对白中用 [id]显示文本[/id] 标出。',
    '组合搜索：id 写成「a_b」代表同时搜索 a 和 b 时的结果；多个 id 用逗号分隔，代表共用同一组结果。'));
  for (const key of Object.keys(kws)) {
    const def = kws[key];
    const card = h('div', { class: 'card' });
    card.append(h('div', { class: 'row' }, h('b', { class: 'mono' }, key),
      h('button', { class: 'small', onclick: () => {
        const nk = prompt('新的关键字 id', key);
        if (!nk || nk === key || kws[nk]) return;
        const rebuilt = {}; for (const [k, v] of Object.entries(kws)) rebuilt[k === key ? nk : k] = v;
        d.keywords = rebuilt;
        const page = mod.manifest.diaryPages.find(p => p.story === id);
        if (page && page.words && page.words[key]) { page.words[nk] = page.words[key]; delete page.words[key]; }
        for (const z of (d.diaryConfig || {}).zones || []) z.words = (z.words || []).map(w => w === key ? nk : w);
        toast('已改名。对白里的 [' + key + '] 标记请手动更新（检查结果会列出）。');
        changed(true);
      } }, '改名'),
      h('button', { class: 'small danger', onclick: () => { if (confirm('删除关键字「' + key + '」？')) { delete kws[key]; changed(true); } } }, '删除')));
    if (!key.includes('_') && !key.includes(',')) {
      card.append(h('div', { class: 'field' }, h('label', {}, '笔记本上显示的文本'), textRef(mod, id, () => def.text, v => { def.text = v; })));
      const calls = Object.keys(d.phoneCalls || {});
      const call = (def.clickEvents || []).find(e => e.type === 'callTo');
      card.append(h('div', { class: 'row' },
        h('label', { style: 'color:var(--text)' }, h('input', { type: 'checkbox', checked: !!def.isAddress, onchange: e => { if (e.target.checked) def.isAddress = true; else delete def.isAddress; changed(); } }), ' 是地址（可在 MART 寄东西过去）', tip('isAddress')),
        h('div', { class: 'field' }, lbl('一起写进笔记本的关键字（addWords）', 'addWords'),
          h('input', { value: (def.addWords || []).join(', '), placeholder: 'kw1, kw2', style: 'width:220px', oninput: e => {
            const v = e.target.value.split(',').map(x => x.trim()).filter(Boolean); if (v.length) def.addWords = v; else delete def.addWords; changed(); } })),
        h('div', { class: 'field' }, lbl('点笔记本按钮时拨打（电话号码）', 'kwCall'),
          h('select', { onchange: e => {
            def.clickEvents = (def.clickEvents || []).filter(x => x.type !== 'callTo');
            if (e.target.value) def.clickEvents.unshift({ type: 'callTo', id: e.target.value });
            if (!def.clickEvents.length) delete def.clickEvents;
            changed();
          } }, h('option', { value: '' }, '（不是电话）'), calls.map(c => h('option', { value: c, selected: call && call.id === c }, c))))));
    }
    def.browser = def.browser || { data: [] };
    const results = def.browser.data = def.browser.data || [];
    card.append(h('h3', { style: 'margin-top:10px' }, '浏览器搜索结果'));
    results.forEach((r, ri) => card.append(browserResultEditor(mod, id, results, r, ri)));
    const typeSel = h('select', {}, Object.entries(BROWSER_TYPES).map(([k, v]) => h('option', { value: k }, v.label)));
    card.append(h('div', { class: 'row' }, typeSel, h('button', { onclick: () => { results.push(BROWSER_TYPES[typeSel.value].make()); changed(true); } }, '＋ 搜索结果')));
    wrap.append(card);
  }
  wrap.append(h('div', { class: 'row' }, h('button', { class: 'primary', onclick: () => {
    const k = prompt('新关键字 id（英文和数字，例如 blackBook）');
    if (!k) return;
    if (!/^[A-Za-z0-9_, ]+$/.test(k)) { alert('只能使用英文、数字、底线、逗号'); return; }
    if (kws[k]) { alert('已存在'); return; }
    kws[k] = { text: '' };
    changed(true);
  } }, '＋ 添加关键字')));
  return wrap;
}

function imageField(r) {
  const listId = 'imgs-' + Math.random().toString(36).slice(2);
  const wrap = h('div', { class: 'field', style: 'width:100%' }, h('label', {}, '配图（游戏内置图片路径，或 mod 自己的 PNG：mods/<Mod>/<文件>，输入关键字筛选）'));
  wrap.append(h('input', { value: r.image || '', list: listId, style: 'width:100%', oninput: e => { r.image = e.target.value; changed(); } }),
    h('datalist', { id: listId }, modImagePaths().concat(CAT.images.filter(p => p.startsWith('newspapper/'))).map(p => h('option', { value: p }))));
  return wrap;
}

// ------------------------------------------------------------------ diary tab

function diaryTab(mod, id, d) {
  const M = mod.manifest;
  let page = M.diaryPages.find(p => p.story === id);
  const wrap = h('div', {});
  wrap.append(h('div', { class: 'help' }, '笔记本的每一页都是游戏场景里手工排版的对象，所以新笼子要「借用」一个现有笼子的页面版型：',
    '把你的关键字分配到版型上的文本字段（红字），再勾选要保留的圆圈或箭头。每个能被收集的关键字都必须有字段，否则游戏会出错。'));
  if (!page) {
    wrap.append(h('button', { class: 'primary', onclick: () => { M.diaryPages.push({ story: id, cloneFrom: 'redFred', words: {}, keep: ['diaryWordvideo'] }); changed(true); } }, '创建笔记本页设置'));
    return wrap;
  }
  page.words = page.words || {}; page.keep = page.keep || [];
  const src = DIARY_BY_ID[page.cloneFrom];
  wrap.append(h('div', { class: 'row' }, h('label', {}, '版型来源'), h('select', { onchange: e => {
    if (Object.keys(page.words).length && !confirm('更换版型会清除目前的字段分配，确定吗？')) { e.target.value = page.cloneFrom; return; }
    page.cloneFrom = e.target.value; page.words = {}; page.keep = ['diaryWordvideo']; changed(true);
  } }, CAT.diaryPages.map(p => h('option', { value: p.id, selected: p.id === page.cloneFrom }, 'diary' + p.id)))));
  if (!src) return wrap;
  const kwList = Object.keys(d.keywords || {}).filter(k => !k.includes(',') && !k.includes('_'));
  const slotToKw = {}; for (const [kw, s] of Object.entries(page.words)) slotToKw[s] = kw;
  let selectedKw = kwList.find(k => !page.words[k]) || kwList[0];
  const kwSel = h('select', { onchange: e => { selectedKw = e.target.value; } }, kwList.map(k => h('option', { value: k, selected: k === selectedKw }, k)));
  wrap.append(h('div', { class: 'row' }, h('label', {}, '点击下图的红色字段，分配给关键字：'), kwSel));

  // Schematic of the page, with the copies and moves of loader 0.5.4+ applied.
  const items = pageItems(src, page);
  const xs = items.map(c => c.x), ys = items.map(c => c.y);
  const minX = Math.min(...xs) - 0.25, maxX = Math.max(...xs) + 0.35, minY = Math.min(...ys) - 0.12, maxY = Math.max(...ys) + 0.12;
  // Page coordinates are much wider than tall; stretch vertically so neighbouring slots do not overlap.
  const W = 880, Hh = 420;
  const sx = x => (x - minX) / (maxX - minX) * W, sy = y => Hh - (y - minY) / (maxY - minY) * Hh;
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('class', 'diary'); svg.setAttribute('width', W); svg.setAttribute('height', Hh);
  svg.style.background = '#e8e3c8'; svg.style.borderRadius = '6px';
  const sv = (tag, attrs, text) => { const e = document.createElementNS('http://www.w3.org/2000/svg', tag); for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v); if (text) e.textContent = text; svg.append(e); return e; };
  for (const c of items) {
    const kept = page.keep.includes(c.name) || c.copy;
    if (c.kind === 'circle') sv('ellipse', { cx: sx(c.x), cy: sy(c.y), rx: 0.33 / (maxX - minX) * W, ry: 0.15 / (maxY - minY) * Hh, fill: 'none', stroke: kept ? '#2c3e50' : '#b9b39a', 'stroke-width': kept ? 2 : 1, 'stroke-dasharray': kept ? '' : '4 3' });
  }
  for (const c of items) {
    if (c.kind === 'word') {
      const slot = c.name.slice(9);
      const kw = slotToKw[slot];
      const t = sv('text', { x: sx(c.x), y: sy(c.y), 'text-anchor': 'middle', class: 'slot' + (kw ? ' sel' : ''), fill: kw ? '#c0392b' : '#7f8c8d' }, kw ? '★' + kw : slot);
      t.append(Object.assign(document.createElementNS('http://www.w3.org/2000/svg', 'title'), { textContent: '字段 ' + slot + (kw ? '：' + kw : '') }));
      t.addEventListener('click', () => {
        if (!selectedKw) { alert('请先在「关键字」分页添加关键字'); return; }
        if (slotToKw[slot] === selectedKw) delete page.words[selectedKw];
        else { if (slotToKw[slot]) delete page.words[slotToKw[slot]]; page.words[selectedKw] = slot; }
        changed(true);
      });
    } else if (c.kind !== 'circle') {
      sv('text', { x: sx(c.x), y: sy(c.y), 'text-anchor': 'middle', fill: page.keep.includes(c.name) || c.copy ? '#2980b9' : '#b9b39a', 'font-style': 'italic' }, c.name.replace(/^diary/, ''));
    }
  }
  wrap.append(svg);
  wrap.append(h('h3', {}, '关键字 → 字段'));
  const wordSlots = items.filter(c => c.kind === 'word').map(c => c.name.slice(9));
  const actionSrc = src.children.filter(c => /Action$/.test(c.name)).map(c => c.name.slice(9, -6));
  wrap.append(h('div', { class: 'help' }, '「可选」（main）：只有可选的字才能在电话、聊天、俱乐部任务里从笔记本选出来，一般全部勾选。',
    '「大写」：人名像游戏一样用大写显示。「按钮」：电话号码或聊天对象旁边的拨号/聊天按钮，从版型上有按钮的字段复制。', tip('diaryMain')));
  wrap.append(h('div', { class: 'row' }, h('button', { class: 'small', onclick: () => { page.main = Object.keys(page.words); changed(true); } }, '全部设为可选'),
    page.main ? h('button', { class: 'small', onclick: () => { delete page.main; changed(true); } }, '改回版型原本的设置') : h('span', { class: 'muted' }, '（目前沿用版型原本哪些字可选）')));
  const toggle = (key, kw, on) => { const a = new Set(page[key] || []); if (on) a.add(kw); else a.delete(kw); page[key] = [...a]; if (key === 'upper' && !page.upper.length) delete page.upper; changed(); };
  for (const kw of kwList) wrap.append(h('div', { class: 'row' }, h('span', { class: 'mono', style: 'width:160px' }, kw), h('select', { onchange: e => {
    for (const [k, s] of Object.entries(page.words)) if (s === e.target.value && k !== kw) delete page.words[k];
    if (e.target.value) page.words[kw] = e.target.value; else delete page.words[kw];
    changed(true);
  } }, h('option', { value: '' }, '（未分配）'), wordSlots.map(s => h('option', { value: s, selected: page.words[kw] === s }, s))),
    h('label', { style: 'color:var(--text)' }, h('input', { type: 'checkbox', checked: !!(page.main && page.main.includes(kw)), onchange: e => toggle('main', kw, e.target.checked) }), ' 可选'),
    h('label', { style: 'color:var(--text)' }, h('input', { type: 'checkbox', checked: !!(page.upper && page.upper.includes(kw)), onchange: e => toggle('upper', kw, e.target.checked) }), ' 大写'),
    h('label', {}, '按钮'), h('select', { onchange: e => {
      page.actions = page.actions || {};
      if (e.target.value) page.actions[kw] = e.target.value; else delete page.actions[kw];
      if (!Object.keys(page.actions).length) delete page.actions;
      changed();
    } }, h('option', { value: '' }, '（无）'), actionSrc.map(a => h('option', { value: a, selected: (page.actions || {})[kw] === a }, a)))));
  if (!kwList.length) wrap.append(h('div', { class: 'muted' }, '还没有关键字。'));
  wrap.append(h('h3', {}, '保留的页面元素', tip('diaryKeep')));
  wrap.append(h('div', { class: 'row' }, src.children.filter(c => c.kind !== 'word').map(c => h('label', { style: 'color:var(--text)' },
    h('input', { type: 'checkbox', checked: page.keep.includes(c.name), onchange: e => {
      page.keep = page.keep.filter(x => x !== c.name); if (e.target.checked) page.keep.push(c.name); changed(true);
    } }), ' ' + c.name))));

  // Zones.
  const dc = d.diaryConfig = d.diaryConfig || {};
  dc.zones = dc.zones || []; if (!Array.isArray(dc.arrows)) dc.arrows = []; if (!Array.isArray(dc.images)) dc.images = [];
  wrap.append(h('h3', {}, '区块（圆圈）', tip('diaryZones')));
  wrap.append(h('div', { class: 'help' }, '区块决定哪些关键字属于哪个圆圈：只要收集到其中任一个字，圆圈就会画出来。'));
  const circles = page.keep.filter(n => /^diaryCircle\d+$/.test(n));
  dc.zones.forEach((z, zi) => {
    wrap.append(h('div', { class: 'card row' },
      h('label', {}, '圆圈'), h('select', { onchange: e => { z.circle = e.target.value; changed(true); } },
        circles.concat(circles.includes(z.circle) ? [] : [z.circle]).map(c => h('option', { value: c, selected: z.circle === c }, c))),
      h('label', {}, '关键字'), kwList.map(k => h('label', { style: 'color:var(--text)' }, h('input', { type: 'checkbox', checked: (z.words || []).includes(k), onchange: e => {
        z.words = (z.words || []).filter(x => x !== k); if (e.target.checked) z.words.push(k); changed();
      } }), ' ' + k)),
      h('button', { class: 'small danger', onclick: () => { dc.zones.splice(zi, 1); changed(true); } }, '删除'),
      mainWordEditor(z, kwList)));
  });
  wrap.append(h('div', { class: 'row' }, h('button', { disabled: !circles.length, onclick: () => { dc.zones.push({ circle: circles[0], words: [] }); changed(true); } }, '＋ 区块'),
    circles.length ? null : h('span', { class: 'muted' }, '（先在上面勾选保留一个 diaryCircle）')));
  wrap.append(deductionEditor(page, src, dc, circles, kwList));
  wrap.append(arrowEditor(page, src, dc, circles));
  wrap.append(layoutEditor(page, src));
  return wrap;
}

/** Source page children after the page's copies and moves (what the loader builds). */
function pageItems(src, page) {
  const items = src.children.map(c => Object.assign({}, c));
  for (const cp of page.copies || []) {
    const from = items.find(c => c.name === cp.from);
    if (from) items.push(Object.assign({}, from, { name: cp.name, x: from.x + (+cp.dx || 0), y: from.y + (+cp.dy || 0), copy: true }));
  }
  for (const mv of page.moves || []) for (const c of items) if (c.name === mv.name) { c.x += +mv.dx || 0; c.y += +mv.dy || 0; }
  return items;
}

function numIn(obj, key, width, dflt) {
  return h('input', { type: 'number', step: 0.01, value: obj[key] ?? dflt, style: 'width:' + (width || 70) + 'px', oninput: e => {
    const v = parseFloat(e.target.value);
    if (isNaN(v) || (dflt !== undefined && v === dflt && (key === 'sx' || key === 'sy'))) delete obj[key]; else obj[key] = v;
    changed();
  } });
}

/** mainWord: the circle writes a word by itself once the player has others (e.g. a box's name once the number is known). */
function mainWordEditor(z, kwList) {
  const box = h('div', { style: 'width:100%' });
  (z.mainWord || []).forEach((m, i) => box.append(h('div', { class: 'row' }, h('span', { class: 'muted' }, '自动写入'),
    h('select', { onchange: e => { m.word = e.target.value; changed(); } }, kwList.map(k => h('option', { value: k, selected: m.word === k }, k))),
    h('span', { class: 'muted' }, '当玩家有'),
    h('input', { value: m.haveWord || '', placeholder: 'kw1,kw2', style: 'width:160px', oninput: e => { m.haveWord = e.target.value.trim(); changed(); } }),
    h('span', { class: 'muted' }, '且这个圆圈至少有'), h('input', { type: 'number', value: m.atLeast ?? '', style: 'width:50px', oninput: e => { if (e.target.value === '') delete m.atLeast; else m.atLeast = +e.target.value; changed(); } }), h('span', { class: 'muted' }, '个字'),
    h('button', { class: 'small danger', onclick: () => { z.mainWord.splice(i, 1); if (!z.mainWord.length) delete z.mainWord; changed(true); } }, '✕'))));
  box.append(h('button', { class: 'small', onclick: () => { z.mainWord = z.mainWord || []; z.mainWord.push({ haveWord: '', word: kwList[0] || '' }); changed(true); } }, '＋ 自动写入（mainWord）'), tip('mainWord'));
  return box;
}

/** Deductions (the "?" on a circle, ModLoader 0.5.5): three answers + the condition for the "?" to appear. */
function deductionEditor(page, src, dc, circles, kwList) {
  const box = h('div', {});
  box.append(h('h3', {}, '推理「？」', tip('deduction')));
  const withSel = circles.filter(c => src.children.some(x => x.name === c + 'Selector'));
  if (!withSel.length) { box.append(h('div', { class: 'muted' }, '这个版型保留的圆圈都没有推理「？」。')); return box; }
  box.append(h('div', { class: 'help' }, '圆圈的字收集够了，旁边会出现「？」，玩家从 3 个答案里选一个，选中的答案会写进笔记本（之后可以搜索、打电话、聊天时使用）。',
    '3 个答案也要是关键字，并分配到圆圈旁边叠在一起的字段（版型原本的答案位置，见上图）。'));
  for (const c of withSel) {
    const answers = (page.selectors || {})[c];
    let z = dc.zones.find(x => x.circle === c);
    const card = h('div', { class: 'card' });
    card.append(h('div', { class: 'row' }, h('b', {}, c), h('label', { style: 'color:var(--text)' }, h('input', { type: 'checkbox', checked: !!answers, onchange: e => {
      page.selectors = page.selectors || {};
      if (e.target.checked) {
        page.selectors[c] = ['', '', ''];
        if (!z) { z = { circle: c, words: [] }; dc.zones.push(z); }
        z.selectableWords = page.selectors[c]; z.wordSelector = z.wordSelector || { atLeast: 3 };
      } else {
        delete page.selectors[c]; if (!Object.keys(page.selectors).length) delete page.selectors;
        if (z) { delete z.selectableWords; delete z.wordSelector; }
      }
      changed(true);
    } }), ' 使用推理')));
    if (answers) {
      card.append(h('div', { class: 'row' }, h('label', {}, '答案（由上到下）'), [0, 1, 2].map(i => h('select', { onchange: e => {
        answers[i] = e.target.value;
        z.selectableWords = answers.slice();
        z.words = z.words || []; if (e.target.value && !z.words.includes(e.target.value)) z.words.push(e.target.value);
        changed();
      } }, h('option', { value: '' }, '（选择）'), kwList.map(k => h('option', { value: k, selected: answers[i] === k }, k))))));
      const ws = z.wordSelector = z.wordSelector || {};
      card.append(h('div', { class: 'row' }, h('label', {}, '至少收集'), numIn(ws, 'atLeast', 50), h('label', {}, '个字；只计算这些字（空白 = 圆圈全部的字）'),
        h('input', { value: (ws.words || []).join(','), placeholder: 'kw1,kw2', style: 'width:200px', oninput: e => {
          const v = e.target.value.split(',').map(x => x.trim()).filter(Boolean); if (v.length) ws.words = v; else delete ws.words; changed(); } }),
        h('label', {}, '而且一定要有'), h('input', { value: ws.haveWord || '', placeholder: 'kw1,kw2', style: 'width:140px', oninput: e => {
          if (e.target.value.trim()) ws.haveWord = e.target.value.trim(); else delete ws.haveWord; changed(); } })));
    }
    box.append(card);
  }
  return box;
}

/** Arrows between circles: shown when both circles are drawn (a circle with a "?" is drawn once it is answered). */
function arrowEditor(page, src, dc, circles) {
  const box = h('div', {});
  box.append(h('h3', {}, '箭头', tip('arrows')));
  const arrows = src.children.filter(c => /^diaryArrow/.test(c.name)).map(c => c.name).concat((page.copies || []).filter(c => /^diaryArrow/.test(c.name)).map(c => c.name));
  dc.arrows.forEach((a, i) => {
    const [c1, c2] = (a.haveCircle || ',').split(',');
    const set = (x, y) => { a.haveCircle = x + ',' + y; changed(); };
    box.append(h('div', { class: 'row' },
      h('select', { onchange: e => set(e.target.value, c2) }, circles.map(c => h('option', { value: c, selected: c === c1 }, c))),
      h('span', {}, '↔'),
      h('select', { onchange: e => set(c1, e.target.value) }, circles.map(c => h('option', { value: c, selected: c === c2 }, c))),
      h('label', {}, '用'), h('select', { onchange: e => { a.arrow = e.target.value; if (!page.keep.includes(a.arrow) && !(page.copies || []).some(c => c.name === a.arrow)) page.keep.push(a.arrow); changed(true); } },
        arrows.map(n => h('option', { value: n, selected: a.arrow === n }, n))),
      h('button', { class: 'small danger', onclick: () => { dc.arrows.splice(i, 1); changed(true); } }, '✕')));
  });
  box.append(h('button', { class: 'small', disabled: circles.length < 2 || !arrows.length, onclick: () => {
    dc.arrows.push({ haveCircle: circles[0] + ',' + circles[1], arrow: arrows[0] });
    if (!page.keep.includes(arrows[0])) page.keep.push(arrows[0]);
    changed(true);
  } }, '＋ 箭头'));
  return box;
}

/** Copies (loader 0.5.4) and moves (0.5.6; sx / sy scale since 0.5.9) of the source page's parts. */
function layoutEditor(page, src) {
  const box = h('div', {});
  box.append(h('h3', {}, '调整版面', tip('diaryLayout')));
  box.append(h('div', { class: 'help' }, '复制：把版型上的东西（例如电话方框和它的两个字段）再复制一份，放到新位置。移动：把元素平移，或放大缩小（sx、sy，1 = 原尺寸）。',
    '单位是笔记本页面座标（整页宽约 3.6、高约 1.6），上图会即时显示结果。'));
  const names = src.children.map(c => c.name);
  const all = names.concat((page.copies || []).map(c => c.name));
  const listEditor = (key, title, make, nameField) => {
    const list = page[key] || [];
    const card = h('div', { class: 'card' }, h('b', {}, title));
    list.forEach((m, i) => card.append(h('div', { class: 'row' },
      nameField(m),
      h('label', {}, 'dx'), numIn(m, 'dx'), h('label', {}, 'dy'), numIn(m, 'dy'),
      h('label', {}, 'sx'), numIn(m, 'sx', 60, 1), h('label', {}, 'sy'), numIn(m, 'sy', 60, 1),
      h('button', { class: 'small danger', onclick: () => { list.splice(i, 1); if (!list.length) delete page[key]; changed(true); } }, '✕'))));
    card.append(h('button', { class: 'small', onclick: () => { page[key] = list; list.push(make()); changed(true); } }, '＋ ' + title));
    return card;
  };
  box.append(listEditor('copies', '复制元素', () => ({ from: names[0], name: 'diaryWordcopy' + ((page.copies || []).length + 1), dx: 0, dy: 0 }), m => h('span', {},
    h('select', { onchange: e => { m.from = e.target.value; changed(true); } }, names.map(n => h('option', { value: n, selected: m.from === n }, n))),
    h('span', {}, ' → 新名称 '), h('input', { value: m.name, style: 'width:170px', oninput: e => { m.name = e.target.value.trim(); changed(); } }))));
  box.append(h('div', { class: 'muted' }, '复制出来的字段名称要以 diaryWord 开头，才能在上面「关键字 → 字段」分配关键字。'));
  box.append(listEditor('moves', '移动元素', () => ({ name: names[0], dx: 0, dy: 0 }), m =>
    h('select', { onchange: e => { m.name = e.target.value; changed(true); } }, all.map(n => h('option', { value: n, selected: m.name === n }, n)))));
  return box;
}

// ------------------------------------------------------------------ strings tab

function stringsTab(mod, id, d) {
  const wrap = h('div', {});
  wrap.append(h('div', { class: 'help' }, `这个笼子的所有文本（区段「${id}」）。英文会同时写进剧情档当作后备文本。游戏的中文接口只能显示简体字。`));
  const nums = new Set();
  for (const r of allRefs(d)) if (r.section === id) nums.add(r.num);
  for (const lang of LANGS) { const t = locTable(mod, lang, false); if (t && t[id]) Object.keys(t[id]).forEach(n => nums.add(n)); }
  const sorted = [...nums].sort((a, b) => (+a || 0) - (+b || 0) || a.localeCompare(b));
  const used = new Set(allRefs(d).filter(r => r.section === id).map(r => r.num));
  wrap.append(h('div', { class: 'row' },
    h('button', { onclick: () => { for (const n of sorted) { const z = getLoc(mod, 'ch', id, n); if (z) setLoc(mod, 'ch', id, n, toSimplified(z)); } changed(true); toast('已把繁体字转成简体'); } }, '全部繁→简'),
    h('button', { onclick: () => {
      let n = 0; for (const k of sorted) if (!used.has(k)) { for (const lang of LANGS) { const t = locTable(mod, lang, false); if (t && t[id]) delete t[id][k]; } n++; }
      changed(true); toast(`已删除 ${n} 条没用到的文本`);
    } }, '删除没用到的文本')));
  const table = h('table', { class: 'strings' }, h('tr', {}, h('th', { style: 'width:70px' }, 'key'), h('th', {}, 'English'), h('th', {}, '简体中文')));
  for (const n of sorted) {
    const zhCell = h('td', {});
    const warn = h('div', { style: 'font-size:12px' });
    const upd = v => {
      warn.innerHTML = '';
      const bad = missingGlyphs(v), tw = traditionalChars(v);
      if (tw.length) warn.append(h('span', { style: 'color:var(--warn)' }, '繁体：' + tw.join('') + ' '));
      if (bad.length) warn.append(h('span', { style: 'color:var(--err)' }, '画不出：' + bad.join(' ')));
    };
    const zi = h('input', { value: getLoc(mod, 'ch', id, n), oninput: e => { setLoc(mod, 'ch', id, n, e.target.value); upd(e.target.value); changed(); } });
    zhCell.append(zi, warn); upd(zi.value);
    table.append(h('tr', {}, h('td', { class: 'mono' }, n, used.has(n) ? '' : h('div', { class: 'muted', style: 'font-size:11px' }, '未使用')),
      h('td', {}, h('input', { value: getLoc(mod, 'en', id, n), oninput: e => {
        setLoc(mod, 'en', id, n, e.target.value);
        // keep the fallback inside the cage file in sync
        const fix = o => { if (Array.isArray(o)) o.forEach((v, i) => { if (typeof v === 'string') { const r = parseRef(v); if (r && r.section === id && r.num === n) o[i] = `${id}_${n}~${e.target.value}`; } else fix(v); });
          else if (o && typeof o === 'object') for (const k of Object.keys(o)) { const v = o[k]; if (typeof v === 'string') { const r = parseRef(v); if (r && r.section === id && r.num === n) o[k] = `${id}_${n}~${e.target.value}`; } else fix(v); } };
        fix(d); changed();
      } })), zhCell));
  }
  wrap.append(table);
  if (!sorted.length) wrap.append(h('div', { class: 'muted' }, '还没有文本。在「剧情」加入「说话」动作，或在「关键字」填写文本后会出现在这里。'));
  return wrap;
}

// ------------------------------------------------------------------ raw tab

function rawTab(mod, id, d) {
  const wrap = h('div', {});
  wrap.append(h('div', { class: 'help' }, '完整的剧情档（files/' + id + '.json）。这里可以编辑编辑器没有表单的部分，例如 emails、chats、phoneCalls、news、prizes、genericEvents。改完按「套用」。'));
  const ta = h('textarea', { rows: 36 }); ta.value = pretty(d);
  wrap.append(ta, h('div', { class: 'row', style: 'margin-top:6px' }, h('button', { class: 'primary', onclick: () => {
    try {
      const v = parseLoose(ta.value);
      if (!v.metadata || !v.script) throw new Error('缺少 metadata 或 script');
      mod.files[id + '.json'] = v; changed(true); toast('已套用');
    } catch (e) { toast('JSON 错误：' + e.message, true); }
  } }, '套用'), h('button', { onclick: () => { ta.value = pretty(cageData(mod, id)); } }, '还原')));
  return wrap;
}

// ------------------------------------------------------------------ boot

function boot() {
  $('#btnOpen').onclick = doOpen;
  if (!('showDirectoryPicker' in window)) $('#btnOpen').disabled = true;
  $('#btnImport').onclick = () => $('#importInput').click();
  $('#importInput').onchange = e => { doImport(e.target.files); e.target.value = ''; };
  $('#btnNewMod').onclick = doNewMod;
  $('#btnSave').onclick = doSave;
  $('#btnZip').onclick = () => project.mods.length ? exportZip(project.mods) : toast('没有可导出的 mod', true);
  $('#btnHome').onclick = () => { ui.view = 'welcome'; render(); };
  window.addEventListener('beforeunload', e => { if (ui.dirty) { e.preventDefault(); e.returnValue = ''; } });
  document.addEventListener('keydown', e => { if ((e.ctrlKey || e.metaKey) && e.key === 's') { e.preventDefault(); doSave(); } });
  render();
}
document.addEventListener('DOMContentLoaded', boot);
