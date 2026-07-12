#!/usr/bin/env python3
"""Generate DayZ-style minimap device frames with smooth anti-aliased rendering."""

from __future__ import annotations

import random
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageFont

OUT = Path("/workspace/minimap-frames")
RENDER_SCALE = 4

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
    screw: tuple[int, int, int, int]
    label: tuple[int, int, int, int]
    glow: tuple[int, int, int, int]
    rubber: tuple[int, int, int, int] | None = None


# Muted, worn palettes inspired by DayZ HUD / survival gear.
PALETTES = {
    "garmin-foretrex": Palette(
        body=(54, 50, 40, 255),
        body_dark=(30, 28, 22, 255),
        body_light=(78, 72, 58, 255),
        bezel=(18, 16, 13, 255),
        accent=(138, 126, 74, 255),
        screw=(112, 106, 90, 255),
        label=(188, 180, 158, 255),
        glow=(88, 168, 72, 255),
        rubber=(34, 32, 26, 255),
    ),
    "tactical-olive": Palette(
        body=(50, 48, 38, 255),
        body_dark=(26, 24, 19, 255),
        body_light=(74, 70, 56, 255),
        bezel=(14, 13, 10, 255),
        accent=(154, 118, 52, 255),
        screw=(98, 94, 80, 255),
        label=(184, 178, 158, 255),
        glow=(196, 148, 48, 255),
        rubber=(22, 20, 16, 255),
    ),
    "soviet-metal": Palette(
        body=(82, 76, 64, 255),
        body_dark=(48, 44, 38, 255),
        body_light=(112, 104, 88, 255),
        bezel=(30, 28, 24, 255),
        accent=(132, 68, 40, 255),
        screw=(68, 64, 56, 255),
        label=(198, 190, 170, 255),
        glow=(148, 72, 44, 255),
    ),
    "carbon-black": Palette(
        body=(34, 34, 32, 255),
        body_dark=(16, 16, 15, 255),
        body_light=(54, 54, 50, 255),
        bezel=(8, 8, 7, 255),
        accent=(98, 138, 148, 255),
        screw=(74, 76, 72, 255),
        label=(172, 176, 170, 255),
        glow=(72, 148, 168, 255),
        rubber=(14, 14, 13, 255),
    ),
    "worn-field": Palette(
        body=(66, 58, 46, 255),
        body_dark=(38, 34, 28, 255),
        body_light=(96, 86, 70, 255),
        bezel=(22, 20, 16, 255),
        accent=(124, 100, 58, 255),
        screw=(104, 96, 80, 255),
        label=(196, 186, 164, 255),
        glow=(118, 98, 56, 255),
        rubber=(28, 25, 20, 255),
    ),
}


def sc(v: int | float) -> int:
    return int(round(v * RENDER_SCALE))


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    size = max(12, sc(size))
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for p in paths:
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


def inner_compass_center_hole() -> tuple[int, int, int, int]:
    """Transparent window in the middle of the compass strip for HUD."""
    cx0, cy0, cx1, cy1 = inner_compass_box()
    w = cx1 - cx0
    hole_w = int(w * 0.84)
    hx0 = cx0 + (w - hole_w) // 2
    return hx0, cy0 + 2, hx0 + hole_w, cy1 - 2


def compass_label_box() -> tuple[int, int, int, int]:
    cx0, cy0, cx1, cy1 = inner_compass_box()
    hx0, _, _, _ = inner_compass_center_hole()
    return cx0 + 4, cy0 + 2, hx0 - 6, cy1 - 2


def map_label_box() -> tuple[int, int, int, int]:
    ix0, iy0, ix1, _ = inner_box()
    split_y = iy0 + COMPASS_H
    map_y0 = iy0 + COMPASS_H + COMPASS_GAP
    return ix0 + 6, split_y + 1, ix0 + 90, map_y0 - 1


def inner_map_box() -> tuple[int, int, int, int]:
    ix0, iy0, ix1, iy1 = inner_box()
    return ix0, iy0 + COMPASS_H + COMPASS_GAP, ix1, iy1


