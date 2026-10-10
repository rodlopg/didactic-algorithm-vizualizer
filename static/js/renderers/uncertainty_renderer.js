window.UncertaintyRenderer = class UncertaintyRenderer {
  constructor(container) {
    this.container = container;
  }

  render(state) {
    if (!state || !state.alternativas || !state.estados) {
      this.container.innerHTML = '<p class="empty-state">No hay matriz visible todavía.</p>';
      return;
    }

    const criterion = state.criterio || '';
    const selected = new Set(state.filas_seleccionadas || []);
    const rowActive = Number.isInteger(state.fila_activa) ? state.fila_activa : -1;
    const colActive = Number.isInteger(state.columna_activa) ? state.columna_activa : -1;
    const hasRegret = Array.isArray(state.regret) && state.regret.length;
    const showResults = Array.isArray(state.resultados) && state.resultados.length;

    const headerCells = state.estados.map((estado, j) => `<th class="decision-head ${j === colActive ? 'is-active' : ''}" scope="col">${this.escape(estado)}</th>`).join('');
    const rows = state.alternativas.map((alt, i) => {
      const rowClass = [
        i === rowActive ? 'is-active-row' : '',
        selected.has(i) ? 'is-selected-row' : '',
      ].filter(Boolean).join(' ');
      const cells = state.estados.map((_, j) => {
        const value = hasRegret ? state.regret[i][j] : state.pagos[i][j];
        const cellClass = [
          i === rowActive && j === colActive ? 'is-focus-cell' : '',
          hasRegret ? 'is-regret' : '',
        ].filter(Boolean).join(' ');
        return `<td class="decision-cell ${cellClass}">${this.format(value)}${hasRegret ? `<span class="cell-note">R</span>` : ''}</td>`;
      }).join('');
      const result = showResults && state.resultados[i] !== undefined
        ? `<td class="decision-result ${selected.has(i) ? 'is-selected' : ''}">${this.format(state.resultados[i])}</td>`
        : '<td class="decision-result">—</td>';
      return `<tr class="${rowClass}"><th scope="row">${this.escape(alt)}</th>${cells}${result}</tr>`;
    }).join('');

    const resultLabel = state.etiquetas_resultado?.[0] || 'Resultado';
    const maxima = state.maxima_columnas || [];
    const columnMaxLine = hasRegret && maxima.length
      ? `<p class="matrix-note"><strong>Referencia por estado:</strong> ${state.estados.map((s, j) => `${this.escape(s)} = ${this.format(maxima[j])}`).join(' · ')}</p>`
      : '';

    this.container.innerHTML = `
      <div class="matrix-meta">
        <span class="matrix-badge">${this.escape(criterion.toUpperCase())}</span>
        <span>${hasRegret ? 'Matriz de arrepentimiento' : 'Matriz de pagos'}</span>
      </div>
      <div class="table-scroll">
        <table class="decision-matrix" aria-label="Matriz de decisión">
          <thead><tr><th scope="col">Alternativa</th>${headerCells}<th scope="col">${this.escape(resultLabel)}</th></tr></thead>
          <tbody>${rows}</tbody>
        </table>
      </div>
      ${columnMaxLine}
      ${hasRegret ? '<p class="matrix-note">R = mejor pago posible en el estado − pago de la alternativa.</p>' : ''}
    `;
  }

  format(value) {
    const numeric = Number(value);
    if (!Number.isFinite(numeric)) return this.escape(value);
    return new Intl.NumberFormat('es-MX', {maximumFractionDigits: 2}).format(numeric);
  }

  escape(value) {
    return String(value).replace(/[&<>"']/g, (character) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[character]));
  }
};
