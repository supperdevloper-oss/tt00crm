#!/usr/bin/env python3
"""Isolated simulation of the new Digylog sending logic.
Re-implements the PHP decision rules in Python and exercises them against
realistic Digylog API answers. It never touches production data."""
import json, re

NORM_ACC = str.maketrans('éèêëàâäîïôöùûüç', 'eeeeaaa iioouuuc'.replace(' ',''))

def norm(v):
    v = str(v or '').strip().lower().translate(NORM_ACC)
    return re.sub(r'[^a-z0-9]+', '', v)

def phone(v):
    d = re.sub(r'\D+', '', str(v or ''))
    if not d: return ''
    if len(d) == 13 and d.startswith('00212'): d = '0' + d[5:]
    elif len(d) == 12 and d.startswith('212'): d = '0' + d[3:]
    if len(d) == 9 and d[0] != '0': d = '0' + d
    return d

def phone_ok(p): return bool(re.fullmatch(r'0\d{9}', p or ''))

def same_ref(a, b):
    a, b = str(a or '').strip(), str(b or '').strip()
    if not a or not b: return False
    if a == b: return True
    da, db = re.sub(r'\D+','',a), re.sub(r'\D+','',b)
    return bool(da) and da == db

def deep_pick(item, keys):
    for k in keys:
        if isinstance(item, dict) and k in item and not isinstance(item[k], (list, dict)):
            v = str(item[k]).strip()
            if v: return v
    if isinstance(item, dict):
        for v in item.values():
            r = deep_pick(v, keys)
            if r: return r
    return ''

def parse_created(resp, ids):
    """Mirror of crm_dl_parse_created (PHP json_decode(...,true))."""
    out = {i: {'ok': False, 'tracking': '', 'err': ''} for i in ids}
    try: j = json.loads(resp)
    except Exception: return out
    if not isinstance(j, (dict, list)): return out
    is_list = isinstance(j, list)
    def g(k): return None if is_list else j.get(k)
    err = ''
    if g('success') is False: err = 'digylog-success-false'
    elif g('isSuccess') in (False, 0): err = 'digylog-isSuccess-false'
    elif g('errors'): err = str(g('errors'))
    if err:
        msg = str(g('message') or '')
        for k in out: out[k]['err'] = (msg + ': ' + err)[:180]
        return out
    explicit_ok = g('success') is True or g('isSuccess') in (True, 1)
    recs, lst = [], None
    if isinstance(g('orders'), list): lst = g('orders')
    elif isinstance(g('data'), list): lst = g('data')
    elif is_list: lst = j
    elif 'num' in j or 'tracking' in j or 'traking' in j: lst = [j]
    if lst is not None:
        for it in lst:
            if not isinstance(it, dict): continue
            bad = (it.get('isSuccess') in (False, 0)) or bool(it.get('errors'))
            m = ''
            if it.get('errors'): m = str(it['errors'])
            elif it.get('message') is not None: m = str(it['message'])
            recs.append({
                'num': deep_pick(it, ['num','orderNum','order_num','externalId','external_id','externalReference','clientReference','client_reference','orderNumber','order_number']),
                'tracking': deep_pick(it, ['tracking','traking','trackingNumber','tracking_number','barcode']),
                'bad': bad, 'msg': m})
    if not recs:
        if explicit_ok:
            for k in out: out[k]['ok'] = True
            return out
        msg = str(j.get('message') or '')
        for k in out: out[k]['err'] = (msg + ': ' if msg else '') + 'digylog-no-order-confirmed'
        return out
    used, matched = set(), 0
    for oid, v in out.items():
        for ri, rec in enumerate(recs):
            if ri in used: continue
            if not rec['num'] or not same_ref(rec['num'], oid): continue
            used.add(ri)
            if rec['bad']:
                out[oid]['err'] = (rec['msg'] or 'digylog-order-rejected')[:180]; continue
            out[oid]['ok'] = True
            if rec['tracking']: out[oid]['tracking'] = rec['tracking']
            matched += 1
    if matched == 0 and len(recs) == len(out):
        for i, oid in enumerate(out):
            rec = recs[i]
            if rec['bad']:
                out[oid]['err'] = (rec['msg'] or 'digylog-order-rejected')[:180]; continue
            out[oid]['ok'] = True
            # no Tracking is taken: without our own num we cannot prove which
            # record belongs to which order
        return out
    for oid, v in out.items():
        if v['ok']: continue
        if not v['err']: out[oid]['err'] = 'digylog-no-record-for-order'
    return out

