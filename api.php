<?php
/**
 * Paraveda CRM — api.php (v3.82)
 *
 * Contract used by index.html (unchanged):
 *   GET  api.php                       → { key: {t, d}, ... }
 *   POST api.php {key, t, d}           → {ok:true, t:<effective t>}   (header X-Sync-Token required)
 *
 * v3.101 — جميع طلبيات Storeep/الشيت الجداد كيتعيّنو لمريم فقط (server-enforced)
 * v3.99 — إشعار أوتوماتيك ملي تدخل/تتبدل طلبية باسم بنت (CRM + الشيت)
 * v3.98 — ID ديال طلبيات الشيت ديما = 1
 * v3.97 — الشيت → CRM: POST {action:'sheet_orders', rows:[...]} كيزيد الطلبيات الجداد
 *   (تكرار سيرفر-سايد: تاريخ + هاتف + منتوج). الجبد الكامل من CRM ما تبدلش.
 *
 * v3.82 — التسليك النهائي: تغيير الباسوورد كيوصل للسيرفر + يوزر ممسوح ما كيرجعش
 *   + المتصفح كيعاود يصيفط اليوزرز/الطلبيات إلا لقا السيرفر راهو رجع لنسخة قديمة.
 *   POST api.php {action: ...}         → Digylog actions  (header X-Sync-Token required)
 *
 * v3.81 — الإصلاح الجذري ديال "اليوزر الجديد كيتمسح من بعد لحضات":
 *   - journal replay ولى كيقارن الوقت: سطر قديم عمرُو ما كيقدر يتربح على داتا أحدث
 *     منه (v3.80 كانت كتطبق آخر سطر ديما — سطر قديم فـ journal الميرا كان كيمسح
 *     اليوزرز/الطلبيات فكل قرية).
 *   - قرية الملفات: primary + mirror كيتدمجو مفتاح بمفتاح (الأحدث كيربح)، واليوزرز
 *     كيتوحّدو بالـ id — ملف قديم فـ أي بلاصة ما بقاش كيخبي يوزرز.
 *   - t ديال أي مفتاح ما كينقصش عمرو (noop:same كان كيرجّع الوقت للور مع ساعة
 *     متأخرة → الأجهزة الأخرى كيوقفو يشوفو التبدلات).
 *   - POST كيرجّع t الفعلي → المتصفح كيسجلو → كلشي متزامن مع ساعة السيرفر.
 *   - فشل الكتابة فـ journal/MIRA كيتسجل فـ audit.log (ما بقاش صامت).
 *
 * v3.41 hardening:
 *   - key whitelist (only known CRM keys are accepted)
 *   - stale-write rejection (older `t` than stored never overwrites newer data)
 *   - unwrap protection (rejects double-wrapped {t,d:{t,d}} payloads → fixes corrupted custom_sheets / team_photos)
 *   - exclusive lock around read-modify-write (two agents saving at once no longer lose a write)
 *   - rotating backups (last 30 writes + 1 per day) instead of a single .backup that got overwritten
 *   - payload size limit + minimal audit log
 *   - data dir outside public_html when available (../crm-paraveda-data), falls back to local file
 */
error_reporting(E_ALL);
ini_set('display_errors', '0');

header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-cache, no-store, must-revalidate');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Headers: Content-Type, X-Sync-Token');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
if (($_SERVER['REQUEST_METHOD'] ?? '') === 'OPTIONS') { exit; }

/* ---------- config ---------- */
$SECRET = '8c907fc0f4ffe0b9775a6b7c3c0fc7700e5724c0d78343df';

/* v3.67: deterministic data dir + mirror.
 * قبل: كان كيبدل المجلد بصمت إلا كان !is_writable → جوج ملفات بيانات مفروشين =
 * طلبيات كتظهر وكتختفي. دابا: كنختارو المجلد بالـ epoch (أحدث بيانات) ونكتبو
 * فـ الجوج بلاصات ديما حتى يرجع التوأمية بيناتهم. */
$DIR_EXT = __DIR__ . '/../crm-paraveda-data';
$DIR_LOC = __DIR__;
function crm_epoch_dir($d) {
  $m = 0;
  $s = @file_get_contents($d . '/crm_data.json');
  if ($s !== false && $s !== '') {
    $j = json_decode($s, true);
    if (is_array($j)) { foreach ($j as $v) { if (is_array($v) && isset($v['t']) && (int)$v['t'] > $m) $m = (int)$v['t']; } }
    else { $m = -1; } // undecodable file must never win
  }
  foreach (array($d . '/journal.log', $d . '/journal.log.1') as $jf) {
    if (!file_exists($jf)) continue;
    $fh = @fopen($jf, 'r'); if (!$fh) continue;
    $sz = @filesize($jf); if ($sz > 8192) @fseek($fh, -8192, SEEK_END);
    $tail = '';
    while (($l = fgets($fh)) !== false) { $l = trim($l); if ($l !== '') $tail = $l; }
    @fclose($fh);
    $e = json_decode((string)$tail, true);
    if (is_array($e) && isset($e['t']) && (int)$e['t'] > $m) $m = (int)$e['t'];
  }
  return $m;
}
$PRIMARY = $DIR_EXT; $MIRROR = $DIR_LOC;
$__eE = 0; $__eL = 0;
if (!is_dir($DIR_EXT)) { $PRIMARY = $DIR_LOC; $MIRROR = null; }
else {
  $__eE = crm_epoch_dir($DIR_EXT); $__eL = crm_epoch_dir($DIR_LOC);
  if ($__eL > $__eE) { $PRIMARY = $DIR_LOC; $MIRROR = $DIR_EXT; }
}
$DATA_DIR    = $PRIMARY;
$DATA_FILE   = $PRIMARY . '/crm_data.json';
$MIRROR_FILE = ($MIRROR !== null) ? $MIRROR . '/crm_data.json' : null;
$LOCK_FILE   = $PRIMARY . '/.crm.lock';
$BACKUP_DIR  = $PRIMARY . '/backups';
$AUDIT_FILE  = $PRIMARY . '/audit.log';
$JOURNAL     = $PRIMARY . '/journal.log';
$JOURNAL_M   = ($MIRROR !== null) ? $MIRROR . '/journal.log' : null;
$PUSH_KEYS_FILE = $DATA_DIR . '/push_keys.json';   // v3.98: مفاتيح Web Push (مسدودة من الويب)
$PUSH_SUBS_FILE = $DATA_DIR . '/push_subs.json';   // v3.98: هواتف البنات (مسدودة من الويب)
/* PERF v3.90: 8MB journal = replay ديال 8 ميغا JSON فـ كل قراية. 512KB كافيين
 * بزاف حيت كل كتابة كتسبقها كتابة كاملة ديال crm_data.json تحت القفل. */
$JOURNAL_MAX = 512 * 1024;
$MAX_BODY    = 24 * 1024 * 1024;   // 24 MB per write
$KEEP_WRITES = 30;                 // rotating pre-write backups
$KEEP_DAYS   = 30;                 // daily snapshots
$ETAG_CACHE  = $PRIMARY . '/.crm.etag';   // PERF v3.90: cache ديال ETag باش GET يولي 304 بلا قراية
$BACKUP_MIN_GAP = 120;             // PERF v3.90: نسخة احتياطية كل دقيقتين كحد أقصى (ماشي فكل كتابة)
$TOMBSTONE_TTL  = 21 * 86400;      // PERF v3.90: الطلبية الممسوحة كتتنحا نهائياً من بعد 21 يوم
$TOMBSTONE_MAX  = 150;             // PERF v3.90: وفأي حال، ما كنحتافظوش بأكثر من 150 طومبستون

$ALLOWED_KEYS = array(
  'paraveda_users_v1','paraveda_orders_v5','paraveda_agent_names_v1','paraveda_chat_v1',
  'paraveda_worktimes_v1','paraveda_remarques_v1','paraveda_avances_v1','paraveda_adspend_v1',
  'paraveda_perfrows_v1','paraveda_livraison_v1','paraveda_history_v1','paraveda_villes_v2',
  'paraveda_catalog_v1','sheet_pièce','paraveda_team_photos_v1','tabs_list_v1',
  'custom_sheets_v1','paraveda_period_v1','paraveda_period_v2',
  'paraveda_backup_v1','paraveda_backup_v1_agents',
  'paraveda_dupok_v1','paraveda_returns_v1','paraveda_return_audit_v1','paraveda_stock_movements_v1'   // v3.94 + retours: المكررات لي تعلّمات «ماشي مكررة»
);

/* ---------- helpers ---------- */
function crm_token() {
  if (isset($_SERVER['HTTP_X_SYNC_TOKEN'])) return (string)$_SERVER['HTTP_X_SYNC_TOKEN'];
  if (isset($_GET['token'])) return (string)$_GET['token'];
  return '';
}
function crm_out($arr, $code = 200) {
  if ($code !== 200) http_response_code($code);
  echo json_encode($arr, JSON_UNESCAPED_UNICODE);
  exit;
}
function crm_audit($line) {
  global $AUDIT_FILE;
  $ip = $_SERVER['REMOTE_ADDR'] ?? '-';
  @file_put_contents($AUDIT_FILE, date('Y-m-d H:i:s') . " | $ip | $line\n", FILE_APPEND | LOCK_EX);
  if (@filesize($AUDIT_FILE) > 2 * 1024 * 1024) { @rename($AUDIT_FILE, $AUDIT_FILE . '.1'); }
}
/** v3.41: afrizon_* → paraveda_* (rename), keeps newest if both exist */
function crm_migrate_keys($j) {
  $o = array();
  foreach ($j as $k => $v) {
    $nk = (strpos($k, 'afrizon_') === 0) ? 'paraveda_' . substr($k, 8) : $k;
    if (isset($o[$nk]) && isset($o[$nk]['t']) && isset($v['t']) && $o[$nk]['t'] >= $v['t']) continue;
    $o[$nk] = $v;
  }
  return $o;
}
/* PERF v3.90: crm_read_raw() كانت كتتسما 3 مرات فـ كل POST — كل مرة كتقرا وتفكّك
 * crm_data.json (1.1MB) + الميرا (1.1MB) + replay ديال 4 ملفات journal.
 * = أكثر من 10MB ديال JSON decoding باش تحفظ طلبية وحدة.
 * دابا النتيجة كتتخزن فالذاكرة داخل نفس الـ request. القراية لي تحت القفل
 * خاصها تكون طرية ($force=true) حيت ممكن شي request آخر كتب بيناتهم. */
function crm_read_raw($force = false) {
  static $cache = null;
  if (!$force && $cache !== null) return $cache;
  $cache = crm_read_raw_fresh();
  return $cache;
}
function crm_read_raw_fresh() {
  global $DATA_FILE, $BACKUP_DIR, $MIRROR_FILE;
  $j = null;
  if (file_exists($DATA_FILE)) {
    $s = @file_get_contents($DATA_FILE);
    $j = json_decode((string)$s, true);
    if (!is_array($j)) crm_audit("corrupt | main file undecodable | len=" . strlen((string)$s));
  }
  if (!is_array($j)) {
    // corrupted/missing main file → try newest backup (journal replay below restores newest state anyway)
    $c = glob($BACKUP_DIR . '/b-*.json');
    if ($c) { rsort($c); foreach ($c as $f) { $j = json_decode((string)@file_get_contents($f), true); if (is_array($j)) { crm_audit("recover | from=" . basename($f)); break; } } }
  }
  if (!is_array($j)) $j = array();
  /* v3.81: دمج primary + mirror مفتاح بمفتاح (الأحدث t كيربح) + توحيد اليوزرز بالـ id.
     قبل: إلا الميرا (crm-paraveda-data) كانت فيها نسخة قديمة، كل قرية كترجع للقديم
     → "اليوزر الجديد كيتمسح من بعد لحضات". دابا ملف قديم فأي بلاصة ما كيقدر
     يخبي داتا أحدث، واليوزرز لي ضاعو من أحد الملفين كيرجعو. */
  if ($MIRROR_FILE && is_file($MIRROR_FILE)) {
    $m = json_decode((string)@file_get_contents($MIRROR_FILE), true);
    if (is_array($m)) {
      /* v3.82: ليستة اليوزرز ديال الملف الرئيسي خاصها تنحفظ قبل دمج المفاتيح —
         إلا الميرا كان أحدث، الدمج كيبدل اليوزرز ديال الرئيسي قبل الاتحاد
         → اليوزرز لي غير فالرئيسي كانو كيضيعو. */
      $pu = (isset($j['paraveda_users_v1']['d']) && is_array($j['paraveda_users_v1']['d'])) ? crm_unwrap($j['paraveda_users_v1']['d']) : null;
      $mirrorOlderKeys = 0;
      foreach ($m as $mk => $mv) {
        if (!is_array($mv) || !isset($mv['t'])) continue;
        if (!isset($j[$mk]) || !is_array($j[$mk]) || (int)$mv['t'] > (int)$j[$mk]['t']) { $j[$mk] = $mv; $mirrorOlderKeys++; }
      }
      if ($mirrorOlderKeys > 0) crm_audit("mirror-merge | newer-from-mirror keys=$mirrorOlderKeys");
      $ub = (isset($m['paraveda_users_v1']['d']) && is_array($m['paraveda_users_v1']['d'])) ? crm_unwrap($m['paraveda_users_v1']['d']) : null;
      if (is_array($pu) && is_array($ub)) {
        $un = crm_users_union($pu, $ub);
        if (count($un) !== count($pu)) { crm_audit("users-rescue | merged users: " . count($pu) . " + " . count($ub) . " → " . count($un)); $j['paraveda_users_v1']['d'] = $un; $j['paraveda_users_v1']['t'] = max((int)$j['paraveda_users_v1']['t'], (int)$m['paraveda_users_v1']['t']); }
      }
    }
  }
  // v3.67: journal replay — أحدث كتابة ناجحة كتربح ديما، حتى إلا crm_data.json تبدل يدويا
  // (FTP) ولا تخسر → الطلبيات الجديدة عمرهم ما كيتنساو.
  return crm_journal_replay(crm_migrate_keys($j));
}
/* v3.81: توحيد ليستة اليوزرز بالـ id — أحدث _u كيربح (الحذف _del محترم).
   كتستعمل فـ دمج الملفات (primary+mirror) باش يوزر مفقود من ملف واحد يرجع. */
function crm_users_union($a, $b) {
  $out = array();
  foreach ($a as $u) { if (is_array($u) && isset($u['id'])) $out[(string)$u['id']] = $u; }
  foreach ($b as $u) {
    if (!is_array($u) || !isset($u['id'])) continue;
    $id = (string)$u['id'];
    if (!isset($out[$id])) { $out[$id] = $u; continue; }
    /* v3.82: الحذف نهائي — إلا شي نسخة فيهم _del هي لي كتربح (من الجوج جيهات).
       جوج طومبستونات → الأحدث _u كيربح. حي ضد ميت → الميت كيربح ديما. */
    $cd = !empty($out[$id]['_del']); $nd = !empty($u['_del']);
    if ($cd || $nd) {
      $cu = isset($out[$id]['_u']) ? (float)$out[$id]['_u'] : -1;
      $nu = isset($u['_u']) ? (float)$u['_u'] : -1;
      if (!$cd || ($nd && $nu > $cu)) $out[$id] = $u;
      continue;
    }
    $cu = isset($out[$id]['_u']) ? (float)$out[$id]['_u'] : -1;
    $nu = isset($u['_u']) ? (float)$u['_u'] : -1;
    if ($nu > $cu) $out[$id] = $u;
  }
  return array_values($out);
}
/* v3.67: journal (WAL) — كل كتابة ناجحة كتسجل سطر فـ journal.log. القراية كتعاود
 * التسجيلات فوق الملف الأساسي: إلا الملف الأساسي رجع لنسخة قديمة ولا تفسد،
 * أحدث حالة كترجع بوحدها من الـ journal. */
function crm_journal_append($k, $t, $d) {
  global $JOURNAL, $JOURNAL_M, $JOURNAL_MAX;
  $line = json_encode(array('k' => $k, 't' => $t, 'd' => $d), JSON_UNESCAPED_UNICODE);
  if ($line === false) return;
  foreach (array($JOURNAL, $JOURNAL_M) as $jf) {
    if (!$jf) continue;
    // v3.81: الفشل كيتسجل فـ audit.log — قبل كان صامت وماحدش كان كيعرف علاش الداتا كتضيع
    if (@file_put_contents($jf, $line . "\n", FILE_APPEND | LOCK_EX) === false) { crm_audit("journal-fail | $jf"); continue; }
    if (@filesize($jf) > $JOURNAL_MAX) {
      // كل كتابة كتسبقها كتابة كاملة ديال الملف الرئيسي تحت القفل → محتوى الـ journalولى
      // مكرر → نحيدوه حتى ما يثقلش القراية (replay) فالطلبات الجاية.
      @unlink($jf);
    }
  }
}
function crm_journal_replay($data) {
  global $JOURNAL, $JOURNAL_M;
  $files = array($JOURNAL . '.1', $JOURNAL, ($JOURNAL_M !== null ? $JOURNAL_M . '.1' : null), $JOURNAL_M);
  foreach ($files as $jf) {
    if (!$jf || !file_exists($jf)) continue;
    $fh = @fopen($jf, 'r'); if (!$fh) continue;
    while (($l = fgets($fh)) !== false) {
      $l = trim($l); if ($l === '') continue;
      $e = json_decode($l, true);
      if (!is_array($e) || !isset($e['k'], $e['t'], $e['d']) || !is_array($e['d'])) continue;
      $k = (string)$e['k']; $et = (int)$e['t'];
      /* v3.81: سطر الـ journal ما كيقبلش يتربح على داتا أحدث منه.
         v3.80 كانت كتطبق آخر سطر ديما بالترتيب → سطر قديم فـ journal الميرا
         (ولا أي journal متأخر) كان كيمسح اليوزرز/الطلبيات الجداد فكل قرية.
         هادشي هو بالضبط "اليوزر الجديد كيتمسح من بعد لحضات". */
      $cur = (isset($data[$k]) && is_array($data[$k]) && isset($data[$k]['t'])) ? (int)$data[$k]['t'] : 0;
      if ($et <= $cur) continue;
      $data[$k] = array('t' => $et, 'd' => $e['d']);
    }
    @fclose($fh);
  }
  return $data;
}
/** unwrap {t,d:{t,d:X}} → X (defensive: corruption produced by old import.php) */
function crm_unwrap($v) {
  $g = 0;
  while (is_array($v) && isset($v['t']) && array_key_exists('d', $v) && is_numeric($v['t']) && count($v) <= 2 && $g++ < 5) { $v = $v['d']; }
  return $v;
}
/* PERF v3.90: بصمة رخيصة (stat فقط، بلا قراية) ديال كل ملفات الداتا.
 * كتخدم باش نعرفو واش تبدل شي حاجة بلا ما نقراو 2.2MB ديال JSON. */
function crm_data_sig() {
  global $DATA_FILE, $MIRROR_FILE, $JOURNAL, $JOURNAL_M;
  $p = '';
  foreach (array($DATA_FILE, $MIRROR_FILE, $JOURNAL, $JOURNAL_M, $JOURNAL . '.1') as $f) {
    if (!$f) continue;
    $p .= '|' . (@filemtime($f) ?: 0) . ':' . (@filesize($f) ?: 0);
  }
  return md5($p);
}
/* كيرجع الـ ETag المخزن إلا البصمة باقة هي هي، وإلا null (خاصنا نقراو بصح). */
function crm_etag_cached($sig) {
  global $ETAG_CACHE;
  $s = @file_get_contents($ETAG_CACHE);
  if ($s === false || $s === '') return null;
  $j = json_decode($s, true);
  if (!is_array($j) || !isset($j['sig'], $j['etag'])) return null;
  return ($j['sig'] === $sig) ? (string)$j['etag'] : null;
}
function crm_etag_store($sig, $etag) {
  global $ETAG_CACHE;
  @file_put_contents($ETAG_CACHE, json_encode(array('sig' => $sig, 'etag' => $etag)), LOCK_EX);
}

