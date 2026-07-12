#!/usr/bin/env python3
"""
10 structurally different minimap overlays — NOT texture reskins.

Fixed transparent windows only:
  compass 1108×50, map 1120×580 (same position every skin).
Everything else: unique silhouette, framing, labels, and layout.
"""

from __future__ import annotations

import math
import random
import zipfile
from pathlib import Path
from typing import Callable

from PIL import Image, ImageDraw

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
    metal_tex,
    rust_splotches,
    sbox,
    sc,
    spoly,
    wood_tex,
)

OUT = Path("/workspace/minimap-frames/diverse")


def tag(d: ImageDraw.ImageDraw, text: str, x: int, y: int, color=(200, 190, 160, 255), bg=(14, 12, 10, 230)):
    f = load_font(9, True)
    bb = f.getbbox(text)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    d.rectangle((sc(x) - sc(3), sc(y) - sc(1), sc(x) + tw + sc(6), sc(y) + th + sc(3)), fill=bg)
    d.text((sc(x), sc(y)), text, font=f, fill=color)


def tape_strip(d: ImageDraw.ImageDraw, p0: tuple, p1: tuple, w: int = 12):
    d.line(spoly([p0, p1]), fill=(148, 140, 108, 210), width=sc(w))


def hole_edge_splinters(d: ImageDraw.ImageDraw, box: tuple[int, int, int, int], seed: int, inward: bool = True):
    """Rough cut edges around a transparent hole."""
    rng = random.Random(seed)
    x0, y0, x1, y1 = box
    pts = []
    for x in range(x0, x1, 8):
        pts.append((x, y0 + rng.randint(-3, 3)))
    for y in range(y0, y1, 8):
        pts.append((x1 + rng.randint(-3, 3), y))
    for x in range(x1, x0, -8):
        pts.append((x, y1 + rng.randint(-3, 3)))
    for y in range(y1, y0, -8):
        pts.append((x0 + rng.randint(-3, 3), y))
    col = (88, 68, 44, 255) if inward else (72, 54, 34, 255)
    d.polygon(spoly(pts), outline=col, fill=None)
    for _ in range(18):
        side = rng.choice("tblr")
        if side == "t":
            x, y = rng.randint(x0, x1), y0
        elif side == "b":
            x, y = rng.randint(x0, x1), y1
        elif side == "l":
            x, y = x0, rng.randint(y0, y1)
        else:
            x, y = x1, rng.randint(y0, y1)
        d.line(spoly([(x, y), (x + rng.randint(-6, 6), y + rng.randint(-6, 6))]), fill=(58, 42, 26, 255), width=sc(1))


def build(painter: Callable, marker: str, seed: int) -> Image.Image:
    w, h = canvas_size()
    rw, rh = sc(w), sc(h)
    base = Image.new("RGBA", (rw, rh), (0, 0, 0, 0))
    painter(ImageDraw.Draw(base), base, seed, rw, rh)

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
    col = (210, 48, 36, 255)
    if marker == "strip":
        _, y0, _, y1 = sbox(inner_compass_box())
        d.rectangle((cx - sc(2), y0, cx + sc(2), y1), fill=col)
    elif marker == "square":
        s = sc(7)
        d.rectangle((cx - s, cy - s, cx + s, cy + s), outline=col, width=sc(2))
    elif marker == "ring":
        d.ellipse((cx - sc(8), cy - sc(8), cx + sc(8), cy + sc(8)), outline=col, width=sc(2))
    elif marker == "cross":
        r = sc(9)
        d.line((cx - r, cy, cx + r, cy), fill=col, width=sc(2))
        d.line((cx, cy - r, cx, cy + r), fill=col, width=sc(2))
    else:
        d.polygon([(cx, cy - sc(9)), (cx - sc(6), cy + sc(5)), (cx + sc(6), cy + sc(5))], fill=col)

    return finish(base.resize((w, h), Image.Resampling.LANCZOS), seed)


