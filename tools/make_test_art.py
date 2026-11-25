"""Draws a small pixel-art set used to test custom art in the mod loader (and as an example for modders).

    python -I make_test_art.py <mod folder>/art/ghostRoom
Outputs: room.png (252x174 background), night.png (night overlay), ghost.png (sprite sheet, 8 cells 24x40),
         help.png (writing only visible with night vision).
"""
import os, sys
from PIL import Image, ImageDraw

out = sys.argv[1]
os.makedirs(out, exist_ok=True)
W, H = 252, 174

# ---------------------------------------------------------------- room
room = Image.new("RGBA", (W, H), (0, 0, 0, 255))
d = ImageDraw.Draw(room)
d.rectangle([0, 0, W, 120], fill=(92, 110, 140))           # wall
for x in range(0, W, 12): d.line([x, 0, x, 120], fill=(84, 101, 130))  # wallpaper stripes
d.rectangle([0, 120, W, H], fill=(96, 70, 52))             # floor
for y in range(124, H, 9): d.line([0, y, W, y], fill=(84, 60, 44))
d.rectangle([150, 20, 222, 80], fill=(40, 46, 70)); d.rectangle([154, 24, 218, 76], fill=(150, 190, 230))  # window
d.line([186, 24, 186, 76], fill=(40, 46, 70), width=3); d.line([154, 50, 218, 50], fill=(40, 46, 70), width=3)
d.ellipse([196, 30, 210, 44], fill=(250, 246, 210))       # moon
d.rectangle([20, 92, 90, 100], fill=(120, 84, 50)); d.rectangle([26, 100, 32, 130], fill=(100, 70, 40)); d.rectangle([78, 100, 84, 130], fill=(100, 70, 40))  # table
d.rectangle([40, 78, 60, 92], fill=(200, 60, 60)); d.rectangle([44, 70, 56, 78], fill=(230, 220, 200))  # candle box
d.rectangle([0, 118, W, 121], fill=(60, 44, 34))
room.save(os.path.join(out, "room.png"))

# ---------------------------------------------------------------- night overlay
night = Image.new("RGBA", (W, H), (10, 14, 40, 190))
nd = ImageDraw.Draw(night)
nd.rectangle([154, 24, 218, 76], fill=(10, 14, 40, 90))  # window stays a bit brighter
night.save(os.path.join(out, "night.png"))

# ---------------------------------------------------------------- night-vision-only writing
helpimg = Image.new("RGBA", (60, 22), (0, 0, 0, 0))
hd = ImageDraw.Draw(helpimg)
# blocky letters H E L P
def block(x, rows):
    for j, row in enumerate(rows):
        for i, c in enumerate(row):
            if c == "#": hd.rectangle([x + i * 3, 2 + j * 3, x + i * 3 + 2, 2 + j * 3 + 2], fill=(200, 20, 20, 255))
block(2, ["#.#", "#.#", "###", "#.#", "#.#"]); block(15, ["###", "#..", "##.", "#..", "###"])
block(28, ["#..", "#..", "#..", "#..", "###"]); block(41, ["##.", "#.#", "##.", "#..", "#.."])
helpimg.save(os.path.join(out, "help.png"))

# ---------------------------------------------------------------- ghost sheet: 8 cells of 24x40
# 0-1 idle, 2-3 walk, 4-5 talk, 6-7 float
CW, CH = 24, 40
sheet = Image.new("RGBA", (CW * 8, CH), (0, 0, 0, 0))
def ghost(cell, bob=0, mouth=False, lean=0, wave=0):
    img = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    g = ImageDraw.Draw(img)
    top = 4 + bob
    g.ellipse([3 + lean, top, 20 + lean, top + 18], fill=(235, 240, 250, 235))
    g.rectangle([3 + lean, top + 9, 20 + lean, top + 30], fill=(235, 240, 250, 235))
    for i in range(4):  # wavy hem
        x = 3 + lean + i * 4 + (wave % 2)
        g.polygon([(x, top + 30), (x + 2, top + 34), (x + 4, top + 30)], fill=(235, 240, 250, 235))
    g.rectangle([7 + lean, top + 8, 9 + lean, top + 11], fill=(20, 20, 30, 255))
    g.rectangle([14 + lean, top + 8, 16 + lean, top + 11], fill=(20, 20, 30, 255))
    if mouth: g.ellipse([10 + lean, top + 14, 13 + lean, top + 19], fill=(20, 20, 30, 255))
    else: g.line([10 + lean, top + 16, 13 + lean, top + 16], fill=(20, 20, 30, 255))
    sheet.paste(img, (cell * CW, 0))
ghost(0, bob=0); ghost(1, bob=1, wave=1)
ghost(2, bob=0, lean=1); ghost(3, bob=1, lean=1, wave=1)
ghost(4, mouth=True); ghost(5, mouth=False, bob=1)
ghost(6, bob=-2); ghost(7, bob=-4, wave=1)
sheet.save(os.path.join(out, "ghost.png"))
print("art written to", out)
