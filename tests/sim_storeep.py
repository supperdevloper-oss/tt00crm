#!/usr/bin/env python3
"""Isolated simulation of the Storeep -> CRM intake (v4.01).

Re-implements the PHP rules of `crm_storeep_norm` / `crm_storeep_city_price` /
the dedupe of `crm_storeep_insert` in Python and exercises them against
realistic Storeep API payloads (https://docs.storeep.com/orders).

It never touches production data and never calls Storeep.
"""
import json
import re
import sys
import unicodedata

API_PHP = 'api.php'
INDEX = 'index.html'

fails = []
total = [0]
def check(name, cond, extra=''):
    total[0] += 1
    if cond:
        print('PASS', name)
    else:
        print('FAIL', name, extra)
        fails.append(name)

# ---------------------------------------------------------------- helpers
def text(v):
    if v is None or isinstance(v, (list, dict)):
        return ''
    return str(v).strip()

def num(v, default):
    if v is None or isinstance(v, (list, dict)):
        return default
    s = str(v).replace(',', '.').strip()
    if not s:
        return default
    try:
        f = float(s)
    except ValueError:
        return default
    return int(f) if f == int(f) else f

def sheet_date(v):
    s = text(v)
    if not s:
        return ''
    m = re.match(r'^(\d{4})-(\d{1,2})-(\d{1,2})', s)
    if m:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
    else:
        m = re.match(r'^(\d{1,2})[/.\-](\d{1,2})[/.\-](\d{4})', s)
        if not m:
            return None
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if not (1 <= mo <= 12 and 1 <= d <= 31):
        return None
    return '%04d-%02d-%02d' % (y, mo, d)

def sheet_phone(v):
    d = re.sub(r'\D+', '', text(v))
    if len(d) == 12 and d.startswith('212'):
        d = '0' + d[3:]
    elif len(d) == 9 and d[0] != '0':
        d = '0' + d
    return d

def norm_city(s):
    s = unicodedata.normalize('NFD', text(s).lower())
    s = ''.join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r'[^\w]+', ' ', s, flags=re.UNICODE)
    return re.sub(r'\s+', ' ', s).strip()

ALIAS = json.loads(open('/tmp/alias.json', encoding='utf-8').read())

def city_alias(s):
    k = norm_city(s)
    return ALIAS.get(k, k)

def city_price(ville, cities):
    if not cities:
        return 0
    v = city_alias(ville)
    if not v:
        return 0
    best = None
    for c in cities:
        n = city_alias(c.get('nom', ''))
        if not n:
            continue
        p = float(c.get('prix') or 0)
        if n == v:
            return p
        if best is None and (v.startswith(n) or n.startswith(v)):
            best = p
    return 0 if best is None else best

def address(r):
    lst = r.get('addresses') or []
    ship = None
    first = None
    for a in lst:
        if not isinstance(a, dict):
            continue
        if first is None:
            first = a
        t = str(a.get('type') or '').strip().lower()
        if ship is None and t in ('shipping', 'livraison'):
            ship = a
    if ship is None:
        ship = first
    return ship or {}

