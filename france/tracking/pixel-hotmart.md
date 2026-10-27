# Tracking — Pixel Meta + Conversions API + attribution Hotmart

> Objectif : que Meta voie la **vente complète** (pas seulement le clic), et que vous sachiez
> **quel créatif** a rapporté chaque euro. Sans ça, l'algorithme optimise à l'aveugle.
>
> ⏱ Temps : 45–60 min. Faites-le **avant** de lancer la première campagne.

---

## 0. Le problème à comprendre d'abord

Le tunnel réel ressemble à ça :

```
facebook.com  →  votre landing (votredomaine.fr)  →  pay.hotmart.com  →  email de livraison
     ↑ pixel         ↑ pixel : PageView, ViewContent,        ↑ pixel ABSENT
                      InitiateCheckout (clic CTA)              (autre domaine)
```

**Conséquence :** votre pixel voit les clics mais **jamais** le `Purchase`.
Si vous optimisez sur « Purchase », Meta n'apprend rien et votre coût par achat explose.

Trois façons de régler ça (utilisez la **1**, la **2** en complément) :

| # | Solution | Effort | Fiabilité |
|---|---|---|---|
| 1 | **Pixel natif Hotmart** (intégration dans la fiche produit) | 5 min | ⭐⭐⭐⭐ |
| 2 | **Connexion Conversions API** (Meta ⇄ Hotmart) | 15 min | ⭐⭐⭐⭐⭐ (récupère les ventes perdues par iOS) |
| 3 | Webhook / postback maison (`sck`) | 1–2 h | ⭐⭐⭐ (pour le suivi fin par créatif) |

---

## 1. Créer le pixel

1. `business.facebook.com` → **Paramètres du compte publicitaire** → **Sources de données** → **Ensembles de données** → **Ajouter**.
2. Nom : `FR — Friteuse 365`.
3. Copiez l'ID (15–16 chiffres). C'est le `VOTRE_PIXEL_ID`.
4. Dans votre `index.html`, cherchez `TODO-PIXEL` et décommentez le bloc en remplaçant l'ID.

✅ Vérification : ouvrez le site, puis `business.facebook.com/events_manager` → **Tester les événements** → votre URL doit remonter un `PageView`.

---

## 2. Brancher le pixel sur Hotmart (indispensable)

Dans Hotmart :

1. **Produits** → votre produit → **Paramètres** (ou *Affiliation/Outils*) → onglet **Pixel / Suivi**.
2. Ajoutez **Meta Pixel** et collez l'ID.
3. Activez les événements : `Purchase`, `InitiateCheckout`, `AddPaymentInfo`.
4. Enregistrez, puis **testez** avec un achat réel à 1 € (ou un code promo 100 %).

> Si votre lien de paiement est un lien d'**affilié** (pas votre propre produit),
> vous ne pouvez pas installer votre pixel : c'est Hotmart du producteur qui compte.
> → Dans ce cas, passez par la **Conversions API** (§3) ou demandez au producteur d'ajouter votre pixel.

---

## 3. Conversions API (le vrai gain en 2026)

Sans CAPI, 20–40 % des conversions sont perdues (bloqueurs, iOS, Safari).
Avec, Meta reçoit un signal serveur, beaucoup plus fiable.

