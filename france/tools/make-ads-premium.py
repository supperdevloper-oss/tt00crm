#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Générateur des créatifs Meta Ads « style RecipeTour » mais premium.

Sortie : 1080 x 1350 (4:5), rendu à 2x puis réduit (bords nets).

Charte Friteuse Facile :
    vert      #0F3D2A
    vert nuit #0B2A1D
    crème     #F6F2E9
    orange    #D95A1E
    orange cl #F0A04B
    encre     #1B1A17

Creative = 1 fichier PNG. Aucun emoji, aucune photo de personne, aucun faux avis.
"""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(ROOT, "assets", "img")
FONTS = os.path.join(ROOT, "assets", "fonts")
OUT = os.path.join(ROOT, "assets", "creatives-nouvelles")

SCALE = 2
W, H = 1080, 1350

GREEN = (15, 61, 42)
GREEN_NIGHT = (11, 42, 29)
CREAM = (246, 242, 233)
ORANGE = (217, 90, 30)
ORANGE_LT = (240, 160, 75)
INK = (27, 26, 23)
WHITE = (255, 255, 255)
MUTED = (111, 104, 92)

F_BOLD = os.path.join(FONTS, "Oswald-Bold.ttf")
F_MED = os.path.join(FONTS, "Oswald-Medium.ttf")
F_REG = os.path.join(FONTS, "Oswald-Regular.ttf")
F_SERIF_I = os.path.join(FONTS, "Playfair-Italic.ttf")
F_SERIF_BI = os.path.join(FONTS, "Playfair-BoldItalic.ttf")
F_SANS_B = os.path.join(FONTS, "Lato-Bold.ttf")
F_SANS = os.path.join(FONTS, "Lato-Regular.ttf")


def font(path, size):
    return ImageFont.truetype(path, int(size * SCALE))


def tracked(d, xy, text, f, fill, tracking=0.0, anchor="la"):
    """Texte avec interlettrage, comme une eyebrow de magazine."""
    x, y = xy
    tr = tracking * SCALE
    widths = [d.textlength(c, font=f) for c in text]
    total = sum(widths) + tr * (len(text) - 1)
    if anchor[0] == "m":
        x -= total / 2
    for c, w in zip(text, widths):
        d.text((x, y), c, font=f, fill=fill, anchor="l" + anchor[1])
        x += w + tr
    return total


def fitted(d, text, path, max_w, start, min_size=10):
    """Réduit la taille jusqu'à tenir dans max_w."""
    s = start
    while s > min_size:
        f = font(path, s)
        if d.textlength(text, font=f) <= max_w * SCALE:
            return f
        s -= 2
    return font(path, min_size)


def soft_shadow(base, box, radius=40, blur=45, opacity=95, offset=(0, 26)):
    """Ombre portée douce derrière un rectangle."""
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    ds = ImageDraw.Draw(layer)
    x0, y0, x1, y1 = [v * SCALE for v in box]
    dx, dy = offset[0] * SCALE, offset[1] * SCALE
    ds.rounded_rectangle(
        [x0 + dx, y0 + dy, x1 + dx, y1 + dy],
        radius=radius * SCALE, fill=(20, 30, 24, opacity),
    )
    layer = layer.filter(ImageFilter.GaussianBlur(blur * SCALE / 3))
    base.alpha_composite(layer)


def paste_shadowed(base, im, center_x, top, width, shadow=True):
    """Colle une image RGBA centrée horizontalement, avec ombre au sol."""
    w = int(width * SCALE)
    h = int(im.height * w / im.width)
    im = im.resize((w, h), Image.LANCZOS)
    x = int(center_x * SCALE - w / 2)
    y = int(top * SCALE)
    if shadow:
        sh = Image.new("RGBA", base.size, (0, 0, 0, 0))
        ds = ImageDraw.Draw(sh)
        ds.ellipse(
            [x + w * 0.10, y + h * 0.94, x + w * 0.90, y + h * 1.03],
            fill=(15, 30, 22, 105),
        )
        sh = sh.filter(ImageFilter.GaussianBlur(22 * SCALE / 2))
        base.alpha_composite(sh)
    base.alpha_composite(im, (x, y))
    return (x / SCALE, y / SCALE, w / SCALE, h / SCALE)


