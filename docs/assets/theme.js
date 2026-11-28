(() => {
  const key = "datazo-theme";
  const root = document.documentElement;
  const saved = localStorage.getItem(key);
  const initial = saved || "light";

  function setTheme(theme) {
    root.dataset.theme = theme;
    const button = document.querySelector("[data-theme-toggle]");
    if (button) {
      button.textContent = theme === "dark" ? "Modo claro" : "Modo oscuro";
      button.setAttribute("aria-label", theme === "dark" ? "Cambiar a modo claro" : "Cambiar a modo oscuro");
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
