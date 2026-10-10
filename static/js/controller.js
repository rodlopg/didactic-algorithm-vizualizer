(() => {
  const form = document.getElementById('tree-form');
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

  let steps = [];
  let currentIndex = -1;
  let timer = null;

  function setPlaying(playing) {
    if (playing && timer) return;
    if (!playing && timer) {
      clearTimeout(timer);
      timer = null;
    }
    playButton.setAttribute('aria-pressed', playing ? 'true' : 'false');
  }

  function updateProblemPreview() {
    try {
      const dataset = JSON.parse(document.getElementById('dataset-input').value);
      window.ProblemData.tree(
        problemPreview,
        dataset,
        document.getElementById('target-input').value.trim() || 'Jugar',
        document.getElementById('criterion-select').value,
        Number(document.getElementById('depth-input').value),
      );
    } catch (_error) {
      problemPreview.innerHTML = '<section class="problem-data-card"><p class="problem-data__empty">Escribe un JSON válido para visualizar los datos del problema aquí.</p></section>';
    }
  }

  function renderVariables(variables) {
    const rows = Object.entries(variables || {}).map(([key, value]) => {
      const display = typeof value === 'object' ? JSON.stringify(value, null, 0) : String(value);
      return `<tr><td>${escapeHtml(key)}</td><td>${escapeHtml(display)}</td></tr>`;
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
      stepCounter.textContent = 'Paso 0 / 0';
      phaseValue.textContent = 'Esperando una ejecución.';
      titleValue.textContent = 'Todavía no hay un paso activo.';
      formulaValue.textContent = '—';
      whyValue.textContent = 'La explicación aparecerá aquí cuando avances.';
      variablesBody.innerHTML = '<tr><td colspan="2">—</td></tr>';
    }
  }

  function play() {
    if (!steps.length) return;
    if (currentIndex >= steps.length - 1) currentIndex = -1;
    setPlaying(true);
    const tick = () => {
      if (!timer) return;
      if (currentIndex >= steps.length - 1) {
        setPlaying(false);
        return;
      }
      showStep(currentIndex + 1);
      const seconds = 1.8 / Number(speedInput.value);
      timer = window.setTimeout(tick, seconds * 1000);
    };
    timer = window.setTimeout(tick, 0);
  }

  async function construir(event) {
    event.preventDefault();
    setPlaying(false);
    sandboxMessage.hidden = true;
    statusLine.textContent = 'Construyendo el recorrido didáctico…';
    try {
      const dataset = JSON.parse(document.getElementById('dataset-input').value);
      const response = await fetch('/api/decision-tree/steps', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          dataset,
          target: document.getElementById('target-input').value.trim() || 'Jugar',
          criterion: document.getElementById('criterion-select').value,
          max_depth: Number(document.getElementById('depth-input').value),
          sample_index: Number(document.getElementById('sample-input').value),
        }),
      });
      const payload = await response.json();
      if (!response.ok || !payload.ok) throw new Error(payload.mensaje || 'No se pudo construir el árbol.');
      steps = payload.pasos || [];
      updateProblemPreview();
      statusLine.textContent = `Listo: ${steps.length} pasos disponibles.`;
      resetPlayback();
    } catch (error) {
      steps = [];
      resetPlayback();
      sandboxMessage.hidden = false;
      sandboxMessage.textContent = error instanceof SyntaxError
        ? 'Los datos no están escritos como JSON válido. Corrige la estructura y vuelve a probar; el árbol seguirá intacto.'
        : (error.message || 'No pudimos procesar los datos. Prueba con unas pocas filas sencillas.');
      statusLine.textContent = 'Necesitamos ajustar los datos antes de continuar.';
    }
  }

  previousButton.addEventListener('click', () => showStep(currentIndex - 1));
  nextButton.addEventListener('click', () => showStep(currentIndex + 1));
  playButton.addEventListener('click', play);
  pauseButton.addEventListener('click', () => setPlaying(false));
  resetButton.addEventListener('click', resetPlayback);
  speedInput.addEventListener('input', () => { speedOutput.value = `${Number(speedInput.value).toFixed(1)}×`; speedOutput.textContent = `${Number(speedInput.value).toFixed(1)}×`; });
  form.addEventListener('submit', construir);
  form.querySelectorAll('input, select, textarea').forEach((input) => input.addEventListener('input', updateProblemPreview));
  updateProblemPreview();
  window.addEventListener('beforeunload', () => setPlaying(false));

  previousButton.disabled = true;
  nextButton.disabled = true;
  pauseButton.addEventListener('click', () => { timer = null; });

  function escapeHtml(value) {
    return String(value).replace(/[&<>"']/g, (character) => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[character]));
  }
})();
