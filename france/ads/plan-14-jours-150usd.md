# Plan 14 jours — budget 150 $ (≈138 €)
### Produit propre · marché FR · prix 9 €

> **À lire avant de dépenser un euro.**
> 150 $ ne servent pas à gagner de l'argent en 14 jours. Ils servent à **acheter des données**
> pour savoir si votre offre tient debout. Si vous comprenez ça, vous ne paniquerez pas au jour 5.
> Objectif réel des 14 jours : **1 créatif gagnant + 1 page qui convertit + 10 à 25 ventes**.

---

## 1. Les chiffres de départ (à connaître par cœur)

| Métrique | Formule | Cible |
|---|---|---|
| CPM | dépenses ÷ impressions × 1000 | 4–8 € (FR) |
| CPC | dépenses ÷ clics | 0,20–0,45 € |
| CTR | clics ÷ impressions | ≥ 1,5 % |
| Taux landing → checkout | clics checkout ÷ clics landing | ≥ 8 % |
| Taux checkout → achat | achats ÷ checkout | ≥ 30 % |
| **CPA** | dépenses ÷ achats | **≤ 6,80 €** pour être rentable à 9 € |

### Combien vous gagnez réellement sur 9 € (Gumroad)
```
Prix affiché .....................  9,00 €  (≈ 10,50 $)
Gumroad 10 % .....................  −1,05 $
Fixe par vente ...................  −0,50 $
Carte 2,9 % + 0,30 $ .............  −0,60 $
-------------------------------------------
Total frais ......................  −2,15 $ ≈ −1,84 €
-------------------------------------------
Net par vente ....................  ≈ 7,15 €
Remboursements (~5 %) ............  −0,35 €
-------------------------------------------
Net réel .........................  ≈ 6,80 €
```
👉 **Seuil de rentabilité : CPA < 6,80 €.**

> Prix à mettre sur la fiche : **devise EUR, 9 €** → le client français voit exactement 9,00 €.
> Si le compte est déjà en USD : `9.99` s'affiche **8,99 €**, `10` s'affiche **9,00 €** (Gumroad
> conserve la terminaison du prix). Détail : `product/LIVRAISON.md` §2.

> ⚠️ **Discover** (la marketplace Gumroad) prend **30 %** : sur une vente à 9 € vous ne gardez
> que ~6,30 €. Au lancement, **désactivez Discover** et n'envoyez que votre propre lien.
> Bonus : Gumroad est *Merchant of Record* → elle collecte et reverse la TVA française,
> vous n'avez aucune démarche OSS/TVA à faire.
En prospection froide, le CPA réel des premiers jours sera plutôt de **8 à 15 €**.
C'est normal. La rentabilité vient : (a) du retargeting, (b) de l'email, (c) d'un upsell.

> **Décision à prendre avant de lancer :** à 9 € vous achetez du **volume et des emails**.
> Si vous voulez être rentable dès la première vente, testez **14,90 €** au jour 8
> (même campagne, même créatif, seul le prix change). C'est le test le plus rentable du plan.

---

## 2. Répartition du budget

| Période | Budget/jour | Total | Phase |
|---|---|---|---|
| J1–J2 | 10 $ | 20 $ | Lancement, apprentissage |
| J3–J4 | 12 $ | 24 $ | Premiers arbitrages |
| J5–J7 | 10 $ | 30 $ | Nettoyage, on garde les gagnants |
| J8–J10 | 12 $ | 36 $ | Test prix + retargeting |
| J11–J14 | 10 $ | 40 $ | Consolidation / scale |
| | | **150 $** | |

---

## 3. Structure de campagne

```
Campagne : [CONV] FR_Friteuse_365_Sales        (objectif : Ventes)
└── Ad set 1 : Broad FR                          budget 10 $/jour
    ├── Créatif C1 01-erreurs.jpg      (texte T1 · titre H2)
    ├── Créatif C2 02-365.jpg          (texte T2 · titre H1)
    ├── Créatif C3 03-temps.jpg        (texte T3 · titre H3)
    └── Créatif C4 04-guide.jpg        (texte T4 · titre H4)
```

