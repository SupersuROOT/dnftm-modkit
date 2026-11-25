/* DNFTM Mod Editor - core: data model, file IO, zip export, strings, validation.
 * Works on the folder layout read by DNFTMModLoader:
 *   Mods/<Mod>/mod.json, Mods/<Mod>/files/<path>, Mods/<Mod>/merge/<path>
 */
'use strict';

const CAT = window.DNFTM_CATALOG;
const GLYPHS = new Set(CAT.glyphs);
const T2S = CAT.t2s;
const BUILTIN_CAGES = new Set(CAT.cages.map(c => c.id.toLowerCase()));
const TEMPLATE_BY_ID = Object.fromEntries(CAT.templates.map(t => [t.id, t]));
/** Templates that have at least one camera (Story0 is the empty placeholder used by the hidden 'empty' cage). */
const USABLE_TEMPLATES = CAT.templates.filter(t => t.cameras.length);
const DIARY_BY_ID = Object.fromEntries(CAT.diaryPages.map(p => [p.id, p]));
const LANGS = ['en', 'ch'];

// ------------------------------------------------------------------ tolerant JSON

/** Parses JSON that may contain // and /* *\/ comments and trailing commas (the mod loader accepts both). */
function parseLoose(text) {
  if (text.charCodeAt(0) === 0xFEFF) text = text.slice(1);
  let out = '', i = 0, inStr = false;
  while (i < text.length) {
    const c = text[i];
    if (inStr) {
      out += c;
      if (c === '\\') { out += text[i + 1] || ''; i += 2; continue; }
      if (c === '"') inStr = false;
      i++; continue;
    }
    if (c === '"') { inStr = true; out += c; i++; continue; }
    if (c === '/' && text[i + 1] === '/') { while (i < text.length && text[i] !== '\n') i++; continue; }
    if (c === '/' && text[i + 1] === '*') { const e = text.indexOf('*/', i + 2); i = e < 0 ? text.length : e + 2; continue; }
    if (c === ',') {
      let j = i + 1;
      while (j < text.length && /\s/.test(text[j])) j++;
      if (text[j] === '}' || text[j] === ']') { i++; continue; }
    }
    out += c; i++;
  }
  return JSON.parse(out);
}

const pretty = obj => JSON.stringify(obj, null, 2) + '\n';
const clone = obj => JSON.parse(JSON.stringify(obj));

// ------------------------------------------------------------------ images (ModLoader 0.5+: mods/<Mod>/<file>)

/** Every image path a browser result uses (news, Metayou avatar and posts, wiki pictures, map, web page images). */
function browserImages(r) {
  const out = [];
  for (const f of ['image', 'imageHeader', 'imageBottom']) if (r[f]) out.push(r[f]);
  for (const p of r.posts || []) if (p.image) out.push(p.image);
  for (const s of r.struct || []) if (s.image) out.push(s.image);
  return out;
}

/** True when a game image path exists: a built-in Resources image, or "mods/<ModFolder>/<file>" = a PNG in that mod. */
function imageExists(path) {
  const m = /(?:^|\/)mods\/([^/]+)\/(.+)$/i.exec(path || '');
  if (m) {
    const mod = project.mods.find(x => x.folder.toLowerCase() === m[1].toLowerCase());
    const rel = m[2].replace(/\.png$/i, '');
    return !!mod && Object.keys(mod.assets).some(a => a.toLowerCase() === (rel + '.png').toLowerCase());
  }
  return CAT.images.includes((path || '').toLowerCase());
}

