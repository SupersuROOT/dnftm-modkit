/* DNFTM Mod Editor - custom art: asset images, sprite frames, camera rendering, art tab. */
'use strict';

const VIEW_W = CAT.view.w, VIEW_H = CAT.view.h; // 252 x 174 script pixels

// ------------------------------------------------------------------ images

const imgCache = new Map();   // key -> HTMLImageElement
const urlCache = new Map();   // mod.folder + '|' + path -> blob URL
let redrawHooks = new Set();  // callbacks run when an image finishes loading

function assetURL(mod, path) {
  const key = mod.folder + '|' + path;
  const bytes = (mod.assets || {})[path];
  if (!bytes) return null;
  const cached = urlCache.get(key);
  if (cached && cached.bytes === bytes) return cached.url;
  if (cached) URL.revokeObjectURL(cached.url);
  const url = URL.createObjectURL(new Blob([bytes], { type: /\.jpe?g$/i.test(path) ? 'image/jpeg' : 'image/png' }));
  urlCache.set(key, { url, bytes });
  return url;
}

function loadImg(src) {
  if (!src) return null;
  let img = imgCache.get(src);
  if (!img) {
    img = new Image();
    img.onload = () => redrawHooks.forEach(f => { try { f(); } catch (e) { /* stale */ } });
    img.src = src;
    imgCache.set(src, img);
  }
  return img.complete && img.naturalWidth ? img : null;
}

/** Resolves one frame (file path or sheet index) of a custom art object to a drawable region. */
function artFrame(mod, o, frame) {
  if (typeof frame === 'string') {
    const img = loadImg(assetURL(mod, frame));
    return img ? { img, sx: 0, sy: 0, sw: img.naturalWidth, sh: img.naturalHeight } : null;
  }
  if (typeof frame === 'number' && o.sheet && o.sheet.image) {
    const img = loadImg(assetURL(mod, o.sheet.image));
    const w = +o.sheet.w, hh = +o.sheet.h;
    if (!img || !w || !hh) return null;
    const cols = Math.max(1, Math.floor(img.naturalWidth / w));
    return { img, sx: (frame % cols) * w, sy: Math.floor(frame / cols) * hh, sw: w, sh: hh };
  }
  return null;
}

function artDefaultFrame(o) {
  if (o.image) return o.image;
  const anims = o.animations || {};
  const a = anims.default || Object.values(anims)[0];
  return a && a.frames && a.frames.length ? a.frames[0] : null;
}

/** Frame of animation `anim` after `t` seconds (non-looping clips hold their last frame). */
function artAnimFrame(o, anim, t) {
  const a = (o.animations || {})[anim];
  if (!a || !a.frames || !a.frames.length) return artDefaultFrame(o);
  const fps = +a.fps || 6;
  let i = Math.floor(t * fps);
  i = a.loop === false ? Math.min(i, a.frames.length - 1) : i % a.frames.length;
  return a.frames[Math.max(0, i)];
}

function artClipDuration(o, anim) {
  const a = (o.animations || {})[anim];
  if (!a || !a.frames || !a.frames.length || a.loop !== false) return 0;
  return a.frames.length / (+a.fps || 6);
}

const PIVOTS = { bottom: [0.5, 0], center: [0.5, 0.5], top: [0.5, 1], bottomLeft: [0, 0] };

// ------------------------------------------------------------------ camera rendering

/**
 * Draws a camera view into a 2D context at `scale`.
 * state (optional, used by the live preview): { objects: {name: {x, y, visible, flip, anim, t}}, bubbles: [...] }
 * opts: { night: 0..1, nightVision: bool }
 */