function crm_backup() {
  global $DATA_FILE, $BACKUP_DIR, $KEEP_WRITES, $KEEP_DAYS, $BACKUP_MIN_GAP;
  if (!file_exists($DATA_FILE)) return;
  if (!is_dir($BACKUP_DIR)) @mkdir($BACKUP_DIR, 0755, true);
  if (!is_dir($BACKUP_DIR)) return;
  /* PERF v3.90: قبل، كل كتابة كانت كتنسخ 1.1MB على القرص. مع 10 وكلاء كيخدمو
   * هادشي ميات الميغاوات ديال I/O فالساعة. دابا نسخة كل دقيقتين كحد أقصى —
   * الحماية باقية (الـ journal + الملف الرئيسي + الميرا) والـ I/O نقص ~95%. */
  $last = 0;
  $b0 = glob($BACKUP_DIR . '/b-*.json');
  if ($b0) { foreach ($b0 as $f) { $mt = @filemtime($f); if ($mt > $last) $last = $mt; } }
  if ($last > 0 && (time() - $last) < $BACKUP_MIN_GAP) {
    $daily0 = $BACKUP_DIR . '/d-' . date('Ymd') . '.json';
    if (!file_exists($daily0)) @copy($DATA_FILE, $daily0);
    return;
  }
  @copy($DATA_FILE, $BACKUP_DIR . '/b-' . date('Ymd-His') . '-' . substr((string)microtime(true) * 1000 % 1000, 0, 3) . '.json');
  $daily = $BACKUP_DIR . '/d-' . date('Ymd') . '.json';
  if (!file_exists($daily)) @copy($DATA_FILE, $daily);
  // rotate
  $b = glob($BACKUP_DIR . '/b-*.json'); if ($b && count($b) > $KEEP_WRITES) { sort($b); foreach (array_slice($b, 0, count($b) - $KEEP_WRITES) as $f) @unlink($f); }
  $d = glob($BACKUP_DIR . '/d-*.json'); if ($d && count($d) > $KEEP_DAYS)   { sort($d); foreach (array_slice($d, 0, count($d) - $KEEP_DAYS) as $f) @unlink($f); }
}
// v3.65: field-level merge — a field edited later (per-field stamp _f) is never overwritten
// by a whole-row write coming from a browser that still held an older copy of the row.
// v3.66: DATE LOCK — dateCreation / dateConfirmation / dateExp / dateLiv can only change
// when the incoming row carries a STRICTLY NEWER per-field stamp (_f.date*). A whole-row
// write from an old/stale browser (no _f, or older _f) can never move a date anymore —
// the stored value always wins. This is the server side of "التاريخ ما كيتبدلش بوحدو".
function crm_merge_row($a, $b) {
  $ua = isset($a['_u']) ? (float)$a['_u'] : 0; $ub = isset($b['_u']) ? (float)$b['_u'] : 0;
  $base = $ub >= $ua ? $b : $a; $oth = $ub >= $ua ? $a : $b;
  if (!empty($a['_del']) || !empty($b['_del'])) return !empty($a['_del']) ? $a : $b;   // v3.103: الحذف نهائي (المسوح ما كيرجعش)
  $bf = (isset($base['_f']) && is_array($base['_f'])) ? $base['_f'] : array();
  $of = (isset($oth['_f']) && is_array($oth['_f'])) ? $oth['_f'] : array();
  foreach ($of as $k => $to) {
    $to = (float)$to; $tb = isset($bf[$k]) ? (float)$bf[$k] : 0;
    if ($to > $tb && array_key_exists($k, $oth)) { $base[$k] = $oth[$k]; $bf[$k] = $to; }
  }
  if ($bf) $base['_f'] = $bf;
  // v3.66 date lock: $a is the STORED row (crm_merge_orders always calls with stored first).
  // If the value differs and the incoming side has no strictly newer explicit date edit,
  // restore the stored value (and its stamp).
  foreach (array('dateCreation','dateConfirmation','dateExp','dateLiv') as $dk) {
    if (!array_key_exists($dk, $a)) continue;
    $av = (string)$a[$dk];
    $bv = array_key_exists($dk, $b) ? (string)$b[$dk] : '';
    if ($av === $bv) continue;
    $ta = (isset($a['_f'][$dk]) && is_numeric($a['_f'][$dk])) ? (float)$a['_f'][$dk] : 0;
    $tb = (isset($b['_f'][$dk]) && is_numeric($b['_f'][$dk])) ? (float)$b['_f'][$dk] : 0;
    if ($tb <= $ta) {
      $base[$dk] = $av;
      if ($ta > 0) {
        $f0 = (isset($base['_f']) && is_array($base['_f'])) ? $base['_f'] : array();
        $f0[$dk] = $ta; $base['_f'] = $f0;
      }
    }
  }
  return $base;
}
function crm_merge_orders($cur, $in, $reset = 0) {
  $nowms = (int)(microtime(true) * 1000);
  $byId = array(); $order = array();
  foreach ($cur as $o) { if (!is_array($o) || !isset($o['id'])) continue; $id = (string)$o['id']; $byId[$id] = $o; $order[] = $id; }
  foreach ($in as $o) {
    if (!is_array($o) || !isset($o['id'])) continue;
    // v3.66: clamp future stamps (device clock ahead of server) — a client can never
    // win a merge just because its clock is wrong; _u and every _f stamp are capped at server time.
    if (isset($o['_u']) && (float)$o['_u'] > $nowms) { $o['_u'] = $nowms; }
    if (isset($o['_f']) && is_array($o['_f'])) {
      foreach ($o['_f'] as $fk => $ft) { if (is_numeric($ft) && (float)$ft > $nowms) $o['_f'][$fk] = $nowms; }
    }
    $id = (string)$o['id'];
    $beforeDates = array();
    if (isset($byId[$id])) {
      foreach (array('dateCreation','dateConfirmation') as $dk) { $beforeDates[$dk] = isset($byId[$id][$dk]) ? (string)$byId[$id][$dk] : ''; }
    }
    if (!isset($byId[$id])) {
      // v3.62: rows older than the last reset (coming from a stale browser cache) are never resurrected
      $u = isset($o['_u']) ? (float)$o['_u'] : 0;
      if ($reset > 0 && $u < $reset) continue;
      $byId[$id] = $o; $order[] = $id; continue;
    }
    $byId[$id] = crm_merge_row($byId[$id], $o);
    // v3.66 audit: every time a merge actually moves a date, leave a trace in audit.log
    foreach ($beforeDates as $dk => $bv) {
      $av = isset($byId[$id][$dk]) ? (string)$byId[$id][$dk] : '';
      if ($bv !== '' && $av !== $bv) crm_audit("date-change | id=$id | $dk: $bv → $av");
    }
  }
  $out = array(); foreach (array_unique($order) as $id) $out[] = $byId[$id];
  usort($out, function($x, $y) { $a = (float)$x['id']; $b = (float)$y['id']; return $a == $b ? 0 : ($a < $b ? 1 : -1); });
  return $out;
}
/* v3.78: دمج موحد — كتابة أحدث كتربح (حتى الحذف)، كتابة متأخرة كتزيد غير الناقص.
   هذا لي كيمنع اختفاء اليوزر الجديد ملي ساعة الجهاز متأخرة ولا جوج زادو فنفس اللحظة. */
function crm_row_key($row) {
  if (is_array($row) && isset($row['id'])) return 'i:' . (string)$row['id'];
  if (is_scalar($row)) return 's:' . (string)$row;
  return 'j:' . json_encode($row);
}
/* PERF v3.90: تنقية الـ tombstones.
 * 599 طلبية من 1408 (42%) كانو عندهم _del=true وباقين فالداتا للأبد — كيتحملو
 * كل مزامنة، كيتدمجو صف بصف، وكياخدو بلاصة فـ localStorage.
 * دابا أي طلبية ممسوحة وقديمة بأكثر من 30 يوم كتتنحا نهائياً. 30 يوم أوسع بزاف
 * من الـ grace ديال المتصفح (15 دقيقة) إذن ما كاين حتى خطر ديال الرجوع. */
function crm_purge_tombstones($rows, $ttl, $max) {
  /* v3.103: الطلبيات الممسوحة ما كتتمسحش نهائياً — كانت كترجع من بعد شي مدة
   * (المتصفح كيرجع نسخة قديمة + الحذف كان كيطيح بعد 150). دابا القديمة كتتصغّر
   * غير (تبقى id + _del + التاريخ/الهاتف/الاسم/المنتوج) باش الحذف يبقى دائم. */
  if (!is_array($rows)) return $rows;
  $cut = ((int)(microtime(true) * 1000)) - ($ttl * 1000);
  $out = array(); $slim = 0;
  foreach ($rows as $r) {
    if (is_array($r) && !empty($r['_del'])) {
      $u = isset($r['_u']) ? (float)$r['_u'] : 0;
      if ($u > 0 && $u < $cut) {
        $r = array(
          'id' => isset($r['id']) ? $r['id'] : '', '_del' => true, '_u' => $u,
          'dateCreation' => isset($r['dateCreation']) ? $r['dateCreation'] : '',
          'telephone' => isset($r['telephone']) ? $r['telephone'] : '',
          'nom' => isset($r['nom']) ? $r['nom'] : '',
          'produit' => isset($r['produit']) ? $r['produit'] : ''
        );
        $slim++;
      }
    }
    $out[] = $r;
  }
  if ($slim > 0) crm_audit("purge | tombstones slimmed=$slim");
  return $out;
}
function crm_merge_list($cur, $in, $tCur, $tIn) {
  if ($tIn >= $tCur) return $in;
  $have = array();
  foreach ($cur as $row) $have[crm_row_key($row)] = true;
  foreach ($in as $row) { $kk = crm_row_key($row); if (!isset($have[$kk])) { $cur[] = $row; $have[$kk] = true; } }
  return $cur;
}
function crm_write($data) {
  global $DATA_FILE;
  $tmp = $DATA_FILE . '.tmp.' . getmypid();
  $json = json_encode($data, JSON_UNESCAPED_UNICODE);
  if ($json === false) return false;
  if (@file_put_contents($tmp, $json, LOCK_EX) === false) return false;
  if (!@rename($tmp, $DATA_FILE)) { @unlink($tmp); return false; }
  return true;
}
/* v3.67: write primary + mirror — الجوج ملفات ديما متطابقين، ما بقاش split-brain */
function crm_write_all($data) {
  global $MIRROR_FILE;
  $ok = crm_write($data);
  if ($MIRROR_FILE) {
    $tmp = $MIRROR_FILE . '.tmp.' . getmypid();
    $json = json_encode($data, JSON_UNESCAPED_UNICODE);
    if ($json !== false && @file_put_contents($tmp, $json, LOCK_EX) !== false) {
      if (!@rename($tmp, $MIRROR_FILE)) { @unlink($tmp); crm_audit("mirror-fail | rename | $MIRROR_FILE"); } // v3.81: ما بقاش صامت
    } else {
      if (file_exists($tmp)) @unlink($tmp);
      crm_audit("mirror-fail | write | $MIRROR_FILE"); // v3.81: ما بقاش صامت
    }
  }
  return $ok;
}

/* ================================================================
 * v3.98 — إشعارات Web Push للبنات (طلبية جديدة ليها من الشيت)
 *   push_keys.json : مفاتيح VAPID (كتتولد وحدها أول مرة). مسدودة من الويب (.htaccess)
 *   push_subs.json : الهواتف المسجّلة {agent, endpoint, p256dh, auth}. مسدودة من الويب
 *   GET  api.php?pushkey=1&token=...          → المفتاح العام
 *   POST {action:'push_subscribe', agent, sub:{endpoint, keys:{p256dh, auth}}}
 *   POST {action:'push_test', agent}          → إشعار تجريبي لهاد البنت
 *   الإشعارات كتصيفط أوتوماتيك ملي كتدخل طلبيات جداد من الشيت (crm_sheet_orders)
 * ================================================================ */
function crm_push_b64e($s) { return rtrim(strtr(base64_encode($s), '+/', '-_'), '='); }
function crm_push_b64d($s) {
  $s = strtr((string)$s, '-_', '+/');
  return base64_decode($s . str_repeat('=', (4 - strlen($s) % 4) % 4), true);
}
function crm_push_read($file) {
  if (!file_exists($file)) return array();
  $j = json_decode((string)@file_get_contents($file), true);
  return is_array($j) ? $j : array();
}
function crm_push_write($file, $arr) {
  $tmp = $file . '.tmp.' . getmypid();
  $json = json_encode($arr, JSON_UNESCAPED_UNICODE);
  if ($json === false || @file_put_contents($tmp, $json, LOCK_EX) === false) return false;
  if (!@rename($tmp, $file)) { @unlink($tmp); return false; }
  return true;
}
/* نقطة P-256 خام (65 بايت، تبدا بـ 0x04) → مفتاح عام PEM */
function crm_push_pub_from_raw($raw) {
  if (!is_string($raw) || strlen($raw) !== 65 || $raw[0] !== "\x04") return false;
  $der = hex2bin('3059301306072a8648ce3d020106082a8648ce3d030107034200') . $raw;
  return @openssl_pkey_get_public("-----BEGIN PUBLIC KEY-----\n" . chunk_split(base64_encode($der), 64, "\n") . "-----END PUBLIC KEY-----\n");
}
/* مفتاح EC → نقطة عامة خام 65 بايت */
function crm_push_raw_pub($key) {
  $d = openssl_pkey_get_details($key);
  if (!$d || !isset($d['ec']['x'], $d['ec']['y'])) return false;
  return "\x04" . str_pad($d['ec']['x'], 32, "\x00", STR_PAD_LEFT) . str_pad($d['ec']['y'], 32, "\x00", STR_PAD_LEFT);
}
/* مفاتيح VAPID: كتتقرا من الملف، ولا كتتولد أول مرة */
function crm_push_keys() {
  global $PUSH_KEYS_FILE;
  $k = crm_push_read($PUSH_KEYS_FILE);
  if (!empty($k['priv']) && !empty($k['pub'])) return $k;
  $key = @openssl_pkey_new(array('curve_name' => 'prime256v1', 'private_key_type' => OPENSSL_KEYTYPE_EC));
  if (!$key) return null;
  $pem = '';
  if (!openssl_pkey_export($key, $pem)) return null;
  $raw = crm_push_raw_pub($key);
  if ($raw === false) return null;
  $k = array('priv' => $pem, 'pub' => crm_push_b64e($raw));
  return crm_push_write($PUSH_KEYS_FILE, $k) ? $k : null;
}
/* توقيع ECDSA (DER) → 64 بايت خام (r||s) كما يطلب JWT */
function crm_push_der2raw($der) {
  $p = 2;
  if (ord($der[1]) & 0x80) $p = 2 + (ord($der[1]) & 0x7f);
  $rl = ord($der[$p + 1]); $r = substr($der, $p + 2, $rl);
  $p2 = $p + 2 + $rl;
  $sl = ord($der[$p2 + 1]); $s = substr($der, $p2 + 2, $sl);
  return str_pad(ltrim($r, "\x00"), 32, "\x00", STR_PAD_LEFT) . str_pad(ltrim($s, "\x00"), 32, "\x00", STR_PAD_LEFT);
}
/* RFC 8292 (VAPID): Authorization header */
function crm_push_vapid_auth($endpoint) {
  $k = crm_push_keys();
  if (!$k) return null;
  $pk = @openssl_pkey_get_private($k['priv']);
  if (!$pk) return null;
  $p = parse_url($endpoint);
  $aud = $p['scheme'] . '://' . $p['host'] . (isset($p['port']) ? ':' . $p['port'] : '');
  $h = crm_push_b64e(json_encode(array('typ' => 'JWT', 'alg' => 'ES256')));
  $b = crm_push_b64e(json_encode(array('aud' => $aud, 'exp' => time() + 12 * 3600, 'sub' => 'mailto:admin@paraveda.ma')));
  $in = $h . '.' . $b;
  if (!openssl_sign($in, $der, $pk, OPENSSL_ALGO_SHA256)) return null;
  return 'vapid t=' . $in . '.' . crm_push_b64e(crm_push_der2raw($der)) . ', k=' . $k['pub'];
}
/* RFC 8291: تشفير aes128gcm. $asKey = مفتاح مؤقت جديد لكل رسالة */
function crm_push_encrypt($payload, $uaPub, $auth, $asKey) {
  $asPub = crm_push_raw_pub($asKey);
  $peer  = crm_push_pub_from_raw($uaPub);
  if ($asPub === false || $peer === false || strlen($auth) !== 16) return null;
  $ecdh = openssl_pkey_derive($peer, $asKey, 32);
  if ($ecdh === false) return null;
  $salt    = random_bytes(16);
  $ikm     = hash_hkdf('sha256', $ecdh, 32, "WebPush: info\x00" . $uaPub . $asPub, $auth);
  $cek     = hash_hkdf('sha256', $ikm, 16, "Content-Encoding: aes128gcm\x00", $salt);
  $nonce   = hash_hkdf('sha256', $ikm, 12, "Content-Encoding: nonce\x00", $salt);
  $ct = openssl_encrypt($payload . "\x02", 'aes-128-gcm', $cek, OPENSSL_RAW_DATA, $nonce, $tag, '', 16);
  if ($ct === false) return null;
  return $salt . pack('N', 4096) . chr(strlen($asPub)) . $asPub . $ct . $tag;
}
/* يبني الطلب (بلا ما يصيفطو): [url, headers, body] أو null */
function crm_push_build($sub, $payload, $asKey = null) {
  $auth = crm_push_vapid_auth($sub['endpoint']);
  if ($auth === null) return null;
  if ($asKey === null) $asKey = @openssl_pkey_new(array('curve_name' => 'prime256v1', 'private_key_type' => OPENSSL_KEYTYPE_EC));
  if (!$asKey) return null;
  $body = crm_push_encrypt(json_encode($payload, JSON_UNESCAPED_UNICODE), crm_push_b64d($sub['p256dh']), crm_push_b64d($sub['auth']), $asKey);
  if ($body === null) return null;
  return array($sub['endpoint'], array(
    'Content-Type: application/octet-stream',
    'Content-Encoding: aes128gcm',
    'TTL: 3600',
    'Urgency: high',
    'Authorization: ' . $auth,
  ), $body);
}
/* يصيفط فعلياً. كيرجع كود HTTP (201 = واصل) ولا 0 إلا فشل */
function crm_push_post($req) {
  $ch = curl_init($req[0]);
  curl_setopt_array($ch, array(
    CURLOPT_POST => true, CURLOPT_POSTFIELDS => $req[2], CURLOPT_HTTPHEADER => $req[1],
    CURLOPT_RETURNTRANSFER => true, CURLOPT_TIMEOUT => 8,
  ));
  curl_exec($ch);
  $code = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE);
  curl_close($ch);
  return $code;
}
/* خدمات Push المعروفة فقط (باش السيرفر ما يصيفطش لأي عنوان) */
function crm_push_endpoint_ok($ep) {
  if (strpos($ep, 'https://') !== 0 || strlen($ep) > 2000) return false;
  $host = (string)parse_url($ep, PHP_URL_HOST);
  foreach (array('googleapis.com', 'mozilla.com', 'push.apple.com', 'windows.com') as $ok) {
    if ($host === $ok || substr($host, -strlen('.' . $ok)) === '.' . $ok) return true;
  }
  return false;
}
/* يصيفط لكل هواتف البنت. كيحيد الهواتف لي ما بقاوش مسجلين (404/410) */
function crm_push_to_agent($agent, $payload) {
  global $PUSH_SUBS_FILE;
  $subs = crm_push_read($PUSH_SUBS_FILE);
  $sent = 0; $removed = false; $keep = array();
  foreach ($subs as $s) {
    if (!is_array($s) || !isset($s['agent'], $s['endpoint']) || strcasecmp($s['agent'], $agent) !== 0) { $keep[] = $s; continue; }
    $req = crm_push_build($s, $payload);
    $code = $req ? crm_push_post($req) : 0;
    if ($code === 404 || $code === 410) { $removed = true; continue; }
    if ($code >= 200 && $code < 300) $sent++;
    else crm_audit('push-fail | ' . $agent . ' | code=' . $code);
    $keep[] = $s;
  }
  if ($removed) crm_push_write($PUSH_SUBS_FILE, $keep);
  return $sent;
}
/* بعد الصيفط من الشيت: إشعار وحدة لكل بنت (بلا ما نصيفطو إشعار لكل طلبية) */
function crm_push_batch($byAgent) {
  foreach ($byAgent as $agent => $list) {
    $n = count($list);
    if ($n === 0) continue;
    $lines = array();
    foreach (array_slice($list, 0, 3) as $o) {
      $lines[] = trim($o['nom'] . ' · ' . $o['produit'] . ' · ' . $o['ville'], ' ·');
    }
    if ($n > 3) $lines[] = '+ ' . ($n - 3) . ' أخرى';
    crm_push_to_agent($agent, array(
      'title' => $n === 1 ? '📥 طلبية جديدة ليك' : '📥 عندك ' . $n . ' طلبيات جداد',
      'body'  => implode("\n", $lines),
      'url'   => './',
      'tag'   => 'pv-orders',
    ));
  }
}
function crm_push_subscribe($b) {
  global $PUSH_SUBS_FILE;
  $agent = trim((string)($b['agent'] ?? ''));
  $sub   = $b['sub'] ?? null;
  if ($agent === '' || !is_array($sub) || !is_array($sub['keys'] ?? null)) crm_out(array('ok'=>false, 'err'=>'bad-sub'), 400);
  $ep   = (string)($sub['endpoint'] ?? '');
  $p256 = (string)($sub['keys']['p256dh'] ?? '');
  $auth = (string)($sub['keys']['auth'] ?? '');
  if (!crm_push_endpoint_ok($ep) || strlen(crm_push_b64d($p256)) !== 65 || strlen(crm_push_b64d($auth)) !== 16)
    crm_out(array('ok'=>false, 'err'=>'bad-sub'), 400);
  $subs = array();
  foreach (crm_push_read($PUSH_SUBS_FILE) as $s) {
    if (is_array($s) && isset($s['endpoint']) && $s['endpoint'] !== $ep) $subs[] = $s;   // نفس الهاتف = تسجيل جديد
  }
  $subs[] = array('agent' => $agent, 'endpoint' => $ep, 'p256dh' => $p256, 'auth' => $auth, 't' => time());
  if (!crm_push_write($PUSH_SUBS_FILE, $subs)) crm_out(array('ok'=>false, 'err'=>'write-failed'), 500);
  crm_out(array('ok'=>true, 'agent'=>$agent));
}
function crm_push_test($b) {
  $agent = trim((string)($b['agent'] ?? ''));
  if ($agent === '') crm_out(array('ok'=>false, 'err'=>'bad-agent'), 400);
  $n = crm_push_to_agent($agent, array(
    'title' => '🔔 تجربة الإشعارات',
    'body'  => 'إلا وصلك هاد الإشعار، كل شي خدام مزيان.',
    'url'   => './', 'tag' => 'pv-test',
  ));
  crm_out(array('ok'=>true, 'sent'=>$n));
}

/* ================================================================
 * v3.97 — الشيت → CRM (Storeep / Google Sheet → الطلبيات)
 *   POST api.php {action:'sheet_orders', rows:[{dateCreation, nom, telephone, ...}]}
 *   كيزيد غير الطلبيات الجداد. التكرار كيتحسب سيرفر-سايد بـ:
 *     التاريخ + الهاتف (آخر 9 أرقام) + المنتوج   (إلا ما كاينش هاتف → الاسم)
 *   فالتالي إلا تصيفطات نفس السطر مرتين، ما كيتزادش مرتين.
 *   كيرجع: {ok, added, dup, skip, t, results:[{i, st:'added'|'dup'|'skip', id?, why?}]}
 * ================================================================ */
/* v3.99: إشعار أوتوماتيك لكل طلبية جديدة باسم بنت (من الشيت ولا زيدتيها بيدك)
 *   أو ملي تبدل لها الطلبية للاسم ديالها. كيحسب غير التغييرات الطرية (دقيقتين)،
 *   وكيوقف إلا كانو بزاف (حماية من الاستيراد/الاسترجاع). */
