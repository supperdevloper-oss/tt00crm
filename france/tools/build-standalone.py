#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Construit une version AUTONOME de la landing : un seul fichier HTML
qui contient les images, les polices et le CSS (data: URI).

    /tmp/v3/bin/python tools/build-standalone.py

Sortie : france/GUIDE-UN-FICHIER.html  (~1,3 Mo)
Aucun dossier assets/ à téléverser : on remplace uniquement index.html.
"""
import base64
import io
import os
import re

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "index.html")
OUT = os.path.join(ROOT, "GUIDE-UN-FICHIER.html")

# (largeur max, qualité) — les aperçus du livre sont réduits : ils s'affichent en petit.
RULES = {
    "assets/img/hero-flatlay.jpg": (1100, 80),
    "assets/img/dish-poulet.jpg": (900, 80),
    "assets/img/dish-saumon.jpg": (900, 80),
    "assets/img/dish-brownie.jpg": (900, 80),
    "assets/img/four-plat.jpg": (900, 80),
    "assets/img/dish-plats.jpg": (900, 80),
    "assets/img/book/apercu-1.jpg": (820, 78),
    "assets/img/book/apercu-2.jpg": (820, 78),
    "assets/img/book/apercu-3.jpg": (820, 78),
    "assets/img/book/apercu-4.jpg": (820, 78),
    "assets/img/book/mockup-livre@520.png": (640, 88),
    "assets/img/book/mockup-livre.webp": (640, 88),
}


def data_uri(rel):
    """Retourne une data: URI optimisée pour un fichier de assets/."""
    path = os.path.join(ROOT, rel)
    if not os.path.exists(path):
        return None
    maxw, quality = RULES.get(rel, (1000, 80))
    im = Image.open(path)
    big = im.width > maxw
    if big:
        im = im.resize((maxw, round(im.height * maxw / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    if im.mode in ("RGBA", "LA", "P") or (im.mode == "P" and "transparency" in im.info):
        im.convert("RGBA").save(buf, "WEBP", quality=quality, method=6)
        mime = "image/webp"
    else:
        im.convert("RGB").save(buf, "WEBP", quality=quality, method=6)
        mime = "image/webp"
    raw = buf.getvalue()
    # si le WebP est plus lourd que l'original, on garde l'original
    orig = os.path.getsize(path)
    if not big and len(raw) >= orig:
        with open(path, "rb") as fh:
            raw = fh.read()
        mime = "image/png" if path.lower().endswith(".png") else "image/jpeg"
    b64 = base64.b64encode(raw).decode("ascii")
    print(f"  {rel:42} {orig/1024:7.1f} Ko -> {len(raw)/1024:7.1f} Ko")
    return f"data:{mime};base64,{b64}"


def main():
    html = open(SRC, encoding="utf-8").read()
    print("Images :")
    cache = {}
    for rel in sorted(set(re.findall(r"assets/[A-Za-z0-9_@./-]+", html))):
        if rel.endswith(".woff2"):
            buf = open(os.path.join(ROOT, rel), "rb").read()
            cache[rel] = "data:font/woff2;base64," + base64.b64encode(buf).decode()
            print(f"  {rel:42} {len(buf)/1024:7.1f} Ko (police)")
            continue
        uri = data_uri(rel)
        if uri is None:
            print(f"  !! ABSENT {rel}")
            continue
        cache[rel] = uri

    # 1) les <link rel="preload"> deviennent inutiles (tout est déjà dans le fichier)
    html = re.sub(r'\n?<link rel="preload"[^>]*>', "", html)

    # 2) le CSS légal est intégré en <style>, polices incluses en data:
    css_path = os.path.join(ROOT, "assets/css/legal.css")
    css = open(css_path, encoding="utf-8").read()
    for font in ("oswald-400", "oswald-500", "oswald-700"):
        rel = f"assets/fonts/web/{font}.woff2"
        css = css.replace(f"url('../fonts/web/{font}.woff2')", f"url({cache[rel]})")
    html = html.replace(
        '<link rel="stylesheet" href="assets/css/legal.css">',
        "<style>\n" + css + "\n</style>",
    )

    # 3) toutes les références assets/ -> data:
    for rel, uri in sorted(cache.items(), key=lambda kv: -len(kv[0])):
        html = html.replace(rel, uri)

    left = sorted(set(re.findall(r"assets/[A-Za-z0-9_@./-]+", html)))
    assert not left, f"références non résolues : {left}"

    open(OUT, "w", encoding="utf-8").write(html)
    print(f"\n{os.path.basename(OUT)} : {os.path.getsize(OUT)/1024/1024:.2f} Mo")


if __name__ == "__main__":
    main()
