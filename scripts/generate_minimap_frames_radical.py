#!/usr/bin/env python3
"""
Radical minimap overlays — each skin must look NOTHING like the others at a glance.

Rules:
  - compass hole 1108×50 and map hole 1120×580 stay fixed
  - no shared bezel template
  - different silhouette, palette, fill density, and object type per skin
"""

from __future__ import annotations

import math
import random
import zipfile
from pathlib import Path
from typing import Callable

from PIL import Image, ImageChops, ImageDraw, ImageFilter

from generate_minimap_frames import (
    COMPASS_GAP,
    COMPASS_H,
    INNER_W,
    MAP_H,
    PAD_BOTTOM,
    PAD_SIDE,
    PAD_TOP,
    RENDER_SCALE,
    canvas_size,
    compass_center,
    finish,
    inner_compass_box,
    inner_map_box,
    load_font,
    sbox,
    sc,
    spoly,
)

OUT = Path("/workspace/minimap-frames/radical")


def layer(w: int, h: int) -> Image.Image:
    return Image.new("RGBA", (w, h), (0, 0, 0, 0))


def shadow(img: Image.Image, ox: int = 4, oy: int = 5, blur: int = 8) -> Image.Image:
    a = img.split()[3]
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sh.paste((0, 0, 0, 140), (sc(ox), sc(oy)), a)
    return sh.filter(ImageFilter.GaussianBlur(sc(blur)))


def bevel_plate(base: Image.Image, box: tuple, color: tuple, seed: int, radius: int = 0):
    """Raised metal/plastic plate with highlight + shadow edges."""
    x0, y0, x1, y1 = sbox(box)
    plate = layer(base.width, base.height)
    d = ImageDraw.Draw(plate)
    if radius:
        d.rounded_rectangle((x0, y0, x1, y1), radius=sc(radius), fill=color)
    else:
        d.rectangle((x0, y0, x1, y1), fill=color)
    hi = layer(base.width, base.height)
    hd = ImageDraw.Draw(hi)
    hd.line([(x0, y0), (x1, y0)], fill=(min(255, color[0] + 40), min(255, color[1] + 40), min(255, color[2] + 40), 180), width=sc(2))
    hd.line([(x0, y0), (x0, y1)], fill=(min(255, color[0] + 30), min(255, color[1] + 30), min(255, color[2] + 30), 160), width=sc(2))
    lo = layer(base.width, base.height)
    ld = ImageDraw.Draw(lo)
    ld.line([(x0, y1), (x1, y1)], fill=(max(0, color[0] - 50), max(0, color[1] - 50), max(0, color[2] - 50), 200), width=sc(3))
    ld.line([(x1, y0), (x1, y1)], fill=(max(0, color[0] - 40), max(0, color[1] - 40), max(0, color[2] - 40), 180), width=sc(2))
    rng = random.Random(seed)
    tex = ImageDraw.Draw(plate)
    for _ in range(80):
        x, y = rng.randint(x0, x1), rng.randint(y0, y1)
        g = color[0] + rng.randint(-20, 20)
        tex.point((x, y), fill=(g, g - 4, g - 8, 200))
    return Image.alpha_composite(Image.alpha_composite(shadow(plate), plate), Image.alpha_composite(hi, lo))


def stamp(d: ImageDraw.ImageDraw, text: str, x: int, y: int, color=(220, 210, 180, 255), bg=None):
    f = load_font(9, True)
    bb = f.getbbox(text)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    if bg:
        d.rectangle((sc(x) - sc(4), sc(y) - sc(2), sc(x) + tw + sc(8), sc(y) + th + sc(4)), fill=bg)
    d.text((sc(x), sc(y)), text, font=f, fill=color)