# ── 1. PLYWOOD CUTOUT — almost no device, just a board with sawn holes ───────
def skin_plywood_cutout(d, base, seed, rw, rh):
    cw, ch = rw // RENDER_SCALE, rh // RENDER_SCALE
    pts = spoly([(6, 18), (cw - 4, 8), (cw - 2, ch - 6), (16, ch - 2), (2, ch // 2)])
    d.polygon(pts, fill=(102, 76, 48, 255), outline=(62, 44, 28, 255))
    wood_tex(d, (pts[0][0], pts[0][1], pts[1][0], pts[2][1]), seed, (102, 76, 48))
    hole_edge_splinters(d, inner_compass_box(), seed + 1)
    hole_edge_splinters(d, inner_map_box(), seed + 2)
    tape_strip(d, (10, 14), (cw - 10, 28), 14)
    tape_strip(d, (8, ch - 30), (cw - 6, ch - 12), 12)
    tape_strip(d, (6, 42), (30, ch - 24), 10)
    tag(d, "SAWN BOARD", 18, 20, (68, 48, 28, 255), (148, 140, 108, 200))
    tag(d, "COMPASS", PAD_SIDE + 6, inner_compass_box()[1] - 15, (90, 70, 44, 255), (148, 140, 108, 200))
    tag(d, "MAP", PAD_SIDE + 6, PAD_TOP + COMPASS_H + 2, (90, 70, 44, 255), (148, 140, 108, 200))


# ── 2. WALKIE-TALKIE — tall left rail, antenna off top, asymmetric ───────────
def skin_walkie_talkie(d, base, seed, rw, rh):
    cw, ch = rw // RENDER_SCALE, rh // RENDER_SCALE
    ix0, iy0, ix1, iy1 = PAD_SIDE, PAD_TOP, PAD_SIDE + INNER_W, PAD_TOP + COMPASS_H + COMPASS_GAP + MAP_H
    rail = sbox((0, 0, 52, ch))
    d.rectangle(rail, fill=(38, 40, 34, 255), outline=(20, 20, 18, 255), width=sc(2))
    for y in range(60, ch - 40, 22):
        d.ellipse(sbox((10, y, 42, y + 18)), fill=(28, 30, 24, 255), outline=(70, 68, 60, 255), width=sc(1))
    # antenna mast off canvas
    ax = 26
    d.line(spoly([(ax, -30), (ax, 8)]), fill=(110, 108, 100, 255), width=sc(4))
    d.line(spoly([(ax, -30), (ax + 18, -50)]), fill=(110, 108, 100, 255), width=sc(2))
    d.ellipse(sbox((ax - 4, -34, ax + 4, -26)), fill=(180, 50, 40, 255))
    # thin top bar only
    d.rectangle(sbox((52, 12, cw - 8, iy0 - 6)), fill=(44, 46, 40, 255))
    # bottom battery hump
    d.rounded_rectangle(sbox((48, iy1 + 4, cw - 12, ch - 2)), 6, fill=(34, 36, 30, 255), outline=(18, 18, 16, 255), width=sc(2))
    for x in range(60, cw - 20, 16):
        d.rectangle(sbox((x, iy1 + 14, x + 10, iy1 + 22)), fill=(16, 16, 14, 255))
    # speaker grille right of map
    gx = ix1 + 6
    for y in range(iy0 + 80, iy1 - 20, 12):
        d.rectangle(sbox((gx, y, cw - 6, y + 6)), fill=(20, 20, 18, 255))
    # compass freq scale
    for x in range(ix0 + 20, ix1 - 20, 40):
        d.line(spoly([(x, iy0 - 4), (x, iy0 + 2)]), fill=(160, 150, 110, 255), width=sc(1))
    tag(d, "CH-07", 58, 18, (170, 168, 140, 255))
    tag(d, "COMPASS", ix0 + 10, iy0 - 18, (170, 158, 110, 255))
    tag(d, "MAP", ix0 + 10, iy0 + COMPASS_H + COMPASS_GAP + 4, (170, 158, 110, 255))


# ── 3. FORK CLAMP — no box; metal triple clamp + fork legs only ─────────────
def skin_fork_clamp(d, base, seed, rw, rh):
    cw, ch = rw // RENDER_SCALE, rh // RENDER_SCALE
    ix0, iy0, ix1, _ = PAD_SIDE, PAD_TOP, PAD_SIDE + INNER_W, None
    comp_bot = iy0 + COMPASS_H
    # triple clamp plate across compass
    plate = sbox((ix0 - 16, iy0 - 22, ix1 + 16, comp_bot + 8))
    d.rectangle(plate, fill=(72, 74, 68, 255), outline=(40, 40, 36, 255), width=sc(2))
    metal_tex(d, plate, seed)
    for bx in range(ix0 - 8, ix1 + 8, 70):
        d.ellipse(sbox((bx - 7, iy0 - 10, bx + 7, iy0 + 6)), fill=(48, 48, 44, 255), outline=(110, 108, 98, 255), width=sc(1))
    # fork legs diverging upward
    for off, lean in ((-50, -28), (50, 28)):
        cx = (ix0 + ix1) // 2 + off
        d.line(spoly([(cx, iy0 - 22), (cx + lean, -20)]), fill=(88, 90, 84, 255), width=sc(7))
        d.line(spoly([(cx + lean, -20), (cx + lean + 8, -55)]), fill=(88, 90, 84, 255), width=sc(5))
    # grip blob bottom-right corner only
    d.rounded_rectangle(sbox((cw - 90, ch - 110, cw - 4, ch - 8)), 14, fill=(32, 28, 24, 255))
    for y in range(ch - 100, ch - 16, 9):
        d.line(spoly([(cw - 82, y), (cw - 12, y)]), fill=(18, 16, 14, 255), width=sc(2))
    # thin bottom tie bar
    d.rectangle(sbox((ix0 - 10, PAD_TOP + COMPASS_H + COMPASS_GAP + MAP_H + 6, ix1 + 10, ch - 18)), fill=(58, 60, 54, 255))
    tag(d, "FORK NAV", ix0, iy0 - 38, (150, 148, 130, 255))


# ── 4. SCOPE TUBE — cylindrical body, knurled compass ring ────────────────
def skin_scope_tube(d, base, seed, rw, rh):
    cw, ch = rw // RENDER_SCALE, rh // RENDER_SCALE
    ix0, iy0, ix1, iy1 = inner_map_box()
    cx0, cy0, cx1, cy1 = inner_compass_box()
    body = sbox((14, 28, cw - 14, ch - 6))
    # tube shading: side shadows
    d.rectangle(body, fill=(48, 50, 46, 255))
    d.rectangle(sbox((body[0], body[1], body[0] + 28, body[3])), fill=(28, 30, 26, 200))
    d.rectangle(sbox((body[2] - 28, body[1], body[2], body[3])), fill=(28, 30, 26, 200))
    d.ellipse(sbox((body[0], body[1] - 8, body[2], body[1] + 24)), fill=(62, 64, 58, 255), outline=(36, 38, 32, 255))
    d.ellipse(sbox((body[0], body[3] - 24, body[2], body[3] + 8)), fill=(42, 44, 38, 255), outline=(28, 28, 24, 255))
    # sunshade flip-up
    shade = spoly([(ix0 - 20, iy0 - 30), (ix1 + 20, iy0 - 30), (ix1 + 8, iy0 - 6), (ix0 - 8, iy0 - 6)])
    d.polygon(shade, fill=(36, 38, 34, 255), outline=(80, 78, 72, 255))
    # knurled compass ring
    ccx = (cx0 + cx1) // 2
    d.ellipse(sbox((ccx - 90, cy0 - 18, ccx + 90, cy1 + 18)), outline=(120, 118, 108, 255), width=sc(3))
    for a in range(0, 360, 12):
        rad = math.radians(a)
        x1 = ccx + int(86 * math.cos(rad))
        y1 = cy0 + COMPASS_H // 2 + int(14 * math.sin(rad))
        x2 = ccx + int(78 * math.cos(rad))
        y2 = cy0 + COMPASS_H // 2 + int(12 * math.sin(rad))
        d.line(spoly([(x1, y1), (x2, y2)]), fill=(90, 88, 80, 255), width=sc(2))
    # turret knob right
    tx, ty = ix1 + 24, iy0 + 40
    d.ellipse(sbox((tx - 16, ty - 16, tx + 16, ty + 16)), fill=(54, 56, 50, 255), outline=(100, 98, 90, 255), width=sc(2))
    d.line(spoly([(tx, ty), (tx + 10, ty - 8)]), fill=(190, 52, 38, 255), width=sc(2))
    tag(d, "4×32 MAP", 24, 34, (160, 164, 148, 255))


# ── 5. OPEN FIELD BOOK — spine left, curled page, no outer rectangle ────────
def skin_field_book(d, base, seed, rw, rh):
    cw, ch = rw // RENDER_SCALE, rh // RENDER_SCALE
    spine = sbox((0, 10, 46, ch - 6))
    d.rectangle(spine, fill=(58, 38, 24, 255))
    for y in range(14, ch - 10, 10):
        d.line((spine[2] - sc(6), sc(y), spine[2], sc(y + 5)), fill=(36, 24, 14, 255), width=sc(1))
    page = sbox((42, 12, cw - 6, ch - 8))
    d.rectangle(page, fill=(194, 182, 148, 255))
    # curl top-right
    d.pieslice(sbox((page[2] - 90, page[1] - 10, page[2] + 20, page[1] + 110)), 250, 30, fill=(148, 136, 108, 180))
    d.arc(sbox((page[2] - 70, page[1], page[2], page[1] + 80)), 270, 0, fill=(110, 100, 78, 200), width=sc(2))
    # ruled lines on margins only
    ix0, iy0, ix1, iy1 = inner_map_box()
    for y in range(iy0 + 30, iy1 - 20, 28):
        if y < iy0 + 8 or y > iy1 - 8:
            continue
        d.line(spoly([(ix0 + 12, y), (ix1 - 12, y)]), fill=(168, 156, 124, 80), width=sc(1))
    # coffee ring
    d.ellipse(sbox((ix1 - 120, iy1 - 100, ix1 - 40, iy1 - 40)), outline=(120, 90, 60, 90), width=sc(3))
    # compass header rule
    d.line(spoly([(ix0, iy0 - 2), (ix1, iy0 - 2)]), fill=(88, 72, 52, 255), width=sc(2))
    tag(d, "FIELD ATLAS", 52, 18, (72, 48, 32, 255), (210, 198, 168, 220))
    tag(d, "COMPASS", ix0 + 8, inner_compass_box()[1] - 16, (88, 68, 44, 255), (210, 198, 168, 200))
    tag(d, "MAP", ix0 + 8, iy0 + 6, (88, 68, 44, 255), (210, 198, 168, 200))


# ── 6. SIDE MIRROR ARM — mostly transparent; arm + mirror pod top-left ───────
def skin_mirror_arm(d, base, seed, rw, rh):
    cw, ch = rw // RENDER_SCALE, rh // RENDER_SCALE
    ix0, iy0, ix1, iy1 = inner_map_box()
    # arm from off-screen left
    d.rounded_rectangle(sbox((-80, ch // 2 - 16, 36, ch // 2 + 16)), 8, fill=(52, 54, 50, 255))
    d.ellipse(sbox((20, ch // 2 - 22, 56, ch // 2 + 22)), fill=(44, 46, 42, 255), outline=(28, 28, 24, 255), width=sc(2))
    # mirror pod overlapping top-left of map zone
    pod = sbox((ix0 - 30, iy0 - 50, ix0 + 130, iy0 + 70))
    d.ellipse(pod, fill=(62, 64, 60, 255), outline=(34, 34, 30, 255), width=sc(3))
    d.ellipse(sbox((pod[0] + 20, pod[1] + 18, pod[2] - 20, pod[3] - 18)), fill=(140, 142, 138, 180), outline=(90, 92, 88, 255), width=sc(2))
    # small housing wedge bottom
    wedge = spoly([(ix1 - 60, iy1 + 8), (cw - 4, iy1 + 20), (cw - 4, ch - 4), (ix1 - 100, ch - 4)])
    d.polygon(wedge, fill=(48, 50, 46, 255), outline=(28, 28, 24, 255))
    # compass strip bracket only (thin L)
    d.rectangle(sbox((ix0 - 6, iy0 - 10, ix1 + 6, iy0 - 4)), fill=(70, 72, 68, 255))
    d.rectangle(sbox((ix0 - 6, iy0 - 10, ix0, iy0 + COMPASS_H + 4)), fill=(70, 72, 68, 255))
    tag(d, "MIRROR GPS", ix0 + 4, iy0 - 42, (180, 182, 170, 255))


# ── 7. FOLDED PAPER MAP — creases, torn border, zero hardware ──────────────
def skin_folded_paper(d, base, seed, rw, rh):
    cw, ch = rw // RENDER_SCALE, rh // RENDER_SCALE
    rng = random.Random(seed)
    # torn outer border polygon
    outer = []
    for x in range(0, cw, 18):
        outer.append((x, 6 + rng.randint(-4, 5)))
    for y in range(6, ch, 18):
        outer.append((cw - 4 + rng.randint(-5, 4), y))
    for x in range(cw, 0, -18):
        outer.append((x, ch - 4 + rng.randint(-4, 5)))
    for y in range(ch, 0, -18):
        outer.append((4 + rng.randint(-4, 5), y))
    d.polygon(spoly(outer), fill=(210, 198, 162, 255), outline=(148, 136, 108, 255))
    # fold creases diagonals
    d.line(spoly([(cw // 3, 0), (cw // 3 + 40, ch)]), fill=(168, 156, 124, 120), width=sc(2))
    d.line(spoly([(2 * cw // 3, 0), (2 * cw // 3 - 30, ch)]), fill=(168, 156, 124, 120), width=sc(2))
    d.line(spoly([(0, ch // 2), (cw, ch // 2 - 20)]), fill=(158, 146, 116, 100), width=sc(3))
    # stamp
    f = load_font(14, True)
    d.text((sc(36), sc(24)), "TOPO", font=f, fill=(140, 40, 36, 140))
    d.text((sc(38), sc(40)), "SHEET", font=f, fill=(140, 40, 36, 140))
    ix0, iy0, _, _ = inner_compass_box()
    tag(d, "COMPASS", ix0 + 6, iy0 - 14, (100, 80, 56, 255), (210, 198, 168, 180))
    tag(d, "MAP", PAD_SIDE + 6, PAD_TOP + COMPASS_H + COMPASS_GAP + 6, (100, 80, 56, 255), (210, 198, 168, 180))


# ── 8. GAS MASK FACE — face-shaped surround, filters, nose ridge ────────────
def skin_gas_mask_face(d, base, seed, rw, rh):
    cw, ch = rw // RENDER_SCALE, rh // RENDER_SCALE
    ix0, iy0, ix1, iy1 = PAD_SIDE, PAD_TOP, PAD_SIDE + INNER_W, PAD_TOP + COMPASS_H + COMPASS_GAP + MAP_H
    cx, cy = cw // 2, ch // 2 + 20
    # face shield outline
    face = []
    for a in range(200, 340, 4):
        rad = math.radians(a)
        r = 340 if 240 < a < 300 else 300
        face.append((cx + int(r * math.cos(rad)), cy + int(r * 0.85 * math.sin(rad))))
    d.polygon(spoly(face), fill=(42, 46, 38, 255), outline=(24, 26, 20, 255))
    # nose ridge top center
    nx = (ix0 + ix1) // 2
    d.polygon(spoly([(nx, iy0 - 36), (nx - 18, iy0 - 4), (nx + 18, iy0 - 4)]), fill=(52, 56, 48, 255))
    # lens rings flanking compass (decorative, not holes)
    for lx in (ix0 + 100, ix1 - 100):
        ly = iy0 + COMPASS_H // 2
        d.ellipse(sbox((lx - 48, ly - 34, lx + 48, ly + 34)), fill=(32, 36, 28, 255), outline=(88, 90, 80, 255), width=sc(2))
        d.ellipse(sbox((lx - 26, ly - 20, lx + 26, ly + 20)), fill=(18, 20, 16, 255), outline=(60, 62, 54, 255), width=sc(1))
    # filter cans bottom corners, extending below
    for fx in (ix0 - 20, ix1 - 40):
        d.rounded_rectangle(sbox((fx, iy1 + 10, fx + 72, ch + 8)), 12, fill=(48, 52, 42, 255), outline=(28, 30, 24, 255), width=sc(2))
        for a in range(0, 360, 30):
            rad = math.radians(a)
            px = fx + 36 + int(22 * math.cos(rad))
            py = iy1 + 50 + int(36 * math.sin(rad))
            d.ellipse((sc(px) - sc(2), sc(py) - sc(2), sc(px) + sc(2), sc(py) + sc(2)), fill=(68, 72, 58, 255))
    # crossing strap
    d.line(spoly([(-10, 40), (cw + 10, ch - 30)]), fill=(36, 38, 30, 160), width=sc(10))
    tag(d, "FILTER MAP", ix0 + 12, iy0 - 52, (170, 180, 150, 255))


# ── 9. TOOL BELT L — only left + bottom straps, top-right open sky ──────────
def skin_tool_belt(d, base, seed, rw, rh):
    cw, ch = rw // RENDER_SCALE, rh // RENDER_SCALE
    ix0, iy0, ix1, iy1 = PAD_SIDE, PAD_TOP, PAD_SIDE + INNER_W, PAD_TOP + COMPASS_H + COMPASS_GAP + MAP_H
    belt_w = 54
    # L-shaped leather
    d.rectangle(sbox((0, 0, belt_w, ch)), fill=(48, 36, 26, 255), outline=(28, 20, 14, 255), width=sc(2))
    d.rectangle(sbox((0, ch - belt_w, ix1 + 20, ch)), fill=(48, 36, 26, 255), outline=(28, 20, 14, 255), width=sc(2))
    # pouches bulging left
    for py in (80, 200, 380, 520):
        d.rounded_rectangle(sbox((4, py, belt_w + 18, py + 70)), 8, fill=(56, 42, 30, 255), outline=(32, 24, 16, 255), width=sc(1))
        d.rectangle(sbox((belt_w + 4, py + 20, belt_w + 16, py + 50)), fill=(38, 28, 18, 255))
    # buckle tongue bottom
    d.polygon(spoly([(ix0 + 40, ch - belt_w - 4), (ix0 + 120, ch - belt_w - 4), (ix0 + 110, ch - belt_w + 20), (ix0 + 50, ch - belt_w + 20)]), fill=(88, 82, 68, 255))
    # cross straps over frame margins (not holes)
    d.line(spoly([(belt_w, iy0 - 8), (ix1, iy0 - 8)]), fill=(36, 30, 22, 200), width=sc(6))
    d.line(spoly([(belt_w, iy1 + 8), (ix1, iy1 + 8)]), fill=(36, 30, 22, 200), width=sc(6))
    tag(d, "BELT NAV", 8, 12, (190, 170, 130, 255))
    tag(d, "COMPASS", belt_w + 8, iy0 - 18, (190, 170, 130, 255))
    tag(d, "MAP", belt_w + 8, iy0 + COMPASS_H + COMPASS_GAP + 4, (190, 170, 130, 255))


# ── 10. SHATTERED TABLET — jagged broken bezels, circuit peek, no full box ─
def skin_shattered_tablet(d, base, seed, rw, rh):
    cw, ch = rw // RENDER_SCALE, rh // RENDER_SCALE
    ix0, iy0, ix1, iy1 = PAD_SIDE, PAD_TOP, PAD_SIDE + INNER_W, PAD_TOP + COMPASS_H + COMPASS_GAP + MAP_H
    rng = random.Random(seed)
    # intact corner top-right (rounded)
    d.rounded_rectangle(sbox((ix1 - 80, iy0 - 30, cw - 4, iy0 + 40)), 12, fill=(58, 60, 56, 255), outline=(32, 32, 28, 255), width=sc(2))
    # jagged left edge shards
    shards_l = [(4, iy0 - 20)]
    for y in range(iy0 - 20, iy1 + 40, 25):
        shards_l.append((rng.randint(8, 36), y))
    shards_l += [(20, iy1 + 40), (4, ch - 8), (4, iy0 - 20)]
    d.polygon(spoly(shards_l), fill=(52, 54, 50, 255), outline=(30, 30, 26, 255))
    # jagged bottom
    shards_b = [(ix0 - 10, iy1 + 10)]
    for x in range(ix0 - 10, ix1 + 30, 30):
        shards_b.append((x, iy1 + rng.randint(10, 36)))
    shards_b += [(cw - 6, ch - 6), (ix0 - 30, ch - 4), (ix0 - 10, iy1 + 10)]
    d.polygon(spoly(shards_b), fill=(46, 48, 44, 255), outline=(28, 28, 24, 255))
    # crack lines
    d.line(spoly([(ix1 - 60, iy0 - 28), (ix0 + 40, iy1 + 20)]), fill=(180, 175, 160, 100), width=sc(1))
    d.line(spoly([(cw - 20, iy0), (ix0 + 200, ch - 20)]), fill=(180, 175, 160, 80), width=sc(1))
    # PCB peek bottom-left gap
    pcb = sbox((12, iy1 + 20, 90, ch - 10))
    d.rectangle(pcb, fill=(28, 68, 48, 255))
    for x in range(pcb[0] + sc(6), pcb[2] - sc(6), sc(10)):
        d.line((x, pcb[1] + sc(4), x, pcb[3] - sc(4)), fill=(48, 120, 72, 255), width=sc(1))
    # compass top shard only
    d.polygon(spoly([(ix0 - 8, iy0 - 12), (ix1 + 12, iy0 - 16), (ix1, iy0 + 4), (ix0, iy0 + 4)]), fill=(62, 64, 60, 255))
    tag(d, "BROKEN TAB", ix0 + 8, iy0 - 38, (200, 198, 180, 255))


SKINS = [
    ("diverse-01-plywood-cutout", "Plywood Cutout", "Sawn board, tape, splinters — no device", "strip", skin_plywood_cutout),
    ("diverse-02-walkie-talkie", "Walkie-Talkie", "Left rail, antenna, battery hump", "square", skin_walkie_talkie),
    ("diverse-03-fork-clamp", "Fork Triple Clamp", "Fork legs up, grip corner only", "triangle", skin_fork_clamp),
    ("diverse-04-scope-tube", "Rifle Scope Tube", "Cylinder, sunshade, knurled ring", "ring", skin_scope_tube),
    ("diverse-05-field-book", "Open Field Book", "Spine + curled page, coffee stain", "strip", skin_field_book),
    ("diverse-06-mirror-arm", "Side Mirror Arm", "Mostly open — arm + mirror pod", "cross", skin_mirror_arm),
    ("diverse-07-folded-paper", "Folded Topo Sheet", "Creases, torn edges, no hardware", "strip", skin_folded_paper),
    ("diverse-08-gas-mask-face", "Gas Mask Face", "Face shield, filters, nose ridge", "ring", skin_gas_mask_face),
    ("diverse-09-tool-belt", "Tool Belt L-Frame", "Left/bottom only, bulging pouches", "square", skin_tool_belt),
    ("diverse-10-shattered-tablet", "Shattered Tablet", "Jagged glass, PCB peek, cracks", "cross", skin_shattered_tablet),
]


def contact_sheet(images: list[tuple[str, Image.Image]], path: Path):
    cols, rows = 5, 2
    thumb_w, thumb_h = 360, 230
    sheet = Image.new("RGBA", (cols * thumb_w + 20, rows * thumb_h + 60), (24, 22, 18, 255))
    d = ImageDraw.Draw(sheet)
    f = load_font(8, True)
    for i, (name, img) in enumerate(images):
        c, r = i % cols, i // cols
        t = img.copy()
        t.thumbnail((thumb_w - 10, thumb_h - 30), Image.Resampling.LANCZOS)
        x = 10 + c * thumb_w + (thumb_w - t.width) // 2
        y = 36 + r * thumb_h + (thumb_h - 30 - t.height) // 2
        sheet.paste(t, (x, y), t)
        d.text((10 + c * thumb_w + 4, 8 + r * thumb_h), name, font=f, fill=(200, 190, 160, 255))
    sheet.save(path, "PNG", optimize=True)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    saved: list[Path] = []
    previews: list[tuple[str, Image.Image]] = []
    for i, (slug, title, desc, marker, painter) in enumerate(SKINS):
        img = build(painter, marker, seed=900 + i * 53)
        p = OUT / f"{slug}.png"
        img.save(p, "PNG", optimize=True)
        p4 = OUT / f"{slug}-4k.png"
        img.resize((img.width * 2, img.height * 2), Image.Resampling.LANCZOS).save(p4, "PNG", optimize=True)
        saved += [p, p4]
        previews.append((f"{i + 1:02d}", img))
        print(f"{slug}: {title} — {desc}")

    cs = OUT / "00-diverse-contact-sheet.png"
    contact_sheet(previews, cs)
    saved.append(cs)

    zp = OUT / "minimap-frames-diverse-10.zip"
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in saved:
            zf.write(p, p.name)
    print(f"Saved {zp} ({len(saved)} files)")


if __name__ == "__main__":
    main()
