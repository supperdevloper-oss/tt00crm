# 🟢 FICHE DE PUBLICATION GUMROAD — 365 Recettes pour Friteuse à Air

> **الهدف:** كل شي كتحتاجو باش تنشر المنتج فـGumroad، فبلاصة وحدة.
> كل بلوك فيه «كوبي/پاست» — ما كتكتبش حتى شي حرف بالفرنسية بيدك.
> **الوقت:** 20–25 دقيقة كاملة.

---

## 1. المعلومات الأساسية (نسخ/لصق)

| الخانة فـGumroad | القيمة |
|---|---|
| **Name** | `365 Recettes pour Friteuse à Air — Le guide pratique` |
| **Type** | Digital product → **PDF** |
| **Price** | `2.97` (بالنقطة، ماشي الفاصلة) |
| **Currency** | **EUR** (كنشوفها وقت إنشاء المنتج — ما تقدرش تبدّلها من بعد) |
| **Quantity** | Unlimited |
| **URL / permalink** | `365-recettes-friteuse-air` → كتولي `https://اسمك.gumroad.com/l/365-recettes-friteuse-air` |
| **Summary (سطر واحد)** | `365 recettes testées, avec le temps et la température exacts. PDF 146 pages + 3 bonus.` |
| **Discover** | ❌ **OFF** (30 % عمولة) |
| **Pay what you want** | ❌ OFF (كاتقتل الثمن) |
| **License keys** | ❌ OFF (ماشي محتاجينها) |

---

## 2. الأربعة ملفات اللي كتحمّل (Content)

حمّلهم **بالترتيب** وسمّيهم بحال ما هوما مسميين — الزبون غادي يشوف هاد الأسماء:

| # | الملف | الحجم | الصفحات |
|---|---|---|---|
| 1 | `365-recettes-friteuse-a-air.pdf` | 5,2 MB | 146 |
| 2 | `1-tableau-temps-et-temperatures.pdf` | 59 KB | 3 |
| 3 | `2-menus-4-semaines.pdf` | 56 KB | 4 |
| 4 | `3-50-desserts.pdf` | 122 KB | 18 |

📁 كاينين فـ: `france/product/` و `france/product/bonus/`

> **ماتديرش ZIP.** Gumroad كيقبل 4 ملفات فمنتج واحد، وكل واحد كيتحمّل بوحدو —
> هادشي كيبيّن «قيمة أكبر» وكينقص الاسترجاع.

---

## 3. الوصف (Description) — كوبي/پاست

```
365 recettes testées pour votre friteuse à air, avec le temps et la température exacts.

LE GUIDE — 146 pages
• 9 chapitres : viandes, poissons, légumes, entrées, plats complets, petit-déjeuner, desserts, cuisine du monde, surgelés
• pour chaque recette : portions, temps, température, ingrédients, étapes numérotées et une astuce
• un tableau temps & températures de 42 aliments
• un index par ingrédient : cuisinez avec ce que vous avez déjà dans le frigo
• 4 semaines de menus et 28 dîners déjà choisis

+ 3 BONUS OFFERTS
1. Le tableau temps & températures à imprimer (3 pages)
2. 4 semaines de menus avec les listes de courses (4 pages)
3. 50 desserts à la friteuse (18 pages)

COMMENT ÇA MARCHE
Après le paiement, vous recevez un email avec tous les fichiers. Téléchargement immédiat,
à vie. Lisible sur téléphone, tablette et ordinateur. Imprimable si vous préférez le papier.

GARANTIE
14 jours. Si le guide ne vous sert pas, répondez à l'email de confirmation : remboursement,
sans justification.

Ce n'est pas un livre papier : ce sont des fichiers PDF.
```

---

## 4. الـCover والصور (الـ7 صور)

حمّلهم فهاد الترتيب — **Gumroad كيبيّن غير 3-4 الأولين** فالمعرض:

| الترتيب | الملف | الاستعمال | القياس |
|---|---|---|---|
| **1** | `assets/img/book/gumroad-cover.jpg` | **Cover** (بانر الفوق) | 1280×720 |
| **2** | `assets/img/book/gumroad-thumb.jpg` | **Thumbnail** | 600×600 |
| **3** | `assets/img/book/apercu-1.jpg` | Sommaire | 1400×2089 |
| **4** | `assets/img/book/apercu-2.jpg` | Une fiche recette | 1400×2089 |
| **5** | `assets/img/book/apercu-3.jpg` | Tableau T° | 1400×2089 |
| **6** | `assets/img/book/apercu-4.jpg` | 4 semaines de menus | 1400×2089 |
| **7** | `assets/img/book/mockup-livre.png` | الموك أب (اختياري) | 1252×1611 |

