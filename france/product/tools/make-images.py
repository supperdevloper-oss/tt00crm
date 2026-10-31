#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prépare les visuels du livre : recadrage + fondu vers le vert de la charte.

    python3 make-images.py

Entrées : ../assets/img/*.jpg  (photos sources)
Sorties : ../assets/img/book/*.jpg
"""
import os
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.normpath(os.path.join(HERE, "..", "..", "assets", "img"))
OUT = os.path.join(IMG, "book")

GREEN = (15, 61, 42)

# (fichier source, sortie, largeur_mm, hauteur_mm, hauteur_cm, debut_fondu)
JOBS = [
    ("hero-flatlay.jpg", "cover-hero.jpg", 210, 124, 55),
    ("dish-poulet.jpg",  "ch-01.jpg", 210, 128, 42),
    ("dish-saumon.jpg",  "ch-02.jpg", 210, 128, 42),
    ("dish-legumes.jpg", "ch-03.jpg", 210, 128, 42),
    ("dish-entrees.jpg", "ch-04.jpg", 210, 128, 42),
    ("dish-plats.jpg",   "ch-05.jpg", 210, 128, 42),
    ("dish-petitdej.jpg",  "ch-06.jpg", 210, 128, 42),
    ("dish-brownie.jpg", "ch-07.jpg", 210, 128, 42),
    ("dish-monde.jpg",   "ch-08.jpg", 210, 128, 42),
    ("dish-express.jpg", "ch-09.jpg", 210, 128, 42),
]

MM_DPI = 254  # 10 px/mm


def blend(img, start_frac, color=GREEN, power=1.9):
    """Fondu vertical progressif vers `color` à partir de start_frac."""
    w, h = img.size
    grad = Image.new("L", (1, h))
    px = grad.load()
    y0 = int(h * start_frac)
    for y in range(h):
        if y < y0:
            px[0, y] = 0
        else:
            t = (y - y0) / max(h - y0 - 1, 1)
            px[0, y] = int(255 * min(t ** power, 1.0))
    mask = grad.resize((w, h))
    solid = Image.new("RGB", (w, h), color)
    return Image.composite(solid, img.convert("RGB"), mask)


def main():
    os.makedirs(OUT, exist_ok=True)
    for src, dst, wmm, hmm, fade in JOBS:
        path = os.path.join(IMG, src)
        if not os.path.exists(path):
            print("  ! manquant :", src)
            continue
        target = (int(wmm / 25.4 * MM_DPI), int(hmm / 25.4 * MM_DPI))
        img = Image.open(path).convert("RGB")
        # cover crop
        sw, sh = img.size
        tr = target[0] / target[1]
        sr = sw / sh
        if sr > tr:
            nw = int(sh * tr); img = img.crop(((sw - nw) // 2, 0, (sw + nw) // 2, sh))
        else:
            nh = int(sw / tr); img = img.crop((0, max((sh - nh) // 2 - sh // 12, 0), sw, max((sh - nh) // 2 - sh // 12, 0) + nh))
        img = img.resize(target, Image.LANCZOS)
        img = blend(img, fade / 100.0)
        img = img.filter(__import__("PIL.ImageFilter", fromlist=["ImageFilter"]).UnsharpMask(radius=1.2, percent=60, threshold=3))
        out = os.path.join(OUT, dst)
        img.save(out, "JPEG", quality=88, optimize=True, progressive=True)
        print(f"  {dst:20s} {img.size[0]}x{img.size[1]}  {os.path.getsize(out)//1024} Ko")


if __name__ == "__main__":
    main()
