import React from "react";
import { createRoot } from "react-dom/client";
import ControlCenter from "./pages/ControlCenter.jsx";
import "./styles.css";

// Same behaviour as the deployed build: render an empty shell first,
// then load the live catalog from ./data/catalog.json.
const emptyCatalog = {
  main: Object.fromEntries(
    ["panels", "plugins", "channels", "feeds", "tools", "media", "skins", "images",
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

renderCatalog(emptyCatalog);
fetch("./data/catalog.json", { cache: "no-store" })
  .then((res) => {
    if (!res.ok) throw new Error("Catalog unavailable");
    return res.json();
  })
  .then(renderCatalog)
  .catch((err) => console.error("Online4Tech catalog load failed:", err));
