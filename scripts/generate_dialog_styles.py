#!/usr/bin/env python3
"""10 radical dialogue UI style mockups — same B/W palette, different structure."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path("/workspace/dialog-styles")
W, H = 1280, 720

TITLE = "ЧЁРНЫЙ РЫНОК «БАРЫГА»"
LINE = "Псс... сюда. Здесь не спрашивают, откуда товар. Спрашивают цену."
OPTS = [
    "Есть работа?",
    "Это чёрный рынок?",
    "Можно доверять?",
    "Есть горячие заказы?",
]


def font(sz: int, bold: bool = False):
    paths = (
        ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
        if bold
        else ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
    )
    for p in paths:
        if Path(p).exists():
            return ImageFont.truetype(p, sz)
    return ImageFont.load_default()


def bg() -> Image.Image:
    """Simulated in-game backdrop."""
    img = Image.new("RGB", (W, H), (42, 40, 38))
    d = ImageDraw.Draw(img)
    for y in range(0, H, 28):
        d.line((0, y, W, y), fill=(38, 36, 34))
    for x in range(0, W, 40):
        d.line((x, 0, x, H), fill=(36, 34, 32))
    d.rectangle((W // 2 - 80, H // 2 - 120, W // 2 + 80, H // 2 + 180), fill=(55, 52, 48))
    d.ellipse((W // 2 - 30, H // 2 - 200, W // 2 + 30, H // 2 - 140), fill=(70, 65, 60))
    return img


def wrap(draw: ImageDraw.ImageDraw, text: str, fnt, max_w: int) -> list[str]:
    words, lines, cur = text.split(), [], ""
    for w in words:
        test = f"{cur} {w}".strip()
        if draw.textlength(test, font=fnt) <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def label(draw, text, x, y, fnt, fill=(235, 235, 235)):
    draw.text((x, y), text, font=fnt, fill=fill)


def opt_btn(draw, x, y, w, h, text, fnt, fill=(210, 210, 210), text_fill=(20, 20, 20)):
    draw.rectangle((x, y, x + w, y + h), fill=fill, outline=(180, 180, 180))
    tw = draw.textlength(text, font=fnt)
    draw.text((x + (w - tw) // 2, y + (h - 18) // 2), text, font=fnt, fill=text_fill)


def save(img: Image.Image, name: str, title: str):
    banner = Image.new("RGB", (W, 36), (18, 18, 18))
    bd = ImageDraw.Draw(banner)
    bd.text((12, 8), title, font=font(14, True), fill=(200, 200, 200))
    out = Image.new("RGB", (W, H + 36), (18, 18, 18))
    out.paste(banner, (0, 0))
    out.paste(img, (0, 36))
    p = OUT / f"{name}.png"
    out.save(p, "PNG", optimize=True)
    print(p)


# ── 01 CORNER BRACKETS — no box, only tactical corners ─────────────────────
def style_01():
    img = bg().convert("RGBA")
    d = ImageDraw.Draw(img)
    bx, by, bw, bh = 60, H - 290, W - 120, 250
    col = (220, 220, 220)
    arm = 36
    for x, y, dx, dy in ((bx, by, 1, 1), (bx + bw, by, -1, 1), (bx, by + bh, 1, -1), (bx + bw, by + bh, -1, -1)):
        d.line((x, y, x + dx * arm, y), fill=col, width=3)
        d.line((x, y, x, y + dy * arm), fill=col, width=3)
    label(d, TITLE, bx + 20, by + 16, font(22, True))
    label(d, LINE, bx + 20, by + 58, font(15))
    oy = by + 120
    for i, o in enumerate(OPTS):
        opt_btn(d, bx + 20, oy + i * 34, bw - 40, 28, o, font(13))
    save(img.convert("RGB"), "01-corner-brackets", "01 — CORNER BRACKETS (только угловые скобы, без рамки)")


# ── 02 TELETYPE STRIP — perforated paper band ───────────────────────────────
def style_02():
    img = bg().convert("RGBA")
    d = ImageDraw.Draw(img)
    y0, y1 = H - 200, H - 30
    d.rectangle((0, y0, W, y1), fill=(12, 12, 12, 230))
    for x in range(0, W, 14):
        d.ellipse((x, y0 - 4, x + 6, y0 + 2), fill=(30, 30, 30))
        d.ellipse((x, y1 - 2, x + 6, y1 + 4), fill=(30, 30, 30))
    mf = font(16)
    label(d, f"> {TITLE}", 40, y0 + 14, mf)
    for i, ln in enumerate(wrap(d, LINE, font(14), W - 80)):
        label(d, ln, 40, y0 + 42 + i * 20, font(14), (190, 190, 190))
    ox = 40
    for i, o in enumerate(OPTS):
        label(d, f"[{i + 1}] {o}", ox, y0 + 100 + i * 22, font(13), (200, 200, 200))
    save(img.convert("RGB"), "02-teletype-strip", "02 — TELETYPE (лента телетайпа с перфорацией)")


# ── 03 DOSSIER FOLDER — tab + document ───────────────────────────────────────
def style_03():
    img = bg().convert("RGBA")
    d = ImageDraw.Draw(img)
    dx, dy, dw, dh = 80, H - 310, W - 160, 270
    d.rectangle((dx, dy + 24, dx + dw, dy + dh), fill=(16, 16, 16, 235), outline=(200, 200, 200))
    d.polygon([(dx + 20, dy + 24), (dx + 20, dy), (dx + 220, dy), (dx + 240, dy + 24)], fill=(28, 28, 28))
    label(d, "ДОСЬЕ // БАРЫГА", dx + 32, dy + 4, font(11, True), (170, 170, 170))
    d.line((dx + 16, dy + 52, dx + dw - 16, dy + 52), fill=(80, 80, 80))
    label(d, TITLE, dx + 24, dy + 64, font(20, True))
    for i, ln in enumerate(wrap(d, LINE, font(14), dw - 48)):
        label(d, ln, dx + 24, dy + 98 + i * 22, font(14), (200, 200, 200))
    d.rectangle((dx + dw - 90, dy + 40, dx + dw - 20, dy + 70), outline=(200, 200, 200))
    label(d, "СЕКРЕТНО", dx + dw - 82, dy + 48, font(10, True), (180, 180, 180))
    for i, o in enumerate(OPTS):
        d.rectangle((dx + 24, dy + 155 + i * 32, dx + dw - 24, dy + 181 + i * 32), outline=(120, 120, 120))
        label(d, f"□ {o}", dx + 36, dy + 160 + i * 32, font(13))
    save(img.convert("RGB"), "03-dossier-folder", "03 — DOSSIER (папка с ярлыком и штампом)")


# ── 04 VERTICAL SPLIT — NPC left / choices right ───────────────────────────
def style_04():
    img = bg().convert("RGBA")
    d = ImageDraw.Draw(img)
    d.rectangle((0, H - 280, W, H), fill=(10, 10, 10, 220))
    d.line((W // 2, H - 280, W // 2, H), fill=(200, 200, 200), width=2)
    label(d, TITLE, 40, H - 260, font(22, True))
    for i, ln in enumerate(wrap(d, LINE, font(15), W // 2 - 80)):
        label(d, ln, 40, H - 220 + i * 24, font(15), (210, 210, 210))
    d.rectangle((40, H - 120, 180, H - 50), outline=(150, 150, 150))
    label(d, "NPC", 90, H - 95, font(12), (140, 140, 140))
    rx = W // 2 + 30
    label(d, "— ОТВЕТ —", rx, H - 260, font(11, True), (160, 160, 160))
    for i, o in enumerate(OPTS):
        d.polygon([(rx, H - 220 + i * 48), (rx + 12, H - 208 + i * 48), (rx, H - 196 + i * 48)], fill=(220, 220, 220))
        label(d, o, rx + 22, H - 216 + i * 48, font(14))
    save(img.convert("RGB"), "04-vertical-split", "04 — VERTICAL SPLIT (текст слева, ответы справа)")


# ── 05 SLIP STACK — each answer is torn slip ───────────────────────────────
def style_05():
    img = bg().convert("RGBA")
    d = ImageDraw.Draw(img)
    d.rectangle((100, H - 300, W - 100, H - 170), fill=(14, 14, 14, 230), outline=(210, 210, 210))
    label(d, TITLE, 130, H - 282, font(21, True))
    label(d, LINE, 130, H - 245, font(14), (200, 200, 200))
    for i, o in enumerate(OPTS):
        ox, oy = 120 + (i % 2) * 280, H - 155 + (i // 2) * 52
        pts = [(ox, oy), (ox + 260, oy + 4), (ox + 255, oy + 38), (ox - 5, oy + 34)]
        d.polygon(pts, fill=(200, 200, 200), outline=(160, 160, 160))
        label(d, o, ox + 14, oy + 12, font(13), (25, 25, 25))
    save(img.convert("RGB"), "05-slip-stack", "05 — SLIP STACK (каждый ответ — оторванная записка)")


# ── 06 SPOTLIGHT — vignette cone, text in light ────────────────────────────
def style_06():
    img = bg().convert("RGBA")
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.ellipse((W // 2 - 420, H - 380, W // 2 + 420, H + 60), fill=(0, 0, 0, 200))
    img = Image.alpha_composite(img, overlay)
    d = ImageDraw.Draw(img)
    label(d, TITLE, W // 2 - 200, H - 270, font(24, True))
    for i, ln in enumerate(wrap(d, LINE, font(15), 500)):
        label(d, ln, W // 2 - 240, H - 225 + i * 24, font(15))
    for i, o in enumerate(OPTS):
        f14 = font(14)
        tw = d.textlength(o, font=f14)
        x = W // 2 - tw // 2
        d.line((x - 20, H - 165 + i * 36, x - 8, H - 165 + i * 36), fill=(220, 220, 220), width=2)
        label(d, o, x, H - 172 + i * 36, f14)
    save(img.convert("RGB"), "06-spotlight", "06 — SPOTLIGHT (текст только в круге света)")


# ── 07 ASCII TERMINAL — box characters frame ─────────────────────────────────
def style_07():
    img = bg().convert("RGBA")
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = 70, H - 295, W - 70, H - 40
    mf = font(14)
    top = "╔" + "═" * 72 + "╗"
    mid = "║" + " " * 72 + "║"
    bot = "╚" + "═" * 72 + "╝"
    for i, row in enumerate([top] + [mid] * 14 + [bot]):
        label(d, row, x0, y0 + i * 16, mf, (220, 220, 220))
    label(d, TITLE, x0 + 20, y0 + 24, font(18, True))
    label(d, LINE, x0 + 20, y0 + 54, font(13), (190, 190, 190))
    for i, o in enumerate(OPTS):
        label(d, f"> {o}", x0 + 24, y0 + 100 + i * 22, font(13))
    label(d, "_", x0 + 20, y0 + 195, font(14), (220, 220, 220))
    save(img.convert("RGB"), "07-ascii-terminal", "07 — ASCII TERMINAL (рамка из символов ╔═╗)")


# ── 08 DIAGONAL CUT — asymmetric slanted panel ─────────────────────────────
def style_08():
    img = bg().convert("RGBA")
    d = ImageDraw.Draw(img)
    pts = [(0, H - 120), (W, H - 260), (W, H), (0, H)]
    d.polygon(pts, fill=(12, 12, 12, 235))
    d.line([(0, H - 120), (W, H - 260)], fill=(220, 220, 220), width=2)
    label(d, TITLE, 50, H - 235, font(22, True))
    label(d, LINE, 50, H - 200, font(14), (205, 205, 205))
    for i, o in enumerate(OPTS):
        opt_btn(d, 60 + i * 18, H - 145 + i * 8, 280, 30, o, font(12))
    save(img.convert("RGB"), "08-diagonal-cut", "08 — DIAGONAL CUT (скошенная асимметричная панель)")


# ── 09 NEWSPAPER — masthead + classified ads as options ─────────────────────
def style_09():
    img = bg().convert("RGBA")
    d = ImageDraw.Draw(img)
    d.rectangle((60, H - 320, W - 60, H - 30), fill=(18, 18, 18, 240), outline=(210, 210, 210))
    d.line((60, H - 275, W - 60, H - 275), fill=(200, 200, 200), width=2)
    d.line((W // 2, H - 275, W // 2, H - 30), fill=(100, 100, 100))
    label(d, "CHERNOGORKA TRIBUNE", 90, H - 308, font(10), (150, 150, 150))
    label(d, TITLE, 90, H - 295, font(26, True))
    for i, ln in enumerate(wrap(d, LINE, font(14), W // 2 - 100)):
        label(d, ln, 90, H - 250 + i * 22, font(14))
    label(d, "ОБЪЯВЛЕНИЯ", W // 2 + 30, H - 258, font(12, True), (180, 180, 180))
    for i, o in enumerate(OPTS):
        label(d, f"• {o}", W // 2 + 30, H - 230 + i * 36, font(13))
    save(img.convert("RGB"), "09-newspaper", "09 — NEWSPAPER (газетная вёрстка, объявления справа)")


# ── 10 DOG TAGS — options hang as metal tags ───────────────────────────────
def style_10():
    img = bg().convert("RGBA")
    d = ImageDraw.Draw(img)
    d.rectangle((0, H - 250, W, H), fill=(10, 10, 10, 225))
    d.rectangle((0, H - 250, W, H - 215), fill=(30, 30, 30))
    label(d, TITLE, 40, H - 242, font(20, True))
    label(d, "✕", W - 50, H - 242, font(18), (200, 200, 200))
    label(d, LINE, 40, H - 195, font(15), (210, 210, 210))
    start_x = 120
    gap = (W - 240) // 4
    for i, o in enumerate(OPTS):
        cx = start_x + i * gap + gap // 2
        d.line((cx, H - 155, cx, H - 120), fill=(180, 180, 180), width=2)
        d.polygon([(cx - 55, H - 115), (cx + 55, H - 115), (cx + 48, H - 70), (cx - 48, H - 70)], fill=(195, 195, 195), outline=(150, 150, 150))
        d.ellipse((cx - 8, H - 112, cx + 8, H - 96), fill=(40, 40, 40))
        short = o if len(o) < 14 else o[:12] + "…"
        f11 = font(11)
        tw = d.textlength(short, font=f11)
        label(d, short, cx - tw // 2, H - 98, f11, (25, 25, 25))
    save(img.convert("RGB"), "10-dog-tags", "10 — DOG TAGS (варианты ответа как жетоны на цепочке)")


def contact_sheet():
    files = sorted(OUT.glob("*.png"))
    if not files:
        return
    cols, rows = 2, 5
    thumb_w, thumb_h = 640, 378
    sheet = Image.new("RGB", (cols * thumb_w + 30, rows * thumb_h + 80), (20, 20, 20))
    for i, p in enumerate(files[:10]):
        if p.name.startswith("00-"):
            continue
        t = Image.open(p)
        t.thumbnail((thumb_w - 10, thumb_h - 10))
        c, r = i % cols, i // cols
        x = 10 + c * thumb_w + (thumb_w - t.width) // 2
        y = 40 + r * thumb_h + (thumb_h - t.height) // 2
        sheet.paste(t, (x, y))
    sheet.save(OUT / "00-all-10-styles.png", "PNG", optimize=True)
    print(OUT / "00-all-10-styles.png")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    style_01()
    style_02()
    style_03()
    style_04()
    style_05()
    style_06()
    style_07()
    style_08()
    style_09()
    style_10()
    contact_sheet()


if __name__ == "__main__":
    main()
