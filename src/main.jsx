import React from "react";
import { createRoot } from "react-dom/client";
import ControlCenter from "./pages/ControlCenter.jsx";
import "./styles.css";

// Keep the existing catalog as the source for every section except Channels.
const emptyCatalog = {
  main: Object.fromEntries(
    ["panels", "plugins", "channels", "feeds", "tools", "skins", "images",
      "picons", "bootlogos", "spinners", "backup", "restore"].map((k) => [k, { tools: [] }])
  ),
};

const root = createRoot(document.getElementById("root"));
const renderCatalog = (data) =>
  root.render(
    <React.StrictMode>
      <ControlCenter data={data} />
    </React.StrictMode>
  );

const sortEntriesAZ = (value) =>
  Object.fromEntries(
    Object.entries(value || {}).sort(([a], [b]) =>
      a.localeCompare(b, undefined, { sensitivity: "base" })
    )
  );

// Promote the legacy Plugins wrapper so its categories sit beside Media.
const flattenPluginCategories = (catalog) => {
  const plugins = catalog?.main?.plugins;
  const groups = plugins?.subcategories;
  const wrapper = groups?.Plugins;
  if (!plugins || !groups || !wrapper || typeof wrapper !== "object") return catalog;

  const nested = wrapper.subcategories || wrapper.children || wrapper.categories || {};
  const siblings = Object.fromEntries(Object.entries(groups).filter(([key]) => key !== "Plugins"));
  plugins.subcategories = { ...nested, ...siblings };
  plugins.description = plugins.description || wrapper.description || wrapper.desc || "";
  plugins.icon = plugins.icon || wrapper.icon || "plugins";
  if (Array.isArray(wrapper.tools) && wrapper.tools.length) {
    plugins.tools = [...(plugins.tools || []), ...wrapper.tools];
  }
  return catalog;
};

// Sort root categories and every category map automatically, including future additions.
const sortCategoryMaps = (value) => {
  if (!value || typeof value !== "object" || Array.isArray(value)) return value;
  for (const key of ["subcategories", "children", "categories", "groups"]) {
    if (value[key] && typeof value[key] === "object" && !Array.isArray(value[key])) {
      const sorted = sortEntriesAZ(value[key]);
      for (const child of Object.values(sorted)) sortCategoryMaps(child);
      value[key] = sorted;
    }
  }
  return value;
};

const prepareCatalog = (catalog) => {
  if (!catalog?.main) return catalog;
  flattenPluginCategories(catalog);
  catalog.main = sortEntriesAZ(catalog.main);
  for (const category of Object.values(catalog.main)) sortCategoryMaps(category);
  return catalog;
};

const applyChannels = (catalog, channels) => {
  const tools = [...channels]
    .sort((a, b) => Number(a.order || 0) - Number(b.order || 0))
    .map((item) => ({
      name: item.name,
      description: [item.description, item.version ? `Version: ${item.version}` : ""].filter(Boolean).join(" | "),
      install: item.download ? `wget -O /tmp/online4tech-${String(item.id).replace(/[^a-zA-Z0-9_-]/g, "-")} ${item.download}` : "",
      path: item.github || item.download || "",
      status: "available",
      icon: "channels",
    }));

  const channelSection = catalog.main?.channels;
  const channelGroup = channelSection?.subcategories?.["ملفات القنوات والأقمار"];
  if (channelGroup) channelGroup.tools = tools;
  else catalog.main.channels = { tools };
  return catalog;
};

renderCatalog(emptyCatalog);
fetch("./data/catalog.json", { cache: "no-store" })
  .then((res) => {
    if (!res.ok) throw new Error("Catalog unavailable");
    return res.json();
  })
  .then(async (catalog) => {
    try {
      const response = await fetch("./data/channels.json", { cache: "no-store" });
      if (!response.ok) throw new Error("Channels data unavailable");
      const channels = await response.json();
      if (!Array.isArray(channels)) throw new Error("Channels data must be an array");
      applyChannels(catalog, channels);
    } catch (err) {
      console.error("Online4Tech Channels data load failed:", err);
    }
    renderCatalog(prepareCatalog(catalog));
  })
  .catch((err) => console.error("Online4Tech catalog load failed:", err));
