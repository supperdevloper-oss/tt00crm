/**
 * UI verification of the professional mobile version of the CRM (نسخة الموبايل v4.01).
 *
 * It extracts the real mobile component from index.html, renders it with React
 * and drives the follow-up list, the KPI tiles, the quick status buttons, the
 * new order sheet, the drafts and the statistics.
 *
 * Run it with:   cd tests/ui && npm i && node mobile_ui.mjs
 * Without the node modules the script prints SKIP and exits with 0.
 */
import fs from "fs";
import path from "path";
import {fileURLToPath, pathToFileURL} from "url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, "../..");

let React, createRoot, act, JSDOM, jsxRuntime;
try {
  React = (await import("react")).default;
  ({createRoot} = await import("react-dom/client"));
  ({act} = await import("react-dom/test-utils"));
  ({JSDOM} = await import("jsdom"));
  jsxRuntime = await import("react/jsx-runtime");
} catch (e) {
  console.log("SKIP  mobile UI test (run: cd tests/ui && npm i)");
  process.exit(0);
}

const html = fs.readFileSync(path.join(ROOT, "index.html"), "utf8");
const start = html.indexOf("function __pvMobileQuery()");
const end = html.indexOf("function __pvRepairStorage()");
const comp = html.slice(start, end);
if (!comp || comp.indexOf("function __PvMobileApp") < 0) {
  console.log("FAIL  the mobile component is missing from index.html");
  process.exit(1);
}

const orders = [
  {id: 1, agent: "Meryam", nom: "فاطمة الزهراء", telephone: "0661000001", ville: "Casablanca",
   adresse: "حي النخيل", produit: "Slimminge Patch", qte: 2, prix: 400, statut: "", livraison: "",
   dateCreation: "2026-10-28", remarques: "توصيل بعد الرابعة"},
  {id: 2, agent: "Meryam", nom: "سعاد العلوي", telephone: "0661000002", ville: "Agadir",
   produit: "Good-Fair", qte: 1, prix: 250, statut: "Rappel", livraison: "",
   dateCreation: "2026-10-27", remarques: ""},
  {id: 3, agent: "Meryam", nom: "خديجة بنعلي", telephone: "0661000003", ville: "Tanger",
   produit: "ParaVida", qte: 1, prix: 300, statut: "Confirmé", livraison: "Livrée",
   dateCreation: "2026-10-20", remarques: ""},
  {id: 4, agent: "Meryam", nom: "نزهة أمين", telephone: "0661000004", ville: "Casablanca",
   produit: "Slim-Bio", qte: 1, prix: 350, statut: "", livraison: "", dateCreation: "2026-10-29",
   remarques: "", _d: 1},
  {id: 5, agent: "AYA", nom: "ليلىRadi", telephone: "0661000005", ville: "Casablanca",
   produit: "X", qte: 1, prix: 100, statut: "", livraison: "", dateCreation: "2026-10-29", remarques: ""},
];

