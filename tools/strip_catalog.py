"""
Makes the public copy of editor/catalog.js: the same data without the game's pictures (scene backgrounds and
object sprites are the game's own art and are not redistributed). The editor then shows placeholders; anyone who
owns the game can rebuild the full file with build_catalog.py (see editor/README_從遊戲提取預覽圖.txt).

    python -I strip_catalog.py <full catalog.js> <out catalog.js>
"""
import json, sys

src, out = sys.argv[1], sys.argv[2]
text = open(src, encoding='utf-8').read()
head, body = text[:text.index('{')], text[text.index('{'):].rstrip().rstrip(';')
cat = json.loads(body)
removed = 0
for t in cat.get('templates', []):
    for cam in t.get('cameras', []):
        for k in ('bg', 'full'):
            if cam.get(k): cam[k] = ''; removed += 1
        for o in cam.get('objects', []):
            if o.get('img'): o['img'] = ''; removed += 1
left = json.dumps(cat).count('data:image')
assert left == 0, '%d pictures left' % left
cat['noPreviews'] = True
with open(out, 'w', encoding='utf-8') as f:
    f.write(head + json.dumps(cat, ensure_ascii=False, separators=(',', ':')) + ';\n')
print('removed %d pictures -> %s' % (removed, out))
