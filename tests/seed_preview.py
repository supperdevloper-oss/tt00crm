#!/usr/bin/env python3
"""Seed a synthetic `crm_data.json` for the local preview only.

`crm_data.json` is git-ignored on purpose (it holds client data in production),
so a fresh sandbox has no data and `dev_server.py` cannot answer `api.php`.
This script writes a *fake* dataset (no real client ever) so the preview boots:

    python3 tests/seed_preview.py          # writes crm_data.json if missing
    python3 tests/seed_preview.py --force  # overwrite the existing one

Nothing here is ever committed: the file stays ignored.
"""
from __future__ import annotations

import json
import re
import sys
import time
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "crm_data.json"

AGENTS = ["Meryam", "AYA", "imane", "safa"]
STATUSES = ["Confirmé", "Confirmé", "Confirmé", "Rappel", "Annulé", ""]
LIVRAISONS = ["", "", "", "Expédier vers", "Livrée", "Retour"]
CLIENTS = [
    "Hajar El Amrani", "Salma Bennani", "Youssef Alami", "Khadija Ouazzani",
    "Omar Tazi", "Nadia Berrada", "Mehdi Chraibi", "Imane Sqalli",
    "Rachid Fassi", "Loubna Idrissi", "Sanaa Alaoui", "Amine Lahlou",
]
CITIES = ["Casablanca", "Rabat", "Marrakech", "Agadir", "Ait melloul", "Fes", "Tanger"]


def default_cities() -> list[dict]:
    """The city table the app itself falls back to (`Ld` inside index.html)."""
    text = (ROOT / "index.html").read_text(encoding="utf-8", errors="replace")
    start = text.find("Ld=[{")
    if start < 0:
        return [{"nom": c, "prix": 35} for c in CITIES]
    end = text.find("]", start)
    try:
        return json.loads(text[start + 3:end + 1])
    except json.JSONDecodeError:
        return [{"nom": c, "prix": 35} for c in CITIES]


def build() -> dict:
    now = int(time.time() * 1000)
    today = date.today()
    cities = default_cities()
    price_of = {c["nom"]: c["prix"] for c in cities}

    users = [{"id": 1, "username": "admin", "password": "paraveda2026",
              "role": "admin", "agent": "", "_u": now}]
    for i, agent in enumerate(AGENTS, start=2):
        users.append({"id": i, "username": agent, "password": "123456",
                      "role": "user", "agent": agent, "_u": now})

    catalog = [
        {"id": 1, "nom": "Slim Bio 60", "prix": 249, "achat": 90},
        {"id": 2, "nom": "Slim Bio 120", "prix": 399, "achat": 150},
        {"id": 3, "nom": "Detox Tea", "prix": 199, "achat": 70},
        {"id": 4, "nom": "Collagene Plus", "prix": 299, "achat": 110},
    ]

    orders = []
    base_id = 1700000000000001
    for i in range(32):
        day = today - timedelta(days=i % 8)
        product = catalog[i % len(catalog)]
        city = CITIES[i % len(CITIES)]
        status = STATUSES[i % len(STATUSES)]
        delivery = LIVRAISONS[i % len(LIVRAISONS)] if status == "Confirmé" else ""
        orders.append({
            "id": base_id + i,
            "dateCreation": day.isoformat(),
            "dateConfirmation": day.isoformat() if status == "Confirmé" else "",
            "statut": status,
            "remarques": "طلبية تجريبية للعرض" if i % 3 == 0 else "",
            "idCmd": "1",
            "nom": CLIENTS[i % len(CLIENTS)],
            "telephone": "0600%06d" % (i + 1),
            "ville": city,
            "adresse": "شارع محمد الخامس، رقم %d" % (10 + i),
            "qte": 1 + (i % 2),
            "prix": product["prix"],
            "produit": product["nom"],
            "livraison": delivery,
            "upsell": 0,
            "carousell": "",
            "agent": AGENTS[i % len(AGENTS)],
            "link": "",
            "carosellFlag": "",
            "originLead": "Facebook",
            "commission": price_of.get(city, 35),
            "fees": "",
            "livreur": "Digylog" if delivery else "",
            "tracking": ("S%08X" % (0x8363F49B + i)) if delivery in ("Livrée", "Retour") else "",
            "dateExp": day.isoformat() if delivery else "",
            "dateLiv": day.isoformat() if delivery == "Livrée" else "",
            "motif": "",
            "_u": now - i * 3600 * 1000,
            "_f": {"statut": now - i * 3600 * 1000},
        })

    return {
        "paraveda_users_v1": {"t": now, "d": users},
        "paraveda_orders_v5": {"t": now, "d": orders},
        "paraveda_villes_v2": {"t": now, "d": cities},
        "paraveda_catalog_v1": {"t": now, "d": catalog},
        "paraveda_agent_names_v1": {"t": now, "d": AGENTS},
        "paraveda_history_v1": {"t": now, "d": []},
    }


def main() -> int:
    force = "--force" in sys.argv
    if TARGET.exists() and not force:
        print(f"{TARGET.name} already exists — use --force to overwrite")
        return 0
    data = build()
    TARGET.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")),
                      encoding="utf-8")
    print("seeded %s: %d orders, %d users, %d cities (synthetic preview data)"
          % (TARGET.name, len(data["paraveda_orders_v5"]["d"]),
             len(data["paraveda_users_v1"]["d"]), len(data["paraveda_villes_v2"]["d"])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