function renderCamera(ctx, cam, scale, state, opts) {
  opts = opts || {};
  ctx.imageSmoothingEnabled = false;
  ctx.fillStyle = '#111'; ctx.fillRect(0, 0, VIEW_W * scale, VIEW_H * scale);
  const clear = cam.artDef && cam.artDef.clear;
  if (!clear) {
    const base = loadImg(previewSrc(state ? cam.bg : cam.full));
    if (base) ctx.drawImage(base, 0, 0, VIEW_W * scale, VIEW_H * scale);
  }
  const draws = [];
  for (const o of cam.objects) {
    if (o.depth !== 0) continue;
    const st = state && state.objects[o.name];
    if (o.custom) {
      const def = o.art;
      if (def.role === 'nightVisionOnly' && !opts.nightVision) continue;
      if (def.role === 'night' && !(opts.night > 0)) continue;
      if (st && !st.visible) continue;
      const frame = st && st.anim ? artAnimFrame(def, st.anim, st.t) : artDefaultFrame(def);
      const f = artFrame(cam.artMod, def, frame);
      if (!f) continue;
      const pv = PIVOTS[def.pivot] || PIVOTS.bottom;
      const flip = st ? st.flip === 'left' : !!def.flip;
      draws.push({ z: +def.z || 0, f, x: st ? st.x : +def.x, y: st ? st.y : +def.y, pvx: pv[0] * f.sw, pvy: pv[1] * f.sh, flip,
        alpha: def.role === 'night' ? Math.min(1, opts.night || 0) : 1, tint: def.role === 'tint' && opts.night });
    } else if (state && o.img && o.anims) {
      if (!st || !st.visible) continue;
      const img = loadImg(o.img);
      if (!img) continue;
      draws.push({ z: o.z || 0, f: { img, sx: 0, sy: 0, sw: img.naturalWidth, sh: img.naturalHeight }, x: st.x, y: st.y,
        pvx: o.pv[0], pvy: o.pv[1], flip: st.flip === 'left', alpha: 1, label: st.anim });
    }
  }
  draws.sort((a, b) => b.z - a.z); // farther (larger z) first
  for (const d of draws) {
    const left = (d.x - d.pvx) * scale, top = (VIEW_H - d.y - (d.f.sh - d.pvy)) * scale;
    ctx.save();
    ctx.globalAlpha = d.alpha;
    if (d.flip) { ctx.translate(left + d.f.sw * scale, top); ctx.scale(-1, 1); ctx.drawImage(d.f.img, d.f.sx, d.f.sy, d.f.sw, d.f.sh, 0, 0, d.f.sw * scale, d.f.sh * scale); }
    else ctx.drawImage(d.f.img, d.f.sx, d.f.sy, d.f.sw, d.f.sh, left, top, d.f.sw * scale, d.f.sh * scale);
    ctx.restore();
    if (d.label) {
      ctx.font = `${Math.max(9, 3 * scale)}px sans-serif`; ctx.fillStyle = 'rgba(0,0,0,.55)';
      const w = ctx.measureText(d.label).width + 6;
      ctx.fillRect(d.x * scale - w / 2, (VIEW_H - d.y) * scale + 2, w, 4 * scale);
      ctx.fillStyle = '#f2c14e'; ctx.textAlign = 'center'; ctx.fillText(d.label, d.x * scale, (VIEW_H - d.y) * scale + 3.4 * scale);
    }
  }
  if (!clear && opts.night > 0) { ctx.fillStyle = `rgba(10,14,40,${0.55 * Math.min(1, opts.night)})`; ctx.fillRect(0, 0, VIEW_W * scale, VIEW_H * scale); }
  if (opts.nightVision) { ctx.fillStyle = 'rgba(40,255,80,0.18)'; ctx.fillRect(0, 0, VIEW_W * scale, VIEW_H * scale); }
}