/** The mod's own PNGs as game image paths (for the image pickers); sprite art under art/ is left out. */
function modImagePaths() {
  const out = [];
  for (const mod of project.mods) for (const a of Object.keys(mod.assets))
    if (/\.png$/i.test(a) && !/^art\//i.test(a)) out.push('mods/' + mod.folder + '/' + a.replace(/\.png$/i, ''));
  return out;
}

// ------------------------------------------------------------------ project model

/**
 * project = { dir: FileSystemDirectoryHandle|null, readOnly: bool, mods: [Mod] }
 * Mod = { folder, manifest, files: {relPath: object|string}, merges: {relPath: object}, deleted: Set<string> }
 * relPath keys are relative to files/ or merge/. JSON files are kept parsed; other files as text.
 */
const project = { dir: null, readOnly: false, mods: [] };

function newMod(folder) {
  // assets: binary files elsewhere in the mod folder (custom art), keyed by path relative to the mod folder
  return { folder, manifest: { name: folder, cages: [], sceneTemplates: [], cameraEffects: [], diaryPages: [] }, files: {}, merges: {}, assets: {}, deleted: new Set() };
}

// Objects on the game's prize shelf (prizeHolderItems/<id>); a mod prize can copy one of them.
const GAME_PRIZE_OBJECTS = ['coca', 'calavera', 'flores1', 'flores2', 'flores3', 'ladrillo', 'luces', 'pierna', 'radiografia', 'urna', 'pastel', 'biblia',
  'freedoniaGorra', 'sheWolfPeluca', 'cryingGameTrofeo', 'elevatorCrusoeMuneco', 'deerEstherCiervo', 'ethanEdgeDisco', 'autumnPlaceLatigo',
  'lostInSpaceParaguas', 'huevo', 'huevoFalso', 'sayCheeseFotografiaX', 'sayCheeseFotografia1', 'sayCheeseFotografia2', 'sayCheeseFotografia3',
  'snDiabolicDollmuneco1', 'snDiabolicDollmuneco2', 'snDiabolicDollmuneco3'];

// The public release of the editor has no game pictures in catalog.js (they are the game's own art). The scene
// previews come back after running tools/build_catalog.py on your own copy of the game (see README).
const NO_PREVIEW = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(
  '<svg xmlns="http://www.w3.org/2000/svg" width="252" height="174"><rect width="252" height="174" fill="#3a3f45"/>' +
  '<text x="126" y="82" fill="#c8ccd0" font-size="13" text-anchor="middle" font-family="sans-serif">没有预览图</text>' +
  '<text x="126" y="102" fill="#9aa0a6" font-size="10" text-anchor="middle" font-family="sans-serif">用 build_catalog.py 从游戏提取</text></svg>');
function previewSrc(u) { return u || NO_PREVIEW; }

// ------------------------------------------------------------------ loader versions
// The newest ModLoader the editor knows, and the first loader version of each feature a mod can use.
const LOADER_LATEST = '0.5.10';
function verCmp(a, b) {
  const pa = String(a || '0').split('.').map(Number), pb = String(b || '0').split('.').map(Number);
  for (let i = 0; i < 3; i++) { const d = (pa[i] || 0) - (pb[i] || 0); if (d) return d; }
  return 0;
}
/** [version, reason] pairs for the loader features a mod uses; the highest one is the minLoader it needs. */
function loaderNeeds(mod) {
  const M = mod.manifest, out = [['0.5.0', 'mod 自己的图片（mods/<Mod>/...）']];
  for (const p of M.diaryPages || []) {
    if (p.actions && Object.keys(p.actions).length) out.push(['0.5.3', '笔记本电话/聊天按钮（actions）']);
    if (p.main || (p.upper && p.upper.length) || (p.copies && p.copies.length)) out.push(['0.5.4', '笔记本 main / upper / copies']);
    if (p.selectors && Object.keys(p.selectors).length) out.push(['0.5.5', '笔记本推理「？」（selectors）']);
    if (p.moves && p.moves.length) out.push(['0.5.6', '移动笔记本元素（moves）']);
    if ([...(p.moves || []), ...(p.copies || [])].some(m => (m.sx !== undefined && m.sx !== 1) || (m.sy !== undefined && m.sy !== 1)))
      out.push(['0.5.9', '放大或缩小笔记本元素（sx / sy）']);
  }
  if ((M.prizes || []).length) out.push(['0.5.10', '物品架上的自订物品（prizes）']);
  return out;
}
function requiredLoader(mod) { return loaderNeeds(mod).reduce((best, [v]) => verCmp(v, best) > 0 ? v : best, '0.5.0'); }
/** On save: raise minLoader to what the mod needs (never lowers a version the author set by hand). */
function autoMinLoader(mod) {
  const need = requiredLoader(mod);
  if (!mod.manifest.minLoader || verCmp(need, mod.manifest.minLoader) > 0) mod.manifest.minLoader = need;
}

function ensureManifestArrays(m) {
  for (const k of ['cages', 'sceneTemplates', 'cameraEffects', 'diaryPages']) if (!Array.isArray(m[k])) m[k] = [];
}

/** Cage ids defined by a mod: manifest cages that also have files/<id>.json. */
function modCages(mod) {
  return mod.manifest.cages.map(c => c.id).filter(id => mod.files[id + '.json'] && typeof mod.files[id + '.json'] === 'object');
}

function cageData(mod, id) { return mod.files[id + '.json']; }

// ------------------------------------------------------------------ reading

async function readHandleTree(dirHandle, prefix, out) {
  for await (const [name, h] of dirHandle.entries()) {
    const p = prefix ? prefix + '/' + name : name;
    if (h.kind === 'directory') await readHandleTree(h, p, out);
    else out.push({ path: p, file: () => h.getFile() });
  }
}

/** Builds mods from a flat list of {path, file()} where path starts with <ModFolder>/... */
async function loadModsFromEntries(entries) {
  const byMod = {};
  for (const e of entries) {
    const parts = e.path.split('/');
    if (parts.length < 2) continue;
    const folder = parts[0];
    if (folder.startsWith('.')) continue;
    (byMod[folder] = byMod[folder] || []).push({ rel: parts.slice(1).join('/'), file: e.file });
  }
  const mods = [];
  for (const folder of Object.keys(byMod).sort((a, b) => a.localeCompare(b))) {
    const mod = newMod(folder);
    let hasManifest = false;
    for (const f of byMod[folder]) {
      if (/\.(png|jpe?g|gif|webp)$/i.test(f.rel)) { mod.assets[f.rel] = new Uint8Array(await (await f.file()).arrayBuffer()); continue; }
      const text = await (await f.file()).text();
      const isJson = /\.json$/i.test(f.rel);
      let data = text;
      if (isJson) {
        try { data = parseLoose(text); }
        catch (err) { data = text; toast('无法解析 ' + folder + '/' + f.rel + '：' + err.message, true); }
      }
      if (f.rel === 'mod.json') { if (typeof data === 'object') { mod.manifest = data; hasManifest = true; } }
      else if (f.rel.startsWith('files/')) mod.files[f.rel.slice(6)] = data;
      else if (f.rel.startsWith('merge/')) mod.merges[f.rel.slice(6)] = data;
    }
    if (!hasManifest && !Object.keys(mod.files).length && !Object.keys(mod.merges).length && !Object.keys(mod.assets).length) continue;
    ensureManifestArrays(mod.manifest);
    mods.push(mod);
  }
  return mods;
}

/** Lets the user pick the game folder, the Mods folder, or one mod folder (read-write). */
async function openFolderRW() {
  let h = await window.showDirectoryPicker({ mode: 'readwrite', id: 'dnftm-mods' });
  // Game folder -> its Mods subfolder (created if missing).
  let isGame = false;
  for await (const [name, child] of h.entries()) if (child.kind === 'directory' && /_Data$/i.test(name)) isGame = true;
  if (isGame) h = await h.getDirectoryHandle('Mods', { create: true });
  // A single mod folder (contains mod.json) -> ask for its parent instead.
  try { await h.getFileHandle('mod.json'); throw new Error('你选到的是单一个 mod 文件夹，请改选它上一层的 Mods 文件夹（或游戏文件夹）。'); }
  catch (e) { if (e.name !== 'NotFoundError' && e.name !== 'TypeMismatchError') throw e; }
  const entries = [];
  await readHandleTree(h, '', entries);
  project.dir = h;
  project.readOnly = false;
  project.mods = await loadModsFromEntries(entries.filter(e => !/^ModLoader\.log$/.test(e.path)));
}

/** Fallback for browsers without the File System Access API: <input webkitdirectory>. Read-only. */
async function importFromFileList(fileList) {
  const files = Array.from(fileList);
  if (!files.length) return;
  // Strip the picked root folder name; if it is the game folder, also strip "Mods/".
  let entries = files.map(f => ({ path: f.webkitRelativePath.split('/').slice(1).join('/'), file: async () => f }));
  if (entries.some(e => e.path.startsWith('Mods/'))) entries = entries.filter(e => e.path.startsWith('Mods/')).map(e => ({ ...e, path: e.path.slice(5) }));
  project.dir = null;
  project.readOnly = true;
  project.mods = await loadModsFromEntries(entries);
}

// ------------------------------------------------------------------ writing

/** Editing forms add empty lists so they can show them (events of a conversation node, its options, a keyword's
 * search results). Leave those out of the saved file: they mean the same as "not there", and a saved cage should
 * only change where the author changed it. */
const EMPTY_DROPPABLE = new Set(['onInitTalk', 'onFinishTalk', 'onCallEnd', 'texts', 'events', 'startEvents', 'finishEvents', 'onOpen', 'onDelete', 'onExpire']);
function withoutEmptyFields(x) {
  if (Array.isArray(x)) return x.map(withoutEmptyFields);
  if (!x || typeof x !== 'object') return x;
  const out = {};
  for (const [k, v] of Object.entries(x)) {
    if (EMPTY_DROPPABLE.has(k) && Array.isArray(v) && !v.length) continue;
    if (k === 'browser' && v && typeof v === 'object' && Array.isArray(v.data) && !v.data.length && Object.keys(v).length === 1) continue;
    out[k] = withoutEmptyFields(v);
  }
  return out;
}

function modOutputFiles(mod) {
  autoMinLoader(mod);
  const out = [{ path: 'mod.json', text: pretty(mod.manifest) }];
  for (const [p, d] of Object.entries(mod.files)) out.push({ path: 'files/' + p, text: typeof d === 'string' ? d : pretty(withoutEmptyFields(d)) });
  for (const [p, d] of Object.entries(mod.merges)) {
    // skip merge files the editor created but left empty (e.g. endings.json with no frames)
    if (d && typeof d === 'object' && Object.values(d).every(v => v && typeof v === 'object' && !Object.keys(v).length)) continue;
    out.push({ path: 'merge/' + p, text: typeof d === 'string' ? d : pretty(d) });
  }
  // Binary assets (custom art); "text" may be a Uint8Array, which writeFile and makeZip both accept.
  for (const [p, d] of Object.entries(mod.assets || {})) out.push({ path: p, text: d });
  return out;
}

async function writeFile(dir, path, text) {
  const parts = path.split('/');
  let d = dir;
  for (const p of parts.slice(0, -1)) d = await d.getDirectoryHandle(p, { create: true });
  const fh = await d.getFileHandle(parts[parts.length - 1], { create: true });
  const w = await fh.createWritable();
  await w.write(text);
  await w.close();
}

async function removeFile(dir, path) {
  const parts = path.split('/');
  let d = dir;
  try {
    for (const p of parts.slice(0, -1)) d = await d.getDirectoryHandle(p);
    await d.removeEntry(parts[parts.length - 1]);
  } catch (e) { /* already gone */ }
}

async function saveToFolder() {
  if (!project.dir) throw new Error('没有打开可写入的文件夹，请改用「导出 zip」。');
  if ((await project.dir.queryPermission({ mode: 'readwrite' })) !== 'granted') {
    if ((await project.dir.requestPermission({ mode: 'readwrite' })) !== 'granted') throw new Error('没有写入权限。');
  }
  for (const mod of project.mods) {
    const modDir = await project.dir.getDirectoryHandle(mod.folder, { create: true });
    for (const p of mod.deleted) await removeFile(modDir, p);
    mod.deleted.clear();
    for (const f of modOutputFiles(mod)) await writeFile(modDir, f.path, f.text);
  }
}

// ------------------------------------------------------------------ zip (store only, UTF-8 names)

const CRC_TABLE = (() => {
  const t = new Uint32Array(256);
  for (let n = 0; n < 256; n++) { let c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xEDB88320 ^ (c >>> 1) : c >>> 1; t[n] = c >>> 0; }
  return t;
})();
function crc32(bytes) { let c = 0xFFFFFFFF; for (let i = 0; i < bytes.length; i++) c = CRC_TABLE[(c ^ bytes[i]) & 0xFF] ^ (c >>> 8); return (c ^ 0xFFFFFFFF) >>> 0; }

function makeZip(files) {
  const enc = new TextEncoder();
  const chunks = [], central = [];
  let offset = 0;
  const now = new Date();
  const dosTime = (now.getHours() << 11) | (now.getMinutes() << 5) | (now.getSeconds() >> 1);
  const dosDate = ((now.getFullYear() - 1980) << 9) | ((now.getMonth() + 1) << 5) | now.getDate();
  for (const f of files) {
    const name = enc.encode(f.path);
    const data = typeof f.data === 'string' ? enc.encode(f.data) : f.data;
    const crc = crc32(data);
    const lh = new DataView(new ArrayBuffer(30));
    lh.setUint32(0, 0x04034b50, true); lh.setUint16(4, 20, true); lh.setUint16(6, 0x0800, true); lh.setUint16(8, 0, true);
    lh.setUint16(10, dosTime, true); lh.setUint16(12, dosDate, true); lh.setUint32(14, crc, true);
    lh.setUint32(18, data.length, true); lh.setUint32(22, data.length, true); lh.setUint16(26, name.length, true); lh.setUint16(28, 0, true);
    chunks.push(new Uint8Array(lh.buffer), name, data);
    const ch = new DataView(new ArrayBuffer(46));
    ch.setUint32(0, 0x02014b50, true); ch.setUint16(4, 20, true); ch.setUint16(6, 20, true); ch.setUint16(8, 0x0800, true); ch.setUint16(10, 0, true);
    ch.setUint16(12, dosTime, true); ch.setUint16(14, dosDate, true); ch.setUint32(16, crc, true);
    ch.setUint32(20, data.length, true); ch.setUint32(24, data.length, true); ch.setUint16(28, name.length, true);
    ch.setUint32(42, offset, true);
    central.push(new Uint8Array(ch.buffer), name);
    offset += 30 + name.length + data.length;
  }
  const cdSize = central.reduce((s, c) => s + c.length, 0);
  const end = new DataView(new ArrayBuffer(22));
  end.setUint32(0, 0x06054b50, true); end.setUint16(8, files.length, true); end.setUint16(10, files.length, true);
  end.setUint32(12, cdSize, true); end.setUint32(16, offset, true);
  return new Blob([...chunks, ...central, new Uint8Array(end.buffer)], { type: 'application/zip' });
}

function exportZip(mods) {
  const files = [];
  for (const mod of mods) for (const f of modOutputFiles(mod)) files.push({ path: 'Mods/' + mod.folder + '/' + f.path, data: f.text });
  const blob = makeZip(files);
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = (mods.length === 1 ? mods[0].folder : 'DNFTM-Mods') + '.zip';
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 5000);
}