const stub = `
const s = {jsx, jsxs, Fragment};
const ee = React;
const j2 = e => Number(e || 0).toLocaleString("fr-FR");
const __pvQ = o => Math.max(1, Number(o.qte) || 1);
const __pvSold = o => o.livraison === "Livrée" || o.livraison === "Rechange";
const __pvBack = o => o.livraison === "Retour" || o.livraison === "Remboursé";
function __pvLocalDate(d) { const p = n => String(n).padStart(2, "0"); return d.getFullYear() + "-" + p(d.getMonth() + 1) + "-" + p(d.getDate()); }
const __pvIsCall = o => { const t = String(o.statut ?? "").trim(); return t === "" || /^Appel/i.test(t); };
const __pvKPI = [
  {k: "call", f: o => __pvIsCall(o) && String(o.livraison ?? "").trim() === ""},
  {k: "suivi", f: o => ["Rappel", "Suivé", "Whatssap"].indexOf(String(o.statut ?? "").trim()) >= 0},
  {k: "ship", f: o => String(o.statut ?? "").trim() === "Confirmé" && String(o.livraison ?? "").trim() === ""},
  {k: "risk", f: o => __pvIsCall(o) && String(o.livraison ?? "").trim() === ""},
];
const __pvKpiF = k => { const d = __pvKPI.find(x => x.k === k); return d ? d.f : null; };
const CITIES = [{nom: "Casablanca", prix: 350}, {nom: "Agadir", prix: 300}, {nom: "Tanger", prix: 320}];
const er = v => String(v || "").trim().toLowerCase();
const Ap = {};
function wo(e, n) { const a = er(e); if (!a) return null; const i = Ap[a] || a; const c = (n || []).find(f => er(f.nom) === i); return c ? c.prix : null; }
const Ll = () => CITIES;
const usePvCatalog = () => [{nom: "Slimminge Patch", prix: 350}, {nom: "Good-Fair", prix: 250}, {nom: "ParaVida", prix: 300}];
function Pk({value, list, onChange, className}) {
  const opts = (list || []).map(p => p.nom);
  return jsx("select", {value: value || "", onChange: e => onChange && onChange(e.target.value), className: className || "",
    children: [jsx("option", {key: "o0", value: "", children: "— اختار المنتوج —"})].concat(opts.map(n => jsx("option", {key: n, value: n, children: n})))});
}
const __pvAdminMobile = () => true;
const ORDER_STATE = {orders: ${JSON.stringify(orders)}};
const CALLS = {add: [], upd: [], publish: []};
const Xt = () => ({
  orders: ORDER_STATE.orders,
  add: o => { CALLS.add.push(o); },
  upd: (id, patch) => { CALLS.upd.push([id, patch]); },
  publish: ids => { CALLS.publish.push([...ids]); return ids.size; },
});
const USER = {currentUser: {username: "Meryam", agent: "Meryam", role: "agent"}, logout: () => {}};
const kr = () => USER;
`;

const modFile = path.join(HERE, "_mobile_component.mjs");
fs.writeFileSync(modFile,
  'import React from "react";\nimport {jsx, jsxs, Fragment} from "react/jsx-runtime";\n'
  + stub + comp + "\nexport {__PvMobileApp, __pvMobileOn, __pvMobileToggle, __pvSetMobile, CALLS};\n");

const dom = new JSDOM("<!doctype html><html><body><div id='root'></div></body></html>",
                       {url: "https://paraveda.store/"});
dom.window.matchMedia = (q) => ({matches: true, media: q, onchange: null,
  addEventListener() {}, removeEventListener() {}, addListener() {}, removeListener() {},
  dispatchEvent() { return false; }});
global.window = dom.window;
global.document = dom.window.document;
try { Object.defineProperty(global, "navigator", {value: dom.window.navigator, configurable: true}); } catch {}
global.HTMLElement = dom.window.HTMLElement;
global.Node = dom.window.Node;
global.IS_REACT_ACT_ENVIRONMENT = true;
global.localStorage = dom.window.localStorage;
Object.defineProperty(dom.window, "innerWidth", {value: 390, configurable: true});
global.addEventListener = dom.window.addEventListener.bind(dom.window);
global.removeEventListener = dom.window.removeEventListener.bind(dom.window);
dom.window.confirm = () => true;
let reloads = 0;
global.location = {search: "", reload: () => { reloads++; }};

const mod = await import(pathToFileURL(modFile).href + "?v=" + Date.now());
const {__PvMobileApp, __pvMobileOn, __pvSetMobile, CALLS} = mod;

const results = [];
const check = (name, ok, detail = "") => results.push([name, !!ok, ok ? "" : String(detail)]);
// the react dev warnings about the automatic runtime are expected here
const realError = console.error;
console.error = (...a) => { if (String(a[0] || "").startsWith("Warning:")) return; realError(...a); };

const root = createRoot(dom.window.document.getElementById("root"));
await act(async () => { root.render(jsxRuntime.jsx(__PvMobileApp, {agent: "Meryam"})); });