def price_disc(base, cx, cy, r, price="2,97 €", old="85 €", label="AUJOURD'HUI"):
    """Pastille de prix : le déclencheur qui fait cliquer sur ce marché."""
    d = ImageDraw.Draw(base)
    # ombre
    sh = Image.new("RGBA", base.size, (0, 0, 0, 0))
    ds = ImageDraw.Draw(sh)
    ds.ellipse([(cx - r) * SCALE, (cy - r + 14) * SCALE, (cx + r) * SCALE, (cy + r + 14) * SCALE],
               fill=(120, 40, 10, 110))
    sh = sh.filter(ImageFilter.GaussianBlur(18 * SCALE / 2))
    base.alpha_composite(sh)

    d.ellipse([(cx - r) * SCALE, (cy - r) * SCALE, (cx + r) * SCALE, (cy + r) * SCALE],
              fill=ORANGE)
    # liseré intérieur
    d.ellipse([(cx - r + 7) * SCALE, (cy - r + 7) * SCALE, (cx + r - 7) * SCALE, (cy + r - 7) * SCALE],
              outline=ORANGE_LT, width=int(2 * SCALE))

    f_lab = font(F_MED, r * 0.175)
    tracked(d, (cx * SCALE, (cy - r * 0.56) * SCALE), label, f_lab, (255, 226, 205),
            tracking=0.11, anchor="mm")

    f_old = font(F_MED, r * 0.24)
    ow = d.textlength(old, font=f_old)
    oy = (cy - r * 0.18) * SCALE
    d.text((cx * SCALE - ow / 2, oy), old, font=f_old, fill=(255, 210, 185), anchor="lm")
    d.line([(cx * SCALE - ow / 2 - 3, oy + 1), (cx * SCALE + ow / 2 + 3, oy + 1)],
           fill=(255, 210, 185), width=max(2, int(r * 0.022 * SCALE)))

    f_price = font(F_BOLD, r * 0.50)
    d.text((cx * SCALE, (cy + r * 0.20) * SCALE), price, font=f_price, fill=WHITE, anchor="mm")

    f_note = font(F_MED, r * 0.15)
    tracked(d, (cx * SCALE, (cy + r * 0.62) * SCALE), "PAIEMENT UNIQUE", f_note,
            (255, 226, 205), tracking=0.08, anchor="mm")


def chip(d, cx, cy, text, f, fg=GREEN, bg=(232, 240, 233), padx=26, h=52, radius=26):
    w = d.textlength(text, font=f) / SCALE + padx * 2
    d.rounded_rectangle(
        [(cx - w / 2) * SCALE, (cy - h / 2) * SCALE, (cx + w / 2) * SCALE, (cy + h / 2) * SCALE],
        radius=radius * SCALE, fill=bg,
    )
    d.text((cx * SCALE, cy * SCALE), text, font=f, fill=fg, anchor="mm")
    return w


# --------------------------------------------------------------------------- 1
def creative_book_badge():
    """Le format qui vend : couverture + pastille de prix. Fond crème."""
    base = Image.new("RGBA", (W * SCALE, H * SCALE), CREAM + (255,))
    d = ImageDraw.Draw(base)

    # filet supérieur
    d.rectangle([0, 0, W * SCALE, 12 * SCALE], fill=GREEN)

    # eyebrow
    f_eb = font(F_MED, 25)
    tracked(d, (W / 2 * SCALE, 58 * SCALE), "LE GUIDE PRATIQUE · ÉDITION 2026", f_eb,
            ORANGE, tracking=0.16, anchor="ma")

    # titre
    f_big = font(F_BOLD, 128)
    d.text((W / 2 * SCALE, 158 * SCALE), "365 RECETTES", font=f_big, fill=GREEN, anchor="ma")

    f_sub = font(F_SERIF_BI, 54)
    d.text((W / 2 * SCALE, 300 * SCALE), "pour votre friteuse à air", font=f_sub, fill=INK, anchor="ma")

    # trait
    d.rectangle([(W / 2 - 60) * SCALE, 372 * SCALE, (W / 2 + 60) * SCALE, 377 * SCALE], fill=ORANGE)

    # livre
    book = Image.open(os.path.join(IMG, "book", "mockup-livre@520.png")).convert("RGBA")
    paste_shadowed(base, book, W / 2, 415, 520)

    # pastille de prix
    price_disc(base, 812, 905, 148)

    # bénéfices
    f_b = font(F_SANS_B, 27)
    lines = ["146 pages mises en page",
             "42 aliments : temps & températures",
             "3 bonus offerts (valeur 47 €)"]
    gap = 18
    y = 1130
    for t in lines:
        tw = d.textlength(t, font=f_b) / SCALE
        bw = 10
        total = bw + gap + tw
        x = (W - total) / 2
        d.ellipse([x * SCALE, (y - bw / 2) * SCALE,
                   (x + bw) * SCALE, (y + bw / 2) * SCALE], fill=ORANGE)
        d.text(((x + bw + gap) * SCALE, y * SCALE), t, font=f_b, fill=INK, anchor="lm")
        y += 46

    # barre CTA
    d.rectangle([0, 1282 * SCALE, W * SCALE, H * SCALE], fill=GREEN)
    f_cta = font(F_MED, 27)
    tracked(d, (W / 2 * SCALE, 1316 * SCALE), "PDF IMMÉDIAT · GARANTIE 30 JOURS", f_cta,
            (232, 240, 233), tracking=0.10, anchor="mm")

    return base


