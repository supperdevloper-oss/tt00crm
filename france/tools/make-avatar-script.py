#!/usr/bin/env python3
"""Avatar « script » pour Friteuse Facile.

Même langage visuel que la référence fournie : un mot en script, une icône
verticale au centre, un second mot en script. Le nom est le nôtre et l'icône
est une friteuse à air (pas des couverts) : aucun élément de la marque d'un
concurrent n'est repris.

Sortie :
  assets/img/brand/avatar-script-blanc.png   1000×1000, noir sur blanc
  assets/img/brand/avatar-script-creme.png   1000×1000, noir sur crème
"""
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "assets", "img", "brand")

FONT = os.path.join(ROOT, "assets", "fonts", "KaushanScript-Regular.ttf")

BLACK = (10, 10, 10)
WHITE = (255, 255, 255)
CREAM = (246, 242, 233)


def airfryer(d, cx, cy, h, bg):
    """Silhouette de friteuse à air, centrée sur (cx, cy), hauteur h.
    Les détails sont dessinés avec la couleur du fond pour « percer » la
    silhouette : c'est ce qui la rend lisible même à 48 px."""
    w = h * 0.78
    x0, x1 = cx - w / 2, cx + w / 2
    y0, y1 = cy - h / 2, cy + h / 2
    r = w * 0.30

    # poignée supérieure
    hw, hh = w * 0.30, h * 0.075
    d.rounded_rectangle(
        [cx - hw / 2, y0 - hh * 0.75, cx + hw / 2, y0 + hh * 1.15],
        radius=hh * 0.7, fill=BLACK,
    )

    # corps
    d.rounded_rectangle([x0, y0, x1, y1], radius=r, fill=BLACK)

    # rainure du tiroir : trait couleur fond
    gy = y1 - h * 0.34
    gw = max(2, int(h * 0.030))
    d.rounded_rectangle(
        [x0 + w * 0.07, gy, x1 - w * 0.07, gy + gw],
        radius=gw / 2, fill=bg,
    )

    # poignée du tiroir (petite barre, sous la rainure)
    pw, ph = w * 0.30, max(2, int(h * 0.030))
    d.rounded_rectangle(
        [cx - pw / 2, gy + h * 0.085, cx + pw / 2, gy + h * 0.085 + ph],
        radius=ph / 2, fill=bg,
    )

    # écran / bouton en haut du corps
    sw, sh = w * 0.26, h * 0.055
    d.rounded_rectangle(
        [cx - sw / 2, y0 + h * 0.105, cx + sw / 2, y0 + h * 0.105 + sh],
        radius=sh / 2, fill=bg,
    )


def build(size, bg):
    S = size
    img = Image.new("RGB", (S, S), bg)
    d = ImageDraw.Draw(img)

    word_a, word_b = "Friteuse", "Facile"
    base = 100
    f = ImageFont.truetype(FONT, base)

    # largeur des mots à la taille de base
    wa = d.textlength(word_a, font=f)
    wb = d.textlength(word_b, font=f)

    HEAD = 0.900 * S          # largeur totale visée
    ico_w_at_base = base * 0.40
    gap_at_base = base * 0.33
    total_base = wa + gap_at_base + ico_w_at_base + gap_at_base + wb

    k = HEAD / total_base
    fs = int(base * k)
    f = ImageFont.truetype(FONT, fs)
    wa = d.textlength(word_a, font=f)
    wb = d.textlength(word_b, font=f)
    ico_w = fs * 0.40
    gap = fs * 0.33

    total = wa + gap + ico_w + gap + wb
    left = (S - total) / 2

    # la ligne de base visuelle : centre optique du mot (pas de la boîte)
    bb = d.textbbox((0, 0), "x", font=f)
    opt_cy = S * 0.5 - (bb[1] + bb[3]) / 2 + fs * 0.06

    d.text((left, opt_cy), word_a, font=f, fill=BLACK, anchor="lm")
    cx = left + wa + gap + ico_w / 2
    airfryer(d, cx, opt_cy + fs * 0.02, h=fs * 1.16, bg=bg)
    d.text((left + wa + gap + ico_w + gap, opt_cy), word_b, font=f, fill=BLACK, anchor="lm")

    return img



def build_compact(size, bg):
    """Variante carrée : icône au-dessus, mot en dessous. Reste lisible à 48 px,
    contrairement à la version en une seule ligne."""
    S = size
    img = Image.new("RGB", (S, S), bg)
    d = ImageDraw.Draw(img)

    word = "Friteuse"
    base = 100
    f = ImageFont.truetype(FONT, base)
    k = (0.58 * S) / d.textlength(word, font=f)
    fs = int(base * k)
    f = ImageFont.truetype(FONT, fs)

    ico_h = S * 0.255
    ico_cy = S * 0.325

    bb = d.textbbox((0, 0), "x", font=f)
    opt_cy = S * 0.715 - (bb[1] + bb[3]) / 2

    airfryer(d, S / 2, ico_cy, h=ico_h, bg=bg)
    d.text((S / 2, opt_cy), word, font=f, fill=BLACK, anchor="mm")
    return img


def main():
    os.makedirs(OUT, exist_ok=True)
    jobs = [
        ("avatar-script-blanc.png", WHITE, build),
        ("avatar-script-creme.png", CREAM, build),
        ("avatar-script-compact-blanc.png", WHITE, build_compact),
        ("avatar-script-compact-creme.png", CREAM, build_compact),
    ]
    for name, bg, fn in jobs:
        p = os.path.join(OUT, name)
        fn(1000, bg).save(p, "PNG", optimize=True)
        print("%-46s %6.1f Ko" % (name, os.path.getsize(p) / 1024))


if __name__ == "__main__":
    main()