// ------------------------------------------------------------------ strings (localization)

/** "section_12~fallback" -> {section, num, fallback}; null when the text is not a localized reference. */
function parseRef(raw) {
  if (typeof raw !== 'string') return null;
  const m = /^([A-Za-z0-9]+)_([A-Za-z0-9]+)~([\s\S]*)$/.exec(raw);
  return m ? { section: m[1], num: m[2], fallback: m[3] } : null;
}

function locTable(mod, lang, create) {
  const path = 'loc/' + lang + '.json';
  if (!mod.merges[path]) { if (!create) return null; mod.merges[path] = {}; }
  return mod.merges[path];
}

function getLoc(mod, lang, section, num) {
  const t = locTable(mod, lang, false);
  return t && t[section] && typeof t[section][num] === 'string' ? t[section][num] : '';
}

function setLoc(mod, lang, section, num, value) {
  const t = locTable(mod, lang, true);
  (t[section] = t[section] || {})[num] = value;
}

function allRefs(obj, out = []) {
  if (typeof obj === 'string') { const r = parseRef(obj); if (r) out.push(r); }
  else if (Array.isArray(obj)) obj.forEach(v => allRefs(v, out));
  else if (obj && typeof obj === 'object') Object.values(obj).forEach(v => allRefs(v, out));
  return out;
}

