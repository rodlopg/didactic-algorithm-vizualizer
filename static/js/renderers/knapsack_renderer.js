(() => {
  class KnapsackRenderer {
    constructor(container) {
      this.container = container;
    }

    render(state) {
      if (!state) {
        this.container.innerHTML = '<p class="empty-state">Construye la tabla y comienza con <strong>Paso siguiente</strong>.</p>';
        return;
      }

      const dp = state.dp || [];
      const activeRow = state.fila_activa;
      const activeCol = state.columna_activa;
      const exclusion = state.celda_exclusion ? `${state.celda_exclusion[0]}-${state.celda_exclusion[1]}` : '';
      const inclusion = state.celda_inclusion ? `${state.celda_inclusion[0]}-${state.celda_inclusion[1]}` : '';
      const selectedCell = state.celda_elegida ? `${state.celda_elegida[0]}-${state.celda_elegida[1]}` : '';

      const columns = Array.from({length: state.capacidad + 1}, (_, i) => i);
      let html = '<div class="knapsack-summary">';
      html += `<span class="matrix-badge">CAPACIDAD ${escapeHtml(state.capacidad)}</span>`;
      html += `<span class="matrix-badge">OBJETOS ${escapeHtml(state.pesos.length)}</span>`;
      html += '<span class="matrix-badge matrix-badge--focus">RECORRIDO POR COLUMNAS</span>';
      if (state.capacidad_actual !== null && state.capacidad_actual !== undefined) {
        html += `<span class="matrix-badge">CAPACIDAD EN RECORRIDO ${escapeHtml(state.capacidad_actual)}</span>`;
      }
      html += '</div>';

      html += '<div class="table-scroll"><table class="knapsack-matrix"><thead><tr>';
      html += '<th scope="col">k / d</th>';
      columns.forEach((d) => { html += `<th scope="col" class="knapsack-head ${activeCol === d ? 'is-active' : ''}">${d}</th>`; });
      html += '</tr></thead><tbody>';

      dp.forEach((row, k) => {
        const rowActive = activeRow === k;
        const label = k === 0 ? '0 · base' : `${k} · O${k}<br><small>b=${format(state.beneficios[k - 1])}, p=${state.pesos[k - 1]}</small>`;
        html += `<tr class="${rowActive ? 'is-active-row' : ''}"><th scope="row">${label}</th>`;
        row.forEach((value, d) => {
          const key = `${k}-${d}`;
          const calculated = (state.celdas_calculadas || []).some((cell) => cell[0] === k && cell[1] === d);
          const classes = [
            'knapsack-cell',
            activeRow === k && activeCol === d ? 'is-focus-cell' : '',
            calculated ? 'is-calculated' : '',
            key === exclusion ? 'is-exclusion' : '',
            key === inclusion ? 'is-inclusion' : '',
            key === selectedCell ? 'is-selected-cell' : '',
          ].filter(Boolean).join(' ');
          const display = (k === 0 || calculated) ? format(value) : '·';
          html += `<td class="${classes}">${display}`;
          if (key === exclusion) html += '<span class="cell-note">sin</span>';
          if (key === inclusion) html += '<span class="cell-note">con</span>';
          html += '</td>';
        });
        html += '</tr>';
      });
      html += '</tbody></table></div>';

      if (state.backtracking && state.backtracking.length) {
        html += '<section class="backtracking-panel" aria-label="Recorrido de backtracking">';
        html += '<h4>Ruta de reconstrucción</h4><ol class="backtracking-list">';
        state.backtracking.forEach((entry) => {
          const action = entry.accion === 'incluido' ? 'INCLUIDO' : 'EXCLUIDO';
          html += `<li><strong>Objeto ${escapeHtml(entry.objeto)}: ${action}</strong> · ${escapeHtml(entry.capacidad_antes)} → ${escapeHtml(entry.capacidad_despues)}</li>`;
        });
        html += '</ol></section>';
      }

      if (state.seleccionados && state.seleccionados.length) {
        html += `<p class="selection-note"><strong>Objetos seleccionados:</strong> ${state.seleccionados.join(', ')}</p>`;
      }

      this.container.innerHTML = html;
    }
  }

  function format(value) {
    const number = Number(value);
    if (!Number.isFinite(number)) return String(value);
    return Number.isInteger(number) ? String(number) : number.toFixed(2);
  }

  function escapeHtml(value) {
    return String(value).replace(/[&<>"']/g, (character) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[character]));
  }

  window.KnapsackRenderer = KnapsackRenderer;
})();
