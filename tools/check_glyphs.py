"""Report characters in a loc/ch.json merge file that the game's Chinese fonts cannot draw."""
import json, re, sys
glyphs = json.load(open(sys.argv[1]))
common = set.intersection(*(set(v) for v in glyphs.values()))
data = json.load(open(sys.argv[2], encoding="utf-8"))
bad = {}
def walk(x, path):
    if isinstance(x, dict):
        for k, v in x.items(): walk(v, path + "/" + k)
    elif isinstance(x, str):
        text = re.sub(r"\[/?[A-Za-z0-9_]+\]", "", x)  # keyword markup is not drawn
        for ch in text:
            if ord(ch) > 0x2000 and ord(ch) not in common:
                bad.setdefault(ch, []).append(path)
walk(data, "")
print("glyphs in all fonts:", len(common))
print("missing:", {k: v for k, v in bad.items()} or "none")