/** Next free numeric id inside a section, looking at the cage file and both loc tables. */
function nextRefNum(mod, section) {
  let max = 0;
  for (const r of allRefs(mod.files)) if (r.section === section && /^\d+$/.test(r.num)) max = Math.max(max, +r.num);
  for (const lang of LANGS) {
    const t = locTable(mod, lang, false);
    if (t && t[section]) for (const k of Object.keys(t[section])) if (/^\d+$/.test(k)) max = Math.max(max, +k);
  }
  return String(max + 1);
}

function newRef(mod, section, english, chinese) {
  const num = nextRefNum(mod, section);
  setLoc(mod, 'en', section, num, english || '');
  setLoc(mod, 'ch', section, num, chinese || '');
  return section + '_' + num + '~' + (english || '');
}

const stripMarkup = s => (s || '').replace(/\[\/?[A-Za-z0-9_]+\]/g, '');
function missingGlyphs(s) {
  const bad = new Set();
  for (const ch of stripMarkup(s)) if (ch.charCodeAt(0) > 0x7F && !GLYPHS.has(ch)) bad.add(ch);
  return [...bad];
}
function traditionalChars(s) { const r = new Set(); for (const ch of s || '') if (T2S[ch]) r.add(ch); return [...r]; }
function toSimplified(s) { let o = ''; for (const ch of s || '') o += T2S[ch] || ch; return o; }
function markupKeywords(s) { const r = []; const re = /\[([A-Za-z0-9_]+)\]/g; let m; while ((m = re.exec(s || ''))) r.push(m[1]); return r; }