**Option A — intégration native (recommandé)**
`Events Manager` → **Sources de données** → votre ensemble → **Paramètres** → **Conversions API** →
**Créer une connexion directe** → chercher **Hotmart**. Si Hotmart n'apparaît pas :
**Passerelle** → choisir *Hotmart* (ou *Zapier/Make* si vous n'avez rien).

**Option B — sans intégration : webhook + Make/Zapier**
1. Hotmart → **Outils** → **Webhook** → URL : votre scénario Make/Zapier.
2. Événement : `PURCHASE_APPROVED` (et `PURCHASE_REFUNDED`).
3. Scénario : POST vers
   `https://graph.facebook.com/v20.0/{PIXEL_ID}/events?access_token={TOKEN}`
   avec :
   ```json
   {
     "data": [{
       "event_name": "Purchase",
       "event_time": 1760000000,
       "event_id": "hotmart_{{transaction}}",
       "action_source": "website",
       "user_data": { "em": ["{{email_sha256}}"], "ph": ["{{phone_sha256}}"] },
       "custom_data": { "value": 9.00, "currency": "EUR", "content_name": "365 Recettes" }
     }]
   }
   ```
   ⚠️ Les emails/téléphones doivent être **hachés en SHA-256** avant l'envoi.

---

## 4. Attribution : savoir quel créatif vend

### a) Côté Meta (dans les liens)
Créez vos liens **directement dans l'éditeur d'annonce** avec ces paramètres d'URL :

```
utm_source=facebook
&utm_medium=paid
&utm_campaign={{campaign.name}}
&utm_adset={{adset.name}}
&utm_content={{ad.name}}
&ad_id={{ad.id}}
```

### b) Côté Hotmart
Hotmart accepte deux paramètres sur le lien de paiement :

| Paramètre | Rôle | Recommandation |
|---|---|---|
| `src` | source de la vente, visible dans les rapports | `facebook_<campagne>` |
| `sck` | « source code », remonte dans la colonne *Origine* | `<nom_du_créatif>` |

Le `index.html` fourni **transmet automatiquement** `utm_source`, `utm_medium`, `utm_campaign`
vers `src`, et `utm_content` vers `sck`. Il ne vous reste qu'à vérifier dans
**Hotmart → Ventes** que la colonne *Origine* affiche bien votre créatif.

### c) Tableau de bord minimal (Google Sheet)
Colonnes utiles : `date | créatif | dépenses | clics | ventes | CA | remboursements | ROAS`.
Rempli 1×/jour à la main. C'est le seul tableau dont vous avez besoin les 14 premiers jours.

---

## 5. Événements : qui envoie quoi

| Événement | Envoyé par | Quand | Utilité |
|---|---|---|---|
| `PageView` | votre landing | chargement | base d'audience (retargeting) |
| `ViewContent` | votre landing | chargement | audience « a vu la page » |
| `CTAClick` *(custom)* | votre landing | clic CTA | diagnostic : le clic marche, la page non ? |
| `InitiateCheckout` | votre landing | clic vers Hotmart | **meilleur objectif intermédiaire** |
| `Purchase` | **Hotmart** (pixel + CAPI) | paiement approuvé | optimisation finale |

> **Astuce budget 150 $** : si en 3 jours votre campagne « Purchase » n'a aucune conversion,
> dupliquez-la en optimisant sur **`InitiateCheckout`** pour que l'algorithme apprenne plus vite,
> puis repassez sur `Purchase` dès 5–10 ventes.

---

## 6. RGPD / consentement (obligatoire en France)

Vous ne pouvez pas poser un pixel Meta avant consentement (CNIL + ePrivacy).
Trois solutions, de la plus simple à la plus propre :

1. **Bandeau simple** (Axeptio, Tarteaucitron, Cookiebot gratuit) qui charge le pixel seulement après « Accepter ».
2. Le snippet fourni dans `index.html` ne charge le pixel **que si** `localStorage.getItem('consent') === 'yes'`.
3. Ne rien faire → risque de plainte + signalement, et vos données seront de toute façon incomplètes.

Ajoutez aussi une page **Politique de confidentialité** et **Mentions légales** (liens dans le footer)
qui mentionnent : responsable de traitement, base légale, Meta Platforms Ireland, droit d'accès/suppression.

---

## 7. Checklist avant lancement

- [ ] Pixel créé et `PageView` visible dans *Tester les événements*
- [ ] `ViewContent` remonte avec `value` et `currency`
- [ ] Pixel Hotmart branché sur le produit
- [ ] CAPI connectée (ou webhook Make)
- [ ] Un achat test réel a fait remonter un `Purchase` dans Events Manager
- [ ] Paramètres d'URL configurés (`utm_*` + `ad_id={{ad.id}}`)
- [ ] `src` et `sck` visibles dans le rapport Ventes Hotmart
- [ ] Bandeau de consentement actif
- [ ] Domaine en HTTPS avec certificat valide
- [ ] Page de remerciement testée sur mobile (`merci.html`)

---

## 8. Erreurs qui coûtent cher

| Erreur | Conséquence | Correctif |
|---|---|---|
| Optimiser sur « Purchase » sans signal | 0 conversion, CPM qui monte | objectif `InitiateCheckout` puis bascule |
| Un seul pixel, deux domaines | données éclatées | un seul ensemble de données |
| Oublier `event_id` en CAPI | ventes comptées 2× | même `event_id` côté navigateur et serveur |
| Pas de consentement | pixel bloqué / risque légal | bandeau CNIL |
| Modifier la campagne 3× le jour 1 | phase d'apprentissage infinie | 72 h sans toucher |
