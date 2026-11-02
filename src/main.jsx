import React from "react";
import { createRoot } from "react-dom/client";
import ControlCenter from "./pages/ControlCenter.jsx";
import data from "./control-center-sample-data.json";
import "./styles.css";

createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <ControlCenter data={data} />
  </React.StrictMode>
);