/** Static camera preview with labels; replaces the image-only version when a camera has custom art. */
function cameraCanvas(cam, scale, extra, opts) {
  const box = h('div', { class: 'preview', style: `width:${VIEW_W * scale}px;height:${VIEW_H * scale}px` });
  const cv = h('canvas', { width: VIEW_W * scale, height: VIEW_H * scale });
  box.append(cv);
  const draw = () => { if (cv.isConnected || !box.parentNode) renderCamera(cv.getContext('2d'), cam, scale, null, opts && opts()); };
  redrawHooks.add(draw);
  draw();
  box.redraw = draw;
  for (const o of cam.objects) {
    if (o.depth !== 0 || !(o.anims || o.clickable || o.custom)) continue;
    if (o.x < 0 || o.x > VIEW_W || o.y < 0 || o.y > VIEW_H) continue;
    box.append(h('div', { class: 'mk ' + (o.anims ? 'anim' : 'click'), style: `left:${o.x * scale}px;top:${(VIEW_H - o.y) * scale}px` }, o.name));
  }
  if (extra) extra(box, scale);
  return box;
}

// ------------------------------------------------------------------ art tab

const ART_KINDS = {
  background: { label: '🖼 背景（整张画面）', def: () => ({ pivot: 'center', x: 126, y: 87, z: 0 }) },
  character: { label: '🧍 角色（有动画）', def: () => ({ pivot: 'bottom', x: 126, y: 20, z: -20, animations: { default: { frames: [], fps: 4, loop: true }, anda: { frames: [], fps: 6, loop: true }, habla: { frames: [], fps: 6, loop: true } } }) },
  prop: { label: '🪑 道具 / 前景', def: () => ({ pivot: 'bottom', x: 126, y: 30, z: -10 }) },
  night: { label: '🌙 夜晚遮罩（晚上渐渐出现）', def: () => ({ pivot: 'center', x: 126, y: 87, z: -100, role: 'night' }) },
  vision: { label: '🟢 夜视才看得到', def: () => ({ pivot: 'center', x: 126, y: 87, z: -2, role: 'nightVisionOnly' }) },
};
const ROLES = { '': '一般', day: '白天才显示', night: '夜晚遮罩（入夜渐显）', tint: '入夜变暗', nightVision: '夜视时变化', nightVisionOnly: '只在夜视中看得到' };