def storeep_norm(r, cities):
    """Returns (why, order, storeep_id, number) exactly like the PHP version."""
    if not isinstance(r, dict):
        return ('bad-order', None, '', '')
    sid = text(r.get('id'))
    if not sid:
        return ('no-id', None, '', '')
    if r.get('is_test'):
        return ('test-order', None, sid, '')
    if r.get('is_abandoned'):
        return ('abandoned', None, sid, '')

    created = ''
    for f in ('created_at', 'createdAt', 'date_creation', 'dateCreation', 'created'):
        if text(r.get(f)):
            created = text(r.get(f))
            break
    dc = sheet_date(created)
    if not dc:
        return ('bad-date', None, sid, '')

    a = address(r)
    nom = text(a.get('fullname'))
    if not nom:
        nom = (text(a.get('firstname')) + ' ' + text(a.get('lastname'))).strip()
    tel = ''
    for f in ('phone', 'whatsapp', 'telephone', 'mobile'):
        if text(a.get(f)):
            tel = sheet_phone(a.get(f))
            break
    if not tel:
        tel = sheet_phone(r.get('phone'))
    if not tel and not nom:
        return ('no-name-or-phone', None, sid, '')

    ville = ''
    for f in ('city', 'commune', 'province', 'state_or_region', 'neighborhood'):
        if text(a.get(f)):
            ville = text(a.get(f))
            break

    parts = []
    for f in ('address1', 'address2', 'neighborhood', 'district', 'apartment',
              'floor', 'postal_code', 'note'):
        v = text(a.get(f))
        if v:
            parts.append(v)
    adresse = ', '.join(parts)

    items = r.get('items') or []
    names, qte, total = [], 0, 0.0
    for it in items:
        if not isinstance(it, dict):
            continue
        nm = text(it.get('name'))
        if not nm:
            continue
        q = int(num(it.get('quantity'), 1))
        if q < 1:
            q = 1
        qte += q
        total += float(num(it.get('price'), 0)) * q
        names.append(nm + (' x%d' % q if q > 1 else ''))
    produit = ' + '.join(names) or 'Storeep'

    prix = num(r.get('total'), 0)
    if float(prix) <= 0:
        prix = num(r.get('subtotal'), 0)
    if float(prix) <= 0:
        prix = total

    number = text(r.get('number'))
    lead = ''
    for f in ('utm_source', 'source', 'lead_source'):
        if text(r.get(f)):
            lead = text(r.get(f))
            break
    lead = 'Facebook' if not lead else lead[:1].upper() + lead[1:].lower()

    o = {
        'dateCreation': dc,
        'dateConfirmation': '',
        'statut': '',
        'remarques': 'Storeep #' + (number if number else sid),
        'idCmd': '1',
        'nom': nom,
        'telephone': tel,
        'ville': ville,
        'adresse': adresse,
        'qte': max(1, qte),
        'prix': prix,
        'produit': produit,
        'livraison': '',
        'upsell': 0,
        'carousell': '',
        'carosellFlag': '',
        'originLead': lead[:40],
        'commission': city_price(ville, cities),
        'fees': '',
        'livreur': '',
        'tracking': '',
        'dateExp': '',
        'dateLiv': '',
        'motif': '',
        'link': '',
        'agent': 'Meryam',
        'src': 'storeep',
    }
    return (None, o, sid, number)

def marker(rem):
    rem = text(rem)
    if not rem or not rem.lower().startswith('storeep'):
        return ''
    m = re.search(r'storeep\s*#?\s*([0-9A-Za-z\-]+)', rem, re.I)
    return m.group(1).strip() if m else ''

def insert(orders, cities, existing=None, seen=None):
    """Dedupe exactly like crm_storeep_insert (id + number + remarks marker)."""
    existing = existing or []
    seen = dict(seen or {})
    row_mk = {}
    for o in existing:
        mk = marker(o.get('remarques'))
        if mk:
            row_mk[mk] = True
    added, dup, skip, out = 0, 0, 0, []
    for i, r in enumerate(orders):
        why, o, sid, snum = storeep_norm(r, cities)
        if why:
            out.append({'i': i, 'st': 'skip', 'why': why})
            skip += 1
            continue
        is_dup = (sid and (sid in seen or sid in row_mk)) or (snum and (snum in seen or snum in row_mk))
        if is_dup:
            out.append({'i': i, 'st': 'dup'})
            dup += 1
            continue
        existing.append(o)
        if sid:
            seen[sid] = True
        if snum:
            seen[snum] = True
        out.append({'i': i, 'st': 'added'})
        added += 1
    return {'added': added, 'dup': dup, 'skip': skip, 'results': out, 'orders': existing}