def build(painter: Callable, marker: str, seed: int) -> Image.Image:
    w, h = canvas_size()
    rw, rh = sc(w), sc(h)
    base = layer(rw, rh)
    painter(base, seed, rw, rh)

    mask = Image.new("L", (rw, rh), 255)
    md = ImageDraw.Draw(mask)
    md.rounded_rectangle(sbox(inner_compass_box()), radius=sc(2), fill=0)
    md.rounded_rectangle(sbox(inner_map_box()), radius=sc(2), fill=0)
    rgba = base.split()
    alpha = Image.composite(rgba[3], Image.new("L", (rw, rh), 0), mask)
    base = Image.merge("RGBA", [*rgba[:3], alpha])

    cx, cy = compass_center()
    cx, cy = sc(cx), sc(cy)
    d = ImageDraw.Draw(base)
    col = (230, 55, 40, 255)
    if marker == "strip":
        _, y0, _, y1 = sbox(inner_compass_box())
        d.rectangle((cx - sc(2), y0, cx + sc(2), y1), fill=col)
    elif marker == "square":
        s = sc(7)
        d.rectangle((cx - s, cy - s, cx + s, cy + s), outline=col, width=sc(2))
    elif marker == "ring":
        d.ellipse((cx - sc(9), cy - sc(9), cx + sc(9), cy + sc(9)), outline=col, width=sc(2))
    elif marker == "cross":
        r = sc(10)
        d.line((cx - r, cy, cx + r, cy), fill=col, width=sc(2))
        d.line((cx, cy - r, cx, cy + r), fill=col, width=sc(2))
    elif marker == "triangle":
        d.polygon([(cx, cy - sc(10)), (cx - sc(7), cy + sc(6)), (cx + sc(7), cy + sc(6))], fill=col)
    else:
        d.polygon([(cx, cy - sc(10)), (cx - sc(7), cy + sc(6)), (cx + sc(7), cy + sc(6))], fill=col)

    return finish(base.resize((w, h), Image.Resampling.LANCZOS), seed)


def rrect(d: ImageDraw.ImageDraw, x0: int, y0: int, x1: int, y1: int, **kw):
    d.rectangle(sbox((min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))), **kw)


# ── 1. CORNER BRACKETS ONLY — ~85% canvas transparent ─────────────────────
def skin_corners_only(base: Image.Image, seed: int, rw: int, rh: int):
    ix0, iy0, ix1, iy1 = inner_map_box()
    cx0, cy0, cx1, cy1 = inner_compass_box()
    d = ImageDraw.Draw(base)
    arm = 70
    thick = 14
    col = (168, 152, 118, 255)
    dark = (68, 60, 48, 255)
    for (x, y, dx, dy) in [
        (ix0 - 8, iy0 - 8, 1, 1),
        (ix1 + 8, iy0 - 8, -1, 1),
        (ix0 - 8, iy1 + 8, 1, -1),
        (ix1 + 8, iy1 + 8, -1, -1),
        (cx0 - 6, cy0 - 6, 1, 1),
        (cx1 + 6, cy0 - 6, -1, 1),
        (cx0 - 6, cy1 + 6, 1, -1),
        (cx1 + 6, cy1 + 6, -1, -1),
    ]:
        rrect(d, x, y, x + dx * arm, y + dy * thick, fill=col, outline=dark, width=sc(1))
        rrect(d, x, y, x + dx * thick, y + dy * arm, fill=col, outline=dark, width=sc(1))
        bx, by = x + dx * 18, y + dy * 18
        d.ellipse(sbox((bx - 5, by - 5, bx + 5, by + 5)), fill=(98, 92, 78, 255), outline=dark)
    # thin connector wires only
    d.line(spoly([(ix0, iy0 - 8), (ix1, iy0 - 8)]), fill=(120, 110, 90, 120), width=sc(1))
    d.line(spoly([(ix0, iy1 + 8), (ix1, iy1 + 8)]), fill=(120, 110, 90, 120), width=sc(1))
    stamp(d, "BRACKET HUD", ix0, iy0 - 32, (200, 185, 140, 255))


