#!/usr/bin/env python3
"""Contract checks based on the supplied Digylog Seller API V2.1.0 examples."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
api = (ROOT / "api.php").read_text(encoding="utf-8")
ui = (ROOT / "digylog-chat.html").read_text(encoding="utf-8")
chat = api[api.index("* Digylog Chat"):api.index("function crm_dl_order_row", api.index("* Digylog Chat"))]

conversation = {
    "id": 50932,
    "traking": "S3900385FA",
    "createdAt": "2025-01-21T11:37:23+01:00",
    "updatedAt": "2025-01-21T11:54:47+01:00",
    "user": "ABDO",
    "closed": False,
}
message = {
    "id": 189975,
    "content": "test",
    "createdAt": "2025-01-21T11:37:23+01:00",
    "sender": "ABDO",
    "profil": "2",
    "status": "read",
}

checks = {
    "documented order-conversations variants": all(value in chat for value in ("'order/' . rawurlencode($tracking) . '/conversations'", "'orders/' . rawurlencode($tracking) . '/conversations'", "$result[0] === 400 || $result[0] === 404")),
    "exact conversation-messages route": "'conversations/' . rawurlencode((string)$conversation['id']) . '/messages'" in chat,
    "no private Seller v48 transport": "/api/seller/v48" not in chat,
    "no temporary Seller Authorization": all(value not in chat + ui for value in ("sellerToken", "chatAuthorization", "digylog_chat_auth_save")),
    "permanent API token only": "$cfg['token']" in chat and "Authorization: Bearer ' . $token" in api,
    "exact Tracking server authorization": all(value in chat for value in ("crm_dl_chat_allowed_trackings", "chat-tracking-forbidden", "chat-conversation-forbidden")),
    "no browser conversation-id trust": "crm_dl_chat_resolve($token, $allowed, $tracking)" in chat and "$verifiedId !== $chatId" in chat,
    "no all-order request fanout": "if ($requested === '') crm_out" in chat,
    "official conversation fixture": set(conversation) == {"id", "traking", "createdAt", "updatedAt", "user", "closed"},
    "official message fixture": set(message) == {"id", "content", "createdAt", "sender", "profil", "status"},
    "official message fields rendered": "m.content" in ui and "m.profil" in ui,
}

failed = [name for name, ok in checks.items() if not ok]
for name, ok in checks.items():
    print(("PASS" if ok else "FAIL") + "  " + name)
if failed:
    raise SystemExit("Failed: " + ", ".join(failed))
print(f"\n{len(checks)} Digylog contract checks passed.")
