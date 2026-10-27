#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Visuels de vente pour Gumroad (couverture 1280x720 + vignette 600x600).

    python3 product/tools/make-covers.py

Entrées : assets/img/book/cover-page.jpg  (page 1 du PDF, rendue)
Sorties : assets/img/book/gumroad-cover.jpg · gumroad-thumb.jpg
"""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
IMG = os.path.join(ROOT, "assets", "img")
FONTS = os.path.join(ROOT, "assets", "fonts")
BOOK = os.path.join(IMG, "book")

GREEN = (15, 61, 42)
GREEN_D = (9, 42, 29)
PAPER = (255, 253, 247)
CREAM = (246, 242, 233)
ORANGE = (217, 90, 30)
ORANGE_L = (240, 160, 75)


def font(name, size):
    return ImageFont.truetype(os.path.join(FONTS, name), size)


def tracked(d, xy, text, fnt, fill, tracking=0, anchor="la"):
    """Texte avec interlettrage (approx.)."""
    widths = [d.textlength(c, font=fnt) for c in text]
    total = sum(widths) + tracking * max(len(text) - 1, 0)
    x, y = xy
    if anchor[0] == "m":
        x -= total / 2
    elif anchor[0] == "r":
        x -= total
    for c, w in zip(text, widths):
        d.text((x, y), c, font=fnt, fill=fill, anchor="l" + anchor[1])
        x += w + tracking
    return total


def book_shadow(canvas, box, radius=14, blur=26, alpha=150):
    sh = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    x0, y0, x1, y1 = box
    ImageDraw.Draw(sh).rounded_rectangle((x0 + 10, y0 + 18, x1 + 10, y1 + 18), radius,
                                         fill=(0, 0, 0, alpha))
    canvas.alpha_composite(sh.filter(ImageFilter.GaussianBlur(blur)))


def paste_book(canvas, cover, box, radius=12):
    x0, y0, x1, y1 = box
    img = cover.resize((x1 - x0, y1 - y0), Image.LANCZOS).convert("RGB")
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, img.size[0] - 1, img.size[1] - 1), radius, fill=255)
    canvas.paste(img, (x0, y0), mask)
    d = ImageDraw.Draw(canvas)
    d.rounded_rectangle(box, radius, outline=(255, 255, 255, 120), width=3)
    # tranche
    d.rectangle((x0 - 9, y0 + 8, x0 - 1, y1 - 8), fill=(226, 219, 206))


def cover_1280():
    W, H = 1280, 720
    img = Image.new("RGBA", (W, H), GREEN)
    # halo doux (flouté, pas d'arcs visibles)
    halo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(halo).ellipse((60, -260, 1000, 760), fill=(24, 78, 54, 255))
    img.alpha_composite(halo.filter(ImageFilter.GaussianBlur(120)))
    d = ImageDraw.Draw(img)

    cover = Image.open(os.path.join(BOOK, "cover-page.jpg")).convert("RGB")
    cw = 290
    ch = int(cw * cover.size[1] / cover.size[0])
    bx, by = 96, (H - ch) // 2
    book_shadow(img, (bx, by, bx + cw, by + ch))
    paste_book(img, cover, (bx, by, bx + cw, by + ch))

    x = bx + cw + 74
    d = ImageDraw.Draw(img)
    tracked(d, (x, 150), "LE GUIDE PRATIQUE", font("Oswald-Medium.ttf", 22), ORANGE_L, 5)
    d.text((x, 186), "365 RECETTES", font=font("Oswald-Bold.ttf", 74), fill=PAPER)
    d.text((x, 268), "pour friteuse à air", font=font("Playfair-BoldItalic.ttf", 54), fill=ORANGE_L)

    d.text((x, 350), "146 pages · 9 chapitres · 3 bonus", font=font("Lato-Regular.ttf", 25),
           fill=(198, 218, 206))
    for i, t in enumerate(["Temps et températures exacts pour chaque recette",
                           "Tableau de cuisson de 42 aliments",
                           "4 semaines de menus + 50 desserts"]):
        y = 396 + i * 34
        d.ellipse((x + 2, y + 11, x + 12, y + 21), fill=ORANGE)
        d.text((x + 24, y), t, font=font("Lato-Regular.ttf", 23), fill=PAPER)

    # pastille prix
    cx, cy, r = x + 56, 596, 54
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=ORANGE)
    d.ellipse((cx - r + 6, cy - r + 6, cx + r - 6, cy + r - 6), outline=(255, 220, 190), width=3)
    d.text((cx, cy), "9 €", font=font("Oswald-Bold.ttf", 38), fill=PAPER, anchor="mm")
    d.text((x + 130, 566), "PDF téléchargeable", font=font("Lato-Bold.ttf", 22), fill=PAPER)
    d.text((x + 130, 594), "immédiatement · garantie 14 jours",
           font=font("Lato-Regular.ttf", 20), fill=(190, 212, 199))

    out = os.path.join(BOOK, "gumroad-cover.jpg")
    img.convert("RGB").save(out, "JPEG", quality=90, optimize=True, progressive=True)
    print("  ", out, f"({os.path.getsize(out)//1024} Ko)")


def thumb_600():
    S = 600
    img = Image.new("RGBA", (S, S), CREAM)
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, S, 112), fill=GREEN)
    tracked(d, (S / 2, 26), "FRITEUSE À AIR", font("Oswald-Medium.ttf", 19), ORANGE_L, 5, "ma")
    d.text((S / 2, 52), "365 RECETTES", font=font("Oswald-Bold.ttf", 33), fill=PAPER, anchor="ma")
    d.text((S / 2, 92), "146 pages · 3 bonus", font=font("Lato-Regular.ttf", 17),
           fill=(196, 216, 204), anchor="ma")

    cover = Image.open(os.path.join(BOOK, "cover-page.jpg")).convert("RGB")
    cw = 190
    ch = int(cw * cover.size[1] / cover.size[0])
    bx, by = (S - cw) // 2, 130
    book_shadow(img, (bx, by, bx + cw, by + ch), blur=16, alpha=120)
    paste_book(img, cover, (bx, by, bx + cw, by + ch), radius=8)

    d = ImageDraw.Draw(img)
    d.text((S / 2, S - 92), "9 €", font=font("Oswald-Bold.ttf", 34), fill=ORANGE, anchor="ma")
    d.text((S / 2, S - 48), "PDF · accès immédiat", font=font("Lato-Bold.ttf", 16),
           fill=GREEN, anchor="ma")

    out = os.path.join(BOOK, "gumroad-thumb.jpg")
    img.convert("RGB").save(out, "JPEG", quality=90, optimize=True, progressive=True)
    print("  ", out, f"({os.path.getsize(out)//1024} Ko)")


if __name__ == "__main__":
    cover_1280()
    thumb_600()
