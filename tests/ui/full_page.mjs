/*
 * Renders the REAL index.html (the whole bundled app) inside jsdom,
 * with a phone user-agent and a logged-in agent account, then checks
 * that the mobile version really shows up (and that the desktop table
 * still shows up for the admin).
 *
 *   cd tests/ui && npm i && node full_page.mjs
 */
import fs from "fs";
import path from "path";
import { fileURLToPath, pathToFileURL } from "url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, "../..");

let JSDOM;
try {
  ({ JSDOM } = await import("jsdom"));
} catch (e) {
  console.log("SKIP  full page test (run: cd tests/ui && npm i)");
  process.exit(0);
}

const html = fs.readFileSync(path.join(ROOT, "index.html"), "utf8");

// --- the inline module script of the CRM ---------------------------------
const blocks = [...html.matchAll(/<script([^>]*)>([\s\S]*?)<\/script>/g)];
const mod = blocks.find((b) => b[1].includes("type=\"module\""));
if (!mod) {
  console.log("FAIL  the module script is missing from index.html");
  process.exit(1);
}
const modFile = path.join(HERE, "_full_app.mjs");
fs.writeFileSync(modFile, mod[2]);

const results = [];
const check = (name, ok, detail) => results.push([name, !!ok, detail || ""]);

const run = async (agent, mobileMode) => {
  const dom = new JSDOM(
    `<!doctype html><html><head><meta name="viewport" content="width=device-width"></head>` +
    `<body><div id="root"></div></body></html>`,
    { url: "https://paraveda.store/", pretendToBeVisual: true }
  );
  const w = dom.window;
  // a phone: the CRM must switch to the mobile version by itself
  Object.defineProperty(w.navigator, "userAgent", {
    value: "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 " +
           "(KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    configurable: true
  });
  Object.defineProperty(w, "innerWidth", { value: 390, configurable: true });
  Object.defineProperty(w, "innerHeight", { value: 844, configurable: true });
  w.matchMedia = (q) => ({
    matches: /max-width:\s*(820|1024|900|1050)/.test(q) ? /820/.test(q) : false,
    media: q, onchange: null,
    addEventListener() {}, removeEventListener() {},
    addListener() {}, removeListener() {}, dispatchEvent() { return false; }
  });
  // the agent is logged in
  w.localStorage.setItem("paraveda_users_v1", JSON.stringify([
    { id: 1, username: "admin@paraveda.ma", password: "x", role: "admin", agent: "" },
    { id: 2, username: "Meryam", password: "x", role: "user", agent: "Meryam" }
  ]));
  w.localStorage.setItem("paraveda_session_v1", agent === "admin" ? "1" : "2");
  if (mobileMode !== null) w.localStorage.setItem("paraveda_mobile_mode", mobileMode);
  w.localStorage.setItem("paraveda_orders_v5", JSON.stringify([
    { id: 1, agent: "Meryam", nom: "فاطمة الزهراء", telephone: "0661000001", ville: "Casablanca",
      produit: "Slimminge Patch", qte: 1, prix: 350, statut: "", livraison: "", dateCreation: "2026-11-04" }
  ]));

  const globals = ["window", "document", "navigator", "location", "localStorage", "sessionStorage",
    "matchMedia", "requestAnimationFrame", "cancelAnimationFrame", "HTMLElement", "HTMLInputElement",
    "HTMLSelectElement", "Element", "Node", "Event", "CustomEvent", "MouseEvent", "KeyboardEvent",
    "InputEvent", "MutationObserver", "getComputedStyle", "devicePixelRatio", "screen", "history",
    "XMLHttpRequest", "IntersectionObserver", "ResizeObserver", "FileReader", "Blob", "URL"];
  const saved = {};
  for (const g of globals) {
    saved[g] = global[g];
    const v = w[g];
    if (v !== undefined) {
      try { global[g] = typeof v === "function" && /^(requestAnimationFrame|cancelAnimationFrame|matchMedia|getComputedStyle)$/.test(g) ? v.bind(w) : v; }
      catch (e) { /* ignore */ }
    }
  }
  global.window = w;
  global.document = w.document;
  try { Object.defineProperty(global, "navigator", { value: w.navigator, configurable: true }); } catch (e) { }
  global.self = w;
  global.IS_REACT_ACT_ENVIRONMENT = false;
  w.fetch = async () => ({ ok: false, status: 0, json: async () => ({}), text: async () => "" });
  global.fetch = w.fetch;
  // jsdom does not implement these observers
  class NoopObserver {
    constructor(cb) { this.cb = cb; }
    observe() {} unobserve() {} disconnect() {} takeRecords() { return []; }
  }
  for (const name of ["ResizeObserver", "IntersectionObserver"]) {
    if (!w[name]) { w[name] = NoopObserver; global[name] = NoopObserver; }
  }

  const errors = [];
  const origError = console.error;
  console.error = (...a) => { errors.push(a.map(String).join(" ")); origError(...a); };

  const url = pathToFileURL(modFile).href + "?v=" + Date.now() + Math.random();
  try {
    await import(url);
  } catch (e) {
    console.error = origError;
    try { for (const g of globals) global[g] = saved[g]; } catch (e2) { }
    return { dom, errors: ["IMPORT FAILED: " + (e && e.stack || e)], html: "" };
  }
  // wait for the bootstrap (2.5s) + a couple of renders
  await new Promise((r) => setTimeout(r, Number(process.env.FULL_WAIT || 4500)));
  const rootHtml = w.document.getElementById("root") ? w.document.getElementById("root").innerHTML : "";
  if (process.env.FULL_DEBUG) {
    console.log("DEBUG root html:", JSON.stringify(rootHtml.slice(0, 400)));
    console.log("DEBUG errors:", errors.slice(0, 5));
    console.log("DEBUG body text:", JSON.stringify((w.document.body.textContent || "").slice(0, 300)));
  }
  console.error = origError;
  try { for (const g of globals) global[g] = saved[g]; } catch (e) { }
  return { dom, errors, html: rootHtml, text: w.document.body.textContent || "" };
};