const text = () => dom.window.document.getElementById("root").textContent.replace(/[  ]/g, " ");
const buttons = () => [...dom.window.document.querySelectorAll("button")];
const byText = t => buttons().find(b => b.textContent.includes(t));
/* the buttons of an order card (not the KPI tiles of the header) */
const cardBtn = t => [...dom.window.document.querySelectorAll(".mv-actions button, .mv-actions a")].find(b => b.textContent.includes(t));
/* the KPI tiles of the top strip */
const tile = t => [...dom.window.document.querySelectorAll(".mv-tile")].find(b => b.textContent.includes(t));
const click = async el => { await act(async () => { el.dispatchEvent(new dom.window.MouseEvent("click", {bubbles: true})); }); };

// --- the shell -------------------------------------------------------------
check("the mobile bottom navigation is rendered",
  ["التبّع", "الطلبيات", "المسودات", "الأرقام"].every(t => !!byText(t)),
  buttons().map(b => b.textContent).join(" | "));
check("the new order button is in the navigation",
  !!dom.window.document.querySelector(".mv-fab"), "no .mv-fab");
check("the header shows the version of the app",
  (dom.window.document.querySelector(".mv-ver") || {}).textContent === "v4.01",
  (dom.window.document.querySelector(".mv-ver") || {}).textContent);
check("the header shows the avatar of the agent",
  !!dom.window.document.querySelector(".mv-avatar"), "no avatar");
check("the search field is always visible",
  !!dom.window.document.querySelector(".mv-search-in"), "no search");

// --- the follow-up list ----------------------------------------------------
check("the follow-up list shows the orders to call",
  text().includes("فاطمة الزهراء"), text().slice(0, 300));
check("the follow-up list never shows the orders of another agent",
  !text().includes("ليلىRadi"), text().slice(0, 300));
check("the order card shows the phone and the city",
  text().includes("0661000001") && text().includes("Casablanca"), text().slice(0, 300));
check("the order card has the quick call button",
  !!dom.window.document.querySelector("a[href^='tel:']"), text().slice(0, 200));
check("the order card has the WhatsApp button",
  !!dom.window.document.querySelector("a[href^='https://wa.me/']"), text().slice(0, 200));
check("the KPI tiles show the counters",
  dom.window.document.querySelectorAll(".mv-tile").length === 4,
  dom.window.document.querySelectorAll(".mv-tile").length + " tiles");

// the quick status buttons write the CRM field
await click(cardBtn("تأكيد"));
check("the status update is sent to the CRM",
  CALLS.upd.length > 0 && CALLS.upd[0][1].statut === "Confirmé", JSON.stringify(CALLS.upd));
await click(cardBtn("متابعة"));
check("the reminder is written to the CRM",
  CALLS.upd.some(x => x[1].statut === "Rappel"), JSON.stringify(CALLS.upd));

// the details of the card
await click(cardBtn("تفاصيل"));
check("the details of the card show the address and the note",
  text().includes("حي النخيل") && text().includes("توصيل بعد الرابعة"), text().slice(0, 400));

// the KPI tiles filter the list
await click(tile("متابعة"));
check("the follow-up filter switches to the reminders",
  !text().includes("فاطمة الزهراء") && text().includes("سعاد العلوي"), text().slice(0, 300));
await click(tile("للاتصال"));
check("the follow-up filter switches back", text().includes("فاطمة الزهراء"), text().slice(0, 300));

// --- the new order sheet ---------------------------------------------------
await click(dom.window.document.querySelector(".mv-fab"));
check("the new order sheet opens",
  !!dom.window.document.querySelector(".mv-sheet"), "no sheet");
check("the new order form is rendered",
  text().includes("الاسم الكامل") && text().includes("الهاتف") && text().includes("المدينة")
  && !!byText("حفظ الطلبية"), text().slice(0, 300));