// ------------------------------------------------------------------ templates

/** Resolves a cage's tmpContainer to {base template, cameras[]} honouring mod sceneTemplates (keepCameras). */
function resolveTemplate(mod, tmpContainer) {
  if (TEMPLATE_BY_ID[tmpContainer]) return { base: TEMPLATE_BY_ID[tmpContainer], cameras: TEMPLATE_BY_ID[tmpContainer].cameras, own: null };
  for (const m of project.mods) {
    const st = m.manifest.sceneTemplates.find(t => t.id === tmpContainer);
    if (st && TEMPLATE_BY_ID[st.cloneFrom]) {
      const base = TEMPLATE_BY_ID[st.cloneFrom];
      let cams = st.keepCameras > 0 ? base.cameras.slice(0, st.keepCameras) : base.cameras;
      const artCams = st.art && Array.isArray(st.art.cameras) ? st.art.cameras : [];
      cams = cams.map((cam, i) => {
        const a = artCams[i];
        if (!a || (!a.clear && !(a.objects || []).length)) return cam;
        const custom = (a.objects || []).map(o => ({
          name: o.name, path: o.name, depth: 0, x: +o.x || 0, y: +o.y || 0, z: +o.z || 0, active: true, sprite: true, custom: true,
          anims: o.animations && Object.keys(o.animations).length ? Object.keys(o.animations) : undefined, art: o,
        }));
        return Object.assign({}, cam, { objects: (a.clear ? [] : cam.objects).concat(custom), artDef: a, artMod: m });
      });
      return { base, cameras: cams, own: st };
    }
  }
  return null;
}

function cagesUsingTemplate(id) { return CAT.cages.filter(c => c.template === id).map(c => c.id); }

// ------------------------------------------------------------------ validation

/**
 * Returns issues: {level: 'err'|'warn'|'info', msg, where, nav: {mod, cage?, tab?, scene?}}
 * Errors are things that crash or break the game; warnings are likely mistakes.
 */
function validateAll() {
  const issues = [];
  const add = (level, msg, where, nav) => issues.push({ level, msg, where, nav });
  const seenIds = {};
  project.mods.forEach((mod, mi) => {
    const M = mod.manifest;
    for (const c of M.cages) {
      const nav = { mod: mi, cage: c.id, tab: 'basic' };
      if (!/^[A-Za-z][A-Za-z0-9]*$/.test(c.id || '')) add('err', `笼子 id「${c.id}」只能用英文字母和数字，且以字母开头。`, mod.folder, nav);
      if (BUILTIN_CAGES.has((c.id || '').toLowerCase())) add('err', `笼子 id「${c.id}」和游戏内置笼子重名。`, mod.folder, nav);
      if (seenIds[c.id]) add('err', `笼子 id「${c.id}」在多个 mod 中重复（${seenIds[c.id]}、${mod.folder}）。`, mod.folder, nav);
      seenIds[c.id] = mod.folder;
      if (!mod.files[c.id + '.json']) add('err', `mod.json 注册了笼子「${c.id}」，但没有 files/${c.id}.json。`, mod.folder, { mod: mi, tab: 'mod' });
    }
    for (const st of M.sceneTemplates) {
      if (!TEMPLATE_BY_ID[st.cloneFrom]) add('err', `场景模板「${st.id}」的来源 Story${st.cloneFrom} 不存在。`, mod.folder, { mod: mi });
      if (TEMPLATE_BY_ID[st.id]) add('err', `场景模板 id「${st.id}」和内置模板重名。`, mod.folder, { mod: mi });
    }
    for (const e of M.cameraEffects) if (!CAT.effects.includes(e.cloneFrom)) add('warn', `摄影机特效来源「${e.cloneFrom}」不存在。`, mod.folder, { mod: mi });
    for (const p of M.diaryPages) {
      const src = DIARY_BY_ID[p.cloneFrom];
      if (!src) { add('err', `笔记本页「${p.story}」的来源 diary${p.cloneFrom} 不存在。`, mod.folder, { mod: mi, cage: p.story, tab: 'diary' }); continue; }
      const names = new Set(src.children.map(c => c.name));
      for (const c of p.copies || []) if (names.has(c.from)) names.add(c.name);   // copied slots can hold keywords too
      const used = {};
      for (const [kw, slot] of Object.entries(p.words || {})) {
        if (!names.has('diaryWord' + slot)) add('err', `关键字「${kw}」对应的字段 diaryWord${slot} 不在 diary${p.cloneFrom} 上。`, p.story, { mod: mi, cage: p.story, tab: 'diary' });
        if (used[slot]) add('err', `字段 ${slot} 同时给了「${used[slot]}」和「${kw}」。`, p.story, { mod: mi, cage: p.story, tab: 'diary' });
        used[slot] = kw;
      }
      const loc = { mod: mi, cage: p.story, tab: 'diary' };
      const copyNames = new Set((p.copies || []).map(c => c.name));
      for (const c of p.copies || []) if (!names.has(c.from)) add('err', `笔记本复制元素的来源「${c.from}」不在 diary${p.cloneFrom} 上。`, p.story, loc);
      for (const m of p.moves || []) if (!names.has(m.name) && !copyNames.has(m.name)) add('warn', `笔记本移动的元素「${m.name}」不在 diary${p.cloneFrom} 上，会被忽略。`, p.story, loc);
      for (const [kw, from] of Object.entries(p.actions || {})) if (!names.has('diaryWord' + from + 'Action')) add('err', `关键字「${kw}」的按钮来源 diaryWord${from}Action 不在 diary${p.cloneFrom} 上。`, p.story, loc);
      for (const [circle, answers] of Object.entries(p.selectors || {})) {
        if (!names.has(circle + 'Selector')) add('err', `圆圈「${circle}」在 diary${p.cloneFrom} 上没有推理「？」（${circle}Selector）。`, p.story, loc);
        if (!Array.isArray(answers) || answers.length !== 3 || answers.some(a => !a)) add('err', `圆圈「${circle}」的推理要刚好 3 个答案关键字。`, p.story, loc);
      }
    }
    const need = requiredLoader(mod);
    if (M.minLoader && verCmp(need, M.minLoader) > 0) add('warn', `mod.json 的 minLoader 是 ${M.minLoader}，但用到的功能需要 ${need}（保存时会自动调高）。`, mod.folder, { mod: mi });
    if (verCmp(need, LOADER_LATEST) > 0) add('err', `用到的功能需要 ModLoader ${need}，比编辑器知道的最新版 ${LOADER_LATEST} 还新。`, mod.folder, { mod: mi });
    for (const id of modCages(mod)) {
      validateCage(mod, mi, id, add);
      if (typeof validateInteractions === 'function') validateInteractions(mod, mi, id, cageData(mod, id), add);
    }
    if (typeof validateArt === 'function') validateArt(mod, mi, add);
    for (const lang of LANGS) {
      const t = locTable(mod, lang, false);
      if (!t) continue;
      for (const [sec, entries] of Object.entries(t)) for (const [num, s] of Object.entries(entries || {})) {
        if (lang === 'ch') {
          const bad = missingGlyphs(s);
          if (bad.length) add('err', `简中文本 ${sec}_${num} 有游戏字体画不出来的字：${bad.join(' ')}`, sec, { mod: mi, cage: sec, tab: 'strings' });
        }
      }
    }
  });
  return issues;
}

