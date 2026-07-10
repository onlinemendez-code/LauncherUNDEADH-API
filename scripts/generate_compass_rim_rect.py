#!/usr/bin/env python3
"""Generate a high-quality transparent PNG compass rim for rectangular maps."""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

CARDINALS = {0: "N", 90: "E", 180: "S", 270: "W"}
ORDINALS = {45: "NE", 135: "SE", 225: "SW", 315: "NW"}


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/inter/Inter-SemiBold.ttf" if bold else "/usr/share/fonts/truetype/inter/Inter-Regular.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def ray_rect_hit(
    cx: float,
    cy: float,
    angle_deg: float,
    left: float,
    top: float,
    right: float,
    bottom: float,
) -> tuple[float, float]:
    rad = math.radians(angle_deg - 90)
    dx = math.cos(rad)
    dy = math.sin(rad)
    hits: list[float] = []
    if dx > 1e-9:
        hits.append((right - cx) / dx)
    elif dx < -1e-9:
        hits.append((left - cx) / dx)
    if dy > 1e-9:
        hits.append((bottom - cy) / dy)
    elif dy < -1e-9:
        hits.append((top - cy) / dy)
    t = min(t for t in hits if t > 0)
    return cx + dx * t, cy + dy * t


def unit_from_angle(angle_deg: float) -> tuple[float, float]:
    rad = math.radians(angle_deg - 90)
    return math.cos(rad), math.sin(rad)


def draw_rotated_text(
    base: Image.Image,
    text: str,
    x: float,
    y: float,
    angle_deg: float,
    font: ImageFont.ImageFont,
    fill: tuple[int, int, int, int] = (255, 255, 255, 255),
) -> None:
    pad = 8
    bbox = font.getbbox(text)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tmp = Image.new("RGBA", (tw + pad * 2, th + pad * 2), (0, 0, 0, 0))
    ImageDraw.Draw(tmp).text((pad - bbox[0], pad - bbox[1]), text, font=font, fill=fill)
    rotated = tmp.rotate(-angle_deg, resample=Image.Resampling.BICUBIC, expand=True)
    base.alpha_composite(rotated, (int(x - rotated.width / 2), int(y - rotated.height / 2)))


def generate_rect_compass(width: int, height: int) -> Image.Image:
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    white = (255, 255, 255, 255)

    scale = min(width, height)
    band = int(scale * 0.075)
    ring_w = max(2, scale // 640)

    outer = (band // 2, band // 2, width - band // 2, height - band // 2)
    inner = (band, band, width - band, height - band)
    cx = width / 2
    cy = height / 2

    draw.rectangle(outer, outline=white, width=ring_w)
    draw.rectangle(inner, outline=white, width=max(1, ring_w - 1))

    for deg in range(0, 360, 5):
        ix, iy = ray_rect_hit(cx, cy, deg, *inner)
        ox, oy = ray_rect_hit(cx, cy, deg, *outer)
        ux, uy = unit_from_angle(deg)

        if deg % 45 == 0:
            frac, tick_w = 1.0, max(3, scale // 720)
        elif deg % 15 == 0:
            frac, tick_w = 0.88, max(2, scale // 960)
        else:
            frac, tick_w = 0.72, max(1, scale // 1280)

        x1, y1 = ix, iy
        x2 = ix + (ox - ix) * frac
        y2 = iy + (oy - iy) * frac
        draw.line([(x1, y1), (x2, y2)], fill=white, width=tick_w)

    font_cardinal = load_font(int(scale * 0.028), bold=True)
    font_ordinal = load_font(int(scale * 0.02), bold=True)
    font_degree = load_font(int(scale * 0.015), bold=False)

    def label_pos(deg: int) -> tuple[float, float]:
        ix, iy = ray_rect_hit(cx, cy, deg, *inner)
        ox, oy = ray_rect_hit(cx, cy, deg, *outer)
        return ix + (ox - ix) * 0.62, iy + (oy - iy) * 0.62

    for deg, label in CARDINALS.items():
        tx, ty = label_pos(deg)
        draw_rotated_text(img, label, tx, ty, deg, font_cardinal)

    for deg, label in ORDINALS.items():
        tx, ty = label_pos(deg)
        draw_rotated_text(img, label, tx, ty, deg, font_ordinal)

    for deg in range(0, 360, 15):
        if deg in CARDINALS or deg in ORDINALS:
            continue
        tx, ty = label_pos(deg)
        draw_rotated_text(img, str(deg), tx, ty, deg, font_degree)

    return img


def main() -> None:
    out_dir = Path("/workspace/compass-rim")
    out_dir.mkdir(parents=True, exist_ok=True)

    variants = [
        ("compass-rim-rect-4k.png", 4096, 2304),
        ("compass-rim-rect-2k.png", 2048, 1152),
        ("compass-rim-rect-square-4k.png", 4096, 4096),
        ("compass-rim-rect-square-2k.png", 2048, 2048),
    ]

    saved: list[Path] = []
    for name, w, h in variants:
        path = out_dir / name
        generate_rect_compass(w, h).save(path, "PNG", optimize=True)
        saved.append(path)
        print(f"Saved: {path} ({w}x{h})")

    import zipfile

    zip_path = out_dir / "compass-rim-rect.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        for p in saved:
            zf.write(p, p.name)
    print(f"Saved: {zip_path}")


if __name__ == "__main__":
    main()