function crm_push_collect_changes($old, $new, $nowms) {
  $oldBy = array();
  if (is_array($old)) { foreach ($old as $o) { if (is_array($o) && isset($o['id'])) $oldBy[(string)$o['id']] = $o; } }
  $by = array(); $n = 0;
  foreach ($new as $o) {
    if (!is_array($o) || !empty($o['_del']) || !isset($o['id'])) continue;
    $ag = trim((string)(isset($o['agent']) ? $o['agent'] : ''));
    if ($ag === '') continue;
    $prev = isset($oldBy[(string)$o['id']]) ? $oldBy[(string)$o['id']] : null;
    if ($prev !== null && trim((string)(isset($prev['agent']) ? $prev['agent'] : '')) === $ag) continue;
    $when = (float)(isset($o['_u']) ? $o['_u'] : 0);
    if (isset($o['_f']['agent'])) $when = max($when, (float)$o['_f']['agent']);
    if ($when < $nowms - 120000) continue;
    $by[$ag][] = array(
      'nom'    => (string)(isset($o['nom']) ? $o['nom'] : ''),
      'produit'=> (string)(isset($o['produit']) ? $o['produit'] : ''),
      'ville'  => (string)(isset($o['ville']) ? $o['ville'] : ''),
    );
    $n++;
  }
  return ($n > 30) ? array() : $by;
}
function crm_sheet_text($v) {
  if ($v === null || is_array($v) || is_object($v)) return '';
  return trim((string)$v);
}
function crm_sheet_num($v, $def) {
  if ($v === null || is_array($v) || is_object($v)) return $def;
  $s = str_replace(',', '.', trim((string)$v));
  if ($s === '' || !is_numeric($s)) return $def;
  $f = (float)$s;
  return ($f == floor($f)) ? (int)$f : $f;
}
/* صيغ مقبولة: YYYY-MM-DD (وبالساعة) ولا DD/MM/YYYY (ولا DD-MM-YYYY) */
function crm_sheet_date($v) {
  $s = crm_sheet_text($v);
  if ($s === '') return '';
  if (preg_match('/^(\d{4})-(\d{1,2})-(\d{1,2})/', $s, $m)) { $y = (int)$m[1]; $mo = (int)$m[2]; $d = (int)$m[3]; }
  elseif (preg_match('/^(\d{1,2})[\/.-](\d{1,2})[\/.-](\d{4})/', $s, $m)) { $d = (int)$m[1]; $mo = (int)$m[2]; $y = (int)$m[3]; }
  else return null;   // ماشي تاريخ صحيح
  return checkdate($mo, $d, $y) ? sprintf('%04d-%02d-%02d', $y, $mo, $d) : null;
}
/* الهاتف: غير الأرقام، +212 / 212 → 0، ورقم 9 أرقام بلا 0 → كنزيدو 0 */
function crm_sheet_phone($v) {
  $d = preg_replace('/\D+/', '', crm_sheet_text($v));
  if (strlen($d) === 12 && strpos($d, '212') === 0) $d = '0' . substr($d, 3);
  elseif (strlen($d) === 9 && $d[0] !== '0') $d = '0' . $d;
  return $d;
}
function crm_sheet_key($date, $phone, $nom, $produit) {
  $p = crm_sheet_phone($phone);
  $p9 = strlen($p) >= 9 ? substr($p, -9) : '';
  $who = $p9 !== '' ? 'p:' . $p9
                    : 'n:' . strtolower(preg_replace('/\s+/u', ' ', crm_sheet_text($nom)));
  return $date . '|' . $who . '|' . strtolower(preg_replace('/\s+/u', ' ', crm_sheet_text($produit)));
}
/* كينقّي سطر الشيت ويحوّلو لطلبية CRM. كيرجع [سبب الرفض|null, الطلبية|null] */
function crm_sheet_norm($r) {
  $raw = isset($r['dateCreation']) ? $r['dateCreation'] : '';
  $dc = crm_sheet_date($raw);
  if ($dc === null || $dc === '') return array(crm_sheet_text($raw) === '' ? 'no-date' : 'bad-date', null);
  $tel = crm_sheet_phone(isset($r['telephone']) ? $r['telephone'] : '');
  $nom = crm_sheet_text(isset($r['nom']) ? $r['nom'] : '');
  if ($tel === '' && $nom === '') return array('no-name-or-phone', null);

  $o = array();
  $o['dateCreation'] = $dc;
  $dco = crm_sheet_date(isset($r['dateConfirmation']) ? $r['dateConfirmation'] : '');
  $o['dateConfirmation'] = ($dco === null || $dco === '') ? $dc : $dco;
  foreach (array('dateExp', 'dateLiv') as $f) {
    $x = crm_sheet_date(isset($r[$f]) ? $r[$f] : '');
    $o[$f] = ($x === null) ? '' : $x;
  }
  $o['telephone'] = $tel;
  $o['nom'] = $nom;
  foreach (array('idCmd','ville','adresse','produit','statut','livraison','remarques','agent','link',
                 'carousell','carosellFlag','originLead','livreur','tracking','motif','fees') as $f) {
    $o[$f] = crm_sheet_text(isset($r[$f]) ? $r[$f] : '');
  }
  $o['qte']        = max(1, (int)crm_sheet_num(isset($r['qte']) ? $r['qte'] : '', 1));
  $o['prix']       = crm_sheet_num(isset($r['prix']) ? $r['prix'] : '', 0);
  $o['upsell']     = crm_sheet_num(isset($r['upsell']) ? $r['upsell'] : '', 0);
  $o['commission'] = crm_sheet_num(isset($r['commission']) ? $r['commission'] : '', 0);
  return array(null, $o);
}
/* Storeep intake: كل طلبية جديدة كتتعيّن دائماً لمريم فقط.
 * التعيين مفروض فالسيرفر وما كيعتمدش على agent جاي من الشيت. */
function crm_sheet_orders($b) {
  global $LOCK_FILE;
  $rows = (isset($b['rows']) && is_array($b['rows'])) ? array_values($b['rows']) : null;
  if ($rows === null) crm_out(array('ok'=>false, 'err'=>'bad-rows'), 400);
  if (count($rows) > 2000) crm_out(array('ok'=>false, 'err'=>'too-many-rows', 'max'=>2000), 413);

  $fh = @fopen($LOCK_FILE, 'c');
  if ($fh) @flock($fh, LOCK_EX);

  $data = crm_read_raw(true);
  $cur = isset($data['paraveda_orders_v5']['d']) ? crm_unwrap($data['paraveda_orders_v5']['d']) : array();
  if (!is_array($cur)) $cur = array();
  $cur = array_values($cur);
  $prevT = isset($data['paraveda_orders_v5']['t']) ? (int)$data['paraveda_orders_v5']['t'] : 0;

  /* مفاتيح الطلبيات الموجودة (الحية) + أكبر id (حتى الممسوحة) باش ما نعاودوش نستعملو id */
  $keys = array(); $maxId = 0;
  foreach ($cur as $o) {
    if (!is_array($o)) continue;
    if (isset($o['id']) && is_numeric($o['id']) && (int)$o['id'] > $maxId) $maxId = (int)$o['id'];
    $keys[crm_sheet_key(
      isset($o['dateCreation']) ? (string)$o['dateCreation'] : '',
      isset($o['telephone'])    ? $o['telephone'] : '',
      isset($o['nom'])          ? $o['nom'] : '',
      isset($o['produit'])      ? $o['produit'] : ''
    )] = true;
  }

  $nowms  = (int)(microtime(true) * 1000);
  $nextId = max((int)(microtime(true) * 1000000), $maxId + 1);
  $out = array(); $added = 0; $dup = 0; $skip = 0;
  $addedBy = array();   // v3.98: الطلبيات الجداد لكل بنت (للإشعارات)
  foreach ($rows as $i => $r) {
    if (!is_array($r)) { $out[] = array('i'=>$i, 'st'=>'skip', 'why'=>'bad-row'); $skip++; continue; }
    list($why, $o) = crm_sheet_norm($r);
    if ($why !== null) { $out[] = array('i'=>$i, 'st'=>'skip', 'why'=>$why); $skip++; continue; }
    $k = crm_sheet_key($o['dateCreation'], $o['telephone'], $o['nom'], $o['produit']);
    if (isset($keys[$k])) { $out[] = array('i'=>$i, 'st'=>'dup'); $dup++; continue; }

    $o['agent'] = 'Meryam';                       // Storeep → مريم فقط (server-enforced)
    $o['idCmd'] = '1';                              // v3.98: ID ديما default = 1
    $o['src']   = 'sheet';
    $o['originLead'] = 'Facebook';                 // كل طلبيات الشيت جاية من Facebook
    $o['id'] = $nextId++;
    $o['_u'] = $nowms;
    $f = array();
    foreach ($o as $fk => $fv) { if ($fk !== 'id' && $fk !== '_u') $f[$fk] = $nowms; }
    $o['_f'] = $f;

    $cur[] = $o;
    $keys[$k] = true;
    $out[] = array('i'=>$i, 'st'=>'added', 'id'=>$o['id'], 'agent'=>$o['agent']);
    $added++;
    $addedBy[$o['agent']][] = array('nom'=>$o['nom'], 'produit'=>$o['produit'], 'ville'=>$o['ville']);
  }

  if ($added === 0) {
    if ($fh) { @flock($fh, LOCK_UN); @fclose($fh); }
    if ($skip > 0) crm_audit("sheet-orders | added=0 | dup=$dup | skip=$skip");
    crm_out(array('ok'=>true, 'added'=>0, 'dup'=>$dup, 'skip'=>$skip, 'results'=>$out));
  }

  crm_backup();
  $t = max($prevT + 1, $nowms);
  $data['paraveda_orders_v5'] = array('t' => $t, 'd' => $cur);
  $ok = crm_write_all($data);
  if ($ok) crm_journal_append('paraveda_orders_v5', $t, $cur);
  if ($fh) { @flock($fh, LOCK_UN); @fclose($fh); }

  if (!$ok) crm_out(array('ok'=>false, 'err'=>'write-failed'), 500);
  crm_audit("sheet-orders | added=$added | dup=$dup | skip=$skip | t=$t");
  try { crm_push_batch($addedBy); } catch (Throwable $__e) { crm_audit('push-error | ' . $__e->getMessage()); }   // v3.98: ما كيوقفش الصيفط
  crm_out(array('ok'=>true, 'added'=>$added, 'dup'=>$dup, 'skip'=>$skip, 't'=>$t, 'results'=>$out));
}

/* ================================================================
 * v3.100 — طلبية سريعة من البنت (من صفحة quick.html)
 *   POST api.php {action:'quick_order', agent:'imane', order:{nom, telephone, ville, adresse, produit, qte, prix, dateCreation?}}
 *   الطلبية كتتسجل باسم البنت لي داخلة بحسابها (ما كتدخلش فالدور ديال الشيت).
 *   كتصيفط إشعار لهاد البنت أوتوماتيك. التكرار: نفس التاريخ + الهاتف + المنتوج → 409.
 *   كيرجع: {ok, id, agent} | {ok:false, err}
 * ================================================================ */
function crm_quick_order($b) {
  global $LOCK_FILE;
  $agents = array('Meryam', 'AYA', 'imane', 'safa');
  $ag = isset($b['agent']) ? trim((string)$b['agent']) : '';
  if (!in_array($ag, $agents, true)) crm_out(array('ok'=>false, 'err'=>'bad-agent'), 400);
  $r = (isset($b['order']) && is_array($b['order'])) ? $b['order'] : null;
  if ($r === null) crm_out(array('ok'=>false, 'err'=>'bad-order'), 400);
  foreach (array('nom', 'telephone', 'ville', 'adresse', 'produit', 'qte', 'prix') as $f) {
    if (!isset($r[$f]) || trim((string)$r[$f]) === '') crm_out(array('ok'=>false, 'err'=>'missing-' . $f), 400);
  }
  if (!isset($r['dateCreation']) || trim((string)$r['dateCreation']) === '') $r['dateCreation'] = date('Y-m-d');
  list($why, $o) = crm_sheet_norm($r);
  if ($why !== null) crm_out(array('ok'=>false, 'err'=>$why), 400);
  if ($o['telephone'] === '') crm_out(array('ok'=>false, 'err'=>'missing-telephone'), 400);

  $fh = @fopen($LOCK_FILE, 'c');
  if ($fh) @flock($fh, LOCK_EX);
  $data = crm_read_raw(true);
  $cur = isset($data['paraveda_orders_v5']['d']) ? crm_unwrap($data['paraveda_orders_v5']['d']) : array();
  if (!is_array($cur)) $cur = array();
  $cur = array_values($cur);
  $prevT = isset($data['paraveda_orders_v5']['t']) ? (int)$data['paraveda_orders_v5']['t'] : 0;

  $keyNew = crm_sheet_key($o['dateCreation'], $o['telephone'], $o['nom'], $o['produit']);
  $maxId = 0;
  foreach ($cur as $x) {
    if (!is_array($x)) continue;
    if (isset($x['id']) && is_numeric($x['id']) && (int)$x['id'] > $maxId) $maxId = (int)$x['id'];
    if (!empty($x['_del'])) continue;
    $k = crm_sheet_key(
      isset($x['dateCreation']) ? (string)$x['dateCreation'] : '',
      isset($x['telephone'])    ? $x['telephone'] : '',
      isset($x['nom'])          ? $x['nom'] : '',
      isset($x['produit'])      ? $x['produit'] : ''
    );
    if ($k === $keyNew) {
      if ($fh) { @flock($fh, LOCK_UN); @fclose($fh); }
      crm_out(array('ok'=>false, 'err'=>'dup'), 409);
    }
  }

  $nowms = (int)(microtime(true) * 1000);
  $o['agent'] = $ag;
  $o['idCmd'] = '1';
  $o['src']   = 'manual';
  $o['id']    = max((int)(microtime(true) * 1000000), $maxId + 1);
  $o['_u']    = $nowms;
  $f = array();
  foreach ($o as $fk => $fv) { if ($fk !== 'id' && $fk !== '_u') $f[$fk] = $nowms; }
  $o['_f'] = $f;
  $cur[] = $o;

  crm_backup();
  $t = max($prevT + 1, $nowms);
  $data['paraveda_orders_v5'] = array('t' => $t, 'd' => $cur);
  $ok = crm_write_all($data);
  if ($ok) crm_journal_append('paraveda_orders_v5', $t, $cur);
  if ($fh) { @flock($fh, LOCK_UN); @fclose($fh); }
  if (!$ok) crm_out(array('ok'=>false, 'err'=>'write-failed'), 500);
  crm_audit("quick-order | agent=$ag | id=" . $o['id'] . " | t=$t");
  try {
    crm_push_batch(array($ag => array(array('nom'=>$o['nom'], 'produit'=>$o['produit'], 'ville'=>$o['ville']))));
  } catch (Throwable $__e) { crm_audit('push-error | ' . $__e->getMessage()); }
  crm_out(array('ok'=>true, 'id'=>$o['id'], 'agent'=>$ag, 't'=>$t));
}

/* ================================================================
 * v3.101 — Digylog: إرسال الطلبيات المؤكدة (Confirmé) أوتوماتيك
 *   كل بنت ليها متجر خاص فـDigylog (store). الطلبية كتمشي لمتجر البنت لي عندها.
 *   الإعدادات فملف digylog_cfg.json (التوكن ما كيتعرضش). كيتشغل بـcron:
 *     GET api.php?action=digylog_sync&token=...   (كل دقيقة)
 *   الطلبية كتتصيفط مرة وحدة: كتتعلم dlSent. إلا فشل، كتعاود (حتى 5 مرات).
 *   غير الطلبيات لي تأكدات (statut = Confirmé) بعد التفعيل (_f.statut >= since).
 * ================================================================ */
function crm_dl_base() { return 'https://api.digylog.com/api/v2/seller'; }
function crm_dl_agents() { return array('Meryam', 'AYA', 'imane', 'safa'); }
function crm_dl_cfg_paths() {
  global $DATA_DIR, $DIR_LOC, $DIR_EXT;
  $paths = array();
  foreach (array($DATA_DIR, $DIR_LOC, $DIR_EXT) as $dir) {
    $dir = rtrim((string)$dir, '/');
    if ($dir === '') continue;
    $path = $dir . '/digylog_cfg.json';
    if (!in_array($path, $paths, true)) $paths[] = $path;
  }
  return $paths;
}
function crm_dl_cfg_merge_missing($base, $other) {
  if (!is_array($base)) $base = array();
  if (!is_array($other)) return $base;
  foreach ($other as $k => $v) {
    if ($k === 'stores' && is_array($v)) {
      if (!isset($base[$k]) || !is_array($base[$k])) $base[$k] = array();
      foreach ($v as $agent => $store) if ((!isset($base[$k][$agent]) || trim((string)$base[$k][$agent]) === '') && trim((string)$store) !== '') $base[$k][$agent] = $store;
      continue;
    }
    $missing = !array_key_exists($k, $base) || $base[$k] === null || (is_string($base[$k]) && trim($base[$k]) === '');
    if ($missing && $v !== null && (!is_string($v) || trim($v) !== '')) $base[$k] = $v;
  }
  return $base;
}
function crm_dl_cfg_get() {
  $merged = array(); $sourceCount = 0; $active = null; $index = 0;
  foreach (crm_dl_cfg_paths() as $path) {
    $raw = @file_get_contents($path);
    $cfg = json_decode((string)$raw, true);
    if ($index === 0 && is_array($cfg)) $active = $cfg;
    $index++;
    if (!is_array($cfg)) continue;
    $merged = crm_dl_cfg_merge_missing($merged, $cfg);
    $sourceCount++;
  }
  /* Heal only when the active copy is missing fields found in its mirror. */
  if ($sourceCount > 0 && (!is_array($active) || json_encode($active) !== json_encode($merged))) crm_dl_cfg_set($merged);
  return $merged;
}
function crm_dl_cfg_set($c) {
  if (!is_array($c)) return false;
  $json = json_encode($c, JSON_UNESCAPED_UNICODE);
  if ($json === false) return false;
  $ok = false;
  foreach (crm_dl_cfg_paths() as $path) {
    $dir = dirname($path);
    if (!is_dir($dir)) continue;
    if (@file_put_contents($path, $json, LOCK_EX) !== false) $ok = true;
  }
  return $ok;
}
function crm_dl_http($method, $path, $token, $body = null) {
  if (!function_exists('curl_init')) return array(0, '', 'no-curl');
  $ch = curl_init(crm_dl_base() . $path);
  $h = array('Accept: application/json', 'Content-Type: application/json', 'Referer: https://apiseller.digylog.com', 'Authorization: Bearer ' . $token);
  curl_setopt($ch, CURLOPT_CUSTOMREQUEST, $method);
  curl_setopt($ch, CURLOPT_HTTPHEADER, $h);
  curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
  curl_setopt($ch, CURLOPT_CONNECTTIMEOUT, 10);
  curl_setopt($ch, CURLOPT_TIMEOUT, 25);
  if ($body !== null) curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($body, JSON_UNESCAPED_UNICODE));
  $resp = curl_exec($ch);
  $err  = (string)curl_error($ch);
  $code = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE);
  curl_close($ch);
  return array($code, $resp === false ? '' : (string)$resp, $err);
}
/* Read-only Digylog order lookup used by the clickable Tracking cell.
 * The configured bearer token never leaves the server and no CRM/Digylog data
 * is modified. Only Tracking numbers already present in this CRM are accepted. */
function crm_dl_order_status($b) {
  $tracking = strtoupper(trim((string)(isset($b['tracking']) ? $b['tracking'] : '')));
  if ($tracking === '' || !preg_match('/^[A-Z0-9_-]{3,80}$/', $tracking)) crm_out(array('ok'=>false, 'err'=>'bad-tracking'), 400);

  $data = crm_read_raw(true);
  $orders = isset($data['paraveda_orders_v5']['d']) ? crm_unwrap($data['paraveda_orders_v5']['d']) : array();
  $found = false;
  if (is_array($orders)) foreach ($orders as $o) {
    if (!is_array($o) || !empty($o['_del'])) continue;
    if (strtoupper(trim((string)(isset($o['tracking']) ? $o['tracking'] : ''))) === $tracking) { $found = true; break; }
  }
  if (!$found) crm_out(array('ok'=>false, 'err'=>'tracking-not-in-crm'), 404);

  $cfg = crm_dl_cfg_get();
  $token = isset($cfg['token']) ? trim((string)$cfg['token']) : '';
  if ($token === '') crm_out(array('ok'=>false, 'err'=>'no-digylog-token'), 503);

  list($infoCode, $infoBody, $infoErr) = crm_dl_http('GET', '/order/' . rawurlencode($tracking) . '/infos', $token);
  if ($infoCode < 200 || $infoCode >= 300) {
    crm_audit('digylog-order-status | tracking=' . $tracking . ' | http=' . $infoCode);
    crm_out(array('ok'=>false, 'err'=>'digylog-http', 'code'=>$infoCode), $infoCode === 404 ? 404 : 502);
  }
  $info = json_decode($infoBody, true);
  if (!is_array($info)) crm_out(array('ok'=>false, 'err'=>'digylog-invalid-response'), 502);

  list($refsCode, $refsBody, $refsErr) = crm_dl_http('GET', '/order/' . rawurlencode($tracking) . '/refs', $token);
  $refsRaw = $refsCode >= 200 && $refsCode < 300 ? json_decode($refsBody, true) : array();
  if (!is_array($refsRaw)) $refsRaw = array();
  $refs = array();
  foreach ($refsRaw as $r) if (is_array($r)) $refs[] = array(
    'designation'=>(string)(isset($r['designation']) ? $r['designation'] : ''),
    'quantity'=>max(1, (int)(isset($r['quantity']) ? $r['quantity'] : 1))
  );

  crm_out(array('ok'=>true, 'order'=>array(
    'tracking'=>(string)(isset($info['traking']) ? $info['traking'] : (isset($info['tracking']) ? $info['tracking'] : $tracking)),
    'status'=>(string)(isset($info['status']) ? $info['status'] : ''),
    'statusId'=>isset($info['idStatus']) ? $info['idStatus'] : null,
    'name'=>(string)(isset($info['name']) ? $info['name'] : ''),
    'phone'=>(string)(isset($info['phone']) ? $info['phone'] : ''),
    'city'=>(string)(isset($info['city']) ? $info['city'] : ''),
    'address'=>(string)(isset($info['address']) ? $info['address'] : ''),
    'price'=>isset($info['price']) ? $info['price'] : null,
    'createdAt'=>(string)(isset($info['createdAt']) ? $info['createdAt'] : ''),
    'updatedAt'=>(string)(isset($info['updatedAt']) ? $info['updatedAt'] : ''),
    'cashStatus'=>(string)(isset($info['cash_status']) ? $info['cash_status'] : ''),
    'paidAt'=>(string)(isset($info['paidAt']) ? $info['paidAt'] : ''),
    'store'=>(string)(isset($info['store']) ? $info['store'] : ''),
    'bl'=>(string)(isset($info['bl']) ? $info['bl'] : ''),
    'deliveryCost'=>isset($info['deliveryCost']) ? $info['deliveryCost'] : null,
    'refs'=>$refs
  )));
}

