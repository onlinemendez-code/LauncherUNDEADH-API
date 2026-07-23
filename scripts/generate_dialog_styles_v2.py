#!/usr/bin/env python3
"""10 NEW radical dialogue UI concepts — v2, completely different from v1."""

from __future__ import annotations

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = Path("/workspace/dialog-styles/v2")
W, H = 1280, 720

TITLE = "ЧЁРНЫЙ РЫНОК «БАРЫГА»"
LINE = "Псс... сюда. Здесь не спрашивают, откуда товар. Спрашивают цену."
OPTS = [
    "Есть работа?",
    "Это чёрный рынок?",
    "Можно доверять?",
    "Есть горячие заказы?",
]


def fnt(sz: int, bold: bool = False):
    p = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    return ImageFont.truetype(p, sz) if Path(p).exists() else ImageFont.load_default()


def scene() -> Image.Image:
    img = Image.new("RGB", (W, H), (36, 34, 32))
    d = ImageDraw.Draw(img)
    for y in range(0, H, 24):
        d.line((0, y, W, y), fill=(32, 30, 28))
    # npc silhouette center
    d.ellipse((W // 2 - 35, H // 2 - 160, W // 2 + 35, H // 2 - 90), fill=(58, 54, 50))
    d.rectangle((W // 2 - 55, H // 2 - 90, W // 2 + 55, H // 2 + 60), fill=(52, 48, 44))
    d.ellipse((W // 2 - 22, H // 2 - 200, W // 2 + 22, H // 2 - 156), fill=(255, 220, 80))
    return img


def wrap(d, text, font, mw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = f"{cur} {w}".strip()
        if d.textlength(t, font=font) <= mw:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def hdr(img: Image.Image, title: str) -> Image.Image:
    bar = Image.new("RGB", (W, 40), (14, 14, 14))
    ImageDraw.Draw(bar).text((14, 11), title, font=fnt(13, True), fill=(210, 210, 210))
    out = Image.new("RGB", (W, H + 40), (14, 14, 14))
    out.paste(bar, (0, 0))
    out.paste(img, (0, 40))
    return out


def save(img, name, cap):
    p = OUT / f"{name}.png"
    hdr(img, cap).save(p, optimize=True)
    print(p)


# ── 01 CINEMATIC SUBTITLE — no box, only film lines ────────────────────────
def s01():
    img = scene().convert("RGBA")
    d = ImageDraw.Draw(img)
    # letterbox
    d.rectangle((0, 0, W, 90), fill=(0, 0, 0, 200))
    d.rectangle((0, H - 140, W, H), fill=(0, 0, 0, 200))
    d.text((W // 2 - d.textlength(TITLE, font=fnt(20, True)) // 2, H - 125), TITLE, font=fnt(20, True), fill=(240, 240, 240))
    y = H - 95
    for ln in wrap(d, LINE, fnt(15), 900):
        d.text((W // 2 - d.textlength(ln, font=fnt(15)) // 2, y), ln, font=fnt(15), fill=(210, 210, 210))
        y += 22
    y += 8
    for o in OPTS:
        tw = d.textlength(o, font=fnt(14))
        x = W // 2 - tw // 2
        d.line((x, y + 16, x + tw, y + 16), fill=(200, 200, 200), width=1)
        d.text((x, y), o, font=fnt(14), fill=(190, 190, 190))
        y += 24
    save(img.convert("RGB"), "01-cinematic-subtitle", "01 — КИНО-СУБТИТРЫ (без рамки, только строки в letterbox)")


# ── 02 CRUMPLED NOTE — paper handed to you ─────────────────────────────────
def s02():
    img = scene().convert("RGBA")
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    cx, cy = W // 2, H // 2 + 40
    pts = [(cx - 200, cy - 80), (cx + 190, cy - 95), (cx + 210, cy + 120), (cx - 180, cy + 130), (cx - 220, cy + 20)]
    d.polygon(pts, fill=(225, 225, 220, 245), outline=(140, 140, 135))
    # fold crease
    d.line([(cx - 180, cy - 20), (cx + 200, cy - 35)], fill=(170, 170, 165), width=2)
    d.text((cx - 170, cy - 65), TITLE, font=fnt(17, True), fill=(30, 30, 30))
    ty = cy - 35
    for ln in wrap(d, LINE, fnt(12), 340):
        d.text((cx - 165, ty), ln, font=fnt(12), fill=(50, 50, 50))
        ty += 18
    ty += 10
    for o in OPTS:
        d.text((cx - 160, ty), f"— {o}", font=fnt(11), fill=(35, 35, 35))
        ty += 20
    layer = layer.rotate(-4, resample=Image.Resampling.BICUBIC, center=(cx, cy))
    return Image.alpha_composite(img, layer)


def s02_save():
    save(s02().convert("RGB"), "02-crumpled-note", "02 — СМЯТАЯ ЗАПИСКА (передают из рук в руки)")


# ── 03 PRISON GLASS — dialogue behind dirty glass ──────────────────────────
def s03():
    img = scene().convert("RGBA")
    d = ImageDraw.Draw(img)
    gx0, gy0, gx1, gy1 = 180, 80, W - 180, H - 60
    d.rectangle((gx0, gy0, gx1, gy1), fill=(20, 20, 20, 180), outline=(200, 200, 200), width=3)
    # vertical bars
    for x in range(gx0 + 60, gx1, 80):
        d.rectangle((x, gy0, x + 8, gy1), fill=(60, 60, 60, 220))
    frost = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fd = ImageDraw.Draw(frost)
    rng = random.Random(7)
    for _ in range(400):
        x, y = rng.randint(gx0, gx1), rng.randint(gy0, gy1)
        fd.ellipse((x, y, x + rng.randint(2, 8), y + rng.randint(2, 8)), fill=(255, 255, 255, rng.randint(8, 35)))
    img = Image.alpha_composite(img, frost)
    d = ImageDraw.Draw(img)
    d.text((gx0 + 30, gy0 + 24), TITLE, font=fnt(22, True), fill=(230, 230, 230))
    ty = gy0 + 65
    for ln in wrap(d, LINE, fnt(14), gx1 - gx0 - 60):
        d.text((gx0 + 30, ty), ln, font=fnt(14), fill=(200, 200, 200))
        ty += 22
    ty = gy1 - 130
    for o in OPTS:
        d.rectangle((gx0 + 30, ty, gx1 - 30, ty + 26), outline=(160, 160, 160))
        d.text((gx0 + 40, ty + 5), o, font=fnt(12), fill=(210, 210, 210))
        ty += 32
    save(img.convert("RGB"), "03-prison-glass", "03 — ТЮРЕМНОЕ СТЕКЛО (решётка + матовое стекло)")


# ── 04 RECEIPT PRINTER — narrow strip right edge ───────────────────────────
def s04():
    img = scene().convert("RGBA")
    d = ImageDraw.Draw(img)
    rx0 = W - 300
    d.rectangle((rx0, 0, W, H), fill=(12, 12, 12, 240))
    d.line((rx0, 0, rx0, H), fill=(220, 220, 220), width=2)
    d.text((rx0 + 16, 20), "PRINT //", font=fnt(10), fill=(140, 140, 140))
    d.text((rx0 + 16, 40), TITLE, font=fnt(14, True), fill=(235, 235, 235))
    ty = 75
    for ln in wrap(d, LINE, fnt(11), 260):
        d.text((rx0 + 16, ty), ln, font=fnt(11), fill=(190, 190, 190))
        ty += 16
    d.line((rx0 + 10, ty + 8, W - 10, ty + 8), fill=(100, 100, 100))
    ty += 20
    for o in OPTS:
        d.text((rx0 + 16, ty), f"> {o}", font=fnt(11), fill=(210, 210, 210))
        ty += 22
        d.line((rx0 + 16, ty - 6, W - 16, ty - 6), fill=(50, 50, 50))
    # tear edge bottom
    pts = [(rx0, H - 20)]
    for x in range(rx0, W, 12):
        pts.append((x, H - 20 + (x % 24 // 12) * 8))
    pts += [(W, H), (rx0, H)]
    d.polygon(pts, fill=(240, 240, 240))
    save(img.convert("RGB"), "04-receipt-printer", "04 — ЧЕКОВЫЙ ПРИНТЕР (узкая лента справа)")


# ── 05 CARD FAN — poker fan from corner ────────────────────────────────────
def s05():
    img = scene().convert("RGBA")
    d = ImageDraw.Draw(img)
    d.text((40, H - 200), TITLE, font=fnt(20, True), fill=(235, 235, 235))
    ty = H - 170
    for ln in wrap(d, LINE, fnt(13), 500):
        d.text((40, ty), ln, font=fnt(13), fill=(200, 200, 200))
        ty += 20
    cx, cy = W - 200, H - 180
    for i, o in enumerate(OPTS):
        ang = -35 + i * 22
        card = Image.new("RGBA", (160, 220), (0, 0, 0, 0))
        cd = ImageDraw.Draw(card)
        cd.rounded_rectangle((0, 0, 158, 218), 8, fill=(220, 220, 220, 245), outline=(150, 150, 150))
        short = o.replace("?", "")
        cd.text((12, 90), short[:10], font=fnt(10), fill=(30, 30, 30))
        card = card.rotate(ang, resample=Image.Resampling.BICUBIC, expand=True)
        img.paste(card, (cx - 80 + i * 8, cy - 100 + i * 5), card)
    save(img.convert("RGB"), "05-card-fan", "05 — ВЕЕР КАРТ (каждый ответ — карта)")


# ── 06 SNIPER SCOPE — dialogue inside scope ring ───────────────────────────
def s06():
    img = scene().convert("RGBA")
    mask = Image.new("L", (W, H), 0)
    md = ImageDraw.Draw(mask)
    md.ellipse((W // 2 - 260, H // 2 - 260, W // 2 + 260, H // 2 + 260), fill=255)
    dark = Image.new("RGBA", (W, H), (0, 0, 0, 210))
    img = Image.composite(img, dark, mask)
    d = ImageDraw.Draw(img)
    cx, cy = W // 2, H // 2
    d.ellipse((cx - 255, cy - 255, cx + 255, cy + 255), outline=(220, 220, 220), width=3)
    d.ellipse((cx - 200, cy - 200, cx + 200, cy + 200), outline=(120, 120, 120), width=1)
    # crosshair
    d.line((cx - 30, cy, cx + 30, cy), fill=(200, 60, 60), width=2)
    d.line((cx, cy - 30, cx, cy + 30), fill=(200, 60, 60), width=2)
    d.text((cx - d.textlength(TITLE, font=fnt(16, True)) // 2, cy - 120), TITLE, font=fnt(16, True), fill=(240, 240, 240))
    ty = cy - 90
    for ln in wrap(d, LINE, fnt(12), 400):
        d.text((cx - d.textlength(ln, font=fnt(12)) // 2, ty), ln, font=fnt(12), fill=(210, 210, 210))
        ty += 18
    ty = cy + 40
    for o in OPTS:
        tw = d.textlength(o, font=fnt(11))
        d.text((cx - tw // 2, ty), f"[ {o} ]", font=fnt(11), fill=(200, 200, 200))
        ty += 22
    # range marks
    for a in range(0, 360, 30):
        rad = math.radians(a)
        x1 = cx + int(248 * math.cos(rad))
        y1 = cy + int(248 * math.sin(rad))
        x2 = cx + int(235 * math.cos(rad))
        y2 = cy + int(235 * math.sin(rad))
        d.line((x1, y1, x2, y2), fill=(180, 180, 180))
    save(img.convert("RGB"), "06-sniper-scope", "06 — ПРИЦЕЛ (диалог внутри оптики)")


# ── 07 RADIO TUNER — frequency presets as answers ──────────────────────────
def s07():
    img = scene().convert("RGBA")
    d = ImageDraw.Draw(img)
    bx, by, bw, bh = 100, H - 280, W - 200, 240
    d.rounded_rectangle((bx, by, bx + bw, by + bh), 20, fill=(14, 14, 14, 235), outline=(210, 210, 210), width=2)
    # dial arc
    d.arc((bx + 40, by + 20, bx + 200, by + 180), 200, 340, fill=(200, 200, 200), width=3)
    d.line((bx + 120, by + 100, bx + 155, by + 55), fill=(230, 230, 230), width=3)
    d.text((bx + 230, by + 30), TITLE, font=fnt(18, True), fill=(240, 240, 240))
    ty = by + 60
    for ln in wrap(d, LINE, fnt(13), bw - 260):
        d.text((bx + 230, ty), ln, font=fnt(13), fill=(200, 200, 200))
        ty += 20
    freqs = ["88.1", "91.4", "103.7", "107.2"]
    ty = by + 140
    for f, o in zip(freqs, OPTS):
        d.rectangle((bx + 220, ty, bx + bw - 20, ty + 28), fill=(200, 200, 200))
        d.text((bx + 230, ty + 6), f, font=fnt(10, True), fill=(30, 30, 30))
        d.text((bx + 290, ty + 6), o, font=fnt(10), fill=(30, 30, 30))
        ty += 34
    save(img.convert("RGB"), "07-radio-tuner", "07 — РАДИОПРИЁМНИК (ответы = частоты)")


# ── 08 WANTED POSTER — nailed poster center ────────────────────────────────
def s08():
    img = scene().convert("RGBA")
    d = ImageDraw.Draw(img)
    px0, py0, pw, ph = W // 2 - 220, 100, 440, 520
    d.rectangle((px0, py0, px0 + pw, py0 + ph), fill=(210, 205, 195, 245), outline=(120, 110, 100), width=3)
    # nail holes
    for nx in (px0 + 20, px0 + pw - 20):
        d.ellipse((nx - 6, py0 + 10, nx + 6, py0 + 22), fill=(80, 80, 80))
    d.text((px0 + pw // 2 - d.textlength("РАЗЫСКИВАЕТСЯ", font=fnt(14, True)) // 2, py0 + 30), "РАЗЫСКИВАЕТСЯ", font=fnt(14, True), fill=(40, 40, 40))
    d.line((px0 + 30, py0 + 55, px0 + pw - 30, py0 + 55), fill=(60, 60, 60), width=2)
    d.text((px0 + 30, py0 + 70), TITLE, font=fnt(22, True), fill=(25, 25, 25))
    ty = py0 + 110
    for ln in wrap(d, LINE, fnt(13), pw - 60):
        d.text((px0 + 30, ty), ln, font=fnt(13), fill=(45, 45, 45))
        ty += 20
    d.text((px0 + 30, ty + 20), "СООБЩИ ИНФОРМАЦИЮ:", font=fnt(11, True), fill=(50, 50, 50))
    ty += 50
    for o in OPTS:
        d.text((px0 + 40, ty), f"• {o}", font=fnt(12), fill=(35, 35, 35))
        ty += 26
    d.text((px0 + pw // 2 - 60, py0 + ph - 40), "НАГРАДА: ???", font=fnt(12, True), fill=(60, 60, 60))
    save(img.convert("RGB"), "08-wanted-poster", "08 — ПЛАКАТ «РОЗЫСК» (прибит к стене)")


# ── 09 CHALK WALL — graffiti scratch text ──────────────────────────────────
def s09():
    img = scene().convert("RGBA")
    d = ImageDraw.Draw(img)
    # wall texture
    rng = random.Random(42)
    for _ in range(3000):
        x, y = rng.randint(0, W), rng.randint(H // 2, H)
        g = rng.randint(45, 75)
        d.point((x, y), fill=(g, g - 5, g - 8, 255))
    d.text((60, H - 280), TITLE, font=fnt(26, True), fill=(220, 220, 215))
    ty = H - 240
    for ln in wrap(d, LINE, fnt(15), 700):
        # double stroke chalk effect
        for ox, oy in ((1, 1), (0, 0)):
            d.text((62 + ox, ty + oy), ln, font=fnt(15), fill=(180, 180, 175) if ox else (230, 230, 225))
        ty += 24
    ty += 15
    for o in OPTS:
        d.line((55, ty + 18, 55 + d.textlength(o, font=fnt(14)) + 20, ty + 18), fill=(100, 100, 95), width=2)
        d.text((60, ty), f">> {o}", font=fnt(14), fill=(210, 210, 205))
        ty += 30
    save(img.convert("RGB"), "09-chalk-wall", "09 — МЕЛ НА СТЕНЕ (граффити, без UI-рамки)")


# ── 10 GLASS SHARDS — fragmented asymmetric pieces ─────────────────────────
def s10():
    img = scene().convert("RGBA")
    d = ImageDraw.Draw(img)
    shards = [
        ((80, H - 260), (420, H - 200), (400, H - 80), (60, H - 120)),
        ((450, H - 300), (900, H - 280), (880, H - 140), (430, H - 160)),
        ((100, H - 110), (350, H - 90), (330, H - 30), (80, H - 40)),
        ((380, H - 100), (650, H - 85), (640, H - 25), (370, H - 35)),
        ((680, H - 95), (950, H - 80), (940, H - 20), (670, H - 30)),
        ((970, H - 280), (1180, H - 260), (1170, H - 140), (960, H - 160)),
    ]
    texts = [TITLE, LINE, *OPTS]
    for i, (poly, txt) in enumerate(zip(shards, texts)):
        d.polygon(poly, fill=(18, 18, 18, 220), outline=(210, 210, 210))
        x, y = poly[0][0] + 14, poly[0][1] + 12
        size = 16 if i == 0 else (12 if i == 1 else 11)
        bold = i == 0
        if i == 1:
            for j, ln in enumerate(wrap(d, txt, fnt(size), poly[1][0] - poly[0][0] - 30)):
                d.text((x, y + j * 16), ln, font=fnt(size), fill=(210, 210, 210))
        else:
            short = txt if len(txt) < 22 else txt[:20] + "…"
            d.text((x, y), short, font=fnt(size, bold), fill=(230, 230, 230) if bold else (200, 200, 200))
    save(img.convert("RGB"), "10-glass-shards", "10 — ОСКОЛКИ СТЕКЛА (каждая фраза — свой осколок)")


def sheet():
    files = sorted(OUT.glob("[0-9]*.png"))
    cols, rows = 2, 5
    tw, th = 640, 380
    s = Image.new("RGB", (cols * tw + 20, rows * th + 50), (16, 16, 16))
    for i, p in enumerate(files[:10]):
        t = Image.open(p)
        t.thumbnail((tw - 8, th - 8))
        c, r = i % cols, i // cols
        s.paste(t, (10 + c * tw + (tw - t.width) // 2, 30 + r * th + (th - t.height) // 2))
    s.save(OUT / "00-all-v2.png", optimize=True)
    print(OUT / "00-all-v2.png")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    s01()
    s02_save()
    s03()
    s04()
    s05()
    s06()
    s07()
    s08()
    s09()
    s10()
    sheet()


if __name__ == "__main__":
    main()