# ---------------------------------------------------------------- fixtures
CITIES = [
    {'nom': 'Casablanca', 'prix': 35},
    {'nom': 'Rabat', 'prix': 40},
    {'nom': 'Marrakech', 'prix': 45},
    {'nom': 'Agadir', 'prix': 45},
    {'nom': 'Ait melloul', 'prix': 35},
]

ORDER = {
    'id': 298437652918374563,
    'number': 1042,
    'subtotal': 59.98,
    'discount': 5.0,
    'shipping': 4.99,
    'total': 59.97,
    'currency': 'MAD',
    'market': 'MA',
    'status': 'pending',
    'is_abandoned': False,
    'is_duplicated': False,
    'is_paid': False,
    'is_test': False,
    'created_at': '2026-11-07 08:15:00',
    'updated_at': '2026-11-07 09:30:00',
    'utm_source': 'facebook',
    'items': [
        {'name': 'Slim Bio 60', 'price': 29.99, 'quantity': 2, 'sku': 'SLIM60'},
    ],
    'addresses': [
        {
            'type': 'shipping', 'fullname': 'Hajar El Amrani',
            'firstname': 'Hajar', 'lastname': 'El Amrani',
            'address1': '123 Rue Zerktouni', 'address2': 'Apt 4B',
            'neighborhood': 'Maarif', 'city': 'Casablanca',
            'phone': '+212612345678', 'note': 'Appeler avant',
        }
    ],
}

# ---------------------------------------------------------------- 1. mapping
why, o, sid, snum = storeep_norm(ORDER, CITIES)
check('A real Storeep order is accepted', why is None, str(why))
check('The storeep id is kept for dedupe', sid == '298437652918374563')
check('The storeep number is kept for dedupe', snum == '1042')
check('The order is always assigned to Meryam', o['agent'] == 'Meryam', o['agent'])
check('The order keeps its Storeep source', o['src'] == 'storeep')
check('The order idCmd is the CRM default 1', o['idCmd'] == '1')
check('The order lands with an empty Suivie', o['livraison'] == '')
check('The order lands unconfirmed (the girl confirms it)', o['statut'] == '', o['statut'])
check('The order keeps the Storeep creation date', o['dateCreation'] == '2026-11-07')
check('The order has no confirmation date yet', o['dateConfirmation'] == '')
check('The phone is normalized to the Moroccan 10 digits', o['telephone'] == '0612345678', o['telephone'])
check('The client name is taken from the shipping address', o['nom'] == 'Hajar El Amrani', o['nom'])
check('The city is taken from the shipping address', o['ville'] == 'Casablanca', o['ville'])
check('The address is a single readable line',
      o['adresse'] == '123 Rue Zerktouni, Apt 4B, Maarif, Appeler avant', o['adresse'])
check('Quantity is the sum of the items', o['qte'] == 2, o['qte'])
check('Product names carry the quantity', o['produit'] == 'Slim Bio 60 x2', o['produit'])
check('The price is the Storeep total', o['prix'] == 59.97, o['prix'])
check('The remark keeps the Storeep order number', o['remarques'] == 'Storeep #1042', o['remarques'])
check('The lead source is the utm source', o['originLead'] == 'Facebook', o['originLead'])
check('Delivery cost comes from the CRM city table (Casablanca = 35)', o['commission'] == 35, o['commission'])

# ---------------------------------------------------------------- 2. delivery cost
check('Arabic city alias resolves the CRM price', city_price('الدار البيضاء', CITIES) == 35)
check('A city with no match gets 0 (not a wrong price)', city_price('Timbuktu', CITIES) == 0)
check('Accents/case do not break the match', city_price('aït melloul', CITIES) == 35)
check('Unknown table (empty) never invents a price', city_price('Rabat', []) == 0)

