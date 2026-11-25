"""
Builds editor/catalog.js: everything the mod editor needs to know about the game, extracted from a local
copy of Do Not Feed the Monkeys (Unity 5.6). Run with the scratch venv (UnityPy, Pillow, opencc):

    python -I build_catalog.py <game>/dnftm_Data <out>/catalog.js

Contents:
  templates   scene templates (Stories/Scenaries/Story<id>): cameras, objects, animator states,
              script-pixel positions and a composited background image per camera
  diaryPages  notebook pages (diary<cage>): children with kind and position (word slots, circles...)
  effects     fixed camera effects (storyEffects/<cage>)
  cages       built-in cages: id -> template, camera count, text section
  images      Resources image paths usable in news/chat JSON
  glyphs      characters drawable by every Chinese font
  t2s         Traditional -> Simplified map limited to drawable characters
"""
import base64, collections, io, json, re, struct, sys
import UnityPy
from PIL import Image
from opencc import OpenCC

DATA, OUT = sys.argv[1], sys.argv[2]
W, H = 252, 174          # camera view in script pixels (calculatePosition: (px-126, px-87) * 0.01)
OX, OY = 126, 87
# Night overlays, black screens, flashes, close-up hands: skipped in the daytime preview images.
OVERLAY = re.compile(r"noche|night|negr|black|flash|blanco|capa|interferenc|^mano|vacio|roto|time", re.I)

env = UnityPy.load(DATA + "/level3")
objs = {o.path_id: o for o in env.objects}
tr = {pid: o.read() for pid, o in objs.items() if o.type.name in ("Transform", "RectTransform")}
go_cache = {}

def go_of(t):
    pid = t.m_GameObject.path_id
    if pid not in go_cache:
        go_cache[pid] = t.m_GameObject.read()
    return go_cache[pid]

def name(t): return go_of(t).m_Name

def children(t): return [tr[c.path_id] for c in t.m_Children if c.path_id in tr]

def find_path(path):
    parts = path.split("/")
    for t in tr.values():
        if name(t) == parts[0] and not (t.m_Father and t.m_Father.path_id):
            cur = t
            for p in parts[1:]:
                cur = next((c for c in children(cur) if name(c) == p), None)
                if cur is None: break
            if cur is not None: return cur
    return None

def components(go):
    out = {}
    for c in go.m_Components:
        ptr = c.component if hasattr(c, "component") else c
        try:
            o = ptr.deref()
        except Exception:
            continue
        if o.type.name == "MonoBehaviour":
            try:
                cls = o.read(check_read=False).m_Script.read().m_ClassName
            except Exception:
                cls = "?"
            out.setdefault("mb", []).append(cls)
        else:
            out[o.type.name] = o
    return out

state_cache = {}
def animator_states(anim_obj):
    a = anim_obj.read()
    try:
        ctrl = a.m_Controller.read()
    except Exception:
        return []
    key = a.m_Controller.path_id, a.m_Controller.file_id
    if key in state_cache: return state_cache[key]
    tos = getattr(ctrl, "m_TOS", None) or {}
    items = tos.items() if hasattr(tos, "items") else tos
    states = sorted({v.split(".", 1)[1] for _, v in items
                     if isinstance(v, str) and v.startswith("Base Layer.") and "->" not in v})
    if not states and hasattr(ctrl, "m_Controller"):  # override controller
        states = []
    state_cache[key] = states
    return states

sprite_img_cache = {}
def sprite_image(sr_obj):
    sr = sr_obj.read()
    if not sr.m_Sprite or not sr.m_Sprite.path_id: return None
    key = (sr.m_Sprite.file_id, sr.m_Sprite.path_id)
    if key not in sprite_img_cache:
        try:
            sp = sr.m_Sprite.read()
            img = sp.image
            ppu = getattr(sp, "m_PixelsToUnits", 100) or 100
            if abs(ppu - 100) > 0.01:
                img = img.resize((max(1, round(img.width * 100 / ppu)), max(1, round(img.height * 100 / ppu))), Image.NEAREST)
            piv = getattr(sp, "m_Pivot", None)
            pivot = (piv.x, piv.y) if piv is not None else (0.5, 0.5)
            sprite_img_cache[key] = (img, pivot)
        except Exception:
            sprite_img_cache[key] = None
    res = sprite_img_cache[key]
    if res is None: return None
    color = getattr(sr, "m_Color", None)
    alpha = color.a if color is not None else 1
    return res[0], res[1], bool(getattr(sr, "m_FlipX", False)), alpha

