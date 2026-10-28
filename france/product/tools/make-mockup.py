#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mockup du livre (couverture + tranche + pages + ombre) en PNG transparent.

    python3 product/tools/make-mockup.py

Entrée  : assets/img/book/cover-page.jpg  (page 1 du PDF, rendue)
Sorties : assets/img/book/mockup-livre.png     (~1100 px de large, haute résolution)
          assets/img/book/mockup-livre@520.png (variante légère pour l'email/OG)
"""
import os
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
BOOK = os.path.join(ROOT, "assets", "img", "book")

SPINE = 46          # largeur de la tranche (px, à l'échelle de sortie)
PAGES = 14          # épaisseur des pages à droite
RADIUS = 12
PAD = 90            # marge pour l'ombre


def rounded(img, radius):
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, img.size[0] - 1, img.size[1] - 1), radius, fill=255)
    out = img.convert("RGBA")
    out.putalpha(mask)
    return out


def build(target_w=1100):
    cover_src = Image.open(os.path.join(BOOK, "cover-page.jpg")).convert("RGB")
    # hauteur de la couverture dans le rendu final
    cover_h = int(target_w * 0.92 * cover_src.size[1] / cover_src.size[0])
    cover_w = int(target_w * 0.92)
    cover = rounded(cover_src.resize((cover_w, cover_h), Image.LANCZOS), RADIUS)

    W = cover_w + SPINE + PAGES + PAD * 2
    H = cover_h + PAD * 2
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    bx = PAD + SPINE
    by = PAD

    # ---- ombre portée douce (derrière le livre) ----
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sh)
    sd.rounded_rectangle((bx - 6, by + 16, bx + cover_w + 10, by + cover_h + 26), 18,
                         fill=(20, 15, 8, 120))
    canvas.alpha_composite(sh.filter(ImageFilter.GaussianBlur(22)))

    # ---- ombre au sol (ellipse) ----
    floor = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(floor).ellipse(
        (bx - 30, by + cover_h - 22, bx + cover_w + 40, by + cover_h + 44),
        fill=(20, 15, 8, 95))
    canvas.alpha_composite(floor.filter(ImageFilter.GaussianBlur(26)))

    # ---- tranche (dégradé crème) ----
    spine = Image.new("RGB", (SPINE, cover_h))
    sp = spine.load()
    for x in range(SPINE):
        t = x / max(SPINE - 1, 1)
        # sombre au bord gauche, clair vers la couverture
        c = (int(198 + 46 * t), int(190 + 48 * t), int(171 + 52 * t))
        for y in range(cover_h):
            sp[x, y] = c
    spine_rgba = Image.new("RGBA", (SPINE, cover_h))
    spine_rgba.paste(spine, (0, 0))
    mask = Image.new("L", (SPINE, cover_h), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, SPINE + RADIUS, cover_h - 1), RADIUS, fill=255)
    spine_rgba.putalpha(mask)
    canvas.alpha_composite(spine_rgba, (bx - SPINE, by))

    # ---- pages (tranche droite) ----
    pages = Image.new("RGBA", (PAGES, cover_h - 10), (0, 0, 0, 0))
    pd = ImageDraw.Draw(pages)
    pd.rounded_rectangle((0, 0, PAGES - 1, cover_h - 11), 3, fill=(247, 243, 233, 255))
    for y in range(6, cover_h - 16, 7):          # fines stries = feuilles
        pd.line((0, y, PAGES - 1, y), fill=(214, 206, 190, 255))
    canvas.alpha_composite(pages, (bx + cover_w - 2, by + 5))

    # ---- couverture ----
    canvas.alpha_composite(cover, (bx, by))

    # ---- reflet vertical sur la couverture (finition papier) ----
    gloss = Image.new("RGBA", (cover_w, cover_h), (0, 0, 0, 0))
    gd = ImageDraw.Draw(gloss)
    gd.polygon([(0, 0), (int(cover_w * 0.30), 0), (0, int(cover_h * 0.55))],
               fill=(255, 255, 255, 26))
    gm = Image.new("L", (cover_w, cover_h), 0)
    ImageDraw.Draw(gm).rounded_rectangle((0, 0, cover_w - 1, cover_h - 1), RADIUS, fill=255)
    canvas.alpha_composite(Image.composite(gloss, Image.new("RGBA", gloss.size, (0, 0, 0, 0)), gm), (bx, by))

    return canvas


if __name__ == "__main__":
    img = build(1100)
    out = os.path.join(BOOK, "mockup-livre.png")
    img.save(out, "PNG", optimize=True)
    print(f"  {out}  {img.size[0]}x{img.size[1]}  {os.path.getsize(out)//1024} Ko")

    small = build(520)
    out2 = os.path.join(BOOK, "mockup-livre@520.png")
    small.save(out2, "PNG", optimize=True)
    print(f"  {out2}  {small.size[0]}x{small.size[1]}  {os.path.getsize(out2)//1024} Ko")
