(() => {
  const drawer = document.getElementById('sys-nav-drawer');
  const overlay = document.getElementById('sys-overlay');
  const trigger = document.getElementById('nav-trigger');
  const close = document.getElementById('nav-close');
  const quickToggle = document.getElementById('theme-quick-toggle');
  const themeMode = document.getElementById('theme-mode');
  const accentMode = document.getElementById('accent-mode');
  const appearanceReset = document.getElementById('appearance-reset');

  const closeNav = (restoreFocus = false) => {
    if (!drawer) return;
    drawer.classList.remove('is-active');
    overlay?.classList.remove('is-active');
    drawer.setAttribute('aria-hidden', 'true');
    trigger?.setAttribute('aria-expanded', 'false');
    if (restoreFocus) trigger?.focus();
  };

  const openNav = () => {
    if (!drawer) return;
    drawer.classList.add('is-active');
    overlay?.classList.add('is-active');
    drawer.setAttribute('aria-hidden', 'false');
    trigger?.setAttribute('aria-expanded', 'true');
    close?.focus();
  };

  trigger?.addEventListener('click', openNav);
  close?.addEventListener('click', () => closeNav(true));
  overlay?.addEventListener('click', () => closeNav(true));
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') closeNav(true);
  });

  if (window.DAVTheme) {
    if (themeMode) themeMode.value = DAVTheme.getTheme();
    if (accentMode) accentMode.value = DAVTheme.getAccent();
    themeMode?.addEventListener('change', (event) => DAVTheme.setTheme(event.target.value));
    accentMode?.addEventListener('change', (event) => DAVTheme.setAccent(event.target.value));
    appearanceReset?.addEventListener('click', () => {
      DAVTheme.reset();
      if (themeMode) themeMode.value = DAVTheme.getTheme();
      if (accentMode) accentMode.value = DAVTheme.getAccent();
    });
    quickToggle?.addEventListener('click', () => {
      DAVTheme.toggle();
      if (themeMode) themeMode.value = DAVTheme.getTheme();
    });

    const updateQuickLabel = () => {
      const dark = document.documentElement.dataset.theme === 'dark';
      if (quickToggle) quickToggle.textContent = dark ? 'CLARO' : 'OSCURO';
    };
    updateQuickLabel();
    new MutationObserver(updateQuickLabel).observe(document.documentElement, {attributes: true, attributeFilter: ['data-theme']});
  }
})();