function crm_dl_order_row($o) {
  return array(
    'num'         => (string)$o['id'],
    'name'        => trim((string)$o['nom']),
    'phone'       => trim((string)$o['telephone']),
    'address'     => trim((string)$o['adresse']),
    'city'        => trim((string)$o['ville']),
    'price'       => (float)$o['prix'],
    'openproduct' => 1,
    'cantry'      => 0,
    'note'        => '',
    'refs'        => array(array('ref' => '', 'designation' => trim((string)$o['produit']), 'quantity' => max(1, (int)$o['qte'])))
  );
}
function crm_dl_body($store, $network, $sentType, $rows) {
  return array(
    'network'        => (int)$network,
    'store'          => (string)$store,
    'sentType'       => (int)$sentType,
    'checkDuplicate' => 1,
    'orders'         => $rows
  );
}
/* admin: POST {action:'digylog_admin', op:'get'|'save'|'test'|'dry'} + header X-Sync-Token */
function crm_dl_admin($b) {
  global $SECRET, $AUDIT_FILE;
  if (!hash_equals($SECRET, crm_token())) crm_out(array('ok'=>false, 'err'=>'token'), 403);
  $op = isset($b['op']) ? (string)$b['op'] : 'get';
  $c = crm_dl_cfg_get();
  $t = isset($c['token']) ? (string)$c['token'] : '';
  $sellerToken = isset($c['sellerToken']) ? crm_tracking_bearer($c['sellerToken']) : '';
  $stores = array();
  foreach (crm_dl_agents() as $ag) $stores[$ag] = (isset($c['stores'][$ag]) ? (string)$c['stores'][$ag] : '');

  if ($op === 'get') {
    crm_out(array('ok'=>true, 'cfg'=>array(
      'enabled'   => !empty($c['enabled']) ? 1 : 0,
      'network'   => isset($c['network']) ? (int)$c['network'] : 1,
      'sentType'  => isset($c['sentType']) ? (int)$c['sentType'] : 0,
      'stores'    => $stores,
      'since'     => isset($c['since']) ? (int)$c['since'] : 0,
      'hasToken'  => $t !== '',
      'tokenTail' => $t !== '' ? substr($t, -4) : '',
      'hasSellerToken' => $sellerToken !== '',
      'sellerTokenTail' => $sellerToken !== '' ? substr($sellerToken, -4) : ''
    )));
  }
  if ($op === 'tracking_token_save') {
    $incoming = isset($b['sellerToken']) ? crm_tracking_bearer($b['sellerToken']) : '';
    if ($incoming === '') crm_out(array('ok'=>false,'err'=>'no-seller-token'),400);
    $c['sellerToken'] = $incoming;
    crm_dl_cfg_set($c);
    crm_audit('digylog-seller-token-saved | tail=' . substr($incoming,-4));
    crm_out(array('ok'=>true,'hasSellerToken'=>true,'sellerTokenTail'=>substr($incoming,-4)));
  }
  if ($op === 'save') {
    if (isset($b['token']) && trim((string)$b['token']) !== '') $c['token'] = trim((string)$b['token']);
    if (isset($b['network'])) $c['network'] = (int)$b['network'];
    if (isset($b['sentType'])) {
      $st = (int)$b['sentType'];
      if (!in_array($st, array(0, 1, 2), true)) crm_out(array('ok'=>false, 'err'=>'bad-sentType'), 400);
      $c['sentType'] = $st;
    }
    if (isset($b['stores']) && is_array($b['stores'])) {
      $s = array();
      foreach (crm_dl_agents() as $ag) $s[$ag] = isset($b['stores'][$ag]) ? trim((string)$b['stores'][$ag]) : '';
      $c['stores'] = $s;
    }
    $en = !empty($b['enabled']) ? 1 : 0;
    if ($en && empty($c['enabled'])) $c['since'] = (int)(microtime(true) * 1000);   // أول تفعيل: غير الطلبيات الجداد
    $c['enabled'] = $en;
    crm_dl_cfg_set($c);
    crm_audit('digylog-save | enabled=' . $en . ' | sentType=' . (isset($c['sentType']) ? $c['sentType'] : 0));
    crm_out(array('ok'=>true));
  }
  if ($op === 'test') {
    if ($t === '') crm_out(array('ok'=>false, 'err'=>'no-token'), 400);
    $out = array();
    foreach (array('/networks', '/stores') as $p) {
      list($code, $body, $err) = crm_dl_http('GET', $p, $t);
      $out[$p] = array('code'=>$code, 'body'=>substr($body, 0, 1500), 'err'=>$err);
    }
    /* PUT /webhook/test: Digylog يصيفط حدث تجريبي لـwebhook المسجل (num=55 ما كاينش فـCRM، كيتجاهل).
     * إلا 400 "webhook not configured" = ما كاينش webhook مسجل. */
    list($tc, $tb, $te) = crm_dl_http('PUT', '/webhook/test', $t, array('eventType' => 'order-status-changed'));
    $out['/webhook/test'] = array('code'=>$tc, 'body'=>substr($tb, 0, 1500), 'err'=>$te);
    /* تشخيص: السيرفر كيجرب الـwebhook نفسو (نفس الرابط اللي مسجل فـDigylog) وكيعرض الجواب */
    $selfBody = json_encode(array('eventType'=>'order-status-changed', 'payload'=>array('num'=>'55', 'idStatus'=>'6', 'status'=>'Livrée')));
    $ch = curl_init('https://paraveda.store/api.php?action=digylog_hook&token=' . urlencode($SECRET));
    curl_setopt_array($ch, array(CURLOPT_POST=>true, CURLOPT_POSTFIELDS=>$selfBody, CURLOPT_HTTPHEADER=>array('Content-Type: application/json'), CURLOPT_RETURNTRANSFER=>true, CURLOPT_TIMEOUT=>15));
    $sb = curl_exec($ch); $sc = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE); $se = (string)curl_error($ch); curl_close($ch);
    $out['/self-hook'] = array('code'=>$sc, 'body'=>substr((string)$sb, 0, 800), 'err'=>$se);
    /* تشخيص: آخر سطور الـwebhook من audit.log (شكل الطلب الحقيقي اللي وصل من Digylog) */
    $__al = (is_file($AUDIT_FILE)) ? array_slice(array_values(array_filter(explode("\n", (string)@file_get_contents($AUDIT_FILE)))), -500) : array();
    $__hk = array_values(array_filter($__al, function ($l) { return strpos($l, 'digylog-hook') !== false; }));
    $out['/hook-log'] = array('lines' => array_slice($__hk, -6));
    crm_out(array('ok'=>true, 'test'=>$out));
  }
  if ($op === 'tracking_candidates') crm_out(crm_tracking_candidates());
  if ($op === 'tracking_sync') {
    $ids = isset($b['ids']) && is_array($b['ids']) ? $b['ids'] : array();
    $syncToken = isset($b['sellerToken']) && trim((string)$b['sellerToken']) !== '' ? (string)$b['sellerToken'] : $sellerToken;
    crm_out(crm_tracking_sync($ids, $syncToken));
  }
  if ($op === 'delivery_sync') {
    $tracking = strtoupper(trim((string)(isset($b['tracking']) ? $b['tracking'] : '')));
    if ($tracking !== '' && !preg_match('/^[A-Z0-9_-]{3,80}$/', $tracking)) crm_out(array('ok'=>false,'err'=>'bad-tracking'),400);
    crm_out(crm_delivery_sync_batch($tracking !== '' ? 1 : 20, $tracking));
  }
  if ($op === 'dry') crm_out(crm_dl_run(true));
  crm_out(array('ok'=>false, 'err'=>'bad-op'), 400);
}

/* ================= Tracking-only Digylog import =================
 * هاد المسار مسموح ليه يكتب tracking فقط. ما كيقراش status وما كيكتبش
 * livraison/dateLiv/statut نهائياً. الـwebhook ديال الحالات باقي موقوف. */
function crm_tracking_bearer($raw) {
  $v = trim((string)$raw, " \t\r\n\"'");
  $v = preg_replace('/^authorization\s*:\s*/i', '', $v);
  $v = preg_replace('/^bearer\s+/i', '', trim($v));
  return trim($v, " \t\r\n\"'");
}
function crm_tracking_phone($v) {
  $d = preg_replace('/\D+/', '', (string)$v);
  if (strlen($d) === 12 && strpos($d, '212') === 0) $d = '0' . substr($d, 3);
  return $d;
}
function crm_tracking_norm($v) {
  $v = trim((string)$v);
  $v = function_exists('mb_strtolower') ? mb_strtolower($v, 'UTF-8') : strtolower($v);
  $v = str_replace(array('é','è','ê','ë','à','â','ä','î','ï','ô','ö','ù','û','ü','ç'), array('e','e','e','e','a','a','a','i','i','o','o','u','u','u','c'), $v);
  return preg_replace('/[^a-z0-9]+/u', '', $v);
}
function crm_tracking_pick($a, $keys) {
  if (!is_array($a)) return '';
  foreach ($keys as $k) if (array_key_exists($k,$a) && !is_array($a[$k]) && !is_object($a[$k]) && trim((string)$a[$k]) !== '') return trim((string)$a[$k]);
  return '';
}
function crm_tracking_deep_pick($a,$keys,$depth=0) {
  if(!is_array($a)||$depth>6)return '';
  $v=crm_tracking_pick($a,$keys);if($v!=='')return $v;
  foreach($a as $child)if(is_array($child)){ $v=crm_tracking_deep_pick($child,$keys,$depth+1);if($v!=='')return $v; }
  return '';
}
function crm_tracking_date($v) {
  $v=trim((string)$v); if($v==='')return '';
  if(preg_match('/^(\d{4})[-\/]?(\d{2})[-\/]?(\d{2})/',$v,$m))return $m[1].'-'.$m[2].'-'.$m[3];
  if(preg_match('/^(\d{2})[\/\-](\d{2})[\/\-](\d{4})/',$v,$m))return $m[3].'-'.$m[2].'-'.$m[1];
  return '';
}
function crm_tracking_records($v, &$out, $depth=0) {
  if($depth>10 || !is_array($v))return;
  $tr=crm_tracking_pick($v,array('traking','tracking','trackingNumber','tracking_number','barcode'));
  if($tr!=='' && preg_match('/^[A-Za-z0-9_-]{5,40}$/',$tr)) {
    $key=strtoupper($tr); if(!isset($out[$key]))$out[$key]=$v;
  }
  foreach($v as $child)if(is_array($child))crm_tracking_records($child,$out,$depth+1);
}
function crm_tracking_internal_get($phone, $token) {
  if(!function_exists('curl_init'))return array(0,'','no-curl');
  $url='https://api.digylog.com/api/seller/v48/historic/orders?phone='.rawurlencode($phone).'&datatype=1&countPerPage=100&currentPage=1&sort=0';
  $ch=curl_init($url);
  curl_setopt_array($ch,array(CURLOPT_HTTPHEADER=>array('Accept: application/json, text/plain, */*','Referer: https://seller.digylog.com/','Origin: https://seller.digylog.com','Authorization: Bearer '.$token),CURLOPT_RETURNTRANSFER=>true,CURLOPT_CONNECTTIMEOUT=>10,CURLOPT_TIMEOUT=>25));
  $body=curl_exec($ch);$err=(string)curl_error($ch);$code=(int)curl_getinfo($ch,CURLINFO_HTTP_CODE);curl_close($ch);
  return array($code,$body===false?'':(string)$body,$err);
}
function crm_tracking_candidates() {
  $data=crm_read_raw(true);$orders=isset($data['paraveda_orders_v5']['d'])?crm_unwrap($data['paraveda_orders_v5']['d']):array();if(!is_array($orders))$orders=array();
  $ids=array();foreach($orders as $o){if(!is_array($o)||!empty($o['_del'])||trim((string)(isset($o['tracking'])?$o['tracking']:''))!==''||crm_tracking_phone(isset($o['telephone'])?$o['telephone']:'')==='')continue;
    $liv=crm_tracking_norm(isset($o['livraison'])?$o['livraison']:'');
    if(!empty($o['dlSent'])||in_array($liv,array('expediervers','livree','retour','retournee','rembourse','rechange'),true))$ids[]=(string)$o['id'];
  }
  return array('ok'=>true,'ids'=>$ids,'total'=>count($ids));
}
function crm_tracking_score($record,$order) {
  $ref=crm_tracking_deep_pick($record,array('num','externalReference','external_reference','clientReference','client_reference','reference','ref','orderNumber','order_number'));
  if($ref!=='' && $ref===(string)$order['id'])return array('score'=>100,'safe'=>true,'why'=>'crm-reference');
  $rd=crm_tracking_date(crm_tracking_deep_pick($record,array('createdAt','created_at','date','creationDate','dateCreation','createdDate')));
  $od=crm_tracking_date(isset($order['dateCreation'])?$order['dateCreation']:'');$dateOk=($rd!==''&&$od!==''&&$rd===$od);$score=$dateOk?10:0;$extra=0;
  $rp=crm_tracking_deep_pick($record,array('price','prix','amount','total','orderPrice'));
  if($rp!==''&&is_numeric($rp)&&abs((float)$rp-(float)(isset($order['prix'])?$order['prix']:0))<0.01){$score+=4;$extra++;}
  $rc=crm_tracking_norm(crm_tracking_deep_pick($record,array('city','ville','destination','cityName')));
  if($rc!==''&&$rc===crm_tracking_norm(isset($order['ville'])?$order['ville']:'')){$score+=3;$extra++;}
  $rn=crm_tracking_norm(crm_tracking_deep_pick($record,array('name','nom','fullname','customerName','client')));
  if($rn!==''&&$rn===crm_tracking_norm(isset($order['nom'])?$order['nom']:'')){$score+=2;$extra++;}
  return array('score'=>$score,'safe'=>($dateOk&&$extra>0),'why'=>$dateOk?'date+extra':'insufficient');
}
function crm_tracking_sync($requestedIds,$rawToken) {
  global $LOCK_FILE;
  $token=crm_tracking_bearer($rawToken);if($token==='')return array('ok'=>false,'err'=>'no-seller-token');
  $want=array();foreach($requestedIds as $id){$id=(string)$id;if($id!=='')$want[$id]=true;if(count($want)>=20)break;}if(!$want)return array('ok'=>false,'err'=>'no-ids');
  $data=crm_read_raw(true);$orders=isset($data['paraveda_orders_v5']['d'])?crm_unwrap($data['paraveda_orders_v5']['d']):array();if(!is_array($orders))$orders=array();$todo=array();
  foreach($orders as $o){$id=is_array($o)&&isset($o['id'])?(string)$o['id']:'';if($id!==''&&isset($want[$id])&&empty($o['_del'])&&trim((string)(isset($o['tracking'])?$o['tracking']:''))==='')$todo[]=$o;}
  $found=array();$cache=array();$checked=0;$notFound=0;$ambiguous=0;$httpCode=0;
  foreach($todo as $o){$phone=crm_tracking_phone(isset($o['telephone'])?$o['telephone']:'');if($phone===''){continue;}$checked++;
    if(!isset($cache[$phone])){list($code,$body,$err)=crm_tracking_internal_get($phone,$token);$httpCode=$code;$records=array();if($code>=200&&$code<300){$j=json_decode($body,true);if(is_array($j))crm_tracking_records($j,$records);}$cache[$phone]=array('code'=>$code,'records'=>$records);}
    $pack=$cache[$phone];if($pack['code']<200||$pack['code']>=300)return array('ok'=>false,'err'=>'digylog-http-'.$pack['code'],'code'=>$pack['code'],'checked'=>$checked-1);
    $best='';$bestScore=-1;$ties=0;$bestSafe=false;
    foreach($pack['records'] as $tr=>$record){$m=crm_tracking_score($record,$o);if($m['score']>$bestScore){$best=$tr;$bestScore=$m['score'];$bestSafe=$m['safe'];$ties=1;}elseif($m['score']===$bestScore)$ties++;}
    if($best!==''&&$bestSafe&&$ties===1)$found[(string)$o['id']]=$best;elseif(count($pack['records'])===0)$notFound++;else$ambiguous++;
  }
  $linked=0;if($found){$fh=@fopen($LOCK_FILE,'c');if($fh)@flock($fh,LOCK_EX);$data=crm_read_raw(true);$cur=isset($data['paraveda_orders_v5']['d'])?crm_unwrap($data['paraveda_orders_v5']['d']):array();if(!is_array($cur))$cur=array();$prevT=isset($data['paraveda_orders_v5']['t'])?(int)$data['paraveda_orders_v5']['t']:0;$now=(int)(microtime(true)*1000);
    foreach($cur as $i=>$o){$id=is_array($o)&&isset($o['id'])?(string)$o['id']:'';if($id===''||!isset($found[$id])||trim((string)(isset($o['tracking'])?$o['tracking']:''))!=='')continue;if(!isset($o['_f'])||!is_array($o['_f']))$o['_f']=array();
      /* السطر الوحيد المسموح به: tracking. لا Suivie لا status لا تاريخ. */
      $o['tracking']=$found[$id];$o['_f']['tracking']=$now;$o['_u']=$now;$cur[$i]=$o;$linked++;}
    if($linked){crm_backup();$t=max($prevT+1,$now);$data['paraveda_orders_v5']=array('t'=>$t,'d'=>array_values($cur));$ok=crm_write_all($data);if($ok)crm_journal_append('paraveda_orders_v5',$t,array_values($cur));}
    if($fh){@flock($fh,LOCK_UN);@fclose($fh);}}
  crm_audit('tracking-only-sync | checked='.$checked.' | linked='.$linked.' | ambiguous='.$ambiguous.' | notFound='.$notFound);
  return array('ok'=>true,'checked'=>$checked,'linked'=>$linked,'ambiguous'=>$ambiguous,'notFound'=>$notFound,'httpCode'=>$httpCode,'trackingOnly'=>true);
}


/* Automatic Tracking import after a CRM order is sent to Digylog.
 * Phone is used only to ask Digylog for a small candidate set. Assignment is
 * NEVER made by phone/name/date: the Digylog record must carry the exact CRM
 * order id in its `num`/reference field. The only CRM field written is tracking. */
function crm_tracking_exact_from_payload($payload,$orderId) {
  $records=array();crm_tracking_records($payload,$records);$hits=array();
  foreach($records as $tracking=>$record){
    $ref=crm_tracking_deep_pick($record,array('num','orderNum','order_num','externalId','external_id','externalReference','external_reference','clientReference','client_reference','reference','ref','orderNumber','order_number'));
    if($ref!=='' && (string)$ref===(string)$orderId)$hits[strtoupper((string)$tracking)]=true;
  }
  $keys=array_keys($hits);return count($keys)===1?$keys[0]:'';
}
function crm_tracking_internal_many($phones,$token) {
  $phones=array_values(array_unique(array_filter($phones)));$out=array();
  if(!$phones)return $out;
  if(!function_exists('curl_multi_init')){
    foreach($phones as $phone){list($code,$body,$err)=crm_tracking_internal_get($phone,$token);$out[$phone]=array('code'=>$code,'body'=>$body,'err'=>$err);}return $out;
  }
  $mh=curl_multi_init();$chs=array();
  foreach($phones as $phone){
    $url='https://api.digylog.com/api/seller/v48/historic/orders?phone='.rawurlencode($phone).'&datatype=1&countPerPage=100&currentPage=1&sort=0';
    $ch=curl_init($url);curl_setopt_array($ch,array(CURLOPT_HTTPHEADER=>array('Accept: application/json, text/plain, */*','Referer: https://seller.digylog.com/','Origin: https://seller.digylog.com','Authorization: Bearer '.$token),CURLOPT_RETURNTRANSFER=>true,CURLOPT_CONNECTTIMEOUT=>8,CURLOPT_TIMEOUT=>20));
    curl_multi_add_handle($mh,$ch);$chs[$phone]=$ch;
  }
  $running=null;do{$mrc=curl_multi_exec($mh,$running);if($running)curl_multi_select($mh,1.0);}while($running&&$mrc===CURLM_OK);
  foreach($chs as $phone=>$ch){$out[$phone]=array('code'=>(int)curl_getinfo($ch,CURLINFO_HTTP_CODE),'body'=>(string)curl_multi_getcontent($ch),'err'=>(string)curl_error($ch));curl_multi_remove_handle($mh,$ch);curl_close($ch);}curl_multi_close($mh);
  return $out;
}
function crm_tracking_auto_sync($limit=30) {
  global $LOCK_FILE;
  $cfg=crm_dl_cfg_get();$token=isset($cfg['sellerToken'])?crm_tracking_bearer($cfg['sellerToken']):'';
  if($token==='')return array('ok'=>false,'err'=>'no-seller-token','checked'=>0,'linked'=>0);
  $data=crm_read_raw(true);$orders=isset($data['paraveda_orders_v5']['d'])?crm_unwrap($data['paraveda_orders_v5']['d']):array();if(!is_array($orders))$orders=array();
  $candidates=array();
  foreach($orders as $o){
    if(!is_array($o)||!empty($o['_del'])||trim((string)(isset($o['tracking'])?$o['tracking']:''))!=='')continue;
    $liv=crm_tracking_norm(isset($o['livraison'])?$o['livraison']:'');if(empty($o['dlSent'])&&$liv!=='expediervers')continue;
    $id=isset($o['id'])?(string)$o['id']:'';$phone=crm_tracking_phone(isset($o['telephone'])?$o['telephone']:'');if($id===''||$phone==='')continue;
    $candidates[]=array('id'=>$id,'phone'=>$phone);
  }
  $total=count($candidates);if(!$total)return array('ok'=>true,'checked'=>0,'pending'=>0,'linked'=>0,'exactOnly'=>true);
  $take=min(max(1,(int)$limit),$total);$cursor=isset($cfg['trackingCursor'])?max(0,(int)$cfg['trackingCursor']):0;if($cursor>=$total)$cursor=0;$batch=array();
  for($i=0;$i<$take;$i++)$batch[]=$candidates[($cursor+$i)%$total];
  $cfg['trackingCursor']=($cursor+$take)%max(1,$total);crm_dl_cfg_set($cfg);
  $phones=array_map(function($x){return $x['phone'];},$batch);$responses=crm_tracking_internal_many($phones,$token);$found=array();$httpErrors=0;$ambiguous=0;
  foreach($batch as $item){$pack=isset($responses[$item['phone']])?$responses[$item['phone']]:array('code'=>0,'body'=>'');if($pack['code']<200||$pack['code']>=300){$httpErrors++;continue;}$payload=json_decode($pack['body'],true);if(!is_array($payload))continue;$tracking=crm_tracking_exact_from_payload($payload,$item['id']);if($tracking!=='')$found[$item['id']]=$tracking;else$ambiguous++;}
  $linked=0;if($found){
    $fh=@fopen($LOCK_FILE,'c');if($fh)@flock($fh,LOCK_EX);$data=crm_read_raw(true);$cur=isset($data['paraveda_orders_v5']['d'])?crm_unwrap($data['paraveda_orders_v5']['d']):array();if(!is_array($cur))$cur=array();$prevT=isset($data['paraveda_orders_v5']['t'])?(int)$data['paraveda_orders_v5']['t']:0;$now=(int)(microtime(true)*1000);
    foreach($cur as $i=>$o){$id=is_array($o)&&isset($o['id'])?(string)$o['id']:'';if($id===''||!isset($found[$id])||trim((string)(isset($o['tracking'])?$o['tracking']:''))!=='')continue;if(!isset($o['_f'])||!is_array($o['_f']))$o['_f']=array();$o['tracking']=$found[$id];$o['_f']['tracking']=$now;$o['_u']=$now;$cur[$i]=$o;$linked++;}
    if($linked){crm_backup();$t=max($prevT+1,$now);$data['paraveda_orders_v5']=array('t'=>$t,'d'=>array_values($cur));$ok=crm_write_all($data);if($ok)crm_journal_append('paraveda_orders_v5',$t,array_values($cur));}
    if($fh){@flock($fh,LOCK_UN);@fclose($fh);}
  }
  crm_audit('digylog-tracking-auto | checked='.count($batch).' | linked='.$linked.' | exactMiss='.$ambiguous.' | httpErrors='.$httpErrors);
  return array('ok'=>true,'checked'=>count($batch),'pending'=>$total,'linked'=>$linked,'exactMiss'=>$ambiguous,'httpErrors'=>$httpErrors,'exactOnly'=>true);
}
/* Browser-triggered sync: makes the feature automatic while the CRM is open,
 * even when hosting cron is missing. A server lock/throttle means all staff
 * devices together can start at most one Digylog lookup every 45 seconds. */