**Paramètres du premier ad set**

| Paramètre | Valeur |
|---|---|
| Pays | France (puis Belgique + Suisse romande si ça marche) |
| Âge | 30–65 |
| Genre | Tous (ne segmentez pas au début) |
| Intérêts | **Aucun** — laissez « Advantage+ audience » ouvert |
| Placements | Automatiques (Advantage+) |
| Optimisation | `Purchase` si le pixel remonte (voir `tracking/`), sinon `InitiateCheckout` |
| Attribution | 7 jours clic / 1 jour vue |
| Budget | Au niveau de l'ad set (pas CBO) pour garder le contrôle |

> **Pourquoi pas d'intérêts ?** En 2026, le créatif fait le ciblage. Les intérêts ne servent
> qu'à réduire la taille de l'audience et augmenter le CPM.

---

## 4. Le calendrier, jour par jour

| Jour | Action | Ce que vous regardez | Décision |
|---|---|---|---|
| **J1** | Lancer. Ne touchez à rien. | — | rien |
| **J2** | Rien. Vérifiez juste que le pixel remonte. | impressions > 1 500 | rien |
| **J3** | Premier tri. | CTR de chaque créatif | couper les créatifs < 0,8 % |
| **J4** | Regrouper le budget sur les 2 meilleurs. | CPC, coût par clic checkout | couper si clic > 0,70 € |
| **J5** | Lire la page : où les gens s'arrêtent ? (Clarity/GA4) | scroll 25/50/75 % | corriger la section qui bloque |
| **J6** | Vérifier le checkout. | clics Gumroad vs ventes | si 0 vente : problème de paiement, pas d'audience |
| **J7** | **Bilan de la semaine 1.** | CPA, ventes | voir §6 |
| **J8** | Dupliquer l'ad set gagnant → **prix 14,90 €** (nouvelle page `/14`). | — | test A/B propre |
| **J9** | Lancer le **retargeting** (voir §5). | — | — |
| **J10** | Comparer 9 € vs 14,90 €. | CA par visiteur | garder le plus rentable |
| **J11** | Produire **1 nouvelle vidéo** (V1, 20 s) avec les hooks gagnants. | — | — |
| **J12** | Tester la vidéo contre l'image gagnante. | CTR, CPA | — |
| **J13** | Écrire la séquence email (3 emails) → automatiser. | — | — |
| **J14** | **Décision finale.** | CPA consolidé | scaler / ajuster / arrêter |

---

## 5. Retargeting (les 40 $ les plus rentables)

Publics à créer (Events Manager → Audiences) :

| Audience | Fenêtre | Message |
|---|---|---|
| Visiteurs de la page sans achat | 7 jours | `T5` (rappel) + créatif `05-bonus` |
| Ont cliqué vers le checkout | 14 jours | « Votre commande n'a pas été finalisée » |
| Ont regardé 50 % d'une vidéo | 7 jours | même créatif, autre hook |
| Liste email (acheteurs) | 180 jours | upsell, PAS le produit déjà acheté |

Budget retargeting : **8 $/jour du J9 au J14** (48 $) — retiré du budget prospection
(J9–J14 passe à 8 $/jour en prospection, la somme reste 150 $).

> Le retargeting coûte 2 à 4 fois moins cher par vente. C'est souvent là que le CPA
> repasse sous les 5 € et rend la campagne globalement rentable.

---

## 6. Arbre de décision (le plus important de ce document)

