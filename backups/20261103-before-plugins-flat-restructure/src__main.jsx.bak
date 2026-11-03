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
    renderCatalog(catalog);
  })
  .catch((err) => console.error("Online4Tech catalog load failed:", err));
