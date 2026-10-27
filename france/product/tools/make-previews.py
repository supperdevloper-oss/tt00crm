#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aperçus pour la fiche Gumroad (galerie) : 3 pages du livre rendues proprement.

    python3 product/tools/make-previews.py

Sorties : assets/img/book/apercu-1.jpg … apercu-4.jpg  (1400 px de large)
"""
import os
import pypdfium2 as pdfium
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
BOOK = os.path.join(ROOT, "assets", "img", "book")
PDF = os.path.join(ROOT, "product", "365-recettes-friteuse-a-air.pdf")
FONTS = os.path.join(ROOT, "assets", "fonts")

CREAM = (246, 242, 233)
GREEN = (15, 61, 42)
ORANGE = (217, 90, 30)
MUTED = (111, 104, 92)

# (page du PDF en base 1, légende)
PAGES = [
    (3, "Le sommaire, avec les numéros de page"),
    (9, "Une fiche recette : temps, température, astuce"),
    (6, "Le tableau de cuisson de 42 aliments"),
    (139, "Les 4 semaines de menus"),
]


def font(name, size):
    return ImageFont.truetype(os.path.join(FONTS, name), size)


def main():
    doc = pdfium.PdfDocument(PDF)
    for i, (page, caption) in enumerate(PAGES, start=1):
        img = doc[page - 1].render(scale=2.4).to_pil().convert("RGB")
        w = 1400
        h = int(img.size[1] * w / img.size[0])
        img = img.resize((w, h), Image.LANCZOS)

        band = 110
        canvas = Image.new("RGB", (w, h + band), CREAM)
        canvas.paste(img, (0, 0))
        d = ImageDraw.Draw(canvas)
        d.rectangle((0, h, w, h + band), fill=CREAM)
        d.rectangle((0, h, w, h + 3), fill=GREEN)
        d.text((44, h + 34), caption, font=font("Lato-Bold.ttf", 34), fill=GREEN)
        d.text((44, h + 74), f"365 Recettes pour Friteuse à Air — page {page}",
               font=font("Lato-Regular.ttf", 22), fill=MUTED)
        d.text((w - 44, h + 56), "9 €", font=font("Oswald-Bold.ttf", 34), fill=ORANGE, anchor="rm")

        out = os.path.join(BOOK, f"apercu-{i}.jpg")
        canvas.save(out, "JPEG", quality=88, optimize=True, progressive=True)
        print("  ", out, f"({os.path.getsize(out)//1024} Ko)")


if __name__ == "__main__":
    main()
