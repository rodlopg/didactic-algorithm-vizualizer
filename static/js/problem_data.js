(() => {
  const escape = (value) => String(value).replace(/[&<>"']/g, (character) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[character]));

  const format = (value) => {
    if (value === null || value === undefined || value === '') return '—';
    const numeric = Number(value);
    if (!Number.isFinite(numeric)) return escape(value);
    return new Intl.NumberFormat('es-MX', {maximumFractionDigits: 2}).format(numeric);
  };

  function table(headers, rows, scope = 'col') {
    const head = headers.map((header) => `<th scope="${scope}">${escape(header)}</th>`).join('');
    const body = rows.map((row) => `<tr>${row.map((cell) => `<td>${cell}</td>`).join('')}</tr>`).join('');
    return `<div class="problem-data__table-scroll"><table class="problem-data__table"><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table></div>`;
  }

  function shell(container, title, subtitle, metrics, tableHtml, note = '') {
    if (!container) return;
    const metricHtml = (metrics || []).map((metric) => `<span class="problem-data__metric"><strong>${escape(metric.value)}</strong><small>${escape(metric.label)}</small></span>`).join('');
    container.innerHTML = `
      <section class="problem-data-card" aria-labelledby="${container.id}-title">
        <header class="problem-data__header">
          <div><p class="eyebrow">ANTES DE EJECUTAR</p><h3 id="${container.id}-title">${escape(title)}</h3><p>${escape(subtitle)}</p></div>
          <div class="problem-data__metrics">${metricHtml}</div>
        </header>
        ${tableHtml}
        ${note ? `<p class="problem-data__note">${escape(note)}</p>` : ''}
      </section>`;
  }

  function tree(container, dataset, target, criterion, maxDepth) {
    if (!Array.isArray(dataset) || !dataset.length) {
      shell(container, 'Datos del problema', 'Escribe el conjunto de ejemplos para visualizarlo aquí.', [], '<p class="problem-data__empty">Todavía no hay filas válidas.</p>');
      return;
    }
    const columns = Array.from(new Set(dataset.flatMap((row) => Object.keys(row))));
    const visible = dataset.slice(0, 12);
    const rows = visible.map((row) => columns.map((column) => escape(row[column] ?? '—')));
    const extra = dataset.length > visible.length ? `Mostrando ${visible.length} de ${dataset.length} filas.` : `${dataset.length} filas de aprendizaje.`;
    shell(container, 'Conjunto de aprendizaje', `La tabla refleja exactamente los datos que alimentarán el árbol. La variable objetivo es «${target || 'Jugar'}».`, [
      {value: String(dataset.length), label: 'ejemplos'},
      {value: criterion === 'gini' ? 'Gini' : 'Entropía', label: 'criterio'},
      {value: String(maxDepth), label: 'profundidad máxima'},
    ], table(columns, rows), extra);
  }

  function uncertainty(container, alternatives, states, payments, criterion, alpha) {
    const alts = Array.isArray(alternatives) ? alternatives : [];
    const sts = Array.isArray(states) ? states : [];
    const matrix = Array.isArray(payments) ? payments : [];
    const rows = alts.map((alt, i) => [escape(alt), ...(sts.map((_, j) => format(matrix?.[i]?.[j]))) ]);
    shell(container, 'Matriz de pagos', 'Cada fila es una alternativa y cada columna un estado de la naturaleza.', [
      {value: `${alts.length} × ${sts.length}`, label: 'dimensión'},
      {value: criterion === 'todos' ? 'Todos' : criterion, label: 'criterio'},
      {value: Number(alpha).toFixed(2), label: 'α de Hurwicz'},
    ], table(['Alternativa', ...sts], rows), 'Los valores se toman directamente de los inputs actuales.');
  }

  function knapsack(container, benefits, weights, capacity) {
    const rows = (Array.isArray(benefits) ? benefits : []).map((benefit, i) => [String(i + 1), format(benefit), format(weights?.[i])]);
    shell(container, 'Datos de la mochila 0/1', 'Ficha de entrada: cada fila representa un objeto antes de comenzar a llenar la matriz zₖ(d).', [
      {value: format(capacity), label: 'capacidad B'},
      {value: String(rows.length), label: 'objetos'},
      {value: String(rows.reduce((sum, row) => sum + Number(row[1].replace(/[^0-9.-]/g, '')) || 0, 0)), label: 'beneficio mostrado'},
    ], table(['I', 'Gᵢ', 'Vᵢ'], rows), 'B = capacidad disponible; la ficha refleja exactamente los valores actuales de los inputs.');
  }

  function resource(container, brigades, stages, performance) {
    const stageNames = Array.isArray(stages) ? stages : [];
    const matrix = Array.isArray(performance) ? performance : [];
    const rows = matrix.map((row, i) => [String(i), ...stageNames.map((_, j) => format(row?.[j]))]);
    shell(container, 'Datos de asignación', 'La tabla muestra la medida de desempeño que produce cada país para cada número de brigadas.', [
      {value: String(brigades), label: 'brigadas totales'},
      {value: String(stageNames.length), label: 'etapas'},
      {value: String(matrix.length), label: 'niveles de brigadas'},
    ], table(['Brigadas', ...stageNames], rows), 'Antes de recorrer la DP puedes comprobar que cada fila tenga una alternativa para cada país.');
  }

  function machine(container, data) {
    const h = Number(data.horizonte);
    const maxAge = Number(data.edad_maxima);
    const income = data.ingresos || [];
    const operation = data.costos_operacion || [];
    const salvage = data.valores_desecho || [];
    const rows = Array.from({length: maxAge + 1}, (_, age) => [
      String(age), format(income[age]), format(operation[age]), format(salvage[age])
    ]);
    shell(container, 'Datos del problema de reemplazo', 'Las filas corresponden a la edad t de la máquina. Estos son los datos que alimentan fᵢ(t).', [
      {value: String(data.edad_inicial), label: 'edad inicial'},
      {value: String(h), label: 'años de horizonte'},
      {value: format(data.costo_adquisicion), label: 'adquisición'},
      {value: String(maxAge), label: 'edad límite'},
    ], table(['Edad t', 'Ingreso r(t)', 'Operación c(t)', 'Desecho s(t)'], rows), 'La edad máxima obliga a reemplazar al inicio del año en que la máquina alcanza ese estado.');
  }

  window.ProblemData = {tree, uncertainty, knapsack, resource, machine, format, escape};
})();
