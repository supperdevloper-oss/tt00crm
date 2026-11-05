/* ==========================================================================
   Paraveda CRM — نسخة الموبايل (speciale pour les téléphones)
   ------------------------------------------------------------------
   هاد الكود كيتحط داخل index.html (قبل function __pvRepairStorage).
  IMPORTANT: الملف مبني بـ automatic runtime ديال React:
      s.jsx(type, props)  /  s.jsxs(type, props)   → children كاينة فـ props.children
      key كاينة فـ props (ماشي فالـ3rd argument)
   ========================================================================== */
function __pvMobileOn() {
  try {
    const v = localStorage.getItem("paraveda_mobile_mode");
    if (v === "1") return true;
    if (v === "0") return false;
  } catch (e) { }
  try {
    if (typeof __pvAdminMobile === "function" && __pvAdminMobile()) return true;
    if (typeof window !== "undefined" && window.innerWidth < 1024) return true;
  } catch (e) { }
  return false;
}
function __pvMobileToggle() {
  try { localStorage.setItem("paraveda_mobile_mode", __pvMobileOn() ? "0" : "1"); } catch (e) { }
  try { location.reload(); } catch (e) { }
}

function __PvMobileApp({ agent: e }) {
  const { orders: a, add: i, upd: c, publish: pubF } = Xt();
  const { currentUser: h, logout: lgOut } = kr();
  const cities = Ll() || [];
  const catalog = usePvCatalog() || [];
  const [tab, setTab] = ee.useState("suivi");
  const [q, setQ] = ee.useState("");
  const [kpi, setKpi] = ee.useState("call");
  const [period, setPeriod] = ee.useState("all");
  const [msg, setMsg] = ee.useState("");
  const [form, setForm] = ee.useState({ nom: "", telephone: "", ville: "", adresse: "", produit: "", qte: 1, prix: 0, commission: 35 });
  const today = __pvLocalDate(new Date());

  const mine = ee.useMemo(() => a.filter(o => o && !o._del && String(o.agent || "").toLowerCase() === String(e || "").toLowerCase()), [a, e]);
  const drafts = ee.useMemo(() => mine.filter(o => o._d), [mine]);
  const live = ee.useMemo(() => mine.filter(o => !o._d), [mine]);

  const inPeriod = ee.useMemo(() => {
    if (period === "today") return o => String(o.dateCreation || "") === today;
    if (period === "week") { const d = new Date(); d.setDate(d.getDate() - 7); const from = __pvLocalDate(d); return o => String(o.dateCreation || "") >= from; }
    if (period === "month") { const d = new Date(); d.setDate(1); const from = __pvLocalDate(d); return o => String(o.dateCreation || "") >= from; }
    return () => true;
  }, [period, today]);

  const follow = ee.useMemo(() => {
    const f = __pvKpiF(kpi) || (() => false);
    const needle = q.trim().toLowerCase();
    return live.filter(f).filter(o => inPeriod(o)).filter(o => !needle || [o.nom, o.telephone, o.ville, o.produit, o.remarques, o.tracking, o.statut].join(" ").toLowerCase().includes(needle));
  }, [live, kpi, q, inPeriod]);

  const list = ee.useMemo(() => {
    const needle = q.trim().toLowerCase();
    return live.filter(inPeriod).filter(o => !needle || [o.nom, o.telephone, o.ville, o.produit, o.adresse, o.remarques, o.statut, o.livraison, o.tracking].join(" ").toLowerCase().includes(needle));
  }, [live, q, inPeriod]);

  const stats = ee.useMemo(() => {
    const l = live.filter(inPeriod);
    const conf = l.filter(o => String(o.statut || "").trim() === "Confirmé");
    const sold = l.filter(o => __pvSold(o));
    const back = l.filter(o => __pvBack(o));
    const wait = l.filter(o => String(o.livraison || "").trim() === "" && String(o.statut || "").trim() === "Confirmé");
    const ca = l.reduce((s, o) => s + (Number(o.prix) || 0), 0);
    return { total: l.length, conf: conf.length, sold: sold.length, back: back.length, wait: wait.length, ca: ca, today: l.filter(o => String(o.dateCreation || "") === today).length };
  }, [live, inPeriod, today]);

  const pickVille = (v) => {
    const c0 = wo(v, cities);
    setForm(f => ({ ...f, ville: v, commission: c0 != null ? c0 : f.commission }));
  };

  // the product fills the selling price (like the catalogue of the desktop)
  const pickProduit = (p) => {
    const prod = catalog.find(x => String(x && x.nom || "").toLowerCase() === String(p || "").toLowerCase());
    const pr = prod ? Number(prod.prix != null ? prod.prix : (prod.price != null ? prod.price : prod.p)) : NaN;
    setForm(f => ({ ...f, produit: p, prix: !isNaN(pr) && pr > 0 ? pr : f.prix }));
  };

  const submit = () => {
    const v = form;
    if (!String(v.nom || "").trim()) { setMsg("❌ الاسم خاصو"); return; }
    if (!String(v.telephone || "").trim()) { setMsg("❌ الهاتف خاصو"); return; }
    if (!String(v.ville || "").trim()) { setMsg("❌ المدينة خاصها"); return; }
    const d = today;
    i({
      dateCreation: d, dateConfirmation: d, statut: "", remarques: "", idCmd: "1",
      nom: String(v.nom).trim(), telephone: String(v.telephone).trim(), ville: v.ville, adresse: String(v.adresse || "").trim(),
      qte: Math.max(1, Number(v.qte) || 1), prix: Number(v.prix) || 0, produit: String(v.produit || "").trim(),
      livraison: "", tracking: "", upsell: 0, carousell: "", agent: e, link: "", carosellFlag: "", originLead: "",
      commission: Number(v.commission) > 0 ? Number(v.commission) : 35, fees: "", _d: 1
    });
    setForm({ nom: "", telephone: "", ville: v.ville, adresse: "", produit: v.produit, qte: 1, prix: v.prix, commission: v.commission });
    setMsg("✅ تحفظت. بعتها للأدمين من «المسودات».");
    setTab("drafts");
  };

  const publishAll = () => {
    if (!drafts.length) return;
    const ids = new Set(drafts.map(o => o.id));
    const n = pubF(ids);
    setMsg(n ? ("✅ بعثنا " + n + " طلبية للأدمين") : "❌ ما بعثناش");
  };

  const chip = (txt, kind, k) => s.jsx("span", { key: k || txt, className: "mv-chip " + (kind || ""), children: txt });

  const card = (o) => {
    const st = String(o.statut || "").trim();
    const liv = String(o.livraison || "").trim();
    const tel = String(o.telephone || "").replace(/\s+/g, "");
    return s.jsxs("div", { key: o.id, className: "mv-card", children: [
      s.jsxs("div", { key: "h", className: "mv-head", children: [
        s.jsx("b", { key: "n", className: "mv-name", children: o.nom || "(بلا اسم)" }),
        s.jsx("span", { key: "p", className: "mv-price", children: (Number(o.prix) || 0) + " DH" })
      ]}),
      s.jsxs("div", { key: "l", className: "mv-line", children: [
        s.jsx("span", { key: "t", children: "📞 " + (o.telephone || "—") }),
        s.jsx("span", { key: "v", children: "📍 " + (o.ville || "—") }),
        o.dateCreation ? s.jsx("span", { key: "dt", children: "🗓️ " + o.dateCreation }) : null,
        Number(o.qte) > 1 ? s.jsx("span", { key: "q", children: "×" + o.qte }) : null
      ]}),
      (o.produit || o.tracking || o.adresse) ? s.jsxs("div", { key: "d", className: "mv-line dim", children: [
        o.produit ? s.jsx("span", { key: "pr", children: "📦 " + o.produit }) : null,
        o.adresse ? s.jsx("span", { key: "ad", children: "🏠 " + o.adresse }) : null,
        o.tracking ? s.jsx("span", { key: "tr", className: "mv-track", children: "Tracking " + o.tracking }) : null
      ]}) : null,
      s.jsxs("div", { key: "c", className: "mv-chips", children: [
        chip(st || "جديد", st === "Confirmé" ? "ok" : (st === "Annulé" ? "bad" : ""), "s"),
        liv ? chip(liv, "gray", "l") : null,
        o._d ? chip("مسودة", "draft", "d") : null
      ]}),
      s.jsxs("div", { key: "a", className: "mv-actions", children: [
        tel ? s.jsx("a", { key: "call", href: "tel:" + tel, className: "mv-btn call", children: "📞 اتصال" }) : null,
        s.jsx("button", { key: "ok", onClick: () => c(o.id, { statut: "Confirmé" }), className: "mv-btn ok", children: "✅ تأكيد" }),
        s.jsx("button", { key: "rl", onClick: () => c(o.id, { statut: "Rappel" }), className: "mv-btn", children: "⏰ رappel" }),
        s.jsx("button", {
          key: "no",
          onClick: () => { if (window.confirm("نلغيو هاد الطلبية؟")) c(o.id, { statut: "Annulé" }); },
          className: "mv-btn danger", children: "✖ إلغاء"
        })
      ]})
    ]});
  };

  const navBtn = (key, icon, label, badge) => s.jsxs("button", {
    onClick: () => setTab(key),
    key: key, className: "mv-nav-btn" + (tab === key ? " on" : ""),
    children: [s.jsx("span", { key: "i", className: "mv-nav-ic", children: icon }), s.jsx("span", { key: "l", children: label }), badge ? s.jsx("span", { key: "b", className: "mv-badge", children: badge }) : null]
  });

  const periodBtn = (key, label) => s.jsx("button", {
    key: key, onClick: () => setPeriod(key),
    className: "mv-seg" + (period === key ? " on" : ""), children: label
  });

  const kpiChip = (key, label) => s.jsx("button", {
    key: key, onClick: () => setKpi(key),
    className: "mv-seg" + (kpi === key ? " on" : ""), children: label
  });

  let body = null;
  if (tab === "suivi") {
    body = s.jsxs("div", { key: "bd", className: "mv-body", children: [
      s.jsxs("div", { key: "k", className: "mv-segs", children: [
        kpiChip("call", "📞 للاتصال"),
        kpiChip("suivi", "⏰ متابعة"),
        kpiChip("ship", "🚚 جاهزة"),
        kpiChip("risk", "⚠️ خطر")
      ]}),
      s.jsxs("div", { key: "p", className: "mv-segs", children: [periodBtn("today", "اليوم"), periodBtn("week", "7 أيام"), periodBtn("month", "هاد الشهر"), periodBtn("all", "الكل")] }),
      follow.length ? follow.map(card) : s.jsx("div", { key: "e", className: "mv-empty", children: "ما كاين حتى طلبية فهاد القائمة ✅" })
    ]});
  } else if (tab === "orders") {
    body = s.jsxs("div", { key: "bd", className: "mv-body", children: [
      s.jsxs("div", { key: "p", className: "mv-segs", children: [periodBtn("today", "اليوم"), periodBtn("week", "7 أيام"), periodBtn("month", "هاد الشهر"), periodBtn("all", "الكل")] }),
      list.length ? list.map(card) : s.jsx("div", { key: "e", className: "mv-empty", children: "ما كاين حتى طلبية" })
    ]});
  } else if (tab === "new") {
    const f = form;
    const set = (k) => (ev) => setForm(x => ({ ...x, [k]: ev.target.value }));
    body = s.jsxs("div", { key: "bd", className: "mv-body", children: [
      s.jsx("label", { key: "l1", className: "mv-lbl", children: "الاسم الكامل" }),
      s.jsx("input", { key: "i1", className: "mv-in", value: f.nom, onChange: set("nom"), placeholder: "مثال: فاطمة الزهراء", autoComplete: "name" }),
      s.jsx("label", { key: "l2", className: "mv-lbl", children: "الهاتف" }),
      s.jsx("input", { key: "i2", className: "mv-in", value: f.telephone, onChange: set("telephone"), placeholder: "06XXXXXXXX", inputMode: "tel", autoComplete: "tel", dir: "ltr" }),
      s.jsx("label", { key: "l3", className: "mv-lbl", children: "المدينة" }),
      s.jsx("select", {
        key: "i3", className: "mv-in", value: f.ville, onChange: ev => pickVille(ev.target.value),
        children: [s.jsx("option", { key: "o0", value: "", children: "اختار المدينة…" })].concat(cities.map(c2 => s.jsx("option", { key: c2.nom, value: c2.nom, children: c2.nom + " — " + c2.prix + " DH" })))
      }),
      s.jsx("div", { key: "l3h", className: "mv-hint", children: "ثمن التوصيل: " + (Number(f.commission) > 0 ? Number(f.commission) + " DH" : "—") }),
      s.jsx("label", { key: "l4", className: "mv-lbl", children: "العنوان" }),
      s.jsx("input", { key: "i4", className: "mv-in", value: f.adresse, onChange: set("adresse"), placeholder: "الحي، الزنقة…" }),
      s.jsx("label", { key: "l5", className: "mv-lbl", children: "المنتج" }),
      s.jsx(Pk, { key: "i5", value: f.produit, list: catalog, onChange: pickProduit, className: "mv-in" }),
      s.jsxs("div", { key: "c2", className: "mv-2col", children: [
        s.jsxs("div", { key: "cq", children: [s.jsx("label", { key: "lq", className: "mv-lbl", children: "الكمية" }), s.jsx("input", { key: "iq", className: "mv-in", value: f.qte, onChange: set("qte"), inputMode: "numeric", type: "number", min: 1 })] }),
        s.jsxs("div", { key: "cp", children: [s.jsx("label", { key: "lp", className: "mv-lbl", children: "الثمن (DH)" }), s.jsx("input", { key: "ip", className: "mv-in", value: f.prix, onChange: set("prix"), inputMode: "numeric", type: "number", min: 0 })] })
      ]}),
      s.jsx("button", { key: "sub", onClick: submit, className: "mv-submit", children: "💾 حفظ الطلبية" })
    ]});
  } else if (tab === "drafts") {
    body = s.jsxs("div", { key: "bd", className: "mv-body", children: [
      drafts.length ? s.jsx("button", { key: "pub", onClick: publishAll, className: "mv-submit", children: "📤 بعت " + drafts.length + " طلبية للأدمين" }) : null,
      drafts.length ? drafts.map(card) : s.jsx("div", { key: "e", className: "mv-empty", children: "ما كاين حتى مسودة" })
    ]});
  } else {
    body = s.jsxs("div", { key: "bd", className: "mv-body", children: [
      s.jsxs("div", { key: "st", className: "mv-stats", children: [
        s.jsxs("div", { key: "s1", className: "mv-stat", children: [s.jsx("b", { key: "v", children: String(stats.total) }), s.jsx("span", { key: "t", children: "طلبيات" })] }),
        s.jsxs("div", { key: "s2", className: "mv-stat", children: [s.jsx("b", { key: "v", children: String(stats.today) }), s.jsx("span", { key: "t", children: "اليوم" })] }),
        s.jsxs("div", { key: "s3", className: "mv-stat", children: [s.jsx("b", { key: "v", children: String(stats.conf) }), s.jsx("span", { key: "t", children: "مؤكدة" })] }),
        s.jsxs("div", { key: "s4", className: "mv-stat", children: [s.jsx("b", { key: "v", children: String(stats.wait) }), s.jsx("span", { key: "t", children: "بانتظار الإرسال" })] }),
        s.jsxs("div", { key: "s5", className: "mv-stat", children: [s.jsx("b", { key: "v", children: String(stats.sold) }), s.jsx("span", { key: "t", children: "مسلّمة" })] }),
        s.jsxs("div", { key: "s6", className: "mv-stat", children: [s.jsx("b", { key: "v", children: String(stats.back) }), s.jsx("span", { key: "t", children: "مرجّعة" })] })
      ]}),
      s.jsxs("div", { key: "ca", className: "mv-card", children: [s.jsxs("div", { key: "h", className: "mv-head", children: [s.jsx("b", { key: "b", children: "المبيعات" }), s.jsx("span", { key: "p", className: "mv-price", children: j2(Math.round(stats.ca)) + " DH" })] })] }),
      s.jsx("div", { key: "me", className: "mv-empty", children: "الحساب ديالك: " + (h ? (h.username + " · " + (h.agent || "")) : "") })
    ]});
  }

  return s.jsxs("div", { className: "mv-root", dir: "rtl", children: [
    s.jsxs("header", { key: "hd", className: "mv-head-bar", children: [
      s.jsxs("div", { key: "hl", className: "mv-head-l", children: [
        s.jsx("b", { key: "u", children: (h && h.username) || e || "" }),
        s.jsx("span", { key: "ag", className: "mv-head-sub", children: e || "" })
      ]}),
      s.jsxs("div", { key: "hr", className: "mv-head-r", children: [
        s.jsx("button", { key: "tb", onClick: __pvMobileToggle, className: "mv-hbtn", title: "النسخة ديال الجدول", children: "🖥️" }),
        s.jsx("button", { key: "lo", onClick: () => lgOut && lgOut(), className: "mv-hbtn", title: "تسجيل الخروج", children: "⏻" })
      ]})
    ]}),
    s.jsx("div", { key: "sr", className: "mv-search", children: [
      s.jsx("input", { key: "si", className: "mv-in", value: q, onChange: ev => setQ(ev.target.value), placeholder: "🔎 بحث (الاسم، الهاتف، المدينة…)" })
    ]}),
    msg ? s.jsx("div", { key: "mg", className: "mv-msg", children: msg }) : null,
    body,
    tab !== "new" ? s.jsx("button", { key: "fab", onClick: () => setTab("new"), className: "mv-fab", title: "طلبية جديدة", children: "+" }) : null,
    s.jsxs("nav", { key: "nv", className: "mv-nav", children: [
      navBtn("suivi", "📞", "التبّع", follow.length ? String(follow.length) : ""),
      navBtn("orders", "📦", "الطلبيات"),
      navBtn("new", "➕", "جديد"),
      navBtn("drafts", "📤", "المسودات", drafts.length ? String(drafts.length) : ""),
      navBtn("stats", "📊", "الأرقام")
    ]})
  ]});
}
