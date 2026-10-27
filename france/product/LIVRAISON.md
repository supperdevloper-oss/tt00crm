# 📦 التسليم — شنو كايوصل للمشتري وكيفاش

هاد الملف هو الجسر بين المنتج (الصفحات اللي بناها `build-pdf.py`) وGumroad.
خد 20 دقيقة وكمّل الخطوات بالترتيب، ومن بعد كلشي كايوصل بوحدو.

---

## 1. شنو غادي تسلّم (4 ملفات)

| # | الملف | الصفحات | الحجم | الوصف فـGumroad |
|---|---|---|---|---|
| 1 | `365-recettes-friteuse-a-air.pdf` | 146 | ~5,2 Mo | Guide complet — 365 recettes |
| 2 | `bonus/1-tableau-temps-et-temperatures.pdf` | 3 | 59 Ko | Bonus 1 — Tableau à imprimer |
| 3 | `bonus/2-menus-4-semaines.pdf` | 4 | 55 Ko | Bonus 2 — 4 semaines de menus |
| 4 | `bonus/3-50-desserts.pdf` | 18 | 122 Ko | Bonus 3 — 50 desserts |

**القاعدة الذهبية:** 4 ملفات منفصلة، ماشي ZIP. الزبون كيحس بالقيمة أكثر، وGumroad كيعرضهم
واحد بواحد فالإيميل. (إلا بغيت ZIP، ديرو كـ«content» إضافي — ماتبدلش الفرديين.)

---

## 2. رفع المنتج فـGumroad (أول مرة)

1. **gumroad.com** → Sign up (بالإيميل، بلا كارت بنكي).
2. **Settings → Payments** → **Sell in… = EUR**. (Gumroad كيصفي الحساب فـUSD فالآخر،
   ولكن الزبون الفرنسي كيشوف ويخلّص **بالأورو**.)
   ⚠️ عملة العرض كتتقرر **وقت إنشاء المنتج** وما تقدرش تبدّلها من بعد — إلا غلطت، عاود صاوب المنتج.
3. **Products → New product** → **Digital product**.
4. **Name**: `365 Recettes pour Friteuse à Air — Le guide pratique`
5. **Price**: `9` → الزبون كيشوف **9,00 €** بالضبط، بحال اللاندينغ. (ما تديرش 9.99.)

   > **إلا كان الحساب ديالك ديجا USD** (ما تقدرش تبدّل): دير **`9.99`** — Gumroad كيحافظ على
   > النهاية ديال الثمن، فالزبون كيشوف **8,99 €** ماشي 8,53 €. و**`10`** كيعطي **9,00 €** بالضبط.
   > الجوج مقبولين؛ 9.99 كيبيع أحسن فالسيكولوجي.

   **الحساب الصافي** (9 €): 10 % (0,90 €) + 0,50 $ (≈0,46 €) + 2,9 % (0,26 €) + 0,30 $ (≈0,28 €)
   ≈ **1,90 € → صافي ≈ 7,10 €**. بهاد السبب **CPA ≤ 6,80 €** هو الخط الأحمر.
6. **Description** (كوبي/پاست):

```
365 recettes testées pour votre friteuse à air, avec le temps et la température exacts.

Le guide de 146 pages :
• 9 chapitres — viandes, poissons, légumes, entrées, plats complets, petit-déjeuner, desserts, cuisine du monde, surgelés
• pour chaque recette : portions, temps, température, ingrédients, étapes numérotées, une astuce
• un tableau temps & températures de 42 aliments
• un index par ingrédient pour cuisiner avec ce que vous avez déjà
• 4 semaines de menus et 28 dîners déjà choisis

+ 3 bonus offerts :
1. Le tableau temps & températures à imprimer
2. 4 semaines de menus avec les listes de courses
3. 50 desserts à la friteuse

PDF téléchargeable immédiatement. Garantie 14 jours, sans justification.
```