def walk_camera(cam):
    """Objects of one camera node with positions in script pixels."""
    objects, layers = [], []
    def rec(t, wx, wy, wz, sx, sy, active_chain, animated_chain, depth, path):
        p, s = t.m_LocalPosition, t.m_LocalScale
        x, y, z = wx + p.x * sx, wy + p.y * sy, wz + p.z
        nsx, nsy = sx * s.x, sy * s.y
        go = go_of(t)
        comps = components(go)
        active = active_chain and bool(go.m_IsActive)
        anim = "Animator" in comps
        states = animator_states(comps["Animator"]) if anim else []
        mbs = comps.get("mb", [])
        entry = {
            "name": go.m_Name, "path": path, "depth": depth,
            "x": round(x * 100 + OX, 1), "y": round(y * 100 + OY, 1),
            "active": bool(go.m_IsActive),
            "sprite": "SpriteRenderer" in comps,
        }
        if states: entry["anims"] = states
        if "StoryItemInterface" in mbs: entry["clickable"] = True
        if "VideoHidden" in mbs: entry["videoHidden"] = True
        entry["z"] = round(z, 2)
        # Default sprite of animated top-level objects, for the editor's live preview.
        if depth == 0 and states and "SpriteRenderer" in comps:
            img = sprite_image(comps["SpriteRenderer"])
            if img:
                im, pivot, flip, alpha = img
                if flip ^ (nsx < 0): im = im.transpose(Image.FLIP_LEFT_RIGHT)
                entry["img"] = png_rgba_b64(im)
                entry["pv"] = [round(pivot[0] * im.width, 1), round(pivot[1] * im.height, 1)]
        objects.append(entry)
        if "SpriteRenderer" in comps and active:
            img = sprite_image(comps["SpriteRenderer"])
            if img and not OVERLAY.search(go.m_Name): layers.append((z, x, y, nsx, nsy, img, animated_chain or anim))
        for c in children(t):
            rec(c, x, y, z, nsx, nsy, active, animated_chain or anim, depth + 1, path + "/" + name(c))
    for c in children(cam):
        rec(c, 0, 0, 0, 1, 1, True, False, 0, name(c))
    return objects, layers

def composite(layers, include_animated):
    canvas = Image.new("RGBA", (W, H), (20, 20, 20, 255))
    for z, x, y, sx, sy, (img, pivot, flip, alpha), animated in sorted(layers, key=lambda l: -l[0]):
        if animated and not include_animated: continue
        if alpha <= 0.01: continue
        im = img
        if flip ^ (sx < 0): im = im.transpose(Image.FLIP_LEFT_RIGHT)
        if sy < 0: im = im.transpose(Image.FLIP_TOP_BOTTOM)
        if abs(abs(sx) - 1) > 0.01 or abs(abs(sy) - 1) > 0.01:
            im = im.resize((max(1, round(im.width * abs(sx))), max(1, round(im.height * abs(sy)))), Image.NEAREST)
        if alpha < 0.99:
            a = im.getchannel("A").point(lambda v: int(v * alpha))
            im = im.copy(); im.putalpha(a)
        px, py = x * 100 + OX, y * 100 + OY
        left = round(px - pivot[0] * im.width)
        top = round((H - py) - (1 - pivot[1]) * im.height)
        canvas.alpha_composite(im.convert("RGBA"), (left, top)) if 0 <= left and 0 <= top and left + im.width <= W and top + im.height <= H \
            else paste_clipped(canvas, im.convert("RGBA"), left, top)
    return canvas

def paste_clipped(canvas, im, left, top):
    x0, y0 = max(0, left), max(0, top)
    x1, y1 = min(W, left + im.width), min(H, top + im.height)
    if x1 <= x0 or y1 <= y0: return
    crop = im.crop((x0 - left, y0 - top, x1 - left, y1 - top))
    canvas.alpha_composite(crop, (x0, y0))

