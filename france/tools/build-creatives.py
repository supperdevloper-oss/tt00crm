#!/usr/bin/env python3
"""
Générateur de créatives publicitaires (Meta) — funnel friteuse à air, marché FR.
Sortie : france/assets/creatives/*.png  (4:5 = 1080x1350 · 1:1 = 1080x1080 · 9:16 = 1080x1920)

Usage :  python3 tools/build-creatives.py
Dépendances : Pillow  (pip install pillow)
"""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(ROOT, "assets", "img")
FNT = os.path.join(ROOT, "assets", "fonts")
OUT = os.path.join(ROOT, "assets", "creatives")
os.makedirs(OUT, exist_ok=True)

# ---------------------------------------------------------------- design tokens
GREEN      = (15, 61, 42)
GREEN_DARK = (9, 44, 30)
CREAM      = (246, 242, 233)
PAPER      = (255, 253, 247)
ORANGE     = (217, 90, 30)
ORANGE_LT  = (240, 160, 75)
INK        = (27, 26, 23)
MUTED      = (120, 112, 100)
RED        = (176, 28, 28)

def F(name, size):
    return ImageFont.truetype(os.path.join(FNT, name), size)

OSW_B = lambda s: F("Oswald-Bold.ttf", s)
OSW_M = lambda s: F("Oswald-Medium.ttf", s)
OSW_R = lambda s: F("Oswald-Regular.ttf", s)
PLA_BI = lambda s: F("Playfair-BoldItalic.ttf", s)
PLA_I  = lambda s: F("Playfair-Italic.ttf", s)

# ---------------------------------------------------------------- primitives
def cover(img, w, h, focus=(0.5, 0.5)):
    """Redimensionne + recadre comme object-fit: cover."""
    r = max(w / img.width, h / img.height)
    im = img.resize((int(img.width * r + 1), int(img.height * r + 1)), Image.LANCZOS)
    x = int((im.width - w) * focus[0]); y = int((im.height - h) * focus[1])
    return im.crop((x, y, x + w, y + h))

def vgrad(size, top, bottom, top_a=255, bottom_a=255):
    """Dégradé vertical RGBA."""
    w, h = size
    g = Image.new("RGBA", (1, h))
    for y in range(h):
        t = y / max(h - 1, 1)
        g.putpixel((0, y), (
            int(top[0] + (bottom[0] - top[0]) * t),
            int(top[1] + (bottom[1] - top[1]) * t),
            int(top[2] + (bottom[2] - top[2]) * t),
            int(top_a + (bottom_a - top_a) * t)))
    return g.resize((w, h))

def tw(d, txt, font, track=0):
    """Largeur du texte avec tracking optionnel."""
    if track == 0:
        b = d.textbbox((0, 0), txt, font=font)
        return b[2] - b[0]
    return sum(d.textlength(c, font=font) for c in txt) + track * max(len(txt) - 1, 0)

def draw_tracked(d, xy, txt, font, fill, track=0, anchor="la"):
    """Dessine avec interlettrage (pour les eyebrows)."""
    x, y = xy
    total = tw(d, txt, font, track)
    if anchor[0] == "m": x -= total / 2
    elif anchor[0] == "r": x -= total
    for c in txt:
        d.text((x, y), c, font=font, fill=fill, anchor="l" + anchor[1])
        x += d.textlength(c, font=font) + track
    return total

def wrap(d, txt, font, maxw, track=0):
    words, lines, cur = txt.split(), [], ""
    for w in words:
        cand = (cur + " " + w).strip()
        if tw(d, cand, font, track) <= maxw or not cur:
            cur = cand
        else:
            lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines

def para(d, xy, txt, font, fill, maxw, lh, track=0, align="left", shadow=None):
    x, y = xy
    for line in wrap(d, txt, font, maxw, track):
        w = tw(d, line, font, track)
        lx = x
        if align == "center": lx = x - w / 2
        elif align == "right": lx = x - w
        if shadow:
            draw_tracked(d, (lx + shadow[0], y + shadow[1]), line, font, shadow[2], track, "la")
        draw_tracked(d, (lx, y), line, font, fill, track, "la")
        y += lh
    return y

