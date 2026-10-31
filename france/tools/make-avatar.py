#!/usr/bin/env python3
"""Génère l'avatar du profil Gumroad « Friteuse Facile ».

Sortie :
  assets/img/brand/avatar-500.png   (500×500, PNG, fond plein — recommandé Gumroad)
  assets/img/brand/avatar-1000.png  (1000×1000, pour un usage retina / réseaux)

Contrainte : l'avatar Gumroad est affiché dans un cercle. Tout le contenu
reste donc dans le cercle inscrit (~70 % du côté) pour ne jamais être rogné.
"""
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "assets", "img", "brand")

GREEN = (15, 61, 42)        # --green
GREEN_DK = (11, 42, 29)     # --green (footer)
CREAM = (246, 242, 233)     # --cream
ORANGE = (217, 90, 30)      # --orange
ORANGE_LT = (240, 160, 75)  # --orange-lt

F_OSWALD = os.path.join(ROOT, "assets", "fonts", "Oswald-Bold.ttf")
F_MED = os.path.join(ROOT, "assets", "fonts", "Oswald-Medium.ttf")


def build(size):
    S = size
    img = Image.new("RGB", (S, S), GREEN)
    d = ImageDraw.Draw(img)

    # léger dégradé vertical pour éviter un aplat trop plat
    for y in range(S):
        t = y / (S - 1)
        c = tuple(int(GREEN[i] + (GREEN_DK[i] - GREEN[i]) * t * 0.85) for i in range(3))
        d.line([(0, y), (S, y)], fill=c)

    # anneau orange fin, rentré pour rester visible dans le cercle de Gumroad
    pad = int(S * 0.075)
    d.ellipse([pad, pad, S - pad, S - pad], outline=ORANGE, width=max(2, int(S * 0.008)))

    # « 365 » — le repère de marque déjà utilisé sur le site
    f365 = ImageFont.truetype(F_OSWALD, int(S * 0.300))
    txt = "365"
    bb = d.textbbox((0, 0), txt, font=f365)
    w, h = bb[2] - bb[0], bb[3] - bb[1]
    x = (S - w) / 2 - bb[0]
    y = S * 0.360 - h / 2 - bb[1]
    d.text((x, y), txt, font=f365, fill=CREAM)

    # filet orange sous le 365
    lw = int(S * 0.150)
    ly = int(S * 0.545)
    d.rectangle([(S - lw) // 2, ly, (S + lw) // 2, ly + max(2, int(S * 0.012))], fill=ORANGE_LT)

    # « RECETTES » espacé
    fsm = ImageFont.truetype(F_MED, int(S * 0.076))
    word = "RECETTES"
    tracking = S * 0.012
    widths = [d.textlength(ch, font=fsm) for ch in word]
    total = sum(widths) + tracking * (len(word) - 1)
    cx = (S - total) / 2
    ty = S * 0.600
    for ch, cw in zip(word, widths):
        d.text((cx, ty), ch, font=fsm, fill=ORANGE_LT)
        cx += cw + tracking

    # « FRITEUSE FACILE » tout petit, pour les affichages en grand
    fx = ImageFont.truetype(F_MED, int(S * 0.040))
    t2 = "FRITEUSE FACILE"
    tr2 = S * 0.009
    w2 = [d.textlength(c, font=fx) for c in t2]
    tot2 = sum(w2) + tr2 * (len(t2) - 1)
    cx2 = (S - tot2) / 2
    for ch, cw in zip(t2, w2):
        d.text((cx2, S * 0.688), ch, font=fx, fill=(169, 195, 180))
        cx2 += cw + tr2

    return img


def main():
    os.makedirs(OUT, exist_ok=True)
    for size in (500, 1000):
        p = os.path.join(OUT, "avatar-%d.png" % size)
        build(size).save(p, "PNG", optimize=True)
        print("%-46s %6.1f Ko" % (p.replace(ROOT + "/", ""), os.path.getsize(p) / 1024))


if __name__ == "__main__":
    main()