def orders_body(store, network, rows, status):
    orders = []
    for r in rows:
        refs = [{'designation': r['ref'][0], 'quantity': r['ref'][1]}]
        orders.append({'num': str(r['id']), 'type': 1, 'mode': 1, 'network': str(network),
                       'store': str(store), 'name': r['name'], 'phone': r['phone'],
                       'address': r['addr'], 'city': r['city'], 'price': float(r['price']),
                       'refs': refs, 'openproduct': 1, 'port': 1, 'note': ''})
    return {'network': int(network), 'store': str(store), 'mode': 1, 'status': int(status),
            'checkDuplicate': 1, 'orders': orders}

def store_by_name(agent_key, boutiques):
    if not agent_key or not boutiques: return ''
    best, best_len = '', 9999
    for st in boutiques:
        ns = norm(st)
        if len(ns) < 3: continue
        if agent_key in ns or ns in agent_key:
            if len(ns) < best_len: best, best_len = st, len(ns)
    return best

def store_known(store, boutiques):
    if not boutiques: return True          # the list is unknown: keep the configured store
    n = norm(store)
    if not n: return False
    return any(norm(d) == n for d in boutiques)

def store_for_agent(agent, stores_map, default_store, boutiques):
    """Mirror of crm_dl_store_for_agent."""
    k = norm(agent)
    if k and k in stores_map:
        st = stores_map[k]
        if store_known(st, boutiques): return st
        by = store_by_name(k, boutiques)
        if by: return by
        if len(boutiques) == 1: return boutiques[0]
        return st
    by = store_by_name(k, boutiques)
    if by: return by
    if default_store:
        if store_known(default_store, boutiques): return default_store
        if len(boutiques) == 1: return boutiques[0]
        return default_store
    if len(boutiques) == 1: return boutiques[0]
    return ''

def eligible(orders, stores_map, default_store, boutiques, disabled=False, gen=3, now_ms=0):
    """Mirror of the candidate selection."""
    if disabled: return [], []
    groups, skipped = {}, []
    for o in orders:
        if o.get('_del') or o.get('dlSent'): continue
        if norm(o.get('statut')) != 'confirme': continue
        if str(o.get('livraison') or '').strip() != '': continue
        miss = next((f for f in ('nom','telephone','adresse','ville','produit')
                     if not str(o.get(f) or '').strip()), None)
        if miss: skipped.append((o['id'], 'missing-' + miss)); continue
        ph = phone(o.get('telephone'))
        if not phone_ok(ph): skipped.append((o['id'], 'bad-phone')); continue
        # A new sender generation resets the retry counter and the backoff:
        # an order can never stay blocked forever by an old failure.
        g = int(o.get('dlGen') or 0)
        next_try = int(o.get('dlNextTry') or 0)
        if g != gen: next_try = 0
        if next_try > now_ms: continue
        ag = str(o.get('agent') or '')
        store = store_for_agent(ag, stores_map, default_store, boutiques)
        if not store: skipped.append((o['id'], 'no-store-for-agent')); continue
        groups.setdefault(store, []).append({
            'id': o['id'], 'name': o['nom'], 'phone': ph, 'addr': o['adresse'],
            'city': o['ville'], 'price': o['prix'], 'ref': (o['produit'], max(1, int(o['qte'])))})
    return groups, skipped

results = []
def check(name, cond, detail=''):
    results.append((name, bool(cond), detail))

# ---- fixtures -------------------------------------------------------------
ORD = [
    {'id': 1001, 'statut': 'Confirmé', 'livraison': '', 'agent': 'Meryam', 'nom': 'Smail',
     'telephone': '0662143552', 'adresse': 'Casablanca', 'ville': 'Casablanca', 'prix': 190,
     'produit': 'Slim Patch', 'qte': 1},
    {'id': 1002, 'statut': 'Confirmé', 'livraison': '', 'agent': 'HAJAR', 'nom': 'Fatima',
     'telephone': '0673345431', 'adresse': 'Rabat', 'ville': 'Rabat', 'prix': 250,
     'produit': 'Slim Patch', 'qte': 2},
    {'id': 1003, 'statut': 'Confirmé', 'livraison': 'Expédier vers', 'agent': 'Meryam', 'nom': 'Already',
     'telephone': '0652429651', 'adresse': 'X', 'ville': 'Y', 'prix': 190, 'produit': 'P', 'qte': 1},
    {'id': 1004, 'statut': 'Appel-2', 'livraison': '', 'agent': 'Meryam', 'nom': 'Called',
     'telephone': '0652429652', 'adresse': 'X', 'ville': 'Y', 'prix': 190, 'produit': 'P', 'qte': 1},
    {'id': 1005, 'statut': 'Confirmé', 'livraison': '', 'agent': 'Meryam', 'nom': 'BadPhone',
     'telephone': '12345', 'adresse': 'X', 'ville': 'Y', 'prix': 190, 'produit': 'P', 'qte': 1},
]
STORES = {'meryam': 'Slim-Bio-MR', 'hajar': 'Slim-Bio-HJ'}