def rrect(d, box, r, fill=None, outline=None, w=1):
    d.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=w)

def pill(d, center, txt, font, bg, fg, padx=34, pady=16, track=2):
    x, y = center
    w = tw(d, txt, font, track) + padx * 2
    h = font.size + pady * 2
    rrect(d, (x - w / 2, y - h / 2, x + w / 2, y + h / 2), h / 2, fill=bg)
    draw_tracked(d, (x, y), txt, font, fg, track, "mm")
    return w, h

# ---------------------------------------------------------------- icônes vectorielles
def ico_clock(d, cx, cy, r, col, w=5):
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=col, width=w)
    d.line((cx, cy, cx, cy - r * 0.55), fill=col, width=w)
    d.line((cx, cy, cx + r * 0.42, cy + r * 0.2), fill=col, width=w)

def ico_heart(d, cx, cy, r, col, w=5):
    pts = []
    import math
    for i in range(0, 361, 4):
        t = math.radians(i)
        x = 16 * math.sin(t) ** 3
        y = -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))
        pts.append((cx + x * r / 17, cy + y * r / 17))
    d.line(pts + [pts[0]], fill=col, width=w, joint="curve")

def ico_family(d, cx, cy, r, col, w=5):
    d.ellipse((cx - r * 0.28, cy - r, cx + r * 0.28, cy - r * 0.42), outline=col, width=w)
    d.arc((cx - r * 0.62, cy - r * 0.28, cx + r * 0.62, cy + r * 0.95), 200, 340, fill=col, width=w)

def ico_coin(d, cx, cy, r, col, w=5):
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=col, width=w)
    f = OSW_B(int(r * 1.5))
    d.text((cx, cy), "€", font=f, fill=col, anchor="mm")

def ico_check(d, cx, cy, r, col, w=6):
    d.line((cx - r * 0.7, cy, cx - r * 0.1, cy + r * 0.6), fill=col, width=w, joint="curve")
    d.line((cx - r * 0.1, cy + r * 0.6, cx + r * 0.75, cy - r * 0.65), fill=col, width=w, joint="curve")

def ico_cross(d, cx, cy, r, col, w=6):
    d.line((cx - r, cy - r, cx + r, cy + r), fill=col, width=w)
    d.line((cx + r, cy - r, cx - r, cy + r), fill=col, width=w)

def ico_star(d, cx, cy, r, col):
    import math
    pts = []
    for i in range(10):
        ang = math.radians(-90 + i * 36)
        rad = r if i % 2 == 0 else r * 0.44
        pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
    d.polygon(pts, fill=col)

def ico_arrow(d, cx, cy, s, col, w=6):
    d.line((cx - s, cy, cx + s * 0.75, cy), fill=col, width=w)
    d.line((cx + s * 0.78, cy, cx + s * 0.15, cy - s * 0.62), fill=col, width=w)
    d.line((cx + s * 0.78, cy, cx + s * 0.15, cy + s * 0.62), fill=col, width=w)

# ---------------------------------------------------------------- composants
def cta_bar(img, d, y, h, text, sub=None, bg=GREEN, fg=PAPER, accent=ORANGE_LT, arrow=True):
    W = img.width
    m = int(W * 0.045)
    rrect(d, (m, y, W - m, y + h), h * 0.22, fill=bg)
    f = OSW_B(int(h * 0.42))
    t = tw(d, text, f, 2)
    ax = W / 2 - (t / 2 if not arrow else t / 2 + h * 0.2)
    draw_tracked(d, (ax + t / 2, y + h * (0.42 if sub else 0.5)), text, f, fg, 2, "mm")
    if sub:
        fs = OSW_M(int(h * 0.17))
        draw_tracked(d, (W / 2, y + h * 0.74), sub, fs, accent, 1, "mm")
    if arrow:
        ico_arrow(d, W - m - h * 0.52, y + h / 2, h * 0.17, accent, max(4, int(h * 0.045)))