function crm_tracking_auto_guarded() {
  global $DATA_DIR;
  $lock=@fopen($DATA_DIR.'/.tracking-auto.lock','c');
  if(!$lock||!@flock($lock,LOCK_EX|LOCK_NB)){if($lock)@fclose($lock);return array('ok'=>true,'skipped'=>'busy','linked'=>0);}
  $stamp=$DATA_DIR.'/.tracking-auto.stamp';$last=is_file($stamp)?(int)@filemtime($stamp):0;
  if($last>0&&time()-$last<45){@flock($lock,LOCK_UN);@fclose($lock);return array('ok'=>true,'skipped'=>'throttled','retryAfter'=>45-(time()-$last),'linked'=>0);}
  @touch($stamp);
  $result=crm_tracking_auto_sync(30);
  /* The same guarded browser heartbeat also checks final Digylog delivery states.
     This keeps Livrée working and adds Retournée without a second client timer. */
  $result['deliverySync']=crm_delivery_auto_guarded();
  @flock($lock,LOCK_UN);@fclose($lock);return $result;
}

/* ================= Livrée + Retournée sync by exact Tracking =================
 * The stored Tracking is the only matching key. The only business field this
 * process may write is livraison: Digylog Livrée -> Livrée, Retournée -> Retour.
 * It never writes statut, dateLiv, tracking, client data, prices, or other fields. */
function crm_delivery_status($info) {
  if(!is_array($info))return '';
  /* Prefer real status fields. A generic top-level `label` can be the parcel
     label/barcode and must never hide the actual Digylog status. */
  $st=crm_tracking_deep_pick($info,array('statusName','status_name','orderStatus','order_status','statut','status','stateName','state_name','state'));
  if($st==='')$st=crm_tracking_deep_pick($info,array('label'));
  $n=crm_tracking_norm($st);
  /* Digylog may append the return reason to “Retournée”. Match that terminal
     prefix, while still refusing a generic intermediate “Retour ...” state. */
  if(strpos($n,'retourne')===0)return 'Retour';
  $id=crm_tracking_deep_pick($info,array('idStatus','statusId','status_id','id_status'));
  if((string)$id==='6'||$n==='livree'||strpos($n,'livree')===0)return 'Livrée';
  return '';
}
function crm_delivery_is_delivered($info) { return crm_delivery_status($info)==='Livrée'; }
function crm_delivery_is_returned($info) { return crm_delivery_status($info)==='Retour'; }
function crm_delivery_fetch_infos($trackings,$token) {
  $out=array();if(!function_exists('curl_multi_init'))return $out;
  $mh=curl_multi_init();$chs=array();
  foreach($trackings as $tr){$tr=strtoupper(trim((string)$tr));if($tr==='')continue;
    $ch=curl_init(crm_dl_base().'/order/'.rawurlencode($tr).'/infos');
    curl_setopt_array($ch,array(CURLOPT_HTTPHEADER=>array('Accept: application/json','Referer: https://apiseller.digylog.com','Authorization: Bearer '.$token),CURLOPT_RETURNTRANSFER=>true,CURLOPT_CONNECTTIMEOUT=>8,CURLOPT_TIMEOUT=>20));
    curl_multi_add_handle($mh,$ch);$chs[$tr]=$ch;
  }
  $running=null;do{$mrc=curl_multi_exec($mh,$running);if($running)curl_multi_select($mh,1.0);}while($running&&$mrc===CURLM_OK);
  foreach($chs as $tr=>$ch){
    $code=(int)curl_getinfo($ch,CURLINFO_HTTP_CODE);$body=(string)curl_multi_getcontent($ch);$j=json_decode($body,true);
    $state=($code>=200&&$code<300&&is_array($j))?crm_delivery_status($j):'';
    $out[$tr]=array('code'=>$code,'state'=>$state,'delivered'=>$state==='Livrée','returned'=>$state==='Retour');
    curl_multi_remove_handle($mh,$ch);curl_close($ch);
  }
  curl_multi_close($mh);return $out;
}
function crm_delivery_sync_batch($limit=20,$onlyTracking='') {
  global $LOCK_FILE;
  $cfg=crm_dl_cfg_get();$token=isset($cfg['token'])?trim((string)$cfg['token']):'';if($token==='')return array('ok'=>false,'err'=>'no-token','checked'=>0,'updated'=>0);
  $onlyTracking=strtoupper(trim((string)$onlyTracking));
  $data=crm_read_raw(true);$orders=isset($data['paraveda_orders_v5']['d'])?crm_unwrap($data['paraveda_orders_v5']['d']):array();if(!is_array($orders))$orders=array();
  /* Retour is terminal. Livrée remains eligible because a delivered parcel can
     later be returned. Active deliveries are checked before already-Livrée rows. */
  $map=array();foreach($orders as $o){
    if(!is_array($o)||!empty($o['_del']))continue;$tr=strtoupper(trim((string)(isset($o['tracking'])?$o['tracking']:'')));$liv=trim((string)(isset($o['livraison'])?$o['livraison']:''));
    if($tr===''||$liv==='Retour'||($onlyTracking!==''&&$tr!==$onlyTracking))continue;
    if(!isset($map[$tr]))$map[$tr]=array('count'=>0,'priority'=>$liv==='Livrée'?1:0);$map[$tr]['count']++;if($liv!=='Livrée')$map[$tr]['priority']=0;
  }
  /* A duplicated Tracking is ambiguous and is never allowed to modify rows.
     Active and already-Livrée rows have independent cursors: old delivered
     history can never postpone current Expédier-vers returns again. */
  $active=array();$final=array();$ambiguous=0;
  foreach($map as $tr=>$meta){if($meta['count']!==1){$ambiguous++;continue;}if($meta['priority']===0)$active[]=$tr;else $final[]=$tr;}
  sort($active);sort($final);$total=count($active)+count($final);
  if($total===0)return array('ok'=>true,'checked'=>0,'pending'=>0,'activePending'=>0,'finalPending'=>0,'delivered'=>0,'returned'=>0,'updated'=>0,'ambiguous'=>$ambiguous,'requestedTracking'=>$onlyTracking,'exactOnly'=>true);
  $limit=max(1,(int)$limit);$batch=array();
  if($onlyTracking!=='')$batch=array_merge($active,$final);
  else{
    $activeN=count($active);$finalN=count($final);$activeTake=$activeN?min($activeN,max(1,(int)ceil($limit*.8))):0;$finalTake=$finalN?min($finalN,max(0,$limit-$activeTake)):0;
    $left=$limit-$activeTake-$finalTake;if($left>0&&$activeTake<$activeN){$add=min($left,$activeN-$activeTake);$activeTake+=$add;$left-=$add;}if($left>0&&$finalTake<$finalN)$finalTake+=min($left,$finalN-$finalTake);
    $activeCursor=isset($cfg['deliveryActiveCursor'])?max(0,(int)$cfg['deliveryActiveCursor']):0;if($activeCursor>=max(1,$activeN))$activeCursor=0;
    $finalCursor=isset($cfg['deliveryFinalCursor'])?max(0,(int)$cfg['deliveryFinalCursor']):0;if($finalCursor>=max(1,$finalN))$finalCursor=0;
    for($i=0;$i<$activeTake;$i++)$batch[]=$active[($activeCursor+$i)%$activeN];for($i=0;$i<$finalTake;$i++)$batch[]=$final[($finalCursor+$i)%$finalN];
    $cfg['deliveryActiveCursor']=$activeN?(($activeCursor+$activeTake)%$activeN):0;$cfg['deliveryFinalCursor']=$finalN?(($finalCursor+$finalTake)%$finalN):0;crm_dl_cfg_set($cfg);
  }
  $infos=crm_delivery_fetch_infos($batch,$token);$targets=array();$delivered=0;$returned=0;$httpErrors=0;$unrecognized=0;
  foreach($infos as $tr=>$r){$state=isset($r['state'])?(string)$r['state']:'';if(isset($r['code'])&&((int)$r['code']<200||(int)$r['code']>=300))$httpErrors++;elseif($state==='Livrée'){$targets[$tr]=$state;$delivered++;}elseif($state==='Retour'){$targets[$tr]=$state;$returned++;}else $unrecognized++;}
  $updated=0;$writeOk=true;if($targets){
    $fh=@fopen($LOCK_FILE,'c');if($fh)@flock($fh,LOCK_EX);$data=crm_read_raw(true);$cur=isset($data['paraveda_orders_v5']['d'])?crm_unwrap($data['paraveda_orders_v5']['d']):array();if(!is_array($cur))$cur=array();$prevT=isset($data['paraveda_orders_v5']['t'])?(int)$data['paraveda_orders_v5']['t']:0;$now=(int)(microtime(true)*1000);
    foreach($cur as $i=>$o){
      if(!is_array($o)||!empty($o['_del']))continue;$tr=strtoupper(trim((string)(isset($o['tracking'])?$o['tracking']:'')));if(!isset($targets[$tr]))continue;
      $next=$targets[$tr];$liv=trim((string)(isset($o['livraison'])?$o['livraison']:''));
      /* Never regress a confirmed return back to Livrée. */
      if($liv===$next||($liv==='Retour'&&$next==='Livrée'))continue;
      if(!isset($o['_f'])||!is_array($o['_f']))$o['_f']=array();
      /* The only business-field write performed by this sync. */
      $o['livraison']=$next;$o['_f']['livraison']=$now;$o['_u']=$now;$cur[$i]=$o;$updated++;
    }
    if($updated){crm_backup();$t=max($prevT+1,$now);$data['paraveda_orders_v5']=array('t'=>$t,'d'=>array_values($cur));$writeOk=crm_write_all($data);if($writeOk)crm_journal_append('paraveda_orders_v5',$t,array_values($cur));else $updated=0;}
    if($fh){@flock($fh,LOCK_UN);@fclose($fh);}
  }
  crm_audit('digylog-delivery-tracking-only | checked='.count($batch).' | delivered='.$delivered.' | returned='.$returned.' | updated='.$updated.' | ambiguous='.$ambiguous.' | httpErrors='.$httpErrors.' | unrecognized='.$unrecognized.' | writeOk='.($writeOk?1:0));
  return array('ok'=>(bool)$writeOk,'checked'=>count($batch),'pending'=>$total,'activePending'=>count($active),'finalPending'=>count($final),'delivered'=>$delivered,'returned'=>$returned,'updated'=>$updated,'ambiguous'=>$ambiguous,'httpErrors'=>$httpErrors,'unrecognized'=>$unrecognized,'requestedTracking'=>$onlyTracking,'exactOnly'=>true);
}
/* Dedicated automatic status heartbeat, independent from Tracking import and
 * shared by every open CRM device. At most one batch runs every 45 seconds. */
function crm_delivery_auto_guarded() {
  global $DATA_DIR;
  $lock=@fopen($DATA_DIR.'/.delivery-auto.lock','c');
  if(!$lock||!@flock($lock,LOCK_EX|LOCK_NB)){if($lock)@fclose($lock);return array('ok'=>true,'skipped'=>'busy','updated'=>0);}
  $stamp=$DATA_DIR.'/.delivery-auto.stamp';$last=is_file($stamp)?(int)@filemtime($stamp):0;
  if($last>0&&time()-$last<45){@flock($lock,LOCK_UN);@fclose($lock);return array('ok'=>true,'skipped'=>'throttled','retryAfter'=>45-(time()-$last),'updated'=>0);}
  @touch($stamp);$result=crm_delivery_sync_batch(60);@flock($lock,LOCK_UN);@fclose($lock);return $result;
}

/* Automatic Confirmé + empty Suivie sender. A shared 7-second throttle and
 * the existing .dl.lock guarantee that several CRM devices cannot duplicate an order. */
function crm_dl_send_guarded() {
  global $DATA_DIR;
  $lock=@fopen($DATA_DIR.'/.dl-send-auto.lock','c');
  if(!$lock||!@flock($lock,LOCK_EX|LOCK_NB)){if($lock)@fclose($lock);return array('ok'=>true,'skipped'=>'busy','sent'=>0);}
  $stamp=$DATA_DIR.'/.dl-send-auto.stamp';$last=is_file($stamp)?(int)@filemtime($stamp):0;
  if($last>0&&time()-$last<7){@flock($lock,LOCK_UN);@fclose($lock);return array('ok'=>true,'skipped'=>'throttled','retryAfter'=>7-(time()-$last),'sent'=>0);}
  @touch($stamp);$result=crm_dl_run(false,0,true,false);@flock($lock,LOCK_UN);@fclose($lock);return $result;
}

/* يشتغل: من cron (GET) أو من admin (dry). forceSentType=0 means Digylog
 * Commandes non envoyées; includeExisting includes every eligible CRM row. */
function crm_dl_run($dry = false,$forceSentType=null,$includeExisting=false,$withStatus=true) {
  global $LOCK_FILE, $DATA_DIR;
  $c = crm_dl_cfg_get();
  if (!$dry && empty($c['enabled'])) return $withStatus?array('ok'=>true,'skipped'=>'sending-disabled','trackingSync'=>crm_tracking_auto_sync(30),'deliveredSync'=>crm_delivery_sync_batch(20)):array('ok'=>true,'skipped'=>'sending-disabled','sent'=>0);
  $since   = isset($c['since']) ? (int)$c['since'] : 0;
  $token   = isset($c['token']) ? (string)$c['token'] : '';
  $network = isset($c['network']) ? (int)$c['network'] : 1;
  $sentTyp = $forceSentType!==null?(int)$forceSentType:(isset($c['sentType'])?(int)$c['sentType']:0);
  $stores  = array();
  foreach (crm_dl_agents() as $ag) $stores[$ag] = isset($c['stores'][$ag]) ? trim((string)$c['stores'][$ag]) : '';
  if (!$dry && $token === '') return array('ok'=>false, 'err'=>'no-token');
  if ($since <= 0 && !$dry && !$includeExisting) return array('ok'=>false, 'err'=>'not-enabled-properly');

  $runLock = @fopen($DATA_DIR . '/.dl.lock', 'c');
  if ($runLock && !$dry && !@flock($runLock, LOCK_EX | LOCK_NB)) return array('ok'=>true, 'skipped'=>'busy');

  /* 1) قراية (لوك قصير) + اختيار الطلبيات */
  $fh = @fopen($LOCK_FILE, 'c'); if ($fh) @flock($fh, LOCK_EX);
  $data = crm_read_raw(true);
  $cur = isset($data['paraveda_orders_v5']['d']) ? crm_unwrap($data['paraveda_orders_v5']['d']) : array();
  if (!is_array($cur)) $cur = array();
  $prevT = isset($data['paraveda_orders_v5']['t']) ? (int)$data['paraveda_orders_v5']['t'] : 0;
  if ($fh) { @flock($fh, LOCK_UN); @fclose($fh); }

  $groups = array(); $skipped = array();
  foreach ($cur as $o) {
    if (!is_array($o) || !empty($o['_del']) || !empty($o['dlSent'])) continue;
    $st = isset($o['statut']) ? (string)$o['statut'] : '';
    if (crm_tracking_norm($st) !== 'confirme') continue;
    if (trim((string)(isset($o['livraison']) ? $o['livraison'] : '')) !== '') continue;   // Suivie فارغ = ما تصيفطاتش بعد
    $stamp = (isset($o['_f']['statut']) && is_numeric($o['_f']['statut'])) ? (float)$o['_f']['statut'] : 0;
    if (!$includeExisting && !($since > 0 ? ($stamp >= $since) : $dry)) continue;
    $tries = isset($o['dlTries']) ? (int)$o['dlTries'] : 0;$nextTry=isset($o['dlNextTry'])?(int)$o['dlNextTry']:0;
    if ($tries >= 20 || (!$dry && $nextTry > (int)(microtime(true)*1000))) continue;
    $id = (string)$o['id'];
    $ag = isset($o['agent']) ? (string)$o['agent'] : '';
    $store = isset($stores[$ag]) ? $stores[$ag] : '';
    if ($store === '') { $skipped[] = array('id'=>$id, 'why'=>'no-store-for-agent', 'agent'=>$ag); continue; }
    $miss = '';
    foreach (array('nom', 'telephone', 'adresse', 'ville', 'produit') as $f) {
      if (!isset($o[$f]) || trim((string)$o[$f]) === '') { $miss = $f; break; }
    }
    if ($miss !== '') { $skipped[] = array('id'=>$id, 'why'=>'missing-' . $miss); continue; }
    $groups[$store][] = array('id'=>$id, 'row'=>crm_dl_order_row($o));
  }

  if ($dry) {
    $sum = array();
    foreach ($groups as $store => $rows) {
      $sum[] = array('store'=>$store, 'count'=>count($rows), 'sample'=>crm_dl_body($store, $network, $sentTyp, array_slice(array_map(function ($r) { return $r['row']; }, $rows), 0, 1)));
    }
    $note = ($since > 0) ? 'هادي هي الطلبيات لي غادي تمشي للمتاجر (بعد التفعيل).' : 'مازال ما تفعلاتش الإرسال. هاد الأرقام معاينة فقط: الطلبيات القديمة ما غاديش تتصيفط. ملي تفعّل، غير الطلبيات Confirmé الجداد غادي يمشيو.';
    /* تشخيص: كل طلبية Confirmé (بلا بيانات حساسة) + علاش ما تصيفطاتش */
    $dbg = array(); $dbgN = 0;
    foreach ($cur as $o) {
      if (!is_array($o) || !empty($o['_del'])) continue;
      $st = isset($o['statut']) ? (string)$o['statut'] : '';
      if (stripos($st, 'confirm') === false) continue;
      $stp = (isset($o['_f']['statut']) && is_numeric($o['_f']['statut'])) ? (float)$o['_f']['statut'] : 0;
      $dbgN++;
      $dbg[] = array(
        'id'      => (string)(isset($o['id']) ? $o['id'] : ''),
        'nom'     => mb_substr((string)(isset($o['nom']) ? $o['nom'] : ''), 0, 20),
        'agent'   => (string)(isset($o['agent']) ? $o['agent'] : ''),
        'liv'     => (string)(isset($o['livraison']) ? $o['livraison'] : ''),
        'stampOk' => ($since > 0 ? ($stp >= $since ? 1 : 0) : -1),
        'dlSent'  => !empty($o['dlSent']) ? 1 : 0,
        'tries'   => isset($o['dlTries']) ? (int)$o['dlTries'] : 0,
        'err'     => mb_substr((string)(isset($o['dlErr']) ? $o['dlErr'] : ''), 0, 160)
      );
    }
    usort($dbg, function ($a, $b) { return ($b['stampOk'] - $a['stampOk']) ?: ($b['dlSent'] - $a['dlSent']); });
    $dbg = array_slice($dbg, 0, 40);
    return array('ok'=>true, 'dry'=>true, 'note'=>$note, 'sentType'=>$sentTyp, 'network'=>$network, 'since'=>$since, 'groups'=>$sum, 'skipped'=>$skipped, 'confirmedTotal'=>$dbgN, 'confirmedDebug'=>$dbg);
  }

  /* 2) إرسال (بلا لوك) */
  $sent = array(); $failed = array(); $sentTracking = array();
  foreach ($groups as $store => $rows) {
    for ($i = 0; $i < count($rows); $i += 50) {
      $chunk = array_slice($rows, $i, 50);
      $body = crm_dl_body($store, $network, $sentTyp, array_map(function ($r) { return $r['row']; }, $chunk));
      list($code, $resp, $err) = crm_dl_http('POST', '/orders/standard', $token, $body);
      $ok = ($code >= 200 && $code < 300);
      $j = json_decode($resp, true);
      if ($ok && is_array($j) && isset($j['success']) && $j['success'] === false) $ok = false;
      foreach ($chunk as $r) {
        if ($ok) {
          $sent[$r['id']] = substr($resp, 0, 200);
          /* Some Digylog responses already contain the generated Tracking.
             Accept it only when the same response record carries this exact CRM id. */
          if (is_array($j)) {
            $generatedTracking = crm_tracking_exact_from_payload($j, $r['id']);
            if ($generatedTracking !== '') $sentTracking[$r['id']] = $generatedTracking;
          }
        } else $failed[$r['id']] = ($err !== '' ? $err : ('http-' . $code . ' ' . substr($resp, 0, 150)));
      }
    }
  }

  /* 3) كتابة النتيجة (لوك) */
  $applied = 0;
  if ($sent || $failed) {
    $fh = @fopen($LOCK_FILE, 'c'); if ($fh) @flock($fh, LOCK_EX);
    $data = crm_read_raw(true);
    $cur = isset($data['paraveda_orders_v5']['d']) ? crm_unwrap($data['paraveda_orders_v5']['d']) : array();
    if (!is_array($cur)) $cur = array();
    $prevT = isset($data['paraveda_orders_v5']['t']) ? (int)$data['paraveda_orders_v5']['t'] : 0;
    $now = (int)(microtime(true) * 1000);
    foreach ($cur as $i => $o) {
      if (!is_array($o) || !isset($o['id'])) continue;
      $id = (string)$o['id'];
      if (!isset($o['_f']) || !is_array($o['_f'])) $o['_f'] = array();
      if (isset($sent[$id])) {
        $o['dlSent'] = 1; $o['dlAt'] = $now; $o['dlRes'] = $sent[$id];$o['dlErr']='';$o['dlNextTry']=0;
        $o['livraison'] = 'Expédier vers'; $o['_f']['livraison'] = $now;   // بعد ما تتسجل فـDigylog: Suivie = Expédier vers
        if (isset($sentTracking[$id]) && trim((string)(isset($o['tracking'])?$o['tracking']:'')) === '') { $o['tracking']=$sentTracking[$id]; $o['_f']['tracking']=$now; }
        $o['_f']['dlSent'] = $now; $o['_u'] = $now; $applied++;
      } elseif (isset($failed[$id])) {
        $o['dlTries'] = (isset($o['dlTries']) ? (int)$o['dlTries'] : 0) + 1;
        $o['dlErr'] = substr((string)$failed[$id], 0, 200);$delay=min(300000,10000*(1<<min(5,max(0,$o['dlTries']-1))));$o['dlNextTry']=$now+$delay;
        $o['_f']['dlTries'] = $now; $o['_f']['dlErr'] = $now;$o['_f']['dlNextTry']=$now; $o['_u'] = $now; $applied++;
      } else continue;
      $cur[$i] = $o;
    }
    if ($applied > 0) {
      crm_backup();
      $t = max($prevT + 1, $now);
      $data['paraveda_orders_v5'] = array('t' => $t, 'd' => array_values($cur));
      $ok = crm_write_all($data);
      if ($ok) crm_journal_append('paraveda_orders_v5', $t, array_values($cur));
    }
    if ($fh) { @flock($fh, LOCK_UN); @fclose($fh); }
  }
  if ($runLock) { @flock($runLock, LOCK_UN); @fclose($runLock); }
  /* Each cron run checks known Trackings exactly and synchronizes only the
     final delivery field: Digylog Livrée -> Livrée, Retournée -> Retour. */
  $trackingSync=$withStatus?crm_tracking_auto_sync(30):array('skipped'=>'fast-send');
  $deliverySync=$withStatus?crm_delivery_sync_batch(20):array('skipped'=>'fast-send');
  crm_audit('digylog-sync | sent=' . count($sent) . ' | failed=' . count($failed) . ' | skipped=' . count($skipped) . ' | applied=' . $applied . ' | sentType='.$sentTyp.' | nonEnvoyees='.($forceSentType===0?1:0).' | trackingLinked=' . (isset($trackingSync['linked'])?(int)$trackingSync['linked']:0) . ' | deliveredUpdated=' . (isset($deliverySync['updated'])?(int)$deliverySync['updated']:0));
  return array('ok'=>true,'sent'=>count($sent),'failed'=>count($failed),'skipped'=>count($skipped),'applied'=>$applied,'sentType'=>$sentTyp,'destination'=>$sentTyp===0?'Commandes non envoyées':'configured','errors'=>$failed,'trackingSync'=>$trackingSync,'deliveredSync'=>$deliverySync);
}

