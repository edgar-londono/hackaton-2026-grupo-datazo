(() => {
  const key = "datazo-theme";
  const root = document.documentElement;
  const saved = localStorage.getItem(key);
  const initial = saved || "light";

  function setTheme(theme) {
    root.dataset.theme = theme;
    const button = document.querySelector("[data-theme-toggle]");
    if (button) {
      const nextTheme = theme === "dark" ? "light" : "dark";
      const label = nextTheme === "light" ? "Cambiar a modo claro" : "Cambiar a modo oscuro";
      button.textContent = nextTheme === "light" ? "☀" : "☾";
      button.setAttribute("aria-label", label);
      button.title = label;
      button.setAttribute("aria-pressed", String(theme === "dark"));
    }
  }

  setTheme(initial);
  document.addEventListener("click", (event) => {
    if (!event.target.closest("[data-theme-toggle]")) return;
    const next = root.dataset.theme === "dark" ? "light" : "dark";
    localStorage.setItem(key, next);
    setTheme(next);
  });
})();