function validateCage(mod, mi, id, add) {
  const d = cageData(mod, id);
  const nav = (tab, extra) => Object.assign({ mod: mi, cage: id, tab }, extra || {});
  const md = d.metadata || {};
  if (md.id !== id) add('err', `metadata.id（${md.id}）必须和文件名 ${id} 相同。`, id, nav('basic'));
  const tpl = resolveTemplate(mod, md.tmpContainer);
  if (!tpl) add('err', `找不到场景模板「${md.tmpContainer}」。`, id, nav('basic'));
  const script = d.script || {};
  const smd = script.metadata || {};
  if (smd.id !== id) add('err', `script.metadata.id 必须是 ${id}。`, id, nav('basic'));
  const camCount = +smd.cameras || 0;
  if (tpl && camCount !== tpl.cameras.length)
    add('err', `镜头数（${camCount}）和场景模板的镜头数（${tpl.cameras.length}）不同，游戏存盘时会出错。请在「基本信息」修正。`, id, nav('basic'));
  const scenes = script.scenes || {};
  if (!scenes[smd.startScene]) add('err', `起始场景「${smd.startScene}」不存在。`, id, nav('scenes'));
  const predef = script.predefinedActions || {};
  const kwDefs = d.keywords || {};
  const kwIds = new Set();
  for (const k of Object.keys(kwDefs)) for (const part of k.split(',')) kwIds.add(part.trim());
  const singleKw = Object.keys(kwDefs).filter(k => !k.includes(',') && !k.includes('_'));

  const checkActions = (list, where, sceneName, cam) => {
    (list || []).forEach((a, i) => {
      const w = where + ' #' + (i + 1);
      if (Array.isArray(a.actions) && !a.action) { checkActions(a.actions, w, sceneName, cam); return; }
      const objs = tpl && tpl.cameras[(cam || 1) - 1] ? tpl.cameras[(cam || 1) - 1].objects : null;
      const obj = objs && a.id ? objs.find(o => o.name === a.id) : null;
      const needsObj = ['say', 'animation', 'move', 'setin', 'enable', 'disable', 'flip', 'setz', 'fullDisable', 'fullEnable'].includes(a.action);
      if (needsObj && objs && a.id && !obj) add('warn', `${w}：对象「${a.id}」不在这个镜头的模板里。`, id, nav('scenes', { scene: sceneName }));
      for (const k of ['animation', 'subanimation', 'endanimation', 'endAnimation']) {
        const anim = a[k];
        if (!anim || !obj || !obj.anims || anim.includes('{')) continue;
        if (!obj.anims.includes(anim)) add('warn', `${w}：「${a.id}」没有动画「${anim}」。可用：${obj.anims.join(', ')}`, id, nav('scenes', { scene: sceneName }));
      }
      if (a.action === 'predefinedAction' && !predef[a.name]) add('err', `${w}：预设动作「${a.name}」不存在。`, id, nav('scenes', { scene: sceneName }));
      if (a.action === 'say') for (const kw of markupKeywords(a.text)) if (!kwIds.has(kw)) add('err', `${w}：对白里的关键字 [${kw}] 没有在「关键字」定义。`, id, nav('scenes', { scene: sceneName }));
      if (a.action === 'say' && !a.text) add('warn', `${w}：对白是空的。`, id, nav('scenes', { scene: sceneName }));
    });
  };
  for (const [name, sc] of Object.entries(scenes)) {
    if (sc.goto && !scenes[sc.goto]) add('err', `场景「${name}」的下一个场景「${sc.goto}」不存在。`, id, nav('scenes', { scene: name }));
    if (camCount && (+sc.camera < 1 || +sc.camera > camCount)) add('err', `场景「${name}」的镜头 ${sc.camera} 超出范围（1-${camCount}）。`, id, nav('scenes', { scene: name }));
    if (!['now', 'today', 'nextDay', 'nextAvailable', undefined].includes(sc.modify)) add('warn', `场景「${name}」的时间模式「${sc.modify}」不常见。`, id, nav('scenes', { scene: name }));
    if (sc.modify === 'nextDay') add('warn', `场景「${name}」用了「隔天」：如果上一个场景跑过午夜，会变成后天（整天没动静）。建议改用「下一个 hour 点」（nextAvailable）。`, id, nav('scenes', { scene: name }));
    checkActions(sc.script, '场景「' + name + '」', name, +sc.camera || 1);
    // Camera light: the game does not light it by itself; scenes where characters act should blink it.
    const acts = [];
    const collect = (l, depth) => (l || []).forEach(x => {
      if (Array.isArray(x.actions) && !x.action) collect(x.actions, depth);
      else if (x.action === 'predefinedAction' && depth < 4) { acts.push(x); collect(predef[x.name], depth + 1); }
      else acts.push(x);
    });
    collect(sc.script, 0);
    const active = acts.some(x => ['say', 'move', 'animation'].includes(x.action));
    if (active && !acts.some(x => x.action === 'blinkLed'))
      add('warn', `场景「${name}」有角色活动，但没有「🔴 镜头灯闪烁」，玩家不会收到提醒。可在剧情分页按「💡 一键加入镜头灯」。`, id, nav('scenes', { scene: name }));
  }
  for (const [name, list] of Object.entries(predef)) checkActions(list, '预设动作「' + name + '」', null, 1);

  // Reachability from the start scene.
  const reach = new Set(); let cur = smd.startScene;
  while (cur && scenes[cur] && !reach.has(cur)) { reach.add(cur); cur = scenes[cur].goto; }
  for (const name of Object.keys(scenes)) if (!reach.has(name)) add('info', `场景「${name}」不在起始场景的 goto 链上（只有被事件跳转时才会播放）。`, id, nav('scenes', { scene: name }));

  // Keyword markup in browser texts too.
  for (const [k, def] of Object.entries(kwDefs)) {
    for (const r of ((def.browser || {}).data || [])) for (const f of ['title', 'subtitle', 'text']) for (const kw of markupKeywords(r[f]))
      if (!kwIds.has(kw)) add('err', `关键字「${k}」的搜索结果里用了未定义的关键字 [${kw}]。`, id, nav('keywords'));
    for (const r of ((def.browser || {}).data || [])) for (const im of browserImages(r)) if (!imageExists(im)) add('warn', `关键字「${k}」的图片路径找不到：${im}`, id, nav('keywords'));
  }

  // Diary: every collectable keyword needs a slot, or the game throws when it is written in the notebook.
  const page = mod.manifest.diaryPages.find(p => p.story === id);
  if (!page) add('err', `没有笔记本页设置。收集关键字时游戏会出错，请到「笔记本」分页设置。`, id, nav('diary'));
  else {
    for (const kw of singleKw) if (!(page.words || {})[kw]) add('err', `关键字「${kw}」没有分配笔记本字段。`, id, nav('diary'));
    const kept = new Set((page.keep || []).concat((page.copies || []).map(c => c.name)));   // copies are kept too
    const dc = d.diaryConfig || {};
    for (const z of dc.zones || []) {
      if (!kept.has(z.circle)) add('err', `笔记本区块的圆圈「${z.circle}」没有保留在页面上。`, id, nav('diary'));
      for (const w of z.words || []) if (!kwIds.has(w)) add('err', `笔记本区块用了未定义的关键字「${w}」。`, id, nav('diary'));
    }
    if (!Array.isArray(dc.arrows) || !Array.isArray(dc.images)) add('err', 'diaryConfig 需要 arrows 和 images 数组（可以是空的）。', id, nav('diary'));
    const sel = page.selectors || {};
    for (const z of dc.zones || []) {
      if (!z.selectableWords && !sel[z.circle]) continue;
      const answers = sel[z.circle] || [];
      if (!z.selectableWords || !z.wordSelector) add('err', `圆圈「${z.circle}」设置了推理答案，但区块缺少 selectableWords / wordSelector（推理条件）。`, id, nav('diary'));
      else if (JSON.stringify(z.selectableWords) !== JSON.stringify(answers)) add('err', `圆圈「${z.circle}」的区块答案（selectableWords）和笔记本页 selectors 不一致。`, id, nav('diary'));
      for (const a of answers) if (!(z.words || []).includes(a)) add('warn', `推理答案「${a}」不在圆圈「${z.circle}」的区块关键字里。`, id, nav('diary'));
    }
    for (const a of dc.arrows || []) if (!kept.has(a.arrow) && !(page.copies || []).some(c => c.name === a.arrow)) add('err', `箭头「${a.arrow}」没有保留在页面上。`, id, nav('diary'));
  }

  // Prizes: the game shows a prize by activating its own object on the prize shelf; without one, receiving it
  // leaves the info popup stuck (looks like a freeze). ModLoader 0.5.10 "prizes" builds that object.
  const shelf = new Set((mod.manifest.prizes || []).map(p => p.id));
  for (const k of Object.keys(d.prizes || {})) if (!shelf.has(k) && !GAME_PRIZE_OBJECTS.includes(k))
    add('err', `物品「${k}」在物品架上没有物件：玩家收到时游戏会卡住。请在「互动 → 物品」设置「物品架上的物件」。`, id, nav('interact'));

  // Strings referenced by the cage should have both translations.
  for (const r of allRefs(d)) {
    if (r.section !== id) continue;
    for (const lang of LANGS) if (!getLoc(mod, lang, r.section, r.num)) add('warn', `文本 ${r.section}_${r.num} 缺少${lang === 'ch' ? '简中' : '英文'}翻译。`, id, nav('strings'));
    const zh = getLoc(mod, 'ch', r.section, r.num);
    if (traditionalChars(zh).length) add('warn', `文本 ${r.section}_${r.num} 含繁体字（${traditionalChars(zh).join('')}），游戏字体只有简体。可在「文本」分页一键转换。`, id, nav('strings'));
  }
  if (!mod.manifest.cameraEffects.find(e => e.story === id)) add('info', '没有指定摄影机特效，每局游戏会随机挑选（可能是黑白画面）。', id, nav('basic'));
}