def price_badge(img, d, cx, cy, r, price="2,97 €", label="SEULEMENT", bg=ORANGE, fg=PAPER):
    # garde-fou : le disque reste toujours entièrement dans l'image
    cx = min(max(cx, r + 6), img.width - r - 6)
    cy = min(max(cy, r + 6), img.height - r - 6)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=bg)
    d.ellipse((cx - r + 9, cy - r + 9, cx + r - 9, cy + r - 9), outline=(255, 255, 255, 90), width=3)
    draw_tracked(d, (cx, cy - r * 0.44), label, OSW_M(int(r * 0.24)), fg, 3, "mm")
    # auto-ajustement : le prix doit tenir dans ~78 % de la largeur du disque
    maxw, fs = r * 1.56, int(r * 0.92)
    while fs > 9 and d.textlength(price, font=OSW_B(fs)) > maxw:
        fs -= 2
    d.text((cx, cy + r * 0.12), price, font=OSW_B(fs), fill=fg, anchor="mm")

def benefit_strip(img, d, y, h, items, bg=PAPER, fg=INK, sep=(225, 219, 207)):
    W = img.width
    d.rectangle((0, y, W, y + h), fill=bg)
    n = len(items)
    step = W / n
    for i, (ic, t1, t2) in enumerate(items):
        cx = step * i + step / 2
        ic(d, cx, y + h * 0.3, h * 0.13, ORANGE, max(3, int(h * 0.02)))
        d.text((cx, y + h * 0.58), t1, font=OSW_B(int(h * 0.135)), fill=fg, anchor="mm")
        d.text((cx, y + h * 0.79), t2, font=OSW_R(int(h * 0.105)), fill=MUTED, anchor="mm")
        if i:
            d.line((step * i, y + h * 0.2, step * i, y + h * 0.8), fill=sep, width=3)

def footnote(img, d, txt, y, col=(255, 255, 255), a=210, size=None):
    size = size or int(img.width * 0.0195)
    f = OSW_R(size)
    draw_tracked(d, (img.width / 2, y), txt, f, (col[0], col[1], col[2], a), 1, "mm")

def scrim_top(img, h, color=(9, 20, 14), a0=235, a1=0):
    s = vgrad((img.width, h), color, color, a0, a1)
    img.alpha_composite(s, (0, 0))

def scrim_band(img, y0, h, color=(9, 20, 14), a0=0, a1=0, mid=None):
    """voile sombre dégradé (montée puis descente) pour lisibilité sur photo"""
    w = img.width
    g = Image.new("RGBA", (1, h))
    for y in range(h):
        t = y / max(h - 1, 1)
        a = a0 + (a1 - a0) * t if mid is None else (a0 + (mid - a0) * (t / 0.5) if t < 0.5 else mid + (a1 - mid) * ((t - 0.5) / 0.5))
        g.putpixel((0, y), (color[0], color[1], color[2], int(a)))
    img.alpha_composite(g.resize((w, h)), (0, y0))

def scrim_bottom(img, h, color=(9, 20, 14), a0=0, a1=240):
    s = vgrad((img.width, h), color, color, a0, a1)
    img.alpha_composite(s, (0, img.height - h))

def squiggle(d, cx, y, wdt, col, w=6):
    """petit trait manuscrit sous un mot"""
    import math
    pts = []
    for i in range(0, int(wdt), 4):
        pts.append((cx - wdt / 2 + i, y + math.sin(i / 14) * 5))
    d.line(pts, fill=col, width=w, joint="curve")

def load(name):
    return Image.open(os.path.join(IMG, name)).convert("RGB")

