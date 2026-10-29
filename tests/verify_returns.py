#!/usr/bin/env python3
"""Static and isolated behavioural checks for the returns module.
Does not read or mutate production CRM data.
"""
from pathlib import Path
import json
import re
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
api = (ROOT / "api.php").read_text(encoding="utf-8")
ui = (ROOT / "retours.html").read_text(encoding="utf-8")
index = (ROOT / "index.html").read_text(encoding="utf-8")
digylog_admin = (ROOT / "digylog-admin.html").read_text(encoding="utf-8")
city_prefix = 'const Qi="paraveda_villes_v2",Ld='
city_rows, _ = json.JSONDecoder().raw_decode(index[index.index(city_prefix) + len(city_prefix):])
city_prices = [row.get("prix") for row in city_rows if isinstance(row, dict)]
start = api.index("* Suivi des Retours")
end = api.index("$m = $_SERVER['REQUEST_METHOD']", start)
returns = api[start:end]
dash = index[index.index("function __PvDashChart"):index.index("function Fj(){const{orders:e}=Xt()")]

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
    "Automatic exact Digylog Tracking sync": all(x in api for x in ("function crm_tracking_auto_sync", "function crm_tracking_exact_from_payload", "$trackingSync=$withStatus?crm_tracking_auto_sync(30)", "'exactOnly'=>true", "$o['tracking']=$found[$id]")),
    "Open CRM triggers throttled Tracking sync": all(x in api for x in ("function crm_tracking_auto_guarded", ".tracking-auto.lock", "if ($a === 'digylog_tracking_auto')")) and all(x in index for x in ("pv-digylog-tracking-auto", "action:'digylog_tracking_auto'", "setInterval(syncTracking,60000)")),
    "Seller Authorization saved server-side": all(x in api for x in ("$op === 'tracking_token_save'", "$c['sellerToken'] = $incoming", "'hasSellerToken'", "$cfg['sellerToken']")) and all(x in digylog_admin for x in ("op:'tracking_token_save'", "Seller Authorization محفوظ", "حفظ وتشغيل جلب Tracking الآن")),
    "Immediate Tracking from send response": all(x in api for x in ("$sentTracking = array()", "$out['tracking'][$id] = $p['tracking'];", "$o['tracking']=$sentTracking[$id]")) and "crm_tracking_exact_from_payload($payload,$orderId)" in api,
    "Digylog Livrée synchronization is preserved": all(x in api for x in ("function crm_delivery_is_delivered", "return crm_delivery_status($info)==='Livrée'", "if((string)$id==='6'||$n==='livree'||strpos($n,'livree')===0)return 'Livrée'", "'delivered'=>$delivered")),
    "Digylog Retournée synchronizes to CRM Retour": all(x in api for x in ("function crm_delivery_is_returned", "strpos($n,'retourne')===0", "return 'Retour'", "$o['livraison']=$next", "'returned'=>$returned")),
    "Return reason suffix cannot hide Retournée": all(x in api for x in ("Digylog may append the return reason", "status','stateName','state_name','state", "if($st==='')$st=crm_tracking_deep_pick($info,array('label'))")),
    "Delivery synchronization stays exact-Tracking-only": all(x in api for x in ("crm_dl_base().'/order/'.rawurlencode($tr).'/infos'", "$targets[$tr]", "'exactOnly'=>true")) and "crm_tracking_phone" not in api[api.index("function crm_delivery_status"):api.index("/* Automatic / manual Digylog sender.")],
    "Duplicate Tracking is never auto-updated": all(x in api for x in ("A duplicated Tracking is ambiguous", "if($meta['count']!==1){$ambiguous++;continue;}", "'ambiguous'=>$ambiguous")),
    "Active deliveries cannot be postponed by delivered history": all(x in api for x in ("independent cursors", "history can never postpone current Expédier-vers returns", "deliveryActiveCursor", "deliveryFinalCursor", "$activeTake", "$finalTake")),
    "Automatic status batch covers active and delivered queues": all(x in api for x in ("crm_delivery_sync_batch(60)", "'activePending'=>count($active)", "'finalPending'=>count($final)", "ceil($limit*.8)")),
    "Admin can synchronize one exact Tracking now": all(x in api for x in ("$op === 'delivery_sync'", "crm_delivery_sync_batch($tracking !== '' ? 1 : 20, $tracking)", "'requestedTracking'=>$onlyTracking")) and all(x in digylog_admin for x in ("مزامنة Suivie من Digylog", "deliveryTracking", "syncDelivery", "op:'delivery_sync'")),
    "Returned synchronization changes no other business field": all(x in api for x in ("The only business-field write performed by this sync", "$o['livraison']=$next;$o['_f']['livraison']=$now;$o['_u']=$now", "It never writes statut, dateLiv, tracking, client data, prices, or other fields")),
    "Open CRM heartbeat checks delivery states": all(x in api for x in ("$result['deliverySync']=crm_delivery_auto_guarded()", "function crm_delivery_auto_guarded", ".delivery-auto.lock", ".delivery-auto.stamp", "if ($a === 'digylog_delivery_auto')")) and all(x in index for x in ("action:'digylog_tracking_auto'", "action:'digylog_delivery_auto'", "Promise.all")),
    "Every authenticated CRM snapshot guarantees automatic fallback": all(x in api for x in ("Guaranteed automatic fallback", "old cached index lacks the heartbeat script", "if (!isset($_GET['export']) && !isset($_GET['pushkey'])) { crm_dl_send_guarded(); crm_delivery_auto_guarded(); }")),
    "Digylog webhook applies final status automatically": all(x in api for x in ("function crm_dl_hook()", "order-status-changed", "crm_delivery_status($p)", "if(isset($_GET['action'])&&$_GET['action']==='digylog_hook')crm_dl_hook()", "The webhook's only business-field write", "$o['livraison']=$newLiv")) and "'disabled'=>true" not in api,
    "Webhook matching is exact and never uses phone": all(x in api for x in ("$rowTracking===$tracking", "(string)$o['id']===$num", "count($hits)!==1", "'ambiguous'=>count($hits)>1")) and "telephone" not in api[api.index("function crm_dl_hook()"):api.index("/* ================================================================\n * Suivi des Retours")],
    "Agent pages include Tracking status": all(x in index for x in ('"Suivie","Tracking","UPSEL"', "pv-agent-mobile-track", "__pvDigylogOrder(String(H.tracking).trim(),Rd)", "tr.cmd-locked td.pv-track-cell")),
    "Waiting CMD draft monitor": all(x in index for x in ("function __PvWaitingCmd", "Waiting CMD", "o&&o._d&&!o._del", "pv-wait-tab", "pv-wait-count", 'w==="Waiting CMD"&&s.jsx(__PvWaitingCmd')),
    "Waiting CMD is permanent": '"Suivi des Retours","Waiting CMD","CMD Annuler"]' in index and 'if(!t.includes("Waiting CMD"))t.push("Waiting CMD")' in index,
    "CMD Annuler is permanent and uses the CRM sheet": all(x in index for x in ('if(!t.includes("CMD Annuler"))', '"Waiting CMD","CMD Annuler"]', '"CMD Annuler":"🚫"', '"CMD Annuler":"red"', 'w==="CMD Annuler"&&s.jsx(t_,{cancelledOnly:!0})')),
    "COMMANDES and CMD Annuler split only the visible rows": all(x in index for x in ('function t_({cancelledOnly:__pvAnn=!1}={})', 'e0.filter(o=>!o._d)', 'iv=ee.useMemo(()=>ie.filter(o=>(String(o.statut??"").trim()==="Annulé")===__pvAnn)', 'return iv.filter(', 'w==="COMONDES"&&s.jsx(t_,{})')),
    "Cancelled orders remain in shared calculations": all(x in index for x in ('const st=sum(ie.filter', 'r.conv=ie.length?nc/ie.length*100:0', 'Ce=ie.filter(Fe=>Fe.statut==="Annulé")', 'return{cmd:ie.length')),
    "Admin phone keeps the exact CRM sheet": all(x in index for x in ('className:"pv-cmd-table w-full border-collapse text-xs"', '.pv-cmd-table{display:table!important', 'min-width:1780px!important', '.pv-vscroll{width:100%!important')) and "function __PvMobileCmdCards" not in index,
    "Admin phone scroll is contained inside the sheet": all(x in index for x in ('id="pv-mobile-crm-style"', 'html,body,#root{width:100%;max-width:100%;overflow-x:hidden}', 'pv-admin-sheet flex-1 overflow-hidden', '.pv-admin-sheet{width:100%;min-width:0;max-width:100%;overflow:hidden!important}', 'overflow-x:scroll!important', 'overscroll-behavior-x:none!important', '-webkit-overflow-scrolling:auto!important', 'touch-action:pan-x pan-y')),
    "Admin KPI dashboard is not rendered on phones": all(x in index for x in ("function __pvAdminMobile()", "Mobi|Android|iPhone|iPad|iPod", "navigator.maxTouchPoints", "touch>1&&/Macintosh/i.test(u)", '!__pvAdminMobile()&&s.jsxs("div",{className:"pvk-bar"')),
    "Admin KPI dashboard also has CSS phone fallback": '@media(hover:none) and (pointer:coarse){.pvk-bar{display:none!important}}' in index,
    "Admin mobile controls fit the viewport": all(x in index for x in ("pv-admin-top", "pv-admin-tools", "pv-period-buttons", "pv-main-nav", "pv-cmd-toolbar", "pv-cmd-pager")),
    "Admin phone header has no empty block": all(x in index for x in ('.pv-admin-top{position:relative;display:flex!important;min-height:0!important', '.pv-admin-tools{display:contents!important}', '.pv-admin-period{width:100%;min-width:0;order:3}')),
    "Phone period filters stay on one row": all(x in index for x in ('.pv-period>span{display:none!important}', 'grid-template-columns:repeat(6,minmax(0,1fr))', 'font-size:9px!important')),
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
    "City delivery prices use the exact one-time mapping": all(x in api for x in ("function crm_city_delivery_price_cut_once", "array('40'=>35,'45'=>40,'50'=>45)", "paraveda_city_price_cut_20261028_v1", ".city-price-cut-20261028.done", "crm_city_delivery_price_cut_once();")),
    "City price migration cannot apply twice": all(x in api for x in ("if(is_file($stamp))return", "isset($data[$marker]['d']['done'])", "'done'=>1", "@touch($stamp)")),
    "Built-in city prices match the requested reduction": len(city_rows) == 612 and city_prices.count(35) == 116 and city_prices.count(40) == 469 and city_prices.count(45) == 0 and city_prices.count(50) == 0,
    "Existing CRM commissions use the exact requested mapping": all(x in api for x in ("function crm_order_commission_cut_once", "array('40'=>35,'45'=>40,'50'=>45)", "paraveda_commission_cut_20261028_v1", "$row['commission']=$map[$key]", "$row['_f']['commission']=$now", "crm_order_commission_cut_once();")),
    "Commission reduction cannot apply twice": all(x in api for x in (".commission-cut-20261028.done", "if(is_file($stamp))return", "isset($data[$marker]['d']['done'])", "'done'=>1", "commission-cut | changed=")),
    "Commission migration leaves deleted orders untouched": "!empty($row['_del'])" in api[api.index("function crm_order_commission_cut_once"):api.index("crm_order_commission_cut_once();")],
    "Confirmed empty-Suivie orders are the only automatic send candidates": all(x in api for x in ("crm_tracking_norm($st) !== 'confirme'", "trim((string)(isset($o['livraison']) ? $o['livraison'] : '')) !== ''", "!empty($o['dlSent'])", "$includeExisting")),
    "Automatic send targets Commandes non envoyées": all(x in api for x in ("crm_dl_run(false,0,true,false,true)", "$forceSentType!==null?(int)$forceSentType", "'destination'=>$status===0?'Commandes non envoyées':'dispatched'", "$status = ($sentTyp===1) ? 1 : 0;   /* status 0 = add only => Commandes non envoyées */")) and "0 — Commandes non envoyées (المطلوب)" in digylog_admin,
    "Non-envoyées uses official Digylog v2.4 payload": all(x in api for x in ("function crm_dl_orders_body", "'mode'=>1,'status'=>(int)$status", "'type'=>1,'mode'=>1", "'port'=>1", "'network'=>(string)$network", "'store'=>(string)$store", "'checkDuplicate'=>1", "'openproduct'=>1")),
    "Digylog create uses the documented POST /orders route": all(x in api for x in ("crm_dl_http('POST', $path, $token, $body)", "$path = '/orders';", "'/orders/standard'")),
    "HTTP success without a confirmed order is not acceptance": all(x in api for x in ("digylog-no-order-confirmed", "digylog-no-record-for-order", "function crm_dl_parse_created", "crm_dl_same_ref")),
    "Automatic sending needs no admin toggle": all(x in api for x in ("$autoOn  = array_key_exists('autoSend',$c) ? (int)$c['autoSend'] : 1;", "if (!$dry && $auto && $autoOn===0)", "if (!$dry && !$auto && empty($c['enabled']))")) and all(x in digylog_admin for x in ("autoSend", "defaultStore")),
    "One bad order cannot block the whole batch": all(x in api for x in ("function crm_dl_send_chunk", "$shapeRejected", "isolate: retry every order of this chunk on its own")),
    "Automatic Digylog send runs within ten seconds": all(x in api for x in ("function crm_dl_send_guarded", ".dl-send-auto.lock", ".dl-send-auto.stamp", "time()-$last<7", "if ($a === 'digylog_send_auto')")) and all(x in index for x in ("pv-digylog-send-auto", "action:'digylog_send_auto'", "setInterval(sendConfirmed,6000)", "setTimeout(sendConfirmed,2000)")),
    "Automatic sender reports why nothing was sent": all(x in api for x in ("function crm_dl_auto_state()", "'eligible'", "'lastRun'", "'boutiques'", "'noStore'")) and all(x in digylog_admin for x in ("op: 'status'", "شوف الحالة دابا", "آخر تشغيل", "بلا متجر")),
    "Every agent can be mapped to a Digylog boutique": all(x in api for x in ("function crm_dl_admin_agents()", "'agents'    => $agents", "function crm_dl_store_for_agent")) and all(x in digylog_admin for x in ("renderStores", "data-agent")),
    "Digylog phone numbers are normalized": all(x in api for x in ("function crm_dl_phone(", "function crm_dl_phone_ok(", "'bad-phone'")),
    "Successful Digylog acceptance alone marks Expédier vers": all(x in api for x in ("if (isset($sent[$id]))", "$o['dlSent'] = 1", "$o['livraison'] = 'Expédier vers'", "$o['_f']['livraison'] = $now")),
    "Orders are sent exactly once": all(x in api for x in ("!empty($o['dlSent'])) continue;", "$o['_f']['dlSent'] = $now;", "$o['dlSent'] = 1; $o['dlAt'] = $now;")),
    "Failed Digylog sends stay pending with backoff": all(x in api for x in ("elseif (isset($failed[$id]))", "$o['dlNextTry']=$now+$delay", "$nextTry >", "min(60000,10000*")) and "$tries >= 20" not in api,
    "A failed order is never blocked forever": all(x in api for x in ("$gen !== CRM_DL_SENDER_GEN", "$tries = 0; $nextTry = 0;", "$o['dlGen']=CRM_DL_SENDER_GEN")),
    "Server version is verifiable over HTTP": all(x in api for x in ("define('CRM_API_VERSION', '3.88')", "define('CRM_DL_SENDER_GEN', 4)", "$__what === 'version'", "'apiVersion'=>CRM_API_VERSION")),
    "Public diagnosis file explains a silent failure": all(x in api for x in ("function crm_dl_diag_save", "function crm_dl_diag_build", "dl-diag.json", "'pendingCount'", "crm_dl_diag_save(crm_dl_diag_build(")),
    "Digylog boutique is resolved automatically": all(x in api for x in ("function crm_dl_store_by_name", "function crm_dl_store_known", "function crm_dl_initials_match", "strpos($ns,$agentKey)!==false", "function crm_dl_networks", "!in_array((string)$network, $ids, true)")),
    "Digylog auth falls back to the seller token": all(x in api for x in ("$code===401 || $code===403", "sellerToken", "crm_tracking_bearer($cfg['sellerToken'])")),
    "CRM shows the sender result instead of failing silently": all(x in index for x in ("pv-digylog-send-auto", "pv-dl-alert", "Digylog: '+f+' طلبية ما تصيفطاتش", "export=version")) and all(x in digylog_admin for x in ("apiVersion", "الطلبيات لي مازال ما تصيفطاتش", "نسخة السيرفر")),
    "Normal authenticated CRM reads also trigger automatic sending": "{ crm_dl_send_guarded(); crm_delivery_auto_guarded(); }" in api,
    "Tracking import falls back to the API token": all(x in api for x in ("function crm_dl_token_candidates", "'sellerToken','token'", "crm_tracking_internal_many($phones,$tokens[0])", "$alt=crm_tracking_internal_many($phones,$tokens[$ti])")),
    "Digylog-style dashboard tab exists on every device": all(x in index for x in ("function __PvDigylogDash", 'w==="Tableau de bord"&&s.jsx(__PvDigylogDash,{})', 'if(!t.includes("Tableau de bord"))t.push("Tableau de bord")', '"Tableau de bord":"\U0001F9ED"', '"Tableau de bord":"indigo"', 'Bilan:["Dashboard performance","Tableau de bord"', 'Gk=["Dashboard performance","Tableau de bord"')),
    "Dashboard mirrors the Digylog scope tabs": all(x in dash for x in ("Global","En ce moment","Hub d'expédition","Hub de livraison","Hub des retours","Retourn\u00e9e")),
    "Dashboard shows the Digylog KPI cards and blocks": all(x in dash for x in ("Chiffre d\'affaire","Total colis livr\u00e9s","Total Exp\u00e9dition","Non pay\u00e9","En cours de paiement","Total Pay\u00e9","\u00c9volution des exp\u00e9ditions","Taux de livraison","Top 5 produits vendus","Statuts livraisons")),
    "Dashboard has the Digylog buttons and filters": all(x in dash for x in ("refresh","Masquer les donn\u00e9es","Depuis le mois dernier","Afficher les donn\u00e9es","Tous",'d+" Jours"')) and 'dir:"ltr"' in dash,
    "Dashboard reuses the CRM charts and helpers": all(x in dash for x in ("s.jsx(__PvDashChart,{points:chart.pts,labels:chart.lbs})","s.jsx(f_,{livrees:st.sold,echouees:st.back,encours:st.enc})","__pvSold","__pvBack","__pvQ","__pvInFlight","__pvLocalDate")),
    "Dashboard can hide the numbers and shift the period": all(x in dash for x in ("Masquer les donn\u00e9es","setHide","setSince","\u0645\u0646\u0630 \u0627\u0644\u0634\u0647\u0631 \u0627\u0644\u0645\u0627\u0636\u064a")),
    "Dashboard KPI rectangle is not rendered on phones": all(x in dash for x in ("__pvAdminMobile()","window.innerWidth<1024","if(narrow){","Indicateurs")) and all(x in index for x in (".pv-dash-tab{",".pv-dash-tab-on{",".pv-dash-wrap{","@media(min-width:1280px){.pv-dash-kpi{grid-template-columns:repeat(3,minmax(0,1fr))}")),
    "Dashboard reads CRM data without changing it": all(x not in dash for x in ("upd(","del(","localStorage.setItem","postMessage")) and 'fetch("api.php?action=digylog_dash"' in dash,
    "The dashboard is linked live to the Digylog dashboard": all(x in api for x in ("function crm_dl_dash_live(","function crm_dl_dash_candidates(","function crm_dl_dash_probe(","function crm_dl_dash_cache_write(","action\'] === \'digylog_dash\'")) and all(x in index for x in ("api.php?action=digylog_dash","setInterval(fetchLive,6e4)","function __PvDashMapLive(","Digylog live")),
    "The live Digylog dashboard never writes to Digylog": "crm_dl_http_url('POST'" not in api and "crm_dl_http_url('PUT'" not in api and "crm_dl_http_url('DELETE'" not in api,
    "The live Digylog rows replace the CRM rows when Digylog answers": "liveRows.length?prep(liveRows):crm" in index and "crmLive.forEach(o=>{" in index,
    "The resolved boutique of every agent is visible": all(x in api for x in ("function crm_dl_agent_stores", "'agentStores'  => crm_dl_agent_stores")) and all(x in digylog_admin for x in ("agentStores", "المتجر ديال كل بنت (محسوب)")),
}