/* Digylog webhook: instant Livrée / Retournée synchronization.
 * Exact Tracking is preferred; exact CRM id (Digylog num) is the fallback.
 * No phone/name matching is allowed and livraison is the only business field written. */
function crm_dl_hook() {
  global $SECRET, $LOCK_FILE;
  $tk=isset($_GET['token'])?(string)$_GET['token']:'';
  if(!hash_equals($SECRET,$tk))crm_out(array('ok'=>false,'err'=>'token'),403);
  $raw=(string)file_get_contents('php://input');$j=json_decode($raw,true);
  if(!is_array($j))crm_out(array('ok'=>false,'err'=>'bad-json'),400);
  if(isset($j['type'])&&$j['type']==='subscribe'&&isset($j['key'])){header('Content-Type: application/json; charset=utf-8');echo json_encode(array('key'=>(string)$j['key']),JSON_UNESCAPED_UNICODE);exit;}
  $ev=isset($j['eventType'])?(string)$j['eventType']:(isset($j['type'])?(string)$j['type']:'');
  if($ev!==''&&$ev!=='order-status-changed')crm_out(array('ok'=>true,'ignored'=>$ev));
  $p=(isset($j['payload'])&&is_array($j['payload'])&&count($j['payload'])>0)?$j['payload']:$j;
  $tracking=strtoupper(trim((string)crm_tracking_deep_pick($p,array('traking','tracking','trackingNumber','tracking_number','barcode'))));
  $num=trim((string)crm_tracking_deep_pick($p,array('num','orderNum','order_num','externalId','external_id')));
  $newLiv=crm_delivery_status($p);if($newLiv==='')$newLiv=crm_delivery_status($j);
  if($newLiv==='')crm_out(array('ok'=>true,'ignored'=>'non-final-status'));
  if($tracking===''&&$num==='')crm_out(array('ok'=>true,'ignored'=>'no-exact-key'));

  $fh=@fopen($LOCK_FILE,'c');if($fh)@flock($fh,LOCK_EX);
  $data=crm_read_raw(true);$cur=isset($data['paraveda_orders_v5']['d'])?crm_unwrap($data['paraveda_orders_v5']['d']):array();if(!is_array($cur))$cur=array();
  $hits=array();
  foreach($cur as $i=>$o){
    if(!is_array($o)||!empty($o['_del']))continue;
    $rowTracking=strtoupper(trim((string)(isset($o['tracking'])?$o['tracking']:'')));
    if($tracking!==''&&$rowTracking===$tracking)$hits[]=$i;
  }
  if($tracking===''||count($hits)===0){
    $hits=array();foreach($cur as $i=>$o)if(is_array($o)&&empty($o['_del'])&&isset($o['id'])&&$num!==''&&(string)$o['id']===$num)$hits[]=$i;
  }
  if(count($hits)!==1){if($fh){@flock($fh,LOCK_UN);@fclose($fh);}crm_audit('digylog-hook | tracking='.$tracking.' | num='.$num.' | ignored='.(count($hits)>1?'ambiguous':'not-found'));crm_out(array('ok'=>true,'found'=>false,'ambiguous'=>count($hits)>1));}
  $hit=$hits[0];$o=$cur[$hit];$liv=trim((string)(isset($o['livraison'])?$o['livraison']:''));
  if($liv===$newLiv||($liv==='Retour'&&$newLiv==='Livrée')){if($fh){@flock($fh,LOCK_UN);@fclose($fh);}crm_out(array('ok'=>true,'found'=>true,'changed'=>false,'livraison'=>$liv));}
  $now=(int)(microtime(true)*1000);if(!isset($o['_f'])||!is_array($o['_f']))$o['_f']=array();
  /* The webhook's only business-field write. */
  $o['livraison']=$newLiv;$o['_f']['livraison']=$now;$o['_u']=$now;$cur[$hit]=$o;
  $prevT=isset($data['paraveda_orders_v5']['t'])?(int)$data['paraveda_orders_v5']['t']:0;crm_backup();$t=max($prevT+1,$now);$data['paraveda_orders_v5']=array('t'=>$t,'d'=>array_values($cur));$ok=crm_write_all($data);if($ok)crm_journal_append('paraveda_orders_v5',$t,array_values($cur));
  if($fh){@flock($fh,LOCK_UN);@fclose($fh);}crm_audit('digylog-hook | tracking='.$tracking.' | num='.$num.' | livraison='.$newLiv.' | changed='.($ok?1:0));
  crm_out(array('ok'=>(bool)$ok,'found'=>true,'changed'=>(bool)$ok,'livraison'=>$newLiv));
}
if(isset($_GET['action'])&&$_GET['action']==='digylog_hook')crm_dl_hook();


/* ================================================================
 * Suivi des Retours — linked to paraveda_orders_v5 by order_id.
 * Stores warehouse reception facts only; livraison remains independent.
 * ================================================================ */
function crm_returns_norm($v) {
  $v=trim((string)$v);$v=function_exists('mb_strtolower')?mb_strtolower($v,'UTF-8'):strtolower($v);
  $v=str_replace(array('é','è','ê','ë','à','â','ä','î','ï','ô','ö','ù','û','ü','ç'),array('e','e','e','e','a','a','a','i','i','o','o','u','u','u','c'),$v);
  return preg_replace('/[^a-z0-9]+/u','',$v);
}
function crm_returns_is_return($o) {
  $s=crm_returns_norm(isset($o['livraison'])?$o['livraison']:'');
  return strpos($s,'retour')!==false||$s==='rembourse';
}
function crm_returns_tracking($o) {
  foreach(array('Tracking','tracking','dlTracking','digylogTracking','trackingAlt') as $k){$v=strtoupper(trim((string)(isset($o[$k])?$o[$k]:'')));if($v!=='')return $v;}
  return '';
}
function crm_returns_iso($ms=null) {
  try{$tz=new DateTimeZone('Africa/Casablanca');$d=new DateTime('now',$tz);if($ms!==null&&is_numeric($ms))$d->setTimestamp((int)floor((float)$ms/1000));return $d->format(DateTime::ATOM);}catch(Exception $e){return date('c');}
}
function crm_returns_actor($b,$data,$need='view') {
  $id=isset($b['actorId'])?(string)$b['actorId']:'';$users=isset($data['paraveda_users_v1']['d'])?crm_unwrap($data['paraveda_users_v1']['d']):array();if(!is_array($users))$users=array();$u=null;
  foreach($users as $x)if(is_array($x)&&empty($x['_del'])&&isset($x['id'])&&(string)$x['id']===$id){$u=$x;break;}
  if(!$u)return array('ok'=>false,'err'=>'user-not-found');$base=isset($u['role'])?(string)$u['role']:'user';$rr=isset($u['returnRole'])?(string)$u['returnRole']:'';
  $role=$base==='admin'?'admin':($rr==='supervisor'?'supervisor':'agent_retour');
  $allowed=$need==='view'||$need==='scan'||(($need==='override'||$need==='restock'||$need==='correct')&&($role==='admin'||$role==='supervisor'));
  return array('ok'=>$allowed,'err'=>$allowed?'':'forbidden','id'=>$id,'name'=>(string)(isset($u['username'])?$u['username']:(isset($u['agent'])?$u['agent']:'Utilisateur')),'role'=>$role);
}
function crm_returns_map($data) {
  $rows=isset($data['paraveda_returns_v1']['d'])?crm_unwrap($data['paraveda_returns_v1']['d']):array();if(!is_array($rows))$rows=array();$m=array();foreach($rows as $r)if(is_array($r)&&isset($r['order_id']))$m[(string)$r['order_id']]=$r;return array($rows,$m);
}
function crm_returns_audit(&$data,$event,$orderId,$tracking,$actor,$details=array()) {
  global $DATA_DIR;$now=crm_returns_iso();$a=array('id'=>(string)(microtime(true)*1000000),'event'=>$event,'order_id'=>(string)$orderId,'tracking'=>(string)$tracking,'at'=>$now,'actor_id'=>(string)$actor['id'],'actor'=>(string)$actor['name'],'role'=>(string)$actor['role'],'details'=>$details);
  $list=isset($data['paraveda_return_audit_v1']['d'])?crm_unwrap($data['paraveda_return_audit_v1']['d']):array();if(!is_array($list))$list=array();array_unshift($list,$a);if(count($list)>5000)$list=array_slice($list,0,5000);$t=(int)(microtime(true)*1000);$data['paraveda_return_audit_v1']=array('t'=>$t,'d'=>$list);
  @file_put_contents($DATA_DIR.'/returns_audit.log',json_encode($a,JSON_UNESCAPED_UNICODE)."\n",FILE_APPEND|LOCK_EX);return $a;
}
function crm_returns_item($o,$r,$audit=array()) {
  $id=(string)(isset($o['id'])?$o['id']:'');$tr=crm_returns_tracking($o);$declMs=isset($o['_f']['livraison'])?$o['_f']['livraison']:null;
  return array('order_id'=>$id,'commande'=>trim((string)(isset($o['idCmd'])?$o['idCmd']:''))!==''?(string)$o['idCmd']:'ORD-'.$id,'tracking'=>$tr,'client'=>(string)(isset($o['nom'])?$o['nom']:''),'phone'=>(string)(isset($o['telephone'])?$o['telephone']:''),'ville'=>(string)(isset($o['ville'])?$o['ville']:''),'adresse'=>(string)(isset($o['adresse'])?$o['adresse']:''),'produit'=>(string)(isset($o['produit'])?$o['produit']:''),'qte'=>max(1,(int)(isset($o['qte'])?$o['qte']:1)),'prix'=>(float)(isset($o['prix'])?$o['prix']:0),'transporteur'=>(string)(isset($o['livreur'])&&trim((string)$o['livreur'])!==''?$o['livreur']:'Digylog'),'return_reason'=>(string)(isset($o['motif'])&&trim((string)$o['motif'])!==''?$o['motif']:'Non renseigné'),'created_at'=>(string)(isset($o['dateCreation'])?$o['dateCreation']:''),'confirmed_at'=>(string)(isset($o['dateConfirmation'])?$o['dateConfirmation']:''),'shipped_at'=>(string)(isset($o['dateExp'])?$o['dateExp']:''),'returned_at'=>isset($r['returned_at'])?$r['returned_at']:($declMs?crm_returns_iso($declMs):''),'delivery_status'=>(string)(isset($o['livraison'])?$o['livraison']:''),'warehouse_status'=>isset($r['warehouse_status'])?$r['warehouse_status']:'En attente','scanned_at'=>isset($r['scanned_at'])?$r['scanned_at']:'','scanned_by'=>isset($r['scanned_by'])?$r['scanned_by']:'','product_condition'=>isset($r['product_condition'])?$r['product_condition']:'','notes'=>isset($r['notes'])?$r['notes']:'','stock_reintegrated_at'=>isset($r['stock_reintegrated_at'])?$r['stock_reintegrated_at']:'','audit'=>$audit);
}
function crm_returns_list($b) {
  $data=crm_read_raw(true);$actor=crm_returns_actor($b,$data,'view');if(empty($actor['ok']))crm_out(array('ok'=>false,'err'=>$actor['err']),403);list($records,$rm)=crm_returns_map($data);$orders=isset($data['paraveda_orders_v5']['d'])?crm_unwrap($data['paraveda_orders_v5']['d']):array();if(!is_array($orders))$orders=array();$aud=isset($data['paraveda_return_audit_v1']['d'])?crm_unwrap($data['paraveda_return_audit_v1']['d']):array();if(!is_array($aud))$aud=array();$byOrder=array();foreach($aud as $a)if(is_array($a)&&isset($a['order_id'])){$oid=(string)$a['order_id'];if(!isset($byOrder[$oid]))$byOrder[$oid]=array();if(count($byOrder[$oid])<50)$byOrder[$oid][]=$a;}
  $items=array();foreach($orders as $o){if(!is_array($o)||!empty($o['_del']))continue;$id=(string)$o['id'];if(!crm_returns_is_return($o)&&!isset($rm[$id]))continue;$items[]=crm_returns_item($o,isset($rm[$id])?$rm[$id]:array(),isset($byOrder[$id])?$byOrder[$id]:array());}
  usort($items,function($a,$b){return strcmp((string)($b['scanned_at']?:$b['returned_at']),(string)($a['scanned_at']?:$a['returned_at']));});$today=(new DateTime('now',new DateTimeZone('Africa/Casablanca')))->format('Y-m-d');$received=0;$todayN=0;foreach($items as $x){if($x['warehouse_status']==='Reçu au dépôt')$received++;if(substr((string)$x['scanned_at'],0,10)===$today)$todayN++;}
  crm_out(array('ok'=>true,'actor'=>array('name'=>$actor['name'],'role'=>$actor['role']),'items'=>$items,'kpis'=>array('total'=>count($items),'pending'=>count($items)-$received,'received'=>$received,'today'=>$todayN),'serverTime'=>crm_returns_iso()));
}
function crm_returns_collect_known_tracking($v,$known,&$hits,$depth=0) {
  if($depth>10)return;
  if(is_array($v)){foreach($v as $x)crm_returns_collect_known_tracking($x,$known,$hits,$depth+1);return;}
  if(is_object($v)){crm_returns_collect_known_tracking((array)$v,$known,$hits,$depth+1);return;}
  $n=strtoupper(trim(preg_replace('/\s+/','',(string)$v)));if($n!==''&&isset($known[$n]))$hits[$known[$n]]=true;
}
function crm_returns_has_exact_value($v,$needle,$depth=0) {
  if($depth>10)return false;if(is_array($v)){foreach($v as $x)if(crm_returns_has_exact_value($x,$needle,$depth+1))return true;return false;}if(is_object($v))return crm_returns_has_exact_value((array)$v,$needle,$depth+1);return strcasecmp(trim((string)$v),trim((string)$needle))===0;
}
function crm_returns_digylog_get_url($url,$token) {
  if(!function_exists('curl_init'))return array(0,'','no-curl');$ch=curl_init($url);curl_setopt_array($ch,array(CURLOPT_HTTPHEADER=>array('Accept: application/json, text/plain, */*','Referer: https://seller.digylog.com/','Origin: https://seller.digylog.com','Authorization: Bearer '.$token),CURLOPT_RETURNTRANSFER=>true,CURLOPT_CONNECTTIMEOUT=>8,CURLOPT_TIMEOUT=>20));$body=curl_exec($ch);$err=(string)curl_error($ch);$code=(int)curl_getinfo($ch,CURLINFO_HTTP_CODE);curl_close($ch);return array($code,$body===false?'':(string)$body,$err);
}
function crm_returns_resolve_qr_tracking($qr,$orders) {
  $qr=trim((string)$qr);if(!preg_match('/^tk[a-z0-9]{12,80}$/i',$qr))return array('tracking'=>'','reason'=>'not-digylog-qr');
  $known=array();foreach($orders as $o){if(!is_array($o)||!empty($o['_del']))continue;$tr=crm_returns_tracking($o);$n=strtoupper(trim(preg_replace('/\s+/','',$tr)));if($n!=='')$known[$n]=$tr;}
  if(!$known)return array('tracking'=>'','reason'=>'no-crm-trackings');
  $cfg=crm_dl_cfg_get();$token=isset($cfg['token'])?trim((string)$cfg['token']):'';if($token==='')return array('tracking'=>'','reason'=>'no-digylog-token');
  $hits=array();$codes=array();foreach(array('/order/'.rawurlencode($qr).'/infos','/order/'.rawurlencode($qr).'/refs') as $path){list($code,$body,$err)=crm_dl_http('GET',$path,$token);$codes[]=$code;if($code<200||$code>=300)continue;$j=json_decode($body,true);if(is_array($j))crm_returns_collect_known_tracking($j,$known,$hits);}
  $keys=array_keys($hits);if(count($keys)===1)return array('tracking'=>$keys[0],'reason'=>'digylog-exact','codes'=>$codes);
  /* Some Digylog labels expose an opaque tk... token rather than the visible
     Tracking. Ask the seller-history search using that exact token and accept
     only a single Tracking which already exists in CRM. */
  $base='https://api.digylog.com/api/seller/v48/historic/orders';$qs=array('tracking','search','barcode','q');
  foreach($qs as $param){$url=$base.'?'.rawurlencode($param).'='.rawurlencode($qr).'&datatype=1&countPerPage=10&currentPage=1&sort=0';list($code,$body,$err)=crm_returns_digylog_get_url($url,$token);$codes[]=$code;if($code<200||$code>=300)continue;$j=json_decode($body,true);$one=array();if(is_array($j)&&crm_returns_has_exact_value($j,$qr))crm_returns_collect_known_tracking($j,$known,$one);$found=array_keys($one);if(count($found)===1)return array('tracking'=>$found[0],'reason'=>'digylog-qr-search-exact','codes'=>$codes);}
  return array('tracking'=>'','reason'=>count($keys)>1?'ambiguous-digylog-response':'digylog-qr-unresolved','codes'=>$codes);
}
function crm_returns_find_order(&$orders,$query,&$matches) {
  $q=strtoupper(trim(preg_replace('/\s+/','',(string)$query)));$hit=-1;$matches=0;foreach($orders as $i=>$o){if(!is_array($o)||!empty($o['_del']))continue;$tr=strtoupper(trim(preg_replace('/\s+/','',crm_returns_tracking($o))));$id=strtoupper(trim((string)(isset($o['id'])?$o['id']:'')));$cmd=strtoupper(trim((string)(isset($o['idCmd'])?$o['idCmd']:'')));if($q!==''&&($tr===$q||$id===$q||$cmd===$q||('ORD-'.$id)===$q)){$hit=$i;$matches++;}}return $hit;
}
function crm_returns_scan($b) {
  global $LOCK_FILE;
  $query=isset($b['tracking'])?trim((string)$b['tracking']):'';if($query==='')crm_out(array('ok'=>false,'err'=>'empty-tracking'),400);
  /* Resolve Digylog's printed QR token before taking the write lock. The
     resolver accepts only a Tracking value that already exists exactly in CRM. */
  $pre=crm_read_raw(true);$preActor=crm_returns_actor($b,$pre,'scan');if(empty($preActor['ok']))crm_out(array('ok'=>false,'err'=>$preActor['err']),403);
  $preOrders=isset($pre['paraveda_orders_v5']['d'])?crm_unwrap($pre['paraveda_orders_v5']['d']):array();if(!is_array($preOrders))$preOrders=array();$preMatches=0;$resolved=$query;$preIdx=crm_returns_find_order($preOrders,$resolved,$preMatches);$qrMeta=array('tracking'=>'','reason'=>'direct');
  if($preMatches===0&&preg_match('/^tk[a-z0-9]{12,80}$/i',$query)){$qrMeta=crm_returns_resolve_qr_tracking($query,$preOrders);if(!empty($qrMeta['tracking']))$resolved=(string)$qrMeta['tracking'];elseif(!empty($b['visibleTracking'])){$manualMatches=0;$manualIdx=crm_returns_find_order($preOrders,(string)$b['visibleTracking'],$manualMatches);if($manualMatches===1){$resolved=crm_returns_tracking($preOrders[$manualIdx]);$qrMeta=array('tracking'=>$resolved,'reason'=>'operator-visible-exact');}else crm_out(array('ok'=>false,'err'=>$manualMatches>1?'tracking-ambiguous':'tracking-not-found'),$manualMatches>1?409:404);}else crm_out(array('ok'=>false,'err'=>'qr-tracking-unresolved','qr'=>$query,'reason'=>$qrMeta['reason'],'canPairVisibleTracking'=>true),404);}
  elseif($preMatches>1)crm_out(array('ok'=>false,'err'=>'tracking-ambiguous'),409);

  $fh=@fopen($LOCK_FILE,'c');if($fh)@flock($fh,LOCK_EX);
  $data=crm_read_raw(true);$actor=crm_returns_actor($b,$data,'scan');
  if(empty($actor['ok'])){if($fh){@flock($fh,LOCK_UN);@fclose($fh);}crm_out(array('ok'=>false,'err'=>$actor['err']),403);}
  $orders=isset($data['paraveda_orders_v5']['d'])?crm_unwrap($data['paraveda_orders_v5']['d']):array();if(!is_array($orders))$orders=array();$matches=0;$idx=crm_returns_find_order($orders,$resolved,$matches);
  if($matches!==1){if($fh){@flock($fh,LOCK_UN);@fclose($fh);}crm_out(array('ok'=>false,'err'=>$matches>1?'tracking-ambiguous':'tracking-not-found','qr'=>$query,'resolvedTracking'=>$resolved),$matches>1?409:404);}
  $o=$orders[$idx];$override=!empty($b['override']);$reason=trim((string)(isset($b['overrideReason'])?$b['overrideReason']:''));
  if(!crm_returns_is_return($o)){
    if(!$override){if($fh){@flock($fh,LOCK_UN);@fclose($fh);}crm_out(array('ok'=>false,'err'=>'not-declared-return','canOverride'=>$actor['role']==='admin'||$actor['role']==='supervisor','resolvedTracking'=>$resolved),409);}
    $oa=crm_returns_actor($b,$data,'override');if(empty($oa['ok'])||$reason===''){if($fh){@flock($fh,LOCK_UN);@fclose($fh);}crm_out(array('ok'=>false,'err'=>'override-forbidden-or-reason-required'),403);}
  }
  list($records,$rm)=crm_returns_map($data);$id=(string)$o['id'];$tr=crm_returns_tracking($o);
  $r=isset($rm[$id])?$rm[$id]:array('id'=>(string)(microtime(true)*1000000),'order_id'=>$id,'tracking_number'=>$tr,'returned_at'=>crm_returns_iso(isset($o['_f']['livraison'])?$o['_f']['livraison']:null),'warehouse_status'=>'En attente','created_at'=>crm_returns_iso());
  if(isset($r['scanned_at'])&&$r['scanned_at']!==''){if($fh){@flock($fh,LOCK_UN);@fclose($fh);}crm_out(array('ok'=>false,'err'=>'already-received','existing'=>crm_returns_item($o,$r),'resolvedTracking'=>$tr),409);}
  $now=crm_returns_iso();$r['tracking_number']=$tr;if(strcasecmp($query,$tr)!==0)$r['qr_code']=$query;$r['warehouse_status']=$override?'À vérifier':'Reçu au dépôt';$r['scanned_at']=$now;$r['scanned_by']=$actor['name'];$r['scanned_by_id']=$actor['id'];$r['updated_at']=$now;if($override){$r['override_reason']=$reason;$r['override_by']=$actor['name'];}
  $found=false;foreach($records as $i=>$x)if(is_array($x)&&isset($x['order_id'])&&(string)$x['order_id']===$id){$records[$i]=$r;$found=true;break;}if(!$found)$records[]=$r;
  $ms=(int)(microtime(true)*1000);$data['paraveda_returns_v1']=array('t'=>$ms,'d'=>array_values($records));if(!isset($o['_f'])||!is_array($o['_f']))$o['_f']=array();$o['warehouseReturnStatus']=$r['warehouse_status'];$o['returnScannedAt']=$now;$o['returnScannedBy']=$actor['name'];$o['_f']['warehouseReturnStatus']=$ms;$o['_f']['returnScannedAt']=$ms;$o['_f']['returnScannedBy']=$ms;$o['_u']=$ms;$orders[$idx]=$o;$ot=isset($data['paraveda_orders_v5']['t'])?(int)$data['paraveda_orders_v5']['t']:0;$data['paraveda_orders_v5']=array('t'=>max($ot+1,$ms),'d'=>array_values($orders));
  $auditDetails=$override?array('reason'=>$reason):array();if(strcasecmp($query,$tr)!==0){$auditDetails['qr_code']=$query;$auditDetails['resolved_tracking']=$tr;}$audit=crm_returns_audit($data,$override?'return_received_override':'return_received',$id,$tr,$actor,$auditDetails);
  crm_backup();$ok=crm_write_all($data);if($ok){crm_journal_append('paraveda_returns_v1',$ms,array_values($records));crm_journal_append('paraveda_orders_v5',$data['paraveda_orders_v5']['t'],array_values($orders));crm_journal_append('paraveda_return_audit_v1',$data['paraveda_return_audit_v1']['t'],$data['paraveda_return_audit_v1']['d']);}
  if($fh){@flock($fh,LOCK_UN);@fclose($fh);}if(!$ok)crm_out(array('ok'=>false,'err'=>'save-failed'),500);crm_out(array('ok'=>true,'message'=>'Retour reçu avec succès','resolvedTracking'=>$tr,'item'=>crm_returns_item($o,$r)));
}
function crm_returns_control($b) {
  global $LOCK_FILE;
  $id=(string)(isset($b['orderId'])?$b['orderId']:'');
  $cond=(string)(isset($b['productCondition'])?$b['productCondition']:'');
  $allowed=array('Produit intact','Emballage endommagé','Produit endommagé','Produit manquant','Colis vide','À vérifier');
  if(!in_array($cond,$allowed,true))crm_out(array('ok'=>false,'err'=>'bad-condition'),400);
  $fh=@fopen($LOCK_FILE,'c');if($fh)@flock($fh,LOCK_EX);
  $data=crm_read_raw(true);$actor=crm_returns_actor($b,$data,'scan');
  if(empty($actor['ok'])){if($fh){@flock($fh,LOCK_UN);@fclose($fh);}crm_out(array('ok'=>false,'err'=>$actor['err']),403);}
  list($records,$rm)=crm_returns_map($data);$hit=-1;
  foreach($records as $i=>$r)if(is_array($r)&&isset($r['order_id'])&&(string)$r['order_id']===$id){$hit=$i;break;}
  if($hit<0||empty($records[$hit]['scanned_at'])){if($fh){@flock($fh,LOCK_UN);@fclose($fh);}crm_out(array('ok'=>false,'err'=>'return-not-received'),409);}
  $warehouse=$cond==='À vérifier'?'À vérifier':(in_array($cond,array('Produit endommagé','Produit manquant','Colis vide'),true)?'Anomalie':'Reçu au dépôt');
  $notes=trim((string)(isset($b['notes'])?$b['notes']:''));$now=crm_returns_iso();$ms=(int)(microtime(true)*1000);
  $records[$hit]['product_condition']=$cond;$records[$hit]['notes']=$notes;$records[$hit]['warehouse_status']=$warehouse;$records[$hit]['updated_at']=$now;
  $data['paraveda_returns_v1']=array('t'=>$ms,'d'=>$records);
  $orders=isset($data['paraveda_orders_v5']['d'])?crm_unwrap($data['paraveda_orders_v5']['d']):array();if(!is_array($orders))$orders=array();
  foreach($orders as $i=>$o){if(!is_array($o)||!isset($o['id'])||(string)$o['id']!==$id)continue;if(!isset($o['_f'])||!is_array($o['_f']))$o['_f']=array();$o['warehouseReturnStatus']=$warehouse;$o['returnProductCondition']=$cond;$o['returnNotes']=$notes;foreach(array('warehouseReturnStatus','returnProductCondition','returnNotes')as$f)$o['_f'][$f]=$ms;$o['_u']=$ms;$orders[$i]=$o;break;}
  $ot=isset($data['paraveda_orders_v5']['t'])?(int)$data['paraveda_orders_v5']['t']:0;$data['paraveda_orders_v5']=array('t'=>max($ot+1,$ms),'d'=>array_values($orders));
  crm_returns_audit($data,'return_controlled',$id,(string)$records[$hit]['tracking_number'],$actor,array('condition'=>$cond,'warehouse_status'=>$warehouse));
  crm_backup();$ok=crm_write_all($data);if($ok){crm_journal_append('paraveda_returns_v1',$ms,$records);crm_journal_append('paraveda_orders_v5',$data['paraveda_orders_v5']['t'],array_values($orders));crm_journal_append('paraveda_return_audit_v1',$data['paraveda_return_audit_v1']['t'],$data['paraveda_return_audit_v1']['d']);}
  if($fh){@flock($fh,LOCK_UN);@fclose($fh);}crm_out(array('ok'=>(bool)$ok,'warehouse_status'=>$warehouse));
}
function crm_returns_restock($b) {
  global $LOCK_FILE;
  $id=(string)(isset($b['orderId'])?$b['orderId']:'');
  $fh=@fopen($LOCK_FILE,'c');if($fh)@flock($fh,LOCK_EX);
  $data=crm_read_raw(true);$actor=crm_returns_actor($b,$data,'restock');
  if(empty($actor['ok'])){if($fh){@flock($fh,LOCK_UN);@fclose($fh);}crm_out(array('ok'=>false,'err'=>$actor['err']),403);}
  list($records,$rm)=crm_returns_map($data);$ri=-1;
  foreach($records as $i=>$r){if(is_array($r)&&isset($r['order_id'])&&(string)$r['order_id']===$id){$ri=$i;break;}}
  if($ri<0||empty($records[$ri]['scanned_at'])||(isset($records[$ri]['product_condition'])?$records[$ri]['product_condition']:'')!=='Produit intact'){if($fh){@flock($fh,LOCK_UN);@fclose($fh);}crm_out(array('ok'=>false,'err'=>'intact-control-required'),409);}
  if(!empty($records[$ri]['stock_reintegrated_at'])){if($fh){@flock($fh,LOCK_UN);@fclose($fh);}crm_out(array('ok'=>false,'err'=>'already-restocked'),409);}
  $orders=isset($data['paraveda_orders_v5']['d'])?crm_unwrap($data['paraveda_orders_v5']['d']):array();$order=null;
  if(is_array($orders))foreach($orders as $o){if(is_array($o)&&isset($o['id'])&&(string)$o['id']===$id){$order=$o;break;}}
  if(!$order){if($fh){@flock($fh,LOCK_UN);@fclose($fh);}crm_out(array('ok'=>false,'err'=>'order-not-found'),404);}
  $cat=isset($data['paraveda_catalog_v1']['d'])?crm_unwrap($data['paraveda_catalog_v1']['d']):array();if(!is_array($cat))$cat=array();$pi=-1;
  foreach($cat as $i=>$p){if(is_array($p)&&crm_returns_norm(isset($p['nom'])?$p['nom']:'')===crm_returns_norm(isset($order['produit'])?$order['produit']:'')){$pi=$i;break;}}
  if($pi<0){if($fh){@flock($fh,LOCK_UN);@fclose($fh);}crm_out(array('ok'=>false,'err'=>'product-not-found-in-catalog'),404);}
  $q=max(1,(int)(isset($order['qte'])?$order['qte']:1));$oldStock=(int)(isset($cat[$pi]['stock'])?$cat[$pi]['stock']:0);$cat[$pi]['stock']=(string)($oldStock+$q);$now=crm_returns_iso();
  $records[$ri]['stock_reintegrated_at']=$now;$records[$ri]['stock_reintegrated_by']=$actor['name'];$records[$ri]['updated_at']=$now;
  $moves=isset($data['paraveda_stock_movements_v1']['d'])?crm_unwrap($data['paraveda_stock_movements_v1']['d']):array();if(!is_array($moves))$moves=array();
  array_unshift($moves,array('id'=>(string)(microtime(true)*1000000),'type'=>'RETURN_IN','order_id'=>$id,'tracking'=>$records[$ri]['tracking_number'],'product'=>$order['produit'],'quantity'=>$q,'at'=>$now,'by'=>$actor['name']));
  $ms=(int)(microtime(true)*1000);$data['paraveda_catalog_v1']=array('t'=>$ms,'d'=>$cat);$data['paraveda_returns_v1']=array('t'=>$ms,'d'=>$records);$data['paraveda_stock_movements_v1']=array('t'=>$ms,'d'=>$moves);
  crm_returns_audit($data,'return_restocked',$id,$records[$ri]['tracking_number'],$actor,array('product'=>$order['produit'],'quantity'=>$q));crm_backup();$ok=crm_write_all($data);
  if($ok){crm_journal_append('paraveda_catalog_v1',$ms,$cat);crm_journal_append('paraveda_returns_v1',$ms,$records);crm_journal_append('paraveda_stock_movements_v1',$ms,$moves);crm_journal_append('paraveda_return_audit_v1',$data['paraveda_return_audit_v1']['t'],$data['paraveda_return_audit_v1']['d']);}
  if($fh){@flock($fh,LOCK_UN);@fclose($fh);}crm_out(array('ok'=>(bool)$ok,'quantity'=>$q,'newStock'=>(int)$cat[$pi]['stock']));
}

