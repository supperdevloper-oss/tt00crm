#!/usr/bin/env python3
"""Simulation of the live Digylog dashboard pipeline.

The CRM «Tableau de bord» mirrors the Digylog screen live:

    api.php?action=digylog_dash  ->  read-only Digylog call (server side)
                                 ->  rows normalised + KPIs extracted
    index.html __PvDigylogDash  ->  Digylog status -> CRM vocabulary
                                 ->  same scopes / KPIs / chart / Top 5

This script mirrors the server rules (row detection, normalisation, KPI
extraction) and the client mapping so a change in one of them is caught
without a PHP runtime.  The PHP source itself is checked by tests/phpcheck.py
and the client by tests/ui/status_map.mjs + tests/ui/dashboard_ui.mjs.
"""
import json
import os
import re
import sys
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = os.path.join(ROOT, "api.php")
INDEX = os.path.join(ROOT, "index.html")

FAILED = []


def check(name, ok, detail=""):
    print(("PASS  " if ok else "FAIL  ") + name + ("" if ok else "  -> " + str(detail)))
    if not ok:
        FAILED.append(name)


# --------------------------------------------------------------------------
# server side (mirrors api.php)
# --------------------------------------------------------------------------
ROW_KEYS = [
    "status", "statusName", "status_name", "orderStatus", "statut", "state", "stateName",
    "traking", "tracking", "trackingNumber", "barcode", "designation", "product",
    "productName", "total", "price", "amount", "createdAt", "dateCreation", "creationDate", "date",
]


def looks_row(r):
    if not isinstance(r, dict):
        return False
    return sum(1 for k in ROW_KEYS if k in r) >= 2


def is_row_list(v):
    if not isinstance(v, list) or not v:
        return False
    return looks_row(v[0])


def find_rows(json_obj, depth=0):
    if depth > 5 or not isinstance(json_obj, (dict, list)):
        return []
    if is_row_list(json_obj):
        return json_obj
    if isinstance(json_obj, dict):
        for v in json_obj.values():
            if is_row_list(v):
                return v
    for v in (json_obj.values() if isinstance(json_obj, dict) else json_obj):
        if isinstance(v, (dict, list)):
            r = find_rows(v, depth + 1)
            if r:
                return r
    return []


def pick(arr, keys):
    if not isinstance(arr, dict):
        return ""
    for k in keys:
        if k in arr and arr[k] not in ("", None):
            return arr[k]
    return ""


def num(arr, keys):
    v = pick(arr, keys)
    if v == "" or not isinstance(v, (int, float)):
        return 0.0
    return float(v)


def norm_date(v):
    s = str(v or "").strip()
    if not s:
        return ""
    m = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})", s)
    if m:
        return "%s-%02d-%02d" % (m.group(1), int(m.group(2)), int(m.group(3)))
    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})", s)
    if m:
        return "%s-%02d-%02d" % (m.group(3), int(m.group(2)), int(m.group(1)))
    return ""


def normalize_row(r):
    if not isinstance(r, dict):
        return None
    status = str(pick(r, ["statusName", "status_name", "orderStatus", "order_status", "statut",
                           "stateName", "state_name", "shippingStatus", "deliveryStatus",
                           "status", "state"]))
    track = str(pick(r, ["traking", "tracking", "trackingNumber", "tracking_number", "barcode"]))
    price = num(r, ["totalPrice", "total_price", "orderPrice", "order_price", "totalAmount",
                    "total_amount", "amountTTC", "amount", "price", "total", "montant", "totalTTC"])
    qty = int(num(r, ["totalQuantity", "total_quantity", "quantity", "qty", "qte",
                      "quantityTotal", "nbProducts"]))
    prod = str(pick(r, ["productName", "product_name", "designation", "libelle", "title",
                        "product", "article", "name"]))
    date = norm_date(pick(r, ["createdAt", "created_at", "creationDate", "creation_date",
                              "dateCreation", "date_creation", "createdDate", "orderDate", "date"]))
    if prod == "" and isinstance(r.get("articles"), list) and r["articles"]:
        a = r["articles"][0]
        if isinstance(a, dict):
            p2 = str(pick(a, ["designation", "libelle", "name", "title", "product"]))
            if p2:
                prod = p2
            if qty <= 0:
                qty = int(num(a, ["quantity", "qty", "qte"]))
    if status == "" and track == "" and price <= 0 and prod == "":
        return None
    return {"s": status, "t": track, "p": price, "q": qty if qty > 0 else 1, "n": prod, "d": date}


def normalize_rows(rows):
    out = []
    for r in rows:
        n = normalize_row(r)
        if n is not None:
            out.append(n)
        if len(out) >= 2000:
            break
    return out


def flatten(json_obj, out=None, depth=0):
    if out is None:
        out = {}
    if depth > 4 or not isinstance(json_obj, dict):
        return out
    for k, v in json_obj.items():
        if isinstance(v, dict):
            flatten(v, out, depth + 1)
        elif isinstance(v, (int, float)) and not isinstance(v, bool):
            out[k.lower()] = float(v)
    return out


