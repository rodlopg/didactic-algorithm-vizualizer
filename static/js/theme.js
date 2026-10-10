(() => {
  const STORAGE_THEME = 'dav-theme-mode';
  const STORAGE_ACCENT = 'dav-accent-mode';
  const validThemes = new Set(['system', 'light', 'dark']);
  const validAccents = new Set(['red', 'cobalt', 'orange']);

  const storedTheme = localStorage.getItem(STORAGE_THEME);
  const storedAccent = localStorage.getItem(STORAGE_ACCENT);
  const theme = validThemes.has(storedTheme) ? storedTheme : 'system';
  const accent = validAccents.has(storedAccent) ? storedAccent : 'red';
  const media = window.matchMedia('(prefers-color-scheme: dark)');

  function applyTheme(mode) {
    const effective = mode === 'system' ? (media.matches ? 'dark' : 'light') : mode;
    document.documentElement.dataset.theme = effective;
    document.documentElement.dataset.themeMode = mode;
  }

  function applyAccent(value) {
    document.documentElement.dataset.accent = value;
  }

  applyTheme(theme);
  applyAccent(accent);

  window.DAVTheme = {
    getTheme() { return localStorage.getItem(STORAGE_THEME) || 'system'; },
    getAccent() { return localStorage.getItem(STORAGE_ACCENT) || 'red'; },
    setTheme(mode) {
      const next = validThemes.has(mode) ? mode : 'system';
      localStorage.setItem(STORAGE_THEME, next);
      applyTheme(next);
    },
    setAccent(value) {
      const next = validAccents.has(value) ? value : 'red';
      localStorage.setItem(STORAGE_ACCENT, next);
      applyAccent(next);
    },
    reset() {
      localStorage.removeItem(STORAGE_THEME);
      localStorage.removeItem(STORAGE_ACCENT);
      applyTheme('system');
      applyAccent('red');
    },
    toggle() {
      const current = document.documentElement.dataset.theme;
      this.setTheme(current === 'dark' ? 'light' : 'dark');
    },
  };

  media.addEventListener?.('change', () => {
    if ((localStorage.getItem(STORAGE_THEME) || 'system') === 'system') applyTheme('system');
  });
})();
