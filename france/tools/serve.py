#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Serveur de prévisualisation pour la landing FR (dev uniquement).

    python3 tools/serve.py            # http://0.0.0.0:8080
    PORT=9000 python3 tools/serve.py

Sert le dossier `france/` à la racine : index.html → /, merci.html → /merci.html,
assets/ → /assets/... Aucun allowlist d'hôte, aucun en-tête d'iframe : la
prévisualisation Arena peut donc proxyfier le port tel quel.
"""
import os
import sys
import functools
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT = int(os.environ.get("PORT", sys.argv[1] if len(sys.argv) > 1 else 8080))

# Quelques types que le module `mimetypes` de certaines images Python ignore.
SimpleHTTPRequestHandler.extensions_map.update({
    ".woff2": "font/woff2",
    ".woff": "font/woff",
    ".webp": "image/webp",
    ".pdf": "application/pdf",
})


class PreviewHandler(SimpleHTTPRequestHandler):
    """Ajoute des en-têtes qui évitent les surprises de cache en prévisualisation."""

    # HTTP/1.1 = keep-alive : la page charge ses ~10 images sans rouvrir de socket.
    protocol_version = "HTTP/1.1"

    def end_headers(self):
        self.send_header("Cache-Control", "no-store, must-revalidate")
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()

    def do_GET(self):
        # / -> /index.html (comportement par défaut déjà géré) ; on log court.
        return super().do_GET()

    def log_message(self, fmt, *args):
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))


def main():
    handler = functools.partial(PreviewHandler, directory=ROOT)
    srv = ThreadingHTTPServer(("0.0.0.0", PORT), handler)
    print(f"Preview FR → http://0.0.0.0:{PORT}/  (racine : {ROOT})", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\narrêt", flush=True)
    finally:
        srv.server_close()


if __name__ == "__main__":
    main()