# --------------------------------------------------------------------------- 2
def creative_value_stack():
    """Décomposition de la valeur : 85 € barré → 2,97 €."""
    base = Image.new("RGBA", (W * SCALE, H * SCALE), GREEN + (255,))
    d = ImageDraw.Draw(base)

    # halo
    halo = Image.new("RGBA", base.size, (0, 0, 0, 0))
    dh = ImageDraw.Draw(halo)
    dh.ellipse([-300 * SCALE, -380 * SCALE, (W + 300) * SCALE, 700 * SCALE], fill=(20, 75, 52, 255))
    halo = halo.filter(ImageFilter.GaussianBlur(60 * SCALE / 2))
    base.alpha_composite(halo)
    d = ImageDraw.Draw(base)

    f_eb = font(F_MED, 25)
    tracked(d, (W / 2 * SCALE, 62 * SCALE), "CE QUE VOUS RECEVEZ", f_eb, ORANGE_LT,
            tracking=0.18, anchor="ma")

    f_h = font(F_BOLD, 96)
    d.text((W / 2 * SCALE, 128 * SCALE), "TOUT INCLUS", font=f_h, fill=CREAM, anchor="ma")

    rows = [
        ("Guide 365 recettes — 146 pages", "38 €"),
        ("Bonus 1 — Tableau temps & températures", "15 €"),
        ("Bonus 2 — 4 semaines de menus", "15 €"),
        ("Bonus 3 — 50 desserts à la friteuse", "17 €"),
    ]
    # les lignes sont dessinées sur un calque séparé : dessiner un fill
    # semi-transparent directement sur une image RGBA remplace l'alpha au
    # lieu de le mélanger, et le texte devenait invisible.
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    do = ImageDraw.Draw(overlay)
    f_r = font(F_SANS, 27)
    f_p = font(F_SANS_B, 31)
    y = 292
    positions = []
    for label, val in rows:
        do.rounded_rectangle(
            [110 * SCALE, (y - 32) * SCALE, 970 * SCALE, (y + 32) * SCALE],
            radius=16 * SCALE, fill=(255, 255, 255, 26),
        )
        positions.append(y)
        y += 86
    base.alpha_composite(overlay)
    d = ImageDraw.Draw(base)
    for (label, val), yy in zip(rows, positions):
        d.text((146 * SCALE, yy * SCALE), label, font=f_r, fill=CREAM, anchor="lm")
        d.text((934 * SCALE, yy * SCALE), val, font=f_p, fill=ORANGE_LT, anchor="rm")

    # total barré
    f_tl = font(F_MED, 40)
    tw = d.textlength("Valeur totale", font=f_tl)
    d.text((110 * SCALE, 686 * SCALE), "Valeur totale", font=f_tl, fill=(169, 195, 180), anchor="lm")
    f_old = font(F_BOLD, 52)
    ox = 110 * SCALE + tw + 24 * SCALE
    ow = d.textlength("85 €", font=f_old)
    d.text((ox, 686 * SCALE), "85 €", font=f_old, fill=(255, 170, 140), anchor="lm")
    d.line([(ox - 4 * SCALE, 687 * SCALE), (ox + ow + 4 * SCALE, 687 * SCALE)],
           fill=(255, 170, 140), width=int(4 * SCALE))

    # prix géant
    d.text((W / 2 * SCALE, 812 * SCALE), "2,97 €", font=font(F_BOLD, 168), fill=CREAM, anchor="mm")
    f_n = font(F_SANS_B, 27)
    d.text((W / 2 * SCALE, 910 * SCALE), "aujourd'hui · paiement unique · aucun abonnement",
           font=f_n, fill=(200, 220, 209), anchor="mm")

    # livres en bas
    book = Image.open(os.path.join(IMG, "book", "mockup-livre@520.png")).convert("RGBA")
    h_b = 235
    w_b = int(book.width * h_b / book.height)
    book = book.resize((int(w_b * SCALE), int(h_b * SCALE)), Image.LANCZOS)
    base.alpha_composite(book, (int((W / 2 - w_b / 2) * SCALE), int(985 * SCALE)))

    d.rectangle([0, 1282 * SCALE, W * SCALE, H * SCALE], fill=(8, 32, 22))
    f_cta = font(F_MED, 27)
    tracked(d, (W / 2 * SCALE, 1316 * SCALE), "TÉLÉCHARGEMENT IMMÉDIAT · 30 JOURS POUR CHANGER D'AVIS",
            f_cta, (232, 240, 233), tracking=0.07, anchor="mm")

    return base