KPI_DEFS = {
    "ca": ["ca", "chiffreaffaire", "chiffreaffaires", "chiffre_affaire", "turnover",
           "totalrevenue", "revenue", "totalca", "montanttotal", "totalamount", "sales"],
    "livre": ["livrees", "livre", "delivered", "totaldelivered", "nblivrees",
              "countdelivered", "deliveredcount", "totaldeliveredcount"],
    "exp": ["expeditions", "expedition", "shipped", "totalshipped", "nbexpeditions",
            "countexpeditions", "totalexpeditions", "shipments"],
    "paye": ["paye", "paid", "totalpaid", "montantpaye", "totalpaye"],
    "encours": ["encours", "encoursdepaiement", "inprogress", "totalencours", "pendingamount"],
    "nonpaye": ["nonpaye", "unpaid", "notpaid", "totalunpaid"],
    "rate": ["rate", "taux", "deliveryrate", "tauxlivraison", "successrate",
             "pourcentage", "tauxdelivraison"],
}


def extract_kpis(json_obj):
    flat = flatten(json_obj)
    out = {}
    for name, keys in KPI_DEFS.items():
        for k in keys:
            if k in flat:
                out[name] = flat[k]
                break
    return out


# --------------------------------------------------------------------------
# client side (mirrors __PvDashMapLive in index.html)
# --------------------------------------------------------------------------
def strip_accents(t):
    return "".join(c for c in unicodedata.normalize("NFD", t)
                   if unicodedata.category(c) != "Mn")


def map_status(s):
    t = strip_accents(str(s or "").lower())
    if not t:
        return ""
    if re.search(r"retour|retourn|rembours|refund|return", t):
        return "Retour"
    if re.search(r"out of stock|rupture", t):
        return "Out Of Stock"
    if re.search(r"rechange|exchange", t):
        return "Rechange"
    if "livree" in t and "*" in t:
        return "Rechange"
    if re.search(r"livree|livre(\s|$)|deliver", t):
        return "Livrée"
    if re.search(r"expedier vers|a expedier|a ship|non env|not sent|to ship|prepar", t):
        return "Expédier vers"
    if re.search(r"expedi|shipped|dispatch|envoy|transit|en route|en cours", t):
        return "Expédié"
    if re.search(r"annul|cancel", t):
        return "Annulé"
    return ""


def live_order(row):
    l = map_status(row.get("s"))
    return {"livraison": l, "statut": "Annulé" if l == "Annulé" else "Confirmé",
            "prix": float(row.get("p") or 0), "qte": int(row.get("q") or 1),
            "produit": str(row.get("n") or ""), "dateCreation": str(row.get("d") or ""),
            "commission": 0, "agent": ""}


def scope(lst, sc):
    if sc == "now":
        return [o for o in lst if o["livraison"] not in
                ("Livrée", "Rechange", "Retour", "Remboursé", "Out Of Stock") and o["statut"] != "Annulé"]
    if sc == "ship":
        return [o for o in lst if o["livraison"] in ("Expédier vers", "Expédié")]
    if sc == "liv":
        return [o for o in lst if o["livraison"] in ("Livrée", "Rechange")]
    if sc == "ret":
        return [o for o in lst if o["livraison"] == "Remboursé"]
    if sc == "ret2":
        return [o for o in lst if o["livraison"] == "Retour"]
    return lst