const citySel = dom.window.document.querySelector(".mv-sheet select.mv-in");
check("the city list is filled with the real cities",
  citySel && citySel.options.length >= 3, citySel ? citySel.options.length : "no select");
await click(byText("حفظ الطلبية"));
check("the empty form is refused with a clear message",
  (dom.window.document.querySelector(".mv-toast") || {}).textContent === "❌ الاسم خاصو",
  (dom.window.document.querySelector(".mv-toast") || {}).textContent);
check("the sheet stays open when the form is empty",
  !!dom.window.document.querySelector(".mv-sheet"), "the sheet was closed");

// the delivery cost of the city
await act(async () => {
  const setter = Object.getOwnPropertyDescriptor(dom.window.HTMLSelectElement.prototype, "value").set;
  setter.call(citySel, "Casablanca");
  citySel.dispatchEvent(new dom.window.Event("change", {bubbles: true}));
});
const hint = dom.window.document.querySelector(".mv-hint");
check("the delivery cost of the city is shown",
  !!hint && /ثمن التوصيل/.test(hint.textContent || ""), hint ? hint.textContent : "no hint");
const price = [...dom.window.document.querySelectorAll(".mv-sheet input.mv-in")].find(i => i.type === "number" && i.min === "0");
check("the selling price is not the delivery cost", !!price && Number(price.value) !== 350,
  price ? "prix=" + price.value : "no price input");
await click(dom.window.document.querySelector(".mv-sheet-close"));
check("the sheet can be closed", !dom.window.document.querySelector(".mv-sheet"), "the sheet is still open");

// --- the drafts ------------------------------------------------------------
await click(byText("المسودات"));
check("the drafts page shows the orders that are not published yet",
  text().includes("نزهة أمين") && !!byText("بعت"), text().slice(0, 300));
await click(byText("بعت"));
check("the drafts are published to the admin", CALLS.publish.length > 0, JSON.stringify(CALLS.publish));

// --- the statistics --------------------------------------------------------
await click(byText("الأرقام"));
check("the statistics page shows the numbers of the agent",
  text().includes("طلبيات") && text().includes("مؤكدة") && text().includes("مسلّمة"), text().slice(0, 300));
check("the statistics page shows the version of the mobile app",
  text().includes("نسخة الموبايل v4.01"), text().slice(0, 300));

// --- the switch between the table and the mobile version ------------------
dom.window.localStorage.setItem("paraveda_mobile_mode", "0");
check("the mobile version can be turned off", __pvMobileOn() === false, String(__pvMobileOn()));
dom.window.localStorage.setItem("paraveda_mobile_mode", "1");
check("the mobile version can be forced on", __pvMobileOn() === true, String(__pvMobileOn()));
dom.window.localStorage.removeItem("paraveda_mobile_mode");
check("on a phone the mobile version is the default", __pvMobileOn() === true, String(__pvMobileOn()));
global.location.search = "?mobile=1";
check("?mobile=1 forces the mobile version", __pvMobileOn() === true, String(__pvMobileOn()));
check("?mobile=1 is remembered", dom.window.localStorage.getItem("paraveda_mobile_mode") === "1",
  dom.window.localStorage.getItem("paraveda_mobile_mode"));
global.location.search = "?mobile=0";
check("?mobile=0 forces the table version", __pvMobileOn() === false, String(__pvMobileOn()));
global.location.search = "";
dom.window.localStorage.removeItem("paraveda_mobile_mode");
const reloadsBefore = reloads;
__pvSetMobile(true);
check("the manual switch reloads the page", reloads === reloadsBefore + 1, String(reloads));

root.unmount();
try { fs.unlinkSync(modFile); } catch {}

let failed = 0;
for (const [n, ok, d] of results) {
  if (!ok) failed++;
  console.log((ok ? "PASS " : "FAIL ") + n + (d ? "  -> " + d : ""));
}
console.log(`\n${results.length - failed}/${results.length} mobile UI checks passed.`);
process.exit(failed ? 1 : 0);