def sbox(box: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    return sc(box[0]), sc(box[1]), sc(box[2]), sc(box[3])


def vertical_gradient(size: tuple[int, int], top: tuple[int, int, int], bottom: tuple[int, int, int]) -> Image.Image:
    w, h = size
    top_img = Image.new("RGB", (w, h), top)
    bot_img = Image.new("RGB", (w, h), bottom)
    grad = Image.linear_gradient("L").resize((w, h))
    return Image.composite(bot_img, top_img, grad)


def rounded_rect(draw: ImageDraw.ImageDraw, box, radius: int, fill, outline=None, width: int = 1) -> None:
    draw.rounded_rectangle(box, radius=sc(radius), fill=fill, outline=outline, width=max(1, sc(width)))


def apply_dayz_finish(img: Image.Image, seed: int, style: str) -> Image.Image:
    rng = random.Random(seed + 101)
    w, h = img.size

    grain = Image.effect_noise((w, h), 12).convert("L")
    grain = grain.filter(ImageFilter.GaussianBlur(0.6))
    grain_rgb = Image.merge("RGB", [grain, grain, grain])
    rgb = img.convert("RGB")
    dusty = ImageChops.multiply(rgb, grain_rgb)
    img = Image.merge("RGBA", (*dusty.split(), img.split()[3]))

    grime = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(grime)
    for _ in range(18 if style != "carbon" else 8):
        x = rng.randint(0, w)
        y = rng.randint(0, h)
        r = rng.randint(sc(20), sc(90))
        shade = rng.randint(18, 42)
        gdraw.ellipse((x - r, y - r, x + r, y - r // 2), fill=(shade, shade - 4, shade - 8, rng.randint(16, 34)))
    grime = grime.filter(ImageFilter.GaussianBlur(sc(8)))
    img = Image.alpha_composite(img, grime)

    rgb = img.convert("RGB")
    rgb = ImageEnhance.Color(rgb).enhance(0.72)
    rgb = ImageEnhance.Contrast(rgb).enhance(1.04)
    rgb = ImageEnhance.Brightness(rgb).enhance(0.96)
    return Image.merge("RGBA", (*rgb.split(), img.split()[3]))


def draw_screw(draw: ImageDraw.ImageDraw, x: int, y: int, r: int, col, dark) -> None:
    x, y = sc(x), sc(y)
    r = sc(r)
    draw.ellipse((x - r, y - r, x + r, y + r), fill=col, outline=dark, width=max(1, sc(1)))
    draw.arc((x - r + sc(2), y - r + sc(2), x + r - sc(2), y + r - sc(2)), 20, 160, fill=dark, width=max(1, sc(1)))


def draw_side_button(draw: ImageDraw.ImageDraw, box, pal: Palette) -> None:
    box = sbox(box)
    rounded_rect(draw, box, 6, pal.body_dark, pal.bezel, 1)
    draw.line((box[0] + sc(5), box[1] + sc(4), box[2] - sc(5), box[1] + sc(4)), fill=(*pal.body_light[:3], 140), width=max(1, sc(1)))


def draw_soft_led(base: Image.Image, x: int, y: int, color) -> None:
    glow = Image.new("RGBA", base.size, (0, 0, 0, 0))
    g = ImageDraw.Draw(glow)
    cx, cy = sc(x), sc(y)
    g.ellipse((cx - sc(10), cy - sc(10), cx + sc(10), cy + sc(10)), fill=(*color[:3], 50))
    glow = glow.filter(ImageFilter.GaussianBlur(sc(5)))
    base.alpha_composite(glow)
    draw = ImageDraw.Draw(base)
    draw.ellipse((cx - sc(4), cy - sc(4), cx + sc(4), cy + sc(4)), fill=(12, 14, 10, 255))
    draw.ellipse((cx - sc(2), cy - sc(2), cx + sc(2), cy + sc(2)), fill=color)


def draw_brand_label(draw: ImageDraw.ImageDraw, shell_u, screen_top: int, label: str, sub: str, pal: Palette) -> None:
    shell = sbox(shell_u)
    font_l = load_font(17, bold=True)
    font_s = load_font(11, bold=False)
    tx = shell[0] + sc(34)
    ty = shell[1] + sc(12)
    lb = font_l.getbbox(label)
    sb = font_s.getbbox(sub)
    text_w = max(lb[2] - lb[0], sb[2] - sb[0])
    text_h = (lb[3] - lb[1]) + sc(18) + (sb[3] - sb[1])
    plate = (tx - sc(10), ty - sc(6), tx + text_w + sc(16), min(ty + text_h + sc(8), sc(screen_top) - sc(8)))
    rounded_rect(draw, plate, 6, (*pal.body_dark[:3], 215), pal.bezel, 1)
    draw.text((tx, ty), label, font=font_l, fill=pal.label)
    draw.text((tx, ty + sc(18)), sub, font=font_s, fill=(*pal.label[:3], 210))


def draw_zone_label(
    draw: ImageDraw.ImageDraw,
    box_u: tuple[int, int, int, int],
    text: str,
    pal: Palette,
    accent: bool = False,
) -> None:
    box = sbox(box_u)
    font = load_font(10, bold=True)
    tb = font.getbbox(text)
    tw, th = tb[2] - tb[0], tb[3] - tb[1]
    tx = box[0] + sc(6)
    ty = box[1] + ((box[3] - box[1]) - th) // 2 - tb[1]
    fill = pal.accent if accent else pal.label
    draw.text((tx, ty), text, font=font, fill=fill)


def draw_compass_housing(draw: ImageDraw.ImageDraw, base: Image.Image, pal: Palette, ix0: int, iy0: int, ix1: int) -> None:
    cx0, cy0, cx1, cy1 = inner_compass_box()
    hx0, hy0, hx1, hy1 = inner_compass_center_hole()
    split_y = iy0 + COMPASS_H
    map_y0 = iy0 + COMPASS_H + COMPASS_GAP

    housing = (ix0 - 4, iy0 - 4, ix1 + 4, split_y + 4)
    hs = sbox(housing)
    backing = (12, 14, 11, 255)

    # Opaque compass backing (full strip)
    cfull = sbox((cx0 - 2, cy0 - 2, cx1 + 2, cy1 + 2))
    rounded_rect(draw, cfull, 4, backing, pal.bezel, 1)

    # Side wings darker
    left_wing = sbox((cx0 - 2, cy0 - 2, hx0 - 1, cy1 + 2))
    right_wing = sbox((hx1 + 1, cy0 - 2, cx1 + 2, cy1 + 2))
    draw.rectangle(left_wing, fill=(18, 20, 16, 255))
    draw.rectangle(right_wing, fill=(18, 20, 16, 255))

    # Center sight frame around transparent hole
    hole = sbox((hx0, hy0, hx1, hy1))
    rounded_rect(draw, hole, 3, (8, 9, 8, 255), pal.accent, 1)
    ncx = (hole[0] + hole[2]) // 2
    ncy = (hole[1] + hole[3]) // 2
    draw.line((ncx, hole[1] + sc(2), ncx, hole[3] - sc(2)), fill=(*pal.accent[:3], 120), width=max(1, sc(1)))
    draw.line((hole[0] + sc(3), ncy, hole[2] - sc(3), ncy), fill=(*pal.accent[:3], 90), width=max(1, sc(1)))
    draw.polygon(
        [(ncx, hole[1] - sc(5)), (ncx - sc(4), hole[1] + sc(1)), (ncx + sc(4), hole[1] + sc(1))],
        fill=pal.accent,
    )

    # Module frame
    rounded_rect(draw, hs, 6, None, pal.body_light, 1)

    # Divider between compass and map
    divider = sbox((ix0 - 6, split_y, ix1 + 6, map_y0))
    draw.rectangle(divider, fill=pal.bezel)
    draw.line((divider[0], divider[1] + sc(1), divider[2], divider[1] + sc(1)), fill=(*pal.body_light[:3], 80), width=max(1, sc(1)))

    draw_zone_label(draw, compass_label_box(), "COMPASS", pal, accent=True)
    draw_zone_label(draw, map_label_box(), "MAP", pal, accent=False)


def build_frame(pal: Palette, style: str, seed: int = 0) -> Image.Image:
    w, h = canvas_size()
    rw, rh = sc(w), sc(h)
    base = Image.new("RGBA", (rw, rh), (0, 0, 0, 0))
    draw = ImageDraw.Draw(base)

    ix0, iy0, ix1, iy1 = inner_box()
    shell_u = (20, 18, w - 20, h - 18)
    outer = sbox((14, 12, w - 14, h - 12))
    shell = sbox(shell_u)
    face = sbox((30, 28, w - 30, h - 30))

    if pal.rubber and style in {"garmin", "field"}:
        for bx in (4, w - 30):
            rounded_rect(draw, sbox((bx, h // 2 - 84, bx + 24, h // 2 + 84)), 10, pal.rubber, pal.bezel, 1)

    rounded_rect(draw, outer, 22, pal.bezel)
    rounded_rect(draw, shell, 18, pal.body_dark, pal.bezel, 2)

    # Corner brackets — different visual style
    for bx, by, dx, dy in (
        (shell[0], shell[1], 1, 1),
        (shell[2], shell[1], -1, 1),
        (shell[0], shell[3], 1, -1),
        (shell[2], shell[3], -1, -1),
    ):
        draw.line((bx, by, bx + dx * sc(24), by), fill=pal.accent, width=max(1, sc(2)))
        draw.line((bx, by, bx, by + dy * sc(24)), fill=pal.accent, width=max(1, sc(2)))

    face_grad = vertical_gradient((face[2] - face[0], face[3] - face[1]), pal.body_light[:3], pal.body_dark[:3])
    mask_face = Image.new("L", (rw, rh), 0)
    ImageDraw.Draw(mask_face).rounded_rectangle(face, radius=sc(16), fill=255)
    grad_rgba = Image.new("RGBA", (rw, rh), (0, 0, 0, 0))
    grad_rgba.paste(face_grad, (face[0], face[1]))
    grad_rgba.putalpha(mask_face)
    base = Image.alpha_composite(base, grad_rgba)
    draw = ImageDraw.Draw(base)
    rounded_rect(draw, face, 16, None, pal.body_light, 1)

    screen_recess = sbox((ix0 - 14, iy0 - 14, ix1 + 14, iy1 + 14))
    rounded_rect(draw, screen_recess, 11, pal.bezel)
    rounded_rect(draw, sbox((ix0 - 8, iy0 - 8, ix1 + 8, iy1 + 8)), 9, pal.body_dark, pal.bezel, 1)

    draw_compass_housing(draw, base, pal, ix0, iy0, ix1)

    mx0, my0, mx1, my1 = inner_map_box()
    ms = sbox((mx0, my0, mx1, my1))
    rounded_rect(draw, ms, 4, None, (*pal.body_light[:3], 130), 1)

    for sx, sy in (
        (shell_u[0] + 28, shell_u[1] + 28),
        (shell_u[2] - 28, shell_u[1] + 28),
        (shell_u[0] + 28, shell_u[3] - 28),
        (shell_u[2] - 28, shell_u[3] - 28),
    ):
        draw_screw(draw, sx, sy, 8, pal.screw, pal.body_dark)

    draw_side_button(draw, (shell_u[0] + 8, iy0 + 70, shell_u[0] + 26, iy0 + 126), pal)
    draw_side_button(draw, (shell_u[0] + 8, iy0 + 146, shell_u[0] + 26, iy0 + 202), pal)
    draw_side_button(draw, (shell_u[2] - 26, iy0 + 100, shell_u[2] - 8, iy0 + 168), pal)
    draw_side_button(draw, (shell_u[2] - 26, iy0 + 186, shell_u[2] - 8, iy0 + 242), pal)

    if style == "garmin":
        label, sub = "GARMIN", "FORETREX 401"
    elif style == "soviet":
        label, sub = "ПРИБОР", "НАВИГАЦИИ"
    elif style == "carbon":
        label, sub = "NAV", "DISPLAY"
    elif style == "field":
        label, sub = "FIELD", "NAV UNIT"
    else:
        label, sub = "TACTICAL", "GPS"

    draw_brand_label(draw, shell_u, iy0 - 14, label, sub, pal)

    menu_font = load_font(11, bold=True)
    pwr_bb = menu_font.getbbox("PWR")
    chin = sbox((ix0 + 36, iy1 + 20, ix1 - 36, iy1 + 48))
    rounded_rect(draw, chin, 8, pal.body_dark, pal.bezel, 1)
    draw.text((chin[0] + sc(14), chin[1] + sc(8)), "MENU", font=menu_font, fill=pal.label)
    draw.text((chin[2] - sc(14) - (pwr_bb[2] - pwr_bb[0]), chin[1] + sc(8)), "PWR", font=menu_font, fill=pal.label)

    if style in {"garmin", "tactical", "field"}:
        draw_soft_led(base, w - 66, 36, pal.glow if style != "garmin" else (88, 168, 72, 255))

    shadow = Image.new("RGBA", (rw, rh), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle((shell[0] + sc(6), shell[1] + sc(8), shell[2] + sc(6), shell[3] + sc(8)), sc(22), fill=(0, 0, 0, 90))
    shadow = shadow.filter(ImageFilter.GaussianBlur(sc(8)))
    base = Image.alpha_composite(shadow, base)

    mask = Image.new("L", (rw, rh), 255)
    mdraw = ImageDraw.Draw(mask)
    mdraw.rounded_rectangle(sbox(inner_compass_center_hole()), radius=sc(3), fill=0)
    mdraw.rounded_rectangle(sbox(inner_map_box()), radius=sc(4), fill=0)
    rgba = base.split()
    alpha = Image.composite(rgba[3], Image.new("L", (rw, rh), 0), mask)
    base = Image.merge("RGBA", [*rgba[:3], alpha])

    out = base.resize((w, h), Image.Resampling.LANCZOS)
    out = out.filter(ImageFilter.UnsharpMask(radius=1.1, percent=70, threshold=3))
    return apply_dayz_finish(out, seed, style)


def save_set() -> list[Path]:
    OUT.mkdir(parents=True, exist_ok=True)
    saved: list[Path] = []

    specs = [
        ("01-garmin-foretrex.png", "garmin-foretrex", "garmin", 11),
        ("02-tactical-olive.png", "tactical-olive", "tactical", 22),
        ("03-soviet-metal.png", "soviet-metal", "soviet", 33),
        ("04-carbon-black.png", "carbon-black", "carbon", 44),
        ("05-worn-field.png", "worn-field", "field", 55),
    ]

    for fname, pal_key, style, seed in specs:
        img = build_frame(PALETTES[pal_key], style, seed)
        path_2k = OUT / fname
        img.save(path_2k, "PNG", optimize=True)
        saved.append(path_2k)

        img_4k = img.resize((img.width * 2, img.height * 2), Image.Resampling.LANCZOS)
        img_4k = img_4k.filter(ImageFilter.UnsharpMask(radius=0.8, percent=55, threshold=3))
        path_4k = OUT / fname.replace(".png", "-4k.png")
        img_4k.save(path_4k, "PNG", optimize=True)
        saved.append(path_4k)
        print(f"Saved {path_2k.name} and {path_4k.name}")

    guide = build_frame(PALETTES["garmin-foretrex"], "garmin", 99).copy()
    gdraw = ImageDraw.Draw(guide)
    gdraw.rectangle(inner_compass_center_hole(), outline=(255, 210, 90, 200), width=2)
    gdraw.rectangle(inner_map_box(), outline=(100, 170, 210, 200), width=2)
    guide_path = OUT / "00-layout-guide.png"
    guide.save(guide_path, "PNG", optimize=True)
    saved.append(guide_path)

    import zipfile

    zip_path = OUT / "minimap-frames.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        for p in saved:
            zf.write(p, p.name)
    saved.append(zip_path)
    print(f"Saved {zip_path.name}")
    return saved


def main() -> None:
    save_set()


if __name__ == "__main__":
    main()
