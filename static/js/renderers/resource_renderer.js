window.ResourceRenderer = class ResourceRenderer {
  constructor(container) {
    this.container = container;
    this.graphRenderer = window.ResourceGraphRenderer
      ? new window.ResourceGraphRenderer(container)
      : null;
  }

  render(state, variables = {}) {
    if (!state || !state.etapas || !state.dp) {
      this.container.innerHTML = '<p class="empty-state">No hay matriz visible todavía.</p>';
      return;
    }

    const activeStage = Number.isInteger(state.etapa_activa) ? state.etapa_activa : -1;
    const activeState = Number.isInteger(state.estado_activo) ? state.estado_activo : -1;
    const selections = state.seleccionados || {};

    const headers = Array.from({length: state.brigadas + 1}, (_, s) =>
      `<th class="resource-head ${s === activeState ? 'is-active' : ''}" scope="col">${s}</th>`
    ).join('');

    const rows = state.etapas.map((stage, i) => {
      const rowClass = i === activeStage ? 'is-active-row' : '';
      const cells = state.dp[i].map((value, s) => {
        const focus = i === activeStage && s === activeState;
        const classes = [
          'resource-cell',
          value !== null && value !== undefined ? 'is-calculated' : '',
          focus ? 'is-focus-cell' : '',
        ].filter(Boolean).join(' ');
        const decision = state.decisiones_optimas?.[i]?.[s];
        return `<td class="${classes}">${value === null || value === undefined ? '—' : this.format(value)}${decision !== null && decision !== undefined ? `<span class="cell-note">x=${decision}</span>` : ''}</td>`;
      }).join('');
      const stageDecision = selections[String(i + 1)];
      return `<tr class="${rowClass}"><th scope="row">${this.escape(stage)}${stageDecision !== undefined ? `<span class="row-note">x=${stageDecision}</span>` : ''}</th>${cells}</tr>`;
    }).join('');

    const path = Array.isArray(state.backtracking) ? state.backtracking : [];
    const pathLine = path.length
      ? `<div class="resource-path"><strong>Política reconstruida:</strong> ${path.map(p => `${this.escape(p.nombre_etapa)} = ${p.brigadas_asignadas}`).join(' → ')}</div>`
      : '';

    this.container.innerHTML = `
      <div class="matrix-meta">
        <span class="matrix-badge">PROGRAMACIÓN DINÁMICA</span>
        <span>Filas = etapas · Columnas = brigadas disponibles · x = brigadas asignadas</span>
      </div>
      <div class="table-scroll">
        <table class="resource-matrix" aria-label="Matriz de asignación de recursos">
          <thead><tr><th scope="col">Etapa / Estado</th>${headers}</tr></thead>
          <tbody>${rows}</tbody>
        </table>
      </div>
      ${pathLine}
      <div id="resource-graph-target" class="resource-graph-target"></div>
      <p class="matrix-note">La tabla muestra los valores óptimos de cada estado; el diagrama inferior muestra todas las transiciones factibles y hace visible la decisión que corresponde al paso actual.</p>
    `;

    if (this.graphRenderer) {
      this.graphRenderer.render({...state, ...{candidatos_evaluados: variables.candidatos_evaluados || []}}, document.getElementById('resource-graph-target'));
    }
  }

  format(value) {
    const numeric = Number(value);
    return Number.isFinite(numeric) ? new Intl.NumberFormat('es-MX', {maximumFractionDigits: 2}).format(numeric) : this.escape(value);
  }

  escape(value) {
    return String(value).replace(/[&<>"']/g, (character) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[character]));
  }
};
