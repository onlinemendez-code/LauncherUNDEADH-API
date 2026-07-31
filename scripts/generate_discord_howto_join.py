#!/usr/bin/env python3
"""Discord forum cards — section 'Как зайти' (3 launchers), minimal UNDEAD HEAVEN style."""

from __future__ import annotations

import zipfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

W, H = 1920, 1080
ASSETS = Path("/opt/cursor/artifacts/assets")
OUT = Path("/workspace/discord-covers-howto-join")

FRAME = 300
STROKE = 14
RADIUS = 28


def font(sz: int, bold: bool = True):
    p = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    return ImageFont.truetype(p, sz) if Path(p).exists() else ImageFont.load_default()


def prep_bg(path: Path) -> Image.Image:
    img = Image.open(path).convert("RGB").resize((W, H), Image.Resampling.LANCZOS)
    img = ImageEnhance.Color(img).enhance(0.55)
    img = ImageEnhance.Contrast(img).enhance(1.05)
    img = ImageEnhance.Brightness(img).enhance(0.82)
    return img.filter(ImageFilter.GaussianBlur(2.2))


def draw_frame_icon(draw: ImageDraw.ImageDraw, cx: int, cy: int, painter):
    x0, y0 = cx - FRAME // 2, cy - FRAME // 2
    x1, y1 = x0 + FRAME, y0 + FRAME
    draw.rounded_rectangle((x0, y0, x1, y1), radius=RADIUS, outline=(255, 255, 255), width=STROKE)
    painter(draw, cx, cy)


def icon_official(d: ImageDraw.ImageDraw, cx: int, cy: int):
    """DayZ official launcher: sidebar + play triangle."""
    # sidebar
    d.rounded_rectangle((cx - 95, cy - 70, cx - 55, cy + 80), radius=6, outline=(255, 255, 255), width=10)
    for y in (cy - 45, cy - 10, cy + 25):
        d.line((cx - 88, y, cx - 62, y), fill=(255, 255, 255), width=8)
    # window
    d.rounded_rectangle((cx - 40, cy - 75, cx + 95, cy + 80), radius=8, outline=(255, 255, 255), width=10)
    # play triangle
    d.polygon([(cx + 10, cy - 20), (cx + 10, cy + 30), (cx + 60, cy + 5)], outline=(255, 255, 255), width=10)


def icon_dzsa(d: ImageDraw.ImageDraw, cx: int, cy: int):
    """DZSA red launcher: server list rows + play."""
    d.rounded_rectangle((cx - 90, cy - 80, cx + 90, cy + 80), radius=8, outline=(255, 255, 255), width=10)
    for i, w in enumerate((120, 100, 130, 90)):
        y = cy - 55 + i * 32
        d.line((cx - 70, y, cx - 70 + w, y), fill=(255, 255, 255), width=8)
    d.polygon([(cx + 45, cy + 35), (cx + 45, cy + 65), (cx + 72, cy + 50)], fill=(255, 255, 255))


def icon_uh(d: ImageDraw.ImageDraw, cx: int, cy: int):
    """UNDEAD HEAVEN launcher: play ring + car silhouette."""
    d.ellipse((cx - 70, cy - 70, cx + 70, cy + 70), outline=(255, 255, 255), width=10)
    d.polygon([(cx - 12, cy - 18), (cx - 12, cy + 22), (cx + 32, cy + 2)], fill=(255, 255, 255))
    # simple car top
    d.rounded_rectangle((cx - 38, cy - 58, cx + 38, cy - 38), radius=6, outline=(255, 255, 255), width=8)
    d.ellipse((cx - 28, cy - 34, cx - 12, cy - 18), outline=(255, 255, 255), width=6)
    d.ellipse((cx + 12, cy - 34, cx + 28, cy - 18), outline=(255, 255, 255), width=6)


def compose(bg_path: Path, title: str, subtitle: str, painter) -> Image.Image:
    img = prep_bg(bg_path).convert("RGBA")
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    # bottom gradient for title readability
    grad = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grad)
    for y in range(H - 260, H):
        a = int(180 * (y - (H - 260)) / 260)
        gd.line((0, y, W, y), fill=(0, 0, 0, a))
    overlay = Image.alpha_composite(overlay, grad)
    d = ImageDraw.Draw(overlay)

    draw_frame_icon(d, W // 2, H // 2 - 40, painter)

    f_title = font(54)
    f_sub = font(28, False)
    tw = d.textlength(title, font=f_title)
    d.text(((W - tw) // 2, H - 150), title, font=f_title, fill=(255, 255, 255, 255))
    sw = d.textlength(subtitle, font=f_sub)
    d.text(((W - sw) // 2, H - 85), subtitle, font=f_sub, fill=(220, 220, 220, 230))

    return Image.alpha_composite(img, overlay).convert("RGB")


CARDS = [
    (
        "01-official-launcher",
        "howto-bg-official.png",
        "ОРИГИНАЛЬНЫЙ ЛАУНЧЕР",
        "DayZ Launcher · Bohemia",
        icon_official,
    ),
    (
        "02-dzsa-launcher",
        "howto-bg-dzsa.png",
        "DZSA LAUNCHER",
        "Красный лаунчер · Список серверов",
        icon_dzsa,
    ),
    (
        "03-uh-launcher",
        "howto-bg-uh-launcher.png",
        "НАШ ЛАУНЧЕР",
        "UNDEAD HEAVEN · UH Launcher",
        icon_uh,
    ),
]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    saved = []
    for slug, bg, title, sub, painter in CARDS:
        img = compose(ASSETS / bg, title, sub, painter)
        p = OUT / f"{slug}-1080p.png"
        img.save(p, "PNG", optimize=True)
        saved.append(p)
        print(f"{p.name}: {title}")

    zp = OUT / "discord-howto-join-3.zip"
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in saved:
            zf.write(p, p.name)
    print(f"Saved {zp}")


if __name__ == "__main__":
    main()