/* One-time 2026-10 city delivery-price adjustment requested by admin.
 * Exact mapping from the pre-change value: 40->35, 45->40, 50->45.
 * The marker prevents a transformed 45->40 price from being discounted twice. */
function crm_city_delivery_price_cut_once() {
  global $LOCK_FILE,$DATA_DIR;
  $marker='paraveda_city_price_cut_20261028_v1';$stamp=rtrim((string)$DATA_DIR,'/').'/.city-price-cut-20261028.done';
  if(is_file($stamp))return;
  $fh=@fopen($LOCK_FILE,'c');if($fh)@flock($fh,LOCK_EX);
  $data=crm_read_raw(true);
  if(isset($data[$marker]['d']['done'])&&!empty($data[$marker]['d']['done'])){@touch($stamp);if($fh){@flock($fh,LOCK_UN);@fclose($fh);}return;}
  $rows=isset($data['paraveda_villes_v2']['d'])?crm_unwrap($data['paraveda_villes_v2']['d']):array();
  if(!is_array($rows)||count($rows)===0){if($fh){@flock($fh,LOCK_UN);@fclose($fh);}return;}
  $map=array('40'=>35,'45'=>40,'50'=>45);$counts=array('40_to_35'=>0,'45_to_40'=>0,'50_to_45'=>0);$changed=0;
  foreach($rows as $i=>$row){
    if(!is_array($row)||!isset($row['prix'])||!is_numeric($row['prix']))continue;$old=(float)$row['prix'];$key=(string)(int)$old;
    if($old!=(float)(int)$old||!isset($map[$key]))continue;$rows[$i]['prix']=$map[$key];$counts[$key.'_to_'.$map[$key]]++;$changed++;
  }
  $now=(int)(microtime(true)*1000);$prevT=isset($data['paraveda_villes_v2']['t'])?(int)$data['paraveda_villes_v2']['t']:0;
  $data['paraveda_villes_v2']=array('t'=>max($prevT+1,$now),'d'=>array_values($rows));
  $data[$marker]=array('t'=>$now,'d'=>array('done'=>1,'at'=>$now,'changed'=>$changed,'counts'=>$counts));
  crm_backup();$ok=crm_write_all($data);if($ok){crm_journal_append('paraveda_villes_v2',$data['paraveda_villes_v2']['t'],array_values($rows));@touch($stamp);}
  if($fh){@flock($fh,LOCK_UN);@fclose($fh);}crm_audit('city-price-cut | changed='.$changed.' | 40to35='.$counts['40_to_35'].' | 45to40='.$counts['45_to_40'].' | 50to45='.$counts['50_to_45'].' | ok='.($ok?1:0));
}
crm_city_delivery_price_cut_once();

/* One-time matching reduction for the existing CRM commission column.
 * Exact original values only: 40->35, 45->40, 50->45. */
function crm_order_commission_cut_once() {
  global $LOCK_FILE,$DATA_DIR;
  $marker='paraveda_commission_cut_20261028_v1';$stamp=rtrim((string)$DATA_DIR,'/').'/.commission-cut-20261028.done';
  if(is_file($stamp))return;
  $fh=@fopen($LOCK_FILE,'c');if($fh)@flock($fh,LOCK_EX);$data=crm_read_raw(true);
  if(isset($data[$marker]['d']['done'])&&!empty($data[$marker]['d']['done'])){@touch($stamp);if($fh){@flock($fh,LOCK_UN);@fclose($fh);}return;}
  $rows=isset($data['paraveda_orders_v5']['d'])?crm_unwrap($data['paraveda_orders_v5']['d']):array();
  if(!is_array($rows)||count($rows)===0){if($fh){@flock($fh,LOCK_UN);@fclose($fh);}return;}
  $map=array('40'=>35,'45'=>40,'50'=>45);$counts=array('40_to_35'=>0,'45_to_40'=>0,'50_to_45'=>0);$changed=0;$now=(int)(microtime(true)*1000);
  foreach($rows as $i=>$row){
    if(!is_array($row)||!empty($row['_del'])||!isset($row['commission'])||!is_numeric($row['commission']))continue;$old=(float)$row['commission'];$key=(string)(int)$old;
    if($old!=(float)(int)$old||!isset($map[$key]))continue;
    $row['commission']=$map[$key];if(!isset($row['_f'])||!is_array($row['_f']))$row['_f']=array();$row['_f']['commission']=$now;$row['_u']=$now;$rows[$i]=$row;$counts[$key.'_to_'.$map[$key]]++;$changed++;
  }
  $prevT=isset($data['paraveda_orders_v5']['t'])?(int)$data['paraveda_orders_v5']['t']:0;$data['paraveda_orders_v5']=array('t'=>max($prevT+1,$now),'d'=>array_values($rows));
  $data[$marker]=array('t'=>$now,'d'=>array('done'=>1,'at'=>$now,'changed'=>$changed,'counts'=>$counts));
  crm_backup();$ok=crm_write_all($data);if($ok){crm_journal_append('paraveda_orders_v5',$data['paraveda_orders_v5']['t'],array_values($rows));@touch($stamp);}
  if($fh){@flock($fh,LOCK_UN);@fclose($fh);}crm_audit('commission-cut | changed='.$changed.' | 40to35='.$counts['40_to_35'].' | 45to40='.$counts['45_to_40'].' | 50to45='.$counts['50_to_45'].' | ok='.($ok?1:0));
}
crm_order_commission_cut_once();

$m = $_SERVER['REQUEST_METHOD'] ?? 'GET';

/* ---------- GET: full snapshot ---------- */
if ($m === 'GET') {
  // v3.101: cron ديال Digylog: api.php?action=digylog_sync&token=...
  if (isset($_GET['action']) && $_GET['action'] === 'digylog_sync') {
    if (!hash_equals($SECRET, crm_token())) crm_out(array('ok'=>false, 'err'=>'token'), 403);
    crm_out(crm_dl_run(false));
  }
  // v3.41: la lecture exige aussi le token (avant: n'importe qui avec l'URL téléchargeait tous les clients)
  if (!hash_equals($SECRET, crm_token())) crm_out(array('ok'=>false, 'err'=>'token'), 403);

  /* Guaranteed automatic fallback: every CRM snapshot can start one throttled
     status batch, even when an old cached index lacks the heartbeat script. */
  if (!isset($_GET['export']) && !isset($_GET['pushkey'])) { crm_dl_send_guarded(); crm_delivery_auto_guarded(); }

  /* PERF v3.90 — أهم إصلاح فالسيرفر.
   * قبل: كل جهاز كيدير GET كل 5 ثواني وكيحمّل 1.1MB حتى إلا ما تبدل والو.
   *      = 720 طلب/ساعة × 1.1MB = ~800MB فالساعة لكل مستخدم.
   * دابا: بصمة رخيصة (stat) → إلا ما تبدل والو كنرجعو 304 بلا ما نقراو حتى ملف
   *      وبلا ما نصيفطو حتى بايت. المتصفح ما كيديرش parse ولا localStorage ولا
   *      إعادة رسم — وهادا هو لي كان كيبلوكي الشاشة كل 5 ثواني. */
  /* ================================================================
   * v3.91 — واجهة خفيفة لـ Google Sheets
   *   api.php?export=adspend&token=...  → المصاريف الخام (للتحرير فالشيت)
   *   api.php?export=perf&token=...     → جدول الأداء محسوب (للقراءة فقط)
   * كترجع غير لي محتاج الشيت (بضع كيلوبايتات) عوض 1.1 ميغا.
   * ================================================================ */
  if (isset($_GET['pushkey'])) {   // v3.98: المفتاح العام ديال Web Push
    $__pk = crm_push_keys();
    crm_out($__pk ? array('ok'=>true, 'key'=>$__pk['pub']) : array('ok'=>false, 'err'=>'no-vapid-keys'), $__pk ? 200 : 500);
  }
  if (isset($_GET['export'])) {
    $__what = (string)$_GET['export'];
    $__d    = crm_read_raw();
    $__ads  = isset($__d['paraveda_adspend_v1']['d']) ? crm_unwrap($__d['paraveda_adspend_v1']['d']) : array();
    if (!is_array($__ads)) $__ads = array();
    $__adsT = isset($__d['paraveda_adspend_v1']['t']) ? (int)$__d['paraveda_adspend_v1']['t'] : 0;
    $__rs   = isset($__d['paraveda_reset_v1']['t'])   ? (int)$__d['paraveda_reset_v1']['t']   : 0;

    if ($__what === 'adspend') {
      crm_out(array('ok'=>true, 't'=>$__adsT, 'rs'=>$__rs, 'rows'=>array_values($__ads)));
    }

    if ($__what === 'perf') {
      $__ord = isset($__d['paraveda_orders_v5']['d']) ? crm_unwrap($__d['paraveda_orders_v5']['d']) : array();
      if (!is_array($__ord)) $__ord = array();
      /* فهرسة الطلبيات بالتاريخ — بلا هادشي كنديرو 109 × 1400 مقارنة */
      $__byDate = array();
      foreach ($__ord as $o) {
        if (!is_array($o) || !empty($o['_del'])) continue;
        $dt = isset($o['dateCreation']) ? (string)$o['dateCreation'] : '';
        if ($dt === '') continue;
        $__byDate[$dt][] = $o;
      }
      $__norm = function($v) { return strtolower(trim((string)$v)); };
      $__rows = array();
      foreach ($__ads as $a) {
        if (!is_array($a)) continue;
        $aDate = isset($a['date'])    ? (string)$a['date']    : '';
        $aAg   = isset($a['agent'])   ? (string)$a['agent']   : '';
        $aPr   = isset($a['produit']) ? (string)$a['produit'] : '';
        $aSrc  = isset($a['source'])  ? (string)$a['source']  : '';
        $amt   = isset($a['amount'])  ? (float)$a['amount']   : 0;

        $cnt = 0; $conf = 0; $livre = 0; $retour = 0; $ca = 0;
        $pool = isset($__byDate[$aDate]) ? $__byDate[$aDate] : array();
        foreach ($pool as $o) {
          /* نفس منطق المطابقة ديال صفحة Dashboard performance بالضبط */
          if ($aAg !== '' && $__norm(isset($o['agent']) ? $o['agent'] : '') !== $__norm($aAg)) continue;
          if ($aPr !== '' && $__norm(isset($o['produit']) ? $o['produit'] : '') !== $__norm($aPr)) continue;
          if ($aAg === '' && $aSrc !== ''
              && $__norm(isset($o['originLead']) ? $o['originLead'] : '') !== $__norm($aSrc)) continue;

          $cnt++;
          $st = isset($o['statut'])    ? (string)$o['statut']    : '';
          $lv = isset($o['livraison']) ? (string)$o['livraison'] : '';
          if ($st === 'Confirmé') $conf++;
          if ($lv === 'Livrée' || $lv === 'Rechange')   { $livre++;  $ca += isset($o['prix']) ? (float)$o['prix'] : 0; }
          if ($lv === 'Retour' || $lv === 'Remboursé')  { $retour++; }
        }
        $__rows[] = array(
          'id'      => isset($a['id']) ? $a['id'] : '',
          'date'    => $aDate,
          'agent'   => $aAg,
          'produit' => $aPr,
          'source'  => $aSrc,
          'amount'  => $amt,
          'count'   => $cnt,
          'conf'    => $conf,
          'livre'   => $livre,
          'retour'  => $retour,
          'ca'      => $ca,
          'cpl'     => $cnt > 0 ? round($amt / $cnt, 2) : '',
        );
      }
      crm_out(array('ok'=>true, 't'=>$__adsT, 'rs'=>$__rs, 'rows'=>$__rows));
    }

    if ($__what === 'orders') {
      /* v3.92: الطلبيات الحية للـ Google Sheet.
       * كنرجعو صفوف (arrays) ماشي objects — الحجم كينقص ~60% وكيدخل
       * مباشرة لـ setValues() بلا تحويل. */
      $__cols = array('id','dateCreation','dateConfirmation','statut','remarques','idCmd',
                      'nom','telephone','ville','adresse','qte','prix','produit','livraison',
                      'upsell','carousell','agent','link','carosellFlag','originLead',
                      'commission','fees','livreur','tracking','dateExp','dateLiv','motif');
      $__since = isset($_GET['since']) ? trim((string)$_GET['since']) : '';
      $__ord = isset($__d['paraveda_orders_v5']['d']) ? crm_unwrap($__d['paraveda_orders_v5']['d']) : array();
      if (!is_array($__ord)) $__ord = array();
      $__out = array();
      foreach ($__ord as $o) {
        if (!is_array($o) || !empty($o['_del'])) continue;              // الممسوحة ما كتبانش
        if ($__since !== '' && (string)(isset($o['dateCreation']) ? $o['dateCreation'] : '') < $__since) continue;
        $row = array();
        foreach ($__cols as $c) {
          $v = isset($o[$c]) ? $o[$c] : '';
          if (is_array($v) || is_object($v)) $v = '';
          $row[] = $v;
        }
        $__out[] = $row;
      }
      /* الأحدث فاللول (نفس ترتيب الـCRM) */
      usort($__out, function($a, $b) {
        if ($a[1] === $b[1]) return ((float)$b[0] < (float)$a[0]) ? -1 : (((float)$b[0] > (float)$a[0]) ? 1 : 0);
        return strcmp((string)$b[1], (string)$a[1]);
      });
      crm_out(array(
        'ok'   => true,
        't'    => isset($__d['paraveda_orders_v5']['t']) ? (int)$__d['paraveda_orders_v5']['t'] : 0,
        'cols' => $__cols,
        'rows' => $__out,
      ));
    }

    if ($__what === 'stats') {
      /* v3.93: تشخيص — كيعطي الأرقام ديال الطلبيات بلا ما يحمّل الداتا كاملة */
      $__ord = isset($__d['paraveda_orders_v5']['d']) ? crm_unwrap($__d['paraveda_orders_v5']['d']) : array();
      if (!is_array($__ord)) $__ord = array();
      $live = 0; $del = 0; $nodate = 0; $bymonth = array(); $min = ''; $max = '';
      foreach ($__ord as $o) {
        if (!is_array($o)) continue;
        if (!empty($o['_del'])) { $del++; continue; }
        $live++;
        $dt = isset($o['dateCreation']) ? (string)$o['dateCreation'] : '';
        if ($dt === '') { $nodate++; continue; }
        $m = substr($dt, 0, 7);
        $bymonth[$m] = (isset($bymonth[$m]) ? $bymonth[$m] : 0) + 1;
        if ($min === '' || $dt < $min) $min = $dt;
        if ($max === '' || $dt > $max) $max = $dt;
      }
      ksort($bymonth);
      crm_out(array(
        'ok'            => true,
        'total_rows'    => count($__ord),
        'live_orders'   => $live,
        'deleted'       => $del,
        'without_date'  => $nodate,
        'oldest'        => $min,
        'newest'        => $max,
        'by_month'      => $bymonth,
        'data_file_kb'  => round(@filesize($DATA_FILE) / 1024),
        'journal_kb'    => round(@filesize($JOURNAL) / 1024),
        'orders_t'      => isset($__d['paraveda_orders_v5']['t']) ? (int)$__d['paraveda_orders_v5']['t'] : 0,
      ));
    }

    if ($__what === 'csv') {
      /* v3.95: CSV مباشر لـ Google Sheets عبر IMPORTDATA() — بلا Apps Script.
       * الأعمدة بنفس ترتيب ورقة COMONDES: A حتى M. بلا رأس. */
      $__ord = isset($__d['paraveda_orders_v5']['d']) ? crm_unwrap($__d['paraveda_orders_v5']['d']) : array();
      if (!is_array($__ord)) $__ord = array();
      $__c = array('dateCreation','dateConfirmation','statut','remarques','idCmd','nom',
                   'telephone','ville','adresse','qte','prix','produit','livraison');
      /* v3.96: &cols=upsell  ولا  &cols=agent,link  → كيرجع غير داك/هادوك الأعمدة،
       * بنفس ترتيب السطور. مفيد للأعمدة لي جايين بعد M فالشيت. */
      if (!empty($_GET['cols'])) {
        $__allf = array('id','dateCreation','dateConfirmation','statut','remarques','idCmd','nom',
                        'telephone','ville','adresse','qte','prix','produit','livraison','upsell',
                        'carousell','agent','link','carosellFlag','originLead','commission','fees',
                        'livreur','tracking','dateExp','dateLiv','motif');
        $__sel = array();
        foreach (explode(',', (string)$_GET['cols']) as $__r) {
          $__r = trim($__r);
          if ($__r === '') continue;
          foreach ($__allf as $__f) { if (strcasecmp($__f, $__r) === 0) { $__sel[] = $__f; break; } }
        }
        if (!$__sel) crm_out(array('ok'=>false,'err'=>'bad-cols','allowed'=>$__allf), 400);
        $__c = $__sel;
      }
      $__rows = array();
      foreach ($__ord as $o) {
        if (!is_array($o) || !empty($o['_del'])) continue;
        $__rows[] = $o;
      }
      usort($__rows, function($a, $b) {
        $x = isset($a['dateCreation']) ? (string)$a['dateCreation'] : '';
        $y = isset($b['dateCreation']) ? (string)$b['dateCreation'] : '';
        if ($x === $y) {
          $ai = isset($a['id']) ? (float)$a['id'] : 0; $bi = isset($b['id']) ? (float)$b['id'] : 0;
          return ($bi < $ai) ? -1 : (($bi > $ai) ? 1 : 0);
        }
        return strcmp($y, $x);
      });
      $out = '';
      foreach ($__rows as $o) {
        $line = array();
        foreach ($__c as $c) {
          $v = isset($o[$c]) ? $o[$c] : '';
          if (is_array($v) || is_object($v)) $v = '';
          $v = (string)$v;
          /* الهاتف: فراغ رفيع فاللول باش Google Sheets ما يحيدش الصفر */
          /* &plain=1 كيحيد الحماية إلا كان عمود الهاتف معمول "نص عادي" فالشيت */
          if ($c === 'telephone' && $v !== '' && $v[0] === '0' && empty($_GET['plain']))
            $v = "\xE2\x80\x8B" . $v;
          $line[] = '"' . str_replace('"', '""', $v) . '"';
        }
        $out .= implode(',', $line) . "\r\n";
      }
      if (!headers_sent()) {
        header('Content-Type: text/csv; charset=utf-8');
        header('Content-Disposition: inline; filename="commandes.csv"');
      }
      echo $out;
      exit;
    }

    crm_out(array('ok'=>false, 'err'=>'unknown-export'), 400);
  }

  $__sig  = crm_data_sig();
  $__inm  = trim((string)($_SERVER['HTTP_IF_NONE_MATCH'] ?? ''));
  $__hit  = crm_etag_cached($__sig);
  if ($__hit !== null && $__inm !== '' && ($__inm === $__hit || $__inm === 'W/' . $__hit)) {
    header('ETag: ' . $__hit);
    http_response_code(304);
    exit;
  }

  $data = crm_read_raw();
  // normalise on the way out so old corrupted entries never reach the browser
  foreach ($data as $k => $v) {
    if (is_array($v) && array_key_exists('d', $v)) { $data[$k]['d'] = crm_unwrap($v['d']); }
  }
  // v3.83: حصر السجل فـ 400 عملية الأخيرة باش أجهزة المتصفح ما تعمرش وتضرب QuotaExceededError
  if (isset($data['paraveda_history_v1']['d']) && is_array($data['paraveda_history_v1']['d'])) {
    if (count($data['paraveda_history_v1']['d']) > 400) {
      $data['paraveda_history_v1']['d'] = array_slice($data['paraveda_history_v1']['d'], 0, 400);
    }
  }
  unset($data['paraveda_backup_v1']);
  unset($data['paraveda_backup_v1_agents']);

  $__body = json_encode($data, JSON_UNESCAPED_UNICODE);
  $__etag = '"' . md5($__body) . '"';
  crm_etag_store($__sig, $__etag);
  header('ETag: ' . $__etag);
  if ($__inm !== '' && ($__inm === $__etag || $__inm === 'W/' . $__etag)) { http_response_code(304); exit; }

  /* PERF v3.90: gzip — الداتا JSON كتضغط ~85%. 1.1MB → ~150KB. */
  if (!headers_sent() && !ini_get('zlib.output_compression')
      && strpos((string)($_SERVER['HTTP_ACCEPT_ENCODING'] ?? ''), 'gzip') !== false
      && function_exists('gzencode')) {
    $__gz = @gzencode($__body, 5);
    if ($__gz !== false) {
      header('Content-Encoding: gzip');
      header('Vary: Accept-Encoding');
      header('Content-Length: ' . strlen($__gz));
      echo $__gz;
      exit;
    }
  }
  header('Content-Length: ' . strlen($__body));
  echo $__body;
  exit;
}

