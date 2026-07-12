#!/usr/bin/env python3
"""10 radically different DayZ post-apocalyptic minimap frame skins.

Inner compass/map window sizes and positions are FIXED.
Only the outer housing design changes between skins.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageFont

OUT = Path("/workspace/minimap-frames")
RENDER_SCALE = 4

INNER_W = 1120
COMPASS_H = 58
COMPASS_GAP = 10
MAP_H = 580
INNER_H = COMPASS_H + COMPASS_GAP + MAP_H
PAD_TOP = 88
PAD_SIDE = 40
PAD_BOTTOM = 68


@dataclass
class Skin:
    slug: str
    title: str
    desc: str
    marker: str
    paint: Callable[[Image.Image, int], None]


def sc(v: float) -> int:
    return int(round(v * RENDER_SCALE))


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    size = max(10, sc(size))
    for p in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ):
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def canvas_size() -> tuple[int, int]:
    return INNER_W + PAD_SIDE * 2, INNER_H + PAD_TOP + PAD_BOTTOM


def inner_box() -> tuple[int, int, int, int]:
    return PAD_SIDE, PAD_TOP, PAD_SIDE + INNER_W, PAD_TOP + INNER_H


def inner_compass_box() -> tuple[int, int, int, int]:
    ix0, iy0, ix1, _ = inner_box()
    return ix0 + 6, iy0 + 4, ix1 - 6, iy0 + COMPASS_H - 4


def inner_map_box() -> tuple[int, int, int, int]:
    ix0, iy0, ix1, iy1 = inner_box()
    return ix0, iy0 + COMPASS_H + COMPASS_GAP, ix1, iy1


def compass_row_box() -> tuple[int, int, int, int]:
    ix0, iy0, ix1, _ = inner_box()
    return ix0, iy0, ix1, iy0 + COMPASS_H


METRO_OUTER_R = 24
METRO_INNER_R = 20


def draw_metro_shell(
    draw: ImageDraw.ImageDraw,
    shell: tuple[int, int, int, int],
    outer: tuple[int, int, int, int],
    inner: tuple[int, int, int, int],
    outline: tuple[int, int, int, int] | None = None,
    w: int = 2,
) -> None:
    """Double rounded shell like Metro pocket compass."""
    ol = outline or (outer[0] // 2, outer[1] // 2, outer[2] // 2, 255)
    rr(draw, shell, METRO_OUTER_R, outer, ol, w)
    rr(draw, (shell[0] + sc(6), shell[1] + sc(6), shell[2] - sc(6), shell[3] - sc(6)), METRO_INNER_R, inner)


def draw_dark_compass_backing(draw: ImageDraw.ImageDraw, color: tuple[int, int, int, int] = (1, 1, 1, 255)) -> None:
    """Opaque strip behind compass HUD — near-black."""
    ix0, iy0, ix1, iy1 = compass_row_box()
    rr(draw, sbox((ix0 - 6, iy0 - 3, ix1 + 6, iy1 + 2)), 10, color)


def draw_screen_cutouts_metro(draw: ImageDraw.ImageDraw, seed: int) -> None:
    ix0, iy0, ix1, iy1 = inner_box()
    recess = sbox((ix0 - 8, iy0 - 8, ix1 + 8, iy1 + 8))
    rr(draw, recess, 11, None, (12, 10, 8, 255), 1)
    gap0, gap1 = iy0 + COMPASS_H, iy0 + COMPASS_H + COMPASS_GAP
    draw.rectangle(sbox((ix0 - 6, gap0, ix1 + 6, gap1)), fill=(8, 7, 5, 255))


def compass_center() -> tuple[int, int]:
    c = inner_compass_box()
    return (c[0] + c[2]) // 2, (c[1] + c[3]) // 2


def spoly(points: list[tuple[float, float]]) -> list[tuple[int, int]]:
    return [(sc(x), sc(y)) for x, y in points]


def sbox(b: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    return sc(b[0]), sc(b[1]), sc(b[2]), sc(b[3])


def rr(draw, b, r, fill=None, outline=None, w=1):
    draw.rounded_rectangle(b, radius=sc(r), fill=fill, outline=outline, width=max(1, sc(w)))


def wood_tex(draw, b, seed, base=(92, 68, 44)):
    rng = random.Random(seed)
    x0, y0, x1, y1 = b
    for y in range(y0, y1, sc(3)):
        c = base[0] + rng.randint(-10, 10)
        draw.line((x0, y, x1, y), fill=(c, c - 14, c - 26, 255), width=sc(2))


def metal_tex(draw, b, seed, base=(78, 74, 68)):
    rng = random.Random(seed)
    x0, y0, x1, y1 = b
    for _ in range(120):
        x, y = rng.randint(x0, x1), rng.randint(y0, y1)
        g = base[0] + rng.randint(-18, 18)
        draw.point((x, y), fill=(g, g - 4, g - 8, 220))


def rust_splotches(draw, b, seed, n=20):
    rng = random.Random(seed)
    x0, y0, x1, y1 = b
    for _ in range(n):
        x, y = rng.randint(x0, x1), rng.randint(y0, y1)
        r = rng.randint(sc(6), sc(28))
        draw.ellipse((x - r, y - r, x + r, y - r // 2), fill=(rng.randint(70, 110), rng.randint(35, 55), rng.randint(20, 35), rng.randint(50, 120)))


def fabric_tex(draw, b, seed, base=(58, 62, 48)):
    rng = random.Random(seed)
    x0, y0, x1, y1 = b
    for y in range(y0, y1, sc(4)):
        for x in range(x0, x1, sc(6)):
            n = base[0] + rng.randint(-8, 8)
            draw.point((x, y), fill=(n, n - 3, n - 8, 255))


def finish(img: Image.Image, seed: int) -> Image.Image:
    rng = random.Random(seed)
    w, h = img.size
    grain = Image.effect_noise((w, h), 9).convert("L").filter(ImageFilter.GaussianBlur(0.5))
    rgb = ImageChops.multiply(img.convert("RGB"), Image.merge("RGB", [grain, grain, grain]))
    img = Image.merge("RGBA", (*rgb.split(), img.split()[3]))
    grime = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    g = ImageDraw.Draw(grime)
    for _ in range(10):
        x, y = rng.randint(0, w), rng.randint(0, h)
        r = rng.randint(sc(10), sc(50))
        g.ellipse((x - r, y - r, x + r, y - r // 2), fill=(20, 18, 14, rng.randint(10, 28)))
    img = Image.alpha_composite(img, grime.filter(ImageFilter.GaussianBlur(sc(6))))
    rgb = ImageEnhance.Color(img.convert("RGB")).enhance(0.68)
    rgb = ImageEnhance.Contrast(rgb).enhance(1.06)
    return Image.merge("RGBA", (*rgb.split(), img.split()[3]))


def draw_marker(draw: ImageDraw.ImageDraw, kind: str, color=(196, 48, 36, 255)) -> None:
    cx, cy = compass_center()
    cx, cy = sc(cx), sc(cy)
    if kind == "triangle":
        draw.polygon([(cx, cy - sc(9)), (cx - sc(6), cy + sc(5)), (cx + sc(6), cy + sc(5))], fill=color)
    elif kind == "strip":
        _, y0, _, y1 = sbox(inner_compass_box())
        draw.rectangle((cx - sc(2), y0 + sc(1), cx + sc(2), y1 - sc(1)), fill=color)
    elif kind == "square":
        s = sc(6)
        draw.rectangle((cx - s, cy - s, cx + s, cy + s), outline=color, width=max(1, sc(2)))
    elif kind == "cross":
        r = sc(9)
        draw.line((cx - r, cy, cx + r, cy), fill=color, width=max(1, sc(2)))
        draw.line((cx, cy - r, cx, cy + r), fill=color, width=max(1, sc(2)))
    elif kind == "diamond":
        s = sc(7)
        draw.polygon([(cx, cy - s), (cx + s, cy), (cx, cy + s), (cx - s, cy)], outline=color, width=max(1, sc(2)))
    elif kind == "notch":
        draw.polygon([(cx, cy - sc(10)), (cx - sc(4), cy - sc(2)), (cx + sc(4), cy - sc(2))], fill=color)


# ---------------------------------------------------------------------------
# 10 UNIQUE HOUSING DESIGNS
# ---------------------------------------------------------------------------

def paint_crt_monitor(base: Image.Image, seed: int) -> None:
    """1. Salvaged CRT monitor — thick chin, vents, cracked bezel."""
    d = ImageDraw.Draw(base)
    cw, ch = base.size[0] // RENDER_SCALE, base.size[1] // RENDER_SCALE
    body = sbox((8, 6, cw - 8, ch - 6))
    rr(d, body, 8, (42, 44, 40, 255), (20, 20, 18, 255), 3)
    # massive bottom chin like old display
    chin = (body[0], body[3] - sc(56), body[2], body[3])
    d.rectangle(chin, fill=(34, 36, 32, 255))
    for x in range(chin[0] + sc(20), chin[2] - sc(20), sc(18)):
        d.rectangle((x, chin[1] + sc(12), x + sc(10), chin[1] + sc(22)), fill=(12, 12, 10, 255))
    # vent slots left side
    for y in range(body[1] + sc(40), body[3] - sc(70), sc(10)):
        d.rectangle((body[0] + sc(8), y, body[0] + sc(28), y + sc(4)), fill=(18, 18, 16, 255))
    # crack lines corner
    d.line((body[2] - sc(40), body[1] + sc(20), body[2] - sc(8), body[1] + sc(50)), fill=(180, 175, 160, 90), width=sc(1))
    d.text((body[0] + sc(18), body[1] + sc(10)), "SALVAGED DISPLAY", font=load_font(9, True), fill=(160, 156, 140, 255))
    metal_tex(d, (body[0], body[1], body[2], body[1] + sc(30)), seed)


def paint_wood_clipboard(base: Image.Image, seed: int) -> None:
    """2. Wooden clipboard with metal spring clip."""
    d = ImageDraw.Draw(base)
    cw, ch = base.size[0] // RENDER_SCALE, base.size[1] // RENDER_SCALE
    shell = sbox((10, 8, cw - 10, ch - 8))
    wood_tex(d, shell, seed, (108, 78, 48))
    rr(d, shell, 6, outline=(58, 40, 24, 255), w=2)
    # metal clip across top
    ix0, iy0, ix1, _ = inner_box()
    clip = sbox((ix0 - 4, iy0 - 28, ix1 + 4, iy0 - 2))
    d.rectangle(clip, fill=(120, 118, 110, 255), outline=(70, 68, 62, 255))
    d.rectangle((clip[0] + sc(30), clip[1] + sc(4), clip[2] - sc(30), clip[3] - sc(4)), fill=(90, 88, 82, 255))
    # nail heads corners
    for px, py in ((shell[0] + sc(14), shell[1] + sc(14)), (shell[2] - sc(14), shell[1] + sc(14)),
                   (shell[0] + sc(14), shell[3] - sc(14)), (shell[2] - sc(14), shell[3] - sc(14))):
        d.ellipse((px - sc(4), py - sc(4), px + sc(4), py + sc(4)), fill=(68, 64, 56, 255))


def paint_wrist_strap(base: Image.Image, seed: int) -> None:
    """3. Wrist-mounted device — curved side straps."""
    d = ImageDraw.Draw(base)
    cw, ch = base.size[0] // RENDER_SCALE, base.size[1] // RENDER_SCALE
    core = sbox((28, 10, cw - 28, ch - 10))
    rr(d, core, 22, (48, 50, 42, 255), (22, 24, 18, 255), 2)
    # protruding strap lugs left/right (unique silhouette)
    for side in (0, cw - 22):
        lug = sbox((side, ch // 2 - 90, side + 22, ch // 2 + 90))
        rr(d, lug, 8, (32, 34, 28, 255))
        for y in range(lug[1] + sc(10), lug[3] - sc(10), sc(22)):
            d.ellipse((lug[0] + sc(6), y, lug[0] + sc(16), y + sc(10)), fill=(18, 18, 14, 255))
    # buckle tongue top
    d.polygon(spoly([(cw // 2 - 30, 4), (cw // 2 + 30, 4), (cw // 2 + 20, 18), (cw // 2 - 20, 18)]), fill=(62, 58, 48, 255))
    d.text((core[0] + sc(12), core[1] + sc(8)), "WRIST NAV", font=load_font(8, True), fill=(170, 164, 140, 255))


def paint_camo_fabric_wrap(base: Image.Image, seed: int) -> None:
    """4. Camo fabric wrap — torn irregular patches."""
    d = ImageDraw.Draw(base)
    shell = sbox((6, 6, base.size[0] // RENDER_SCALE - 6, base.size[1] // RENDER_SCALE - 6))
    fabric_tex(d, shell, seed, (52, 58, 40))
    rng = random.Random(seed)
    patches = [(68, 62, 44), (44, 52, 36), (78, 72, 50), (38, 46, 32)]
    for _ in range(16):
        px = rng.randint(shell[0], shell[2] - sc(60))
        py = rng.randint(shell[1], shell[3] - sc(40))
        c = rng.choice(patches)
        pts = [(px + rng.randint(-sc(8), sc(8)), py + rng.randint(-sc(8), sc(8))) for _ in range(5)]
        d.polygon(pts, fill=(*c, rng.randint(140, 210)))
    # torn edge top
    pts = [shell[0], shell[1]] + [(shell[0] + i, shell[1] + rng.randint(-sc(4), sc(6))) for i in range(0, shell[2] - shell[0], sc(20))] + [shell[2], shell[1]]
    d.line(pts, fill=(28, 30, 22, 255), width=sc(3))


def paint_dash_wedge(base: Image.Image, seed: int) -> None:
    """5. Stolen car dashboard wedge — trapezoid, angular."""
    d = ImageDraw.Draw(base)
    cw, ch = base.size[0] // RENDER_SCALE, base.size[1] // RENDER_SCALE
    pts = spoly([(18, 14), (cw - 18, 8), (cw - 8, ch - 8), (8, ch - 6)])
    d.polygon(pts, fill=(56, 52, 48, 255), outline=(28, 26, 22, 255))
    # cigarette burn
    bx, by = pts[0][0] + sc(80), pts[0][1] + sc(40)
    d.ellipse((bx - sc(8), by - sc(8), bx + sc(8), by + sc(8)), fill=(22, 20, 16, 255), outline=(40, 36, 30, 255))
    # screw holes
    for px, py in ((pts[0][0] + sc(20), pts[0][1] + sc(20)), (pts[2][0] - sc(20), pts[2][1] - sc(20))):
        d.ellipse((px - sc(5), py - sc(5), px + sc(5), py + sc(5)), fill=(24, 22, 18, 255))
    d.text((pts[0][0] + sc(24), pts[0][1] + sc(10)), "DASH MOUNT", font=load_font(8, True), fill=(150, 146, 130, 255))


def paint_ammo_tin(base: Image.Image, seed: int) -> None:
    """6. Military ammo tin with hinge bar and rough cut."""
    d = ImageDraw.Draw(base)
    shell = sbox((12, 20, base.size[0] // RENDER_SCALE - 12, base.size[1] // RENDER_SCALE - 8))
    d.rectangle(shell, fill=(58, 62, 48, 255), outline=(30, 32, 24, 255), width=sc(3))
    # hinge across top
    hx0, hy = shell[0] + sc(24), shell[1] - sc(8)
    d.rectangle((hx0, hy, shell[2] - sc(24), hy + sc(10)), fill=(88, 84, 70, 255))
    for x in range(hx0 + sc(10), shell[2] - sc(34), sc(28)):
        d.ellipse((x, hy + sc(1), x + sc(8), hy + sc(9)), fill=(48, 46, 38, 255))
    # dent
    d.arc((shell[2] - sc(80), shell[1] + sc(30), shell[2] - sc(20), shell[1] + sc(90)), 270, 40, fill=(40, 42, 34, 255), width=sc(4))
    rust_splotches(d, shell, seed, 14)
    d.text((shell[0] + sc(14), shell[1] + sc(6)), "7.62x39 / MAP", font=load_font(8, True), fill=(170, 166, 140, 255))


def paint_wood_crate(base: Image.Image, seed: int) -> None:
    """7. Wooden crate planks — horizontal boards, nails."""
    d = ImageDraw.Draw(base)
    shell = sbox((8, 8, base.size[0] // RENDER_SCALE - 8, base.size[1] // RENDER_SCALE - 8))
    plank_h = (shell[3] - shell[1]) // 5
    rng = random.Random(seed)
    for i in range(5):
        y0 = shell[1] + i * plank_h
        y1 = y0 + plank_h - sc(2)
        c = 82 + rng.randint(-12, 12)
        d.rectangle((shell[0], y0, shell[2], y1), fill=(c, c - 18, c - 30, 255), outline=(48, 34, 22, 255))
        for nx in range(shell[0] + sc(16), shell[2] - sc(8), sc(80)):
            d.ellipse((nx - sc(3), y0 + sc(6), nx + sc(3), y0 + sc(12)), fill=(58, 54, 46, 255))


def paint_tin_lid_open(base: Image.Image, seed: int) -> None:
    """8. Compass tin with lid flipped open behind."""
    d = ImageDraw.Draw(base)
    cw = base.size[0] // RENDER_SCALE
    # open lid sticking up behind
    lid = spoly([(24, 0), (cw - 24, 0), (cw - 14, 36), (14, 36)])
    d.polygon(lid, fill=(62, 70, 48, 255), outline=(34, 38, 26, 255))
    d.text((lid[0][0] + sc(40), lid[0][1] + sc(8)), "ARMY MAP TIN", font=load_font(8, True), fill=(180, 176, 148, 255))
    shell = sbox((16, 32, cw - 16, base.size[1] // RENDER_SCALE - 8))
    rr(d, shell, 4, (54, 60, 42, 255), (28, 32, 22, 255), 2)
    # latch on front
    ix0, iy0, ix1, _ = inner_box()
    latch = sbox((ix1 - 60, iy0 - 18, ix1 + 4, iy0 + 2))
    d.rectangle(latch, fill=(100, 96, 80, 255))


def paint_gauge_plate(base: Image.Image, seed: int) -> None:
    """9. Industrial metal plate with bolted gauge circles in corners."""
    d = ImageDraw.Draw(base)
    shell = sbox((10, 10, base.size[0] // RENDER_SCALE - 10, base.size[1] // RENDER_SCALE - 10))
    d.rectangle(shell, fill=(72, 70, 64, 255), outline=(36, 34, 30, 255), width=sc(2))
    metal_tex(d, shell, seed)
    for px, py in ((shell[0] + sc(28), shell[1] + sc(28)), (shell[2] - sc(28), shell[1] + sc(28)),
                   (shell[0] + sc(28), shell[3] - sc(28)), (shell[2] - sc(28), shell[3] - sc(28))):
        d.ellipse((px - sc(16), py - sc(16), px + sc(16), py + sc(16)), fill=(48, 46, 42, 255), outline=(110, 106, 96, 255), width=sc(2))
        d.ellipse((px - sc(4), py - sc(4), px + sc(4), py + sc(4)), fill=(140, 50, 36, 255))
    # stencil text
    d.text((shell[0] + sc(40), shell[1] + sc(12)), "NAV PLATE", font=load_font(10, True), fill=(130, 126, 112, 255))


def paint_canvas_roll(base: Image.Image, seed: int) -> None:
    """10. Canvas map sleeve — rolled top & bottom fabric."""
    d = ImageDraw.Draw(base)
    cw, ch = base.size[0] // RENDER_SCALE, base.size[1] // RENDER_SCALE
    mid = sbox((14, 30, cw - 14, ch - 24))
    fabric_tex(d, mid, seed, (88, 80, 64))
    # rolled top cylinder
    roll = sbox((10, 8, cw - 10, 38))
    d.ellipse((roll[0], roll[1], roll[2], roll[1] + sc(28)), fill=(96, 88, 72, 255), outline=(52, 46, 36, 255))
    d.rectangle((roll[0], roll[1] + sc(12), roll[2], roll[3]), fill=(88, 80, 64, 255))
    # rolled bottom
    roll2 = sbox((10, ch - 32, cw - 10, ch - 6))
    d.ellipse((roll2[0], roll2[3] - sc(24), roll2[2], roll2[3]), fill=(96, 88, 72, 255))
    d.rectangle((roll2[0], roll2[1], roll2[2], roll2[3] - sc(10)), fill=(88, 80, 64, 255))
    # stitch line
    ix0, _, ix1, _ = inner_box()
    for x in range(sc(ix0), sc(ix1), sc(14)):
        d.point((x, mid[1] + sc(6)), fill=(60, 54, 42, 255))


PAINTERS: list[tuple[str, str, str, str, Callable]] = [
    ("01-crt-monitor", "Salvaged CRT Monitor", "Old display, vents, cracked corner", "triangle", paint_crt_monitor),
    ("02-wood-clipboard", "Wooden Clipboard", "Wood board + metal clip", "strip", paint_wood_clipboard),
    ("03-wrist-strap", "Wrist Strap Mount", "Side lugs + buckle", "square", paint_wrist_strap),
    ("04-camo-wrap", "Camo Fabric Wrap", "Torn camo patches", "cross", paint_camo_fabric_wrap),
    ("05-dash-wedge", "Dashboard Wedge", "Angular trapezoid from vehicle", "notch", paint_dash_wedge),
    ("06-ammo-tin", "Ammo Tin Box", "Hinged metal tin, rust", "strip", paint_ammo_tin),
    ("07-wood-crate", "Wood Crate Planks", "Horizontal nailed boards", "triangle", paint_wood_crate),
    ("08-tin-lid-open", "Map Tin Open Lid", "Flipped lid behind", "diamond", paint_tin_lid_open),
    ("09-gauge-plate", "Industrial Gauge Plate", "Corner gauges + bolts", "cross", paint_gauge_plate),
    ("10-canvas-roll", "Canvas Map Roll", "Rolled fabric top/bottom", "square", paint_canvas_roll),
]


def draw_screen_cutouts(draw: ImageDraw.ImageDraw, seed: int) -> None:
    """Minimal inner bezel — same for all; keeps window positions identical."""
    ix0, iy0, ix1, iy1 = inner_box()
    recess = sbox((ix0 - 8, iy0 - 8, ix1 + 8, iy1 + 8))
    rr(draw, recess, 6, None, (16, 14, 12, 255), 1)
    gap0, gap1 = iy0 + COMPASS_H, iy0 + COMPASS_H + COMPASS_GAP
    draw.rectangle(sbox((ix0 - 6, gap0, ix1 + 6, gap1)), fill=(20, 18, 14, 255))


def draw_zone_tags(draw: ImageDraw.ImageDraw) -> None:
    f = load_font(9, True)
    ix0, iy0, _, _ = inner_box()
    cx0, cy0, _, _ = inner_compass_box()
    split = PAD_TOP + COMPASS_H
    for text, y in (("COMPASS", cy0 - 16), ("MAP", split + 1)):
        bb = f.getbbox(text)
        tw = bb[2] - bb[0]
        tx, ty = sc(ix0 + 8), sc(y)
        draw.rectangle((tx - sc(3), ty - sc(1), tx + tw + sc(6), ty + (bb[3] - bb[1]) + sc(3)), fill=(18, 16, 12, 220))
        draw.text((tx, ty), text, font=f, fill=(170, 158, 120, 255))


def build_frame(
    paint_fn: Callable,
    marker: str,
    seed: int,
    *,
    metro_style: bool = False,
    dark_compass: bool = False,
) -> Image.Image:
    w, h = canvas_size()
    rw, rh = sc(w), sc(h)
    base = Image.new("RGBA", (rw, rh), (0, 0, 0, 0))
    paint_fn(base, seed)
    draw = ImageDraw.Draw(base)
    if dark_compass:
        draw_dark_compass_backing(draw)
    if metro_style:
        draw_screen_cutouts_metro(draw, seed)
    else:
        draw_screen_cutouts(draw, seed)
    draw_zone_tags(draw)

    mask = Image.new("L", (rw, rh), 255)
    md = ImageDraw.Draw(mask)
    hole_r_c, hole_r_m = (8, 10) if metro_style else (3, 4)
    md.rounded_rectangle(sbox(inner_compass_box()), radius=sc(hole_r_c), fill=0)
    md.rounded_rectangle(sbox(inner_map_box()), radius=sc(hole_r_m), fill=0)
    rgba = base.split()
    alpha = Image.composite(rgba[3], Image.new("L", (rw, rh), 0), mask)
    base = Image.merge("RGBA", [*rgba[:3], alpha])
    draw_marker(ImageDraw.Draw(base), marker)
    out = base.resize((w, h), Image.Resampling.LANCZOS)
    return finish(out, seed)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    saved = []
    for i, (slug, title, desc, marker, painter) in enumerate(PAINTERS):
        img = build_frame(painter, marker, seed=30 + i * 23)
        p = OUT / f"{slug}.png"
        img.save(p, "PNG", optimize=True)
        p4 = OUT / f"{slug}-4k.png"
        img.resize((img.width * 2, img.height * 2), Image.Resampling.LANCZOS).save(p4, "PNG", optimize=True)
        saved += [p, p4]
        print(f"{slug}: {title} — {desc}")

    guide = build_frame(PAINTERS[0][4], "cross", 999)
    g = ImageDraw.Draw(guide)
    g.rectangle(inner_compass_box(), outline=(230, 170, 60, 220), width=2)
    g.rectangle(inner_map_box(), outline=(80, 160, 210, 220), width=2)
    gp = OUT / "00-layout-guide.png"
    guide.save(gp)
    saved.append(gp)

    import zipfile
    zp = OUT / "minimap-frames-10skins.zip"
    with zipfile.ZipFile(zp, "w") as zf:
        for p in saved:
            zf.write(p, p.name)
    print(f"Saved {zp}")


if __name__ == "__main__":
    main()