```
J7 — Vous avez dépensé ~70 $.
│
├─ 0 vente
│   ├─ clics < 100  → PROBLÈME CRÉATIF (CTR) → nouveaux hooks, ne touchez pas la page
│   ├─ clics > 100 et checkout < 8 % → PROBLÈME PAGE → refaire le hero + le prix visible
│   └─ checkout > 10 % et 0 achat → PROBLÈME PAIEMENT → tester le lien à la main, moyens de paiement
│
├─ 1–3 ventes (CPA 20–70 $)
│   └─ NORMAL en semaine 1. Continuez, coupez le créatif le plus faible,
│      lancez le retargeting au J9. Ne changez pas le prix maintenant.
│
└─ 5+ ventes (CPA < 14 $)
    └─ BON SIGNE. Augmentez de 20 % tous les 3 jours maximum.
       Ne dupliquez pas 5 fois la même campagne « pour aller plus vite » : vous vous cannibalisez.
```

### Quand couper un créatif
- CTR < 0,8 % après **1 000 impressions** → couper.
- Coût par clic checkout > 3 € après **3 jours** → couper.
- Fréquence > 2,5 sur 7 jours → renouveler le créatif (fatigue).

### Quand scaler
- 3 jours consécutifs avec CPA < 7 € → **+20 %** de budget.
- Jamais +50 % d'un coup : vous repartez en phase d'apprentissage.

---

## 7. Tableau de bord à remplir chaque soir (5 min)

| Date | Dépense | Impr. | Clics | CTR | Checkouts | Ventes | CA | CPA | ROAS | Créatif gagnant |
|---|---|---|---|---|---|---|---|---|---|---|
| | | | | | | | | | | |

Google Sheet, 11 colonnes, une ligne par jour. C'est suffisant. **Ne regardez pas les chiffres plus
d'une fois par jour** — l'optimisation compulsive détruit les campagnes.

---

## 8. Après les 14 jours : les 3 scénarios

| Scénario | Signes | Que faire |
|---|---|---|
| **A — Ça marche** | CPA ≤ 7 € et ≥ 10 ventes | Passer à 20–30 $/jour, ajouter un upsell (19 €) pour monter le panier moyen, créer un 2ᵉ ad set (Belgique/Suisse) |
| **B — Mitigé** | 5–10 ventes, CPA 8–15 € | Ne pas scaler. Travailler **le panier moyen** : upsell + email. Un produit à 9 € seul est rarement viable ; à 9 € + upsell à 19 €, il le devient. |
| **C — Ça ne marche pas** | < 5 ventes, CPA > 20 € | Arrêter la prospection froide. Soit le marché FR à 9 € est trop cher, soit l'offre est faible. Tester : prix 14,90 €, ou l'audience arabe/chinoise, ou un autre produit du même catalogue. |

---

## 9. Les 5 erreurs qui tuent un budget de 150 $

1. **Modifier la campagne tous les jours** → apprentissage jamais terminé.
2. **Optimiser sur « Purchase » alors que le pixel ne remonte pas** → 0 vente, budget brûlé.
3. **Changer le prix ET le créatif ET la page en même temps** → aucune conclusion possible.
4. **Couper un créatif après 200 impressions** → vous coupez au hasard.
5. **Ignorer le retargeting** → vous payez 2 fois pour le même visiteur.

---

## 10. Ce qu'il faut préparer AVANT le jour 1

- [ ] Page en ligne, HTTPS, testée sur mobile (4G, pas wifi)
- [ ] Lien de paiement testé avec **un vrai achat à 1 €** + remboursement
- [ ] Pixel + événements vérifiés (voir `tracking/pixel-gumroad.md`)
- [ ] Livraison automatique de l'email testée (boîte Gmail + Outlook + Yahoo)
- [ ] `merci.html` testée
- [ ] Mentions légales + CGV + politique de confidentialité en ligne
- [ ] Bandeau de consentement cookies actif
- [ ] 4 créatifs en 1080×1350 prêts (+ versions 1:1 et 9:16)
- [ ] Compte publicitaire avec moyen de paiement **international** validé
