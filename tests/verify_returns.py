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
digylog_admin = (ROOT / "digylog-admin.html").read_text(encoding="utf-8")
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
    "Returns tab cannot be deleted": 'tg=["COMONDES"' in index and '"Suivi des Retours"' in index and '"Waiting CMD","CMD Annuler"]' in index,
    "Ready-to-ship product summary": all(x in index for x in ("__pvProdAll", "pv-prod-sum", "pv-prod-list", "pv-prod-cols", "توزيع الكمية", "ملخص المنتجات الجاهزة للإرسال")),
    "Tracking opens live Digylog status": all(x in index for x in ("__pvDigylogOrder", "digylog_order_status", "pv-dl-status", "عرض Statut الحقيقي ديال الطلبية من Digylog")) and all(x in api for x in ("function crm_dl_order_status", "'/order/' . rawurlencode($tracking) . '/infos'", "tracking-not-in-crm", "if ($a === 'digylog_order_status')")),
    "Automatic exact Digylog Tracking sync": all(x in api for x in ("function crm_tracking_auto_sync", "function crm_tracking_exact_from_payload", "'trackingSync'=>crm_tracking_auto_sync(30)", "$trackingSync=crm_tracking_auto_sync(30)", "'exactOnly'=>true", "$o['tracking']=$found[$id]")),
    "Open CRM triggers throttled Tracking sync": all(x in api for x in ("function crm_tracking_auto_guarded", ".tracking-auto.lock", "if ($a === 'digylog_tracking_auto')")) and all(x in index for x in ("pv-digylog-tracking-auto", "action:'digylog_tracking_auto'", "setInterval(syncTracking,60000)")),
    "Seller Authorization saved server-side": all(x in api for x in ("$op === 'tracking_token_save'", "$c['sellerToken'] = $incoming", "'hasSellerToken'", "$cfg['sellerToken']")) and all(x in digylog_admin for x in ("op:'tracking_token_save'", "Seller Authorization محفوظ", "حفظ وتشغيل جلب Tracking الآن")),
    "Immediate Tracking from send response": all(x in api for x in ("$sentTracking = array()", "crm_tracking_exact_from_payload($j, $r['id'])", "$o['tracking']=$sentTracking[$id]")),
    "Agent pages include Tracking status": all(x in index for x in ('"Suivie","Tracking","UPSEL"', "pv-agent-mobile-track", "__pvDigylogOrder(String(H.tracking).trim(),Rd)", "tr.cmd-locked td.pv-track-cell")),
    "Waiting CMD draft monitor": all(x in index for x in ("function __PvWaitingCmd", "Waiting CMD", "o&&o._d&&!o._del", "pv-wait-tab", "pv-wait-count", 'w==="Waiting CMD"&&s.jsx(__PvWaitingCmd')),
    "Waiting CMD is permanent": '"Suivi des Retours","Waiting CMD","CMD Annuler"]' in index and 'if(!t.includes("Waiting CMD"))t.push("Waiting CMD")' in index,
    "CMD Annuler is permanent and uses the CRM sheet": all(x in index for x in ('if(!t.includes("CMD Annuler"))', '"Waiting CMD","CMD Annuler"]', '"CMD Annuler":"🚫"', '"CMD Annuler":"red"', 'w==="CMD Annuler"&&s.jsx(t_,{cancelledOnly:!0})')),
    "COMMANDES and CMD Annuler split only the visible rows": all(x in index for x in ('function t_({cancelledOnly:__pvAnn=!1}={})', 'e0.filter(o=>!o._d)', 'iv=ee.useMemo(()=>ie.filter(o=>(String(o.statut??"").trim()==="Annulé")===__pvAnn)', 'return iv.filter(', 'w==="COMONDES"&&s.jsx(t_,{})')),
    "Cancelled orders remain in shared calculations": all(x in index for x in ('const st=sum(ie.filter', 'r.conv=ie.length?nc/ie.length*100:0', 'Ce=ie.filter(Fe=>Fe.statut==="Annulé")', 'return{cmd:ie.length')),
    "Admin phone keeps the exact CRM sheet": all(x in index for x in ('className:"pv-cmd-table w-full border-collapse text-xs"', '.pv-cmd-table{display:table!important', 'min-width:1780px!important', '.pv-vscroll{overflow:auto!important')) and "function __PvMobileCmdCards" not in index,
    "Admin phone scroll is contained inside the sheet": all(x in index for x in ('id="pv-mobile-crm-style"', 'html,body,#root{width:100%;max-width:100%;overflow-x:hidden}', 'overscroll-behavior:contain', 'touch-action:pan-x pan-y')),
    "Admin KPI dashboard is not rendered on phones": all(x in index for x in ("function __pvAdminMobile()", "Mobi|Android|iPhone|iPad|iPod", "navigator.maxTouchPoints", "touch>1&&/Macintosh/i.test(u)", '!__pvAdminMobile()&&s.jsxs("div",{className:"pvk-bar"')),
    "Admin KPI dashboard also has CSS phone fallback": '@media(hover:none) and (pointer:coarse){.pvk-bar{display:none!important}}' in index,
    "Admin mobile controls fit the viewport": all(x in index for x in ("pv-admin-top", "pv-admin-tools", "pv-period-buttons", "pv-main-nav", "pv-cmd-toolbar", "pv-cmd-pager")),
    "Admin mobile preserves desktop pagination": '__pvSizes=[50,100,200,500,0]' in index and 'if(r===null||r==="")return 100' in index,
    "Agent phone workspace remains unchanged": 'function I2({agent:e})' in index and 's.jsx(I2,{agent:c.agent})' in index and 'cancelledOnly' not in index[index.index('function I2({agent:e})'):index.index('function __PvWaitingCmd',index.index('function I2({agent:e})'))],
    "Waiting CMD exit is permanently stamped": all(x in index for x in ("waitingExitedAt:Number(i.waitingExitedAt)||0", "waitingExitedDate:String(legacyExit?legacyDate:i.waitingExitedDate||", "waitingExitedBy:String(i.waitingExitedBy||", "waitingExitedAt:now,waitingExitedDate:exitDate,waitingExitedBy:exitBy")),
    "Waiting CMD exit snapshot survives later edits": all(x in index for x in ("waitingExitedStatus:String(i.waitingExitedStatus||", "waitingExitedProduct:String(i.waitingExitedProduct||", "waitingExitedQty:Number(i.waitingExitedQty)||", "waitingExitedAgent:String(i.waitingExitedAgent||", "waitingExitedClient:String(i.waitingExitedClient||", "waitingExitedPhone:String(i.waitingExitedPhone||")) and all(x in index for x in ("waitingExitedStatus:String(T.statut", "waitingExitedProduct:String(T.produit", "waitingExitedQty:Math.max(1,Number(T.qte)", "waitingExitedClient:String(T.nom")),
    "Waiting CMD legacy history matches CRM DATE filter": all(x in index for x in ("legacyDate=validDay(i.dateCreation)?String(i.dateCreation).slice(0,10)", "Number(i.waitingExitedLegacy)===1", 'String(i.waitingExitedBy||"")==="Historique avant filtre"', "!i._d&&!i._del", 'String(i.statut||"").trim()==="Confirmé"', "waitingExitedDate:String(legacyExit?legacyDate", 'legacyExit?"Historique avant filtre"', "waitingExitedLegacy:legacyExit?1:0")),
    "Waiting CMD history uses dedicated exit date": all(x in index for x in ("const [day,setDay]=ee.useState(today)", "exitDay(o)===day", 'type:"date",value:day==="all"?"":day', "Number(o.waitingExitedAt)||0", 'children:"البارح"', 'children:"جميع التواريخ"')),
    "Waiting CMD preparation summary and order detail": all(x in index for x in ("productSummary", "totalPieces", "pv-wait-qty-chip", "توزيع الكمية", "pv-wait-out-details", "وقت الخروج", 'String(o.waitingExitedStatus||"").trim()==="Confirmé"', "o.waitingExitedProduct||o.produit", "o.waitingExitedQty")),
    "Embedded module mode": "retours.html?embed=1" in index and "body.embedded .side{display:none}" in ui,
    "Digylog Chat removed completely": not (ROOT / "digylog-chat.html").exists() and all(x not in api for x in ("digylog_chat_", "crm_dl_chat", "Digylog Chat")) and all(x not in index for x in ("Digylog Chat", "digylog-chat.html", "pv-digylog-chat-launcher", "pv-dl-chat", "pv-chat-")),
    "CAROUSELL and FEES columns removed": all(x not in index for x in ('label:"CAROUSELL"', 'field:"carousell"', 'fkey:"carousell"', 'label:"FEES"', 'field:"fees"', 'fkey:"fees"')) and all(x in index for x in ('label:"Agent"', 'label:"CAROSELL"', 'label:"commision"')),
    "Menu buttons cannot trigger rename prompt": all(x not in index for x in ('onDoubleClick:()=>{C!=="Waiting CMD"&&X(C)}', "نقرة مزدوجة لإعادة التسمية", "الاسم الجديد:")),
    "Digylog config survives primary/mirror directory switches": all(x in api for x in ("function crm_dl_cfg_paths", "$DATA_DIR, $DIR_LOC, $DIR_EXT", "function crm_dl_cfg_merge_missing", "crm_dl_cfg_set($merged)", "LOCK_EX")),
    "Storeep intake is assigned only to Meryam": "$o['agent'] = 'Meryam';" in api and "crm_sheet_agents" not in api and "crm_rr_get" not in api and "crm_rr_set" not in api and "$agents[$rr % count($agents)]" not in api,
}

package = ROOT / "paraveda-admin-phone-table-final.zip"
with zipfile.ZipFile(package) as z:
    checks["Final admin phone-table package is valid and minimal"] = z.testzip() is None and z.namelist() == ["index.html"] and z.read("index.html") == (ROOT / "index.html").read_bytes()

failed = [name for name, ok in checks.items() if not ok]
for name, ok in checks.items():
    print(("PASS" if ok else "FAIL") + "  " + name)
if failed:
    raise SystemExit("Failed: " + ", ".join(failed))
print(f"\n{len(checks)} checks passed.")