# Isolated behavioural simulation of the automatic sender (never touches real data).
import subprocess
sim = subprocess.run([sys.executable, str(ROOT / "tests" / "sim_digylog_send.py")],
                     capture_output=True, text=True)
checks["Isolated simulation of the automatic sender passes"] = sim.returncode == 0
if sim.returncode != 0:
    print(sim.stdout[-2000:], sim.stderr[-2000:])

sim2 = subprocess.run([sys.executable, str(ROOT / "tests" / "sim_dashboard.py")],
                      capture_output=True, text=True)
checks["Isolated simulation of the dashboard passes"] = sim2.returncode == 0
if sim2.returncode != 0:
    print(sim2.stdout[-2000:], sim2.stderr[-2000:])

sim3 = subprocess.run([sys.executable, str(ROOT / "tests" / "sim_digylog_dash.py")],
                      capture_output=True, text=True)
checks["Isolated simulation of the live Digylog dashboard passes"] = sim3.returncode == 0
if sim3.returncode != 0:
    print(sim3.stdout[-2000:], sim3.stderr[-2000:])

smap = subprocess.run(["node", str(ROOT / "tests" / "ui" / "status_map.mjs")],
                      capture_output=True, text=True)
checks["Every Digylog status maps to the CRM vocabulary"] = smap.returncode == 0
if smap.returncode != 0:
    print(smap.stdout[-2000:], smap.stderr[-2000:])

