# Tracking — Pixel Meta + CAPI + attribution Gumroad

> الهدف من هاد الملف: Meta تعرف **أشمن إعلان جاب البيعة**، ماشي غير الكليكات.
> بلا هادشي، Advantage+ غادي يبقى يعمى ويصرف الـ150 $ بلا نتيجة.

---

## 0. الخريطة — فين كايتنقل المشتري

```
facebook.com (إعلان)
   ↓  utm_* + fbclid
لاندينغ (votredomaine.fr/index.html)     ← هنا كاين البيكسل ديالك
   ↓  زر «Je veux mes 365 recettes»
Gumroad checkout                         ← هنا كاين البيكسل الثاني (نفس ID)
   ↓  wanted=true → مباشرة للدفع
Gumroad /library + إيميل الفاتورة
```

**المهم:** البيكسل واحد (نفس الـID) فهاد الجوج من الأماكن. فـMeta غادي تشوف الحدث مرتين إلا مادرتيش الحساب — شوف §4.

---

## 1. أحداث لازم يكونو

| الحدث | فين كايتصيفط | علاش |
|---|---|---|
| `PageView` | لاندينغ (ديالك) | أساسي |
| `ViewContent` | لاندينغ | باش تبني جمهور مشاهدين |
| `InitiateCheckout` | كليك على زر CTA (ديالك) | **أهم حدث وسيط** — كايتصيفط قبل ما يفتح Gumroad |
| `Purchase` | **Gumroad** (Third-party analytics) | البيعة الحقيقية + القيمة + العملة |

⚠️ **ماتحاولش تصيفط `Purchase` من لاندينغ.** ماكاينش عندك معلومات الدفع، وغادي تكذب على الخوارزمية.

---

## 2. البيكسل فـلاندينغ (5 دقايق)

1. Meta Events Manager → **Data sources** → **Connect data** → **Web** → سمّيه `LP 365 Friteuse`.
2. خد **Pixel ID** (رقم 15/16 رقم).
3. فـ`index.html` قلّب على `TODO-PIXEL` → حط الـID وحلّ الكومونتير.
4. زيد الحدثين اللي كاينين فـ`index.html` (كاينين ديجا فالكود، غير تأكد):
   - فـ`<head>`: `fbq('track','ViewContent',{content_name:'365 recettes',value:9.00,currency:'EUR'})`
   - فـكليك الـCTA: `fbq('track','InitiateCheckout',{value:9.00,currency:'EUR'})`
5. **Meta Pixel Helper** (إضافة Chrome) → حل لصفحتك → خاصك تشوف: `PageView` + `ViewContent` = أخضر.

---

## 3. `Purchase` من Gumroad (هاد الخطوة هي اللي كاتهم)

Gumroad ماعندهاش Conversions API ديال Meta، ولكن عندها بيكسل طرف أول:

1. Gumroad → **Settings** → **Advanced** → **Third-party analytics**
2. حط **نفس Pixel ID** فخانة **Facebook Pixel**
3. Save.
4. الخريطة الرسمية بين Gumroad و Meta:

   | حدث Gumroad | حدث Meta |
   |---|---|
   | `viewed` | `ViewContent` |
   | `iwantthis` | `InitiateCheckout` |
   | `purchased` | `Purchase` (بالقيمة + العملة) |

5. الـstatus غادي يبقى **Unverified** حتى يدوز شي واحد من رابط فيسبوك ويشري. دير **بيعة اختبار** (كوبون 100% + رابط فيه `?wanted=true`) باش يتحقق.

> 🔴 Gumroad كايصيفط `Purchase` بالدولار (`USD`) إلا كان الحساب ديالك بالدولار. باش مايتخلطش الحساب فـMeta، خلي `currency` ديال الإعلان = `EUR` غير فـلاندينغ، وماتقارنش القيمة — قارن **عدد البيوع**.

---

## 4. متى كايتضاعف العدّ (وكيفاش توقفو)

كاين جوج حالات:

| الحالة | النتيجة | الحل |
|---|---|---|
| البيكسل فـلاندينغ + Gumroad | `Purchase` كايتصيفط مرة واحدة (لاندينغ ماكاتصيفطش Purchase) | ✅ ماشي مشكل |
| زدت `Purchase` فـ`merci.html` **و** فـGumroad | بيعة محسوبة 2× | ❌ حيّد واحد منهم (خلي Gumroad) |
| CAPI (شوف §5) + Gumroad | 2× إلا ماكانش `event_id` | استعمل `sale_id` كـ`event_id` فالجوج |

