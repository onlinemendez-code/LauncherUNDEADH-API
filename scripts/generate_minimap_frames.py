#!/usr/bin/env python3
"""Generate rugged device-style frames for DayZ minimap + compass HUD overlays."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

OUT = Path("/workspace/minimap-frames")

# Inner transparent viewport (compass strip + map), tuned for DayZ HUD proportions.
INNER_W = 760
COMPASS_H = 78
MAP_H = 620
INNER_H = COMPASS_H + MAP_H
PAD_TOP = 54
PAD_SIDE = 58
PAD_BOTTOM = 92


@dataclass
class Palette:
    name: str
    body: tuple[int, int, int, int]
    body_dark: tuple[int, int, int, int]
    body_light: tuple[int, int, int, int]
    bezel: tuple[int, int, int, int]
    accent: tuple[int, int, int, int]
    screw: tuple[int, int, int, int]
    label: tuple[int, int, int, int]
    rubber: tuple[int, int, int, int] | None = None


PALETTES = {
    "garmin-foretrex": Palette(
        name="GARMIN FORETREX 401",
        body=(58, 68, 48, 255),
        body_dark=(34, 40, 28, 255),
        body_light=(92, 104, 72, 255),
        bezel=(20, 24, 16, 255),
        accent=(132, 156, 84, 255),
        screw=(168, 174, 148, 255),
        label=(214, 222, 188, 255),
        rubber=(36, 40, 30, 255),
    ),
    "tactical-olive": Palette(
        name="TACTICAL GPS",
        body=(52, 58, 42, 255),
        body_dark=(28, 32, 22, 255),
        body_light=(78, 86, 60, 255),
        bezel=(14, 16, 12, 255),
        accent=(168, 132, 52, 255),
        screw=(108, 112, 96, 255),
        label=(214, 210, 188, 255),
        rubber=(20, 22, 16, 255),
    ),
    "soviet-metal": Palette(
        name="ПРИБОР НАВИГАЦИИ",
        body=(98, 92, 78, 255),
        body_dark=(58, 54, 46, 255),
        body_light=(132, 126, 108, 255),
        bezel=(36, 34, 30, 255),
        accent=(150, 72, 44, 255),
        screw=(72, 68, 60, 255),
        label=(220, 214, 196, 255),
    ),
    "carbon-black": Palette(
        name="NAV DISPLAY",
        body=(24, 26, 28, 255),
        body_dark=(10, 11, 12, 255),
        body_light=(46, 48, 52, 255),
        bezel=(4, 4, 5, 255),
        accent=(72, 168, 196, 255),
        screw=(88, 92, 96, 255),
        label=(196, 200, 206, 255),
        rubber=(14, 15, 16, 255),
    ),
    "worn-field": Palette(
        name="FIELD NAV UNIT",
        body=(74, 66, 52, 255),
        body_dark=(42, 38, 30, 255),
        body_light=(108, 98, 78, 255),
        bezel=(24, 22, 18, 255),
        accent=(132, 108, 62, 255),
        screw=(118, 110, 92, 255),
        label=(228, 220, 200, 255),
        rubber=(32, 28, 22, 255),
    ),
}


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for p in paths:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def canvas_size() -> tuple[int, int]:
    w = INNER_W + PAD_SIDE * 2
    h = INNER_H + PAD_TOP + PAD_BOTTOM
    return w, h


def inner_box() -> tuple[int, int, int, int]:
    return PAD_SIDE, PAD_TOP, PAD_SIDE + INNER_W, PAD_TOP + INNER_H


def add_noise(img: Image.Image, amount: int = 10, seed: int = 7) -> Image.Image:
    rng = random.Random(seed)
    w, h = img.size
    noise = Image.new("L", (w, h))
    px = noise.load()
    for y in range(0, h, 2):
        for x in range(0, w, 2):
            v = rng.randint(220 - amount, 255)
            px[x, y] = v
            if x + 1 < w:
                px[x + 1, y] = v
            if y + 1 < h:
                px[x, y + 1] = v
    noise = noise.filter(ImageFilter.GaussianBlur(0.8))
    rgb = img.convert("RGB")
    n3 = Image.merge("RGB", [noise, noise, noise])
    mixed = ImageChops.multiply(rgb, n3)
    out = Image.merge("RGBA", (*mixed.split(), img.split()[3]))
    return out


def draw_drop_shadow(base: Image.Image, box: tuple[int, int, int, int], radius: int, spread: int = 10) -> Image.Image:
    w, h = base.size
    shadow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow)
    x0, y0, x1, y1 = box
    sdraw.rounded_rectangle((x0 + 6, y0 + 8, x1 + 6, y1 + 8), radius=radius, fill=(0, 0, 0, 120))
    shadow = shadow.filter(ImageFilter.GaussianBlur(8))
    return Image.alpha_composite(shadow, base)


def rounded_rect(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], radius: int, fill, outline=None, width: int = 1) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def draw_screw(draw: ImageDraw.ImageDraw, x: int, y: int, r: int, col: tuple[int, int, int, int], dark: tuple[int, int, int, int]) -> None:
    draw.ellipse((x - r, y - r, x + r, y + r), fill=col, outline=dark, width=2)
    draw.line((x - r + 3, y, x + r - 3, y), fill=dark, width=2)


def draw_side_button(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], pal: Palette) -> None:
    rounded_rect(draw, box, 6, pal.body_dark, pal.bezel, 2)
    lx0, ly0, lx1, ly1 = box
    draw.line((lx0 + 4, ly0 + 5, lx1 - 4, ly0 + 5), fill=pal.body_light, width=2)


def draw_led(draw: ImageDraw.ImageDraw, x: int, y: int, color: tuple[int, int, int, int]) -> None:
    draw.ellipse((x - 5, y - 5, x + 5, y + 5), fill=(10, 12, 8, 255))
    draw.ellipse((x - 3, y - 3, x + 3, y + 3), fill=color)


def build_frame(pal: Palette, style: str, seed: int = 0) -> Image.Image:
    w, h = canvas_size()
    base = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(base)

    ix0, iy0, ix1, iy1 = inner_box()
    outer = (14, 12, w - 14, h - 12)
    shell = (outer[0] + 6, outer[1] + 6, outer[2] - 6, outer[3] - 6)
    face = (shell[0] + 10, shell[1] + 10, shell[2] - 10, shell[3] - 10)

    if pal.rubber and style in {"garmin", "field"}:
        for bx in (4, w - 30):
            rounded_rect(draw, (bx, h // 2 - 84, bx + 24, h // 2 + 84), 10, pal.rubber, pal.bezel, 2)

    rounded_rect(draw, outer, 30, pal.bezel)
    rounded_rect(draw, shell, 24, pal.body_dark, pal.bezel, 3)
    rounded_rect(draw, face, 18, pal.body, pal.body_light, 2)

    # Bevel highlights / shadows
    draw.arc((face[0], face[1], face[2], face[1] + 50), 200, 340, fill=pal.body_light, width=4)
    draw.arc((face[0], face[3] - 40, face[2], face[3]), 20, 160, fill=pal.body_dark, width=5)

    screen_recess = (ix0 - 14, iy0 - 14, ix1 + 14, iy1 + 14)
    rounded_rect(draw, screen_recess, 12, pal.bezel)
    rounded_rect(draw, (ix0 - 8, iy0 - 8, ix1 + 8, iy1 + 8), 10, pal.body_dark, pal.bezel, 2)

    split_y = iy0 + COMPASS_H
    draw.rectangle((ix0 - 10, split_y - 4, ix1 + 10, split_y + 4), fill=pal.bezel)
    draw.line((ix0 - 4, split_y - 1, ix1 + 4, split_y - 1), fill=pal.body_light, width=1)
    draw.line((ix0 - 4, split_y + 1, ix1 + 4, split_y + 1), fill=pal.accent, width=2)

    draw.rounded_rectangle((ix0, iy0, ix1, iy1), radius=5, outline=pal.body_light, width=2)
    draw.rounded_rectangle((ix0 + 1, iy0 + 1, ix1 - 1, iy1 - 1), radius=4, outline=(0, 0, 0, 120), width=1)

    screw_pts = [
        (shell[0] + 28, shell[1] + 28),
        (shell[2] - 28, shell[1] + 28),
        (shell[0] + 28, shell[3] - 28),
        (shell[2] - 28, shell[3] - 28),
    ]
    for sx, sy in screw_pts:
        draw_screw(draw, sx, sy, 9, pal.screw, pal.body_dark)

    draw_side_button(draw, (shell[0] + 8, iy0 + 70, shell[0] + 26, iy0 + 126), pal)
    draw_side_button(draw, (shell[0] + 8, iy0 + 146, shell[0] + 26, iy0 + 202), pal)
    draw_side_button(draw, (shell[2] - 26, iy0 + 100, shell[2] - 8, iy0 + 168), pal)
    draw_side_button(draw, (shell[2] - 26, iy0 + 186, shell[2] - 8, iy0 + 242), pal)

    if style == "garmin":
        draw_led(draw, outer[2] - 52, outer[1] + 24, (70, 210, 90, 255))
        label = "GARMIN"
        sub = "FORETREX 401"
    elif style == "soviet":
        # Rivets along sides
        for yy in range(outer[1] + 60, outer[3] - 40, 48):
            draw.ellipse((outer[0] + 14, yy, outer[0] + 24, yy + 10), fill=pal.screw)
            draw.ellipse((outer[2] - 24, yy, outer[2] - 14, yy + 10), fill=pal.screw)
        label, sub = "ПРИБОР", "НАВИГАЦИИ"
    elif style == "carbon":
        # Carbon weave hint
        rng = random.Random(seed + 3)
        for y in range(outer[1] + 20, outer[3] - 20, 6):
            for x in range(outer[0] + 20, outer[2] - 20, 14):
                c = 34 + rng.randint(-6, 6)
                draw.line((x, y, x + 8, y + 6), fill=(c, c, c + 2, 70), width=1)
        label, sub = "NAV", "DISPLAY"
    elif style == "field":
        # Worn paint chips
        rng = random.Random(seed + 9)
        for _ in range(40):
            x = rng.randint(outer[0] + 10, outer[2] - 10)
            y = rng.randint(outer[1] + 10, outer[3] - 10)
            draw.ellipse((x, y, x + rng.randint(4, 16), y + rng.randint(2, 8)), fill=(*pal.body_light[:3], 60))
        label, sub = "FIELD", "NAV UNIT"
    else:
        draw_led(draw, outer[2] - 52, outer[1] + 24, (220, 170, 48, 255))
        label, sub = "TACTICAL", "GPS"

    font_l = load_font(22, bold=True)
    font_s = load_font(14, bold=False)
    tx = shell[0] + 42
    ty = shell[1] + 18
    draw.text((tx, ty), label, font=font_l, fill=pal.label)
    draw.text((tx, ty + 24), sub, font=font_s, fill=(*pal.label[:3], 210))

    rounded_rect(draw, (ix0 + 36, iy1 + 20, ix1 - 36, iy1 + 48), 9, pal.body_dark, pal.bezel, 2)
    draw.line((ix0 + 50, iy1 + 26, ix1 - 50, iy1 + 26), fill=pal.body_light, width=1)
    draw.text((ix0 + 50, iy1 + 30), "MENU", font=load_font(12, bold=True), fill=pal.label)
    draw.text((ix1 - 104, iy1 + 30), "PWR", font=load_font(12, bold=True), fill=pal.label)

    base = add_noise(base, amount=8 if style != "carbon" else 6, seed=seed)
    base = draw_drop_shadow(base, shell, 24)

    # Apply transparency mask for screen area
    mask = Image.new("L", (w, h), 255)
    mdraw = ImageDraw.Draw(mask)
    mdraw.rounded_rectangle((ix0, iy0, ix1, iy1), radius=4, fill=0)
    rgba = base.split()
    alpha = Image.composite(rgba[3], Image.new("L", (w, h), 0), mask)
    base = Image.merge("RGBA", [*rgba[:3], alpha])

    return base


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
        path_4k = OUT / fname.replace(".png", "-4k.png")
        img_4k.save(path_4k, "PNG", optimize=True)
        saved.append(path_4k)
        print(f"Saved {path_2k.name} and {path_4k.name}")

    # Guide overlay showing compass/map zones
    guide = build_frame(PALETTES["garmin-foretrex"], "garmin", 99).copy()
    gdraw = ImageDraw.Draw(guide)
    ix0, iy0, ix1, iy1 = inner_box()
    gdraw.rectangle((ix0, iy0, ix1, iy0 + COMPASS_H), outline=(255, 220, 80, 180), width=2)
    gdraw.rectangle((ix0, iy0 + COMPASS_H, ix1, iy1), outline=(80, 180, 255, 180), width=2)
    gdraw.text((ix0 + 8, iy0 + 8), "COMPASS", font=load_font(16, True), fill=(255, 220, 80, 220))
    gdraw.text((ix0 + 8, iy0 + COMPASS_H + 8), "MAP", font=load_font(16, True), fill=(80, 180, 255, 220))
    guide_path = OUT / "00-layout-guide.png"
    guide.save(guide_path, "PNG", optimize=True)
    saved.append(guide_path)
    print(f"Saved {guide_path.name}")

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
