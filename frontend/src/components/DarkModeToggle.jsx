import { useEffect, useState } from "react";

export default function DarkModeToggle() {
  const [dark, setDark] = useState(
    localStorage.theme === "dark" ||
      (!("theme" in localStorage) &&
        window.matchMedia("(prefers-color-scheme: dark)").matches)
  );

  useEffect(() => {
    if (dark) {
      document.documentElement.classList.add("dark");
      localStorage.theme = "dark";
    } else {
      document.documentElement.classList.remove("dark");
      localStorage.theme = "light";
    }
  }, [dark]);

  return (
    <button
      onClick={() => setDark(!dark)}
      className="px-3 py-1 rounded-md text-sm
                 bg-gray-200 dark:bg-gray-700
                 text-gray-900 dark:text-gray-100
                 hover:bg-gray-300 dark:hover:bg-gray-600
                 transition"
    >
      {dark ? "🌙 Dark" : "☀️ Light"}
    </button>
  );
}
