import { useEffect, useState } from "react";

const STORAGE_KEY = "scyt_theme";

type ThemeMode = "dark" | "light";

export function ThemeToggle() {
  const [theme, setTheme] = useState<ThemeMode>(() => {
    const stored = window.localStorage.getItem(STORAGE_KEY);
    return stored === "light" ? "light" : "dark";
  });

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    window.localStorage.setItem(STORAGE_KEY, theme);
  }, [theme]);

  return (
    <button
      type="button"
      className="app-nav-theme-btn"
      onClick={() => setTheme((prev) => (prev === "dark" ? "light" : "dark"))}
      aria-label="Toggle theme"
    >
      <span className="material-symbols-outlined" aria-hidden="true">
        {theme === "dark" ? "dark_mode" : "light_mode"}
      </span>
    </button>
  );
}
