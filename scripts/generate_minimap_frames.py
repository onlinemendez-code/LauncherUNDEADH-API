#!/usr/bin/env python3
"""Ten DayZ-style minimap frame skins — inner compass/map windows are fixed size."""

from __future__ import annotations

import random
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageFont

OUT = Path("/workspace/minimap-frames")
RENDER_SCALE = 4

# Fixed layout — do not change (user requirement).
INNER_W = 1120
COMPASS_H = 58
COMPASS_GAP = 10
MAP_H = 580
INNER_H = COMPASS_H + COMPASS_GAP + MAP_H
LABEL_BAND_H = 54
PAD_TOP = LABEL_BAND_H + 34
PAD_SIDE = 40
PAD_BOTTOM = 68


@dataclass
class Palette:
    body: tuple[int, int, int, int]
    body_dark: tuple[int, int, int, int]
    body_light: tuple[int, int, int, int]
    bezel: tuple[int, int, int, int]
    accent: tuple[int, int, int, int]
    marker: tuple[int, int, int, int]
    label: tuple[int, int, int, int]
    screw: tuple[int, int, int, int]
    rubber: tuple[int, int, int, int] | None = None


@dataclass
class Skin:
    slug: str
    title: str
    palette: Palette
    marker: str
    drawer: Callable[..., None]


def sc(v: int | float) -> int:
    return int(round(v * RENDER_SCALE))


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    size = max(12, sc(size))
    for p in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
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


def compass_center() -> tuple[int, int]:
    cx0, cy0, cx1, cy1 = inner_compass_box()
    return (cx0 + cx1) // 2, (cy0 + cy1) // 2