# ── 2. CORK BOARD — full tan surface, pushpins, string ─────────────────────
def skin_cork_board(base: Image.Image, seed: int, rw: int, rh: int):
    cw, ch = rw // RENDER_SCALE, rh // RENDER_SCALE
    board = sbox((0, 0, cw, ch))
    cork = layer(rw, rh)
    d = ImageDraw.Draw(cork)
    d.rectangle(board, fill=(148, 108, 72, 255))
    rng = random.Random(seed)
    for _ in range(600):
        x, y = rng.randint(board[0], board[2]), rng.randint(board[1], board[3])
        c = 130 + rng.randint(-25, 25)
        d.point((x, y), fill=(c, c - 28, c - 48, 255))
    base.alpha_composite(cork)
    d = ImageDraw.Draw(base)
    ix0, iy0, ix1, iy1 = inner_map_box()
    cx0, cy0, cx1, cy1 = inner_compass_box()
    # paper edge shadows around holes (drawn on cork, cut later)
    for box in (inner_compass_box(), inner_map_box()):
        x0, y0, x1, y1 = box
        d.rectangle(sbox((x0 - 5, y0 - 5, x1 + 5, y1 + 5)), outline=(88, 62, 40, 255), width=sc(3))
    # red string between pins
    pins = [(20, 20), (cw - 20, 24), (cw - 16, ch - 16), (18, ch - 12)]
    for p in pins:
        d.ellipse(sbox((p[0] - 7, p[1] - 7, p[0] + 7, p[1] + 7)), fill=(180, 40, 36, 255))
    d.line(spoly([pins[0], pins[1], pins[2], pins[3], pins[0]]), fill=(160, 36, 32, 200), width=sc(2))
    stamp(d, "OPS BOARD", 24, 18, (240, 230, 200, 255), (100, 70, 45, 220))
    stamp(d, "COMPASS", cx0 + 4, cy0 - 18, (80, 55, 35, 255))
    stamp(d, "MAP", ix0 + 4, iy0 + 4, (80, 55, 35, 255))


