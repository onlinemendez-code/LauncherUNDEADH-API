#!/usr/bin/env python3
"""Generate a high-quality transparent PNG compass rim (PUBG-style)."""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SIZE = 4096
CENTER = SIZE // 2
RING_RADIUS = int(SIZE * 0.36)
TICK_OUTER = int(SIZE * 0.395)
TEXT_RADIUS = int(SIZE * 0.418)

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


def polar_to_xy(radius: float, angle_deg: float) -> tuple[float, float]:
  # 0° at top, clockwise
    rad = math.radians(angle_deg - 90)
    return CENTER + radius * math.cos(rad), CENTER + radius * math.sin(rad)


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
    # Text baseline faces outward from center; angle_deg is compass bearing from top.
    rotated = tmp.rotate(-angle_deg, resample=Image.Resampling.BICUBIC, expand=True)
    base.alpha_composite(rotated, (int(x - rotated.width / 2), int(y - rotated.height / 2)))


def main() -> None:
    out_dir = Path("/workspace/compass-rim")
    out_dir.mkdir(parents=True, exist_ok=True)

    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    white = (255, 255, 255, 255)
    ring_width = max(2, SIZE // 640)

    draw.ellipse(
        [
            CENTER - RING_RADIUS,
            CENTER - RING_RADIUS,
            CENTER + RING_RADIUS,
            CENTER + RING_RADIUS,
        ],
        outline=white,
        width=ring_width,
    )

    tick_base = RING_RADIUS + ring_width // 2
    for deg in range(0, 360, 5):
        if deg % 45 == 0:
            inner_r, outer_r, tick_w = tick_base, TICK_OUTER, max(3, SIZE // 720)
        elif deg % 15 == 0:
            inner_r, outer_r, tick_w = tick_base, int(TICK_OUTER * 0.88), max(2, SIZE // 960)
        else:
            inner_r, outer_r, tick_w = tick_base, int(TICK_OUTER * 0.72), max(1, SIZE // 1280)

        x1, y1 = polar_to_xy(inner_r, deg)
        x2, y2 = polar_to_xy(outer_r, deg)
        draw.line([(x1, y1), (x2, y2)], fill=white, width=tick_w)

    font_cardinal = load_font(int(SIZE * 0.028), bold=True)
    font_ordinal = load_font(int(SIZE * 0.02), bold=True)
    font_degree = load_font(int(SIZE * 0.015), bold=False)

    for deg, label in CARDINALS.items():
        x, y = polar_to_xy(TEXT_RADIUS, deg)
        draw_rotated_text(img, label, x, y, deg, font_cardinal)

    for deg, label in ORDINALS.items():
        x, y = polar_to_xy(TEXT_RADIUS, deg)
        draw_rotated_text(img, label, x, y, deg, font_ordinal)

    for deg in range(0, 360, 15):
        if deg in CARDINALS or deg in ORDINALS:
            continue
        x, y = polar_to_xy(TEXT_RADIUS, deg)
        draw_rotated_text(img, str(deg), x, y, deg, font_degree)

    png_path = out_dir / "compass-rim-4k.png"
    img.save(png_path, "PNG", optimize=True)

    # Smaller preview / practical overlay size
    preview = img.resize((2048, 2048), Image.Resampling.LANCZOS)
    preview_path = out_dir / "compass-rim-2k.png"
    preview.save(preview_path, "PNG", optimize=True)

    print(f"Saved: {png_path}")
    print(f"Saved: {preview_path}")


if __name__ == "__main__":
    main()