// --- 1. the agent on a phone gets the mobile version ---------------------
const agent = await run("agent", null);
check("the app boots (the root is not empty)", agent.html.length > 50, "len=" + agent.html.length);
check("the app does not crash", agent.errors.length === 0, agent.errors.slice(0, 3).join(" | "));
check("the mobile version is shown to the agent on the phone",
  agent.html.includes("mv-root") && agent.text.includes("التبّع") && agent.text.includes("المسودات"),
  agent.text.slice(0, 200));
check("the mobile version shows the call button and the order",
  agent.html.includes("tel:0661000001") && agent.text.includes("فاطمة الزهراء"),
  agent.text.slice(0, 200));

// --- 1b. the mobile version really works (form, price, status) -----------
{
  const w = agent.dom.window;
  const doc = w.document;
  const click = async (el) => {
    el.dispatchEvent(new w.MouseEvent("click", { bubbles: true, cancelable: true }));
    await new Promise((r) => setTimeout(r, 120));
  };
  const fab = doc.querySelector(".mv-fab");
  check("the mobile version has a button for a new order", !!fab, fab ? fab.className : "missing");
  if (fab) {
    await click(fab);
    const sel = doc.querySelector("select.mv-in");
    check("the new order form opens with the cities", !!sel && sel.options.length > 1,
      sel ? "options=" + sel.options.length : "no select");
    if (sel) {
      const opt = [...sel.options].find(o => o.value === "Casablanca");
      if (opt) {
        sel.value = "Casablanca";
        sel.dispatchEvent(new w.Event("change", { bubbles: true }));
        await new Promise((r) => setTimeout(r, 250));
      }
      const hint = doc.querySelector(".mv-hint");
      check("the delivery cost of the city is shown", !!hint && /ثمن التوصيل/.test(hint.textContent || ""),
        hint ? hint.textContent : "no hint");
      const price = [...doc.querySelectorAll("input.mv-in")].find(i => i.type === "number" && i.min === "0");
      check("the selling price is not the delivery cost", !!price && Number(price.value) !== 35,
        price ? "prix=" + price.value : "no price input");
    }
  }
  const ok = [...doc.querySelectorAll(".mv-btn.ok")][0];
  if (ok) {
    await click(ok);
    await new Promise((r) => setTimeout(r, 400));
    const txt = doc.body.textContent || "";
    check("the status can be changed from the phone", txt.includes("Confirmé"), txt.slice(0, 160));
  }
}

// --- 2. the admin on a phone keeps the table ------------------------------
const admin = await run("admin", null);
check("the admin still gets the table version",
  !admin.html.includes("mv-root") && admin.html.length > 50,
  (admin.html.includes("mv-root") ? "mv-root found" : "ok"));

// --- 3. the desktop keeps the table (mobile mode forced off) --------------
const desk = await run("agent", "0");
check("the table version can be forced (mobile mode off)",
  !desk.html.includes("mv-root") && desk.html.length > 50,
  (desk.html.includes("mv-root") ? "mv-root found" : "ok"));

try { fs.unlinkSync(modFile); } catch {}

let failed = 0;
for (const [n, ok, d] of results) {
  if (!ok) failed++;
  console.log((ok ? "PASS " : "FAIL ") + n + (d ? "  -> " + d : ""));
}
console.log(`\n${results.length - failed}/${results.length} full page checks passed.`);
process.exit(failed ? 1 : 0);