def main():
    api = open(API, encoding="utf-8").read()
    index = open(INDEX, encoding="utf-8").read()

    # ---- server plumbing -------------------------------------------------
    check("api.php exposes the live Digylog dashboard action",
          "action'] === 'digylog_dash'" in api and "function crm_dl_dash_live(" in api)
    check("api.php reads Digylog without writing to it",
          "crm_dl_http_url('GET'" in api and "crm_dl_http_url('POST'" not in api)
    check("api.php caches the live payload", "function crm_dl_dash_cache_write(" in api)
    check("api.php probes several read-only endpoints",
          all(x in api for x in ["/orders/grid", "/orders/statistics", "/orders/chart", "/dashboard"]))
    check("the api version is bumped", "CRM_API_VERSION', '3.89'" in api)

    # ---- client plumbing -------------------------------------------------
    check("the dashboard asks the server for the live Digylog dashboard",
          'api.php?action=digylog_dash' in index)
    check("the dashboard refreshes the live data every minute",
          "setInterval(fetchLive,6e4)" in index)
    check("the dashboard maps the Digylog statuses", "function __PvDashMapLive(" in index)
    check("the dashboard shows which source feeds the numbers",
          "Digylog live" in index and "liveRows.length" in index)
    check("the live rows replace the CRM rows when Digylog answers",
          "liveRows.length?prep(liveRows):crm" in index)
    check("the agent table stays on the CRM data", "crmLive.forEach(o=>{" in index)
    check("the client expects the new api version", "const EXPECTED='3.89'" in index)
    check("the client partitions the Digylog statuses by tab", "__PvDashDlGroup" in index and "non envoy" in index)
    check("the client draws one card per Digylog status", "__PvDashStatusLook" in index and "statusCard" in index)
    check("the probe tries every authentication style", all(x in api for x in ("crm_dl_dash_headers", "'xseller'", "'cookie'", "'xauthtok'")))
    check("the probe tries every host and version", "'https://apiseller.digylog.com'" in api and "'v49'" in api and "'v50'" in api)
    check("the working authentication is remembered", "'style' => $style" in api and "crm_dl_dash_cache_write(array('endpoint' => $used, 'style' => $style" in api)
    check("the server reads every page of the Digylog orders", "crm_dl_dash_get_pages" in api and "currentPage=" in api)
    check("the server also reads the Digylog statistics", "orders/statistics?datatype=1" in api and "'stats'" in api)
    check("the status card order follows Digylog", all(x in index for x in ("__PvDashStatusRank","cours de livraison","injoignable","report","ville","annul","refus")))

    # ---- row detection ----------------------------------------------------
    flat = [{"tracking": "T1", "status": "Livrée", "price": 100, "product": "P1", "date": "2026-10-20"}]
    check("a flat list of orders is detected", len(normalize_rows(find_rows(flat))) == 1)
    nested = {"data": {"orders": [{"traking": "T2", "statusName": "Expédié", "total": 200,
                                   "designation": "P2", "createdAt": "2026-10-21"}]}}
    check("a nested list of orders is detected", len(normalize_rows(find_rows(nested))) == 1)
    deep = {"result": {"data": [{"num": "T4", "status": "Livrée", "total": 400, "libelle": "P4",
                                 "dateCreation": "2026-10-23"}]}}
    check("a deeply nested list of orders is detected", len(normalize_rows(find_rows(deep))) == 1)
    check("a payload without orders is ignored", find_rows({"total": 3, "stats": {"ca": 10}}) == [])

    # ---- normalisation ----------------------------------------------------
    rows = normalize_rows(find_rows(nested))
    r = rows[0]
    check("the status is read", r["s"] == "Expédié", r)
    check("the tracking is read", r["t"] == "T2", r)
    check("the price is read", r["p"] == 200, r)
    check("the product is read", r["n"] == "P2", r)
    check("the date is normalised", r["d"] == "2026-10-21", r)
    art = normalize_rows(find_rows([{"status": "Livrée", "articles": [
        {"designation": "Sérum", "quantity": 3}], "total": 10}]))
    check("the product comes from the articles when needed",
          art and art[0]["n"] == "Sérum" and art[0]["q"] == 3, art)

    # ---- kpis -------------------------------------------------------------
    k = extract_kpis({"chiffreAffaire": 103692, "livrees": 559, "expeditions": 1076,
                       "paye": 96433, "encours": 4059, "nonpaye": 3200, "taux": 55})
    check("the Digylog KPI totals are extracted",
          k.get("ca") == 103692 and k.get("livre") == 559 and k.get("exp") == 1076
          and k.get("rate") == 55, k)
    k2 = extract_kpis({"statistics": {"ca": 1000, "delivered": 10, "shipped": 20, "rate": 50}})
    check("nested KPI totals are extracted",
          k2.get("ca") == 1000 and k2.get("livre") == 10 and k2.get("exp") == 20, k2)

    # ---- status mapping ---------------------------------------------------
    pairs = [("Livrée", "Livrée"), ("Livrée*", "Rechange"), ("Expédié", "Expédié"),
             ("Expédier vers", "Expédier vers"), ("À expédier", "Expédier vers"),
             ("Non envoyée", "Expédier vers"), ("En préparation", "Expédier vers"),
             ("Retournée", "Retour"), ("Remboursé", "Retour"), ("Returned", "Retour"),
             ("Out Of Stock", "Out Of Stock"), ("Rupture de stock", "Out Of Stock"),
             ("Annulée", "Annulé"), ("En cours de livraison", "Expédié"), ("Confirmé", "")]
    bad = [(i, map_status(i), e) for i, e in pairs if map_status(i) != e]
    check("every Digylog status maps to the CRM vocabulary", not bad, bad)

    # ---- live scopes ------------------------------------------------------
    sample = [
        {"s": "Livrée", "p": 100, "q": 1, "n": "A", "d": "2026-10-20"},
        {"s": "Expédié", "p": 200, "q": 1, "n": "B", "d": "2026-10-21"},
        {"s": "Retournée", "p": 300, "q": 1, "n": "A", "d": "2026-10-22"},
        {"s": "Expédier vers", "p": 400, "q": 1, "n": "C", "d": "2026-10-23"},
    ]
    live_orders = [live_order(x) for x in sample]
    check("the live global scope keeps every order", len(scope(live_orders, "global")) == 4)
    check("the live delivery scope keeps the delivered ones",
          len(scope(live_orders, "liv")) == 1)
    check("the live shipping scope keeps the parcels on the road",
          len(scope(live_orders, "ship")) == 2)
    check("the live returned scope keeps the returned ones",
          len(scope(live_orders, "ret2")) == 1)
    ca = sum(o["prix"] for o in live_orders)
    check("the live turnover is the sum of the Digylog amounts", ca == 1000, ca)

    print()
    if FAILED:
        print("%d live dashboard simulation checks FAILED: %s" % (len(FAILED), ", ".join(FAILED)))
        return 1
    print("All live dashboard simulation checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
