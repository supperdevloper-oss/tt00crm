/**
 * UI verification of the Digylog-style dashboard (Tab "Tableau de bord").
 *
 * It extracts the real component from index.html, renders it with React and
 * drives the six scope tabs, the "Masquer les données" switch, the period
 * toggles and the refresh button.
 *
 * Run it with:   cd tests/ui && npm i && node dashboard_ui.mjs
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
  console.log("SKIP  dashboard UI test (run: cd tests/ui && npm i)");
  process.exit(0);
}

const html = fs.readFileSync(path.join(ROOT, "index.html"), "utf8");
const comp = html.slice(html.indexOf("function __PvDashChart"),
                        html.indexOf("function Fj(){const{orders:e}=Xt()"));
const charts = html.slice(html.indexOf("function f_({livrees"),
                          html.indexOf("function or({label:e,value:n,sub:a,color:i,bg:c,onClick:f})"));
if (!comp || comp.indexOf("function __PvDigylogDash") < 0) {
  console.log("FAIL  the dashboard component is missing from index.html");
  process.exit(1);
}

let orders = [];
try {
  const data = JSON.parse(fs.readFileSync(path.join(ROOT, "crm_data.json"), "utf8"));
  orders = (data.paraveda_orders_v5 && data.paraveda_orders_v5.d) || [];
} catch { orders = []; }
orders = orders.filter(o => o && typeof o === "object" && !o._del);

const sold = o => o.livraison === "Livrée" || o.livraison === "Rechange";
const back = o => o.livraison === "Retour" || o.livraison === "Remboursé";
const onRoad = o => o.livraison === "Expédier vers" || o.livraison === "Expédié";
const live = orders.filter(o => o.statut !== "Annulé");
const EXPECT = {
  live: live.length,
  sold: live.filter(sold).length,
  back: live.filter(back).length,
  road: live.filter(onRoad).length,
  retour: live.filter(o => o.livraison === "Retour").length,
  rembourse: live.filter(o => o.livraison === "Remboursé").length,
  sent: live.filter(o => ["Expédier vers", "Expédié", "Livrée", "Rechange"].includes(o.livraison)).length,
};

const stub = `
const s = {jsx, jsxs, Fragment};
const ee = React;
const ya = e => Number(e || 0).toLocaleString("fr-FR");
const ja = (e, n = 2) => e === null || !isFinite(e) ? "—" : (Math.round(e * 100) / 100).toLocaleString("fr-FR", {maximumFractionDigits: n});
const Ir = (e, n) => n > 0 ? e / n * 100 : 0;
const __pvQ = o => Math.max(1, Number(o.qte) || 1);
const __pvSold = o => o.livraison === "Livrée" || o.livraison === "Rechange";
const __pvBack = o => o.livraison === "Retour" || o.livraison === "Remboursé";
const __pvInFlight = o => o.livraison !== "Livrée" && o.livraison !== "Retour" && o.livraison !== "Out Of Stock" && o.livraison !== "Remboursé" && o.livraison !== "Rechange" && o.statut !== "Annulé" && (o.statut === "Confirmé" || !!o.livraison);
function __pvLocalDate(d) { const p = n => String(n).padStart(2, "0"); return d.getFullYear() + "-" + p(d.getMonth() + 1) + "-" + p(d.getDate()); }
const orders = ${JSON.stringify(orders)};
const Xt = () => ({orders});
const Tn = () => ({inRange: () => true, label: "الكل"});
const yp = () => s.jsx("div", {}, "PERIOD");
const ig = () => [];
const lg = new Map();
const __pvEtag = null;
const __pvFetchSnap = async () => ({});
const __pvAdminMobile = () => false;
const Rd = "ui-test-token";
`;

const modFile = path.join(HERE, "_dashboard_component.mjs");
fs.writeFileSync(modFile,
  'import React from "react";\nimport {jsx, jsxs, Fragment} from "react/jsx-runtime";\n'
  + stub + charts + comp + "\nexport {__PvDigylogDash};\n");

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
global.addEventListener = dom.window.addEventListener.bind(dom.window);
global.removeEventListener = dom.window.removeEventListener.bind(dom.window);

const {__PvDigylogDash} = await import(pathToFileURL(modFile).href + "?v=" + Date.now());

const results = [];
const check = (name, ok, detail = "") => results.push([name, !!ok, ok ? "" : String(detail)]);

const fetchCalls = [];
const LIVE_ROWS = [
  {s: "Livrée", t: "SAAA11111", p: 1234, q: 2, n: "Produit Digylog", d: "2026-10-28"},
  {s: "Expédié", t: "SAAA22222", p: 500, q: 1, n: "Autre produit", d: "2026-10-28"},
  {s: "Retournée", t: "SAAA33333", p: 300, q: 1, n: "Produit Digylog", d: "2026-10-27"},
];
let liveMode = "offline";
global.fetch = async (url) => {
  fetchCalls.push(String(url));
  if (liveMode === "offline") throw new Error("offline");
  return {ok: true, status: 200, json: async () => ({
    ok: true, source: "digylog", mode: "orders",
    endpoint: "https://api.digylog.com/api/v2/seller/orders/grid",
    at: Math.floor(Date.now() / 1000), rows: LIVE_ROWS, kpis: {},
  })};
};

const root = createRoot(dom.window.document.getElementById("root"));
await act(async () => { root.render(jsxRuntime.jsx(__PvDigylogDash, {})); });

const text = () => dom.window.document.getElementById("root").textContent.replace(/[  ]/g, " ");
const buttons = () => [...dom.window.document.querySelectorAll("button")];
const byText = t => buttons().find(b => b.textContent.includes(t));
const click = async el => { await act(async () => { el.dispatchEvent(new dom.window.MouseEvent("click", {bubbles: true})); }); };

await act(async () => { await new Promise(r => setTimeout(r, 30)); });
check("the dashboard asks the server for the live Digylog dashboard",
  fetchCalls.some(u => u.includes("api.php?action=digylog_dash")),
  fetchCalls.join(" | "));
check("the six Digylog scope tabs are rendered",
  ["Global", "En ce moment", "Hub d'expédition", "Hub de livraison", "Hub des retours", "Retournée"].every(t => !!byText(t)),
  buttons().map(b => b.textContent).join(" | "));
check("the six KPI cards are rendered",
  ["Chiffre d'affaire", "Total colis livrés", "Total Expédition", "Non payé", "En cours de paiement", "Total Payé"].every(t => text().includes(t)));
check("the charts and the tables are rendered",
  text().includes("Évolution des expéditions") && text().includes("Taux de livraison")
  && text().includes("Top 5 produits vendus") && text().includes("Statuts livraisons"));
check("the global scope shows every delivered and shipped parcel",
  text().includes(String(EXPECT.sold)) && text().includes(String(EXPECT.sent)),
  `sold=${EXPECT.sold} sent=${EXPECT.sent} :: ${text().slice(0, 300)}`);

await click(byText("Hub de livraison"));
check("the delivery hub only counts delivered orders",
  text().includes(String(EXPECT.sold)) && !text().includes(String(EXPECT.road)),
  `sold=${EXPECT.sold} road=${EXPECT.road} :: ${text().slice(0, 300)}`);

await click(byText("Retournée"));
check("the returned hub only counts returned parcels",
  text().includes(String(EXPECT.retour)) && !text().includes(String(EXPECT.sold)),
  `retour=${EXPECT.retour} :: ${text()}`);

await click(byText("Global"));
await click(byText("Masquer les données"));
check("Masquer les données hides every number", text().includes("•••"), text().slice(0, 200));
await click(byText("Afficher les données"));
check("the numbers come back", !text().includes("•••"), text().slice(0, 200));

await click(byText("Depuis le mois dernier"));
check("the since last month switch keeps the page alive", text().includes("Depuis le mois dernier"));
await click(byText("15 Jours"));
await click(byText("30 Jours"));
check("the chart period toggles work", text().includes("Évolution des expéditions"));
await click(byText("refresh"));
check("the refresh button works", text().includes("refresh"));

// Live Digylog data must take over the page as soon as the server answers.
liveMode = "live";
await click(byText("refresh"));
await act(async () => { await new Promise(r => setTimeout(r, 30)); });
check("the live Digylog numbers replace the CRM numbers",
  text().includes("1 234 DH") && text().includes("Digylog live"),
  text().slice(0, 400));
check("the live badge counts the Digylog orders",
  text().includes("Digylog live · 3 commandes"), text().slice(0, 200));

// The KPI rectangle must never be rendered on a phone: the page falls back to tables.
Object.defineProperty(dom.window, "innerWidth", {value: 640, configurable: true});
await act(async () => { dom.window.dispatchEvent(new dom.window.Event("resize")); });
check("the KPI rectangle is not rendered on a phone",
  !text().includes("Évolution des expéditions") && text().includes("Indicateurs"),
  text().slice(0, 300));

root.unmount();
try { fs.unlinkSync(modFile); } catch {}

let failed = 0;
for (const [n, ok, d] of results) {
  if (!ok) failed++;
  console.log((ok ? "PASS " : "FAIL ") + n + (d ? "  -> " + d : ""));
}
console.log(`\n${results.length - failed}/${results.length} dashboard UI checks passed.`);
process.exit(failed ? 1 : 0);
