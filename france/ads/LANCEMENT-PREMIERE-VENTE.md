# 🚀 LANCEMENT — Première vente Meta Ads

**Objectif : 1 seule vente. Budget : 15 $/jour, 5 jours = 75 $.**
Produit : 365 Recettes pour Friteuse à Air · 2,97 € · Gumroad `kidcfk`
Landing : `https://www.easymeatrecipe.com/Guide/`

> ⚠️ **Lis la section 0 en entier avant de toucher à Ads Manager.**
> Quatre problèmes bloquent la campagne aujourd'hui. Trois se règlent en 20 minutes.

---

# 0. 🔴 CE QUI BLOQUE LE LANCEMENT (à faire dans cet ordre)

## 0.0 — ✅ Le bon lien : `easymeatrecipe.gumroad.com` (username changé)

Vérifié le 31/10 :

| URL testée | Résultat |
|---|---|
| `isabelkemp.gumroad.com/l/airfryer` | ❌ **Page not found** |
| `easymeatrecipe.gumroad.com/l/airfryer` | ✅ 200 — prix 2,97, 5 visuels, 6 détails, vendeur « Friteuse Facile » |
| `…l/airfryer?wanted=true` | ✅ ouvre directement le checkout |

⇒ **Le username Gumroad a été changé en `easymeatrecipe`.** Tous les anciens liens
`isabelkemp` sont morts. Le `index.html` du dépôt est déjà corrigé (L731) :

```js
checkout : "https://easymeatrecipe.gumroad.com/l/airfryer?wanted=true",
```

> 🛑 **Ne rechange plus jamais le username.** Chaque changement casse tous les liens
> déjà publiés, les emails envoyés et les pubs en cours.

---

## 0.1 — Ta copie locale de `index.html` est une VIEILLE version · 3 min

Ta capture VS Code montre, aux lignes 669-674 :

```html
<a href="#">Mentions légales</a>            ← ancien
<a href="#">CGV</a>
<p>… édité par [Friteuse Facile], . Contact : [contact@easymeatrecipe.com].</p>
        ↑ nom de marque au lieu de la raison sociale, adresse vide, email entre crochets
```

La version à jour contient :

```html
<a href="mentions-legales.html">Mentions légales</a>
<a href="cgv.html">CGV</a>
<a href="confidentialite.html">Politique de confidentialité</a>
<a href="#" id="manageCookies">Gérer mes cookies</a>
<a href="mailto:[VOTRE EMAIL]">Contact / Support</a>
<p><b id="brandFoot">Friteuse Facile</b> — guide numérique édité par [VOTRE NOM COMPLET],
   [VOTRE ADRESSE]. Contact : [VOTRE EMAIL]. Ventes opérées par Gumroad, Inc. …</p>
```

⇒ **Ne corrige pas ta vieille copie à la main : re-télécharge le fichier.**

```
https://github.com/supperdevloper-oss/tt00crm/raw/arena/5faa1edd-tt00crm/france/index.html
```

Puis dans ce fichier, seules **2 choses** restent à faire (Ctrl+F) :
`pixelId` (ligne 697) et les 3 champs `[VOTRE …]` (footer + 3 pages légales).

> ⚠️ Le footer ne doit **jamais** contenir le nom de marque à la place de la raison sociale :
> la loi française exige l'**identité réelle** de l'éditeur.

---

## 0.2 — Passer le produit Gumroad en EUR · 3 min · BLOQUANT

Test réel du checkout (`gumroad.com/checkout?product=kidcfk`) :

```
Sous-total : US$2.97
Devise     : $ (US Dollars) — detected
             £ · ¥ · ₹ · A$ · CAD$ · HK$ · SGD$ · NT$ · NZ$ · R$ · ZAR · CHF …
             ⚠️ PAS d'EUR dans la liste
```

⇒ Un acheteur français paie **2,97 $ (~2,70 €)**, pas 2,97 €. La pub annonce « 2,97 € ».

