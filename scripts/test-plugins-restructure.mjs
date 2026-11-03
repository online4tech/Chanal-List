import assert from "node:assert/strict";
import { readFileSync, existsSync, readdirSync } from "node:fs";

const readJson = (path) => JSON.parse(readFileSync(path, "utf8"));
const catalog = readJson("control-center/data/catalog.json");
const clone = structuredClone(catalog);
const countTools = (value) => {
  if (!value || typeof value !== "object" || Array.isArray(value)) return 0;
  let total = Array.isArray(value.tools) ? value.tools.length : 0;
  for (const key of ["subcategories", "children", "categories", "groups"]) {
    const group = value[key];
    if (group && typeof group === "object" && !Array.isArray(group)) {
      for (const child of Object.values(group)) total += countTools(child);
    }
  }
  return total;
};
const sortEntriesAZ = (value) =>
  Object.fromEntries(Object.entries(value || {}).sort(([a], [b]) =>
    a.localeCompare(b, undefined, { sensitivity: "base" })
  ));
const plugin = clone.main.plugins;
const beforeCount = countTools(plugin);
const groups = plugin.subcategories || {};
const wrapper = groups.Plugins;
assert.ok(wrapper, "Legacy Plugins wrapper exists in source catalog");
const nested = wrapper.subcategories || wrapper.children || wrapper.categories || {};
const siblings = Object.fromEntries(Object.entries(groups).filter(([key]) => key !== "Plugins"));
plugin.subcategories = sortEntriesAZ({ ...nested, ...siblings });
if (Array.isArray(wrapper.tools) && wrapper.tools.length) {
  plugin.tools = [...(plugin.tools || []), ...wrapper.tools];
}
assert.equal(countTools(plugin), beforeCount, "Flattening preserves every plugin/tool record");
const expected = ["IPTV", "Media", "Other", "Settings", "Softcam", "Translation"];
assert.deepEqual(Object.keys(plugin.subcategories), expected, "Plugin categories are flat and A-Z");
const expectedCounts = { IPTV: 15, Media: 6, Other: 6, Settings: 9, Softcam: 8, Translation: 6 };
for (const [name, count] of Object.entries(expectedCounts)) {
  assert.equal(countTools(plugin.subcategories[name]), count, `${name} item count`);
}
assert.ok(!Object.hasOwn(plugin.subcategories, "Plugins"), "Intermediate Plugins wrapper removed");

const entry = readFileSync("src/main.jsx", "utf8");
assert.ok(entry.includes("flattenPluginCategories"), "Runtime flattening is wired");
assert.ok(entry.includes("localeCompare"), "Case-insensitive A-Z sorting is wired");
assert.ok(entry.includes("prepareCatalog(catalog)"), "Prepared catalog is rendered");

const ui = readFileSync("src/pages/ControlCenter.jsx", "utf8");
assert.ok(ui.includes("navigationHistory") && ui.includes("goBack"), "Existing hierarchical back navigation remains");
assert.ok(ui.includes("const results = useMemo"), "Existing deferred search remains");

const css = readFileSync("src/styles.css", "utf8");
for (const marker of ["height: 72px", "gap: 14px", "blur(16px)", "min-width: 768px", "min-width: 1280px"]) {
  assert.ok(css.includes(marker), `Responsive card style: ${marker}`);
}
assert.ok(readFileSync("control-center-app/index.html", "utf8").includes("header-logo.css"), "Header branding stylesheet remains linked");
assert.ok(readFileSync("vite.config.js", "utf8").includes("readdirSync"), "Build cleanup preserves custom assets");

if (existsSync("control-center/index.html")) {
  const builtHtml = readFileSync("control-center/index.html", "utf8");
  const refs = [...builtHtml.matchAll(/(?:src|href)="([^"]+assets\/[^"]+)"/g)].map((m) => m[1]);
  for (const ref of refs) {
    const filename = ref.split("/").pop();
    assert.ok(existsSync(`control-center/assets/${filename}`), `Built asset exists: ${filename}`);
  }
  assert.ok(existsSync("control-center/assets/header-logo.css"), "Custom header asset survives build");
}
console.log("Plugins restructure integrity tests: PASS");
