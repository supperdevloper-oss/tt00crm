#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Génère le produit « 365 Recettes pour Friteuse à Air » (PDF A4) + les 3 bonus.

    python3 build-pdf.py            # tout
    python3 build-pdf.py main       # seulement le guide
    python3 build-pdf.py bonus      # seulement les bonus

Dépendances : fpdf2   (pip install fpdf2)
Entrées    : data/*.txt  (Titre|pers|temps|température|ingrédients|étapes ;;|astuce)
Sorties    : 365-recettes-friteuse-a-air.pdf  +  bonus/*.pdf
"""
import os, sys, glob, re, unicodedata
from fpdf import FPDF

ROOT = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(os.path.dirname(ROOT), "assets", "fonts")
IMG = os.path.join(os.path.dirname(ROOT), "assets", "img")
DATA = os.path.join(ROOT, "data")
OUT = ROOT

# ---------------------------------------------------------------- couleurs
GREEN = (15, 61, 42)
GREEN_D = (9, 42, 29)
GREEN_L = (31, 122, 82)
CREAM = (246, 242, 233)
PAPER = (255, 253, 247)
ORANGE = (217, 90, 30)
ORANGE_L = (240, 160, 75)
INK = (27, 26, 23)
MUTED = (111, 104, 92)
LINE = (226, 219, 206)
TINT = (252, 246, 235)

BOOK_IMG = {
    "dish-poulet.jpg": "ch-01.jpg", "dish-saumon.jpg": "ch-02.jpg",
    "dish-legumes.jpg": "ch-03.jpg", "dish-entrees.jpg": "ch-04.jpg",
    "dish-plats.jpg": "ch-05.jpg", "dish-petitdej.jpg": "ch-06.jpg",
    "dish-brownie.jpg": "ch-07.jpg", "dish-monde.jpg": "ch-08.jpg",
    "dish-express.jpg": "ch-09.jpg",
}

CHAP_INTRO = [
    ("La viande est ce qui a fait la réputation de la friteuse à air : une peau croustillante, "
     "une chair qui reste juteuse, et deux fois moins de matière grasse qu'à la poêle. Le secret "
     "tient en trois mots : sécher, espacer, retourner.",
     "Un thermomètre à cœur vaut mieux que dix minutes de plus : le poulet est cuit à 75 °C, jamais avant."),
    ("Le poisson supporte mal l'approximation : deux minutes de trop et il sèche. À l'air chaud, il "
     "cuit vite et garde son eau — à condition de le poser peau vers le bas et de ne pas le noyer sous "
     "une sauce dès le départ.",
     "Pour un poisson entier, glissez une tranche de citron sous la peau : le parfum passe dans la chair, pas sur la croûte."),
    ("Les légumes sont la meilleure raison d'acheter une friteuse à air : ils rôtissent comme au four, "
     "en un tiers du temps, avec une cuillère d'huile au lieu d'un fond de plat. Le croustillant vient "
     "de l'eau que vous retirez, jamais de l'huile que vous ajoutez.",
     "Séchez les légumes dans un torchon propre avant de les huiler : c'est la seule étape qui décide du résultat."),
    ("Un apéritif réussi se joue à la chaleur et au croustillant. Toutes les recettes de ce chapitre "
     "se préparent en moins de vingt minutes et se servent brûlantes — c'est-à-dire à l'instant où "
     "les invités arrivent.",
     "Une seule couche, jamais deux : deux fournées de 10 minutes valent mieux qu'une fournée de 20."),
    ("Un plat complet, c'est une viande, un féculent et un légume qui cuisent ensemble et arrivent "
     "en même temps dans la même assiette. Chaque recette de ce chapitre est calculée pour un seul "
     "panier et une seule vaisselle.",
     "Coupez tous les morceaux à la même taille : c'est ce qui permet de tout cuire en une fois."),
    ("Le matin, la friteuse remplace le grille-pain, la poêle à crêpes et le four. Elle réchauffe, "
     "elle dore, elle cuit les œufs — et elle se nettoie en trois minutes, ce qui compte à 7 heures "
     "du matin.",
     "Préchauffez pendant que vous préparez : le premier toast sera aussi bon que le dernier."),
    ("Oui, on fait des gâteaux à la friteuse. La cuisson est plus douce qu'au four, la mie reste "
     "moelleuse et les bords ne sèchent pas. Il faut simplement un moule adapté, un préchauffage "
     "sérieux et un cure-dent pour vérifier.",
     "Baissez de 10 °C et couvrez d'aluminium si le dessus dore trop vite : le sucre brunit avant que le cœur ne cuise."),
    ("Falafels, nems, tacos, tikka masala : la friteuse à air est née dans les cuisines où l'on "
     "n'utilise pas de bain de friture. Ce chapitre rassemble les recettes du monde qui gagnent "
     "le plus à cette cuisson.",
     "Les marinades sucrées (miel, hoisin, barbecue) s'appliquent toujours en fin de cuisson."),
    ("Le congelé est le vrai test d'une friteuse à air. Pas de décongélation, pas de papier "
     "absorbant, pas d'attente : un panier, un minuteur, et un dîner en quinze minutes. Ce chapitre "
     "est le plus rapide du livre.",
     "Ne décongelez jamais avant : l'eau rendue par la décongélation empêche le croustillant."),
]

CHAPTERS = [
    ("01-viandes.txt",        "Viandes & volailles",        "Les classiques qui doivent rester juteux.",        "dish-poulet.jpg"),
    ("02-poissons.txt",       "Poissons & fruits de mer",   "La cuisson la plus difficile — et la plus rapide.", "dish-saumon.jpg"),
    ("03-legumes.txt",        "Légumes & accompagnements",  "Le croustillant sans la friture.",                  "dish-legumes.jpg"),
    ("04-entrees.txt",        "Entrées & apéros",           "Ce qui fait venir tout le monde dans la cuisine.",  "dish-entrees.jpg"),
    ("05-plats-complets.txt", "Plats complets",             "Un plat, un panier, pas de vaisselle.",             "dish-plats.jpg"),
    ("06-petit-dejeuner.txt", "Petit-déjeuner & goûter",    "Le matin, la friteuse n'a rien à envier au grille-pain.", "dish-petitdej.jpg"),
    ("07-desserts.txt",       "Desserts",                   "Oui, on fait des gâteaux à la friteuse.",           "dish-brownie.jpg"),
    ("08-monde.txt",          "Cuisine du monde",           "Un voyage sans quitter la cuisine.",                "dish-monde.jpg"),
    ("09-express.txt",        "Surgelés & express",         "Moins de 20 minutes, zéro préparation.",            "dish-express.jpg"),
]

# ---------------------------------------------------------------- données
def load_recipes():
    recs, num = [], 0
    for ci, (fname, title, subtitle, image) in enumerate(CHAPTERS):
        path = os.path.join(DATA, fname)
        if not os.path.exists(path):
            raise SystemExit("Fichier manquant : " + path)
        lines = [l for l in open(path, encoding="utf-8").read().splitlines() if l.strip()]
        start = num
        for line in lines:
            p = [x.strip() for x in line.split("|")]
            if len(p) != 7:
                raise SystemExit(f"{fname} : {len(p)} champs -> {line[:60]}")
            num += 1
            recs.append({
                "n": num, "ch": ci, "title": p[0], "pers": p[1], "time": p[2],
                "temp": p[3], "ing": [x.strip() for x in p[4].split("•") if x.strip()],
                "steps": [x.strip() for x in p[5].split(";;") if x.strip()],
                "tip": p[6],
            })
        yield ci, title, subtitle, image, recs[start:num]
    if num != 365:
        raise SystemExit(f"365 recettes attendues, {num} trouvées")


def chapters():
    return list(load_recipes())


# ---------------------------------------------------------------- texte
def norm(s):
    s = unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode()
    return s.lower()


def hyph(s):
    return s.replace("œ", "oe").replace("Œ", "OE")


class Book(FPDF):
    def __init__(self, **kw):
        super().__init__(orientation="P", unit="mm", format="A4", **kw)
        self.set_auto_page_break(False)
        self.set_margins(18, 18, 18)
        self.add_font("Oswald", "", os.path.join(FONTS, "Oswald-Regular.ttf"))
        self.add_font("Oswald", "B", os.path.join(FONTS, "Oswald-Bold.ttf"))
        self.add_font("OswaldM", "", os.path.join(FONTS, "Oswald-Medium.ttf"))
        self.add_font("Lato", "", os.path.join(FONTS, "Lato-Regular.ttf"))
        self.add_font("Lato", "B", os.path.join(FONTS, "Lato-Bold.ttf"))
        self.add_font("Lato", "I", os.path.join(FONTS, "Lato-Italic.ttf"))
        self.add_font("Playfair", "BI", os.path.join(FONTS, "Playfair-BoldItalic.ttf"))
        self.add_font("Playfair", "I", os.path.join(FONTS, "Playfair-Italic.ttf"))
        self.chapter_name = ""
        self.part_label = ""
        self.toc = {}
        self.folio = {}
        self._meta = {}
        self.plain = False
        self.toc_pass = 2
        self.W, self.H = 210, 297
        self.ml, self.ml2 = 18, 192      # gauche / droite
        self.cw = 174                     # largeur de contenu

    def add_page(self, *a, **k):
        super().add_page(*a, **k)
        self._meta[self.page_no()] = (self.chapter_name, self.part_label, self.plain)

    def multi_cell(self, *a, **k):
        k.setdefault("new_x", "LMARGIN")
        k.setdefault("new_y", "NEXT")
        k.setdefault("align", "L")
        return super().multi_cell(*a, **k)

    def mark(self, name, level=0):
        try:
            self.start_section(name, level=level)
        except Exception:
            pass

    # ---- helpers
    def txt(self, h, s, w=None, font=("Lato", "", 9), color=INK, align="L", fill=False, lh=None):
        self.set_font(*font)
        self.set_text_color(*color)
        self.multi_cell(w or self.cw, lh or h, s, align=align, fill=fill, new_x="LMARGIN", new_y="NEXT")
        return self.get_y()

    def measure(self, s, w, font, lh):
        self.set_font(*font)
        return self.multi_cell(w, lh, s, dry_run=True, output="HEIGHT")

    def tracked_w(self, s, font, track=0.0):
        self.set_font(*font)
        return sum(self.get_string_width(c) for c in s) + track * max(len(s) - 1, 0)

    def tracked(self, x, y, s, font, color=INK, track=0.9, align="L"):
        self.set_font(*font)
        self.set_text_color(*color)
        w = self.tracked_w(s, font, track)
        if align == "C": x = x - w / 2
        elif align == "R": x = x - w
        for c in s:
            self.text(x, y, c)
            x += self.get_string_width(c) + track
        return w

    def rule(self, x, y, w, color=LINE, t=0.3):
        self.set_draw_color(*color)
        self.set_line_width(t)
        self.line(x, y, x + w, y)

    def rrect(self, x, y, w, h, r, fill=None, stroke=None, lw=0.3):
        if fill: self.set_fill_color(*fill)
        if stroke:
            self.set_draw_color(*stroke); self.set_line_width(lw)
        style = ""
        if fill: style += "F"
        if stroke: style += "D"
        if style:
            self.rect(x, y, w, h, style, round_corners=r > 0, corner_radius=r)

    # ---- entêtes / pieds
    def _pm(self):
        return self._meta.get(self.page_no(), ("", "", False))

    def header(self):
        chap, part, plain = self._pm()
        if self.page_no() <= 3 or plain:
            return
        self.set_font("OswaldM", "", 7.6)
        self.set_text_color(*MUTED)
        self.text(self.ml, 12, hyph(chap.upper()))
        self.set_font("Oswald", "", 7.6)
        self.text(self.ml2 - self.get_string_width("365 RECETTES · FRITEUSE À AIR"), 12, "365 RECETTES · FRITEUSE À AIR")
        self.rule(self.ml, 14.5, self.cw, LINE, 0.25)

    def footer(self):
        chap, part, plain = self._pm()
        if self.page_no() <= 3 or plain:
            return
        self.set_font("Oswald", "", 8)
        self.set_text_color(*MUTED)
        n = str(self.page_no())
        self.text(self.ml, 288, hyph(part.upper()))
        self.text(self.ml2 - self.get_string_width(n) / 2, 288, n)


# ---------------------------------------------------------------- couverture
def cover(b):
    b.add_page()
    b.mark("Couverture")
    b.set_fill_color(*GREEN); b.rect(0, 0, 210, 297, "F")
    img = os.path.join(IMG, "book", "cover-hero.jpg")
    if os.path.exists(img):
        b.image(img, 0, 0, 210, 124)
    b.set_text_color(*PAPER)
    b.tracked(105, 142, "LE GUIDE PRATIQUE", ("OswaldM", "", 11), ORANGE_L, 3.2, "C")
    b.set_font("Oswald", "B", 92); b.set_text_color(*PAPER)
    b.text(105 - b.get_string_width("365") / 2, 196, "365")
    b.set_font("Playfair", "BI", 46); b.set_text_color(*ORANGE_L)
    b.text(105 - b.get_string_width("recettes") / 2, 226, "recettes")
    b.set_font("Oswald", "B", 21); b.set_text_color(*PAPER)
    for i, t in enumerate(["POUR VOTRE", "FRITEUSE À AIR"]):
        b.text(105 - b.get_string_width(t) / 2, 244 + i * 10, t)
    b.set_draw_color(*ORANGE); b.set_line_width(0.8)
    b.line(78, 262, 132, 262)
    b.set_font("Lato", "", 10); b.set_text_color(*(200, 220, 208))
    for i, t in enumerate(["Temps et températures exacts · ingrédients simples",
                           "ÉDITION 2026"]):
        b.text(105 - b.get_string_width(t) / 2, 272 + i * 6, t)


def copyright_page(b, ref):
    b.add_page()
    b.mark("Comment utiliser ce guide")
    b.set_fill_color(*PAPER); b.rect(0, 0, 210, 297, "F")
    y = 62
    b.set_font("Oswald", "B", 25); b.set_text_color(*GREEN)
    b.text(18, y, "365 Recettes pour Friteuse à Air")
    y += 13
    b.set_font("Playfair", "I", 13.5); b.set_text_color(*MUTED)
    b.text(18, y, "Le guide pratique de la friteuse à air — édition 2026")
    y += 10
    b.set_draw_color(*ORANGE); b.set_line_width(1); b.line(18, y, 58, y)
    y += 10
    paras = [
        "Ce guide a été conçu pour être utilisé, pas rangé. Chaque recette donne la quantité, "
        "le temps, la température et le geste qui fait la différence. Ouvrez, suivez, recommencez.",
        "Les temps indiqués correspondent à une friteuse à air de 4 à 6 litres, de 1500 à 1800 W. "
        "Les appareils plus petits ou moins puissants demandent 2 à 5 minutes de plus : fiez-vous au "
        f"tableau de la page {ref.get('table', 6)} et à la cuisson réelle, jamais seulement à la montre.",
        "Les photographies sont illustratives. Les marques citées appartiennent à leurs propriétaires "
        "respectifs ; ce guide n'est affilié à aucun fabricant.",
        "Tous droits réservés. Aucune partie de cet ouvrage ne peut être reproduite, distribuée ou "
        "revendue sans autorisation écrite, à l'exception d'un usage personnel et familial.",
    ]
    for pt in paras:
        b.set_xy(18, y)
        b.set_font("Lato", "", 9.4); b.set_text_color(*(60, 58, 52))
        b.multi_cell(b.cw, 5.1, pt)
        y = b.get_y() + 5.4

    y += 8
    b.set_font("OswaldM", "", 8.4); b.set_text_color(*ORANGE)
    b.tracked(18, y, "COMMENT UTILISER CE GUIDE", ("OswaldM", "", 8.4), ORANGE, 1.8)
    y += 9
    for n, t in [
        ("1.", f"Commencez par les pages {ref.get('rules', 4)} à {ref.get('rules', 4) + 1} : les règles qui changent tout."),
        ("2.", f"Notez les températures du tableau page {ref.get('table', 6)} sur un papier collé à votre friteuse."),
        ("3.", "Choisissez une recette par jour. Le numéro se trouve en haut de chaque page."),
        ("4.", "Écrivez dans la marge ce qui a marché chez vous : votre friteuse a ses habitudes."),
    ]:
        b.set_font("Lato", "B", 9.2); b.set_text_color(*GREEN)
        b.text(18, y, n)
        b.set_font("Lato", "", 9.2); b.set_text_color(*(60, 58, 52))
        b.text(24, y, t)
        y += 6.6
    b.set_font("Lato", "I", 8.2); b.set_text_color(*MUTED)
    b.text(18, 268, "Édition 2026 · 365 recettes · 9 chapitres · index par ingrédient en fin d'ouvrage")
    b.set_font("Oswald", "", 7.6); b.set_text_color(*MUTED)
    b.tracked(18, 276, "FRITEUSE FACILE", ("Oswald", "", 7.6), MUTED, 1.6)


def toc_page(b, chap_pages, ref):
    b.plain = True
    b.add_page()
    b.mark("Sommaire")
    b.plain = False
    b.set_fill_color(*PAPER); b.rect(0, 0, 210, 297, "F")
    b.set_font("Oswald", "B", 30); b.set_text_color(*GREEN)
    b.text(18, 34, "Sommaire")
    b.set_draw_color(*ORANGE); b.set_line_width(1)
    b.line(18, 39, 60, 39)

    # colonne gauche : avant-propos + chapitres
    y = 56
    for t, p in [("Comment utiliser ce guide", 2),
                 ("Les 12 règles d'or", ref.get("rules", 4)),
                 ("Tableau temps & températures", ref.get("table", 6))]:
        b.set_font("Lato", "", 10.2); b.set_text_color(*INK)
        b.text(18, y, t)
        b.set_font("OswaldM", "", 9.2); b.set_text_color(*MUTED)
        num = str(p)
        b.text(112 - b.get_string_width(num), y, num)
        b.set_draw_color(*LINE); b.set_line_width(0.2)
        b.line(18, y + 2, 112, y + 2)
        y += 8.6

    y += 5
    b.tracked(18, y, "LES 9 CHAPITRES", ("OswaldM", "", 8.4), ORANGE, 1.8)
    y += 9
    for ci, (fname, title, subtitle, image) in enumerate(CHAPTERS):
        b.set_font("OswaldM", "", 9.4); b.set_text_color(*ORANGE)
        b.text(18, y, f"{ci+1:02d}")
        b.set_font("Lato", "B", 10.8); b.set_text_color(*INK)
        b.text(27, y, title)
        rng = RANGES[ci]
        b.set_font("Lato", "", 8); b.set_text_color(*MUTED)
        b.text(27, y + 4.4, f"recettes {rng[0]:03d} à {rng[1]:03d}")
        b.set_font("OswaldM", "", 9.2); b.set_text_color(*MUTED)
        num = str(chap_pages.get(ci, "·"))
        b.text(112 - b.get_string_width(num), y, num)
        b.set_draw_color(*LINE); b.set_line_width(0.2)
        b.line(18, y + 6.6, 112, y + 6.6)
        y += 12.8

    # colonne droite : visuel + annexes + bonus
    img = os.path.join(IMG, "dish-poulet.jpg")
    if os.path.exists(img):
        b.image(img, 128, 26, 64, 74, keep_aspect_ratio=False)
        b.set_draw_color(*GREEN); b.set_line_width(0.8)
        b.rect(128, 26, 64, 74)

    ry = 114
    b.tracked(128, ry, "POUR ALLER PLUS LOIN", ("OswaldM", "", 7.8), ORANGE, 1.4)
    ry += 8
    for t, key in [("Menus de la semaine", "menus"),
                   ("Convertir une recette", "conv"),
                   ("Entretien & sécurité", "care"),
                   ("Index par ingrédient", "index")]:
        b.set_font("Lato", "", 8.6); b.set_text_color(*INK)
        b.text(128, ry, t)
        b.set_font("OswaldM", "", 8.4); b.set_text_color(*MUTED)
        num = str(ref.get(key, "·"))
        b.text(192 - b.get_string_width(num), ry, num)
        b.set_draw_color(*LINE); b.set_line_width(0.2)
        b.line(128, ry + 1.8, 192, ry + 1.8)
        ry += 8

    by = ry + 6
    b.set_fill_color(*GREEN); b.rrect(128, by, 64, 76, 2.5, fill=GREEN)
    b.set_font("OswaldM", "", 6.6); b.set_text_color(*ORANGE_L)
    b.tracked(133, by + 8, "VOS 3 BONUS", ("OswaldM", "", 6.6), ORANGE_L, 1.2)
    lines = [("1", "Tableau temps &", "températures"),
             ("2", "4 semaines de", "menus + courses"),
             ("3", "50 desserts à", "la friteuse")]
    yy = by + 16
    for n, a, c in lines:
        b.set_font("OswaldM", "", 7.4); b.set_text_color(*ORANGE_L)
        b.text(133, yy, n)
        b.set_font("Lato", "B", 7.4); b.set_text_color(*PAPER)
        b.text(138, yy, a)
        b.set_font("Lato", "", 7.4); b.set_text_color(*(198, 218, 206))
        b.text(138, yy + 4.2, c)
        yy += 13
    b.set_font("Lato", "I", 6.8); b.set_text_color(*(170, 195, 182))
    b.set_xy(133, by + 58)
    b.multi_cell(54, 3.4, "Fichiers PDF séparés, à imprimer\nou à garder sur le téléphone.")

    # bandeau de chiffres
    by2 = 238
    b.set_fill_color(*CREAM); b.rrect(18, by2, 174, 26, 2.5, fill=CREAM)
    for i, (n, lab) in enumerate([("365", "RECETTES"), ("9", "CHAPITRES"), ("3", "BONUS OFFERTS")]):
        cx = 18 + 29 + i * 58
        b.set_font("Oswald", "B", 20); b.set_text_color(*GREEN)
        b.text(cx - b.get_string_width(n) / 2, by2 + 13, n)
        b.set_font("OswaldM", "", 6.6); b.set_text_color(*MUTED)
        wd = b.get_string_width(lab)
        b.tracked(cx - wd / 2, by2 + 20, lab, ("OswaldM", "", 6.6), MUTED, 0.9)


# ---------------------------------------------------------------- pages texte
def text_page(b, kicker, title, blocks, plain=False):
    b.add_page()
    b.mark(title)
    y = 26
    b.tracked(18, y, kicker.upper(), ("OswaldM", "", 8.5), ORANGE, 2.2)
    y += 10
    b.set_font("Oswald", "B", 24); b.set_text_color(*GREEN)
    b.text(18, y, title)
    y += 4
    b.set_draw_color(*ORANGE); b.set_line_width(0.9)
    b.line(18, y, 46, y)
    y += 10
    for blk in blocks:
        kind = blk[0]
        if kind == "p":
            b.set_xy(18, y)
            b.set_font("Lato", "", 9.6); b.set_text_color(*INK)
            b.multi_cell(b.cw, 5.2, blk[1])
            y = b.get_y() + 5.4
        elif kind == "h":
            y += 7.4 if y > 40 else 2.0
            b.set_font("Oswald", "B", 10.8); b.set_text_color(*GREEN)
            b.tracked(18, y, blk[1].upper(), ("Oswald", "B", 10.8), GREEN, 0.5)
            y += 6.6
            b.set_y(y)
        elif kind == "plead":
            lead, rest = blk[1], blk[2]
            full = lead + " " + rest
            nlines = max(1, int(round(b.measure(full, b.cw - 0.5, ("Lato", "B", 9.4), 5.2) / 5.2)))
            b.set_xy(18, y)
            b.set_font("Lato", "B", 9.4); b.set_text_color(*GREEN)
            b.write(5.2, lead + " ")
            b.set_font("Lato", "", 9.4); b.set_text_color(*INK)
            b.write(5.2, rest)
            y = y + nlines * 5.2 + 5.0
            b.set_y(y)
        elif kind == "li":
            b.set_fill_color(*ORANGE)
            b.ellipse(19.2, y - 2.3, 1.5, 1.5, "F")
            b.set_font("Lato", "", 9.4); b.set_text_color(*INK)
            b.set_xy(24, y - 3.6)
            b.multi_cell(b.cw - 6, 5.2, blk[1])
            y = b.get_y() + 3.6
            b.set_y(y)
        elif kind == "bul":
            b.set_font("Lato", "B", 9.3); b.set_text_color(*GREEN)
            b.text(18, y, "•  " + blk[1])
            b.set_font("Lato", "", 9.3); b.set_text_color(*INK)
            b.set_xy(18 + b.get_string_width("•  " + blk[1]) + 1, y - 3.2)
            b.multi_cell(b.cw - 45, 4.8, blk[2])
            y = max(b.get_y(), y) + 1.6
            b.set_y(y)
        elif kind == "box":
            inner = blk[1]
            hh = b.measure(inner.replace("**", ""), b.cw - 16, ("Lato", "I", 9), 4.9) + 12
            b.set_fill_color(*TINT); b.rrect(18, y - 2, b.cw, hh, 2.5, fill=TINT)
            b.set_draw_color(*ORANGE); b.set_line_width(1.6)
            b.line(18, y - 2, 18, y - 2 + hh)
            b.set_xy(26, y + 4)
            b.multi_cell(b.cw - 16, 4.9, inner.replace('**', ''))
            y += hh + 6
            b.set_y(y)
        elif kind == "gap":
            y += blk[1]
            b.set_y(y)
    return y


RULES = [
    ("Préchauffez 3 minutes", "Un panier froid saisit mal. Le préchauffage à vide crée la croûte dès la première minute."),
    ("Séchez ce que vous cuisez", "L'eau cuit à la vapeur, l'air chaud cuit par contact. Épongez viandes, légumes et poissons."),
    ("Une seule couche", "Deux couches, c'est déjà trop. Deux fournées valent mieux qu'une seule ratée."),
    ("Une cuillère d'huile, pas un litre", "L'huile sert à dorer, pas à frire. Au pinceau ou en spray, elle suffit."),
    ("Secouez à mi-cuisson", "Le dessus de l'aliment ne dore pas tout seul. Secouez ou retournez une fois."),
    ("Salez au bon moment", "Légumes : avant. Viandes : au repos. Fromage : jamais deux fois."),
    ("Ne dépassez pas la ligne MAX", "Au-delà, l'air circule mal et rien ne croustille. C'est la règle la plus ignorée."),
    ("Le sucre brûle avant la viande", "Marinade au miel, laque, sauce barbecue : toujours en fin de cuisson."),
    ("Les temps sont indicatifs", "1500 W et 1800 W ne cuisent pas pareil. La montre repère, le thermomètre juge."),
    ("Vérifiez à cœur les viandes", "Poulet 75 °C, porc 63 °C, bœuf 55 °C. Un thermomètre à 10 € remplace tous les doutes."),
    ("Nettoyez entre deux usages", "Un panier sale fume, conduit mal la chaleur et donne un goût de brûlé."),
    ("Notez vos réglages", "Votre friteuse n'est pas la mienne. Le meilleur réglage est celui que vous avez noté."),
]


def rules_part(b):
    b.chapter_name = "Les 12 règles d'or"
    b.part_label = "Le guide"
    b.add_page()
    b.mark("Les 12 règles d'or")
    b.tracked(18, 26, "AVANT DE COMMENCER", ("OswaldM", "", 8.5), ORANGE, 2.2)
    b.set_font("Oswald", "B", 24); b.set_text_color(*GREEN)
    b.text(18, 40, "Les 12 règles d'or")
    b.set_draw_color(*ORANGE); b.set_line_width(0.9); b.line(18, 45, 46, 45)
    b.set_xy(18, 54)
    b.set_font("Lato", "", 9.4); b.set_text_color(*(60, 58, 52))
    b.multi_cell(b.cw, 4.9, "90 % des recettes ratées à la friteuse à air ne viennent pas de la recette, "
                            "mais de l'une de ces douze erreurs. Elles prennent cinq minutes à lire et "
                            "changent définitivement le résultat.")

    for i, (t, d) in enumerate(RULES):
        col, row = i // 6, i % 6
        x = 18 + col * 90
        y = 82 + row * 32
        b.set_font("Oswald", "B", 22); b.set_text_color(*(238, 226, 208))
        b.text(x, y + 2, f"{i+1:02d}")
        b.set_font("Lato", "B", 8.6); b.set_text_color(*GREEN)
        b.text(x + 13, y - 4.5, hyph(t))
        b.set_xy(x + 13, y + 0.5)
        b.set_font("Lato", "", 8.2); b.set_text_color(*(72, 68, 60))
        b.multi_cell(72, 4.2, hyph(d))

    # encadré de synthèse
    y = 272
    b.set_fill_color(*GREEN); b.rrect(18, y - 18, 174, 17, 2.5, fill=GREEN)
    b.set_xy(26, y - 13)
    b.set_font("Lato", "I", 9); b.set_text_color(*PAPER)
    b.multi_cell(160, 4.6, "La règle qui résume toutes les autres : si ça ne croustille pas, "
                           "c'est qu'il y avait trop d'air ou trop d'eau. Ajoutez du temps, retirez de la quantité.")


# ---------------------------------------------------------------- tableau t°/min
TEMP_ROWS = [
    ("PILONS DE POULET", "190–200 °C", "20–25 min", "Retourner à mi-cuisson"),
    ("HAUTS DE CUISSE", "190–200 °C", "22–28 min", "Peau vers le haut"),
    ("BLANCS DE POULET", "190 °C", "14–18 min", "Aplatir à 1,5 cm"),
    ("POULET ENTIER (1,2 kg)", "180 °C", "40–45 min", "Retourner une fois"),
    ("AILES DE POULET", "195–200 °C", "18–20 min", "Deux ou trois secouages"),
    ("STEAK HACHÉ", "200 °C", "8–10 min", "Ne pas presser"),
    ("BŒUF EN LAMELLES", "200 °C", "6–8 min", "Une seule couche"),
    ("RÔTI DE PORC", "180 °C", "30–35 min", "Repos de 8 min"),
    ("TRAVERS DE PORC", "175 °C", "35–40 min", "Sauce en fin"),
    ("CÔTELETTES D'AGNEAU", "200 °C", "8–12 min", "Selon l'épaisseur"),
    ("SAUCISSES", "180 °C", "15–18 min", "Piquer la peau"),
    ("SAUMON", "185–190 °C", "10–12 min", "Peau vers le bas"),
    ("CABILLAUD", "185–190 °C", "10–12 min", "Dos, pas de pavé"),
    ("CREVETTES", "190 °C", "5–8 min", "Dès qu'elles sont opaques"),
    ("THON", "200 °C", "6–8 min", "Resté rosé"),
    ("CALAMARS", "200 °C", "6–9 min", "Court et fort"),
    ("POISSON PANÉ", "195 °C", "10–12 min", "Une seule couche"),
    ("FRITES MAISON", "200 °C", "18–22 min", "Rincer et sécher"),
    ("FRITES SURGELÉES", "200 °C", "15–18 min", "Ne pas décongeler"),
    ("PATATES DOUCES", "200 °C", "15–18 min", "Brunit vite"),
    ("POMMES DE TERRE GRENAILLE", "190 °C", "20–25 min", "Couper en deux"),
    ("Pommes de terre entières", "200 °C", "35–40 min", "Piquer la peau"),
    ("CHOU-FLEUR", "195 °C", "18–20 min", "Petits bouquets"),
    ("BROCOLI", "190 °C", "8–10 min", "Reste ferme"),
    ("ASPERSES", "190 °C", "7–9 min", "Séchées"),
    ("COURGETTES", "190 °C", "10–14 min", "Demi-rondelles épaisses"),
    ("POIVRONS", "200 °C", "12–14 min", "Peau vers le haut"),
    ("AUBERGINES", "190 °C", "16–20 min", "Huiler au pinceau"),
    ("OIGNONS", "185 °C", "18–20 min", "Garder la peau"),
    ("CHAMPIGNONS", "190 °C", "10–12 min", "Ne pas saler avant"),
    ("BROWNIES", "170 °C", "20–22 min", "Cœur tremblant"),
    ("CAKE", "165 °C", "30–35 min", "Cure-dent sec"),
    ("MUFFINS", "180 °C", "14–18 min", "Moules aux 2/3"),
    ("COOKIES", "175 °C", "9–11 min", "Souples à la sortie"),
    ("PAIN PERDU", "180 °C", "6–8 min", "Retourner"),
    ("NUGGETS SURGELÉS", "195 °C", "10–12 min", "Une seule couche"),
    ("CROISSANTS", "170 °C", "5–8 min", "Réchauffage"),
    ("PIZZA (petite)", "180 °C", "8–10 min", "Préchauffer 5 min"),
    ("GRILLADES DE LÉGUMES", "190 °C", "12–16 min", "Même taille"),
    ("HARICOTS VERTS", "190 °C", "8–10 min", "Séchés, entiers"),
    ("PETITS POIS SURGELÉS", "180 °C", "10–12 min", "Remuer à mi-cuisson"),
    ("POIREAUX", "185 °C", "12–15 min", "Tronçons de 3 cm"),
    ("MAÏS EN ÉPI", "190 °C", "12–15 min", "Beurré, emballé"),
    ("TOMATES CERISES", "180 °C", "8–10 min", "Elles éclatent"),
    ("HALLUMI", "190 °C", "8–10 min", "Sans marinade sucrée"),
    ("CROQUE-MONSIEUR", "180 °C", "6–8 min", "Beurre à l'extérieur"),
    ("PIZZA SURGELÉE", "180 °C", "10–12 min", "Format individuel"),
    ("PAIN GRATINÉ", "190 °C", "4–6 min", "Fromage au dernier moment"),
    ("CHÂTAIGNES", "190 °C", "15–20 min", "Inciser la peau"),
    ("POMMES RÔTIES", "180 °C", "15–18 min", "Évidées, au four"),
    ("BANANES RÔTIES", "180 °C", "8–10 min", "Avec la peau"),
    ("MERINGUES", "140 °C", "40–45 min", "Séchage lent"),
    ("CHOUX À LA CRÈME", "180 °C", "14–16 min", "Bien dorés"),
    ("TARTELETTES", "175 °C", "18–22 min", "Moule individuel"),
    ("BRIOCHES", "170 °C", "16–18 min", "Levain frais"),
]


def temp_table_part(b):
    b.chapter_name = "Tableau temps & températures"
    b.part_label = "Repères"
    for page_i in range(2):
        b.add_page()
        if page_i == 0:
            b.mark("Tableau temps & températures")
        y = 26
        if page_i == 0:
            b.tracked(18, y, "REPÈRES", ("OswaldM", "", 8.5), ORANGE, 2.2)
            y += 10
            b.set_font("Oswald", "B", 24); b.set_text_color(*GREEN)
            b.text(18, y, "Tableau temps & températures")
            y += 4
            b.set_draw_color(*ORANGE); b.set_line_width(0.9); b.line(18, y, 46, y)
            y += 7
            b.set_xy(18, y)
            b.set_font("Lato", "", 9.2); b.set_text_color(*MUTED)
            b.multi_cell(b.cw, 4.8, "Valeurs de référence pour une friteuse de 4 à 6 litres (1500–1800 W). "
                                    "Ajoutez 2 à 5 minutes si votre appareil est plus petit.")
            y = b.get_y() + 7
        else:
            y = 24

        b.set_fill_color(*GREEN); b.rect(18, y, b.cw, 8, "F")
        b.set_text_color(*PAPER); b.set_font("OswaldM", "", 8)
        b.text(21, y + 5.4, "ALIMENT")
        b.text(96, y + 5.4, "TEMPÉRATURE")
        b.text(126, y + 5.4, "DURÉE")
        b.text(156, y + 5.4, "REPÈRE")
        y += 8
        rows = TEMP_ROWS[28 * page_i: 28 * (page_i + 1)]
        ytop = y
        for i, (a, t, d, r) in enumerate(rows):
            if i % 2 == 0:
                b.set_fill_color(*CREAM); b.rect(18, y, b.cw, 6.6, "F")
            b.set_text_color(*INK); b.set_font("Lato", "B", 8.2)
            b.text(21, y + 4.4, hyph(a.upper()))
            b.set_font("Lato", "", 8.2); b.set_text_color(*GREEN)
            b.text(96, y + 4.4, hyph(t))
            b.set_font("Lato", "", 8.2); b.set_text_color(*INK)
            b.text(126, y + 4.4, hyph(d))
            b.set_text_color(*MUTED)
            b.text(156, y + 4.4, hyph(r))
            y += 6.6
        b.set_draw_color(*LINE); b.set_line_width(0.2)
        b.rect(18, ytop - 8, b.cw, 6.6 * len(rows) + 8)

        if page_i == 1:
            y += 9
            b.set_font("OswaldM", "", 7.8); b.set_text_color(*ORANGE)
            b.tracked(18, y, "LES 6 REPÈRES À CONNAÎTRE PAR CŒUR", ("OswaldM", "", 7.8), ORANGE, 1.6)
            y += 7.5
            reps = [("Poulet cuit", "75 °C à cœur"), ("Porc rosé", "63 °C à cœur"),
                    ("Bœuf saignant", "55 °C à cœur"), ("Frites croustillantes", "200 °C · 20 min"),
                    ("Gâteau réussi", "165 °C · 30 min"), ("Légumes croquants", "190 °C · 12 min")]
            for i, (k, v) in enumerate(reps):
                cx = 18 if i % 2 == 0 else 106
                cy = y + (i // 2) * 10.2
                b.set_fill_color(*CREAM); b.rrect(cx, cy, 86, 8.6, 1.8, fill=CREAM)
                b.set_font("Lato", "B", 8.2); b.set_text_color(*INK)
                b.text(cx + 4, cy + 5.7, hyph(k))
                b.set_font("OswaldM", "", 8.2); b.set_text_color(*ORANGE)
                b.text(cx + 82 - b.get_string_width(hyph(v)), cy + 5.7, hyph(v))
            y += 3 * 10.2 + 5
            b.set_fill_color(*TINT); b.rrect(18, y, b.cw, 19, 2.5, fill=TINT)
            b.set_fill_color(*ORANGE); b.rect(18, y, 1.8, 19, "F")
            b.set_xy(26, y + 4)
            b.set_font("Lato", "I", 8.6); b.set_text_color(*(60, 56, 48))
            b.multi_cell(b.cw - 16, 4.4,
                         "Notez au crayon, dans la marge de ce tableau, les valeurs qui marchent chez vous. "
                         "Au bout de deux semaines, vous n'aurez plus besoin de le consulter.")


# ---------------------------------------------------------------- recettes
ING_W = 50.0
GAP = 7.0
CW = 174.0


def _meta_pills(b, x, y, r):
    items = [f'{r["pers"]} pers.' if r["pers"] else "", r["time"], r["temp"]]
    items = [i for i in items if i and i.strip() not in ("—", "0 min")]
    cx = x
    for it in items:
        b.set_font("Lato", "B", 7.8)
        tw = b.get_string_width(hyph(it))
        pw = tw + 7.0
        b.set_fill_color(*(238, 230, 214)); b.rrect(cx, y, pw, 5.4, 1.6, fill=(238, 230, 214))
        b.set_text_color(*GREEN)
        b.text(cx + 3.5, y + 3.9, hyph(it))
        cx += pw + 2.6
    return cx


def card_height(b, r, w=CW):
    tw = w - 15
    th = b.measure(hyph(r["title"]), tw, ("Oswald", "B", 16.0), 6.6)
    head = th + 9.0
    ing_h = 0
    for ing in r["ing"]:
        ing_h += b.measure(hyph(ing), ING_W - 4.2, ("Lato", "", 8.5), 4.15) + 1.0
    steps_w = w - ING_W - GAP
    st_h = 0
    for st in r["steps"]:
        st_h += b.measure(hyph(st), steps_w - 4.6, ("Lato", "", 8.5), 4.15) + 1.1
    body = max(ing_h, st_h)
    tip_h = b.measure(hyph(r["tip"]), w - 24, ("Lato", "I", 8.0), 4.0) if r["tip"] else 0
    tip = (tip_h + 6.4 + 3.2) if r["tip"] else 0
    return head + 6.0 + body + tip + 2.6


def draw_card(b, r, x, y, w=CW):
    steps_w = w - ING_W - GAP
    # numéro + titre
    b.set_font("OswaldM", "", 8.2); b.set_text_color(*ORANGE)
    b.text(x, y + 3.4, f'{r["n"]:03d}')
    b.set_font("Oswald", "B", 16.0); b.set_text_color(*GREEN)
    b.set_xy(x + 13, y - 1.2)
    th = b.measure(hyph(r["title"]), w - 15, ("Oswald", "B", 16.0), 6.6)
    b.multi_cell(w - 15, 6.6, hyph(r["title"]), align="L")
    yy = y - 1.2 + th + 1.6
    _meta_pills(b, x + 13, yy, r)
    y2 = yy + 5.4 + 2.2
    b.rule(x, y2, w, LINE, 0.35)
    body = y2 + 2.6

    # ingrédients
    b.set_font("OswaldM", "", 6.9); b.set_text_color(*ORANGE)
    b.tracked(x, body + 3.4, "INGRÉDIENTS", ("OswaldM", "", 7.2), ORANGE, 1.2)
    iy = body + 8.4
    for ing in r["ing"]:
        b.set_fill_color(*ORANGE_L); b.ellipse(x + 0.5, iy - 1.5, 1.05, 1.05, "F")
        b.set_xy(x + 3.8, iy - 2.9)
        b.set_font("Lato", "", 8.5); b.set_text_color(*(45, 43, 38))
        b.multi_cell(ING_W - 4.2, 4.15, hyph(ing))
        iy = b.get_y() + 2.9 + 1.0

    # préparation
    sx = x + ING_W + GAP
    b.set_font("OswaldM", "", 6.9); b.set_text_color(*ORANGE)
    b.tracked(sx, body + 3.4, "PRÉPARATION", ("OswaldM", "", 7.2), ORANGE, 1.2)
    sy = body + 8.4
    for i, st in enumerate(r["steps"], 1):
        b.set_font("OswaldM", "", 7.4); b.set_text_color(*ORANGE)
        b.text(sx, sy + 1.5, f"{i}.")
        b.set_xy(sx + 4.6, sy - 2.9)
        b.set_font("Lato", "", 8.5); b.set_text_color(*(45, 43, 38))
        b.multi_cell(steps_w - 4.6, 4.15, hyph(st))
        sy = b.get_y() + 2.9 + 1.1
    body_end = max(iy, sy)

    # astuce
    if r["tip"]:
        tipy = body_end + 2.0
        tip_h = b.measure(hyph(r["tip"]), w - 24, ("Lato", "I", 8.0), 4.0)
        b.set_fill_color(*TINT); b.rrect(x, tipy, w, tip_h + 5.6, 1.8, fill=TINT)
        b.set_fill_color(*ORANGE); b.rect(x, tipy, 1.5, tip_h + 5.6, "F")
        b.set_font("OswaldM", "", 6.6); b.set_text_color(*ORANGE)
        b.text(x + 4.5, tipy + 4.2, "ASTUCE")
        b.set_xy(x + 20, tipy + 2.1)
        b.set_font("Lato", "I", 8.0); b.set_text_color(*(70, 62, 50))
        b.multi_cell(w - 24, 4.0, hyph(r["tip"]))
        body_end = tipy + tip_h + 5.6
    return body_end - y


def recs_titles(ci):
    path = os.path.join(DATA, CHAPTERS[ci][0])
    out = []
    for line in open(path, encoding="utf-8").read().splitlines():
        if line.strip():
            out.append(line.split("|")[0].strip())
    return out[:8]


def chapter_opener(b, ci, title, subtitle, image, n_rec, first, last, ref):
    b.chapter_name = title
    b.part_label = f"Chapitre {ci+1}"
    b.plain = True
    b.add_page()
    b.mark(hyph(title))
    b.plain = False
    b.folio[ci] = b.page_no()
    b.set_fill_color(*GREEN); b.rect(0, 0, 210, 128, "F")
    img = os.path.join(IMG, "book", BOOK_IMG.get(image, image))
    if os.path.exists(img):
        b.image(img, 0, 0, 210, 128)
    b.set_fill_color(*GREEN_D); b.rect(0, 96, 62, 10, "F")
    b.tracked(9, 102.8, f"CHAPITRE {ci+1:02d}", ("OswaldM", "", 9), ORANGE_L, 2.6)
    b.set_font("Oswald", "B", 30); b.set_text_color(*PAPER)
    t = hyph(title)
    if b.get_string_width(t) > 174:
        b.set_font("Oswald", "B", 24)
    b.text(18, 116, t)
    y = 150
    b.set_font("Playfair", "I", 15); b.set_text_color(*GREEN)
    b.text(18, y, hyph(subtitle))
    y += 11
    b.set_font("Lato", "", 9.2); b.set_text_color(*MUTED)
    b.text(18, y, hyph(f"{n_rec} recettes · numéros {first:03d} à {last:03d}"))
    b.set_draw_color(*ORANGE); b.set_line_width(1); b.line(18, y + 6, 52, y + 6)

    # texte d'ouverture
    para, ctip = CHAP_INTRO[ci]
    y += 16
    b.set_xy(18, y)
    b.set_font("Lato", "", 10.2); b.set_text_color(*(55, 53, 47))
    b.multi_cell(120, 5.4, para)
    y = b.get_y() + 12

    # au programme : 8 titres en 2 colonnes
    b.set_font("OswaldM", "", 7.4); b.set_text_color(*ORANGE)
    b.tracked(18, y, "AU PROGRAMME", ("OswaldM", "", 7.4), ORANGE, 1.4)
    y += 8
    shown = recs_titles(ci)[:6]
    for i, t in enumerate(shown):
        cx = 18 if i < 3 else 88
        cy = y + (i % 3) * 6.4
        b.set_font("OswaldM", "", 7.2); b.set_text_color(*ORANGE_L)
        b.text(cx, cy, "·")
        b.set_font("Lato", "", 8.8); b.set_text_color(*(70, 68, 62))
        b.text(cx + 3.4, cy, hyph(t if len(t) < 36 else t[:34] + "…"))
    y += 3 * 6.4 + 10

    # astuce du chapitre
    ty = min(y, 246)
    th = b.measure(hyph(ctip), 140, ("Lato", "I", 9.4), 4.9) + 14
    b.set_fill_color(*TINT); b.rrect(18, ty, 174, th, 2.5, fill=TINT)
    b.set_fill_color(*ORANGE); b.rect(18, ty, 2, th, "F")
    b.set_font("OswaldM", "", 7.2); b.set_text_color(*ORANGE)
    b.tracked(26, ty + 7, "LE CONSEIL DU CHAPITRE", ("OswaldM", "", 7.2), ORANGE, 1.2)
    b.set_xy(26, ty + 10.5)
    b.set_font("Lato", "I", 9.4); b.set_text_color(*(60, 56, 48))
    b.multi_cell(140, 4.9, hyph(ctip))


def recipes_part(b, chap_list, ref):
    """Remplissage au mieux : 2 à 4 recettes par page, espacement réparti."""
    TOP, BOTTOM, GAP = 20.0, 282.0, 8.5
    for ci, title, subtitle, image, recs in chap_list:
        chapter_opener(b, ci, title, subtitle, image, len(recs), recs[0]["n"], recs[-1]["n"], ref)
        b.add_page()
        pages, cur, used = [], [], 0.0
        for r in recs:
            h = card_height(b, r)
            add = h + (GAP if cur else 0.0)
            if cur and (used + add > BOTTOM - TOP or len(cur) == 4):
                pages.append(cur); cur, used = [], 0.0
                add = h
            cur.append((r, h)); used += add
        if cur:
            pages.append(cur)

        for pi, page in enumerate(pages):
            if pi:
                b.add_page()
            total = sum(h for _, h in page)
            free = (BOTTOM - TOP) - total
            n = len(page)
            gap = min(max(free / max(n, 1), GAP), 15.0) if n > 1 else 0
            extra = max(free - gap * n, 0)
            y = TOP + min(extra / 2, 9.0)
            for j, (r, h) in enumerate(page):
                if j:
                    b.set_draw_color(*LINE); b.set_line_width(0.2)
                    b.set_dash_pattern(dash=0.9, gap=1.4)
                    gy = y - gap / 2 - 0.6
                    b.line(18, gy, 192, gy)
                    b.set_dash_pattern()
                draw_card(b, r, 18, y)
                y += h + gap


# ---------------------------------------------------------------- annexes
MENUS = [
    ("SEMAINE 1 — Classiques", [
        ("Lundi", 1), ("Mardi", 24), ("Mercredi", 75), ("Jeudi", 168),
        ("Vendredi", 200), ("Samedi", 251), ("Dimanche", 300)]),
    ("SEMAINE 2 — Léger", [
        ("Lundi", 30), ("Mardi", 96), ("Mercredi", 178), ("Jeudi", 210),
        ("Vendredi", 258), ("Samedi", 305), ("Dimanche", 342)]),
    ("SEMAINE 3 — Famille", [
        ("Lundi", 12), ("Mardi", 84), ("Mercredi", 183), ("Jeudi", 214),
        ("Vendredi", 262), ("Samedi", 310), ("Dimanche", 350)]),
    ("SEMAINE 4 — Envie de changer", [
        ("Lundi", 41), ("Mardi", 100), ("Mercredi", 186), ("Jeudi", 222),
        ("Vendredi", 270), ("Samedi", 320), ("Dimanche", 360)]),
]


INGREDIENT_KEYWORDS = [
    "poulet", "bœuf", "porc", "agneau", "veau", "dinde", "canard", "saucisse", "merguez", "lardons",
    "jambon", "saumon", "cabillaud", "thon", "crevettes", "gambas", "calamars", "sardines", "maquereaux",
    "moules", "saint-jacques", "colin", "dorade", "truite", "lotte", "merlan", "lieu", "sole", "rouget",
    "pommes de terre", "patate douce", "courgette", "aubergine", "poivron", "tomate", "champignon",
    "chou-fleur", "brocoli", "carotte", "oignon", "poireau", "fenouil", "épinards", "betterave",
    "chocolat", "pomme", "banane", "citron", "fraise", "framboise", "cerises", "poire", "miel",
    "fromage", "chèvre", "mozzarella", "parmesan", "feta", "crème", "yaourt", "pâte feuilletée",
    "pâte brisée", "pâte sablée", "brick", "riz", "pâtes", "semoule", "pois chiches", "lentilles",
    "farine", "avoine", "noix", "amandes", "cacahuète",
]


def build_index(chap_list):
    by_ing, by_num = {}, {}
    for ci, title, subtitle, image, recs in chap_list:
        for r in recs:
            by_num[r["n"]] = r
            txt = " " + re.sub(r"[^a-z0-9 ]", " ", norm(" ".join(r["ing"] + [r["title"]]))) + " "
            for kw in INGREDIENT_KEYWORDS:
                k = re.sub(r"[^a-z0-9 ]", " ", norm(kw))
                if re.search(r"(?<![a-z])" + re.escape(k) + r"(?![a-z])", txt):
                    by_ing.setdefault(kw, []).append(r["n"])
    return by_ing, by_num


def menus_part(b, by_num):
    b.chapter_name = "Menus de la semaine"
    b.part_label = "Organisation"
    THEMES = [
        ("Semaine des classiques", "Les recettes qui marchent à tous les coups. Idéal pour commencer."),
        ("Semaine légère", "Poisson, légumes, cuissons courtes. Moins de gras, pas moins de goût."),
        ("Semaine famille", "Des plats qui rassasient, peu épicés, que les enfants mangent sans négocier."),
        ("Semaine du monde", "Pour sortir de la routine sans changer ses habitudes d'achat."),
    ]
    b.plain = True
    b.add_page()
    b.mark("4 semaines de menus")
    b.plain = False
    b.tracked(18, 26, "ORGANISATION", ("OswaldM", "", 8.5), ORANGE, 2.2)
    b.set_font("Oswald", "B", 26); b.set_text_color(*GREEN)
    b.text(18, 40, "4 semaines de menus")
    b.set_draw_color(*ORANGE); b.set_line_width(0.9); b.line(18, 45, 46, 45)
    b.set_xy(18, 54)
    b.set_font("Lato", "", 9.6); b.set_text_color(*(60, 58, 52))
    b.multi_cell(120, 5.0, "Vingt-huit dîners déjà choisis, avec leur numéro de recette, leur temps de "
                           "cuisson et leur température. Vous n'avez plus qu'à ouvrir la page.")
    img = os.path.join(IMG, "book", "ch-05.jpg")
    if os.path.exists(img):
        b.image(img, 0, 74, 210, 78)

    y = 166
    for ti, (name, desc) in enumerate(THEMES):
        b.set_font("Oswald", "B", 12.5); b.set_text_color(*GREEN)
        b.text(18, y, hyph(name))
        b.set_font("Lato", "", 8.8); b.set_text_color(*MUTED)
        b.text(18, y + 4.6, hyph(desc))
        y += 15
    b.set_fill_color(*TINT); b.rrect(18, y + 2, 174, 20, 2.5, fill=TINT)
    b.set_fill_color(*ORANGE); b.rect(18, y + 2, 1.8, 20, "F")
    b.set_xy(26, y + 7)
    b.set_font("Lato", "I", 8.8); b.set_text_color(*(60, 56, 48))
    b.multi_cell(160, 4.6, "Chaque numéro renvoie à une recette du guide. Si un plat ne plaît pas, "
                           "remplacez-le par une recette du même chapitre.")

    for pair in range(2):
        b.add_page()
        y = 26
        for k in range(2):
            wi = pair * 2 + k
            title, days = MENUS[wi]
            b.set_font("OswaldM", "", 7.6); b.set_text_color(*ORANGE)
            b.tracked(18, y, f"SEMAINE {wi+1}", ("OswaldM", "", 7.6), ORANGE, 1.6)
            b.set_font("Oswald", "B", 17); b.set_text_color(*GREEN)
            b.text(18, y + 9, hyph(title.split("—")[1].strip()))
            b.set_draw_color(*LINE); b.set_line_width(0.3)
            b.line(18, y + 13, 192, y + 13)
            yy = y + 22
            for day, num in days:
                rec = by_num.get(num)
                if not rec:
                    continue
                b.set_font("Oswald", "B", 8); b.set_text_color(*ORANGE)
                b.text(18, yy, f"{num:03d}")
                b.set_font("Lato", "B", 9); b.set_text_color(*MUTED)
                b.text(32, yy, day)
                b.set_font("Lato", "", 9.6); b.set_text_color(*INK)
                b.text(52, yy, hyph(rec["title"]))
                b.set_font("Lato", "", 8.2); b.set_text_color(*MUTED)
                b.text(150, yy, hyph(f'{rec["time"]} · {rec["temp"]}'))
                yy += 8.4
            y = yy + 14


def conversion_part(b):
    b.chapter_name = "Convertir une recette de four"
    b.part_label = "Pratique"
    text_page(b, "Pratique", "Convertir une recette de four", [
        ("p", "Toutes vos recettes de four fonctionnent à la friteuse à air. Il suffit d'appliquer "
              "deux corrections : moins de degrés, moins de temps."),
        ("h", "La règle de conversion"),
        ("li", "Température : retirez 20 °C à la température du four (180 °C au four donnent 160 °C à la friteuse)."),
        ("li", "Temps : retirez 25 % du temps (30 minutes ramenées à 22 minutes)."),
        ("li", "Contrôlez 5 minutes avant la fin : c'est là que tout se joue."),
        ("h", "Exemples concrets"),
        ("bul", "Four 180 °C / 40 min", "Friteuse 160 °C / 30 min"),
        ("bul", "Four 200 °C / 25 min", "Friteuse 180 °C / 18 min"),
        ("bul", "Four 220 °C / 15 min", "Friteuse 200 °C / 11 min"),
        ("h", "Les trois exceptions"),
        ("plead", "1. Les gâteaux.", "Ils ont besoin d'un moule et d'une chaleur douce : baissez encore de "
              "10 °C et couvrez d'une feuille d'aluminium si le dessus dore trop vite."),
        ("plead", "2. Les grosses pièces.", "Un rôti de 1,5 kg ne convertit pas comme une escalope : comptez "
              "2 minutes de plus par 500 g et vérifiez à cœur."),
        ("plead", "3. Les pâtes à choux et les pâtes levées.", "Elles gonflent : laissez toujours un tiers du "
              "panier libre, et ne les sortez jamais avant qu'elles soient bien dorées."),
        ("box", "À retenir : la conversion n'est jamais parfaite du premier coup. Notez le réglage qui a "
                "marché, et vous n'aurez plus jamais à réfléchir."),
    ])


def care_part(b):
    b.chapter_name = "Entretien & sécurité"
    b.part_label = "Pratique"
    text_page(b, "Pratique", "Entretien & sécurité", [
        ("h", "Nettoyage en 3 minutes"),
        ("li", "Débranchez et laissez refroidir complètement avant de retirer le panier."),
        ("li", "Le panier et la grille passent au lave-vaisselle si le fabricant le permet ; sinon, eau chaude, "
               "une goutte de liquide vaisselle, trempage de 10 minutes."),
        ("li", "Jamais de grattoir métallique ni d'éponge abrasive : le revêtement antiadhésif ne se répare pas."),
        ("li", "L'intérieur de l'appareil (résistance) se nettoie avec un chiffon humide, jamais immergé."),
        ("h", "Les odeurs"),
        ("p", "Après un poisson ou une friture, faites tourner l'appareil 5 minutes à 180 °C avec un fond "
              "d'eau et deux cuillères de vinaigre blanc. Rincez, séchez, c'est réglé."),
        ("h", "Sécurité : les 6 règles qui comptent"),
        ("li", "Ne posez jamais l'appareil contre un mur ou sous un meuble haut : il rejette de l'air chaud."),
        ("li", "Ne le remplissez jamais d'huile. Ce n'est pas une friteuse à bain."),
        ("li", "Ne couvrez jamais le panier avec du film plastique ou de l'aluminium pendant la cuisson."),
        ("li", "Ne faites pas cuire un aliment liquide (pâte à gâteau liquide sans moule) directement dans le panier."),
        ("li", "Débranchez systématiquement après usage, même pour 10 minutes."),
        ("li", "Nettoyez la résistance : les projections accumulées sont la première cause de fumée et d'incendie."),
        ("box", "Le réflexe qui sauve : si de la fumée noire apparaît, arrêtez l'appareil et laissez-le "
                "refroidir avec la porte fermée. N'ouvrez pas pour « voir » : l'air ravive les flammes."),
    ])


def index_part(b, by_ingredient, by_num):
    b.chapter_name = "Index par ingrédient"
    b.part_label = "Index"

    def open_page(suite=False):
        b.add_page()
        b.mark("Index par ingrédient", 0 if not suite else 1)
        if suite:
            b.set_font("OswaldM", "", 8); b.set_text_color(*ORANGE)
            b.tracked(18, 26, "INDEX PAR INGRÉDIENT · SUITE", ("OswaldM", "", 8), ORANGE, 1.6)
            return 40.0
        b.tracked(18, 26, "INDEX", ("OswaldM", "", 8.5), ORANGE, 2.2)
        b.set_font("Oswald", "B", 24); b.set_text_color(*GREEN)
        b.text(18, 40, "Index par ingrédient")
        b.set_draw_color(*ORANGE); b.set_line_width(0.9); b.line(18, 45, 46, 45)
        b.set_xy(18, 54)
        b.set_font("Lato", "", 9.2); b.set_text_color(*MUTED)
        b.multi_cell(b.cw, 4.8, "Retrouvez une recette à partir de ce qu'il y a dans votre réfrigérateur. "
                                "Les nombres renvoient aux numéros de recette, pas aux pages.")
        return 72.0

    items = sorted(by_ingredient.items())
    COL_W, GAP, X0, BOTTOM = 55.0, 4.5, 18.0, 282.0
    page_top = open_page()
    y = page_top
    col = 0
    for kw, nums in items:
        nums_txt = " · ".join(f"{n:03d}" for n in nums[:16])
        h1 = b.measure(hyph(kw), COL_W, ("Lato", "B", 8.8), 4.5)
        h2 = b.measure(nums_txt, COL_W, ("Lato", "", 7.5), 3.75)
        need = h1 + h2 + 2.4
        if y + need > BOTTOM:
            col += 1
            if col > 2:
                col = 0
                page_top = open_page(suite=True)
            y = page_top
        x = X0 + col * (COL_W + GAP)
        b.set_xy(x, y)
        b.set_font("Lato", "B", 8.8); b.set_text_color(*GREEN)
        b.multi_cell(COL_W, 4.5, hyph(kw))
        b.set_xy(x, b.get_y())
        b.set_font("Lato", "", 7.5); b.set_text_color(*MUTED)
        b.multi_cell(COL_W, 3.75, nums_txt)
        y = b.get_y() + 2.4


def back_cover(b):
    b.plain = True
    b.add_page()
    b.mark("Quatrième de couverture")
    b.plain = False
    b.set_fill_color(*GREEN); b.rect(0, 0, 210, 297, "F")

    img = os.path.join(IMG, "book", "ch-07.jpg")
    if os.path.exists(img):
        b.image(img, 0, 0, 210, 96)

    b.set_draw_color(*ORANGE_L); b.set_line_width(0.6)
    b.line(88, 118, 122, 118)
    b.set_font("Playfair", "BI", 21); b.set_text_color(*PAPER)
    t = "Il ne manquait que les réglages."
    b.text(105 - b.get_string_width(t) / 2, 136, t)

    b.set_font("Lato", "", 10); b.set_text_color(*(205, 224, 212))
    for i, l in enumerate(["365 recettes, 9 chapitres, un tableau de cuisson,",
                           "4 semaines de menus et un index par ingrédient."]):
        b.text(105 - b.get_string_width(l) / 2, 150 + i * 7, l)

    y = 176
    b.set_font("OswaldM", "", 7.4); b.set_text_color(*ORANGE_L)
    w = b.get_string_width("DANS CE GUIDE")
    b.tracked(105 - (w + 1.6 * 12) / 2, y, "DANS CE GUIDE", ("OswaldM", "", 7.4), ORANGE_L, 1.6)
    y += 10
    for n, t2 in [("365", "recettes avec temps, températures et astuces"),
                  ("9", "chapitres : viandes, poissons, légumes, desserts..."),
                  ("40", "aliments dans le tableau de cuisson à imprimer"),
                  ("4", "semaines de menus et dîners déjà choisis")]:
        b.set_font("Oswald", "B", 13); b.set_text_color(*ORANGE_L)
        b.text(40, y, n)
        b.set_font("Lato", "", 9.2); b.set_text_color(*PAPER)
        b.text(52, y, hyph(t2))
        y += 9.5

    b.set_font("Oswald", "B", 12); b.set_text_color(*ORANGE_L)
    t3 = "365 RECETTES · FRITEUSE À AIR"
    b.text(105 - b.get_string_width(t3) / 2, 272, t3)
    b.set_font("Lato", "I", 8); b.set_text_color(*(170, 195, 182))
    t4 = "Édition 2026 · Friteuse Facile"
    b.text(105 - b.get_string_width(t4) / 2, 279, t4)


# ---------------------------------------------------------------- assemblage
def build_main(chap_list):
    by_ing, by_num = build_index(chap_list)
    pages, ref = {}, {}
    for attempt in range(3):
        b = Book()
        b.set_title("365 Recettes pour Friteuse à Air — Le guide pratique")
        b.set_author("Friteuse Facile")
        b.set_subject("365 recettes testées avec temps et températures exacts")
        b.set_keywords("friteuse à air, air fryer, recettes, cuisine, guide")
        b.set_creator("Friteuse Facile")
        cover(b)
        copyright_page(b, ref)
        toc_page(b, pages, ref)
        b.folio["rules"] = b.page_no() + 1
        rules_part(b)
        b.folio["table"] = b.page_no() + 1
        temp_table_part(b)
        recipes_part(b, chap_list, ref)
        b.folio["menus"] = b.page_no() + 1
        menus_part(b, by_num)
        b.folio["conv"] = b.page_no() + 1
        conversion_part(b)
        b.folio["care"] = b.page_no() + 1
        care_part(b)
        b.folio["index"] = b.page_no() + 1
        index_part(b, by_ing, by_num)
        back_cover(b)
        new_pages = {k: v for k, v in b.folio.items() if isinstance(k, int)}
        new_ref = {k: v for k, v in b.folio.items() if isinstance(k, str)}
        same = (new_pages == pages and new_ref == ref)
        pages, ref = new_pages, new_ref
        print(f"  passe {attempt+1} : {b.page_no()} pages" + ("  (stable)" if same else ""))
        if same and attempt > 0:
            break
    out = os.path.join(OUT, "365-recettes-friteuse-a-air.pdf")
    b.output(out)
    print("  →", out, f"({os.path.getsize(out)//1024} Ko)")
    return out


# ---------------------------------------------------------------- bonus
def _bonus_header(b, title, sub):
    b.set_fill_color(*GREEN); b.rect(0, 0, 210, 40, "F")
    b.set_font("Oswald", "B", 20); b.set_text_color(*PAPER)
    b.text(18, 23, hyph(title))
    b.set_font("Lato", "", 9.2); b.set_text_color(*(200, 220, 208))
    b.text(18, 31, hyph(sub))


def bonus_tableau():
    b = Book()
    b.set_title("Bonus 1 — Tableau temps & températures")
    b.set_author("Friteuse Facile")
    b.chapter_name = "Bonus 1 · Tableau de cuisson"
    b.part_label = "Bonus"

    rows = TEMP_ROWS
    per_page, per_col = 28, 14
    pages = [rows[i:i + per_page] for i in range(0, len(rows), per_page)]

    REPERES = [("Poulet cuit", "75 °C", "À cœur, jamais avant. Un thermomètre règle la question."),
               ("Porc rosé", "63 °C", "À cœur, après 5 minutes de repos hors du panier."),
               ("Bœuf saignant", "55 °C", "À cœur. 60 °C pour une cuisson à point."),
               ("Frites croustillantes", "200 °C", "20 minutes, deux secouages, jamais deux couches."),
               ("Gâteau réussi", "165 °C", "30 minutes, cure-dent sec, moule beurré."),
               ("Légumes croquants", "190 °C", "12 minutes, séchés et huilés au pinceau.")]

    for pi, chunk in enumerate(pages):
        last = (pi == len(pages) - 1)
        b.add_page()
        if pi == 0:
            _bonus_header(b, "Tableau temps & températures",
                          "À imprimer et à coller sur la porte de votre friteuse.")
            b.set_font("Lato", "", 8.6); b.set_text_color(*MUTED)
            b.set_xy(18, 47)
            b.multi_cell(b.cw, 4.4, "Valeurs pour une friteuse de 4 à 6 litres (1500–1800 W). "
                                    "Ajoutez 2 à 5 minutes si votre appareil est plus petit.")
            top = 58
        else:
            b.set_font("OswaldM", "", 8); b.set_text_color(*ORANGE)
            b.tracked(18, 22, "TABLEAU TEMPS & TEMPÉRATURES · SUITE", ("OswaldM", "", 8), ORANGE, 1.6)
            top = 32

        bottom_used = top
        for c in range(2):
            x = 18 + c * 90
            part = chunk[c * per_col:(c + 1) * per_col]
            if not part:
                continue
            y = top
            b.set_fill_color(*GREEN); b.rect(x, y, 84, 8, "F")
            b.set_text_color(*PAPER); b.set_font("OswaldM", "", 7.4)
            b.text(x + 3, y + 5.4, "ALIMENT")
            b.text(x + 56, y + 5.4, "T°")
            b.text(x + 71, y + 5.4, "TEMPS")
            y += 8
            for i, (a, t, d, r) in enumerate(part):
                rh = 10.6
                if i % 2 == 0:
                    b.set_fill_color(*CREAM); b.rect(x, y, 84, rh, "F")
                b.set_text_color(*INK); b.set_font("Lato", "B", 7.6)
                nm = hyph(a.upper())
                if b.get_string_width(nm) > 51:
                    while b.get_string_width(nm) > 51 and len(nm) > 3:
                        nm = nm[:-1]
                    nm = nm.rstrip() + "…"
                b.text(x + 3, y + 4.3, nm)
                b.set_font("Lato", "", 7.4); b.set_text_color(*GREEN)
                b.text(x + 55, y + 4.3, hyph(t.replace("–", "-")))
                b.set_font("Lato", "", 7.4); b.set_text_color(*INK)
                b.text(x + 70, y + 4.3, hyph(d.replace(" min", "")))
                b.set_font("Lato", "I", 6.3); b.set_text_color(*MUTED)
                b.text(x + 3, y + 8.6, hyph(r))
                y += rh
            b.set_draw_color(*LINE); b.set_line_width(0.2)
            b.rect(x, top, 84, 8 + 10.6 * len(part))
            bottom_used = max(bottom_used, y)

        if False:
            y = bottom_used + 14
            b.set_font("OswaldM", "", 8); b.set_text_color(*ORANGE)
            b.tracked(18, y, "LES 6 REPÈRES À CONNAÎTRE PAR CŒUR", ("OswaldM", "", 8), ORANGE, 1.6)
            y += 8
            for i, (k, v, expl) in enumerate(REPERES):
                b.set_fill_color(*CREAM); b.rrect(18, y, 174, 18, 2.5, fill=CREAM)
                b.set_font("Lato", "B", 9.6); b.set_text_color(*INK)
                b.text(25, y + 6.4, hyph(k))
                b.set_font("Oswald", "B", 12); b.set_text_color(*ORANGE)
                b.text(186 - b.get_string_width(v), y + 7, v)
                b.set_font("Lato", "", 7.8); b.set_text_color(*MUTED)
                b.text(25, y + 13.6, hyph(expl))
                y += 21
            y += 2
            b.set_fill_color(*TINT); b.rrect(18, y, 174, 18, 2.5, fill=TINT)
            b.set_fill_color(*ORANGE); b.rect(18, y, 1.8, 18, "F")
            b.set_xy(26, y + 4)
            b.set_font("Lato", "I", 8.4); b.set_text_color(*(60, 56, 48))
            b.multi_cell(160, 4.4, "Imprimez cette page et collez-la sur la porte du frigo : au bout de dix "
                                   "jours, vous n'aurez plus besoin de la consulter.")

    # page des repères
    b.add_page()
    _bonus_header(b, "Les 6 repères à connaître par cœur",
                  "Ceux qu'on finit par retenir sans regarder le tableau.")
    y = 56
    for k, v, expl in REPERES:
        b.set_fill_color(*CREAM); b.rrect(18, y, 174, 26, 2.5, fill=CREAM)
        b.set_font("Lato", "B", 11); b.set_text_color(*INK)
        b.text(26, y + 10, hyph(k))
        b.set_font("Oswald", "B", 15); b.set_text_color(*ORANGE)
        b.text(186 - b.get_string_width(v), y + 11, v)
        b.set_font("Lato", "", 8.6); b.set_text_color(*MUTED)
        b.text(26, y + 19, hyph(expl))
        y += 30

    y += 4
    b.set_fill_color(*TINT); b.rrect(18, y, 174, 24, 2.5, fill=TINT)
    b.set_fill_color(*ORANGE); b.rect(18, y, 1.8, 24, "F")
    b.set_xy(26, y + 5.5)
    b.set_font("Lato", "I", 9); b.set_text_color(*(60, 56, 48))
    b.multi_cell(160, 4.7, "Imprimez cette page et collez-la sur la porte du frigo : au bout de dix jours, "
                           "vous n'aurez plus besoin de la consulter.")

    out = os.path.join(OUT, "bonus", "1-tableau-temps-et-temperatures.pdf")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    b.output(out)
    print("  →", out, f"({os.path.getsize(out)//1024} Ko)")


PREVOIR = [
    ("1 kg de pilons et hauts de cuisse", "400 g de saumon ou de cabillaud", "1 chou-fleur", "250 g de chocolat",
     "6 filets de colin", "500 g de pommes de terre"),
    ("500 g de crevettes", "4 escalopes de veau", "1 kg de légumes variés", "200 g de fromage frais",
     "1 pâte feuilletée", "500 g de fruits de saison"),
    ("1 poulet en morceaux", "500 g de bœuf haché", "1 kg de pommes de terre", "200 g de cheddar",
     "1 sachet de feuilles de brick", "500 g de pommes"),
    ("500 g de poulet", "400 g de thon frais", "200 g de saucisse", "1 brocoli",
     "250 g de flocons d'avoine", "500 g de bananes"),
]


def bonus_menus(chap_list):
    by_ing, by_num = build_index(chap_list)
    b = Book()
    b.set_title("Bonus 2 — 4 semaines de menus")
    b.set_author("Friteuse Facile")
    b.chapter_name = "Bonus 2 · Menus"
    b.part_label = "Bonus"

    b.add_page()
    _bonus_header(b, "4 semaines de menus",
                  "28 dîners déjà choisis, avec les courses de chaque semaine.")
    b.set_xy(18, 52)
    b.set_font("Lato", "", 9.6); b.set_text_color(*(60, 58, 52))
    b.multi_cell(150, 5.2, "Les numéros renvoient aux recettes du guide. Remplacez librement un plat par un "
                           "autre du même chapitre : la liste de courses se recalcule en relisant les "
                           "ingrédients de la recette.")
    y = 78
    for wi, (title, days) in enumerate(MENUS):
        b.set_fill_color(*CREAM); b.rrect(18, y, 174, 30, 2.5, fill=CREAM)
        b.set_font("OswaldM", "", 7.4); b.set_text_color(*ORANGE)
        b.tracked(26, y + 8, f"SEMAINE {wi+1}", ("OswaldM", "", 7.4), ORANGE, 1.4)
        b.set_font("Oswald", "B", 13); b.set_text_color(*GREEN)
        b.text(26, y + 16, hyph(title.split("—")[1].strip()))
        b.set_font("Lato", "", 8.4); b.set_text_color(*MUTED)
        b.text(26, y + 23, " · ".join(f"{n:03d}" for _, n in days))
        b.set_font("Lato", "", 8); b.set_text_color(*MUTED)
        b.text(150, y + 16, f"{len(days)} dîners")
        y += 35

    b.set_xy(18, y + 6)
    b.set_font("Lato", "I", 8.8); b.set_text_color(*MUTED)
    b.multi_cell(174, 4.8, "Les listes de courses des pages suivantes ne remplacent pas une vérification "
                           "dans votre cuisine : elles ne comptent que les ingrédients principaux.")

    for pair in range(2):
        b.add_page()
        y = 26
        for k in range(2):
            wi = pair * 2 + k
            title, days = MENUS[wi]
            b.set_font("OswaldM", "", 7.6); b.set_text_color(*ORANGE)
            b.tracked(18, y, f"SEMAINE {wi+1}", ("OswaldM", "", 7.6), ORANGE, 1.6)
            b.set_font("Oswald", "B", 17); b.set_text_color(*GREEN)
            b.text(18, y + 9, hyph(title.split("—")[1].strip()))
            b.set_draw_color(*LINE); b.set_line_width(0.3)
            b.line(18, y + 13, 192, y + 13)
            yy = y + 22
            for day, num in days:
                rec = by_num.get(num)
                if not rec:
                    continue
                b.set_font("Oswald", "B", 8); b.set_text_color(*ORANGE)
                b.text(18, yy, f"{num:03d}")
                b.set_font("Lato", "B", 9); b.set_text_color(*MUTED)
                b.text(32, yy, day)
                b.set_font("Lato", "", 9.6); b.set_text_color(*INK)
                b.text(52, yy, hyph(rec["title"]))
                b.set_font("Lato", "", 8.2); b.set_text_color(*MUTED)
                b.text(150, yy, hyph(f'{rec["time"]} · {rec["temp"]}'))
                yy += 8.4
            yy += 4
            b.set_font("OswaldM", "", 7.2); b.set_text_color(*ORANGE)
            b.tracked(18, yy, "À PRÉVOIR", ("OswaldM", "", 7.2), ORANGE, 1.4)
            yy += 6
            for i, it in enumerate(PREVOIR[wi]):
                cx = 18 + (i % 2) * 87
                cy = yy + (i // 2) * 5.2
                b.set_fill_color(*ORANGE_L); b.ellipse(cx, cy - 2.1, 1.2, 1.2, "F")
                b.set_font("Lato", "", 8.2); b.set_text_color(*(60, 58, 52))
                b.text(cx + 3.4, cy, hyph(it))
            y = yy + 3 * 5.2 + 12

    # page finale : méthode
    b.add_page()
    b.set_font("Oswald", "B", 17); b.set_text_color(*GREEN)
    b.text(18, 34, "Comment tenir quatre semaines")
    b.set_draw_color(*ORANGE); b.set_line_width(0.9); b.line(18, 39, 46, 39)
    y = 54
    for i, (k, t) in enumerate([
        ("Faites vos courses le dimanche", "Une semaine de dîners tient sur une seule liste."),
        ("Préparez les bases", "Marinades, légumes coupés, viandes séchées : 30 minutes le dimanche soir."),
        ("Congelez les portions", "Les recettes en sauce et les boulettes se congèlent très bien."),
        ("Gardez une place libre", "Un soir par semaine, finissez les restes : c'est le meilleur moyen de ne rien jeter."),
    ]):
        b.set_font("Oswald", "B", 22); b.set_text_color(*(238, 226, 208))
        b.text(18, y + 2, f"{i+1:02d}")
        b.set_font("Lato", "B", 9.6); b.set_text_color(*GREEN)
        b.text(31, y - 3, hyph(k))
        b.set_xy(31, y + 1.5)
        b.set_font("Lato", "", 9); b.set_text_color(*(70, 66, 58))
        b.multi_cell(150, 4.6, hyph(t))
        y += 26

    out = os.path.join(OUT, "bonus", "2-menus-4-semaines.pdf")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    b.output(out)
    print("  →", out, f"({os.path.getsize(out)//1024} Ko)")


def bonus_desserts(chap_list):
    recs = [r for (_, _, _, _, rs) in chap_list for r in rs if r["ch"] == 6][:50]
    b = Book()
    b.set_title("Bonus 3 — 50 desserts à la friteuse")
    b.set_author("Friteuse Facile")
    b.chapter_name = "Bonus 3 · Desserts"
    b.part_label = "Bonus"

    b.add_page()
    _bonus_header(b, "50 desserts à la friteuse", "Extraits du guide, classés par temps de cuisson.")
    b.set_xy(18, 50)
    b.set_font("Lato", "", 9.4); b.set_text_color(*(60, 58, 52))
    b.multi_cell(120, 5.0, "Un moule adapté, un préchauffage sérieux, un cure-dent pour vérifier : "
                           "les gâteaux à la friteuse sont plus moelleux qu'au four et cuisent en "
                           "moitié moins de temps.")
    b.add_page()
    pages, cur, used = [], [], 0.0
    for r in recs:
        h = card_height(b, r)
        if cur and used + h + 8.5 > 262:
            pages.append(cur); cur, used = [], 0.0
        cur.append((r, h)); used += h + 8.5
    if cur:
        pages.append(cur)
    for pi, page in enumerate(pages):
        if pi:
            b.add_page()
        y = 20.0
        for r, h in page:
            draw_card(b, r, 18, y)
            y += h + 10.0

    out = os.path.join(OUT, "bonus", "3-50-desserts.pdf")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    b.output(out)
    print("  →", out, f"({os.path.getsize(out)//1024} Ko)")


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    cl = chapters()
    RANGES = []
    for _, _, _, _, recs in cl:
        RANGES.append((recs[0]["n"], recs[-1]["n"]))
    globals()["RANGES"] = RANGES
    if what in ("all", "main"):
        print("Guide principal :")
        build_main(cl)
    if what in ("all", "bonus"):
        print("Bonus :")
        bonus_tableau()
        bonus_menus(cl)
        bonus_desserts(cl)