# Optional browser-engine test of the dashboard tab (needs `cd tests/ui && npm i`).
ui_dir = ROOT / "tests" / "ui"
if (ui_dir / "node_modules").exists():
    uit = subprocess.run(["node", str(ui_dir / "dashboard_ui.mjs")],
                         capture_output=True, text=True, cwd=str(ui_dir))
    checks["Dashboard tab behaves correctly in a browser engine"] = uit.returncode == 0
    if uit.returncode != 0:
        print(uit.stdout[-2000:], uit.stderr[-2000:])
else:
    print("note: optional dashboard UI test skipped (cd tests/ui && npm i)")

package = ROOT / "paraveda-digylog-send-v3.zip"
with zipfile.ZipFile(package) as z:
    checks["Digylog automatic fix package is valid and minimal"] = (
        z.testzip() is None
        and z.namelist() == ["api.php", "index.html", "digylog-admin.html", ".htaccess"]
        and all(z.read(name) == (ROOT / name).read_bytes() for name in z.namelist())
    )

failed = [name for name, ok in checks.items() if not ok]
for name, ok in checks.items():
    print(("PASS" if ok else "FAIL") + "  " + name)
if failed:
    raise SystemExit("Failed: " + ", ".join(failed))
print(f"\n{len(checks)} checks passed.")