def sbox(box: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    return sc(box[0]), sc(box[1]), sc(box[2]), sc(box[3])


def rounded_rect(draw, box, radius: int, fill=None, outline=None, width: int = 1) -> None:
    draw.rounded_rectangle(box, radius=sc(radius), fill=fill, outline=outline, width=max(1, sc(width)))


def vertical_gradient(size: tuple[int, int], top: tuple[int, int, int], bottom: tuple[int, int, int]) -> Image.Image:
    w, h = size
    grad = Image.linear_gradient("L").resize((w, h))
    return Image.composite(Image.new("RGB", (w, h), bottom), Image.new("RGB", (w, h), top), grad)


def apply_dayz_finish(img: Image.Image, seed: int) -> Image.Image:
    rng = random.Random(seed + 101)
    w, h = img.size
    grain = Image.effect_noise((w, h), 10).convert("L").filter(ImageFilter.GaussianBlur(0.55))
    dusty = ImageChops.multiply(img.convert("RGB"), Image.merge("RGB", [grain, grain, grain]))
    img = Image.merge("RGBA", (*dusty.split(), img.split()[3]))
    grime = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    g = ImageDraw.Draw(grime)
    for _ in range(14):
        x, y = rng.randint(0, w), rng.randint(0, h)
        r = rng.randint(sc(16), sc(70))
        s = rng.randint(20, 40)
        g.ellipse((x - r, y - r, x + r, y - r // 2), fill=(s, s - 3, s - 6, rng.randint(14, 30)))
    img = Image.alpha_composite(img, grime.filter(ImageFilter.GaussianBlur(sc(7))))
    rgb = ImageEnhance.Color(img.convert("RGB")).enhance(0.7)
    rgb = ImageEnhance.Contrast(rgb).enhance(1.05)
    return Image.merge("RGBA", (*rgb.split(), img.split()[3]))


# --- Compass center markers (overlay on frame, does NOT shrink inner window) ---

def marker_red_triangle(draw: ImageDraw.ImageDraw, pal: Palette) -> None:
    cx, cy = compass_center()
    cx, cy = sc(cx), sc(cy)
    draw.polygon([(cx, cy - sc(7)), (cx - sc(5), cy + sc(4)), (cx + sc(5), cy + sc(4))], fill=pal.marker)
    draw.line((cx, cy - sc(8), cx, cy + sc(6)), fill=(*pal.marker[:3], 140), width=max(1, sc(1)))


def marker_red_strip(draw: ImageDraw.ImageDraw, pal: Palette) -> None:
    cx, _ = compass_center()
    cx = sc(cx)
    _, cy0, _, cy1 = sbox(inner_compass_box())
    draw.rectangle((cx - sc(2), cy0 + sc(2), cx + sc(2), cy1 - sc(2)), fill=pal.marker)


def marker_square_bracket(draw: ImageDraw.ImageDraw, pal: Palette) -> None:
    cx, cy = compass_center()
    cx, cy = sc(cx), sc(cy)
    s = sc(7)
    for dx, dy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        x0, y0 = cx + dx * s, cy + dy * s
        draw.line((x0, y0, x0 + dx * s, y0), fill=pal.marker, width=max(1, sc(2)))
        draw.line((x0, y0, x0, y0 + dy * s), fill=pal.marker, width=max(1, sc(2)))


def marker_crosshair(draw: ImageDraw.ImageDraw, pal: Palette) -> None:
    cx, cy = compass_center()
    cx, cy = sc(cx), sc(cy)
    r = sc(8)
    draw.line((cx - r, cy, cx + r, cy), fill=pal.marker, width=max(1, sc(1)))
    draw.line((cx, cy - r, cx, cy + r), fill=pal.marker, width=max(1, sc(1)))
    draw.ellipse((cx - sc(3), cy - sc(3), cx + sc(3), cy + sc(3)), outline=pal.marker, width=max(1, sc(1)))


def marker_chevron(draw: ImageDraw.ImageDraw, pal: Palette) -> None:
    cx, cy = compass_center()
    cx, cy = sc(cx), sc(cy)
    draw.polygon([(cx, cy - sc(8)), (cx - sc(6), cy), (cx - sc(2), cy), (cx, cy - sc(4)),
                  (cx + sc(2), cy), (cx + sc(6), cy)], fill=pal.marker)


def marker_dot_ring(draw: ImageDraw.ImageDraw, pal: Palette) -> None:
    cx, cy = compass_center()
    cx, cy = sc(cx), sc(cy)
    draw.ellipse((cx - sc(5), cy - sc(5), cx + sc(5), cy + sc(5)), outline=pal.marker, width=max(1, sc(2)))
    draw.ellipse((cx - sc(2), cy - sc(2), cx + sc(2), cy + sc(2)), fill=pal.marker)


MARKERS: dict[str, Callable] = {
    "triangle": marker_red_triangle,
    "strip": marker_red_strip,
    "bracket": marker_square_bracket,
    "crosshair": marker_crosshair,
    "chevron": marker_chevron,
    "dot_ring": marker_dot_ring,
}


def draw_screw(draw, x: int, y: int, r: int, pal: Palette) -> None:
    x, y, r = sc(x), sc(y), sc(r)
    draw.ellipse((x - r, y - r, x + r, y + r), fill=pal.screw, outline=pal.bezel, width=max(1, sc(1)))


def draw_labels(draw: ImageDraw.ImageDraw, pal: Palette, compass_tag: str = "COMPASS", map_tag: str = "MAP") -> None:
    cx0, cy0, cx1, cy1 = inner_compass_box()
    ix0, _, _, _ = inner_box()
    split_y = PAD_TOP + COMPASS_H
    font = load_font(10, True)
    # COMPASS — left of compass window, in opaque bezel above
    tb = font.getbbox(compass_tag)
    tx = sc(ix0 + 10)
    ty = sc(cy0 - 18)
    draw.rectangle((tx - sc(4), ty - sc(2), tx + (tb[2] - tb[0]) + sc(8), ty + (tb[3] - tb[1]) + sc(4)), fill=(*pal.body_dark[:3], 230))
    draw.text((tx, ty), compass_tag, font=font, fill=pal.accent)
    # MAP — in divider band
    mb = font.getbbox(map_tag)
    mx = sc(ix0 + 10)
    my = sc(split_y + 1)
    draw.rectangle((mx - sc(4), my - sc(1), mx + (mb[2] - mb[0]) + sc(8), my + (mb[3] - mb[1]) + sc(3)), fill=(*pal.body_dark[:3], 230))
    draw.text((mx, my), map_tag, font=font, fill=pal.label)


# --- 10 frame skin drawers (outer design only) ---

def skin_garmin_worn(draw, base, pal, w, h, ix0, iy0, ix1, iy1, shell_u, seed) -> None:
    outer, shell = sbox((12, 10, w - 12, h - 10)), sbox(shell_u)
    rounded_rect(draw, outer, 24, pal.bezel)
    rounded_rect(draw, shell, 20, pal.body_dark, pal.bezel, 2)
    if pal.rubber:
        for bx in (6, w - 28):
            rounded_rect(draw, sbox((bx, h // 2 - 80, bx + 22, h // 2 + 80)), 8, pal.rubber)
    draw_brand(draw, shell_u, iy0 - 14, "GARMIN", "FORETREX 401", pal)
    draw_chin_buttons(draw, ix0, iy1, pal)


def skin_soviet_metal(draw, base, pal, w, h, ix0, iy0, ix1, iy1, shell_u, seed) -> None:
    shell = sbox(shell_u)
    draw.rectangle(shell, fill=pal.body, outline=pal.bezel, width=sc(2))
    for yy in range(shell_u[1] + 50, shell_u[3] - 40, 46):
        draw.rectangle(sbox((shell_u[0] + 10, yy, shell_u[0] + 22, yy + 8)), fill=pal.screw)
        draw.rectangle(sbox((shell_u[2] - 22, yy, shell_u[2] - 10, yy + 8)), fill=pal.screw)
    draw_brand(draw, shell_u, iy0 - 14, "ПРИБОР", "НАВИГАЦИИ", pal)
    draw_chin_buttons(draw, ix0, iy1, pal)


def skin_duct_tape(draw, base, pal, w, h, ix0, iy0, ix1, iy1, shell_u, seed) -> None:
    shell = sbox(shell_u)
    rounded_rect(draw, shell, 14, pal.body_dark)
    rng = random.Random(seed)
    for _ in range(28):
        y = rng.randint(shell[1], shell[3])
        draw.line((shell[0], y, shell[2], y + rng.randint(-3, 3)), fill=(58, 54, 46, rng.randint(40, 90)), width=sc(3))
    for x in (shell[0] + sc(8), shell[2] - sc(28)):
        draw.rectangle((x, shell[1] + sc(20), x + sc(20), shell[3] - sc(20)), fill=(92, 86, 68, 200))
    draw_brand(draw, shell_u, iy0 - 14, "FIELD", "NAV", pal)
    draw_chin_buttons(draw, ix0, iy1, pal)


def skin_leather_case(draw, base, pal, w, h, ix0, iy0, ix1, iy1, shell_u, seed) -> None:
    shell = sbox(shell_u)
    rounded_rect(draw, shell, 26, pal.body, pal.body_dark, 3)
    draw.arc((shell[0], shell[1], shell[0] + sc(40), shell[3]), 90, 270, fill=pal.body_dark, width=sc(4))
    draw.arc((shell[2] - sc(40), shell[1], shell[2], shell[3]), 270, 90, fill=pal.body_light, width=sc(2))
    draw_brand(draw, shell_u, iy0 - 14, "SURVIVAL", "MAP KIT", pal)
    draw_chin_buttons(draw, ix0, iy1, pal)


def skin_bakelite_radio(draw, base, pal, w, h, ix0, iy0, ix1, iy1, shell_u, seed) -> None:
    shell = sbox(shell_u)
    rounded_rect(draw, shell, 18, pal.body_dark, pal.bezel, 2)
    rounded_rect(draw, (shell[0] + sc(6), shell[1] + sc(6), shell[2] - sc(6), shell[3] - sc(6)), 14, pal.body)
    for sx, sy in corners(shell_u, 24):
        draw.ellipse(sbox((sx - 5, sy - 5, sx + 5, sy + 5)), fill=pal.bezel)
    draw_brand(draw, shell_u, iy0 - 14, "RADIO", "NAV SET", pal)
    draw_chin_buttons(draw, ix0, iy1, pal)


def skin_hunter_plate(draw, base, pal, w, h, ix0, iy0, ix1, iy1, shell_u, seed) -> None:
    shell = sbox(shell_u)
    rounded_rect(draw, shell, 12, pal.body_light, pal.body_dark, 2)
    rounded_rect(draw, (shell[0] + sc(10), shell[1] + sc(10), shell[2] - sc(10), shell[3] - sc(10)), 8, pal.body)
    for sx, sy in corners(shell_u, 30):
        draw_screw(draw, sx, sy, 7, pal)
    draw_brand(draw, shell_u, iy0 - 14, "HUNTER", "GPS", pal)
    draw_chin_buttons(draw, ix0, iy1, pal)


def skin_ammo_lid(draw, base, pal, w, h, ix0, iy0, ix1, iy1, shell_u, seed) -> None:
    shell = sbox(shell_u)
    draw.rectangle(shell, fill=pal.body_dark, outline=pal.bezel, width=sc(3))
    draw.rectangle((shell[0] + sc(12), shell[1] + sc(12), shell[2] - sc(12), shell[3] - sc(12)), outline=pal.body_light, width=sc(1))
    hinge_y = shell[1] + sc(16)
    draw.rectangle((shell[0] + sc(30), hinge_y, shell[2] - sc(30), hinge_y + sc(6)), fill=pal.screw)
    draw_brand(draw, shell_u, iy0 - 14, "7.62", "FIELD MAP", pal)
    draw_chin_buttons(draw, ix0, iy1, pal)


def skin_rusted_bolt(draw, base, pal, w, h, ix0, iy0, ix1, iy1, shell_u, seed) -> None:
    shell = sbox(shell_u)
    rounded_rect(draw, shell, 10, pal.body_dark, (80, 42, 28, 255), 2)
    rng = random.Random(seed + 5)
    for _ in range(35):
        x, y = rng.randint(shell[0], shell[2]), rng.randint(shell[1], shell[3])
        draw.point((x, y), fill=(rng.randint(50, 90), rng.randint(30, 50), rng.randint(20, 35), 180))
    for sx, sy in corners(shell_u, 26):
        draw_screw(draw, sx, sy, 9, pal)
    draw_brand(draw, shell_u, iy0 - 14, "RUST", "NAV PLATE", pal)
    draw_chin_buttons(draw, ix0, iy1, pal)


def skin_canvas_board(draw, base, pal, w, h, ix0, iy0, ix1, iy1, shell_u, seed) -> None:
    shell = sbox(shell_u)
    rounded_rect(draw, shell, 16, pal.body, pal.body_dark, 2)
    rng = random.Random(seed + 7)
    for y in range(shell[1], shell[3], sc(5)):
        c = 74 + rng.randint(-8, 8)
        draw.line((shell[0], y, shell[2], y), fill=(c, c - 6, c - 12, 60), width=1)
    draw.rectangle(sbox((shell_u[0] + 8, shell_u[1] + 8, shell_u[0] + 28, shell_u[3] - 8)), fill=(96, 88, 72, 220))
    draw_brand(draw, shell_u, iy0 - 14, "CANVAS", "MAP BOARD", pal)
    draw_chin_buttons(draw, ix0, iy1, pal)


def skin_ambulance_repurpose(draw, base, pal, w, h, ix0, iy0, ix1, iy1, shell_u, seed) -> None:
    shell = sbox(shell_u)
    rounded_rect(draw, shell, 20, (48, 46, 42, 255), pal.bezel, 2)
    rounded_rect(draw, (shell[0] + sc(8), shell[1] + sc(8), shell[2] - sc(8), shell[3] - sc(8)), 16, pal.body)
    cross_x = shell[0] + sc(36)
    cross_y = shell[1] + sc(20)
    draw.rectangle((cross_x, cross_y, cross_x + sc(4), cross_y + sc(14)), fill=(120, 38, 32, 200))
    draw.rectangle((cross_x - sc(5), cross_y + sc(5), cross_x + sc(9), cross_y + sc(9)), fill=(120, 38, 32, 200))
    draw_brand(draw, shell_u, iy0 - 14, "MED", "NAV UNIT", pal)
    draw_chin_buttons(draw, ix0, iy1, pal)


def corners(shell_u, inset: int) -> list[tuple[int, int]]:
    x0, y0, x2, y2 = shell_u
    return [(x0 + inset, y0 + inset), (x2 - inset, y0 + inset), (x0 + inset, y2 - inset), (x2 - inset, y2 - inset)]


def draw_brand(draw, shell_u, screen_top: int, a: str, b: str, pal: Palette) -> None:
    shell = sbox(shell_u)
    fl, fs = load_font(16, True), load_font(10, False)
    tx, ty = shell[0] + sc(30), shell[1] + sc(10)
    draw.text((tx, ty), a, font=fl, fill=pal.label)
    draw.text((tx, ty + sc(16)), b, font=fs, fill=(*pal.label[:3], 200))


def draw_chin_buttons(draw, ix0: int, iy1: int, pal: Palette) -> None:
    chin = sbox((ix0 + 36, iy1 + 20, ix0 + INNER_W - 36, iy1 + 48))
    rounded_rect(draw, chin, 7, pal.body_dark, pal.bezel, 1)
    f = load_font(10, True)
    draw.text((chin[0] + sc(12), chin[1] + sc(7)), "MENU", font=f, fill=pal.label)
    pwr = f.getbbox("PWR")
    draw.text((chin[2] - sc(12) - (pwr[2] - pwr[0]), chin[1] + sc(7)), "PWR", font=f, fill=pal.label)


def draw_screen_recess(draw, pal: Palette, ix0, iy0, ix1, iy1) -> None:
    recess = sbox((ix0 - 12, iy0 - 12, ix1 + 12, iy1 + 12))
    rounded_rect(draw, recess, 10, pal.bezel)
    rounded_rect(draw, sbox((ix0 - 6, iy0 - 6, ix1 + 6, iy1 + 6)), 8, pal.body_dark, pal.bezel, 1)
    split = PAD_TOP + COMPASS_H
    gap0 = iy0 + COMPASS_H
    gap1 = iy0 + COMPASS_H + COMPASS_GAP
    draw.rectangle(sbox((ix0 - 8, gap0, ix1 + 8, gap1)), fill=pal.bezel)


SKINS: list[Skin] = [
    Skin("01-garmin-worn", "Garmin Worn", Palette(
        (56, 52, 42, 255), (28, 26, 20, 255), (82, 76, 60, 255), (16, 14, 11, 255),
        (140, 128, 72, 255), (178, 48, 38, 255), (190, 182, 158, 255), (118, 112, 96, 255), (32, 30, 24, 255)), "triangle", skin_garmin_worn),
    Skin("02-soviet-metal", "Soviet Metal", Palette(
        (88, 82, 70, 255), (50, 46, 38, 255), (118, 110, 94, 255), (32, 30, 26, 255),
        (156, 72, 40, 255), (190, 52, 36, 255), (204, 196, 176, 255), (72, 68, 58, 255)), "strip", skin_soviet_metal),
    Skin("03-duct-tape", "Duct Tape Improvised", Palette(
        (62, 58, 48, 255), (34, 32, 26, 255), (88, 82, 68, 255), (22, 20, 16, 255),
        (148, 132, 78, 255), (200, 56, 42, 255), (186, 178, 156, 255), (96, 90, 76, 255)), "bracket", skin_duct_tape),
    Skin("04-leather-case", "Leather Map Case", Palette(
        (72, 54, 38, 255), (42, 32, 22, 255), (104, 78, 54, 255), (28, 20, 14, 255),
        (148, 112, 62, 255), (168, 44, 34, 255), (196, 180, 152, 255), (92, 70, 48, 255)), "crosshair", skin_leather_case),
    Skin("05-bakelite-radio", "Bakelite Radio", Palette(
        (48, 44, 38, 255), (24, 22, 18, 255), (72, 66, 56, 255), (12, 11, 9, 255),
        (132, 118, 68, 255), (184, 50, 40, 255), (178, 172, 154, 255), (86, 80, 70, 255)), "chevron", skin_bakelite_radio),
    Skin("06-hunter-plate", "Hunter Plate", Palette(
        (66, 60, 48, 255), (36, 32, 26, 255), (98, 90, 72, 255), (20, 18, 14, 255),
        (124, 104, 58, 255), (192, 46, 36, 255), (194, 186, 164, 255), (108, 100, 84, 255)), "dot_ring", skin_hunter_plate),
    Skin("07-ammo-lid", "Ammo Box Lid", Palette(
        (58, 62, 48, 255), (30, 32, 24, 255), (86, 90, 70, 255), (18, 19, 14, 255),
        (140, 136, 72, 255), (176, 42, 32, 255), (188, 184, 160, 255), (102, 106, 86, 255)), "strip", skin_ammo_lid),
    Skin("08-rusted-bolt", "Rusted Bolt Plate", Palette(
        (70, 52, 40, 255), (38, 28, 22, 255), (102, 76, 58, 255), (24, 18, 14, 255),
        (138, 96, 56, 255), (168, 38, 28, 255), (192, 176, 152, 255), (88, 64, 48, 255)), "triangle", skin_rusted_bolt),
    Skin("09-canvas-board", "Canvas Map Board", Palette(
        (78, 70, 56, 255), (44, 40, 32, 255), (108, 98, 80, 255), (26, 23, 18, 255),
        (136, 118, 66, 255), (188, 48, 38, 255), (198, 188, 166, 255), (98, 88, 72, 255)), "bracket", skin_canvas_board),
    Skin("10-ambulance-repurpose", "Repurposed Med Unit", Palette(
        (52, 50, 46, 255), (28, 26, 24, 255), (78, 74, 68, 255), (14, 13, 12, 255),
        (128, 122, 88, 255), (196, 44, 36, 255), (186, 182, 168, 255), (96, 92, 84, 255)), "crosshair", skin_ambulance_repurpose),
]


def build_frame(skin: Skin, seed: int = 0) -> Image.Image:
    pal = skin.palette
    w, h = canvas_size()
    rw, rh = sc(w), sc(h)
    base = Image.new("RGBA", (rw, rh), (0, 0, 0, 0))
    draw = ImageDraw.Draw(base)

    ix0, iy0, ix1, iy1 = inner_box()
    shell_u = (20, 18, w - 20, h - 18)

    skin.drawer(draw, base, pal, w, h, ix0, iy0, ix1, iy1, shell_u, seed)
    draw_screen_recess(draw, pal, ix0, iy0, ix1, iy1)
    draw_labels(draw, pal)

    mx0, my0, mx1, my1 = inner_map_box()
    ms = sbox((mx0, my0, mx1, my1))
    draw.rounded_rectangle(ms, radius=sc(3), outline=(*pal.body_light[:3], 120), width=max(1, sc(1)))

    shadow = Image.new("RGBA", (rw, rh), (0, 0, 0, 0))
    sh = sbox(shell_u)
    ImageDraw.Draw(shadow).rounded_rectangle((sh[0] + sc(5), sh[1] + sc(7), sh[2] + sc(5), sh[3] + sc(7)), sc(18), fill=(0, 0, 0, 80))
    base = Image.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(sc(7))), base)

    # Fixed-size transparent windows — full compass + full map
    mask = Image.new("L", (rw, rh), 255)
    mdraw = ImageDraw.Draw(mask)
    mdraw.rounded_rectangle(sbox(inner_compass_box()), radius=sc(3), fill=0)
    mdraw.rounded_rectangle(sbox(inner_map_box()), radius=sc(4), fill=0)
    rgba = base.split()
    alpha = Image.composite(rgba[3], Image.new("L", (rw, rh), 0), mask)
    base = Image.merge("RGBA", [*rgba[:3], alpha])

    # Center marker drawn AFTER mask — does not change inner window size
    draw2 = ImageDraw.Draw(base)
    MARKERS[skin.marker](draw2, pal)

    out = base.resize((w, h), Image.Resampling.LANCZOS)
    out = out.filter(ImageFilter.UnsharpMask(radius=1.0, percent=65, threshold=3))
    return apply_dayz_finish(out, seed)


def save_set() -> list[Path]:
    OUT.mkdir(parents=True, exist_ok=True)
    saved: list[Path] = []

    for i, skin in enumerate(SKINS):
        img = build_frame(skin, seed=10 + i * 17)
        path = OUT / f"{skin.slug}.png"
        img.save(path, "PNG", optimize=True)
        saved.append(path)
        path4 = OUT / f"{skin.slug}-4k.png"
        img.resize((img.width * 2, img.height * 2), Image.Resampling.LANCZOS).save(path4, "PNG", optimize=True)
        saved.append(path4)
        print(f"Saved {skin.slug} — {skin.title}")

    guide = build_frame(SKINS[0], 99).copy()
    gdraw = ImageDraw.Draw(guide)
    gdraw.rectangle(inner_compass_box(), outline=(220, 170, 70, 200), width=2)
    gdraw.rectangle(inner_map_box(), outline=(90, 150, 190, 200), width=2)
    cx, cy = compass_center()
    gdraw.line((cx - 12, cy, cx + 12, cy), fill=(255, 60, 50, 220), width=1)
    gdraw.line((cx, cy - 12, cx, cy + 12), fill=(255, 60, 50, 220), width=1)
    gp = OUT / "00-layout-guide.png"
    guide.save(gp, "PNG")
    saved.append(gp)

    import zipfile
    zp = OUT / "minimap-frames-10skins.zip"
    with zipfile.ZipFile(zp, "w") as zf:
        for p in saved:
            zf.write(p, p.name)
    saved.append(zp)
    print(f"Saved {zp.name}")
    return saved


def main() -> None:
    save_set()


if __name__ == "__main__":
    main()