> 🔴 **الأهم**: الصور 3 → 6 (داخل الكتاب) هوما اللي كيبيعو. الغلاف وحدو ما كيبيعش.
> الزبون كيخلّص 2,97 € على «شنو غادي ياخذ»، ماشي على غلاف زوين.

**باش تعاود تبنييهم** (إلا بدّلت شي حاجة فالكتاب):
```bash
python3 product/tools/make-covers.py      # cover + thumbnail
python3 product/tools/make-previews.py    # الـ4 معاينات
python3 product/tools/make-mockup.py      # الموك أب
```

---

## 5. الرابط والربط باللاندينغ

كياخذ الرابط من Gumroad: `https://اسمك.gumroad.com/l/365-recettes-friteuse-air`

دير هاد التعديل فـ`france/index.html` (السطر ~605):

```js
checkout : "https://اسمك.gumroad.com/l/365-recettes-friteuse-air?wanted=true",
```

> `?wanted=true` كيحل الـcheckout ديريكت — كليك واحدة أقل = بيوع أكثر.
> الكود كيزيد بوحدو `referrer=...` و`utm_*` باش تعرف منين جات البيعة.

---

## 6. الإيميل اللي كيمشي للزبون (Receipt message)

Gumroad → Settings → **Receipt** → «Message to buyers»:

```
Merci pour votre achat !

Vos 4 fichiers sont juste au-dessus : le guide de 146 pages et les 3 bonus.
Commencez par la page 4 (« 12 règles d'or ») — c'est 5 minutes et ça change tout.

Un souci ? Répondez directement à cet email, je réponds personnellement.
```

---

## 7. الأبسيل 19 € — 🔴 هذا اللي كيخلّص الإعلانات

بـ2,97 €، Gumroad كتاخذ **36 %** (1,07 €). الفايدة الحقيقية كتجي من الأبسيل:

| المنتج | الثمن | صافي ليك |
|---|---|---|
| الكتاب | 2,97 € | **1,90 €** |
| الأبسيل (باكيت الطباعة / الفيديوهات) | 19 € | **15,86 €** |

**كيفاش تديرو:** Gumroad → المنتج → **Sections** → زيد section جديد سميه
«Le pack complet» بـ19 €، وحطو **بعد** المنتج الأساسي (post-purchase offer).
إلا حطيت غير لينك فـ`merci.html`، غادي يجيك 5–10 % برك. داخل الـcheckout كيوصل 20–30 %.

---

## 8. تشيك قبل ما تنشر (6 نقط)

- [ ] الثمن `2.97` و**العملة EUR** — والثمن فاللاندينغ `CONFIG.price` = نفسو
- [ ] **4 ملفات** مرفوعين، كلهم كيتحمّلو (جرّب بكوبون 100 % على حسابك)
- [ ] الـPDF كيتفتح فـiPhone (Preview) وفـAndroid (Drive) — الخطوط سليمة
- [ ] صفحة Gumroad فالموبايل: الثمن باين، زر الشراء باين
- [ ] **Discover طافي**
- [ ] `CONFIG.checkout` فاللاندينغ فيها الرابط الحقيقي + `?wanted=true`

---

## 9. بعد النشر — شنو كتراقب

| المؤشر | الهدف | إلا كان خايب |
|---|---|---|
| CTR ديال الإعلان | ≥ 1,5 % | بدّل الكرياتيف |
| landing → checkout | ≥ 8 % | مشكل فالصفحة / الثمن |
| checkout → بيعة | ≥ 30 % | مشكل فالثقة / الدفع |
| **taux d'upsell** | **≥ 20 %** | هادي اللي كتقرر كلشي |
| CPA | ≤ panier moyen net | كتخسر |

📖 التفاصيل: `ads/plan-14-jours-150usd.md` · التتبع: `tracking/pixel-gumroad.md`

---

## 10. إيميلات ما بعد الشراء

كاينين 5 إيميلات واجدين فـ`france/emails/`:
`01-livraison` · `02-j+1` · `03-j+3` · `04-winback-14j` · `05-refund`

الطريقة السهلة: Gumroad → **Workflows** → New workflow → *Purchase* → الصق النص.