7. **Content** → حمّل الأربعة ملفات (سمّيهم بالأسماء اللي فوق بالضبط).
8. **Cover** → حمّل `assets/img/book/gumroad-cover.jpg` (1280×720، جاهزة).
   **Thumbnail** → `assets/img/book/gumroad-thumb.jpg` (600×600).
   **Galerie** (3-4 صور): `assets/img/book/apercu-1.jpg` … `apercu-4.jpg`
   (الفهرس، صفحة وصفة، جدول الحرارة، الـ4 أسابيع). هادو هوما اللي كيبيعو، ماشي الغلاف.
   باش تعاود تبنييهم: `python3 product/tools/make-covers.py` و `make-previews.py`.
9. **Settings** ديال المنتج:
   - ✅ **Generate license keys** — ماشي ضروري، خليه مطفي.
   - ✅ **Allow customers to pay what they want** — مطفي (كاتقتل الثمن).
   - ❌ **Discover** — طفي «Eligible for Gumroad Discover» فالإطلاق (30 % عمولة).
   - ✅ **Receipt** → زيد رسالة شكر قصيرة (جملة وحدة فيها «Répondez à cet email si…»).
10. **Publish**.

**الرابط ديالك** غادي يكون: `https://اسمك.gumroad.com/l/xxxxx`
حطو فـ`index.html` → `CONFIG.checkout` مع `?wanted=true` فالآخر.

---

## 3. الثمن والعملة — الحقيقة اللي كتفرق

- Gumroad كتخلّص **بالدولار**، والزبون كيشوف الثمن بالأورو (Gumroad كتحوّل أوتوماتيكياً).
- الثمن 9 $ ≈ 8,30 € عند الزبون. إلا بغيت الزبون يشوف **8,99 €** بالضبط، حط الثمن `9.99 $`.
- **TVA**: Gumroad هي Merchant of Record → كتجمعها وكتخلّصها هي. **ماعندكش دوشي مع TVA فرنسية.**

> 💡 باش الثمن اللي فالصفحة (9 €) يبقى صحيح: حط المنتج بـ**9.99 $** فـGumroad
> ولا بدّل `CONFIG.price` فـ`index.html` لـ`8,99`.

---

## 4. إيميل التسليم

Gumroad كاتصيفط الفاتورة + الروابط أوتوماتيكياً. **ولكن** الإيميل كيجي بارد وحده.

الطريقة اللي كتزيد الثقة وكتنقص الاسترجاع: بيعة كتوصلك إشعار → كتصيفط إيميل شخصي
(دقيقة وحدة) بالقالب اللي فـ`emails/01-livraison.md`.

إلا بغيت أوتوماتيكي 100 %: Gumroad → **Workflows** → New workflow → *Purchase* →
إيميل فيه «Merci, voici comment commencer» + رابط `gumroad.com/library`.

---

## 5. بعد ما تنشر — 6 تشيكات (5 دقايق)

- [ ] حمّلت المنتج براسك بكوبون 100 % → الأربعة ملفات كايتحمّلو
- [ ] الـPDF كيتفتح فـiPhone (Preview) وفـAndroid (Drive) — بلا خطوط مقطوعة
- [ ] صفحة Gumroad على الموبايل: الثمن باين، زر الشراء باين
- [ ] `index.html` كايحوّل لـGumroad بـ`?wanted=true` (تشيك فـURL بعد الكليك)
- [ ] إيميل الفاتورة وصل (شوف فـSpam)
- [ ] `Purchase` بان فـEvents Manager (شوف `../tracking/pixel-gumroad.md`)

---

## 6. تحديث المنتج بعد البيع

عندك الحق تبدل الملفات فأي وقت: **Product → Content → Replace**. الزبون القديم
كياخد النسخة الجديدة إلى عاود حمّل من `gumroad.com/library`.

نسخة 1.1 (مثلاً زدت 30 وصفة):
1. بدّل `product/data/*.txt`
2. `python3 product/build-pdf.py`
3. Replace الملف فـGumroad
4. صيفط إيميل «mise à jour gratuite» للمشترين — هادي كتنقص الاسترجاع بزاف.