**القاعدة:** `Purchase` = مصدر واحد فقط. هو Gumroad.

---

## 5. CAPI (اختياري — غير إلا بغيت دقة عالية)

Gumroad عندها **Ping**: كاتصيفط `POST` لأي URL عندك مع كل بيعة (فيها `sale_id`, `price`, `email`, `product_permalink`).

```
Gumroad → Settings → Advanced → «Ping» → https://hook.make.com/xxxx
   ↓
Make/Zapier → HTTP → graph.facebook.com/v20.0/{PIXEL_ID}/events?access_token=...
```

Payload مبسط:

```json
{
  "data": [{
    "event_name": "Purchase",
    "event_time": 1761600000,
    "event_id": "gumroad_{{sale_id}}",
    "action_source": "website",
    "user_data": { "em": ["{{sha256(lowercase(email))}}"], "fbp": "{{fbp}}" },
    "custom_data": { "value": 9.00, "currency": "EUR", "content_ids": ["365-recettes"] }
  }]
}
```

⚠️ للأسبوعين الأولين ماتحتاجش CAPI. 9 € × 20-30 بيعة = داتا قليلة، وGumroad كافي. CAPI بعد ما توصل 50 بيعة.

---

## 6. UTM — القاعدة الذاتية

كل إعلان عندو UTM خاص بيه. البنية:

```
?utm_source=facebook
&utm_medium=paid
&utm_campaign=fr_365_j1-14
&utm_content={{ad.name}}        ← فـMeta: Dynamic Parameter
&utm_term={{adset.name}}
```

فـMeta: فـ**URL Parameters** ديال الإعلان حط:

```
utm_source=facebook&utm_medium=paid&utm_campaign=fr_365_j1-14&utm_content={{ad.name}}
```

**فين تشوفها فـGumroad:** Sales → كل بيعة عندها **Referrer**. اللاندينغ كاتصيفط `referrer=facebook_paid_<campaign>`، فغادي تشوفها ديك الساعة.

**فين تشوفها فـMeta:** Events Manager → Breakdown → **Campaign name / Ad name** (هادشي كايجي من البيكسل، ماشي من الـUTM).

---

## 7. الأرقام اللي كاتقيس (كل 48 ساعة)

| المؤشر | من فين | الهدف | إلا خرج على هادشي |
|---|---|---|---|
| CTR | Meta | ≥ 1,5 % | < 0,8 % بعد 1 000 ظهور → وقّف الكرياتيف |
| CPC | Meta | 0,20–0,45 € | > 0,80 € → غيّر الـhook |
| LP → Gumroad (CTA clicks) | Meta `InitiateCheckout` ÷ `Link clicks` | ≥ 8 % | < 4 % → مشكل فالصفحة |
| Gumroad → sale | Gumroad sales ÷ InitiateCheckout | ≥ 30 % | < 15 % → مشكل فالثمن ولا فالثقة |
| CPA | Spend ÷ Sales | < 4 € | 4–7 € = مقبول فالأسبوع الأول، فوق 7 € = خسارة |

**الحساب الحقيقي:** كل بيعة 9 € كاتخليك ~7,15 € صافي (شوف `../README.md`). إذن **CPA فوق 7 € = كاتخسر**.

---

## 8. Checklist قبل ما تشعل الإعلان

- [ ] Pixel ID فـ`index.html` (وحلّ الكومونتير)
- [ ] `ViewContent` + `InitiateCheckout` كايبانو فـPixel Helper
- [ ] نفس Pixel ID فـGumroad → Settings → Advanced
- [ ] بيعة اختبار (كوبون 100%) → `Purchase` بان فـEvents Manager
- [ ] `merci.html` **بلا** `Purchase` مكرر
- [ ] UTM Parameters محطوطين فـMeta Ads
- [ ] Business Manager فيه الدومين متحقق (Domain verification)
- [ ] Aggregated Event Measurement: `Purchase` فوق، `InitiateCheckout` تحتو
- [ ] Landing فـHTTPS