# 1. eligibility
g, sk = eligible(ORD, STORES, '', ['Slim-Bio-MR'])
ids = sorted(r['id'] for rs in g.values() for r in rs)
check('Only Confirmé + empty Suivie are candidates', ids == [1001, 1002], str(ids))
check('Bad phone is skipped, not sent', any(w == 'bad-phone' for _, w in sk), str(sk))
check('Already Expédier vers is never re-sent', 1003 not in ids)
check('Appel-2 is never sent', 1004 not in ids)

# 2. payload
body = orders_body('Slim-Bio-MR', 1, g['Slim-Bio-MR'], 0)
check('Payload uses status=0 (add only)', body['status'] == 0)
check('Payload is mode=1 standard', body['mode'] == 1 and body['orders'][0]['mode'] == 1)
check('Payload carries checkDuplicate', body['checkDuplicate'] == 1)
check('Payload ref uses designation', body['orders'][0]['refs'][0] == {'designation': 'Slim Patch', 'quantity': 1})
check('Payload phone normalized', body['orders'][0]['phone'] == '0662143552')
check('Payload num is the CRM id', body['orders'][0]['num'] == '1001')

# 3. acceptance: documented array answer
resp = json.dumps([{'num': '1001', 'tracking': 'S8363F49B8'}])
p = parse_created(resp, ['1001'])
check('Documented array answer is accepted', p['1001']['ok'])
check('Returned Tracking is captured', p['1001']['tracking'] == 'S8363F49B8')

# 4. acceptance: wrapped answer
resp = json.dumps({'data': [{'num': '1001', 'tracking': 'S111'}]})
check('data-wrapped answer accepted', parse_created(resp, ['1001'])['1001']['ok'])

# 5. acceptance: single object
resp = json.dumps({'num': '1001', 'tracking': 'S222'})
check('single object answer accepted', parse_created(resp, ['1001'])['1001']['ok'])

# 6. validation error with HTTP 200 -> must NOT be accepted
resp = json.dumps({'message': 'invalid phone', 'errors': {'phone': 'bad'}})
p = parse_created(resp, ['1001'])
check('HTTP 200 validation error is NOT acceptance', not p['1001']['ok'])
check('Validation error message is kept', 'invalid phone' in p['1001']['err'])

# 7. isSuccess false -> rejected
resp = json.dumps([{'num': '1001', 'isSuccess': False, 'errors': ['city unknown']}])
p = parse_created(resp, ['1001'])
check('isSuccess=false is rejected', not p['1001']['ok'])

# 8. per-order rejection inside an accepted batch
resp = json.dumps([{'num': '1001', 'tracking': 'S1'}, {'num': '1002', 'isSuccess': False, 'errors': ['store unknown']}])
p = parse_created(resp, ['1001', '1002'])
check('Good order accepted in a mixed batch', p['1001']['ok'])
check('Bad order rejected in a mixed batch', not p['1002']['ok'])

# 9. no order record at all -> not accepted (retry, never duplicate)
resp = json.dumps({'message': 'queued'})
p = parse_created(resp, ['1001'])
check('Answer without any order is NOT acceptance', not p['1001']['ok'])

# 10. num mismatch -> accepted (Digylog created it) but NO Tracking is taken
resp = json.dumps([{'num': '999999', 'tracking': 'S9'}])
p = parse_created(resp, ['1001'])
check('Mismatched num is still accepted', p['1001']['ok'])
check('Mismatched num takes no Tracking', p['1001']['tracking'] == '')

# 10b. a num that does not match any order must not steal the Tracking
resp = json.dumps([{'num': '777', 'tracking': 'S7'}])
p = parse_created(resp, ['1001'])
check('Foreign num never writes a Tracking', p['1001']['tracking'] == '')

# 11. numeric num vs string CRM id
resp = json.dumps([{'num': 1001, 'tracking': 'S3'}])
check('Numeric num matches string CRM id', parse_created(resp, ['1001'])['1001']['ok'])

# 12. agent without a store and no fallback -> skipped
g2, sk2 = eligible([ORD[1]], {'meryam': 'Slim-Bio-MR'}, '', ['A', 'B'])
check('Agent without store is skipped', not g2 and any(w == 'no-store-for-agent' for _, w in sk2))