# ── 3. NIGHT VISION — green rubber, black plastic, L-shape ────────────────
def skin_night_vision(base: Image.Image, seed: int, rw: int, rh: int):
    cw, ch = rw // RENDER_SCALE, rh // RENDER_SCALE
    ix0, iy0, ix1, iy1 = inner_map_box()
    cx0, cy0, cx1, cy1 = inner_compass_box()
    green = (48, 72, 38, 255)
    black = (18, 20, 16, 255)
    # L-shaped housing: left bar + bottom bar only
    base.alpha_composite(bevel_plate(base, (0, 0, 62, ch), black, seed))
    base.alpha_composite(bevel_plate(base, (0, ch - 48, cw, ch), black, seed + 1))
    base.alpha_composite(bevel_plate(base, (0, 0, cw, 44), black, seed + 2))
    d = ImageDraw.Draw(base)
    # rubber eyecups flanking compass
    for ex in (cx0 - 90, cx1 + 90):
        ecy = (cy0 + cy1) // 2
        d.ellipse(sbox((ex - 42, ecy - 36, ex + 42, ecy + 36)), fill=green, outline=(28, 42, 22, 255), width=sc(3))
        d.ellipse(sbox((ex - 22, ecy - 20, ex + 22, ecy + 20)), fill=(12, 18, 10, 255))
    # battery box sticking left
    base.alpha_composite(bevel_plate(base, (-20, ch // 2 - 40, 30, ch // 2 + 40), (36, 38, 32, 255), seed + 3, 4))
    stamp(d, "ПНВ-4", 72, 10, (120, 180, 90, 255))
    stamp(d, "NVG MAP", 72, ch - 38, (120, 180, 90, 255))


# ── 4. HAZARD CASE — yellow/black stripes, industrial ─────────────────────
def skin_hazard_case(base: Image.Image, seed: int, rw: int, rh: int):
    cw, ch = rw // RENDER_SCALE, rh // RENDER_SCALE
    ix0, iy0, ix1, iy1 = inner_map_box()
    # thick left column entirely hazard striped
    col_w = 88
    stripe = layer(rw, rh)
    sd = ImageDraw.Draw(stripe)
    for y in range(0, ch, 16):
        c = (220, 178, 28, 255) if (y // 16) % 2 == 0 else (22, 20, 16, 255)
        sd.rectangle(sbox((0, y, col_w, y + 16)), fill=c)
    base.alpha_composite(stripe)
    # grey metal remainder — only thin top + right + bottom lips
    base.alpha_composite(bevel_plate(base, (col_w - 4, 0, cw, 36), (96, 98, 92, 255), seed))
    base.alpha_composite(bevel_plate(base, (cw - 28, 0, cw, ch), (88, 90, 84, 255), seed + 1))
    base.alpha_composite(bevel_plate(base, (col_w, ch - 32, cw, ch), (92, 94, 88, 255), seed + 2))
    d = ImageDraw.Draw(base)
    stamp(d, "RADIOACTIVE?", col_w + 8, 8, (240, 200, 40, 255), (20, 18, 14, 200))
    stamp(d, "DO NOT OPEN", col_w + 8, 24, (240, 200, 40, 255), (20, 18, 14, 200))
    # metal latch
    d.rectangle(sbox((cw - 36, iy1 + 20, cw - 8, iy1 + 52)), fill=(72, 74, 68, 255), outline=(40, 40, 36, 255), width=sc(2))


# ── 5. MANILA ENVELOPE — cream paper, triangular flap, string tie ─────────
def skin_envelope(base: Image.Image, seed: int, rw: int, rh: int):
    cw, ch = rw // RENDER_SCALE, rh // RENDER_SCALE
    cream = (210, 192, 148, 255)
    d = ImageDraw.Draw(base)
    # body
    d.polygon(spoly([(0, 50), (cw, 40), (cw, ch), (0, ch)]), fill=cream, outline=(148, 128, 92, 255))
    # triangular flap
    d.polygon(spoly([(0, 50), (cw // 2, 120), (cw, 40)]), fill=(196, 178, 136, 255), outline=(138, 118, 84, 255))
    # string closure circle
    d.ellipse(sbox((cw // 2 - 28, 88, cw // 2 + 28, 144)), outline=(120, 90, 60, 255), width=sc(2))
    d.arc(sbox((cw // 2 - 20, 100, cw // 2 + 20, 130)), 20, 160, fill=(100, 75, 50, 255), width=sc(2))
    # address lines
    for y in (160, 178, 196):
        d.line(spoly([(40, y), (cw - 60, y)]), fill=(168, 148, 110, 120), width=sc(1))
    stamp(d, "CLASSIFIED MAP", 44, 130, (100, 70, 45, 255))


# ── 6. BRASS PORTHOLE — circular ring, canvas corners empty ───────────────
def skin_brass_porthole(base: Image.Image, seed: int, rw: int, rh: int):
    cw, ch = rw // RENDER_SCALE, rh // RENDER_SCALE
    cx, cy = cw // 2, ch // 2 + 10
    ring = layer(rw, rh)
    d = ImageDraw.Draw(ring)
    for r, col, w in [(390, (42, 36, 28, 255), 28), (362, (168, 132, 62, 255), 22), (340, (108, 86, 44, 255), 8)]:
        d.ellipse(sbox((cx - r, cy - r, cx + r, cy + r)), outline=col, width=sc(w))
    # bolts
    for a in range(0, 360, 24):
        rad = math.radians(a)
        bx = cx + int(374 * math.cos(rad))
        by = cy + int(374 * math.sin(rad))
        d.ellipse(sbox((bx - 8, by - 8, bx + 8, by + 8)), fill=(140, 112, 56, 255), outline=(68, 54, 28, 255))
    base.alpha_composite(ring)
    d = ImageDraw.Draw(base)
    stamp(d, "BULKHEAD NAV", cx - 80, cy - 420, (200, 165, 90, 255), (40, 32, 20, 200))


# ── 7. TROPHY PLAQUE — wood shield, antlers off top ───────────────────────
def skin_trophy_plaque(base: Image.Image, seed: int, rw: int, rh: int):
    cw, ch = rw // RENDER_SCALE, rh // RENDER_SCALE
    cx = cw // 2
    shield = spoly([(cx, -60), (cx + 220, 40), (cx + 180, ch - 4), (cx - 180, ch - 4), (cx - 220, 40)])
    d = ImageDraw.Draw(base)
    d.polygon(shield, fill=(88, 58, 34, 255), outline=(48, 30, 18, 255))
    rng = random.Random(seed)
    for y in range(-20, ch, 6):
        c = 78 + rng.randint(-12, 12)
        d.line(spoly([(cx - 200, y), (cx + 200, y)]), fill=(c, c - 18, c - 30, 255), width=sc(2))
    # antlers
    for side in (-1, 1):
        d.line(spoly([(cx + side * 40, 20), (cx + side * 120, -80)]), fill=(200, 190, 170, 255), width=sc(6))
        d.line(spoly([(cx + side * 80, -20), (cx + side * 160, -50)]), fill=(200, 190, 170, 255), width=sc(4))
        d.line(spoly([(cx + side * 100, -40), (cx + side * 140, -100)]), fill=(200, 190, 170, 255), width=sc(3))
    stamp(d, "TROPHY MAP", cx - 52, 50, (220, 200, 160, 255), (50, 32, 18, 200))


# ── 8. STACKED POSTCARDS — offset cream cards, stamp marks ─────────────────
def skin_postcards(base: Image.Image, seed: int, rw: int, rh: int):
    cw, ch = rw // RENDER_SCALE, rh // RENDER_SCALE
    offsets = [(34, 28, (228, 220, 200, 255)), (18, 14, (218, 208, 186, 255)), (0, 0, (240, 234, 216, 255))]
    for ox, oy, col in offsets:
        card = layer(rw, rh)
        cd = ImageDraw.Draw(card)
        cd.rounded_rectangle(sbox((ox, oy, cw - 6, ch - 6)), 6, fill=col, outline=(160, 148, 120, 255), width=sc(2))
        base.alpha_composite(shadow(card, 6, 8, 10))
        base.alpha_composite(card)
    d = ImageDraw.Draw(base)
    # postage stamp top-right
    d.rectangle(sbox((cw - 110, 20, cw - 30, 70)), fill=(180, 60, 50, 255), outline=(120, 40, 32, 255), width=sc(1))
    for px in range(cw - 108, cw - 32, 8):
        d.line((sc(px), sc(20), sc(px), sc(24)), fill=(240, 230, 210, 255), width=sc(1))
    stamp(d, "CHERNO", 36, 36, (100, 80, 60, 255))
    stamp(d, "POST", 36, 52, (100, 80, 60, 255))


# ── 9. SNIPER CROSSHAIR — thin lines across whole canvas ──────────────────
def skin_crosshair(base: Image.Image, seed: int, rw: int, rh: int):
    cw, ch = rw // RENDER_SCALE, rh // RENDER_SCALE
    ix0, iy0, ix1, iy1 = inner_map_box()
    cx, cy = cw // 2, ch // 2
    d = ImageDraw.Draw(base)
    line = (200, 40, 36, 180)
    # full cross
    d.line(spoly([(0, cy), (cw, cy)]), fill=line, width=sc(1))
    d.line(spoly([(cx, 0), (cx, ch)]), fill=line, width=sc(1))
    # mil dots
    for i in range(-8, 9):
        if i == 0:
            continue
        d.ellipse(sbox((cx + i * 40 - 2, cy - 2, cx + i * 40 + 2, cy + 2)), fill=(200, 40, 36, 220))
        d.ellipse(sbox((cx - 2, cy + i * 40 - 2, cx + 2, cy + i * 40 + 2)), fill=(200, 40, 36, 220))
    # corner range marks only
    for px, py, dx, dy in [(ix0 - 30, iy0 - 30, 1, 1), (ix1 + 30, iy0 - 30, -1, 1), (ix0 - 30, iy1 + 30, 1, -1), (ix1 + 30, iy1 + 30, -1, -1)]:
        d.line(spoly([(px, py), (px + dx * 50, py)]), fill=(180, 180, 170, 200), width=sc(2))
        d.line(spoly([(px, py), (px, py + dy * 50)]), fill=(180, 180, 170, 200), width=sc(2))
    stamp(d, "MIL RETICLE", 12, 8, (200, 50, 40, 255))


# ── 10. SOVIET CAR VISOR — fabric flap from top, clip ─────────────────────
def skin_car_visor(base: Image.Image, seed: int, rw: int, rh: int):
    cw, ch = rw // RENDER_SCALE, rh // RENDER_SCALE
    ix0, iy0, ix1, iy1 = inner_map_box()
    flap = spoly([(0, 0), (cw, 0), (cw - 30, 160), (30, 150)])
    d = ImageDraw.Draw(base)
    d.polygon(flap, fill=(52, 48, 44, 255), outline=(28, 26, 22, 255))
    rng = random.Random(seed)
    for y in range(10, 150, 5):
        c = 48 + rng.randint(-8, 8)
        d.line(spoly([(20, y), (cw - 20, y + 4)]), fill=(c, c - 4, c - 6, 255), width=sc(2))
    # clip at top center
    d.rounded_rectangle(sbox((cw // 2 - 36, 0, cw // 2 + 36, 22)), 4, fill=(100, 98, 92, 255), outline=(60, 58, 54, 255))
    # mirror patch left (faded)
    d.ellipse(sbox((8, 40, 90, 120)), fill=(140, 142, 138, 90), outline=(100, 100, 96, 120), width=sc(2))
    # sagging bottom edge fabric
    pts = [(20, ch - 20)]
    for x in range(20, cw - 10, 25):
        pts.append((x, ch - 12 + rng.randint(-6, 4)))
    pts += [(cw - 10, ch - 8), (20, ch - 20)]
    d.polygon(spoly(pts), fill=(44, 40, 36, 255))
    stamp(d, "ЖИГУЛИ VISOR", 100, 18, (190, 180, 160, 255))


SKINS = [
    ("radical-01-corners", "Corner Brackets", "85% transparent, metal corners only", "cross", skin_corners_only),
    ("radical-02-cork-board", "Cork Ops Board", "Full tan cork, pins, red string", "square", skin_cork_board),
    ("radical-03-night-vision", "Night Vision NVG", "Green rubber cups, L-frame black", "ring", skin_night_vision),
    ("radical-04-hazard-case", "Hazard Case", "Yellow/black stripes, metal lips", "strip", skin_hazard_case),
    ("radical-05-envelope", "Manila Envelope", "Cream paper, flap, string tie", "triangle", skin_envelope),
    ("radical-06-porthole", "Brass Porthole", "Circular ring, empty corners", "ring", skin_brass_porthole),
    ("radical-07-trophy", "Trophy Plaque", "Wood shield, antlers up", "triangle", skin_trophy_plaque),
    ("radical-08-postcards", "Stacked Postcards", "Offset cream cards, postage", "strip", skin_postcards),
    ("radical-09-crosshair", "Mil Crosshair", "Thin red grid, minimal frame", "cross", skin_crosshair),
    ("radical-10-visor", "Soviet Visor", "Fabric flap from top, mirror patch", "square", skin_car_visor),
]


def contact_sheet(images: list[tuple[str, Image.Image]], path: Path):
    cols, rows = 5, 2
    tw, th = 360, 230
    sheet = Image.new("RGBA", (cols * tw + 20, rows * th + 60), (32, 30, 28, 255))
    d = ImageDraw.Draw(sheet)
    f = load_font(8, True)
    for i, (name, img) in enumerate(images):
        c, r = i % cols, i // cols
        t = img.copy()
        t.thumbnail((tw - 10, th - 30), Image.Resampling.LANCZOS)
        x = 10 + c * tw + (tw - t.width) // 2
        y = 36 + r * th + (th - 30 - t.height) // 2
        sheet.paste(t, (x, y), t)
        d.text((10 + c * tw + 4, 8 + r * th), name, font=f, fill=(220, 210, 180, 255))
    sheet.save(path, "PNG", optimize=True)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    saved: list[Path] = []
    previews: list[tuple[str, Image.Image]] = []
    for i, (slug, title, desc, marker, painter) in enumerate(SKINS):
        img = build(painter, marker, seed=2000 + i * 67)
        p = OUT / f"{slug}.png"
        img.save(p, "PNG", optimize=True)
        p4 = OUT / f"{slug}-4k.png"
        img.resize((img.width * 2, img.height * 2), Image.Resampling.LANCZOS).save(p4, "PNG", optimize=True)
        saved += [p, p4]
        previews.append((f"{i + 1:02d}", img))
        print(f"{slug}: {title} — {desc}")

    cs = OUT / "00-radical-contact-sheet.png"
    contact_sheet(previews, cs)
    saved.append(cs)

    zp = OUT / "minimap-frames-radical-10.zip"
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in saved:
            zf.write(p, p.name)
    print(f"Saved {zp}")


if __name__ == "__main__":
    main()
