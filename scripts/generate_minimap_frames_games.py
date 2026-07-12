#!/usr/bin/env python3
"""10 minimap frame skins inspired by different survival/tactical games."""

from __future__ import annotations

import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

import generate_minimap_frames as core

OUT = Path("/workspace/minimap-frames/games")
GDIR = OUT


def paint_dayz(base: Image.Image, seed: int) -> None:
    """DayZ — Garmin Foretrex, olive drab, rubber bumpers."""
    d = ImageDraw.Draw(base)
    cw, ch = base.size[0] // core.RENDER_SCALE, base.size[1] // core.RENDER_SCALE
    shell = core.sbox((16, 14, cw - 16, ch - 12))
    core.draw_metro_shell(d, shell, (52, 58, 42, 255), (38, 44, 30, 255), (22, 26, 18, 255))
    for bx in (4, cw - 26):
        core.rr(d, core.sbox((bx, ch // 2 - 78, bx + 22, ch // 2 + 78)), 8, (34, 38, 28, 255))
    d.text((shell[0] + core.sc(14), shell[1] + core.sc(8)), "GARMIN FORETREX", font=core.load_font(8, True), fill=(186, 192, 158, 255))
    d.ellipse((shell[2] - core.sc(36), shell[1] + core.sc(10), shell[2] - core.sc(24), shell[1] + core.sc(22)), fill=(72, 168, 64, 255))


def paint_tarkov(base: Image.Image, seed: int) -> None:
    """Escape from Tarkov — dark tan tactical, stencil feel."""
    d = ImageDraw.Draw(base)
    cw, ch = base.size[0] // core.RENDER_SCALE, base.size[1] // core.RENDER_SCALE
    shell = core.sbox((10, 10, cw - 10, ch - 8))
    core.draw_metro_shell(d, shell, (48, 44, 36, 255), (32, 28, 22, 255), (24, 22, 18, 255))
    # corner brackets like Tarkov UI
    for x, y, dx, dy in ((shell[0], shell[1], 1, 1), (shell[2], shell[1], -1, 1),
                         (shell[0], shell[3], 1, -1), (shell[2], shell[3], -1, -1)):
        d.line((x, y, x + dx * core.sc(28), y), fill=(168, 132, 64, 255), width=core.sc(2))
        d.line((x, y, x, y + dy * core.sc(28)), fill=(168, 132, 64, 255), width=core.sc(2))
    d.text((shell[0] + core.sc(16), shell[1] + core.sc(8)), "ТАКТИЧЕСКАЯ КАРТА", font=core.load_font(8, True), fill=(176, 158, 118, 255))
    core.metal_tex(d, shell, seed, (40, 36, 30))


def paint_stalker(base: Image.Image, seed: int) -> None:
    """STALKER — green PDA rubber body, radiation warning stripe."""
    d = ImageDraw.Draw(base)
    cw, ch = base.size[0] // core.RENDER_SCALE, base.size[1] // core.RENDER_SCALE
    shell = core.sbox((12, 12, cw - 12, ch - 10))
    core.rr(d, shell, 10, (38, 48, 34, 255), (18, 24, 16, 255), 2)
    stripe = (shell[0], shell[1] + core.sc(6), shell[2], shell[1] + core.sc(14))
    d.rectangle(stripe, fill=(168, 148, 48, 255))
    d.text((shell[0] + core.sc(40), shell[1] + core.sc(7)), "PDA", font=core.load_font(7, True), fill=(24, 28, 18, 255))
    d.text((shell[0] + core.sc(14), shell[1] + core.sc(22)), "ZONE NAV", font=core.load_font(8, True), fill=(148, 168, 120, 255))
    # scanline bezel
    for y in range(shell[1], shell[3], core.sc(3)):
        if y % core.sc(6) == 0:
            d.line((shell[0], y, shell[2], y), fill=(0, 0, 0, 40), width=1)


def paint_pubg(base: Image.Image, seed: int) -> None:
    """PUBG — minimal dark rubber, thin white compass rail."""
    d = ImageDraw.Draw(base)
    cw, ch = base.size[0] // core.RENDER_SCALE, base.size[1] // core.RENDER_SCALE
    shell = core.sbox((14, 12, cw - 14, ch - 10))
    core.rr(d, shell, 14, (28, 30, 32, 255), (14, 15, 16, 255), 1)
    ix0, iy0, ix1, _ = core.inner_box()
    rail = core.sbox((ix0 - 2, iy0 - 20, ix1 + 2, iy0 - 2))
    d.rectangle(rail, fill=(20, 22, 24, 255), outline=(180, 182, 186, 120))
    d.text((shell[0] + core.sc(12), shell[1] + core.sc(6)), "TACTICAL MAP", font=core.load_font(7, True), fill=(190, 192, 196, 255))


def paint_arma(base: Image.Image, seed: int) -> None:
    """Arma 3 — military GPS, digital green accent, grid feel."""
    d = ImageDraw.Draw(base)
    cw, ch = base.size[0] // core.RENDER_SCALE, base.size[1] // core.RENDER_SCALE
    shell = core.sbox((8, 8, cw - 8, ch - 8))
    d.rectangle(shell, fill=(44, 50, 40, 255), outline=(68, 120, 58, 255), width=core.sc(1))
    for x in range(shell[0] + core.sc(10), shell[2], core.sc(24)):
        d.line((x, shell[1], x, shell[3]), fill=(58, 98, 48, 40), width=1)
    d.text((shell[0] + core.sc(12), shell[1] + core.sc(8)), "GPS 18X", font=core.load_font(9, True), fill=(120, 180, 88, 255))
    d.text((shell[2] - core.sc(80), shell[1] + core.sc(8)), "NATO", font=core.load_font(7, True), fill=(100, 140, 80, 255))


def paint_rust(base: Image.Image, seed: int) -> None:
    """Rust — welded scrap plates, asymmetrical."""
    d = ImageDraw.Draw(base)
    cw, ch = base.size[0] // core.RENDER_SCALE, base.size[1] // core.RENDER_SCALE
    plates = core.sbox((6, 10, cw - 4, ch - 6))
    d.polygon(core.spoly([(6, 14), (cw - 6, 8), (cw - 2, ch - 8), (4, ch - 4)]), fill=(58, 54, 48, 255), outline=(32, 28, 24, 255))
    # weld seams
    d.line(core.spoly([(20, 30), (cw - 30, 20)]), fill=(88, 80, 68, 200), width=core.sc(3))
    d.line(core.spoly([(30, ch - 20), (cw - 20, ch - 30)]), fill=(88, 80, 68, 200), width=core.sc(3))
    core.rust_splotches(d, plates, seed, 18)
    d.text((core.sc(20), core.sc(16)), "SCRAP NAV", font=core.load_font(9, True), fill=(168, 152, 120, 255))


def paint_metro(base: Image.Image, seed: int) -> None:
    """Metro — brass pocket instrument, leather edge."""
    d = ImageDraw.Draw(base)
    cw, ch = base.size[0] // core.RENDER_SCALE, base.size[1] // core.RENDER_SCALE
    shell = core.sbox((18, 16, cw - 18, ch - 12))
    core.draw_metro_shell(d, shell, (108, 88, 52, 255), (72, 58, 36, 255), (68, 54, 32, 255))
    # leather strap hint top
    d.rounded_rectangle(core.sbox((cw // 2 - 40, 4, cw // 2 + 40, 18)), 4, fill=(62, 42, 28, 255))
    d.text((shell[0] + core.sc(20), shell[1] + core.sc(10)), "METRO COMPASS", font=core.load_font(8, True), fill=(220, 200, 160, 255))


def paint_division(base: Image.Image, seed: int) -> None:
    """The Division — SHD orange accent, angular smart device."""
    d = ImageDraw.Draw(base)
    cw, ch = base.size[0] // core.RENDER_SCALE, base.size[1] // core.RENDER_SCALE
    shell = core.sbox((12, 12, cw - 12, ch - 10))
    core.rr(d, shell, 8, (36, 38, 40, 255), (18, 19, 20, 255), 2)
    # orange SHD stripe left
    d.rectangle((shell[0], shell[1] + core.sc(20), shell[0] + core.sc(6), shell[3] - core.sc(20)), fill=(212, 108, 38, 255))
    d.polygon(core.spoly([(cw - 30, 12), (cw - 8, 12), (cw - 8, 28), (cw - 18, 28)]), fill=(212, 108, 38, 255))
    d.text((shell[0] + core.sc(20), shell[1] + core.sc(10)), "SHD MAP", font=core.load_font(9, True), fill=(210, 212, 208, 255))


def paint_hunt(base: Image.Image, seed: int) -> None:
    """Hunt: Showdown — Victorian brass corners, dark leather."""
    d = ImageDraw.Draw(base)
    cw, ch = base.size[0] // core.RENDER_SCALE, base.size[1] // core.RENDER_SCALE
    shell = core.sbox((10, 14, cw - 10, ch - 10))
    core.rr(d, shell, 6, (42, 34, 28, 255), (88, 72, 44, 255), 2)
    for px, py in ((shell[0] + core.sc(16), shell[1] + core.sc(16)), (shell[2] - core.sc(16), shell[1] + core.sc(16)),
                   (shell[0] + core.sc(16), shell[3] - core.sc(16)), (shell[2] - core.sc(16), shell[3] - core.sc(16))):
        d.arc((px - core.sc(14), py - core.sc(14), px + core.sc(14), py + core.sc(14)), 0, 90, fill=(148, 118, 62, 255), width=core.sc(3))
    d.text((shell[0] + core.sc(30), shell[1] + core.sc(8)), "HUNT MAP", font=core.load_font(9, True), fill=(188, 168, 120, 255))


def paint_scum(base: Image.Image, seed: int) -> None:
    """SCUM — crude prison/survival craft, stamped metal."""
    d = ImageDraw.Draw(base)
    cw, ch = base.size[0] // core.RENDER_SCALE, base.size[1] // core.RENDER_SCALE
    shell = core.sbox((8, 10, cw - 8, ch - 8))
    d.rectangle(shell, fill=(56, 52, 46, 255), outline=(30, 28, 24, 255), width=core.sc(2))
    core.metal_tex(d, shell, seed)
    d.text((shell[0] + core.sc(14), shell[1] + core.sc(10)), "PRISONER NAV", font=core.load_font(8, True), fill=(148, 140, 120, 255))
    # barcode stamp
    for x in range(shell[0] + core.sc(14), shell[0] + core.sc(80), core.sc(4)):
        h = core.sc(random.Random(seed).randint(4, 12))
        d.line((x, shell[3] - core.sc(20), x, shell[3] - core.sc(20) + h), fill=(100, 96, 88, 255), width=core.sc(2))


GAME_PAINTERS = [
    ("game-01-dayz", "DayZ", "Garmin Foretrex olive survival", "triangle", paint_dayz, True),
    ("game-02-tarkov", "Escape from Tarkov", "Tan tactical brackets", "cross", paint_tarkov, True),
    ("game-03-stalker", "STALKER", "Green PDA radiation stripe", "strip", paint_stalker, False),
    ("game-04-pubg", "PUBG", "Minimal dark rubber rail", "notch", paint_pubg, False),
    ("game-05-arma3", "Arma 3", "Military GPS green grid", "triangle", paint_arma, False),
    ("game-06-rust", "Rust", "Welded scrap plates", "square", paint_rust, False),
    ("game-07-metro", "Metro 2033", "Brass pocket + leather", "diamond", paint_metro, True),
    ("game-08-division", "The Division", "SHD orange angular", "strip", paint_division, False),
    ("game-09-hunt", "Hunt: Showdown", "Victorian brass corners", "cross", paint_hunt, False),
    ("game-10-scum", "SCUM", "Stamped prison metal", "square", paint_scum, False),
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    saved = []
    for i, (slug, title, desc, marker, painter, metro) in enumerate(GAME_PAINTERS):
        img = core.build_frame(painter, marker, seed=200 + i * 31, metro_style=metro, dark_compass=metro)
        p = OUT / f"{slug}.png"
        img.save(p, "PNG", optimize=True)
        p4 = OUT / f"{slug}-4k.png"
        img.resize((img.width * 2, img.height * 2), Image.Resampling.LANCZOS).save(p4, "PNG", optimize=True)
        saved += [p, p4]
        print(f"{slug}: {title} — {desc}")

    import zipfile
    zp = OUT / "minimap-frames-games-10.zip"
    with zipfile.ZipFile(zp, "w") as zf:
        for p in saved:
            zf.write(p, p.name)
    print(f"Saved {zp}")


if __name__ == "__main__":
    main()
