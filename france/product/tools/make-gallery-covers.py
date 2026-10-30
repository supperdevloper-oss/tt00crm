#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Covers de galerie Gumroad — format 1280x720, IDENTIQUE à la cover principale.

Gumroad : "You can add up to 8 covers" et "we auto-adjust the height of covers
to match the height of the first cover". Donc toutes les images doivent avoir
la MÊME HAUTEUR (720) — sinon l'affichage casse.

    python3 product/tools/make-gallery-covers.py

Sorties : assets/img/book/gallery-1..4.jpg (1280x720)
"""
import os
import pypdfium2 as pdfium
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
BOOK = os.path.join(ROOT, "assets", "img", "book")
FONTS = os.path.join(ROOT, "assets", "fonts")
PDF = os.path.join(ROOT, "product", "365-recettes-friteuse-a-air.pdf")

GREEN = (15, 61, 42)
PAPER = (255, 253, 247)
ORANGE = (217, 90, 30)
ORANGE_L = (240, 160, 75)

W, H = 1280, 720

# (page du PDF, surtitre, titre ligne 1, titre ligne 2, sous-titre)
PAGES = [
    (3,   "À L'INTÉRIEUR", "Le sommaire", "", "9 chapitres · chaque recette numérotée"),
    (9,   "À L'INTÉRIEUR", "Une fiche", "recette", "Portions · temps · °C · étapes · astuce"),
    (6,   "À L'INTÉRIEUR", "Le tableau", "des températures", "42 aliments · à imprimer"),
    (139, "À L'INTÉRIEUR", "4 semaines", "de menus", "28 dîners + la liste de courses"),
]


def font(name, size):
    return ImageFont.truetype(os.path.join(FONTS, name), size)


def tracked(d, xy, text, fnt, fill, tracking=0, anchor="la"):
    widths = [d.textlength(c, font=fnt) for c in text]
    total = sum(widths) + tracking * max(len(text) - 1, 0)
    x, y = xy
    if anchor[0] == "m":
        x -= total / 2
    for c, w in zip(text, widths):
        d.text((x, y), c, font=fnt, fill=fill, anchor="l" + anchor[1])
        x += w + tracking


def make(page, eyebrow, t1, t2, sub, out):
    img = Image.new("RGBA", (W, H), GREEN)
    halo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(halo).ellipse((420, -280, 1400, 800), fill=(24, 78, 54, 255))
    img.alpha_composite(halo.filter(ImageFilter.GaussianBlur(130)))

    # --- page du PDF, hauteur 620 ---
    doc = pdfium.PdfDocument(PDF)
    pg = doc[page - 1].render(scale=2.2).to_pil().convert("RGB")
    ph = 620
    pw = int(ph * pg.size[0] / pg.size[1])
    pg = pg.resize((pw, ph), Image.LANCZOS)

    px, py = W - pw - 96, (H - ph) // 2
    # ombre
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle((px + 12, py + 18, px + pw + 12, py + ph + 18), fill=(0, 0, 0, 150))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(26)))
    img.paste(pg, (px, py))
    d = ImageDraw.Draw(img)
    d.rectangle((px, py, px + pw, py + ph), outline=(255, 255, 255, 90), width=2)

    # --- texte à gauche ---
    x = 96
    tracked(d, (x, 214), eyebrow, font("Oswald-Medium.ttf", 20), ORANGE_L, 5)
    y = 250
    d.text((x, y), t1, font=font("Oswald-Bold.ttf", 62), fill=PAPER)
    y += 66
    if t2:
        d.text((x, y), t2, font=font("Playfair-BoldItalic.ttf", 52), fill=ORANGE_L)
        y += 68
    else:
        y += 6
    d.text((x, y + 10), sub, font=font("Lato-Regular.ttf", 21), fill=(196, 216, 204))

    d.rectangle((x, y + 56, x + 46, y + 60), fill=ORANGE)

    img.convert("RGB").save(out, "JPEG", quality=90, optimize=True, progressive=True)
    print(f"  {os.path.basename(out):22s} {W}x{H}  {os.path.getsize(out)//1024} Ko")


if __name__ == "__main__":
    for i, (p, eb, t1, t2, sub) in enumerate(PAGES, 1):
        make(p, eb, t1, t2, sub, os.path.join(BOOK, f"gallery-{i}.jpg"))
