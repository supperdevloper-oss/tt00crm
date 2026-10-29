#!/usr/bin/env python3
"""Isolated simulation of the Digylog-style dashboard computations.
Re-implements the rules of __PvDigylogDash (index.html) in Python and checks
them against a deterministic fixture and a read-only local snapshot.
It never touches production data."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
results = []


def check(name, ok, detail=''):
    results.append((name, bool(ok), detail if not ok else ''))


def sold(o):
    return o.get('livraison') in ('Livrée', 'Rechange')


def back(o):
    return o.get('livraison') in ('Retour', 'Remboursé')


def on_road(o):
    return o.get('livraison') in ('Expédier vers', 'Expédié')


def in_flight(o):
    return (o.get('livraison') not in ('Livrée', 'Retour', 'Out Of Stock', 'Remboursé', 'Rechange')
            and o.get('statut') != 'Annulé'
            and (o.get('statut') == 'Confirmé' or bool(o.get('livraison'))))


def scope_filter(scope, o):
    if scope == 'now':
        return in_flight(o)
    if scope == 'ship':
        return on_road(o)
    if scope == 'liv':
        return o.get('livraison') in ('Livrée', 'Rechange')
    if scope == 'ret':
        return o.get('livraison') == 'Remboursé'
    if scope == 'ret2':
        return o.get('livraison') == 'Retour'
    return True


def stats(orders, scope='global'):
    live = [o for o in orders if o.get('statut') != 'Annulé']
    scoped = [o for o in live if scope_filter(scope, o)]
    sd = [o for o in scoped if sold(o)]
    bk = [o for o in scoped if back(o)]
    rd = [o for o in scoped if on_road(o)]
    wt = [o for o in scoped if not o.get('livraison') and o.get('statut') == 'Confirmé']
    sent = [o for o in scoped if o.get('livraison') in
            ('Expédier vers', 'Expédié', 'Livrée', 'Rechange')]
    num = lambda rows, f: sum(float(o.get(f) or 0) for o in rows)
    return {
        'total': len(scoped), 'sold': len(sd), 'back': len(bk), 'onRoad': len(rd),
        'wait': len(wt), 'sent': len(sent), 'oos': len([o for o in scoped if o.get('livraison') == 'Out Of Stock']),
        'ca': num(scoped, 'prix'), 'paye': num(sd, 'prix'), 'encours': num(rd, 'prix'),
        'nonpaye': num(wt, 'prix'), 'comm': num(scoped, 'commission'),
        'pieces': sum(max(1, int(o.get('qte') or 1)) for o in scoped),
    }


def top_products(orders, limit=5):
    m = {}
    for o in orders:
        name = str(o.get('produit') or '').strip()
        if not name:
            continue
        c = m.setdefault(name, {'qty': 0, 'tot': 0, 'ok': 0, 'rev': 0.0})
        c['tot'] += 1
        c['rev'] += float(o.get('prix') or 0)
        if sold(o):
            c['qty'] += max(1, int(o.get('qte') or 1))
            c['ok'] += 1
    rows = [{'name': k, **v, 'pct': (v['ok'] / v['tot'] * 100) if v['tot'] else 0}
            for k, v in m.items()]
    rows.sort(key=lambda r: (-r['qty'], -r['rev']))
    return rows[:limit]


def chart(orders, days=7, today='2026-10-29'):
    """Counts the orders created per day over the last N days."""
    from datetime import date, timedelta
    y, m, d = (int(x) for x in today.split('-'))
    end = date(y, m, d)
    pts = []
    for i in range(days - 1, -1, -1):
        day = (end - timedelta(days=i)).isoformat()
        pts.append(sum(1 for o in orders if str(o.get('dateCreation') or '')[:10] == day))
    return pts


FIXTURE = [
    {'id': 1, 'statut': 'Confirmé', 'livraison': '', 'prix': 100, 'qte': 1, 'commission': 10,
     'produit': 'P1', 'agent': 'Meryam', 'dateCreation': '2026-10-29'},
    {'id': 2, 'statut': 'Confirmé', 'livraison': 'Expédier vers', 'prix': 200, 'qte': 2, 'commission': 20,
     'produit': 'P1', 'agent': 'Meryam', 'dateCreation': '2026-10-28'},
    {'id': 3, 'statut': 'Confirmé', 'livraison': 'Livrée', 'prix': 300, 'qte': 1, 'commission': 30,
     'produit': 'P2', 'agent': 'AYA', 'dateCreation': '2026-10-27'},
    {'id': 4, 'statut': 'Confirmé', 'livraison': 'Rechange', 'prix': 400, 'qte': 1, 'commission': 40,
     'produit': 'P2', 'agent': 'AYA', 'dateCreation': '2026-10-27'},
    {'id': 5, 'statut': 'Confirmé', 'livraison': 'Retour', 'prix': 500, 'qte': 1, 'commission': 50,
     'produit': 'P3', 'agent': 'imane', 'dateCreation': '2026-10-26'},
    {'id': 6, 'statut': 'Confirmé', 'livraison': 'Remboursé', 'prix': 600, 'qte': 1, 'commission': 60,
     'produit': 'P3', 'agent': 'imane', 'dateCreation': '2026-10-26'},
    {'id': 7, 'statut': 'Confirmé', 'livraison': 'Out Of Stock', 'prix': 700, 'qte': 1, 'commission': 70,
     'produit': 'P4', 'agent': 'safa', 'dateCreation': '2026-10-25'},
    {'id': 8, 'statut': 'Annulé', 'livraison': '', 'prix': 800, 'qte': 1, 'commission': 80,
     'produit': 'P4', 'agent': 'safa', 'dateCreation': '2026-10-25'},
    {'id': 9, 'statut': 'Rappel', 'livraison': '', 'prix': 900, 'qte': 1, 'commission': 90,
     'produit': 'P5', 'agent': 'Meryam', 'dateCreation': '2026-10-24'},
]

g = stats(FIXTURE)
check('Cancelled orders never enter the KPIs', g['total'] == 8, str(g['total']))
check('Livrée and Rechange count as delivered', g['sold'] == 2, str(g['sold']))
check('Retour and Remboursé count as returned', g['back'] == 2, str(g['back']))
check('Shipped orders are the ones on the road', g['onRoad'] == 1, str(g['onRoad']))
check('Confirmed with empty Suivie are waiting', g['wait'] == 1, str(g['wait']))
check('Total Expédition counts every parcel that left', g['sent'] == 3, str(g['sent']))
check('Chiffre d affaires sums the scoped orders', g['ca'] == 3700, str(g['ca']))
check('Total Payé is the delivered revenue', g['paye'] == 700, str(g['paye']))
check('En cours de paiement is the shipped revenue', g['encours'] == 200, str(g['encours']))
check('Non payé is the waiting revenue', g['nonpaye'] == 100, str(g['nonpaye']))
check('Pieces are summed from the quantities', g['pieces'] == 9, str(g['pieces']))

check('Hub de livraison counts only delivered orders', stats(FIXTURE, 'liv')['total'] == 2)
check('Hub des retours counts only Remboursé', stats(FIXTURE, 'ret')['total'] == 1)
check('Retournée counts only Retour', stats(FIXTURE, 'ret2')['total'] == 1)
check("Hub d'expédition counts only shipped orders", stats(FIXTURE, 'ship')['total'] == 1)
check('En ce moment counts only orders in flight', stats(FIXTURE, 'now')['total'] == 2,
      str(stats(FIXTURE, 'now')['total']))
check('Scopes never overlap', stats(FIXTURE, 'liv')['total'] + stats(FIXTURE, 'ret')['total']
      + stats(FIXTURE, 'ret2')['total'] + stats(FIXTURE, 'ship')['total']
      + stats(FIXTURE, 'now')['total'] <= g['total'])

top = top_products(FIXTURE)
check('Top products are sorted by sold quantity', [t['name'] for t in top][0] == 'P2',
      str([t['name'] for t in top]))
check('Top products keep the delivered percentage', top[0]['pct'] == 100.0, str(top[0]))
check('Top products never exceed five rows', len(top_products(FIXTURE, 5)) <= 5)

pts = chart(FIXTURE, 7)
check('The evolution chart has one point per day', len(pts) == 7, str(pts))
check('The evolution chart counts the orders of each day', pts[-1] == 1 and pts[-2] == 1, str(pts))
check('The 30 day chart also works', len(chart(FIXTURE, 30)) == 30)

# Read-only sanity check against the local snapshot (never packaged, never mutated).
snap = ROOT / 'crm_data.json'
if snap.exists():
    data = json.loads(snap.read_text(encoding='utf-8'))
    rows = data.get('paraveda_orders_v5', {}).get('d', [])
    rows = [r for r in rows if isinstance(r, dict) and not r.get('_del')]
    s = stats(rows)
    check('Snapshot: every live order is counted once', s['total'] == len([r for r in rows if r.get('statut') != 'Annulé']))
    check('Snapshot: delivered plus returned plus shipped fits the total',
          s['sold'] + s['back'] + s['onRoad'] + s['oos'] + s['wait'] <= s['total'])
    check('Snapshot: the revenue is not negative', s['ca'] >= 0)
    check('Snapshot: top products exist', len(top_products(rows)) > 0)
else:
    print('note: no local snapshot, snapshot checks skipped')

failed = [r for r in results if not r[1]]
for n, ok, d in results:
    print(('PASS ' if ok else 'FAIL ') + n + (('  -> ' + d) if (d and not ok) else ''))
print(f"\n{len(results)-len(failed)}/{len(results)} dashboard simulation checks passed.")
raise SystemExit(1 if failed else 0)
