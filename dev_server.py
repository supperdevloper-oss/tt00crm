#!/usr/bin/env python3
"""Local development server for the exported Paraveda CRM.

Production uses api.php. The Arena preview environment does not ship PHP, so this
server provides the same basic GET/POST sync contract while serving static files.
Run with: python3 dev_server.py --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
import threading
import time
import unicodedata
from datetime import date
from email.utils import formatdate
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parent
DATA_FILE = ROOT / "crm_data.json"
LOCK = threading.RLock()
MAX_BODY = 24 * 1024 * 1024
SYNC_TOKEN = "8c907fc0f4ffe0b9775a6b7c3c0fc7700e5724c0d78343df"
ALLOWED_KEYS = {
    "paraveda_users_v1", "paraveda_orders_v5", "paraveda_dupok_v1",
    "paraveda_agent_names_v1", "paraveda_chat_v1", "paraveda_worktimes_v1",
    "paraveda_remarques_v1", "paraveda_avances_v1", "paraveda_adspend_v1",
    "paraveda_perfrows_v1", "paraveda_livraison_v1", "paraveda_history_v1",
    "paraveda_villes_v2", "paraveda_catalog_v1", "sheet_pièce",
    "paraveda_team_photos_v1", "tabs_list_v1", "custom_sheets_v1",
    "paraveda_period_v1", "paraveda_period_v2", "paraveda_backup_v1",
    "paraveda_backup_v1_agents",
}


def read_data() -> dict[str, Any]:
    with LOCK:
        try:
            value = json.loads(DATA_FILE.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"Cannot read {DATA_FILE.name}: {exc}") from exc
        if not isinstance(value, dict):
            raise RuntimeError(f"{DATA_FILE.name} must contain a JSON object")
        return value


def write_data(value: dict[str, Any]) -> None:
    payload = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    with LOCK:
        fd, temp_name = tempfile.mkstemp(prefix=".crm_data.", suffix=".tmp", dir=ROOT)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temp_name, DATA_FILE)
        finally:
            try:
                os.unlink(temp_name)
            except FileNotFoundError:
                pass


def encoded_snapshot() -> tuple[bytes, str]:
    payload = json.dumps(read_data(), ensure_ascii=False, separators=(",", ":")).encode()
    etag = '"' + hashlib.sha256(payload).hexdigest() + '"'
    return payload, etag


def normalized(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or "").strip().casefold())
    return "".join(char for char in text if not unicodedata.combining(char))


def pick(value: dict[str, Any], names: tuple[str, ...]) -> str:
    for name in names:
        item = value.get(name)
        if not isinstance(item, (dict, list)) and str(item or "").strip():
            return str(item).strip()
    return ""


def digylog_payload(event: dict[str, Any]) -> dict[str, Any]:
    payload = dict(event)
    for _ in range(3):
        nested = next(
            (payload.get(name) for name in ("payload", "data", "order")
             if isinstance(payload.get(name), dict) and payload[name]),
            None,
        )
        if nested is None:
            break
        for name in ("payload", "data", "order"):
            payload.pop(name, None)
        payload.update(nested)
    return payload


def apply_digylog_hook(event: dict[str, Any]) -> dict[str, Any]:
    if normalized(event.get("type")) == "subscribe" and "key" in event:
        return {"key": str(event["key"])}

    payload = digylog_payload(event)
    status = pick(payload, ("status", "statusName", "status_name", "orderStatus", "order_status", "label"))
    num = pick(payload, ("num", "orderNum", "order_num", "externalId", "external_id",
                         "externalReference", "external_reference", "reference", "ref",
                         "clientReference", "client_reference"))
    status_id = pick(payload, ("idStatus", "statusId", "status_id", "id_status"))
    digylog_id = pick(payload, ("idOrder", "orderId", "order_id", "id"))
    tracking = pick(payload, ("traking", "tracking", "trackingId", "tracking_id", "trackingNumber",
                              "tracking_number", "barcode"))
    if not (num or digylog_id or tracking):
        return {"ok": True, "ignored": "no-order-reference"}

    status_text = normalized(status)
    delivery = ""
    # Only the final returned state counts. "En cours ... retour" is still in transit.
    if any(word in status_text for word in ("retourne", "returned")):
        delivery = "Retournée"
    elif status_id == "6" or any(word in status_text for word in ("livr", "deliver", "distribu", "remis")):
        delivery = "Livrée"

    with LOCK:
        data = read_data()
        wrapper = data.get("paraveda_orders_v5", {})
        orders = wrapper.get("d", []) if isinstance(wrapper, dict) else []
        if not isinstance(orders, list):
            orders = []

        hit = -1
        matched_by = ""
        if num:
            for index, order in enumerate(orders):
                if isinstance(order, dict) and not order.get("_del") and str(order.get("id", "")) == num:
                    hit, matched_by = index, "num"
                    break
        digylog_refs = {value for value in (num, digylog_id) if value}
        if hit < 0 and digylog_refs:
            for index, order in enumerate(orders):
                if not isinstance(order, dict) or order.get("_del"):
                    continue
                for key in ("dlOrderId", "digylogId", "dlId", "dlNum"):
                    if str(order.get(key, "")) in digylog_refs:
                        hit, matched_by = index, key
                        break
                if hit >= 0:
                    break
        if hit < 0 and tracking:
            matches = [index for index, order in enumerate(orders)
                       if isinstance(order, dict) and not order.get("_del")
                       and str(order.get("tracking", "")).strip() == tracking]
            if len(matches) == 1:
                hit, matched_by = matches[0], "tracking"
        if hit < 0:
            return {"ok": True, "found": False, "num": num}

        now = int(time.time() * 1000)
        order = dict(orders[hit])
        fields = dict(order.get("_f", {})) if isinstance(order.get("_f"), dict) else {}
        order.update({"dlStatus": status, "dlStatusId": status_id, "dlStatusAt": now})
        fields.update({"dlStatus": now, "dlStatusId": now})
        if num:
            order["dlNum"] = num
            fields["dlNum"] = now
        if digylog_id:
            order["dlOrderId"] = digylog_id
            fields["dlOrderId"] = now
        if tracking and not str(order.get("tracking", "")).strip():
            order["tracking"] = tracking
            fields["tracking"] = now
        if delivery:
            order["livraison"] = delivery
            fields["livraison"] = now
            if delivery == "Livrée" and not str(order.get("dateLiv", "")).strip():
                order["dateLiv"] = date.today().isoformat()
                fields["dateLiv"] = now
        order["_f"] = fields
        order["_u"] = now
        orders[hit] = order
        data["paraveda_orders_v5"] = {"t": max(int(wrapper.get("t", 0)) + 1, now), "d": orders}
        write_data(data)
    return {"ok": True, "found": True, "matchedBy": matched_by, "livraison": order.get("livraison", "")}


class CRMHandler(SimpleHTTPRequestHandler):
    server_version = "ParavedaDev/1.0"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def end_headers(self) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        super().end_headers()

    def api_headers(self, status: int, length: int = 0, etag: str | None = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Sync-Token")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Date", formatdate(timeval=None, localtime=False, usegmt=True))
        if etag:
            self.send_header("ETag", etag)
        self.send_header("Content-Length", str(length))
        self.end_headers()

    def json_response(self, value: Any, status: int = HTTPStatus.OK) -> None:
        payload = json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode()
        self.api_headers(status, len(payload))
        self.wfile.write(payload)

    def do_OPTIONS(self) -> None:  # noqa: N802
        if self.path.split("?", 1)[0].endswith("/api.php"):
            self.api_headers(HTTPStatus.NO_CONTENT)
        else:
            super().do_OPTIONS()

    def do_GET(self) -> None:  # noqa: N802
        path = self.path.split("?", 1)[0]
        if path.endswith("/api.php"):
            try:
                payload, etag = encoded_snapshot()
                if self.headers.get("If-None-Match") == etag:
                    self.api_headers(HTTPStatus.NOT_MODIFIED, etag=etag)
                    return
                self.api_headers(HTTPStatus.OK, len(payload), etag)
                self.wfile.write(payload)
            except RuntimeError as exc:
                self.json_response({"ok": False, "error": str(exc)}, HTTPStatus.INTERNAL_SERVER_ERROR)
            return
        if path == "/":
            self.path = "/index.html"
        super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        request_url = urlsplit(self.path)
        if not request_url.path.endswith("/api.php"):
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        params = parse_qs(request_url.query)
        is_digylog_hook = params.get("action", [""])[0] == "digylog_hook"
        supplied_token = params.get("token", [""])[0] if is_digylog_hook else self.headers.get("X-Sync-Token", "")
        if supplied_token != SYNC_TOKEN:
            self.json_response({"ok": False, "error": "unauthorized"}, HTTPStatus.UNAUTHORIZED)
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            size = 0
        if size <= 0 or size > MAX_BODY:
            self.json_response({"ok": False, "error": "invalid body size"}, HTTPStatus.BAD_REQUEST)
            return
        try:
            body = json.loads(self.rfile.read(size))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self.json_response({"ok": False, "error": "invalid json"}, HTTPStatus.BAD_REQUEST)
            return
        if not isinstance(body, dict):
            self.json_response({"ok": False, "error": "invalid payload"}, HTTPStatus.BAD_REQUEST)
            return
        if is_digylog_hook:
            self.json_response(apply_digylog_hook(body))
            return
        if "action" in body:
            self.json_response(
                {"ok": False, "error": "This dev server supports key sync and the Digylog webhook only."},
                HTTPStatus.NOT_IMPLEMENTED,
            )
            return
        key = body.get("key")
        if key not in ALLOWED_KEYS or "d" not in body:
            self.json_response({"ok": False, "error": "invalid key or payload"}, HTTPStatus.BAD_REQUEST)
            return
        incoming_t = int(body.get("t") or int(time.time() * 1000))
        with LOCK:
            data = read_data()
            current = data.get(key)
            current_t = int(current.get("t", 0)) if isinstance(current, dict) else 0
            if incoming_t < current_t:
                self.json_response({"ok": True, "stale": True, "t": current_t})
                return
            effective_t = max(incoming_t, int(time.time() * 1000))
            data[key] = {"t": effective_t, "d": body["d"]}
            write_data(data)
        self.json_response({"ok": True, "t": effective_t})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Serve the Paraveda CRM locally")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), CRMHandler)
    print(f"Paraveda CRM preview: http://{args.host}:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