**Correctif :** Product → Edit → section **Pricing** → clique sur le symbole **`$`**
à gauche du montant `2.97` → choisis **EUR / €** → Save.
Le montant devient `2,97 €` et le checkout facture en euros.

**Contrôle :** recharge `https://easymeatrecipe.gumroad.com/l/airfryer` en navigation privée.
Tu dois lire **2,97 €** (et non `$2.97`).

> Si le sélecteur de devise n'apparaît pas ou si EUR est absent, écris à
> `support@gumroad.com` : « *Please change the display currency of my product
> (permalink: airfryer) from USD to EUR.* » — c'est fait en 24 h.

---

## 0.3 — La garantie dit 30 jours à 3 endroits sur Gumroad · 4 min · BLOQUANT

Ta fiche produit affiche :

| Endroit sur Gumroad | Ce qui est écrit | À mettre |
|---|---|---|
| Champ **Description**, section `GARANTIE` | « **30 jours.** Si le guide… » | **14 jours** |
| Section **Settings → Refund period** | `30-day money back guarantee` | **14 days** (si l'option existe) |
| Champ **Additional details → Garantie** | « 14 jours » ✅ | déjà bon |

Et la landing (version à jour) dit **14 jours** partout.

> ⚠️ Une garantie annoncée à 30 jours dans la description **engage juridiquement** :
> un client pourra réclamer un remboursement au jour 25 et tu devras l'accepter.
> Aligne tout sur **14 jours** avant de dépenser un euro en publicité.

**Texte corrigé à coller dans Description** (remplace le bloc `GARANTIE` seul) :
```
GARANTIE
14 jours. Si le guide ne vous sert pas, répondez à l'email de confirmation : remboursement,
sans justification.
```

---

## 0.3 bis — La page en ligne n'est pas la bonne version · 5 min · BLOQUANT

`fetch_page` sur `https://www.easymeatrecipe.com/Guide/` renvoie encore :

| En ligne aujourd'hui | Attendu |
|---|---|
| « 30 jours » (FAQ + bouton final) | « 14 jours » |
| aucune bannière cookies | bandeau + pixel conditionné |
| liens légaux `href="#"` | 3 pages réelles |
| prix 2,97 € | ✅ déjà bon |

⇒ La version corrigée **n'est pas en ligne**. cPanel → `public_html/Guide/` →
uploader le contenu du pack (5 fichiers `.html` + `assets/css/legal.css`).

**4 URL à tester après upload** (toutes doivent répondre) :
```
https://www.easymeatrecipe.com/Guide/
https://www.easymeatrecipe.com/Guide/mentions-legales.html
https://www.easymeatrecipe.com/Guide/cgv.html
https://www.easymeatrecipe.com/Guide/confidentialite.html
```
Puis **Ctrl+F « 30 jours »** sur l'accueil : plus rien ne doit sortir.

> Sans HTTPS valide sur ces pages, Meta refuse la pub (et le pixel ne part pas).

---

## 0.4 — Pixel Meta : 2 endroits, 1 seul ID · 5 min

```
Pixel ID : 28976191782041006     ✅ déjà installé dans index.html (L735)
```

| Où | Chemin exact | Ce que ça trace |
|---|---|---|
| **Landing** (HostGator) | ✅ `CONFIG.pixelId = 28976191782041006` | `PageView`, `ViewContent`, `CTAClick` — **après consentement** |
| **Gumroad** | Settings → **Advanced** → Third-Party Analytics → *Facebook Pixel* | `ViewContent`, `InitiateCheckout`, **`Purchase`** |

🔴 **Sans le pixel côté Gumroad, il n'y a AUCUN `Purchase`.** La landing ne peut pas savoir
qu'une vente a eu lieu : le paiement se fait sur `gumroad.com`. C'est le point qui casse
90 % des campagnes « conversion ».
Source : Gumroad Help 255 (viewed → ViewContent · iwantthis → InitiateCheckout · purchased → Purchase).

> Le statut du pixel reste « Unverified » jusqu'à la première vente réelle. C'est normal.

---

# 1. Ce qu'il te faut avant de cliquer (checklist)

| # | Élément | Où | État |
|---|---|---|---|
| 1 | Page Meta Business + page Facebook (nom : Friteuse Facile) | business.facebook.com | ⬜ |
| 2 | Compte publicitaire avec moyen de paiement (carte) | Ads Manager | ⬜ |
| 3 | Domaine `easymeatrecipe.com` vérifié dans Business Manager | Business Settings → Brand Safety → Domains | ⬜ |
| 4 | Pixel installé aux 2 endroits (§0.4) | — | ⬜ |
| 5 | Produit Gumroad en EUR + 14 jours (§0.2–0.3) | — | ⬜ |
| 6 | Landing à jour (§0.1) | HostGator | ⬜ |
| 7 | 4 PDF réellement dans l'onglet **Content** de Gumroad | Gumroad | ⬜ |
| 8 | Achat test avec code 100 % | Gumroad → Discounts | ⬜ |
| 9 | Profil vendeur : nom + support email (§6 bis du guide Gumroad) | gumroad.com/settings/profile | ⬜ |
| 10 | Créatifs prêts (15 fichiers) | `france/assets/creatives/` | ✅ |

---

# 2. Structure de campagne (n'en dévie pas)

```
Campagne      PROSPECTION FR — 1 vente
  └ Ad set    FR · Large · 25-65 · Femmes
      └ Ad    3 créatifs (même texte, 3 visuels)
```

| Réglage | Valeur | Pourquoi |
|---|---|---|
| **Objectif** | **Ventes** (Conversions) | optimise sur `Purchase`, pas sur les clics |
| Événement de conversion | `Purchase` | — |
| **Budget** | **15 $/jour · CBO activé** | 1 seul ad set, le budget reste sur la campagne |
| **Audience** | France · 25–65 · Femmes | la cible réelle d'un guide de cuisine |
| **Ciblage détaillé** | **aucun** (ni intérêts, ni lookalike) | à 75 $ on laisse l'algorithme trouver |
| **Placements** | **Avantage+ (automatiques)** | ne pas restreindre : le reach coûte plus cher |
| **Optimisation** | `Purchase` | dépense seulement si Meta croit à une vente |
| **Attribution** | 7 jours clic / 1 jour vue | défaut, ne pas toucher |
| **Âge minimum** | 25 | en dessous, aucun pouvoir d'achat |

### Pourquoi l'objectif « Ventes » et pas « Trafic »
Avec `Trafic` tu paies des clics qui ne rapportent rien et Meta n'apprend jamais qui achète.
Avec `Ventes`, Meta cherche les acheteurs — même à 2,97 €, c'est le seul réglage qui te
donne une **audience de retargeting** utilisable au jour 4.

> ⚠️ Si Meta refuse « Ventes » (pixel non vérifié au départ), lance en `Trafic` **3 jours
> maximum**, puis repasse en `Ventes`. Ne reste pas en Trafic.

---

# 3. L'annonce — copie-colle

## 3.1 Créatifs (choisis 3, même format)

| Fichier | Format | Message |
|---|---|---|
| `01-erreurs-4x5.jpg` | 1080×1350 | « 3 erreurs qui rendent votre poulet sec » |
| `03-temps-4x5.jpg` | 1080×1350 | « Four 45 min / Friteuse 12 min » |
| `02-365-4x5.jpg` | 1080×1350 | « 365 recettes » |

Chemins : `france/assets/creatives/`
Téléchargement direct : `https://github.com/supperdevloper-oss/tt00crm/raw/arena/5faa1edd-tt00crm/france/assets/creatives/01-erreurs-4x5.jpg`

> **Format 4:5 obligatoire** : il occupe le plus de surface sur mobile. Le 1:1 et le 9:16
> servent seulement si tu ajoutes des placements Stories/Reels.
> ⚠️ Ne mets **jamais** deux formats différents dans le même ad set : Meta compare mal.

## 3.2 Texte principal (T1 — le plus performant)

```
Votre poulet sort sec de la friteuse ? Ce n'est pas l'appareil.

C'est l'un de ces 3 réglages :
• le temps (4 minutes de trop suffisent)
• la température de départ
• le panier trop rempli

Notre guide corrige les trois, recette par recette : quantité, temps, température, geste.

365 recettes testées · ingrédients simples · PDF immédiat
2,97 € — paiement unique, aucun abonnement.

👉 Téléchargez le guide
```

**Titre (headline) :**
```
365 recettes — 2,97 € seulement
```

**Description :**
```
Téléchargement immédiat · Garantie 14 jours
```

**Bouton CTA :** `En savoir plus`
> Prospection froide = `En savoir plus`. `Acheter` fait chuter le CTR de 20–30 % sur une
> audience qui ne te connaît pas.

## 3.3 URL du site (destination)

```
https://www.easymeatrecipe.com/Guide/?utm_source=fb&utm_medium=cpc&utm_campaign=fr_j1&utm_content=erreurs
```

Le `buildUrl()` de la landing récupère ces paramètres et les recopie vers Gumroad
(`referrer=fb_cpc_fr_j1`) — c'est ce qui te permet de voir **quelle pub a vendu**
dans Gumroad → Ventes → Referrer. Les 4 boutons sont déjà branchés.

> Change seulement `utm_content` pour chaque créatif : `erreurs` · `temps` · `365`.

---

# 4. Lancement, minute par minute

1. **Events Manager → Test Events** : ouvre-le, puis visite ta landing.
   Tu dois voir `PageView` puis `ViewContent` **après avoir cliqué « Accepter »** sur le bandeau cookies.
   ❌ Rien ne s'affiche → le pixel n'est pas bon, arrête ici.
2. **Ads Manager → Créer** → objectif **Ventes** → nom `PROSPECTION FR — 1 vente`.
3. **Ad set** : applique le tableau §2 (France, 25–65, Femmes, 15 $/jour, Avantage+).
4. **Ad** : 3 visuels, le texte §3.2, l'URL §3.3.
5. **Publier.** Puis **vérifier la pub dans l'onglet « Aperçu » sur mobile** :
   le texte est-il lisible ? le prix visible ? la page s'ouvre-t-elle en moins de 3 s ?
6. **Ne touche plus à rien pendant 72 heures.**

> 🔴 **La règle des 72 h** : Meta a besoin de ~50 événements pour sortir de la phase
> d'apprentissage. À 15 $/jour tu en auras très peu — c'est normal. Modifier le budget,
> l'audience ou le créatif **remet le compteur à zéro**. C'est l'erreur n°1 des débutants.

---

# 5. Ce que tu regardes (et quand)

| Moment | Où | Métrique | Seuil d'alerte |
|---|---|---|---|
| **J+1 (après 24 h)** | Ads Manager | Dépense | ~15 $ consommés |
| | | CTR (taux de clic) | **< 0,8 %** ⇒ le créatif ne marche pas |
| | | CPM | > 12 $ ⇒ audience trop étroite |
| | | Clics sur le lien | au moins 15 |
| **J+2** | Gumroad → Ventes | `InitiateCheckout` | 0 ⇒ problème de page ou de prix |
| **J+3** | Ads Manager | **Achats** | **0 achat = décision** |
| | Landing | taux de clic vers Gumroad | < 5 % ⇒ la page ne convainc pas |

## Les 3 décisions possibles à J+3

| Situation | Diagnostic | Action |
|---|---|---|
| **1 vente ou plus** | ✅ l'offre tient | ne touche à rien, laisse tourner jusqu'à 75 $ |
| **0 vente mais CTR > 1,5 %** | la pub marche, la page non | garde la pub, refais le **haut de page** (hero + prix + preuve) |
| **0 vente et CTR < 0,8 %** | le créatif ne marche pas | change **le visuel**, pas le texte. Relance 3 jours |

> **Objectif réaliste** : 1 vente avec 75 $ = CPA 75 $. C'est **normal et attendu** à ce prix.
> Cette première vente ne sert pas à gagner de l'argent : elle sert à **débloquer le pixel**
> (`Purchase` vérifié), à créer ta première audience de retargeting, et à prouver que
> le tunnel fonctionne de bout en bout.

---

# 6. Garde-fous — à respecter absolument

| ❌ Ne fais pas | Pourquoi |
|---|---|
| Boost le post depuis la page Facebook | aucun ciblage, aucun pixel, budget gaspillé |
| Change le budget ou l'audience avant 72 h | remet l'apprentissage à zéro |
| Lance 2 campagnes en parallèle | 75 $ ne suffisent pas pour 2 ; tu doubles le bruit |
| Mets « 100 % satisfait ou remboursé » sans conditions | Meta peut refuser ; et ce n'est pas ce que dit ta CGV |
| Utilise « Guérit / détox / perdez du poids » | refus immédiat (santé) |
| Affiche un faux compte à rebours | refus + risque DGCCRF |
| Cible « France » + intérêts « cuisine » | audience trop petite, CPM qui explose |
| Envoie le trafic vers `gumroad.com/l/airfryer` directement | tu perds toute la page de vente |

---

# 7. Le jour où la vente tombe

1. **Gumroad → Ventes** : vérifier que la commande est bien passée et que le client a reçu son email.
2. **Events Manager → Test Events / Aperçu** : `Purchase` doit apparaître. C'est **la** preuve que le pixel est actif.
3. **Créer l'audience de retargeting** (dès 1 vente, exploitable à 100 personnes) :
   `Events Manager → Audiences → Créer → Audience personnalisée → Site web → Événement Purchase → 180 jours`.
4. **Répondre au client sous 24 h** : demande-lui (gentiment) un avis. Premier avis réel = première preuve sociale.
5. **Ne change rien** avant d'avoir dépensé les 75 $. Ensuite seulement : passer à 25 $/jour si le CPA ≤ 5 $.

---

# 8. Après la première vente — le vrai sujet

À 2,97 €, Gumroad garde ~36 % : il te reste **1,90 € par vente**.
Un CPA de 75 $ sur la première vente est acceptable **une fois**. Il ne l'est pas deux fois.

**La rentabilité ne peut venir que de l'upsell à 19 €** (Gumroad Help 331 `Creating an Upsell`).
Sans lui, tu ne pourras jamais dépasser ~10 $/jour de budget, quel que soit le créatif.

À faire dès que tu as 3 ventes :
- créer le produit upsell 19 € (`france/GUMROAD-PUBLICATION.md` §7)
- le brancher **dans le tunnel** (`Content → Upsell`), pas sur `merci.html`
- objectif : 20 % d'acceptation ⇒ panier net moyen 5,07 € ⇒ CPA max 5,07 €

---

## Récapitulatif en une page

```
[ ] 1. Re-télécharger index.html (version à jour)       2 min
[ ] 2. Gumroad : devise -> EUR (2,97 €)                 3 min
[ ] 3. Gumroad : Description -> GARANTIE 14 jours       3 min
[ ] 4. Gumroad : Refund period -> 14 days               1 min
[ ] 5. Pixel ID dans index.html + Settings Gumroad      5 min
[ ] 6. Uploader la landing sur HostGator                5 min
[ ] 7. Vérifier les 4 PDF dans Content                  2 min
[ ] 8. Achat test avec code 100 %                       5 min
[ ] 9. Vérifier « Purchase » dans Events Manager        2 min
[ ] 10. Créer la campagne (Ventes, 15 $/j, FR 25-65 F)  10 min
[ ] 11. Publier et NE PLUS TOUCHER pendant 72 h
```

**Total : ~40 minutes. Puis 3 jours d'attente.**
