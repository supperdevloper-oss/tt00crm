/* ==========================================================================
   Paraveda CRM — نسخة الموبايل الاحترافية (v4.01)
   ------------------------------------------------------------------
   هاد الكود كيتحط داخل index.html (قبل function __pvRepairStorage).
   IMPORTANT: الملف مبني بـ automatic runtime ديال React:
      s.jsx(type, props)  /  s.jsxs(type, props)   → children كاينة فـ props.children
      key كاينة فـ props (ماشي فالـ3rd argument)
   ========================================================================== */

/* --- تفعيل/تعطيل نسخة الموبايل ---------------------------------------- */
function __pvMobileQuery() {
  try {
    const s = (typeof location !== "undefined" && location.search) || "";
    const m = /[?&]mobile=([^&#]*)/.exec(s);
    return m ? decodeURIComponent(m[1] || "") : "";
  } catch (e) { return ""; }
}
function __pvMobileSmallScreen() {
  /* نسخة الموبايل ما كاينةش إلا فـ شاشة صغيرة — الديسكطوب كيفضل الجدول */
  try {
    if (typeof window !== "undefined" && typeof window.innerWidth === "number" && window.innerWidth < 1024) return true;
    if (typeof window !== "undefined" && typeof window.matchMedia === "function" && window.matchMedia("(max-width:1023px)").matches) return true;
  } catch (e) { }
  return false;
}
function __pvMobileOn() {
  const small = __pvMobileSmallScreen();
  /* 1) ?mobile=1 ولا ?mobile=0 — قوة مطلقة (URL جديد = بلا كاش) */
  const q = __pvMobileQuery();
  if (q === "1" || q === "0") {
    try { localStorage.setItem("paraveda_mobile_mode", q); } catch (e) { }
    return q === "1" && small;
  }
  /* 2) الاختيار المحفوظ (الزر اليدوي) */
  try {
    const v = localStorage.getItem("paraveda_mobile_mode");
    if (v === "1") return small;
    if (v === "0") return false;
  } catch (e) { }
  /* 3) الكشف التلقائي: الهاتف دايما */
  return small;
}
function __pvSetMobile(on) {
  try { localStorage.setItem("paraveda_mobile_mode", on ? "1" : "0"); } catch (e) { }
  try { location.reload(); } catch (e) { }
}
function __pvMobileToggle() {
  __pvSetMobile(!__pvMobileOn());
}

/* --- التطبيق ديال الموبايل --------------------------------------------- */
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
  const [bad, setBad] = ee.useState(false);
  const [sheet, setSheet] = ee.useState(false);
  const [open, setOpen] = ee.useState(0);
  const [form, setForm] = ee.useState({ nom: "", telephone: "", ville: "", adresse: "", produit: "", qte: 1, prix: 0, commission: 35 });
  const today = __pvLocalDate(new Date());
  const tmr = ee.useRef(null);

  const toast = (t, isBad) => {
    setMsg(t); setBad(!!isBad);
    try { if (tmr.current) clearTimeout(tmr.current); } catch (e) { }
    try { tmr.current = setTimeout(() => setMsg(""), 4200); } catch (e) { }
  };

  const mine = ee.useMemo(() => a.filter(o => o && !o._del && String(o.agent || "").toLowerCase() === String(e || "").toLowerCase()), [a, e]);
  const drafts = ee.useMemo(() => mine.filter(o => o._d), [mine]);
  const live = ee.useMemo(() => mine.filter(o => !o._d), [mine]);

  const inPeriod = ee.useMemo(() => {
    if (period === "today") return o => String(o.dateCreation || "") === today;
    if (period === "week") { const d = new Date(); d.setDate(d.getDate() - 7); const from = __pvLocalDate(d); return o => String(o.dateCreation || "") >= from; }
    if (period === "month") { const d = new Date(); d.setDate(1); const from = __pvLocalDate(d); return o => String(o.dateCreation || "") >= from; }
    return () => true;
  }, [period, today]);

  const needle = q.trim().toLowerCase();
  const matches = (o) => !needle || [o.nom, o.telephone, o.ville, o.produit, o.adresse, o.remarques, o.tracking, o.statut, o.livraison].join(" ").toLowerCase().includes(needle);

  const scoped = ee.useMemo(() => live.filter(inPeriod), [live, inPeriod]);
  const follow = ee.useMemo(() => {
    if (needle) return scoped.filter(matches);
    const f = __pvKpiF(kpi) || (() => false);
    return scoped.filter(f);
  }, [scoped, kpi, needle]);
  const list = ee.useMemo(() => scoped.filter(matches), [scoped, needle]);

  const counts = ee.useMemo(() => {
    const r = {};
    ["call", "suivi", "ship", "risk"].forEach(k => {
      const f = __pvKpiF(k);
      r[k] = f ? scoped.filter(f).length : 0;
    });
    return r;
  }, [scoped]);

  const stats = ee.useMemo(() => {
    const conf = scoped.filter(o => String(o.statut || "").trim() === "Confirmé");
    const sold = scoped.filter(o => __pvSold(o));
    const back = scoped.filter(o => __pvBack(o));
    const wait = scoped.filter(o => String(o.livraison || "").trim() === "" && String(o.statut || "").trim() === "Confirmé");
    const ca = scoped.reduce((s, o) => s + (Number(o.prix) || 0), 0);
    return { total: scoped.length, conf: conf.length, sold: sold.length, back: back.length, wait: wait.length, ca: ca, today: scoped.filter(o => String(o.dateCreation || "") === today).length };
  }, [scoped, today]);

  /* --- الطلبية الجديدة ------------------------------------------------- */
  const pickVille = (v) => {
    const c0 = wo(v, cities);
    setForm(f => ({ ...f, ville: v, commission: c0 != null ? c0 : f.commission }));
  };
  const pickProduit = (p) => {
    const prod = catalog.find(x => String(x && x.nom || "").toLowerCase() === String(p || "").toLowerCase());
    const pr = prod ? Number(prod.prix != null ? prod.prix : (prod.price != null ? prod.price : prod.p)) : NaN;
    setForm(f => ({ ...f, produit: p, prix: !isNaN(pr) && pr > 0 ? pr : f.prix }));
  };
  const submit = () => {
    const v = form;
    if (!String(v.nom || "").trim()) { toast("❌ الاسم خاصو", true); return; }
    if (!String(v.telephone || "").trim()) { toast("❌ الهاتف خاصو", true); return; }
    if (!String(v.ville || "").trim()) { toast("❌ المدينة خاصها", true); return; }
    const d = today;
    i({
      dateCreation: d, dateConfirmation: d, statut: "", remarques: "", idCmd: "1",
      nom: String(v.nom).trim(), telephone: String(v.telephone).trim(), ville: v.ville, adresse: String(v.adresse || "").trim(),
      qte: Math.max(1, Number(v.qte) || 1), prix: Number(v.prix) || 0, produit: String(v.produit || "").trim(),
      livraison: "", tracking: "", upsell: 0, carousell: "", agent: e, link: "", carosellFlag: "", originLead: "",
      commission: Number(v.commission) > 0 ? Number(v.commission) : 35, fees: "", _d: 1
    });
    setForm({ nom: "", telephone: "", ville: v.ville, adresse: "", produit: v.produit, qte: 1, prix: v.prix, commission: v.commission });
    setSheet(false);
    setTab("drafts");
    toast("✅ تحفظت كمسودة — بعيتيها للأدمين من «المسودات»");
  };
  const publishAll = () => {
    if (!drafts.length) return;
    const ids = new Set(drafts.map(o => o.id));
    const n = pubF(ids);
    toast(n ? "✅ بعثنا " + n + " طلبية للأدمين" : "❌ ما بعثناش", !n);
  };

  /* --- القطع الصغيرة ---------------------------------------------------- */
  const chip = (txt, kind, k) => s.jsx("span", { key: k || txt, className: "mv-chip " + (kind || ""), children: txt });

  const card = (o) => {
    const st = String(o.statut || "").trim();
    const liv = String(o.livraison || "").trim();
    const tel = String(o.telephone || "").replace(/\s+/g, "");
    const wa = tel.replace(/^\+/, "");
    const isOpen = open === o.id;
    const tone = st === "Confirmé" ? "ok" : (st === "Annulé" ? "bad" : (st === "Rappel" ? "warn" : "new"));
    const kids = [];
    kids.push(s.jsxs("div", { key: "h", className: "mv-card-top", children: [
      s.jsxs("div", { key: "n", className: "mv-card-name", children: [
        s.jsx("b", { key: "t", children: o.nom || "(بلا اسم)" }),
        s.jsx("span", { key: "p", className: "mv-phone", children: "📞 " + (o.telephone || "—") })
      ]}),
      s.jsxs("div", { key: "v", className: "mv-card-side", children: [
        s.jsx("b", { key: "pr", className: "mv-price", children: (Number(o.prix) || 0) + " DH" }),
        o.dateCreation ? s.jsx("span", { key: "dt", className: "mv-date", children: "🗓️ " + o.dateCreation }) : null
      ]})
    ]}));
    const line = [];
    line.push(s.jsx("span", { key: "v", children: "📍 " + (o.ville || "—") }));
    if (o.produit) line.push(s.jsx("span", { key: "pr", children: "📦 " + o.produit }));
    if (Number(o.qte) > 1) line.push(s.jsx("span", { key: "q", children: "×" + o.qte }));
    if (o.tracking) line.push(s.jsx("span", { key: "tr", className: "mv-track", children: "Tracking " + o.tracking }));
    kids.push(s.jsxs("div", { key: "l", className: "mv-line", children: line }));
    if (isOpen) {
      const extra = [];
      if (o.adresse) extra.push(s.jsx("span", { key: "ad", children: "🏠 " + o.adresse }));
      if (o.remarques) extra.push(s.jsx("span", { key: "rm", children: "📝 " + o.remarques }));
      if (o.livraison) extra.push(s.jsx("span", { key: "lv", children: "🚚 " + o.livraison }));
      if (extra.length) kids.push(s.jsxs("div", { key: "x", className: "mv-line dim", children: extra }));
    }
    kids.push(s.jsxs("div", { key: "c", className: "mv-chips", children: [
      chip(st || "جديد", st === "Confirmé" ? "ok" : (st === "Annulé" ? "bad" : (st === "Rappel" ? "warn" : "")), "s"),
      liv ? chip(liv, "gray", "l") : null,
      o._d ? chip("مسودة", "draft", "d") : null
    ]}));
    kids.push(s.jsxs("div", { key: "a", className: "mv-actions", children: [
      tel ? s.jsx("a", { key: "call", href: "tel:" + tel, className: "mv-btn call", children: "📞 اتصال" }) : null,
      s.jsx("button", { key: "ok", onClick: () => { c(o.id, { statut: "Confirmé" }); toast("✅ تأكدات " + (o.nom || "الطلبية")); }, className: "mv-btn ok", children: "✅ تأكيد" }),
      s.jsx("button", { key: "rl", onClick: () => { c(o.id, { statut: "Rappel" }); toast("⏰ تسجلت للمتابعة"); }, className: "mv-btn", children: "⏰ متابعة" }),
      wa ? s.jsx("a", { key: "wa", href: "https://wa.me/" + wa, target: "_blank", rel: "noopener", className: "mv-btn wa", children: "💬 واتساب" }) : null,
      s.jsx("button", {
        key: "no",
        onClick: () => { if (window.confirm("نلغيو هاد الطلبية؟")) { c(o.id, { statut: "Annulé" }); toast("✖ تلغات الطلبية"); } },
        className: "mv-btn danger", children: "✖ إلغاء"
      }),
      s.jsx("button", { key: "mo", onClick: () => setOpen(isOpen ? 0 : o.id), className: "mv-btn ghost", children: isOpen ? "⌃ أقل" : "⌄ تفاصيل" })
    ]}));
    return s.jsxs("div", { key: o.id, className: "mv-card tone-" + tone, children: kids });
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

  const tile = (key, label, n, tone) => s.jsx("button", {
    key: key, onClick: () => { setKpi(key); setTab("suivi"); },
    className: "mv-tile " + (tone || "") + (kpi === key && !needle ? " on" : ""),
    children: [s.jsx("b", { key: "v", children: String(n) }), s.jsx("span", { key: "l", children: label })]
  });

  /* --- الصفحة ------------------------------------------------------------ */
  let body = null;
  if (tab === "suivi") {
    body = s.jsxs("div", { key: "bd", className: "mv-body", children: [
      s.jsxs("div", { key: "st", className: "mv-strip", children: [
        tile("call", "📞 للاتصال", counts.call, "red"),
        tile("suivi", "⏰ متابعة", counts.suivi, "amber"),
        tile("ship", "🚚 جاهزة", counts.ship, "blue"),
        tile("risk", "⚠️ خطر", counts.risk, "violet")
      ]}),
      s.jsxs("div", { key: "p", className: "mv-segs", children: [periodBtn("today", "اليوم"), periodBtn("week", "7 أيام"), periodBtn("month", "هاد الشهر"), periodBtn("all", "الكل")] }),
      s.jsxs("div", { key: "n", className: "mv-count", children: (needle ? (list.length + " نتيجة للبحث") : (follow.length + " طلبية فالتبّع")) }),
      follow.length ? follow.map(card) : s.jsx("div", { key: "e", className: "mv-empty", children: "ما كاين حتى طلبية فهاد القائمة ✅" })
    ]});
  } else if (tab === "orders") {
    body = s.jsxs("div", { key: "bd", className: "mv-body", children: [
      s.jsxs("div", { key: "p", className: "mv-segs", children: [periodBtn("today", "اليوم"), periodBtn("week", "7 أيام"), periodBtn("month", "هاد الشهر"), periodBtn("all", "الكل")] }),
      s.jsxs("div", { key: "n", className: "mv-count", children: list.length + " طلبية" }),
      list.length ? list.map(card) : s.jsx("div", { key: "e", className: "mv-empty", children: "ما كاين حتى طلبية" })
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
      s.jsxs("div", { key: "ca", className: "mv-card", children: [s.jsxs("div", { key: "h", className: "mv-card-top", children: [
        s.jsx("b", { key: "b", children: "💰 المبيعات" }),
        s.jsx("b", { key: "p", className: "mv-price", children: j2(Math.round(stats.ca)) + " DH" })
      ]})] }),
      s.jsxs("div", { key: "me", className: "mv-card", children: [s.jsxs("div", { key: "h", className: "mv-card-top", children: [
        s.jsxs("div", { key: "n", className: "mv-card-name", children: [
          s.jsx("b", { key: "t", children: "👤 الحساب" }),
          s.jsx("span", { key: "p", className: "mv-phone", children: h ? (h.username + " · " + (h.agent || "")) : "" })
        ]}),
        s.jsx("span", { key: "v", className: "mv-date", children: "نسخة الموبايل v4.01" })
      ]})] })
    ]});
  }

  /* --- ورقة الطلبية الجديدة --------------------------------------------- */
  const f = form;
  const set = (k) => (ev) => setForm(x => ({ ...x, [k]: ev.target.value }));
  const sheetNode = s.jsxs("div", { key: "sh", className: "mv-sheet-wrap", children: [
    s.jsx("div", { key: "bk", className: "mv-sheet-back", onClick: () => setSheet(false) }),
    s.jsxs("div", { key: "pn", className: "mv-sheet", children: [
      s.jsxs("div", { key: "hd", className: "mv-sheet-head", children: [
        s.jsx("b", { key: "t", children: "➕ طلبية جديدة" }),
        s.jsx("button", { key: "x", onClick: () => setSheet(false), className: "mv-sheet-close", title: "إغلاق", children: "✕" })
      ]}),
      s.jsxs("div", { key: "bd", className: "mv-sheet-body", children: [
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
      ]})
    ]})
  ]});

  const agentName = (h && (h.agent || h.username)) || e || "";

  return s.jsxs("div", { className: "mv-root", dir: "rtl", children: [
    s.jsxs("header", { key: "hd", className: "mv-head-bar", children: [
      s.jsx("div", { key: "av", className: "mv-avatar", children: String(agentName || "?").trim().charAt(0).toUpperCase() }),
      s.jsxs("div", { key: "hl", className: "mv-head-l", children: [
        s.jsx("b", { key: "u", children: agentName }),
        s.jsx("span", { key: "ag", className: "mv-head-sub", children: "نسخة الموبايل · " + stats.total + " طلبية" })
      ]}),
      s.jsxs("div", { key: "hr", className: "mv-head-r", children: [
        s.jsx("span", { key: "vb", className: "mv-ver", title: "نسخة التطبيق", children: "v4.01" }),
        s.jsx("button", { key: "tb", onClick: __pvMobileToggle, className: "mv-hbtn", title: "النسخة ديال الجدول", children: "🖥️" }),
        s.jsx("button", { key: "lo", onClick: () => lgOut && lgOut(), className: "mv-hbtn", title: "تسجيل الخروج", children: "⏻" })
      ]})
    ]}),
    s.jsxs("div", { key: "sr", className: "mv-search", children: [
      s.jsx("span", { key: "si", className: "mv-search-ic", children: "🔎" }),
      s.jsx("input", { key: "sq", className: "mv-in mv-search-in", value: q, onChange: ev => setQ(ev.target.value), placeholder: "بحث بالاسم، الهاتف، المدينة، Tracking…" })
    ]}),
    msg ? s.jsx("div", { key: "mg", className: "mv-toast" + (bad ? " bad" : ""), children: msg }) : null,
    body,
    s.jsxs("nav", { key: "nv", className: "mv-nav", children: [
      navBtn("suivi", "📞", "التبّع", follow.length ? String(follow.length) : ""),
      navBtn("orders", "📦", "الطلبيات"),
      s.jsx("button", { key: "new", onClick: () => setSheet(true), className: "mv-fab", title: "طلبية جديدة", children: "+" }),
      navBtn("drafts", "📤", "المسودات", drafts.length ? String(drafts.length) : ""),
      navBtn("stats", "📊", "الأرقام")
    ]}),
    sheet ? sheetNode : null
  ]});
}