// ------------------------------------------------------------------ new cage scaffold

function scaffoldCage(mod, opts) {
  const { id, templateId, cameras, effectFrom, diaryFrom } = opts;
  const base = TEMPLATE_BY_ID[templateId];
  const ownTpl = id; // always derive our own template so camera count matches and art can be replaced later
  mod.manifest.sceneTemplates = mod.manifest.sceneTemplates.filter(t => t.id !== ownTpl);
  mod.manifest.sceneTemplates.push({ id: ownTpl, cloneFrom: templateId, keepCameras: cameras });
  mod.manifest.cages = mod.manifest.cages.filter(c => c.id !== id);
  mod.manifest.cages.push({ id, insertAt: 0 });
  mod.manifest.cameraEffects = mod.manifest.cameraEffects.filter(e => e.story !== id);
  if (effectFrom) mod.manifest.cameraEffects.push({ story: id, cloneFrom: effectFrom });
  mod.manifest.diaryPages = mod.manifest.diaryPages.filter(p => p.story !== id);
  const keep = (DIARY_BY_ID[diaryFrom] || { children: [] }).children.filter(c => c.name === 'diaryWordvideo').map(c => c.name);
  mod.manifest.diaryPages.push({ story: id, cloneFrom: diaryFrom, words: {}, keep });

  // Start scene hides every animated character so the room starts empty.
  // Characters plus screen overlays that templates leave switched on (black screen, flash, close-up hand).
  // Night layers (noche...) are left alone: the game fades them by time of day.
  const overlay = /black|negr|flash|^mano|interferenc/i;
  const isCharacter = o => (o.anims || []).some(a => /^(anda|habla|camina)/i.test(a));
  const hideList = cam => cam.objects.filter(o => o.depth === 0 && o.active && (isCharacter(o) || overlay.test(o.name)))
    .map(o => ({ id: o.name, action: 'disable' }));
  const scenes = {
    start: { _comment: '开场：隐藏模板里原本的角色', camera: 1, hour: '0', modify: 'now', goto: 'day1', script: hideList(base.cameras[0]) },
    day1: { _comment: '第一天', camera: 1, hour: '10', modify: 'today', script: [] },
  };
  mod.files[id + '.json'] = {
    metadata: { id, hint: '', tmpContainer: ownTpl, difficulty: 30, interest: 50 },
    items: {}, prizes: {}, chatConfig: {}, chats: {}, phoneCalls: {}, emails: {}, news: {},
    keywords: {},
    diaryConfig: { zones: [], arrows: [], images: [] },
    genericEvents: {},
    script: { metadata: { cameras, id, startScene: 'start' }, predefinedActions: {}, scenes },
  };
  for (let c = 2; c <= cameras; c++) {
    scenes['start' + c] = { _comment: `镜头 ${c} 开场`, camera: c, hour: '0', modify: 'now', script: hideList(base.cameras[c - 1]) };
    mod.files[id + '.json'].script.metadata['startScene' + c] = 'start' + c;
  }
  mod.deleted.delete('files/' + id + '.json');
}

function deleteCage(mod, id) {
  mod.manifest.cages = mod.manifest.cages.filter(c => c.id !== id);
  mod.manifest.sceneTemplates = mod.manifest.sceneTemplates.filter(t => t.id !== id);
  mod.manifest.cameraEffects = mod.manifest.cameraEffects.filter(e => e.story !== id);
  mod.manifest.diaryPages = mod.manifest.diaryPages.filter(p => p.story !== id);
  delete mod.files[id + '.json'];
  mod.deleted.add('files/' + id + '.json');
  for (const lang of LANGS) { const t = locTable(mod, lang, false); if (t) delete t[id]; }
}
