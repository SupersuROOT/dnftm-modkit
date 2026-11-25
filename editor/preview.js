/* DNFTM Mod Editor - live scene preview: simulates a scene's actions on a timeline. */
'use strict';

/**
 * Approximations of the game's timing (genericConfig.textSpeed: base 1s + 0.04s per character + 0.1s per word).
 * Template animations have unknown lengths, so waitFinish on them assumes 1.2 s.
 */
function sayDuration(text) {
  const t = stripMarkup(text || '');
  const words = t.split(/\s+/).filter(Boolean).length;
  return 1 + 0.04 * t.length + 0.1 * words;
}

/** Turns an action list into timed steps: {start, end, a, index, depthPath}. Groups run in parallel. */
function scheduleActions(list, ctx, t0, out, path, depth) {
  let t = t0;
  (list || []).forEach((a, i) => {
    const p = path.concat(i);
    if (Array.isArray(a.actions) && !a.action) {
      let end = t;
      for (const sub of a.actions) end = Math.max(end, scheduleActions([sub], ctx, t, out, p, depth));
      t = end;
      return;
    }
    if (a.action === 'predefinedAction') {
      const pd = (ctx.predef || {})[a.name];
      out.push({ start: t, end: t, a, path: p, top: depth === 0 ? i : null });
      if (pd && depth < 6) t = scheduleActions(pd, ctx, t, out, p, depth + 1);
      return;
    }
    let dur = 0;
    switch (a.action) {
      case 'move': dur = +a.time || 0; break;
      case 'wait': dur = +a.time || 0; break;
      case 'say': dur = sayDuration(ctx.textOf(a.text)); break;
      case 'animation': {
        if (a.waitFinish) {
          const o = ctx.objects.find(x => x.name === a.id);
          dur = o && o.custom ? artClipDuration(o.art, a.animation) || 0.5 : 1.2;
        }
        break;
      }
    }
    out.push({ start: t, end: t + dur, a, path: p, top: depth === 0 ? i : null });
    t += dur;
  });
  return t;
}

/** Object state at time `time` after applying steps (state is mutated from `init`). */
function stateAt(steps, init, time, ctx) {
  const objs = {};
  for (const [k, v] of Object.entries(init)) objs[k] = Object.assign({}, v);
  const bubbles = [];
  let led = false, current = null;
  for (const s of steps) {
    if (s.start > time) break;
    const a = s.a;
    if (s.top !== null) current = s; // latest top-level action that has started
    if (a.action === 'blinkLed') { led = true; continue; }
    if (a.action === 'stopLed' || a.action === 'stopkLed') { led = false; continue; }
    if (!a.id) continue;
    const o = objs[a.id] = objs[a.id] || { x: 126, y: 20, visible: true, t0: 0 };
    const k = Math.min(1, s.end > s.start ? (time - s.start) / (s.end - s.start) : 1);
    const running = time < s.end;
    const setAnim = (name, at) => { if (o && name && o.anim !== name) { o.anim = name; o.t0 = at; } };
    switch (a.action) {
      case 'enable': o.visible = true; break;
      case 'disable': case 'fullDisable': o.visible = false; break;
      case 'fullEnable': o.visible = true; break;
      case 'setin': if (a.position) { o.x = +a.position.x; o.y = +a.position.y; } break;
      case 'flip': o.flip = a.direction; break;
      case 'move': {
        if (s.fromX === undefined) { s.fromX = o.x; s.fromY = o.y; }
        const tx = a.position ? +a.position.x : o.x, ty = a.position ? +a.position.y : o.y;
        o.x = s.fromX + (tx - s.fromX) * k; o.y = s.fromY + (ty - s.fromY) * k;
        if (a.flip) o.flip = a.flip;
        if (running) setAnim(a.subanimation, s.start); else setAnim(a.endAnimation || a.endanimation, s.end);
        break;
      }
      case 'animation': setAnim(a.animation, s.start); if (a.flip) o.flip = a.flip; break;
      case 'say':
        if (running) { setAnim(a.subanimation, s.start); bubbles.push({ id: a.id, text: ctx.textOf(a.text) }); }
        else setAnim(a.endanimation || a.endAnimation, s.end);
        break;
      case 'blinkLed': led = true; break;
      case 'stopLed': case 'stopkLed': led = false; break;
    }
  }
  for (const o of Object.values(objs)) o.t = Math.max(0, time - (o.t0 || 0));
  return { objects: objs, bubbles, led, current };
}

