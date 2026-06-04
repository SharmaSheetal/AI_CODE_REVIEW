/**
 * main.jsx — React entry point.
 * Mounts the App component into the #root div in index.html.
 * StrictMode helps catch bugs by rendering components twice in development.
 */

import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App.jsx";

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <App />
  </StrictMode>
);