def png_rgba_b64(img):
    img = img.convert("RGBA")
    if img.width * img.height > 4096:
        img = img.quantize(colors=64, method=Image.Quantize.FASTOCTREE)
    buf = io.BytesIO(); img.save(buf, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()

def png_b64(img):
    img = img.convert("RGB").quantize(colors=128, method=Image.Quantize.MEDIANCUT)
    buf = io.BytesIO(); img.save(buf, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()

# ------------------------------------------------------------------ templates
catalog = {"version": 1, "view": {"w": W, "h": H}}
scen = find_path("Stories/Scenaries")
templates = []
for st in children(scen):
    n = name(st)
    if not n.startswith("Story"): continue
    tpl = {"id": n[5:], "cameras": []}
    for cam in children(st):
        objects, layers = walk_camera(cam)
        tpl["cameras"].append({
            "node": name(cam), "objects": objects,
            "bg": png_b64(composite(layers, False)),
            "full": png_b64(composite(layers, True)),
        })
    templates.append(tpl)
    print("template", tpl["id"], [len(c["objects"]) for c in tpl["cameras"]], file=sys.stderr)
catalog["templates"] = templates

# ------------------------------------------------------------------ diary pages
diary_root = find_path("Game/diaryObject/diaryStory")
pages = []
for pg in children(diary_root):
    n = name(pg)
    if not n.startswith("diary"): continue
    kids = []
    for c in children(pg):
        cn = name(c); p = c.m_LocalPosition
        kind = ("word" if cn.startswith("diaryWord") and not cn.endswith("Action") else
                "action" if cn.endswith("Action") else
                "circle" if re.match(r"diaryCircle\d+$", cn) else
                "arrow" if cn.startswith("diaryArrow") else
                "image" if cn.startswith("diaryImage") else "other")
        kids.append({"name": cn, "kind": kind, "x": round(p.x, 3), "y": round(p.y, 3)})
    pages.append({"id": n[5:], "children": kids})
catalog["diaryPages"] = pages
print("diary pages", len(pages), file=sys.stderr)

# ------------------------------------------------------------------ camera effects
eff = find_path("storyEffects")
catalog["effects"] = sorted(name(c) for c in children(eff)) if eff else []

# ------------------------------------------------------------------ built-in cages + resources
res_env = UnityPy.load(DATA + "/resources.assets")
texts = {}
for o in res_env.objects:
    if o.type.name == "TextAsset":
        d = o.read(); s = d.m_Script
        texts.setdefault(d.m_Name, s if isinstance(s, str) else bytes(s).decode("utf-8", "replace"))
cages = []
for n, s in texts.items():
    try: j = json.loads(s.lstrip("﻿"))
    except Exception: continue
    if isinstance(j, dict) and isinstance(j.get("metadata"), dict) and "tmpContainer" in j["metadata"]:
        cages.append({"id": j["metadata"].get("id", n), "file": n, "template": j["metadata"]["tmpContainer"],
                      "cameras": (j.get("script") or {}).get("metadata", {}).get("cameras")})
catalog["cages"] = sorted(cages, key=lambda c: c["id"].lower())

# Shop items (for "items": what happens when the player ships a shop item to a cage's address).
def loc_lookup(loc, raw):
    m = re.match(r"^([A-Za-z0-9]+)_([A-Za-z0-9]+)~(.*)$", raw or "", re.S)
    if not m: return raw
    return ((loc.get(m.group(1)) or {}).get(m.group(2))) or m.group(3)
try:
    en_loc = json.loads(texts["en"].lstrip("﻿"))
    ch_loc = json.loads(texts["ch"].lstrip("﻿"))
    shop = json.loads(texts["shop"].lstrip("﻿"))
    items = []
    for cat, entries in shop.items():
        for iid, it in entries.items():
            items.append({"id": iid, "category": cat, "price": it.get("price"),
                          "en": loc_lookup(en_loc, it.get("name")), "ch": loc_lookup(ch_loc, it.get("name"))})
    catalog["shopItems"] = items
except Exception as e:
    print("shop items skipped:", e, file=sys.stderr)
    catalog["shopItems"] = []

gg = UnityPy.load(DATA + "/globalgamemanagers")
images = set()
for o in gg.objects:
    if o.type.name == "ResourceManager":
        for k, v in o.read_typetree()["m_Container"]:
            if k.startswith(("newspapper/", "avatares chat/", "avatares trabajo/", "endingsimg/", "door/", "objetos mart/")):
                images.add(k)
catalog["images"] = sorted(images)

# ------------------------------------------------------------------ fonts
sa2 = UnityPy.load(DATA + "/sharedassets2.assets")
font_sets = []
for o in sa2.objects:
    if o.type.name != "MonoBehaviour": continue
    try: n = o.read(check_read=False).m_Name
    except Exception: continue
    if "Chinese" not in n or "SDF" not in n: continue
    raw = o.get_raw_data(); best = (0, 0)
    for off in range(0, len(raw) - 4, 4):
        cnt = struct.unpack_from("<i", raw, off)[0]
        if cnt < 50 or off + 4 + cnt * 36 > len(raw): continue
        if all(32 <= struct.unpack_from("<i", raw, off + 4 + k * 36)[0] <= 0x10FFFF for k in range(min(cnt, 40))):
            if cnt > best[0]: best = (cnt, off)
    cnt, off = best
    font_sets.append({struct.unpack_from("<i", raw, off + 4 + k * 36)[0] for k in range(cnt)})
glyphs = set.intersection(*font_sets) if font_sets else set()
catalog["glyphs"] = "".join(sorted(chr(c) for c in glyphs if c > 0x7F))

cc = OpenCC("t2s")
t2s = {}
for cp in list(range(0x3000, 0x303F)) + list(range(0x4E00, 0xA000)) + list(range(0xFF00, 0xFFEF)):
    ch = chr(cp); s = cc.convert(ch)
    if s != ch and len(s) == 1 and ord(s) in glyphs:
        t2s[ch] = s
catalog["t2s"] = t2s
print("glyphs", len(catalog["glyphs"]), "t2s", len(t2s), "images", len(images), "cages", len(cages), file=sys.stderr)

with open(OUT, "w", encoding="utf-8") as f:
    f.write("// Generated by tools/build_catalog.py from the game's data. Do not edit by hand.\n")
    f.write("window.DNFTM_CATALOG = ")
    json.dump(catalog, f, ensure_ascii=False, separators=(",", ":"))
    f.write(";\n")
