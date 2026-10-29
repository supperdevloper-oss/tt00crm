/**
 * Digylog status -> CRM delivery vocabulary.
 *
 * The live dashboard reads the Digylog order list and turns every Digylog
 * status into the CRM value used by the scopes (Livrée, Rechange, Expédier
 * vers, Expédié, Retour, Remboursé, Out Of Stock, Annulé).
 *
 * Run it with:   node tests/ui/status_map.mjs
 */
import fs from "fs";
import path from "path";
import {fileURLToPath} from "url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, "../..");
const html = fs.readFileSync(path.join(ROOT, "index.html"), "utf8");

const a = html.indexOf("function __PvDashMapLive");
const b = html.indexOf("function __PvDigylogDash");
if (a < 0 || b < 0) {
  console.log("FAIL  __PvDashMapLive is missing from index.html");
  process.exit(1);
}
const map = new Function(html.slice(a, b) + "; return __PvDashMapLive;")();

const CASES = [
  ["Livrée", "Livrée"], ["livree", "Livrée"], ["Livré", "Livrée"], ["Livrée*", "Rechange"],
  ["Rechange", "Rechange"], ["Delivered", "Livrée"], ["delivery done", "Livrée"],
  ["Expédié", "Expédié"], ["Shipped", "Expédié"], ["En transit", "Expédié"],
  ["En cours de livraison", "Expédié"], ["En cours", "Expédié"], ["Dispatched", "Expédié"],
  ["Expédier vers", "Expédier vers"], ["À expédier", "Expédier vers"], ["Non envoyée", "Expédier vers"],
  ["Ready to ship", "Expédier vers"], ["To ship", "Expédier vers"], ["En préparation", "Expédier vers"],
  ["Retournée", "Retour"], ["Retour", "Retour"], ["Returned", "Retour"], ["Remboursé", "Retour"],
  ["Refund", "Retour"],
  ["Out Of Stock", "Out Of Stock"], ["Rupture de stock", "Out Of Stock"],
  ["Annulée", "Annulé"], ["Cancelled", "Annulé"],
  ["Confirmé", ""], ["", ""], ["Inconnu", ""],
];

let bad = 0;
for (const [input, expected] of CASES) {
  const got = map(input);
  if (got !== expected) {
    bad++;
    console.log(`FAIL  "${input}" -> "${got}" (expected "${expected}")`);
  }
}
console.log(`${CASES.length - bad}/${CASES.length} Digylog status mappings passed.`);
process.exit(bad ? 1 : 0);
