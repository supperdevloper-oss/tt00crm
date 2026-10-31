#!/usr/bin/env python3
"""5 variantes du logo « script + couverts », calquées sur la référence.

Proportions mesurées sur le logo de référence (image 1000 × 1000) :

    mot              x   61..396   hauteur d'encre 108
    fourchette       x  427..478   y 329..679   h 351  (l/h = 0.148)
    couteau          x  502..536   y 316..683   h 368  (l/h = 0.095)
    cuillère         x  563..626   y 339..670   h 332  (l/h = 0.193)
    mot              x  650..938   hauteur d'encre 116
    largeur totale   x   61..938   = 878  (87,8 % de la toile)
    couverts centrés verticalement sur la boîte d'encre des mots
    hauteur des couverts = 3,20 × hauteur d'encre du mot

Le nom reste « Friteuse Facile » : jamais celui d'une autre marque.
Sortie : assets/img/brand/logo-N-*.png (1000 × 1000, noir sur blanc).
"""
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "assets", "img", "brand")
FONTS = os.path.join(ROOT, "assets", "fonts")

BLACK = (8, 8, 8)
WHITE = (255, 255, 255)
SS = 4  # suréchantillonnage

# --- constantes de composition (issues de la mesure de la référence) ---
TOTAL_W = 0.878      # largeur totale d'encre / côté
CUT_OVER_TEXT = 3.20  # hauteur des couverts / hauteur d'encre du mot
R_FORK, R_KNIFE, R_SPOON = 0.148, 0.098, 0.180
GAP_PIECES = 0.068   # entre deux couverts, en fraction de leur hauteur
GAP_WORD = 0.090     # entre un mot et les couverts


def _rr(d, box, r, fill):
    d.rounded_rectangle(box, radius=max(1, r), fill=fill)


# ------------------------------------------------------------------ pièces --
def fork(d, cx, top, h, ink=BLACK):
    """Fourchette élancée : 4 dents, tête pleine, long manche."""
    w = h * R_FORK
    x0, x1 = cx - w / 2, cx + w / 2

    tine_top = top
    tine_h = h * 0.235            # dents
    head_h = h * 0.048            # socle plein
    head_w = w * 0.92

    # 4 dents (3 évidements)
    slot = w * 0.088
    tw = (head_w - slot * 3) / 4
    for i in range(4):
        tx = cx - head_w / 2 + i * (tw + slot)
        _rr(d, [tx, tine_top, tx + tw, tine_top + tine_h + head_h * 0.6], tw * 0.45, ink)

    # socle des dents
    _rr(d, [cx - head_w / 2, tine_top + tine_h, cx + head_w / 2, tine_top + tine_h + head_h],
        head_h * 0.40, ink)

    # manche : s'affine vers le bas, bout arrondi
    y0 = tine_top + tine_h + head_h * 0.6
    y1 = top + h
    wt = w * 0.60
    wb = w * 0.34
    d.polygon([(cx - wt / 2, y0), (cx + wt / 2, y0), (cx + wb / 2, y1), (cx - wb / 2, y1)], fill=ink)
    _rr(d, [cx - wb / 2, y1 - wb, cx + wb / 2, y1], wb * 0.5, ink)


def knife(d, cx, top, h, ink=BLACK):
    """Couteau de chef : lame pleine et pointue, manche plus étroit.
    Le tranchant est un seul polygone plein (pas de bord rapporté) pour éviter
    l'effet « cure-dent » que produit une lame trop étroite."""
    w = h * R_KNIFE
    blade_h = h * 0.340
    cx_ = cx

    # lame : base large, pointe fine décalée vers la droite
    pts = [
        (cx_ + w * 0.02, top),                       # pointe
        (cx_ + w * 0.34, top + blade_h * 0.26),
        (cx_ + w * 0.50, top + blade_h * 0.62),
        (cx_ + w * 0.48, top + blade_h * 0.88),
        (cx_ + w * 0.34, top + blade_h),
        (cx_ - w * 0.50, top + blade_h),
        (cx_ - w * 0.50, top + blade_h * 0.10),
    ]
    d.polygon(pts, fill=ink)

    # manche
    y0 = top + blade_h * 0.96
    y1 = top + h
    wt = w * 0.70
    wb = w * 0.38
    d.polygon([(cx_ - wt / 2, y0), (cx_ + wt / 2, y0), (cx_ + wb / 2, y1), (cx_ - wb / 2, y1)], fill=ink)
    _rr(d, [cx_ - wb / 2, y1 - wb, cx_ + wb / 2, y1], wb * 0.5, ink)


