#!/usr/bin/env python3
"""Fixed A4 Beauty Guide 2026 layout compositor."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path("/opt/cursor/artifacts/assets")
OUT = Path("/workspace/beauty-guide")

# A4 @ 150 dpi
W, H = 1240, 1754
M = 44
LEFT_W = int((W - 2 * M) * 0.40)
RIGHT_W = W - 2 * M - LEFT_W - 16
LX = M
RX = M + LEFT_W + 16


def font(sz: int, bold: bool = False):
    p = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    return ImageFont.truetype(p, sz) if Path(p).exists() else ImageFont.load_default()


def fit(img: Image.Image, w: int, h: int) -> Image.Image:
    img = img.convert("RGB")
    r = min(w / img.width, h / img.height)
    nw, nh = int(img.width * r), int(img.height * r)
    img = img.resize((nw, nh), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (w, h), (255, 255, 255))
    canvas.paste(img, ((w - nw) // 2, (h - nh) // 2))
    return canvas


def title(d: ImageDraw.ImageDraw, text: str, x: int, y: int, sz: int = 11):
    d.text((x, y), text.upper(), font=font(sz, True), fill=(20, 20, 20))


def body(d: ImageDraw.ImageDraw, lines: list[str], x: int, y: int, sz: int = 9, gap: int = 14):
    for ln in lines:
        d.text((x, y), ln, font=font(sz), fill=(50, 50, 50))
        y += gap
    return y


def swatch_row(d: ImageDraw.ImageDraw, colors: list[tuple], labels: list[str], x: int, y: int, w: int, h: int, gap: int = 8):
    n = len(colors)
    sw = (w - gap * (n - 1)) // n
    for i, (col, lab) in enumerate(zip(colors, labels)):
        sx = x + i * (sw + gap)
        d.rectangle((sx, y, sx + sw, y + h), fill=col, outline=(210, 210, 210))
        tw = d.textlength(lab, font=font(7))
        d.text((sx + (sw - tw) // 2, y + h + 4), lab, font=font(7), fill=(80, 80, 80))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    page = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(page)

    portrait = fit(Image.open(ROOT / "beauty-source-portrait.png"), LEFT_W, 700)
    page.paste(portrait, (LX, M))

    hair_pair_full = Image.open(ROOT / "beauty-hairstyles-pair.png").convert("RGB")
    hw = hair_pair_full.width // 2
    left_style = fit(hair_pair_full.crop((0, 0, hw, hair_pair_full.height)), LEFT_W // 2 - 4, 180)
    right_style = fit(hair_pair_full.crop((hw, 0, hair_pair_full.width, hair_pair_full.height)), LEFT_W // 2 - 4, 180)
    page.paste(left_style, (LX, M + 710))
    page.paste(right_style, (LX + LEFT_W // 2 + 4, M + 710))

    # RESULT block
    ry = M + 900
    d.line((LX, ry, LX + LEFT_W, ry), fill=(220, 220, 220), width=1)
    title(d, "Результат", LX, ry + 10, 12)
    body(
        d,
        [
            "• Мягкий контур без тяжести",
            "• Волосы подчёркивают овал лица",
            "• Брови балансируют очки",
            "• Губы — главный акцент образа",
        ],
        LX,
        ry + 34,
        10,
        18,
    )

    # RIGHT — hair triptych
    tri = fit(Image.open(ROOT / "beauty-hair-triptych.png"), RIGHT_W, 260)
    page.paste(tri, (RX, M))
    title(d, "Стрижка: мягкий lob с face-framing", RX, M + 268, 10)
    body(
        d,
        [
            "Длина до ключиц. Слои у лица смягчают",
            "овал. Пробор сбоку — ваш идеальный.",
            "Укладка: объём у корней + лёгкие волны.",
        ],
        RX,
        M + 286,
        8,
        13,
    )

    # Hair palette
    py = M + 350
    title(d, "Оттенок волос", RX, py)
    hair_colors = [
        (62, 42, 30),
        (88, 58, 38),
        (110, 72, 48),
        (78, 52, 36),
        (98, 68, 44),
        (54, 36, 26),
    ]
    hair_labels = ["Эспрессо", "Каштан", "Карамель", "Мокко", "Бронза", "Шоколад"]
    swatch_row(d, hair_colors, hair_labels, RX, py + 20, RIGHT_W // 2 + 80, 28)

    tips_x = RX + RIGHT_W // 2 + 100
    body(
        d,
        [
            "Рекомендация:",
            "Тёплый каштан",
            "с карамельными",
            "бликами у лица.",
            "",
            "Избегать:",
            "платиновых",
            "и пепельных",
            "тонов.",
        ],
        tips_x,
        py + 18,
        8,
        13,
    )

    # BROWS
    by = M + 450
    title(d, "Брови", RX, by)
    body(
        d,
        [
            "Форма: мягкий изгиб",
            "с лёгким хвостом",
            "Цвет: taupe brown",
            "Толщина: средняя",
            "Не перегружать —",
            "очки уже дают акцент",
            "Фиксация: гель +",
            "карандаш точечно",
        ],
        RX,
        by + 20,
        8,
        14,
    )
    eyes = fit(Image.open(ROOT / "beauty-eyes-brows.png"), RIGHT_W // 2 + 20, 130)
    page.paste(eyes, (RX + RIGHT_W // 2 - 10, by))

    # EYES
    ey = M + 610
    title(d, "Глаза — 5 образов", RX, ey)
    row = fit(Image.open(ROOT / "beauty-eye-makeup-row.png"), RIGHT_W, 100)
    page.paste(row, (RX, ey + 18))
    labels = ["Clean", "Brown smoke", "Rose taupe", "Tightline", "Berry"]
    lx = RX
    for lab in labels:
        d.text((lx, ey + 124), lab, font=font(7), fill=(90, 90, 90))
        lx += RIGHT_W // 5

    # CHEEKS & FACE
    cy = M + 760
    title(d, "Скулы и лицо", RX, cy)
    face = fit(Image.open(ROOT / "beauty-face-contour.png"), 140, 140)
    page.paste(face, (RX, cy + 22))
    cx = RX + 160
    contour_colors = [
        ((142, 108, 88), "Контур"),
        ((196, 128, 118), "Румяна"),
        ((238, 220, 200), "Хайлайтер"),
        ((184, 132, 96), "Бронзер"),
    ]
    for i, (col, lab) in enumerate(contour_colors):
        sx = cx + (i % 2) * 110
        sy = cy + 22 + (i // 2) * 58
        d.rectangle((sx, sy, sx + 90, sy + 40), fill=col, outline=(220, 220, 220))
        d.text((sx, sy + 44), lab, font=font(8), fill=(60, 60, 60))
    body(
        d,
        [
            "Контур: cool taupe по скулам",
            "Румяна: dusty rose на яблочках",
            "Хайлайтер: шампань на скулах",
            "Бронзер: лёгкий тёплый тан",
            "Тип кожи: fair cool-neutral",
        ],
        cx,
        cy + 130,
        8,
        14,
    )

    # LIPS
    ly = M + 980
    title(d, "Губы", RX, ly)
    lip_colors = [
        (120, 58, 72),
        (168, 98, 108),
        (140, 72, 82),
        (108, 48, 58),
        (176, 108, 98),
        (128, 52, 62),
    ]
    lip_labels = ["Berry", "Mauve", "Plum", "Wine", "Nude rose", "Your shade"]
    swatch_row(d, lip_colors, lip_labels, RX, ly + 22, RIGHT_W, 36, 10)

    body(
        d,
        [
            "Ваш идеал: berry-mauve matte — уже попадаете в тон.",
            "Днём: rose nude. Вечером: plum или wine.",
        ],
        RX,
        ly + 78,
        8,
        14,
    )

    # Header title
    d.text((M, 12), "GLOW UP GUIDE", font=font(10), fill=(160, 160, 160))
    d.text((M + 130, 12), "ПЕРСОНАЛЬНАЯ ПАМЯТКА", font=font(10), fill=(160, 160, 160))

    # Footer
    ft = "Beauty Guide 2026"
    tw = d.textlength(ft, font=font(11))
    d.text((W - M - tw, H - M - 10), ft, font=font(11), fill=(120, 120, 120))

    out = OUT / "beauty-guide-2026.png"
    out_hr = OUT / "beauty-guide-2026-4k.png"
    page.save(out, "PNG", optimize=True)
    page.resize((W * 2, H * 2), Image.Resampling.LANCZOS).save(out_hr, "PNG", optimize=True)
    print(out)
    print(out_hr)


if __name__ == "__main__":
    main()
