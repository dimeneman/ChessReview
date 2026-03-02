import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App.jsx";

// Debug alert to confirm JS execution
window.alert('React App Starting...');

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <div className="min-h-screen bg-gray-100 dark:bg-[#1e1e1e] transition-colors duration-300">
      <App />
    </div>
  </StrictMode>
);