# ================================================================ CRÉATIVE 1 — « 3 erreurs »
def creative_erreurs(size=(1080, 1350)):
    W, H = size
    base = cover(load("dish-poulet.jpg"), W, int(H * 0.66), (0.5, 0.45))
    img = Image.new("RGBA", size, CREAM)
    img.paste(base, (0, 0))
    scrim_band(img, 0, int(H * 0.62), (10, 22, 15), 252, 0, mid=196)

    d = ImageDraw.Draw(img)
    m = int(W * 0.06)
    draw_tracked(d, (W / 2, m - 6), "FRITEUSE À AIR", OSW_M(28), ORANGE_LT, 8, "ma")
    y = m + 48
    d.text((W / 2, y), "3 ERREURS QUI", font=OSW_B(96), fill=PAPER, anchor="ma")
    d.text((W / 2, y + 102), "RENDENT VOTRE", font=OSW_B(96), fill=PAPER, anchor="ma")
    d.text((W / 2, y + 204), "POULET SEC", font=OSW_B(108), fill=ORANGE_LT, anchor="ma")
    squiggle(d, W / 2, y + 330, int(W * 0.50), ORANGE, 7)
    para(d, (W / 2, y + 360), "Et comment le rendre croustillant dehors, juteux dedans — en 12 minutes.",
         OSW_M(38), (255, 255, 255, 245), int(W * 0.78), 50, align="center",
         shadow=(0, 3, (0, 0, 0, 170)))

    # bandeau bas cream
    band_h = int(H * 0.30)
    by = H - band_h
    d.rectangle((0, by, W, H), fill=CREAM)
    d.rectangle((0, by, W, by + 8), fill=GREEN)

    items = ["TEMPS TROP LONG", "TEMPÉRATURE FAUSSE", "PANIER TROP PLEIN"]
    ys = by + int(band_h * 0.17)
    step = W / 3
    for i, txt in enumerate(items):
        cx = step * i + step / 2
        f = OSW_M(25)
        t = tw(d, txt, f, 1)
        total = 34 + t
        x0 = cx - total / 2
        ico_cross(d, x0 + 13, ys + 2, 12, RED, 5)
        draw_tracked(d, (x0 + 34, ys), txt, f, INK, 1, "la")

    cta_bar(img, d, by + int(band_h * 0.32), int(band_h * 0.34),
            "VOIR LA SOLUTION", sub="365 RECETTES TESTÉES · 2,97 € · PDF IMMÉDIAT")
    footnote(img, d, "Paiement unique · Garantie 14 jours", H - int(band_h * 0.09), INK, 150)

    return img.convert("RGB")

