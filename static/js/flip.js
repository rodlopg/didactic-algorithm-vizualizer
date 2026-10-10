(() => {
  const trigger = document.getElementById('nav-trigger');
  const closeBtn = document.getElementById('nav-close');
  const drawer = document.getElementById('sys-nav-drawer');
  const overlay = document.getElementById('sys-overlay');
  if (!trigger || !closeBtn || !drawer || !overlay) return;

  function abrir() {
    const firstRect = trigger.getBoundingClientRect();
    drawer.classList.add('is-active');
    overlay.classList.add('is-active');
    drawer.setAttribute('aria-hidden', 'false');
    overlay.setAttribute('aria-hidden', 'false');
    trigger.setAttribute('aria-expanded', 'true');

    const lastRect = drawer.getBoundingClientRect();
    const deltaX = firstRect.left - lastRect.left;
    const deltaY = firstRect.top - lastRect.top;
    const scaleX = firstRect.width / lastRect.width;
    const scaleY = firstRect.height / lastRect.height;
    drawer.style.transform = `translate(${deltaX}px, ${deltaY}px) scale(${scaleX}, ${scaleY})`;
    drawer.style.transition = 'none';

    requestAnimationFrame(() => {
      drawer.getBoundingClientRect();
      drawer.style.transition = 'transform 0.4s cubic-bezier(0.2, 0.8, 0.2, 1), opacity 0.2s cubic-bezier(0.4, 0, 0.2, 1)';
      drawer.style.transform = 'none';
      closeBtn.focus();
    });
  }

  function cerrar() {
    drawer.classList.remove('is-active');
    overlay.classList.remove('is-active');
    drawer.setAttribute('aria-hidden', 'true');
    overlay.setAttribute('aria-hidden', 'true');
    trigger.setAttribute('aria-expanded', 'false');
    window.setTimeout(() => {
      drawer.style.transform = '';
      drawer.style.transition = '';
    }, 400);
    trigger.focus();
  }

  trigger.addEventListener('click', abrir);
  closeBtn.addEventListener('click', cerrar);
  overlay.addEventListener('click', cerrar);
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && drawer.classList.contains('is-active')) cerrar();
  });
})();
