#!/usr/bin/env python3
"""Static and isolated behavioural checks for the returns module.
Does not read or mutate production CRM data.
"""
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]
api = (ROOT / "api.php").read_text(encoding="utf-8")
ui = (ROOT / "retours.html").read_text(encoding="utf-8")
index = (ROOT / "index.html").read_text(encoding="utf-8")
start = api.index("* Suivi des Retours")
end = api.index("$m = $_SERVER['REQUEST_METHOD']", start)
returns = api[start:end]

checks = {
    "API routes": all(x in api for x in ("returns_list", "returns_scan", "returns_control", "returns_restock")),
    "Exact Tracking field supported": "array('Tracking','tracking'" in returns,
    "Digylog QR resolves to existing exact Tracking": all(x in returns for x in ("crm_returns_resolve_qr_tracking", "digylog-exact", "digylog-qr-search-exact", "qr-tracking-unresolved", "resolved_tracking")),
    "Safe visible Tracking fallback": all(x in returns for x in ("visibleTracking", "operator-visible-exact", "canPairVisibleTracking")),
    "QR resolution performs no phone matching": "crm_tracking_phone" not in returns,
    "Unknown tracking rejected": "tracking-not-found" in returns,
    "Ambiguous tracking rejected": "tracking-ambiguous" in returns,
    "Duplicate reception rejected": "already-received" in returns,
    "Non-return requires override": "not-declared-return" in returns and "override-forbidden-or-reason-required" in returns,
    "Override restricted": "crm_returns_actor($b,$data,'override')" in returns,
    "Restock restricted": "crm_returns_actor($b,$data,'restock')" in returns,
    "Intact inspection required": "intact-control-required" in returns,
    "Duplicate restock rejected": "already-restocked" in returns,
    "Atomic write lock": "flock($fh,LOCK_EX)" in returns and "crm_write_all($data)" in returns,
    "Delivery status not written": not re.search(r"\[['\"]livraison['\"]\]\s*=", returns),
    "Delivery date not written": not re.search(r"\[['\"]dateLiv['\"]\]\s*=", returns),
    "UI camera scanner": all(x in ui for x in ("BarcodeDetector", "ParavedaZXingCpp", "tryHarder", "tryDenoise", "cameraBtn", "photoInput", "cppRead")),
    "Digylog label scanner targets linear Tracking": "formats:['Code128','Code39','Code93','EAN13','EAN8','ITF','Codabar']" in ui and "'qr_code'" not in ui,
    "Mobile opens scanner top-level": 'C==="Suivi des Retours"&&window.matchMedia("(max-width:1050px)").matches' in index,
    "UI filtering and pagination": all(x in ui for x in ("carrierFilter", "employeeFilter", "dateFilter", "prevBtn", "nextBtn")),
    "UI CSV and Excel export": "exportCsv" in ui and "exportExcel" in ui,
    "UI live refresh": "setInterval(()=>{if(!document.hidden&&!scanLock)load(true)},4000)" in ui,
    "CRM navigation integration": "Suivi des Retours" in index and 'w==="Suivi des Retours"&&s.jsx("iframe"' in index,
    "Returns tab cannot be deleted": '"LIVRAISON","Suivi des Retours"]' in index,
    "Ready-to-ship product summary": all(x in index for x in ("__pvProdAll", "pv-prod-sum", "pv-prod-list", "pv-prod-cols", "توزيع الكمية", "ملخص المنتجات الجاهزة للإرسال")),
    "Tracking opens live Digylog status": all(x in index for x in ("__pvDigylogOrder", "digylog_order_status", "pv-dl-status", "عرض Statut الحقيقي ديال الطلبية من Digylog")) and all(x in api for x in ("function crm_dl_order_status", "'/order/' . rawurlencode($tracking) . '/infos'", "tracking-not-in-crm", "if ($a === 'digylog_order_status')")),
    "Automatic exact Digylog Tracking sync": all(x in api for x in ("function crm_tracking_auto_sync", "function crm_tracking_exact_from_payload", "'trackingSync'=>crm_tracking_auto_sync(30)", "$trackingSync=crm_tracking_auto_sync(30)", "'exactOnly'=>true", "$o['tracking']=$found[$id]")),
    "Immediate Tracking from send response": all(x in api for x in ("$sentTracking = array()", "crm_tracking_exact_from_payload($j, $r['id'])", "$o['tracking']=$sentTracking[$id]")),
    "Agent pages include Tracking status": all(x in index for x in ('"Suivie","Tracking","UPSEL"', "pv-agent-mobile-track", "__pvDigylogOrder(String(H.tracking).trim(),Rd)", "tr.cmd-locked td.pv-track-cell")),
    "Embedded module mode": "retours.html?embed=1" in index and "body.embedded .side{display:none}" in ui,
}

package = ROOT / "paraveda-crm-retours.zip"
with zipfile.ZipFile(package) as z:
    checks["Package is valid and minimal"] = z.testzip() is None and set(z.namelist()) == {"api.php"}

failed = [name for name, ok in checks.items() if not ok]
for name, ok in checks.items():
    print(("PASS" if ok else "FAIL") + "  " + name)
if failed:
    raise SystemExit("Failed: " + ", ".join(failed))
print(f"\n{len(checks)} checks passed.")