/** Initial object state for a scene: template defaults, then earlier scenes of the same camera fast-forwarded. */
function initialState(d, sceneName, cam, ctx) {
  const init = {};
  for (const o of cam.objects) if (o.depth === 0 && (o.anims || o.custom)) init[o.name] = { x: o.x, y: o.y, visible: o.active !== false, flip: o.art && o.art.flip ? 'left' : undefined, t0: 0 };
  const scenes = d.script.scenes, smd = d.script.metadata;
  const camNo = +(scenes[sceneName] || {}).camera || 1;
  const startKey = camNo === 1 ? 'startScene' : 'startScene' + camNo;
  let cur = smd[startKey];
  const seen = new Set();
  let state = { objects: init };
  while (cur && scenes[cur] && cur !== sceneName && !seen.has(cur)) {
    seen.add(cur);
    if ((+scenes[cur].camera || 1) === camNo) {
      const steps = []; const end = scheduleActions(scenes[cur].script, ctx, 0, steps, [], 0);
      const st = stateAt(steps, state.objects, end + 0.001, ctx);
      for (const o of Object.values(st.objects)) { o.t0 = -1000; }
      state = st;
    }
    cur = scenes[cur].goto;
  }
  return state.objects;
}

function wrapText(ctx, text, maxW) {
  const lines = [];
  for (const para of text.split('|')) {
    let line = '';
    for (const ch of para) {
      const test = line + ch;
      if (ctx.measureText(test).width > maxW && line) {
        // break at the last space for Latin text
        const sp = line.lastIndexOf(' ');
        if (sp > 0 && /[A-Za-z]/.test(ch)) { lines.push(line.slice(0, sp)); line = line.slice(sp + 1) + ch; }
        else { lines.push(line); line = ch; }
      } else line = test;
    }
    lines.push(line);
  }
  return lines;
}

function drawBubbles(c, st, scale, keywordColor) {
  c.font = `bold ${Math.round(3.6 * scale)}px "Microsoft JhengHei", "PingFang TC", sans-serif`;
  c.textAlign = 'center';
  for (const b of st.bubbles) {
    const o = st.objects[b.id] || { x: 126, y: 30 };
    const lines = wrapText(c, stripMarkup(b.text), 90 * scale);
    const lh = 4.4 * scale;
    let y = (VIEW_H - o.y - 52) * scale - (lines.length - 1) * lh;
    y = Math.max(lh, y);
    const x = Math.min(Math.max(o.x * scale, 46 * scale), (VIEW_W - 46) * scale);
    lines.forEach((ln, i) => {
      c.lineWidth = scale * 0.9; c.strokeStyle = '#000'; c.strokeText(ln, x, y + i * lh);
      c.fillStyle = '#fff'; c.fillText(ln, x, y + i * lh);
    });
  }
}