# 13. single boutique fallback
g3, sk3 = eligible([ORD[1]], {'meryam': 'Slim-Bio-MR'}, '', ['OnlyOne'])
check('Single boutique is used as fallback', 'OnlyOne' in g3)

# 14. default store fallback
g4, sk4 = eligible([ORD[1]], {'meryam': 'Slim-Bio-MR'}, 'DefStore', ['A', 'B'])
check('Default store is used as fallback', 'DefStore' in g4)

# 15. disabled auto switch -> nothing
g5, sk5 = eligible(ORD, STORES, '', ['X'], disabled=True)
check('Disabled auto send sends nothing', not g5)

# 15b. a partially named batch keeps the unmapped orders pending
resp = json.dumps([{'num': '1001', 'tracking': 'SA'}, {'num': 'other', 'tracking': 'SB'}])
p = parse_created(resp, ['1001', '1002'])
check('Named order accepted', p['1001']['ok'])
check('Unnamed order in a partial batch stays pending', not p['1002']['ok'])

# 16. tracking must never leak across orders
resp = json.dumps([{'num': '1001', 'tracking': 'SA'}, {'num': '1002', 'tracking': 'SB'}])
p = parse_created(resp, ['1001', '1002'])
check('Each order keeps its own Tracking', p['1001']['tracking'] == 'SA' and p['1002']['tracking'] == 'SB')

# 17. a boutique named after the agent is resolved automatically
g6, sk6 = eligible([ORD[1]], {'meryam': 'Slim-Bio-MR'}, '', ['Boutique HAJAR', 'Slim-Bio-MR'])
check('Boutique named after the agent is used', 'Boutique HAJAR' in g6, str(g6))

# 18. an order blocked by an old failure is retried immediately
old = dict(ORD[0]); old.update({'dlGen': 1, 'dlTries': 25, 'dlNextTry': 99999999999999})
g7, sk7 = eligible([old], STORES, '', ['Slim-Bio-MR'], gen=3, now_ms=1000)
check('Old generation is retried immediately', any(r['id'] == 1001 for rs in g7.values() for r in rs), str(g7))

# 19. the backoff of the current generation is respected
cur = dict(ORD[0]); cur.update({'dlGen': 3, 'dlTries': 2, 'dlNextTry': 5000})
g8, sk8 = eligible([cur], STORES, '', ['Slim-Bio-MR'], gen=3, now_ms=1000)
check('Current generation respects the backoff', not g8, str(g8))

# 20. no permanent kill: many failures still keep the order a candidate
many = dict(ORD[0]); many.update({'dlGen': 3, 'dlTries': 999, 'dlNextTry': 0})
g9, sk9 = eligible([many], STORES, '', ['Slim-Bio-MR'], gen=3, now_ms=1000)
check('Many failures never kill the order', any(r['id'] == 1001 for rs in g9.values() for r in rs), str(g9))

# 21. the boutique named after the agent wins over the generic default store
g10, _ = eligible([ORD[1]], {'meryam': 'Slim-Bio-MR'}, 'DefStore', ['Boutique HAJAR', 'Slim-Bio-MR'])
check('Boutique named after the agent beats the default store', 'Boutique HAJAR' in g10 and 'DefStore' not in g10, str(g10))

# 22. a configured boutique that does not exist falls back to the only boutique
g11, _ = eligible([ORD[1]], {'hajar': 'Slim-Bio-HJ'}, '', ['TheOnlyOne'])
check('Unknown boutique falls back to the only boutique', 'TheOnlyOne' in g11, str(g11))

# 23. a configured boutique that does not exist is replaced by the matching name
g12, _ = eligible([ORD[1]], {'hajar': 'Slim-Bio-HJ'}, '', ['Boutique HAJAR', 'Other'])
check('Unknown boutique is replaced by the matching boutique', 'Boutique HAJAR' in g12, str(g12))

# 24. a configured boutique that exists is never replaced
g13, _ = eligible([ORD[1]], {'hajar': 'Slim-Bio-HJ'}, '', ['Slim-Bio-HJ', 'Boutique HAJAR'])
check('Existing boutique keeps priority', 'Slim-Bio-HJ' in g13 and 'Boutique HAJAR' not in g13, str(g13))

failed = [r for r in results if not r[1]]
for n, ok, d in results:
    print(('PASS ' if ok else 'FAIL ') + n + (('  -> ' + d) if (d and not ok) else ''))
print(f"\n{len(results)-len(failed)}/{len(results)} simulation checks passed.")
raise SystemExit(1 if failed else 0)
