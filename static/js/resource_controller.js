(() => {
  const form = document.getElementById('resource-form');
  const renderer = new window.ResourceRenderer(document.getElementById('resource-canvas'));
  const previousButton = document.getElementById('res-previous-button');
  const nextButton = document.getElementById('res-next-button');
  const playButton = document.getElementById('res-play-button');
  const pauseButton = document.getElementById('res-pause-button');
  const resetButton = document.getElementById('res-reset-button');
  const speedInput = document.getElementById('res-speed-input');
  const speedOutput = document.getElementById('res-speed-output');
  const statusLine = document.getElementById('res-status-line');
  const stepCounter = document.getElementById('res-step-counter');
  const sandboxMessage = document.getElementById('res-sandbox-message');
  const phaseValue = document.getElementById('res-phase-value');
  const titleValue = document.getElementById('res-title-value');
  const formulaValue = document.getElementById('res-formula-value');
  const whyValue = document.getElementById('res-why-value');
  const variablesBody = document.getElementById('res-variables-body');
  const problemPreview = document.getElementById('resource-problem-data');

  let steps = [];
  let currentIndex = -1;
  let timer = null;

  function setPlaying(playing) {
    if (!playing && timer) { clearTimeout(timer); timer = null; }
    playButton.setAttribute('aria-pressed', playing ? 'true' : 'false');
  }

  function updateProblemPreview() {
    try {
      const stages = document.getElementById('resource-stages-input').value.split(',').map((x) => x.trim()).filter(Boolean);
      const performance = JSON.parse(document.getElementById('resource-table-input').value);
      const brigades = Number(document.getElementById('resource-total-input').value);
      window.ProblemData.resource(problemPreview, brigades, stages, performance);
    } catch (_error) {
      problemPreview.innerHTML = '<section class="problem-data-card"><p class="problem-data__empty">Escribe una matriz JSON válida para visualizar los rendimientos aquí.</p></section>';
    }
  }

  function renderVariables(variables) {
    variablesBody.innerHTML = Object.entries(variables || {}).map(([key, value]) => {
      const display = typeof value === 'object' ? JSON.stringify(value) : String(value);
      return `<tr><td>${escapeHtml(key)}</td><td>${escapeHtml(display)}</td></tr>`;
    }).join('') || '<tr><td colspan="2">—</td></tr>';
  }

  function showStep(index) {
    if (!steps.length) return;
    currentIndex = Math.min(Math.max(index, 0), steps.length - 1);
    const step = steps[currentIndex];
    renderer.render(step.estado_visual, step.variables);
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
      renderer.render(null);
    }
  }

  function play() {
    if (!steps.length) return;
    if (currentIndex >= steps.length - 1) currentIndex = -1;
    setPlaying(true);
    const tick = () => {
      if (!timer) return;
      if (currentIndex >= steps.length - 1) { setPlaying(false); return; }
      showStep(currentIndex + 1);
      timer = window.setTimeout(tick, (1.8 / Number(speedInput.value)) * 1000);
    };
    timer = window.setTimeout(tick, 0);
  }

  async function construir(event) {
    event.preventDefault();
    setPlaying(false);
    sandboxMessage.hidden = true;
    statusLine.textContent = 'Construyendo la matriz de programación dinámica…';
    try {
      const etapas = document.getElementById('resource-stages-input').value.split(',').map((x) => x.trim()).filter(Boolean);
      const rendimientos = JSON.parse(document.getElementById('resource-table-input').value);
      const brigadas = Number(document.getElementById('resource-total-input').value);
      const response = await fetch('/api/resource-allocation/steps', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({brigadas, etapas, rendimientos}),
      });
      const payload = await response.json();
      if (!response.ok || !payload.ok) throw new Error(payload.mensaje || 'No se pudo construir el recorrido.');
      steps = payload.pasos || [];
      updateProblemPreview();
      statusLine.textContent = `Listo: ${steps.length} pasos disponibles.`;
      resetPlayback();
    } catch (error) {
      steps = [];
      resetPlayback();
      sandboxMessage.hidden = false;
      sandboxMessage.textContent = error.message || 'No pudimos procesar la matriz. Revisa etapas y valores.';
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
  form.querySelectorAll('input, textarea').forEach((input) => input.addEventListener('input', updateProblemPreview));
  updateProblemPreview();
  previousButton.disabled = true;
  nextButton.disabled = true;

  function escapeHtml(value) {
    return String(value).replace(/[&<>"']/g, (character) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[character]));
  }
})();