/** Builds the preview panel for one scene. */
function scenePreview(mod, id, d, sceneName, cams) {
  const sc = d.script.scenes[sceneName];
  const cam = cams[(+sc.camera || 1) - 1];
  const panel = h('div', { class: 'card' });
  if (!cam) return panel;
  const scale = 3;
  let lang = 'ch', speed = 1, playing = false, time = 0, nightMode = 0;
  const ctxSim = {
    objects: cam.objects,
    predef: d.script.predefinedActions || {},
    textOf: raw => {
      const r = parseRef(raw);
      if (!r) return raw || '';
      return getLoc(mod, lang, r.section, r.num) || getLoc(mod, 'en', r.section, r.num) || r.fallback;
    },
  };
  let steps = [], total = 0, init = {};
  const rebuild = () => {
    steps = []; total = scheduleActions(sc.script, ctxSim, 0, steps, [], 0);
    init = initialState(d, sceneName, cam, ctxSim);
    slider.max = String(Math.max(0.1, total));
  };
  const cv = h('canvas', { width: VIEW_W * scale, height: VIEW_H * scale, style: 'display:block;image-rendering:pixelated;max-width:100%' });
  const info = h('span', { class: 'muted mono', style: 'font-size:12px' });
  const slider = h('input', { type: 'range', min: 0, max: 1, step: 0.01, value: 0, style: 'flex:1', oninput: e => { time = +e.target.value; playing = false; playBtn.textContent = '▶ 播放'; draw(); } });
  const playBtn = h('button', { class: 'primary', onclick: () => { if (time >= total) time = 0; playing = !playing; playBtn.textContent = playing ? '⏸ 暂停' : '▶ 播放'; last = performance.now(); if (playing) requestAnimationFrame(loop); } }, '▶ 播放');
  const draw = () => {
    const st = stateAt(steps, init, time, ctxSim);
    const c = cv.getContext('2d');
    renderCamera(c, cam, scale, st, { night: nightMode >= 1 ? 1 : 0, nightVision: nightMode === 2 });
    drawBubbles(c, st, scale);
    if (st.led) { c.fillStyle = '#ff3030'; c.beginPath(); c.arc(VIEW_W * scale - 18, 18, 7, 0, Math.PI * 2); c.fill(); }
    slider.value = String(time);
    info.textContent = `${time.toFixed(1)} / ${total.toFixed(1)} 秒` + (st.current ? `　#${st.current.top !== null ? st.current.top + 1 : '?'} ${st.current.a.action}` : '');
    // highlight the running top-level action in the list
    document.querySelectorAll('.sceneedit .action.playing').forEach(e => e.classList.remove('playing'));
    if (st.current && st.current.top !== null) {
      const el = document.querySelectorAll('.sceneedit > div > div > .action')[st.current.top];
      if (el) el.classList.add('playing');
    }
  };
  let last = 0;
  const loop = now => {
    if (!playing || !cv.isConnected) return;
    time = Math.min(total, time + (now - last) / 1000 * speed);
    last = now;
    draw();
    if (time >= total) { playing = false; playBtn.textContent = '▶ 播放'; return; }
    requestAnimationFrame(loop);
  };
  rebuild();
  redrawHooks.add(() => { if (cv.isConnected && !playing) draw(); });
  panel.append(h('div', { class: 'row' }, h('b', {}, '▶ 即时预览'), playBtn,
    h('button', { onclick: () => { time = 0; draw(); } }, '⏮'),
    h('label', {}, '速度'), h('select', { onchange: e => { speed = +e.target.value; } }, [1, 2, 4, 8].map(v => h('option', { value: v }, v + '×'))),
    h('label', {}, '语言'), h('select', { onchange: e => { lang = e.target.value; draw(); } }, h('option', { value: 'ch' }, '简中'), h('option', { value: 'en' }, 'English')),
    h('label', {}, '光线'), h('select', { onchange: e => { nightMode = +e.target.value; draw(); } }, h('option', { value: 0 }, '白天'), h('option', { value: 1 }, '夜晚'), h('option', { value: 2 }, '夜视'))));
  panel.append(cv, h('div', { class: 'row', style: 'margin-top:6px' }, slider, info));
  panel.append(h('div', { class: 'muted', style: 'font-size:11px' },
    '预览是近似仿真：条件 (if/ifNot) 一律当作成立；内置角色显示默认姿势并标出目前动画名称，自订素材会播放真正的影格；对白时间依游戏的文本速度估算。'));
  panel.refresh = () => { rebuild(); time = Math.min(time, total); draw(); };
  draw();
  return panel;
}
