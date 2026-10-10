(() => {
  const form = document.getElementById('knapsack-form');
  const renderer = new window.KnapsackRenderer(document.getElementById('knapsack-canvas'));
  const previousButton = document.getElementById('knap-previous-button');
  const nextButton = document.getElementById('knap-next-button');
  const playButton = document.getElementById('knap-play-button');
  const pauseButton = document.getElementById('knap-pause-button');
  const resetButton = document.getElementById('knap-reset-button');
  const speedInput = document.getElementById('knap-speed-input');
  const speedOutput = document.getElementById('knap-speed-output');
  const statusLine = document.getElementById('knap-status-line');
  const stepCounter = document.getElementById('knap-step-counter');
  const sandboxMessage = document.getElementById('knap-sandbox-message');
  const phaseValue = document.getElementById('knap-phase-value');
  const titleValue = document.getElementById('knap-title-value');
  const formulaValue = document.getElementById('knap-formula-value');
  const whyValue = document.getElementById('knap-why-value');
  const variablesBody = document.getElementById('knap-variables-body');
  const problemPreview = document.getElementById('knap-problem-data');

  let steps = [];
  let currentIndex = -1;
  let timer = null;

  function setPlaying(playing) {
    if (!playing && timer) {
      clearTimeout(timer);
      timer = null;
    }
    playButton.setAttribute('aria-pressed', playing ? 'true' : 'false');
  }

  function updateProblemPreview() {
    try {
      const benefits = JSON.parse(document.getElementById('benefits-input').value);
      const weights = JSON.parse(document.getElementById('weights-input').value);
      const capacity = Number(document.getElementById('capacity-input').value);
      window.ProblemData.knapsack(problemPreview, benefits, weights, capacity);
    } catch (_error) {
      problemPreview.innerHTML = '<section class="problem-data-card"><p class="problem-data__empty">Escribe listas JSON válidas para visualizar los objetos aquí.</p></section>';
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
      renderer.render(null);
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
      timer = window.setTimeout(tick, (1.8 / Number(speedInput.value)) * 1000);
    };
    timer = window.setTimeout(tick, 0);
  }

  async function construir(event) {
    event.preventDefault();
    setPlaying(false);
    sandboxMessage.hidden = true;
    statusLine.textContent = 'Construyendo la tabla de programación dinámica…';
    try {
      const beneficios = JSON.parse(document.getElementById('benefits-input').value);
      const pesos = JSON.parse(document.getElementById('weights-input').value);
      const capacidad = Number(document.getElementById('capacity-input').value);
      const response = await fetch('/api/knapsack/steps', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({beneficios, pesos, capacidad}),
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
      sandboxMessage.textContent = error.message || 'No pudimos procesar los datos. Revisa que ambas listas tengan el mismo número de elementos.';
      statusLine.textContent = 'Necesitamos ajustar los datos antes de continuar.';
    }
  }

  previousButton.addEventListener('click', () => showStep(currentIndex - 1));
  nextButton.addEventListener('click', () => showStep(currentIndex + 1));
  playButton.addEventListener('click', play);
  pauseButton.addEventListener('click', () => setPlaying(false));
  resetButton.addEventListener('click', resetPlayback);
  speedInput.addEventListener('input', () => {
    speedOutput.value = `${Number(speedInput.value).toFixed(1)}×`;
    speedOutput.textContent = `${Number(speedInput.value).toFixed(1)}×`;
  });
  form.addEventListener('submit', construir);
  form.querySelectorAll('input, textarea').forEach((input) => input.addEventListener('input', updateProblemPreview));
  updateProblemPreview();

  previousButton.disabled = true;
  nextButton.disabled = true;

  function escapeHtml(value) {
    return String(value).replace(/[&<>"']/g, (character) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[character]));
  }
})();