# --------------------------------------------------------------------------- 3
def creative_photo_badge():
    """Photo plein cadre + voile sombre + promesse + pastille."""
    base = Image.new("RGBA", (W * SCALE, H * SCALE), INK + (255,))

    photo = Image.open(os.path.join(IMG, "dish-poulet.jpg")).convert("RGB")
    # recadrage 4:5 centré
    tw, th = photo.width, int(photo.width * H / W)
    if th > photo.height:
        th = photo.height
        tw = int(photo.height * W / H)
    left = (photo.width - tw) // 2
    top = (photo.height - th) // 2
    photo = photo.crop((left, top, left + tw, top + th)).resize(
        (W * SCALE, H * SCALE), Image.LANCZOS)
    base.alpha_composite(photo.convert("RGBA"))

    # voile : dégradé du bas
    veil = Image.new("RGBA", (W * SCALE, H * SCALE), (0, 0, 0, 0))
    dv = ImageDraw.Draw(veil)
    for i in range(H * SCALE):
        t = i / (H * SCALE)
        a = int(235 * max(0.0, (t - 0.30) / 0.70) ** 1.25)
        dv.line([(0, i), (W * SCALE, i)], fill=(8, 26, 18, a))
    base.alpha_composite(veil)

    d = ImageDraw.Draw(base)

    # badge haut : cadre fin, texte centré proprement
    f_eb = font(F_MED, 23)
    label = "SANS HUILE  ·  SANS FOUR"
    lw = d.textlength(label, font=f_eb) / SCALE
    cy_b = 96
    d.rounded_rectangle(
        [(W / 2 - lw / 2 - 30) * SCALE, (cy_b - 25) * SCALE,
         (W / 2 + lw / 2 + 30) * SCALE, (cy_b + 25) * SCALE],
        radius=6 * SCALE, outline=(255, 255, 255, 120), width=int(2 * SCALE),
    )
    d.text((W / 2 * SCALE, cy_b * SCALE), label, font=f_eb, fill=CREAM, anchor="mm")

    # titre bas
    f_h1 = font(F_BOLD, 104)
    d.text((70 * SCALE, 880 * SCALE), "CROUSTILLANT", font=f_h1, fill=CREAM, anchor="la")
    d.text((70 * SCALE, 985 * SCALE), "DEHORS.", font=f_h1, fill=ORANGE_LT, anchor="la")
    f_h2 = font(F_SERIF_BI, 60)
    d.text((70 * SCALE, 1105 * SCALE), "Juteux dedans.", font=f_h2, fill=CREAM, anchor="la")

    f_p = font(F_SANS, 30)
    d.text((70 * SCALE, 1180 * SCALE), "365 recettes, temps et températures exacts.",
           font=f_p, fill=(214, 226, 216), anchor="la")

    # pastille
    price_disc(base, 855, 1010, 132, label="SEULEMENT")

    d.rectangle([0, 1282 * SCALE, W * SCALE, H * SCALE], fill=GREEN)
    f_cta = font(F_MED, 28)
    tracked(d, (W / 2 * SCALE, 1316 * SCALE), "JE VEUX LES 365 RECETTES", f_cta,
            CREAM, tracking=0.12, anchor="mm")

    return base