def spoon(d, cx, top, h, ink=BLACK):
    """Cuillère : cuilleron ovale, manche effilé."""
    w = h * R_SPOON
    bowl_h = h * 0.320

    d.ellipse([cx - w / 2, top, cx + w / 2, top + bowl_h], fill=ink)

    y0 = top + bowl_h * 0.82
    y1 = top + h
    wt = w * 0.42
    wb = w * 0.30
    d.polygon([(cx - wt / 2, y0), (cx + wt / 2, y0), (cx + wb / 2, y1), (cx - wb / 2, y1)], fill=ink)
    _rr(d, [cx - wb / 2, y1 - wb, cx + wb / 2, y1], wb * 0.5, ink)


PIECES = (fork, knife, spoon)


# ------------------------------------------------------------------- logo --
def build(font_file, size=1000, word_a="Friteuse", word_b="Facile"):
    S = size * SS
    img = Image.new("RGB", (S, S), WHITE)
    d = ImageDraw.Draw(img)

    # 1) calibrer la police pour que la largeur d'encre totale = TOTAL_W
    probe = ImageFont.truetype(font_file, 300)
    unit = 300.0

    def metrics(fs):
        f = ImageFont.truetype(font_file, fs)
        wa = d.textlength(word_a, font=f)
        wb = d.textlength(word_b, font=f)
        ia = d.textbbox((0, 0), word_a, font=f, anchor="ls")
        ib = d.textbbox((0, 0), word_b, font=f, anchor="ls")
        h_ink = max(ia[3], ib[3]) - min(ia[1], ib[1])
        ink = ia
        cut_h = h_ink * CUT_OVER_TEXT
        gap_w = cut_h * GAP_WORD
        gap_p = cut_h * GAP_PIECES
        w_fork, w_knife, w_spoon = (cut_h * R_FORK, cut_h * R_KNIFE, cut_h * R_SPOON)
        group = w_fork + w_knife + w_spoon + gap_p * 2
        total = wa + gap_w + group + gap_w + wb
        return dict(f=f, wa=wa, wb=wb, h_ink=h_ink, cut_h=cut_h,
                    gap_w=gap_w, gap_p=gap_p, w=(w_fork, w_knife, w_spoon),
                    group=group, total=total)

    # dichotomie rapide sur la taille de police
    lo, hi = 10, S
    for _ in range(28):
        mid = (lo + hi) / 2
        if metrics(int(mid))["total"] < S * TOTAL_W:
            lo = mid
        else:
            hi = mid
    m = metrics(int(lo))

    # 2) centrage : tout est aligné sur la boîte d'encre réelle des mots
    f = m["f"]
    ink_a = d.textbbox((0, 0), word_a, font=f, anchor="ls")
    ink_b = d.textbbox((0, 0), word_b, font=f, anchor="ls")
    top_ink = min(ink_a[1], ink_b[1])
    bot_ink = max(ink_a[3], ink_b[3])
    word_cy = S * 0.5

    # avec anchor "ls", y de la zone d'encre est relatif à la ligne de base
    baseline = word_cy - (top_ink + bot_ink) / 2

    left = (S - m["total"]) / 2
    d.text((left, baseline), word_a, font=f, anchor="ls", fill=BLACK)
    d.text((left + m["wa"] + m["gap_w"] + m["group"] + m["gap_w"], baseline),
           word_b, font=f, anchor="ls", fill=BLACK)

    # 3) couverts, centrés verticalement sur la même boîte d'encre
    cut_h = m["cut_h"]
    cut_top = word_cy - cut_h / 2
    x = left + m["wa"] + m["gap_w"]
    for fn, w in zip(PIECES, m["w"]):
        fn(d, x + w / 2, cut_top, cut_h)
        x += w + m["gap_p"]

    return img.resize((size, size), Image.LANCZOS)


VARIANTS = [
    ("logo-1-kaushan.png", os.path.join(FONTS, "KaushanScript-Regular.ttf")),
    ("logo-2-yellowtail.png", os.path.join(FONTS, "script", "Yellowtail.ttf")),
    ("logo-3-alexbrush.png", os.path.join(FONTS, "script", "AlexBrush.ttf")),
    ("logo-4-grandhotel.png", os.path.join(FONTS, "script", "GrandHotel.ttf")),
    ("logo-5-dancing.png", os.path.join(FONTS, "script", "DancingScript-Bold.ttf")),
]


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, font in VARIANTS:
        p = os.path.join(OUT, name)
        build(font).save(p, "PNG", optimize=True)
        print("%-26s %6.1f Ko" % (name, os.path.getsize(p) / 1024))


if __name__ == "__main__":
    main()
