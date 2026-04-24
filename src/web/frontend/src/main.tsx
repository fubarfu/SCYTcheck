import React from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import "./styles/theme.css";
import "./styles/app.css";

const element = document.getElementById("root");
if (!element) {
  throw new Error("Root element #root was not found");
}

createRoot(element).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