# --------------------------------------------------------------------------- 4
def creative_pages():
    """Preuve : les vraies pages du PDF, à plat."""
    base = Image.new("RGBA", (W * SCALE, H * SCALE), CREAM + (255,))
    d = ImageDraw.Draw(base)
    d.rectangle([0, 0, W * SCALE, 12 * SCALE], fill=GREEN)

    f_eb = font(F_MED, 25)
    tracked(d, (W / 2 * SCALE, 56 * SCALE), "À L'INTÉRIEUR DU GUIDE", f_eb, ORANGE,
            tracking=0.18, anchor="ma")

    f_h = font(F_BOLD, 76)
    d.text((W / 2 * SCALE, 112 * SCALE), "REGARDEZ AVANT", font=f_h, fill=GREEN, anchor="ma")
    d.text((W / 2 * SCALE, 200 * SCALE), "D'ACHETER", font=f_h, fill=GREEN, anchor="ma")

    # 2 pages côte à côte
    pages = ["apercu-2.jpg", "apercu-3.jpg"]
    pw = 348
    gap = 44
    total = pw * 2 + gap
    x = (W - total) / 2
    top = 322
    for i, name in enumerate(pages):
        im = Image.open(os.path.join(IMG, "book", name)).convert("RGB")
        hh = int(im.height * pw / im.width)
        box = (x + i * (pw + gap), top, x + i * (pw + gap) + pw, top + hh)
        soft_shadow(base, box, radius=10, blur=34, opacity=70, offset=(0, 18))
        card = Image.new("RGBA", base.size, (0, 0, 0, 0))
        dc = ImageDraw.Draw(card)
        dc.rounded_rectangle([box[0] * SCALE, box[1] * SCALE, box[2] * SCALE, box[3] * SCALE],
                             radius=10 * SCALE, fill=(255, 255, 255, 255))
        base.alpha_composite(card)
        im = im.resize((int(pw * SCALE), int(hh * SCALE)), Image.LANCZOS).convert("RGBA")
        base.alpha_composite(im, (int(box[0] * SCALE), int(box[1] * SCALE)))

        f_c = font(F_SANS_B, 23)
        d.text(((box[0] + pw / 2) * SCALE, (top + hh + 34) * SCALE),
               ["Fiche recette : temps, °C, étapes", "Tableau : 42 aliments"][i],
               font=f_c, fill=MUTED, anchor="mm")

    # bandeau chiffres
    y = 1068
    band = Image.new("RGBA", base.size, (0, 0, 0, 0))
    db = ImageDraw.Draw(band)
    db.rounded_rectangle([70 * SCALE, (y - 58) * SCALE, 1010 * SCALE, (y + 58) * SCALE],
                         radius=22 * SCALE, fill=(232, 240, 233, 255))
    base.alpha_composite(band)
    for i, (n, lab) in enumerate([("365", "recettes"), ("146", "pages"), ("42", "aliments"), ("3", "bonus")]):
        cx = 70 + (1010 - 70) * (i + 0.5) / 4
        d.text((cx * SCALE, (y - 14) * SCALE), n, font=font(F_BOLD, 50), fill=ORANGE, anchor="mm")
        d.text((cx * SCALE, (y + 34) * SCALE), lab, font=font(F_SANS, 22), fill=GREEN, anchor="mm")
        if i < 3:
            d.rectangle([(cx + (1010 - 70) / 4 / 2) * SCALE, (y - 34) * SCALE,
                         (cx + (1010 - 70) / 4 / 2) * SCALE, (y + 34) * SCALE],
                        fill=(210, 220, 208))

    d.rectangle([0, 1282 * SCALE, W * SCALE, H * SCALE], fill=GREEN)
    f_cta = font(F_MED, 28)
    tracked(d, (W / 2 * SCALE, 1316 * SCALE), "365 RECETTES · 2,97 € · PDF IMMÉDIAT", f_cta,
            CREAM, tracking=0.10, anchor="mm")

    return base


BUILDERS = [
    ("1-livre-badge.png", creative_book_badge),
    ("2-valeur-85-297.png", creative_value_stack),
    ("3-photo-badge.png", creative_photo_badge),
    ("4-pages-pdf.png", creative_pages),
]


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, fn in BUILDERS:
        im = fn().convert("RGB").resize((W, H), Image.LANCZOS)
        p = os.path.join(OUT, name)
        im.save(p, "PNG", optimize=True)
        print("%-24s %4dx%-4d %6.1f Ko" % (name, im.width, im.height, os.path.getsize(p) / 1024))


if __name__ == "__main__":
    main()
