#!/usr/bin/env python3
"""Construit les deux archives de mise en ligne depuis les sources de france/.

  LANDING-SOUS-DOSSIER.zip : tout sous un seul dossier « 365/ »
                             (à uploader dans public_html sans rien écraser)
  SITE-HOSTGATOR.zip       : fichiers à la racine (public_html vide uniquement)

Les fichiers référencés par les pages (images, polices, CSS) sont détectés
automatiquement : aucun asset oublié, aucun asset inutile embarqué.

Usage :  python3 tools/build-packs.py
"""
import io
import os
import re
import shutil
import zipfile

SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PAGES = [
    "index.html",
    "merci.html",
    "mentions-legales.html",
    "cgv.html",
    "confidentialite.html",
]

RE_ATTR = re.compile(r"""(?:href|src|srcset)\s*=\s*["']([^"']+)""")
RE_CSS = re.compile(r"""url\(\s*["']?([^)"']+)""")

LISEZ = """365 RECETTES POUR FRITEUSE A AIR - version 2,97 EUR
====================================================

CE DOSSIER CONTIENT
  1. La page de vente + la page de remerciement
  2. Trois pages legales deja redigees (mentions, CGV, confidentialite)
  3. Toutes les images et polices necessaires

DEJA CONFIGURE (ne pas toucher)
  - bouton d'achat  -> votre Gumroad
  - prix affiche    -> 2,97 EUR
  - marque          -> Friteuse Facile
  - cookies         -> le pixel Meta ne charge qu'apres "Accepter"

IL RESTE 2 CHOSES (ouvrez les fichiers avec un editeur de texte)
  1. Ctrl+F / Cmd+F -> "pixelId" : coller votre Meta Pixel ID entre
     les guillemets. Laisse vide = aucun pixel charge.

  2. Ctrl+F / Cmd+F -> "VOTRE" : remplacer les 3 champs dans les
     4 fichiers index.html, mentions-legales.html, cgv.html,
     confidentialite.html :
        [VOTRE NOM COMPLET]  ex. Ismail El Amrani
        [VOTRE ADRESSE]      ex. 12 rue Ibn Batouta, 20000 Casablanca, Maroc
        [VOTRE EMAIL]        ex. contact@easymeatrecipe.com

  N'INVENTEZ JAMAIS un numero SIRET, TVA ou ICE : c'est un delit.
  Votre identite reelle suffit, Gumroad est le vendeur contractuel.

UPLOAD (HostGator : cPanel > Gestionnaire de fichiers > public_html)
  Uploadez le dossier "365" ENTIER dans public_html.
  Resultat : public_html/365/index.html
  URL      : https://votre-domaine.com/365/

  NE TOUCHEZ PAS a votre index.html existant : il reste intact.

APRES L'UPLOAD
  - Gumroad > Settings > "Redirect after purchase" vers
    https://votre-domaine.com/365/merci.html
  - Pages legales : /365/mentions-legales.html  /365/cgv.html
                    /365/confidentialite.html
"""


def refs(*files):
    out = set()
    for f in files:
        s = io.open(os.path.join(SRC, f), encoding="utf-8").read()
        for m in RE_ATTR.findall(s) + RE_CSS.findall(s):
            for part in m.split(","):
                tok = part.split()[0] if part.split() else ""
                if tok.startswith("assets/") and not tok.endswith("/"):
                    out.add(tok)
    return sorted(out)


def build(dest, prefix, lisez_text):
    if os.path.isdir(dest):
        shutil.rmtree(dest)
    os.makedirs(dest, exist_ok=True)
    base = os.path.join(dest, prefix) if prefix else dest
    os.makedirs(base, exist_ok=True)
    for p in PAGES:
        shutil.copy2(os.path.join(SRC, p), os.path.join(base, p))
    missing = []
    for r in refs(*PAGES):
        src = os.path.join(SRC, r)
        if not os.path.exists(src):
            missing.append(r)
            continue
        d = os.path.join(base, r)
        os.makedirs(os.path.dirname(d), exist_ok=True)
        shutil.copy2(src, d)
    io.open(os.path.join(dest, "LISEZ-MOI.txt"), "w", encoding="utf-8").write(lisez_text)
    return missing


def zipit(srcdir, out):
    if os.path.exists(out):
        os.remove(out)
    n = 0
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for root, dirs, files in os.walk(srcdir):
            dirs.sort()
            for f in sorted(files):
                p = os.path.join(root, f)
                z.write(p, os.path.relpath(p, srcdir))
                n += 1
    return n, os.path.getsize(out)


def main():
    lisez_site = LISEZ.replace(
        'Uploadez le dossier "365" ENTIER dans public_html.\n'
        "  Resultat : public_html/365/index.html\n"
        "  URL      : https://votre-domaine.com/365/\n\n"
        "  NE TOUCHEZ PAS a votre index.html existant : il reste intact.",
        "Le CONTENU de ce dossier va a la RACINE de public_html.\n"
        "  A n'utiliser que si public_html est VIDE.\n"
        "  Si vous avez deja un site, prenez LANDING-SOUS-DOSSIER.zip.",
    )

    jobs = [
        ("/tmp/pack_sub", "365", LISEZ, "LANDING-SOUS-DOSSIER.zip", "sous-dossier"),
        ("/tmp/pack_site", "", lisez_site, "SITE-HOSTGATOR.zip", "site"),
    ]
    for dest, prefix, lisez, out, name in jobs:
        missing = build(dest, prefix, lisez)
        print("assets manquants (%-12s) : %s" % (name, missing or "aucun"))
        n, sz = zipit(dest, os.path.join(SRC, out))
        print("  -> %-26s %2d fichiers  %.2f Mo" % (out, n, sz / 1048576))


if __name__ == "__main__":
    main()
