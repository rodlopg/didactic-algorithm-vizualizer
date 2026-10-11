(() => {
  const form = document.getElementById('tree-form');
  const treeInput = document.getElementById('tree-json-input');
  const renderer = new window.TreeRenderer(document.getElementById('tree-canvas'));
  const previousButton = document.getElementById('previous-button');
  const nextButton = document.getElementById('next-button');
  const playButton = document.getElementById('play-button');
  const pauseButton = document.getElementById('pause-button');
  const resetButton = document.getElementById('reset-button');
  const speedInput = document.getElementById('speed-input');
  const speedOutput = document.getElementById('speed-output');
  const statusLine = document.getElementById('status-line');
  const stepCounter = document.getElementById('step-counter');
  const sandboxMessage = document.getElementById('sandbox-message');
  const phaseValue = document.getElementById('phase-value');
  const titleValue = document.getElementById('title-value');
  const formulaValue = document.getElementById('formula-value');
  const whyValue = document.getElementById('why-value');
  const variablesBody = document.getElementById('variables-body');
  const problemPreview = document.getElementById('tree-problem-data');
  const basicButton = document.getElementById('basic-example-button');
  const multilevelButton = document.getElementById('multilevel-example-button');

  const MULTILEVEL_TREE = {
    type: 'decision',
    label: 'Elegir presupuesto de la primera temporada',
    options: [
      {
        label: 'Bajo presupuesto',
        next: {
          type: 'chance', label: 'Resultado de la primera temporada · bajo',
          events: [
            { label: 'Éxito', probability: 0.6, payoff: 5, next: {
              type: 'decision', label: 'Presupuesto de la segunda temporada · tras éxito bajo',
              options: [
                { label: 'Bajo presupuesto', next: { type: 'chance', label: 'Resultado de temporada 2 · bajo', events: [
                  { label: 'Éxito', probability: 0.65, payoff: 6 },
                  { label: 'Fracaso', probability: 0.35, payoff: -1.4 },
                ] } },
                { label: 'Alto presupuesto', next: { type: 'chance', label: 'Resultado de temporada 2 · alto', events: [
                  { label: 'Éxito', probability: 0.9, payoff: 5.5 },
                  { label: 'Fracaso', probability: 0.1, payoff: -2.2 },
                ] } },
              ],
            } },
            // El pago del fracaso (-1) se suma al pago terminal de cancelar (-0.1).
            { label: 'Fracaso', probability: 0.4, payoff: -1, next: { type: 'terminal', label: 'Cancelar la serie', payoff: -0.1 } },
          ],
        },
      },
      {
        label: 'Alto presupuesto',
        next: {
          type: 'chance', label: 'Resultado de la primera temporada · alto',
          events: [
            { label: 'Éxito', probability: 0.8, payoff: 4, next: {
              type: 'decision', label: 'Presupuesto de la segunda temporada · tras éxito alto',
              options: [
                { label: 'Bajo presupuesto', next: { type: 'chance', label: 'Resultado de temporada 2 · bajo', events: [
                  { label: 'Éxito', probability: 0.55, payoff: 7 },
                  { label: 'Fracaso', probability: 0.45, payoff: -1.2 },
                ] } },
                { label: 'Alto presupuesto', next: { type: 'chance', label: 'Resultado de temporada 2 · alto', events: [
                  { label: 'Éxito', probability: 0.95, payoff: 4.5 },
                  { label: 'Fracaso', probability: 0.05, payoff: -2.5 },
                ] } },
              ],
            } },
            // El pago del fracaso (-2) se suma al pago terminal de cancelar (-0.3).
            { label: 'Fracaso', probability: 0.2, payoff: -2, next: { type: 'terminal', label: 'Cancelar la serie', payoff: -0.3 } },
          ],
        },
      },
    ],
  };

  let steps = [];
  let currentIndex = -1;
  let timer = null;
  const originalTreeText = treeInput.value;

  function setPlaying(playing) {
    if (!playing && timer !== null) {
      clearTimeout(timer);
      timer = null;
    }
    playButton.setAttribute('aria-pressed', playing ? 'true' : 'false');
  }

  function updateProblemPreview() {
    try {
      const tree = JSON.parse(treeInput.value);
      window.ProblemData.decisionTree(problemPreview, tree);
    } catch (_error) {
      problemPreview.innerHTML = '<section class="problem-data-card"><p class="problem-data__empty">No podemos preparar la ficha hasta que el JSON sea válido. El árbol anterior no se modifica.</p></section>';
    }
  }

  function renderVariables(variables) {
    const rows = Object.entries(variables || {}).map(([key, value]) => {
      const display = typeof value === 'object' ? JSON.stringify(value, null, 0) : String(value);
      return `<tr><td>${escapeHtml(key.replaceAll('_', ' '))}</td><td>${escapeHtml(display)}</td></tr>`;
    }).join('');
    variablesBody.innerHTML = rows || '<tr><td colspan="2">—</td></tr>';
  }

  function showStep(index) {
    if (!steps.length) return;
    currentIndex = Math.min(Math.max(index, 0), steps.length - 1);
    const step = steps[currentIndex];
    renderer.render(step.estado_visual);
    stepCounter.textContent = `Paso ${step.paso} / ${step.total_pasos}`;
    phaseValue.textContent = step.fase;
    titleValue.textContent = step.titulo;
    formulaValue.textContent = step.formula;
    whyValue.textContent = step.explicacion;
    renderVariables(step.variables);
    statusLine.textContent = `${step.fase}: ${step.titulo}`;
    previousButton.disabled = currentIndex === 0;
    nextButton.disabled = currentIndex === steps.length - 1;
  }

  function resetPlayback() {
    setPlaying(false);
    currentIndex = -1;
    if (steps.length) showStep(0);
    else {
      renderer.render(null);
      stepCounter.textContent = 'Paso 0 / 0';
      phaseValue.textContent = 'Esperando una ejecución.';
      titleValue.textContent = 'Todavía no hay un paso activo.';
      formulaValue.textContent = '—';
      whyValue.textContent = 'La explicación aparecerá aquí cuando avances.';
      variablesBody.innerHTML = '<tr><td colspan="2">—</td></tr>';
      previousButton.disabled = true;
      nextButton.disabled = true;
    }
  }

  function play() {
    if (!steps.length) return;
    setPlaying(false);
    if (currentIndex >= steps.length - 1) currentIndex = -1;
    playButton.setAttribute('aria-pressed', 'true');
    const tick = () => {
      if (currentIndex >= steps.length - 1) {
        setPlaying(false);
        return;
      }
      showStep(currentIndex + 1);
      timer = window.setTimeout(tick, 1800 / Number(speedInput.value));
    };
    timer = window.setTimeout(tick, 0);
  }

  async function construir(event) {
    event.preventDefault();
    setPlaying(false);
    sandboxMessage.hidden = true;
    statusLine.textContent = 'Validando probabilidades, pagos y estructura del árbol…';
    try {
      const tree = JSON.parse(treeInput.value);
      const response = await fetch('/api/decision-tree/steps', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({tree}),
      });
      const payload = await response.json();
      if (!response.ok || !payload.ok) throw new Error(payload.mensaje || 'No se pudo construir el árbol.');
      steps = payload.pasos || [];
      updateProblemPreview();
      statusLine.textContent = `Árbol válido: ${steps.length} pasos disponibles.`;
      resetPlayback();
    } catch (error) {
      steps = [];
      resetPlayback();
      sandboxMessage.hidden = false;
      sandboxMessage.textContent = error instanceof SyntaxError
        ? 'El contenido no es JSON válido. Revisa comas, llaves y comillas; usa uno de los ejemplos para recuperar una estructura válida.'
        : (error.message || 'No pudimos procesar el árbol. Revisa que cada nodo de azar sume probabilidades de 1.');
      statusLine.textContent = 'Corrige los datos para poder resolver el árbol.';
    }
  }

  function loadTree(treeText) {
    setPlaying(false);
    treeInput.value = treeText;
    updateProblemPreview();
    sandboxMessage.hidden = true;
    statusLine.textContent = 'Ejemplo cargado; pulsa «Resolver árbol paso a paso». ';
  }

  previousButton.addEventListener('click', () => showStep(currentIndex - 1));
  nextButton.addEventListener('click', () => showStep(currentIndex + 1));
  playButton.addEventListener('click', play);
  pauseButton.addEventListener('click', () => setPlaying(false));
  resetButton.addEventListener('click', () => { currentIndex = -1; resetPlayback(); });
  speedInput.addEventListener('input', () => {
    speedOutput.value = `${Number(speedInput.value).toFixed(1)}×`;
    speedOutput.textContent = `${Number(speedInput.value).toFixed(1)}×`;
  });
  basicButton.addEventListener('click', () => loadTree(originalTreeText));
  multilevelButton.addEventListener('click', () => loadTree(JSON.stringify(MULTILEVEL_TREE, null, 2)));
  treeInput.addEventListener('input', updateProblemPreview);
  form.addEventListener('submit', construir);
  window.addEventListener('beforeunload', () => setPlaying(false));
  updateProblemPreview();
  previousButton.disabled = true;
  nextButton.disabled = true;

  function escapeHtml(value) {
    return String(value).replace(/[&<>"']/g, (character) => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[character]));
  }
})();