/* ---------- POST ---------- */
if ($m === 'POST') {
  if (!hash_equals($SECRET, crm_token())) crm_out(array('ok'=>false, 'err'=>'token'), 403);

  $raw = file_get_contents('php://input');
  if (strlen($raw) > $MAX_BODY) crm_out(array('ok'=>false, 'err'=>'too-large'), 413);
  $b = json_decode($raw, true);
  if (!is_array($b)) crm_out(array('ok'=>false, 'err'=>'bad-json'), 400);

  /* -- actions (Digylog etc.) -- */
  if (isset($b['action'])) {
    $a = (string)$b['action'];
    if ($a === 'ping') crm_out(array('ok'=>true, 'v'=>'3.83'));
    if ($a === 'restore') crm_out(array('ok'=>false, 'err'=>'restore-not-implemented', 'msg'=>'الاسترجاع كيدار يدوياً من مجلد backups'), 501);
    if ($a === 'sheet_orders') crm_sheet_orders($b);   // v3.97: الشيت → CRM
    if ($a === 'push_subscribe') crm_push_subscribe($b);   // v3.98
    if ($a === 'push_test') crm_push_test($b);             // v3.98
    if ($a === 'quick_order') crm_quick_order($b);         // v3.100: طلبية سريعة من البنت
    if ($a === 'digylog_order_status') crm_dl_order_status($b); // read-only exact Tracking lookup
    if ($a === 'digylog_tracking_auto') crm_out(crm_tracking_auto_guarded());
    if ($a === 'digylog_delivery_auto') crm_out(crm_delivery_auto_guarded());
    if ($a === 'digylog_send_auto') crm_out(crm_dl_send_guarded());
    if ($a === 'digylog_admin') crm_dl_admin($b);          // v3.101: إعدادات Digylog (أدمين)
    if ($a === 'returns_list') crm_returns_list($b);
    if ($a === 'returns_scan') crm_returns_scan($b);
    if ($a === 'returns_control') crm_returns_control($b);
    if ($a === 'returns_restock') crm_returns_restock($b);
    if (strpos($a, 'digylog') === 0) crm_out(array('ok'=>false, 'err'=>'digylog-removed', 'msg'=>'الربط مع Digylog تحيد فـ v3.41'), 410);
    crm_out(array('ok'=>false, 'err'=>'unknown-action'), 400);
  }

  /* -- normal key write -- */
  if (!isset($b['key']) || !array_key_exists('d', $b)) crm_out(array('ok'=>false, 'err'=>'bad-body'), 400);
  $k = (string)$b['key'];
  if (strpos($k, 'afrizon_') === 0) $k = 'paraveda_' . substr($k, 8); // old tabs
  if (!in_array($k, $ALLOWED_KEYS, true)) { crm_audit("reject | key=$k | not-allowed"); crm_out(array('ok'=>false, 'err'=>'key-not-allowed'), 400); }
  // v3.83: paraveda_backup_v1 ملغية لحماية كاش المتصفح من الامتلاء
  if ($k === 'paraveda_backup_v1' || $k === 'paraveda_backup_v1_agents') {
    // FIX v3.90: $t كانت كتستعمل قبل ما تتعرّف (notice + t=null فالجواب)
    crm_out(array('ok'=>true, 'noop'=>'backup_deprecated', 't'=>(int)(microtime(true) * 1000)));
  }

  $d = crm_unwrap($b['d']);
  $t = isset($b['t']) ? (int)$b['t'] : (int)(microtime(true) * 1000);
  $now = (int)(microtime(true) * 1000);
  if ($t > $now + 60000) $t = $now; // clock skew guard

  // v3.62: reset epoch — writes of wiped keys carrying data older than the reset are ignored
  // v3.67: EXCEPT for reset-aware clients — the body now carries rs (the client's seen reset
  // stamp). A device that acknowledged the reset can never silently lose its NEW orders again,
  // even if its clock is behind (client _u < RESET_T was wrongly discarding genuine new rows).
  $__cur0 = crm_read_raw();
  $RESET_T = isset($__cur0['paraveda_reset_v1']['t']) ? (int)$__cur0['paraveda_reset_v1']['t'] : 0;
  $RS = isset($b['rs']) ? (int)$b['rs'] : 0;
  $RESET_AWARE = ($RESET_T > 0 && $RS >= $RESET_T);
  $RESET_KEYS = array('paraveda_catalog_v1','sheet_pièce','paraveda_history_v1','paraveda_adspend_v1','paraveda_perfrows_v1','paraveda_backup_v1');
  if ($RESET_T > 0 && !$RESET_AWARE && in_array($k, $RESET_KEYS, true) && $t < $RESET_T) { crm_audit("reset-stale | key=$k | t=$t < reset=$RESET_T"); crm_out(array('ok'=>true, 'noop'=>'reset-stale', 'reset'=>$RESET_T, 't'=>$RESET_T)); }
  if ($k === 'paraveda_orders_v5' && $RESET_T > 0 && !$RESET_AWARE && is_array($d)) {
    $__f = array(); foreach ($d as $o) { if (is_array($o) && isset($o['_u']) && (float)$o['_u'] >= $RESET_T) $__f[] = $o; }
    $d = $__f;
  }
  // ghost guard: never let a client wipe orders/users with an empty array while server has data
  /* v3.91: zidt paraveda_adspend_v1 — دابا Google Sheet كيقدر يكتب هنا،
   * وإلا تمسحات الورقة بالغلط (ولا سكريبت طاح فنص الطريق) ما خاصش
   * المصاريف كاملين يطيرو من الـCRM. */
  if (($k === 'paraveda_orders_v5' || $k === 'paraveda_users_v1' || $k === 'paraveda_villes_v2' || $k === 'paraveda_chat_v1' || $k === 'paraveda_catalog_v1' || $k === 'paraveda_adspend_v1' || $k === 'paraveda_backup_v1' || $k === 'paraveda_backup_v1_agents') && is_array($d) && count($d) === 0) {
    $cur = $__cur0;   // PERF v3.90: كنعاودو نستعملو القراية ديال فوق عوض قراية جديدة ديال 2.2MB
    if (isset($cur[$k]['d']) && is_array($cur[$k]['d']) && count($cur[$k]['d']) > 0) {
      crm_audit("ghost | key=$k | empty write blocked");
      crm_out(array('ok'=>true, 'noop'=>'ghost', 't'=>(int)$cur[$k]['t']));
    }
  }

  $fh = @fopen($LOCK_FILE, 'c');
  if ($fh) @flock($fh, LOCK_EX);

  // PERF v3.90: هادي الوحيدة لي خاصها تكون طرية — ممكن شي request آخر كتب
  // قبل ما ناخدو القفل. الجوج القرايات ديال فوق كيتشاركو نفس الـ cache.
  $data = crm_read_raw(true);
  $prevT = isset($data[$k]['t']) ? (int)$data[$k]['t'] : 0;

  $__NOMERGE = array('paraveda_orders_v5','paraveda_chat_v1','paraveda_users_v1','paraveda_agent_names_v1','paraveda_villes_v2','paraveda_worktimes_v1','paraveda_remarques_v1','paraveda_avances_v1','paraveda_adspend_v1','paraveda_perfrows_v1','paraveda_livraison_v1','paraveda_history_v1','paraveda_catalog_v1','tabs_list_v1','sheet_pièce');
  if ($t < $prevT && !in_array($k, $__NOMERGE, true)) { // stale write — غير على ليستة ما كيندمجوش
    if ($fh) { @flock($fh, LOCK_UN); @fclose($fh); }
    crm_audit("stale | key=$k | t=$t < $prevT");
    crm_out(array('ok'=>true, 'noop'=>'stale', 't'=>$prevT));
  }
  $prevJson = isset($data[$k]['d']) ? json_encode($data[$k]['d'], JSON_UNESCAPED_UNICODE) : null;
  $newJson  = json_encode($d, JSON_UNESCAPED_UNICODE);
  if ($prevJson === $newJson) {          // nothing changed: touch time only, no backup churn
    /* v3.81: t ما كينقصش عمرو — قبل، جهاز ساعتو متأخرة كان كيرجّع t للور
       → الأجهزة الأخرى كيوقفو يشوفو التبدلات (i.t > c كتفشل ديما). */
    $effT = max($prevT, $t);
    $data[$k]['t'] = $effT;
    crm_write_all($data);
    if ($fh) { @flock($fh, LOCK_UN); @fclose($fh); }
    crm_out(array('ok'=>true, 'noop'=>'same', 't'=>$effT));
  }

  crm_backup();
  // v3.45: orders are merged row-by-row (newest _u wins, rows never dropped) so
  // several agents/admins writing at the same time never erase each other.
  if ($k === 'paraveda_orders_v5' && is_array($d)) {
    $__storedO = (isset($data[$k]['d']) && is_array($data[$k]['d'])) ? crm_unwrap($data[$k]['d']) : null;   // v3.81: unwrap قبل الدمج
    if (is_array($__storedO)) $d = crm_merge_orders($__storedO, $d, $RESET_T);
    // PERF v3.90: تنقية الطلبيات الممسوحة القديمة (أكثر من 30 يوم) — كانو 42% من الداتا
    $d = crm_purge_tombstones($d, $TOMBSTONE_TTL, $TOMBSTONE_MAX);
  }
  // v3.72: الرسائل كيتدمجو union بالـ id (ما كاينش مسح فالشات) — كاتب متزامنين ما يضيعوش رسائل
  if ($k === 'paraveda_chat_v1' && is_array($d)) {
    $__storedC = (isset($data[$k]['d']) && is_array($data[$k]['d'])) ? crm_unwrap($data[$k]['d']) : null;   // v3.81: unwrap قبل الدمج
    if (!is_array($__storedC)) $__storedC = array();
    $byId = array();
    foreach ($__storedC as $m) { if (is_array($m) && isset($m['id'])) $byId[(string)$m['id']] = $m; }
    foreach ($d as $m) {
      if (!is_array($m) || !isset($m['id'])) continue;
      $id = (string)$m['id'];
      if (isset($byId[$id])) { $byId[$id]['read'] = !empty($byId[$id]['read']) || !empty($m['read']); }
      else $byId[$id] = $m;
    }
    usort($byId, function($x, $y) { $a = (float)$x['id']; $b = (float)$y['id']; return $a == $b ? 0 : ($a < $b ? -1 : 1); });
    $d = array_values($byId);
  }
  // v3.79: اليوزرز — دمج بالصفوف (نفس حل الطلبيات): _u الأحدث كيربح، الحذف _del ناعم.
  // حتى دفع قديم ولا ساعة متقدمة ما بقاش يقدر يمسح يوزر مضاف.
  // v3.81: unwrap على الداتا المخزنة قبل الدمج — غلاف مزدوج قديم كان كيخلي
  // الدمج كيبدا من ليستة خاوية → اليوزرز كلهم كيتمسحو بلا ما حد يحس.
  if ($k === 'paraveda_users_v1' && is_array($d)) {
    $__storedU = (isset($data[$k]['d']) && is_array($data[$k]['d'])) ? crm_unwrap($data[$k]['d']) : null;
    if (is_array($__storedU)) {
      $uById = array();
      foreach ($__storedU as $u) { if (is_array($u) && isset($u['id'])) $uById[(string)$u['id']] = $u; }
      $nowms2 = (int)(microtime(true) * 1000);
      foreach ($d as $u) {
        if (!is_array($u) || !isset($u['id'])) continue;
        if (isset($u['_u']) && (float)$u['_u'] > $nowms2) $u['_u'] = $nowms2;
        $uid = (string)$u['id'];
        if (!isset($uById[$uid])) {
          /* v3.81: نفس الاسم ما كيتزادش مرتين بجوج ids — جوج أجهزة زادو نفس
             اليوزر فنفس الوقت كانو كيديرو دوبلون. اللي كاين فالسيرفر كيبقى. */
          $un = (isset($u['username']) && is_string($u['username'])) ? strtolower(trim($u['username'])) : '';
          $dup = false;
          if ($un !== '') { foreach ($uById as $su) { if (empty($su['_del']) && isset($su['username']) && is_string($su['username']) && strtolower(trim((string)$su['username'])) === $un) { $dup = true; break; } } }
          if (!$dup) $uById[$uid] = $u;
          continue;
        }
        /* v3.82: الحذف نهائي (من الجوج جيهات): نسخة فيها _del كتربح دايماً،
           حتى إلا كانت _u ديالها أقدم — يوزر ممسوح ما كيرجعش. */
        $sd = !empty($uById[$uid]['_del']); $id2 = !empty($u['_del']);
        if ($sd || $id2) {
          $cu = isset($uById[$uid]['_u']) ? (float)$uById[$uid]['_u'] : 0;
          $nu = isset($u['_u']) ? (float)$u['_u'] : 0;
          if (!$sd || ($id2 && $nu > $cu)) $uById[$uid] = $u;
          continue;
        }
        $cu = isset($uById[$uid]['_u']) ? (float)$uById[$uid]['_u'] : 0;
        $nu = isset($u['_u']) ? (float)$u['_u'] : 0;
        if ($nu > $cu) $uById[$uid] = $u;
      }
      $d = array_values($uById);
    }
  }
  // v3.78: دمج موحد — الوكلاء/المدن/غيرهم
  if (in_array($k, $__NOMERGE, true) && $k !== 'paraveda_orders_v5' && $k !== 'paraveda_chat_v1' && $k !== 'paraveda_users_v1'
      && is_array($d)) {
    $__storedL = (isset($data[$k]['d']) && is_array($data[$k]['d'])) ? crm_unwrap($data[$k]['d']) : null;    // v3.81: unwrap قبل الدمج
    if (is_array($__storedL)) $d = crm_merge_list($__storedL, $d, $prevT, $t);
  }
  // v3.83: حصر السجل فـ 400 عملية الأخيرة كحد أقصى
  if ($k === 'paraveda_history_v1' && is_array($d)) {
    usort($d, function($x, $y) {
      $atX = (is_array($x) && isset($x['at'])) ? (string)$x['at'] : '';
      $atY = (is_array($y) && isset($y['at'])) ? (string)$y['at'] : '';
      $c = strcmp($atY, $atX);
      if ($c !== 0) return $c;
      $idX = (is_array($x) && isset($x['id'])) ? (float)$x['id'] : 0;
      $idY = (is_array($y) && isset($y['id'])) ? (float)$y['id'] : 0;
      return $idX == $idY ? 0 : ($idX < $idY ? 1 : -1);
    });
    if (count($d) > 400) {
      $d = array_slice($d, 0, 400);
    }
  }
  $pushBy = ($k === 'paraveda_orders_v5' && is_array($d)) ? crm_push_collect_changes(isset($data[$k]['d']) ? $data[$k]['d'] : array(), $d, $now) : array();
  $data[$k] = array('t' => max($prevT + 1, $t), 'd' => $d);   // v3.81: t رتيب ديما — كتابة جديدة كيشوفها كلشي حتى من جهاز ساعتو متأخرة
  $effT = $data[$k]['t'];
  $ok = crm_write_all($data);
  if ($ok && is_array($d)) crm_journal_append($k, $effT, $d);
  if ($fh) { @flock($fh, LOCK_UN); @fclose($fh); }

  if (!$ok) crm_out(array('ok'=>false, 'err'=>'write-failed'), 500);
  crm_audit("write | $k | t=$effT | bytes=" . strlen($newJson));
  if (!empty($pushBy)) { try { crm_push_batch($pushBy); } catch (Throwable $__e) { crm_audit('push-error | ' . $__e->getMessage()); } }   // v3.99
  crm_out(array('ok'=>true, 't'=>$effT));
}

http_response_code(405);
echo '{"ok":false,"err":"method-not-allowed"}';
exit;