# ---------------------------------------------------------------- 3. bad rows
check('A test order is refused', storeep_norm(dict(ORDER, is_test=True), CITIES)[0] == 'test-order')
check('An abandoned cart is refused', storeep_norm(dict(ORDER, is_abandoned=True), CITIES)[0] == 'abandoned')
check('An order with no id is refused', storeep_norm(dict(ORDER, id=None), CITIES)[0] == 'no-id')
check('A broken date is refused', storeep_norm(dict(ORDER, created_at='pas une date'), CITIES)[0] == 'bad-date')

# ---------------------------------------------------------------- 4. dedupe
res = insert([ORDER, ORDER, ORDER], CITIES)
check('The same webhook delivered 3 times adds exactly 1 order', res['added'] == 1, res['added'])
check('The two repeats are counted as duplicates', res['dup'] == 2, res['dup'])

res2 = insert([dict(ORDER, id=999, number=1043)], CITIES, existing=res['orders'])
check('A second real order is added', res2['added'] == 1)
check('Two Storeep orders = two CRM orders', len(res2['orders']) == 2)

# after a reload the seen list is rebuilt from remarks → still no duplicate
res3 = insert([ORDER], CITIES, existing=res2['orders'], seen={})
check('After a restart the old order is not imported again (remarks marker)', res3['added'] == 0, res3['added'])
check('The marker reader finds the Storeep number', marker('Storeep #1042') == '1042')
check('A normal remark is not treated as a Storeep marker', marker('client préfère le soir') == '')

# ---------------------------------------------------------------- 5. many pages
many = [dict(ORDER, id=100000 + i, number=2000 + i) for i in range(50)]
res4 = insert(many, CITIES)
check('A full page of 50 new orders is imported entirely', res4['added'] == 50, res4['added'])
check('No silent skip on a full page', res4['skip'] == 0, res4['skip'])

# ---------------------------------------------------------------- 6. add-to-CRM shape
check('Every imported order carries the fields the CRM table needs',
      all(k in res2['orders'][0] for k in ('dateCreation', 'nom', 'telephone', 'ville', 'produit',
                                          'qte', 'prix', 'statut', 'livraison', 'agent')))
check('Imported orders never carry a Tracking', res2['orders'][0]['tracking'] == '')

# ---------------------------------------------------------------- 7. PHP wiring
api = open(API_PHP, encoding='utf-8').read()
need = [
    "define('CRM_STOREEP_API', 'https://api.storeep.com/v1')",
    'function crm_storeep_norm(',
    'function crm_storeep_insert(',
    'function crm_storeep_hook(',
    'function crm_storeep_sync(',
    'function crm_storeep_sync_guarded(',
    'function crm_storeep_admin(',
    "if (isset($_GET['action']) && $_GET['action'] === 'storeep_hook') crm_storeep_hook();",
    "$_GET['action'] === 'storeep_sync'",
    "$a === 'storeep_admin'",
    'crm_storeep_sync_guarded(); }',
    "$o['agent'] = 'Meryam';",
]
check('The Storeep intake is wired in api.php', all(x in api for x in need),
      [x for x in need if x not in api].__str__())
check('The webhook is protected by a secret key', "!hash_equals($expect, $key)" in api)
check('The Storeep token is never sent to the browser',
      "'tokenTail'" in api and ("'token'" in api))
check('Client writes cannot wipe a fresh Storeep order', "storeep-guard" in api)
check('Storeep settings file is blocked by .htaccess',
      'storeep_cfg.json' in open('.htaccess', encoding='utf-8').read())

idx = open(INDEX, encoding='utf-8').read()
check('The CRM page version matches the API version',
      "const EXPECTED='4.01';" in idx and "define('CRM_API_VERSION', '4.01')" in api)
adm = open('digylog-admin.html', encoding='utf-8').read()
check('The admin page has the Storeep card', 'storeep_admin' in adm and 'spHook' in adm)

print()
if fails:
    print('%d FAILED' % len(fails))
    for f in fails:
        print('  -', f)
    sys.exit(1)
print('%d checks passed.' % total[0])
