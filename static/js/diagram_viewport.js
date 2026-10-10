/**
 * Controles compartidos para todos los diagramas SVG de los laboratorios.
 * Ajusta el diagrama completo al cuadro al dibujarse y permite zoom y escala
 * horizontal/vertical independientes sin dependencias externas.
 */
(() => {
  const SELECTOR = 'svg.tree-svg, svg.resource-graph__svg, svg.machine-svg';
  const FIT_HEIGHT = 560;
  const MIN_VIEW_WIDTH = 180;
  const enhanced = new WeakSet();
  const fitters = new WeakMap();
  const axisPreferences = new Map();

  const diagramKey = (svg) => svg.classList.contains('tree-svg')
    ? 'tree'
    : svg.classList.contains('resource-graph__svg')
      ? 'resource'
      : 'machine';

  const getViewBox = (svg) => {
    const raw = (svg.getAttribute('viewBox') || '').trim().split(/[\s,]+/).map(Number);
    if (raw.length === 4 && raw.every(Number.isFinite) && raw[2] > 0 && raw[3] > 0) {
      return {x: raw[0], y: raw[1], width: raw[2], height: raw[3]};
    }
    const width = Number(svg.getAttribute('width')) || 1000;
    const height = Number(svg.getAttribute('height')) || 600;
    return {x: 0, y: 0, width, height};
  };

  const makeControls = () => {
    const bar = document.createElement('section');
    bar.className = 'diagram-viewport-controls';
    bar.setAttribute('aria-label', 'Controles de visualización del diagrama');
    bar.innerHTML = `
      <div class="diagram-viewport-controls__top">
        <strong class="diagram-viewport-controls__title">Vista del diagrama</strong>
        <div class="diagram-viewport-controls__zoom">
          <button type="button" class="ui-button diagram-zoom-out" aria-label="Reducir zoom">−</button>
          <output class="diagram-zoom-value" aria-live="polite">100%</output>
          <button type="button" class="ui-button diagram-zoom-in" aria-label="Aumentar zoom">+</button>
          <button type="button" class="ui-button diagram-fit">Ajustar al cuadro</button>
        </div>
      </div>
      <div class="diagram-viewport-controls__axes">
        <label class="diagram-scale-control">
          <span>Escala horizontal <output class="diagram-scale-x-value">100%</output></span>
          <input class="diagram-scale-x" type="range" min="50" max="200" step="10" value="100" aria-label="Escala horizontal del diagrama">
        </label>
        <label class="diagram-scale-control">
          <span>Escala vertical <output class="diagram-scale-y-value">100%</output></span>
          <input class="diagram-scale-y" type="range" min="50" max="200" step="10" value="100" aria-label="Escala vertical del diagrama">
        </label>
      </div>
      <p class="diagram-viewport-controls__hint">Al cambiar de paso, el diagrama vuelve a encajarse completo en el cuadro. Después puedes ampliar o ajustar cada eje.</p>`;
    return bar;
  };

  function enhance(svg) {
    if (enhanced.has(svg) || !svg.isConnected) return;
    const scroll = svg.parentElement;
    if (!scroll) return;

    enhanced.add(svg);
    scroll.classList.add('diagram-viewport__scroll');
    scroll.setAttribute('tabindex', '0');
    scroll.setAttribute('aria-label', 'Área desplazable del diagrama');
    svg.setAttribute('preserveAspectRatio', 'none');
    svg.style.maxWidth = 'none';
    svg.style.minWidth = '0';
    svg.style.display = 'block';
    svg.style.flex = '0 0 auto';

    const controls = makeControls();
    scroll.insertAdjacentElement('beforebegin', controls);

    const zoomOut = controls.querySelector('.diagram-zoom-out');
    const zoomIn = controls.querySelector('.diagram-zoom-in');
    const fitButton = controls.querySelector('.diagram-fit');
    const zoomValue = controls.querySelector('.diagram-zoom-value');
    const scaleX = controls.querySelector('.diagram-scale-x');
    const scaleY = controls.querySelector('.diagram-scale-y');
    const scaleXValue = controls.querySelector('.diagram-scale-x-value');
    const scaleYValue = controls.querySelector('.diagram-scale-y-value');
    const viewBox = getViewBox(svg);
    const key = diagramKey(svg);
    const preferences = axisPreferences.get(key) || {x: 100, y: 100};
    const state = {zoom: 100, x: preferences.x, y: preferences.y, fit: 1};
    scaleX.value = String(state.x);
    scaleY.value = String(state.y);

    const apply = (reset = false) => {
      if (!svg.isConnected || !scroll.isConnected) return;
      if (reset) {
        state.zoom = 100;
        state.x = 100;
        state.y = 100;
        preferences.x = 100;
        preferences.y = 100;
        axisPreferences.set(key, preferences);
        scaleX.value = '100';
        scaleY.value = '100';
      }

      const style = window.getComputedStyle(scroll);
      const sidePadding = (parseFloat(style.paddingLeft) || 0) + (parseFloat(style.paddingRight) || 0);
      const availableWidth = Math.max(MIN_VIEW_WIDTH, scroll.clientWidth - sidePadding - 18);
      const availableHeight = FIT_HEIGHT;
      // Ajusta la geometría completa considerando los ejes elegidos; el zoom
      // general se aplica después para que el usuario pueda ampliar y desplazar.
      state.fit = Math.min(
        availableWidth / (viewBox.width * (state.x / 100)),
        availableHeight / (viewBox.height * (state.y / 100)),
      );
      if (!Number.isFinite(state.fit) || state.fit <= 0) state.fit = 1;

      const width = Math.max(1, viewBox.width * state.fit * (state.zoom / 100) * (state.x / 100));
      const height = Math.max(1, viewBox.height * state.fit * (state.zoom / 100) * (state.y / 100));
      svg.style.width = `${width}px`;
      svg.style.height = `${height}px`;
      svg.setAttribute('width', String(width));
      svg.setAttribute('height', String(height));
      zoomValue.value = `${state.zoom}%`;
      zoomValue.textContent = `${state.zoom}%`;
      scaleXValue.value = `${state.x}%`;
      scaleXValue.textContent = `${state.x}%`;
      scaleYValue.value = `${state.y}%`;
      scaleYValue.textContent = `${state.y}%`;
      zoomOut.disabled = state.zoom <= 50;
      zoomIn.disabled = state.zoom >= 300;
    };

    zoomOut.addEventListener('click', () => {
      state.zoom = Math.max(50, state.zoom - 25);
      apply();
    });
    zoomIn.addEventListener('click', () => {
      state.zoom = Math.min(300, state.zoom + 25);
      apply();
    });
    fitButton.addEventListener('click', () => apply(true));
    scaleX.addEventListener('input', () => {
      state.x = Number(scaleX.value) || 100;
      preferences.x = state.x;
      axisPreferences.set(key, preferences);
      apply();
    });
    scaleY.addEventListener('input', () => {
      state.y = Number(scaleY.value) || 100;
      preferences.y = state.y;
      axisPreferences.set(key, preferences);
      apply();
    });

    fitters.set(svg, () => apply(false));
    svg.__diagramRefit = () => apply(false);
    apply();
    // Una segunda medición en el siguiente frame cubre los casos en que el panel
    // termina de tomar su ancho después de insertar el SVG.
    requestAnimationFrame(() => apply(false));
  }

  function scan(root = document) {
    if (root instanceof Element && root.matches(SELECTOR)) enhance(root);
    if (root.querySelectorAll) root.querySelectorAll(SELECTOR).forEach(enhance);
  }

  const start = () => {
    scan(document);
    const observer = new MutationObserver((records) => {
      records.forEach((record) => record.addedNodes.forEach((node) => {
        if (node.nodeType === Node.ELEMENT_NODE) scan(node);
      }));
    });
    observer.observe(document.body, {childList: true, subtree: true});
    window.addEventListener('resize', () => {
      document.querySelectorAll(SELECTOR).forEach((svg) => fitters.get(svg)?.());
    }, {passive: true});
  };

  window.DiagramViewport = {refresh: scan};
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start, {once: true});
  else start();
})();