# ================================================================ CRÉATIVE 2 — « 365 » grille
def creative_365(size=(1080, 1350)):
    W, H = size
    img = Image.new("RGBA", size, GREEN_DARK)
    tiles = ["dish-poulet.jpg", "dish-saumon.jpg", "dish-brownie.jpg", "hero-flatlay.jpg"]
    gap = int(W * 0.014)
    cell_w = (W - gap) // 2
    cell_h = (H - gap) // 2
    pos = [(0, 0), (cell_w + gap, 0), (0, cell_h + gap), (cell_w + gap, cell_h + gap)]
    for p, t in zip(pos, tiles):
        im = cover(load(t), cell_w, cell_h, (0.5, 0.5))
        img.paste(ImageEnhance.Color(im).enhance(1.04), p)

    ov = Image.new("RGBA", size, (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    band = int(H * 0.42)
    od.rounded_rectangle((int(W * 0.055), (H - band) / 2, W - int(W * 0.055), (H + band) / 2),
                         int(W * 0.03), fill=(11, 46, 31, 248), outline=(255, 255, 255, 60), width=3)
    img.alpha_composite(ov)
    scrim_bottom(img, int(H * 0.22), (6, 24, 15), 0, 235)

    d = ImageDraw.Draw(img)
    cy = H / 2
    draw_tracked(d, (W / 2, cy - band * 0.395), "POUR VOTRE FRITEUSE À AIR", OSW_M(28), ORANGE_LT, 7, "mm")
    d.text((W / 2, cy - band * 0.145), "365", font=OSW_B(224), fill=PAPER, anchor="mm")
    d.text((W / 2, cy + band * 0.165), "recettes", font=PLA_BI(100), fill=ORANGE_LT, anchor="mm")
    d.text((W / 2, cy + band * 0.325), "une recette pour chaque jour de l'année",
           font=OSW_R(35), fill=(228, 238, 230), anchor="mm")

    price_badge(img, d, int(W * 0.815), int(H * 0.205), int(W * 0.095))
    pill(d, (int(W * 0.215), int(H * 0.062)), "PDF · ACCÈS IMMÉDIAT", OSW_M(24), PAPER, GREEN, 24, 12, 2)
    footnote(img, d, "Temps & température exacts · ingrédients simples · zéro huile",
             H - int(H * 0.055), (255, 255, 255), 235, size=30)
    return img.convert("RGB")

# ================================================================ CRÉATIVE 3 — comparaison temps
def creative_temps(size=(1080, 1350)):
    W, H = size
    img = Image.new("RGBA", size, CREAM)
    split_y = int(H * 0.57)
    left = cover(load("four-plat.jpg"), W // 2, split_y, (0.5, 0.5))
    left = ImageEnhance.Brightness(left).enhance(0.78).filter(ImageFilter.GaussianBlur(0.6))
    left = ImageEnhance.Color(left).enhance(0.55)
    right = cover(load("dish-poulet.jpg"), W - W // 2, split_y, (0.62, 0.55))
    img.paste(left.convert("RGB"), (0, 0))
    img.paste(right.convert("RGB"), (W // 2, 0))

    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, W // 2, 104), fill=(30, 30, 28, 235))
    d.rectangle((W // 2, 0, W, 104), fill=(15, 61, 42, 240))
    draw_tracked(d, (W * 0.25, 52), "FOUR · 45 MIN", OSW_B(38), (236, 236, 236), 3, "mm")
    draw_tracked(d, (W * 0.75, 52), "FRITEUSE · 12 MIN", OSW_B(38), PAPER, 3, "mm")
    # petit séparateur vertical
    d.rectangle((W // 2 - 3, 0, W // 2 + 3, split_y), fill=PAPER)

    # bloc texte bas
    by = split_y
    d.rectangle((0, by, W, H), fill=PAPER)
    d.rectangle((0, by, W, by + 7), fill=ORANGE)
    m = int(W * 0.07)
    d.text((m, by + 40), "Le même plat.", font=OSW_B(70), fill=INK)
    d.text((m, by + 122), "Sans allumer le four.", font=PLA_BI(60), fill=GREEN)
    para(d, (m, by + 200),
         "365 recettes avec le temps et la température exacts, pour ne plus jamais rater un plat.",
         OSW_R(34), MUTED, W - m * 2, 45)

    cta_bar(img, d, by + 300, 106, "TÉLÉCHARGER LES RECETTES", bg=GREEN)
    footnote(img, d, "2,97 € · paiement unique · PDF envoyé en 1 minute", H - 46, INK, 165)
    return img.convert("RGB")

# ================================================================ CRÉATIVE 4 — mockup ebook
def creative_mockup(size=(1080, 1350)):
    W, H = size
    bg = cover(load("hero-flatlay.jpg"), W, H, (0.5, 0.45))
    bg = ImageEnhance.Brightness(bg).enhance(0.50).filter(ImageFilter.GaussianBlur(3))
    img = bg.convert("RGBA")
    img.alpha_composite(vgrad(size, (9, 30, 20), (9, 30, 20), 150, 225))
    d = ImageDraw.Draw(img)

    m = int(W * 0.065)
    draw_tracked(d, (m, int(H * 0.075)), "LE GUIDE PRATIQUE", OSW_M(27), ORANGE_LT, 7, "la")
    d.text((m, int(H * 0.115)), "Toutes vos", font=OSW_B(66), fill=PAPER)
    d.text((m, int(H * 0.115) + 74), "recettes.", font=PLA_BI(66), fill=ORANGE_LT)

    # couverture RÉELLE du livre (page 1 du PDF, rendue en 1200 px)
    bw = int(W * 0.455); bh = int(bw * 297 / 210)
    bx, by = int((W - bw) / 2) - int(W * 0.01), int(H * 0.262)
    sh = Image.new("RGBA", size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((bx + 16, by + 26, bx + bw + 16, by + bh + 26),
                                         16, fill=(0, 0, 0, 140))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(22)))

    cv = Image.open(os.path.join(IMG, "book", "cover-page.jpg")).convert("RGB").resize((bw, bh), Image.LANCZOS)
    mask = Image.new("L", (bw, bh), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, bw - 1, bh - 1), 10, fill=255)
    img.paste(cv, (bx, by), mask)
    d = ImageDraw.Draw(img)
    # tranche du livre (effet 3D léger à gauche)
    sw_ = max(4, int(W * 0.006))
    d.rectangle((bx - sw_, by + 6, bx, by + bh - 6), fill=(226, 219, 206))
    d.line((bx - sw_, by + 6, bx - sw_, by + bh - 6), fill=(190, 182, 168), width=1)
    d.rounded_rectangle((bx, by, bx + bw, by + bh), 10, outline=(255, 255, 255, 110), width=2)

    price_badge(img, d, int(W * 0.855), int(H * 0.415), int(W * 0.105))

    cta_bar(img, d, H - int(H * 0.16), 110, "JE VEUX CE GUIDE", sub="PDF · 2,97 € · GARANTIE 14 JOURS")
    footnote(img, d, "Lisible sur téléphone, tablette, ordinateur — aucune application",
             H - 44, (255, 255, 255), 205)
    return img.convert("RGB")

# ================================================================ CRÉATIVE 5 — bonus / retargeting
def creative_bonus(size=(1080, 1350)):
    W, H = size
    img = Image.new("RGBA", size, CREAM)
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, W, int(H * 0.30)), fill=GREEN)
    img.alpha_composite(vgrad((W, int(H * 0.09)), GREEN, CREAM, 255, 0), (0, int(H * 0.30)))
    d = ImageDraw.Draw(img)

    draw_tracked(d, (W / 2, 58), "OFFRE DE LANCEMENT", OSW_M(28), ORANGE_LT, 8, "ma")
    d.text((W / 2, 100), "3 BONUS OFFERTS", font=OSW_B(88), fill=PAPER, anchor="ma")
    d.text((W / 2, 202), "avec votre guide aujourd'hui", font=OSW_R(36), fill=(220, 235, 226), anchor="ma")

    cards = [("TABLEAU T°", "42 aliments, à imprimer", "15 €", "dish-poulet.jpg"),
             ("4 SEMAINES", "28 menus + courses", "15 €", "dish-plats.jpg"),
             ("50 DESSERTS", "gâteaux & goûters", "17 €", "dish-brownie.jpg")]
    cw = int(W * 0.28); ch = int(H * 0.30); gap = int(W * 0.033)
    x0 = (W - (cw * 3 + gap * 2)) / 2
    y0 = int(H * 0.335)
    for i, (t1, t2, val, ph) in enumerate(cards):
        x = x0 + i * (cw + gap)
        # ombre
        sh = Image.new("RGBA", size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle((x + 6, y0 + 10, x + cw + 6, y0 + ch + 10), 16, fill=(0, 0, 0, 45))
        img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
        d = ImageDraw.Draw(img)
        rrect(d, (x, y0, x + cw, y0 + ch), 16, fill=PAPER, outline=(224, 217, 204), w=2)
        ih = int(ch * 0.44)
        im = cover(load(ph), cw - 14, ih - 8, (0.5, 0.5))
        img.paste(im, (int(x + 7), y0 + 7))
        rrect(d, (x, y0, x + cw, y0 + ch), 16, outline=(224, 217, 204), w=2)
        d = ImageDraw.Draw(img)
        pill(d, (int(x + cw / 2), y0 + 22), f"BONUS {i+1}", OSW_M(22), ORANGE, PAPER, 16, 8, 1)
        cy2 = y0 + ih + 34
        for line in wrap(d, t1, OSW_B(31), cw - 24):
            d.text((x + cw / 2, cy2), line, font=OSW_B(31), fill=INK, anchor="ma"); cy2 += 34
        for line in wrap(d, t2, OSW_R(25), cw - 30):
            d.text((x + cw / 2, cy2 + 6), line, font=OSW_R(25), fill=MUTED, anchor="ma"); cy2 += 28
        # valeur barrée
        vy = y0 + ch - 46
        vtxt = val
        fv = OSW_M(26)
        wv = tw(d, vtxt, fv, 1)
        d.text((x + cw / 2, vy), vtxt, font=fv, fill=MUTED, anchor="mm")
        d.line((x + cw / 2 - wv / 2 - 2, vy, x + cw / 2 + wv / 2 + 2, vy), fill=(200, 80, 60), width=3)
        d.text((x + cw / 2, vy + 26), "OFFERT", font=OSW_B(24), fill=GREEN, anchor="mm")

    yy = y0 + ch + 40
    d.text((W / 2, yy), "Valeur du pack : 85 €", font=OSW_M(38), fill=MUTED, anchor="mm")
    d.text((W / 2, yy + 54), "Aujourd'hui : 2,97 €", font=OSW_B(62), fill=GREEN, anchor="mm")
    d.text((W / 2, yy + 104), "soit 96 % de réduction", font=OSW_M(30), fill=ORANGE, anchor="mm")
    cta_bar(img, d, yy + 132, 108, "JE PROFITE DES BONUS", bg=GREEN)
    footnote(img, d, "Bonus envoyés par email avec le guide · garantie 14 jours", H - 52, INK, 165)
    return img.convert("RGB")

# ================================================================ variantes de format
def to_1x1(src_fn):
    def build(size=(1080, 1080)):
        img = src_fn((1080, 1350))
        canvas = Image.new("RGB", (1080, 1080), CREAM)
        canvas.paste(img.resize((1080, 1350), Image.LANCZOS).crop((0, 135, 1080, 1215)), (0, 0))
        return canvas
    return build

def to_story(src_fn, add_cta=False):
    """Version 9:16. add_cta=True uniquement pour les créas qui n'ont pas de bouton intégré."""
    def build(size=(1080, 1920)):
        img = src_fn((1080, 1350))
        canvas = Image.new("RGB", (1080, 1920), GREEN_DARK)
        canvas.paste(img, (0, 285))
        d = ImageDraw.Draw(canvas)
        d.rectangle((0, 0, 1080, 285), fill=GREEN)
        d.rectangle((0, 1635, 1080, 1920), fill=GREEN)
        draw_tracked(d, (540, 96), "LE GUIDE DE LA FRITEUSE À AIR", OSW_M(36), PAPER, 6, "ma")
        draw_tracked(d, (540, 168), "365 recettes · 2,97 € · PDF immédiat", OSW_R(31), ORANGE_LT, 3, "ma")
        if add_cta:
            cta_bar(canvas, d, 1690, 116, "JE LE VEUX MAINTENANT", bg=(20, 92, 58))
        else:
            draw_tracked(d, (540, 1738), "JE LE VEUX", OSW_B(58), PAPER, 8, "ma")
            draw_tracked(d, (540, 1812), "Téléchargement immédiat · garantie 14 jours",
                         OSW_R(29), (176, 203, 186), 2, "ma")
        return canvas
    return build

# ================================================================ exécution
JOBS = [
    ("01-erreurs-4x5",   creative_erreurs,  (1080, 1350)),
    ("01-erreurs-1x1",   to_1x1(creative_erreurs), (1080, 1080)),
    ("01-erreurs-9x16",  to_story(creative_erreurs), (1080, 1920)),
    ("02-365-4x5",       creative_365,      (1080, 1350)),
    ("02-365-1x1",       to_1x1(creative_365), (1080, 1080)),
    ("02-365-9x16",      to_story(creative_365, add_cta=True), (1080, 1920)),
    ("03-temps-4x5",     creative_temps,    (1080, 1350)),
    ("03-temps-1x1",     to_1x1(creative_temps), (1080, 1080)),
    ("04-guide-4x5",     creative_mockup,   (1080, 1350)),
    ("04-guide-1x1",     to_1x1(creative_mockup), (1080, 1080)),
    ("04-guide-9x16",    to_story(creative_mockup), (1080, 1920)),
    ("05-bonus-4x5",     creative_bonus,    (1080, 1350)),
    ("05-bonus-1x1",     to_1x1(creative_bonus), (1080, 1080)),
    ("03-temps-9x16",    to_story(creative_temps), (1080, 1920)),
    ("05-bonus-9x16",    to_story(creative_bonus), (1080, 1920)),
]

if __name__ == "__main__":
    for name, fn, size in JOBS:
        im = fn(size)
        path = os.path.join(OUT, name + ".jpg")
        im.save(path, "JPEG", quality=86, optimize=True, progressive=True)
        print(f"{name:18s} {im.size[0]}x{im.size[1]}  {os.path.getsize(path)//1024} KB")
    print("\nOK →", OUT)
