(() => {
  const form = document.getElementById('machine-form');
  const renderer = new window.MachineReplacementRenderer(document.getElementById('machine-canvas'));
  const preview = document.getElementById('machine-problem-data');
  const previousButton = document.getElementById('machine-previous-button');
  const nextButton = document.getElementById('machine-next-button');
  const playButton = document.getElementById('machine-play-button');
  const pauseButton = document.getElementById('machine-pause-button');
  const resetButton = document.getElementById('machine-reset-button');
  const speedInput = document.getElementById('machine-speed-input');
  const speedOutput = document.getElementById('machine-speed-output');
  const statusLine = document.getElementById('machine-status-line');
  const stepCounter = document.getElementById('machine-step-counter');
  const sandboxMessage = document.getElementById('machine-sandbox-message');
  const phaseValue = document.getElementById('machine-phase-value');
  const titleValue = document.getElementById('machine-title-value');
  const formulaValue = document.getElementById('machine-formula-value');
  const whyValue = document.getElementById('machine-why-value');
  const variablesBody = document.getElementById('machine-variables-body');

  let steps = [];
  let currentIndex = -1;
  let timer = null;

  function parseInput(id) {
    return JSON.parse(document.getElementById(id).value);
  }

  function readData() {
    return {
      horizonte: Number(document.getElementById('machine-horizon-input').value),
      edad_inicial: Number(document.getElementById('machine-initial-age-input').value),
      edad_maxima: Number(document.getElementById('machine-max-age-input').value),
      costo_adquisicion: Number(document.getElementById('machine-purchase-input').value),
      ingresos: parseInput('machine-income-input'),
      costos_operacion: parseInput('machine-operation-input'),
      valores_desecho: parseInput('machine-residual-input'),
    };
  }

  function updatePreview() {
    try {
      const data = readData();
      window.ProblemData.machine(preview, data);
    } catch (_error) {
      window.ProblemData.machine(preview, {
        horizonte: document.getElementById('machine-horizon-input').value,
        edad_inicial: document.getElementById('machine-initial-age-input').value,
        edad_maxima: document.getElementById('machine-max-age-input').value,
        costo_adquisicion: document.getElementById('machine-purchase-input').value,
        ingresos: [], costos_operacion: [], valores_desecho: [],
      });
    }
  }

  function setPlaying(playing) {
    if (!playing && timer) { clearTimeout(timer); timer = null; }
    playButton.setAttribute('aria-pressed', playing ? 'true' : 'false');
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
    statusLine.textContent = 'Construyendo las etapas del problema…';
    try {
      const data = readData();
      const response = await fetch('/api/machine-replacement/steps', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data),
      });
      const payload = await response.json();
      if (!response.ok || !payload.ok) throw new Error(payload.mensaje || 'No se pudo construir el recorrido.');
      steps = payload.pasos || [];
      updatePreview();
      statusLine.textContent = `Listo: ${steps.length} pasos disponibles.`;
      resetPlayback();
    } catch (error) {
      steps = [];
      resetPlayback();
      sandboxMessage.hidden = false;
      sandboxMessage.textContent = error.message || 'No pudimos procesar los datos. Revisa las listas por edad.';
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
  form.querySelectorAll('input, textarea').forEach((input) => input.addEventListener('input', updatePreview));

  previousButton.disabled = true;
  nextButton.disabled = true;
  updatePreview();

  function escapeHtml(value) {
    return String(value).replace(/[&<>"']/g, (character) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[character]));
  }
})();