function artTab(mod, id, d) {
  const own = mod.manifest.sceneTemplates.find(t => t.id === d.metadata.tmpContainer);
  const wrap = h('div', {});
  wrap.append(h('div', { class: 'help' },
    '在这里导入自己画的 PNG：背景、角色（逐格动画或 sprite sheet）、道具、夜晚遮罩，以及只有开夜视才看得到的东西。',
    '座标单位是画面像素（252×174，y 由下往上）。角色的锚点默认在脚底。勾选「清空原模板」就是完全自订的场景。',
    '动画名称 default / anda（走路）/ habla（说话）最常用；剧本动作的动画字段会自动列出这里的名称。'));
  if (!own) { wrap.append(h('div', { class: 'help' }, '这个笼子直接使用内置模板，无法加自订素材。请用「添加笼子」精灵创建的笼子。')); return wrap; }
  own.art = own.art || { cameras: [] };
  const cams = resolveTemplate(mod, d.metadata.tmpContainer).cameras;

  // Asset library.
  const lib = h('div', { class: 'card' });
  const folder = 'art/' + id + '/';
  const assets = Object.keys(mod.assets || {}).filter(p => p.startsWith('art/')).sort();
  const fileInput = h('input', { type: 'file', accept: 'image/png,image/jpeg', multiple: true, style: 'display:none', onchange: async e => {
    for (const f of e.target.files) {
      const safe = f.name.replace(/[^A-Za-z0-9_.-]/g, '_');
      mod.assets[folder + safe] = new Uint8Array(await f.arrayBuffer());
      mod.deleted.delete(folder + safe);
    }
    toast(`已导入 ${e.target.files.length} 张图片到 ${folder}`);
    changed(true);
  } });
  lib.append(h('div', { class: 'row' }, h('b', {}, '🗂 图片素材'), h('button', { class: 'primary', onclick: () => fileInput.click() }, '＋ 导入 PNG'), fileInput,
    h('span', { class: 'muted' }, `存放在 Mods/${mod.folder}/${folder}`)));
  const strip = h('div', { class: 'row', style: 'gap:8px' });
  for (const p of assets) {
    const url = assetURL(mod, p);
    strip.append(h('div', { class: 'tpl', style: 'width:120px;padding:4px', title: p },
      h('img', { src: url, style: 'max-height:70px;object-fit:contain;background:#444' }),
      h('div', { class: 'cap mono', style: 'font-size:10px;word-break:break-all' }, p.replace(/^art\//, '')),
      h('button', { class: 'small danger', onclick: () => { if (confirm('删除 ' + p + '？')) { delete mod.assets[p]; mod.deleted.add(p); changed(true); } } }, '删除')));
  }
  if (!assets.length) strip.append(h('span', { class: 'muted' }, '还没有图片。'));
  lib.append(strip);
  wrap.append(lib);

  cams.forEach((cam, ci) => {
    const a = own.art.cameras[ci] = own.art.cameras[ci] || { clear: false, objects: [] };
    a.objects = a.objects || [];
    const card = h('div', { class: 'card' });
    const view = { night: 0, vision: false };
    let pickTarget = null;
    const camNow = () => resolveTemplate(mod, d.metadata.tmpContainer).cameras[ci];
    const prevHolder = h('div', {});
    const drawPreview = () => {
      prevHolder.innerHTML = '';
      const p = cameraCanvas(camNow(), 3, null, () => ({ night: view.night, nightVision: view.vision }));
      p.style.cursor = pickTarget ? 'crosshair' : '';
      p.addEventListener('click', e => {
        if (!pickTarget) return;
        const r = p.getBoundingClientRect();
        pickTarget.x = Math.round((e.clientX - r.left) / 3); pickTarget.y = Math.round(VIEW_H - (e.clientY - r.top) / 3);
        pickTarget = null; changed(true);
      });
      prevHolder.append(p);
    };
    card.append(h('div', { class: 'row' }, h('b', {}, `镜头 ${ci + 1}`),
      h('label', { style: 'color:var(--text)' }, h('input', { type: 'checkbox', checked: !!a.clear, onchange: e => { a.clear = e.target.checked; changed(true); } }), ' 清空原模板对象（全自订场景）', tip('art.clear')),
      h('label', {}, '预览：'),
      h('select', { onchange: e => { view.night = +e.target.value; view.vision = e.target.value === '2'; if (view.vision) view.night = 1; drawPreview(); } },
        h('option', { value: '0' }, '白天'), h('option', { value: '1' }, '夜晚'), h('option', { value: '2' }, '夜晚 + 夜视'))));
    card.append(prevHolder);
    drawPreview();

    a.objects.forEach((o, oi) => card.append(artObjectCard(mod, a, o, oi, () => { pickTarget = o; drawPreview(); toast('在上方画面点一下选择位置'); })));
    const kindSel = h('select', {}, Object.entries(ART_KINDS).map(([k, v]) => h('option', { value: k }, v.label)));
    card.append(h('div', { class: 'row', style: 'margin-top:8px' }, kindSel, h('button', { onclick: () => {
      const base = ART_KINDS[kindSel.value].def();
      let name = kindSel.value, n = 2;
      while (a.objects.some(x => x.name === name) || camNow().objects.some(x => x.name === name && !x.custom)) name = kindSel.value + n++;
      const imgs = Object.keys(mod.assets || {}).filter(p => p.startsWith('art/'));
      if (!base.animations && imgs.length) base.image = imgs[0];
      a.objects.push(Object.assign({ name }, base));
      changed(true);
    } }, '＋ 添加对象')));
    wrap.append(card);
  });
  wrap.append(h('div', { class: 'help' }, '⚠ 自订对象在游戏里一开始都是显示状态；如果角色要晚点才登场，请在起始场景加入「🙈 隐藏」动作，再用「👁 显示」让它出场。'));
  return wrap;
}

function artObjectCard(mod, a, o, oi, onPick) {
  const imgs = Object.keys(mod.assets || {}).filter(p => p.startsWith('art/')).sort();
  const imgSelect = (val, onch, allowEmpty) => h('select', { onchange: e => onch(e.target.value) },
    allowEmpty ? h('option', { value: '' }, '（无）') : null, imgs.map(p => h('option', { value: p, selected: p === val }, p.replace(/^art\//, ''))),
    val && !imgs.includes(val) ? h('option', { value: val, selected: true }, val + '（找不到）') : null);
  const card = h('div', { class: 'action', style: 'border-left-color:#ff9f6b' });
  const isAnim = !!o.animations;
  card.append(h('div', { class: 'head' },
    h('input', { value: o.name, style: 'width:120px;font-weight:bold', title: '对象名称（剧本动作用这个名字）', onchange: e => {
      const nn = e.target.value.trim(); if (!/^[A-Za-z][A-Za-z0-9_]*$/.test(nn)) { alert('名称只能用英文、数字、底线，且以字母开头'); e.target.value = o.name; return; }
      o.name = nn; changed(true);
    } }),
    h('span', { class: 'muted' }, isAnim ? '动画对象' : '静态图片'),
    h('div', { class: 'tools' },
      h('button', { class: 'small', onclick: () => { if (oi > 0) { [a.objects[oi - 1], a.objects[oi]] = [a.objects[oi], a.objects[oi - 1]]; changed(true); } } }, '↑'),
      h('button', { class: 'small', onclick: () => { if (oi < a.objects.length - 1) { [a.objects[oi + 1], a.objects[oi]] = [a.objects[oi], a.objects[oi + 1]]; changed(true); } } }, '↓'),
      h('button', { class: 'small danger', onclick: () => { if (confirm('删除对象 ' + o.name + '？')) { a.objects.splice(oi, 1); changed(true); } } }, '✕'))));
  const body = h('div', { class: 'body' });
  const num = (k, label, step, key) => h('div', { class: 'field' }, lbl(label, key), h('input', { type: 'number', step: step || 1, value: o[k] ?? '', oninput: e => { o[k] = +e.target.value; changed(); }, onchange: () => changed(true) }));
  body.append(num('x', 'x'), num('y', 'y'), num('z', 'z（前后层次）', 'any', 'art.z'),
    h('div', { class: 'field' }, h('label', {}, '位置'), h('button', { class: 'small', onclick: onPick }, '📍 在画面上选')),
    h('div', { class: 'field' }, lbl('锚点', 'art.pivot'), h('select', { onchange: e => { o.pivot = e.target.value; changed(true); } },
      [['bottom', '脚底（角色）'], ['center', '中心（背景）'], ['top', '顶端'], ['bottomLeft', '左下角']].map(([k, v]) => h('option', { value: k, selected: (o.pivot || 'bottom') === k }, v)))),
    h('div', { class: 'field' }, lbl('日夜用途', 'art.role'), h('select', { onchange: e => { if (e.target.value) o.role = e.target.value; else delete o.role; changed(true); } },
      Object.entries(ROLES).map(([k, v]) => h('option', { value: k, selected: (o.role || '') === k }, v)))),
    h('div', { class: 'field' }, lbl('水平翻转', 'art.flip'), h('input', { type: 'checkbox', checked: !!o.flip, onchange: e => { o.flip = e.target.checked; changed(true); } })),
    (() => {
      // Clickable: the player clicks this object in the camera view to collect a keyword.
      const d = cageData(project.mods[ui.mod], ui.cage) || {};
      const kws = Object.keys(d.keywords || {}).filter(x => !x.includes(',') && !x.includes('_'));
      return h('div', { class: 'field' }, lbl('可点击关键字', 'art.keyword'), h('select', { onchange: e => { if (e.target.value) o.keyword = e.target.value; else delete o.keyword; changed(true); } },
        h('option', { value: '' }, '（不可点击）'), kws.map(k => h('option', { value: k, selected: o.keyword === k }, k)),
        o.keyword && !kws.includes(o.keyword) ? h('option', { value: o.keyword, selected: true }, o.keyword + '（不存在）') : null));
    })());
  if (!isAnim) {
    body.append(h('div', { class: 'field' }, h('label', {}, '图片'), imgSelect(o.image, v => { o.image = v; changed(true); })),
      h('div', { class: 'field' }, h('label', {}, '　'), h('button', { class: 'small', onclick: () => { o.animations = { default: { frames: o.image ? [o.image] : [], fps: 4, loop: true } }; delete o.image; changed(true); } }, '改成动画对象')));
  } else {
    o.sheet = o.sheet || null;
    const useSheet = !!o.sheet;
    body.append(h('div', { class: 'field' }, h('label', {}, '影格来源'), h('select', { onchange: e => {
      if (e.target.value === 'sheet') o.sheet = { image: imgs[0] || '', w: 32, h: 48 }; else delete o.sheet;
      changed(true);
    } }, h('option', { value: 'files', selected: !useSheet }, '多张 PNG（一张一格）'), h('option', { value: 'sheet', selected: useSheet }, 'Sprite sheet（一张切格）'))));
    if (useSheet) {
      body.append(h('div', { class: 'field' }, h('label', {}, 'Sheet 图片'), imgSelect(o.sheet.image, v => { o.sheet.image = v; changed(true); })),
        h('div', { class: 'field' }, h('label', {}, '每格宽'), h('input', { type: 'number', value: o.sheet.w, onchange: e => { o.sheet.w = +e.target.value; changed(true); } })),
        h('div', { class: 'field' }, h('label', {}, '每格高'), h('input', { type: 'number', value: o.sheet.h, onchange: e => { o.sheet.h = +e.target.value; changed(true); } })));
      body.append(sheetStrip(mod, o));
    }
    const anims = o.animations;
    const animBox = h('div', { style: 'width:100%' }, lbl('动画（名称、影格、每秒几格、是否循环）', 'art.frames'));
    for (const [an, ad] of Object.entries(anims)) {
      const framesText = (ad.frames || []).map(f => typeof f === 'number' ? f : f.replace(/^art\//, '')).join(', ');
      const thumb = h('canvas', { width: 64, height: 64, style: 'background:#333;image-rendering:pixelated' });
      const tick = () => {
        if (!thumb.isConnected) return;
        const t = performance.now() / 1000;
        const f = artFrame(mod, o, artAnimFrame(o, an, ad.loop === false ? t % ((ad.frames.length || 1) / (ad.fps || 6) + 0.6) : t));
        const c = thumb.getContext('2d'); c.imageSmoothingEnabled = false; c.clearRect(0, 0, 64, 64);
        if (f) { const s = Math.min(64 / f.sw, 64 / f.sh); c.drawImage(f.img, f.sx, f.sy, f.sw, f.sh, (64 - f.sw * s) / 2, 64 - f.sh * s, f.sw * s, f.sh * s); }
        requestAnimationFrame(tick);
      };
      requestAnimationFrame(tick);
      animBox.append(h('div', { class: 'row' }, thumb,
        h('input', { value: an, style: 'width:90px', onchange: e => {
          const nn = e.target.value.trim(); if (!nn || anims[nn]) { e.target.value = an; return; }
          const rebuilt = {}; for (const [k, v] of Object.entries(anims)) rebuilt[k === an ? nn : k] = v; o.animations = rebuilt; changed(true);
        } }),
        h('input', { value: framesText, style: 'flex:1;min-width:200px', placeholder: useSheet ? '格子编号，例如 0, 1, 2' : '文件名，例如 ghostRoom/walk1.png, ghostRoom/walk2.png', onchange: e => {
          ad.frames = e.target.value.split(',').map(s => s.trim()).filter(Boolean).map(s => /^\d+$/.test(s) && useSheet ? +s : (s.startsWith('art/') ? s : 'art/' + s));
          changed(true);
        } }),
        h('label', {}, 'fps'), h('input', { type: 'number', step: 'any', value: ad.fps ?? 6, style: 'width:60px', onchange: e => { ad.fps = +e.target.value; changed(true); } }),
        h('label', { style: 'color:var(--text)' }, h('input', { type: 'checkbox', checked: ad.loop !== false, onchange: e => { ad.loop = e.target.checked; changed(true); } }), ' 循环'),
        h('button', { class: 'small danger', onclick: () => { delete anims[an]; changed(true); } }, '✕')));
    }
    animBox.append(h('button', { class: 'small', onclick: () => { let n = 'anim', i = 1; while (anims[n + i]) i++; anims[n + i] = { frames: [], fps: 6, loop: true }; changed(true); } }, '＋ 动画'));
    if (!useSheet && imgs.length) animBox.append(h('div', { class: 'muted', style: 'font-size:11px' }, '可用文件名：' + imgs.map(p => p.replace(/^art\//, '')).join('、')));
    body.append(animBox);
  }
  card.append(body);
  return card;
}

/** Thumbnails of every cell of a sprite sheet, numbered, so frame lists are easy to type. */
function sheetStrip(mod, o) {
  const box = h('div', { style: 'width:100%' });
  const img = loadImg(assetURL(mod, o.sheet.image));
  if (!img || !o.sheet.w || !o.sheet.h) { box.append(h('span', { class: 'muted' }, '（选择 sheet 图片并填好每格大小后会显示切格）')); return box; }
  const cols = Math.floor(img.naturalWidth / o.sheet.w), rows = Math.floor(img.naturalHeight / o.sheet.h);
  const strip = h('div', { class: 'row', style: 'gap:4px' });
  for (let i = 0; i < cols * rows; i++) {
    const c = h('canvas', { width: o.sheet.w * 2, height: o.sheet.h * 2, style: 'background:#333;image-rendering:pixelated' });
    const ctx = c.getContext('2d'); ctx.imageSmoothingEnabled = false;
    ctx.drawImage(img, (i % cols) * o.sheet.w, Math.floor(i / cols) * o.sheet.h, o.sheet.w, o.sheet.h, 0, 0, o.sheet.w * 2, o.sheet.h * 2);
    strip.append(h('div', { style: 'text-align:center;font-size:11px' }, c, h('div', {}, i)));
  }
  box.append(h('label', {}, `切格结果（${cols}×${rows}），动画影格填这些编号：`), strip);
  return box;
}

// ------------------------------------------------------------------ validation for art

function validateArt(mod, mi, add) {
  for (const st of mod.manifest.sceneTemplates) {
    if (!st.art || !Array.isArray(st.art.cameras)) continue;
    const nav = { mod: mi, cage: st.id, tab: 'art' };
    st.art.cameras.forEach((a, ci) => {
      const names = new Set();
      for (const o of (a && a.objects) || []) {
        const where = `镜头 ${ci + 1}「${o.name}」`;
        if (names.has(o.name)) add('err', `${where}：对象名称重复。`, st.id, nav);
        names.add(o.name);
        const need = p => { if (typeof p === 'string' && !(mod.assets || {})[p]) add('err', `${where}：找不到图片 ${p}。`, st.id, nav); };
        need(o.image);
        if (o.sheet) { need(o.sheet.image); if (!(+o.sheet.w > 0 && +o.sheet.h > 0)) add('err', `${where}：sprite sheet 要填每格宽高。`, st.id, nav); }
        if (!o.image && !o.animations) add('err', `${where}：没有图片也没有动画。`, st.id, nav);
        if (o.keyword) {
          const d = cageData(mod, st.id) || {};
          if (!(d.keywords || {})[o.keyword]) add('err', `${where}：可点击关键字「${o.keyword}」没有在「关键字」定义。`, st.id, nav);
        }
        for (const [an, ad] of Object.entries(o.animations || {})) {
          if (!ad.frames || !ad.frames.length) add('err', `${where}：动画「${an}」没有影格。`, st.id, nav);
          for (const f of ad.frames || []) { if (typeof f === 'number' && !o.sheet) add('err', `${where}：动画「${an}」用了格子编号，但没有设置 sprite sheet。`, st.id, nav); need(f); }
        }
      }
    });
  }
}
