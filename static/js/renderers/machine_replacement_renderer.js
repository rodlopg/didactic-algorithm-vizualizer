window.MachineReplacementRenderer = class MachineReplacementRenderer {
  constructor(container) {
    this.container = container;
  }

  render(state) {
    if (!state || !Array.isArray(state.nodos) || !state.nodos.length) {
      this.container.innerHTML = '<p class="empty-state">Construye el problema y comienza con <strong>Paso siguiente</strong>.</p>';
      return;
    }

    const h = Number(state.horizonte);
    const maxAge = Number(state.edad_maxima);
    const nodes = state.nodos || [];
    const edges = state.aristas || [];
    const activeYear = Number.isInteger(state.anio_activo) ? state.anio_activo : -1;
    const activeAge = Number.isInteger(state.edad_activa) ? state.edad_activa : -1;
    const activeAction = String(state.decision_activa || '');
    const optimalEdgeIds = new Set((state.rutas_optimas || []).flatMap((route) => route.aristas || []));

    // Geometría deliberadamente cercana al esquema docente:
    // eje X = año de decisión, eje Y = edad de la máquina.
    const columnGap = Math.max(205, Math.min(235, 930 / Math.max(4, h)));
    const ageGap = 78;
    const left = 140;
    const top = 128;
    const finalGap = 150;
    const right = 110;
    const years = h + 1; // año h+1 = final del horizonte
    const finalX = left + (years - 1) * columnGap + finalGap;
    const width = Math.max(1250, finalX + right);
    const height = Math.max(620, top + (maxAge - 1) * ageGap + 160);
    const radius = 24;
    const markerId = 'machine-arrow';

    const pos = (anio, edad) => ({
      x: left + (anio - 1) * columnGap,
      y: top + (maxAge - edad) * ageGap,
    });

    const fmt = (value) => {
      const n = Number(value);
      if (!Number.isFinite(n)) return String(value ?? '—');
      return new Intl.NumberFormat('es-MX', { maximumFractionDigits: 0 }).format(n);
    };

    const esc = (value) => String(value ?? '').replace(/[&<>"']/g, (character) => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[character]));

    const sourceNodeIds = new Set(nodes.map((node) => node.id));

    const edgeSvg = edges.map((edge, edgeIndex) => {
      if (edge.tipo === 'final') {
        const from = pos(edge.anio, edge.edad_origen);
        const active = edge.anio === activeYear && activeAction === 'S' && edge.edad_origen === activeAge;
        const optimal = optimalEdgeIds.has(edge.id);
        const endX = finalX - 64;
        const endY = top + ((maxAge - 1) * ageGap) / 2;
        const bend = (edge.edad_origen % 2 === 0 ? -1 : 1) * Math.min(42, 10 + Math.abs(from.y - endY) * 0.08);
        const midX = (from.x + endX) / 2;
        const pathD = `M ${from.x + radius} ${from.y} Q ${midX} ${((from.y + endY) / 2) + bend} ${endX} ${endY}`;
        const classes = ['machine-edge', 'machine-edge--final', optimal ? 'is-policy' : '', active ? 'is-active' : ''].filter(Boolean).join(' ');
        const labelX = midX;
        const labelY = (from.y + endY) / 2 + bend - 2;
        return `
          <g class="${classes}" data-edge-id="${esc(edge.id)}">
            <path d="${pathD}" marker-end="url(#${markerId})"></path>
            <g class="machine-edge-label-pill" transform="translate(${labelX}, ${labelY})">
              <rect x="-18" y="-14" width="36" height="28"></rect>
              <text x="0" y="5" text-anchor="middle">S</text>
            </g>
            <title>Desechar (S) la máquina de ${edge.edad_origen} años al finalizar el horizonte.</title>
          </g>`;
      }

      if (!sourceNodeIds.has(edge.origen)) return '';
      const from = pos(edge.anio, edge.edad_origen);
      const to = pos(edge.anio + 1, edge.edad_destino);
      const active = edge.anio === activeYear && edge.edad_origen === activeAge && edge.accion === activeAction;
      const optimal = optimalEdgeIds.has(edge.id);

      let pathD;
      let labelY;
      let labelX = (from.x + to.x) / 2;

      if (edge.accion === 'K') {
        // Conservar: diagonal ascendente una edad.
        const bendY = (from.y + to.y) / 2 - 7;
        pathD = `M ${from.x + radius} ${from.y} Q ${labelX} ${bendY} ${to.x - radius} ${to.y}`;
        labelY = bendY - 15;
      } else {
        // Reemplazar: vuelve siempre a edad 1 en el año siguiente.
        // La curvatura evita tapar el resto de ramas que convergen al estado 1.
        const outward = 22 + Math.min(26, Math.abs(from.y - to.y) * 0.06) + (edgeIndex % 3) * 6;
        const controlX = labelX;
        const controlY = Math.min(from.y, to.y) - outward;
        pathD = `M ${from.x + radius} ${from.y} Q ${controlX} ${controlY} ${to.x - radius} ${to.y}`;
        labelY = controlY - 13;
      }

      const classes = ['machine-edge', `is-${edge.accion.toLowerCase()}`, optimal ? 'is-policy' : '', active ? 'is-active' : ''].filter(Boolean).join(' ');
      const label = edge.accion;
      const actionName = edge.accion === 'K' ? 'Conservar' : 'Reemplazar';
      const score = edge.valor !== undefined ? ` · ${fmt(edge.valor)}` : '';
      return `
        <g class="${classes}" data-edge-id="${esc(edge.id)}">
          <path d="${pathD}" marker-end="url(#${markerId})"></path>
          <g class="machine-edge-label-pill" transform="translate(${labelX}, ${labelY})">
            <rect x="-24" y="-14" width="48" height="28"></rect>
            <text x="0" y="5" text-anchor="middle">${label}</text>
          </g>
          <title>${actionName}${score ? ` · ingreso candidato ${score.replace(' · ', '')}` : ''}.</title>
        </g>`;
    }).join('');

    const nodeSvg = nodes.map((node) => {
      const p = pos(node.anio, node.edad);
      const active = node.anio === activeYear && node.edad === activeAge;
      const hasOptimalIncoming = edges.some((edge) => edge.destino === node.id && optimalEdgeIds.has(edge.id));
      const start = node.anio === 1 && node.edad === Number(state.edad_inicial);
      const classes = ['machine-node', start ? 'is-start' : '', hasOptimalIncoming ? 'is-route' : '', active ? 'is-active' : ''].filter(Boolean).join(' ');
      return `
        <g class="${classes}" transform="translate(${p.x}, ${p.y})">
          <circle r="${radius}"></circle>
          <text class="machine-node-age" x="0" y="6" text-anchor="middle">${esc(node.edad)}</text>
          <title>Año ${node.anio}, edad de la máquina ${node.edad} años</title>
        </g>`;
    }).join('');

    const stageLabels = Array.from({ length: years }, (_, i) => {
      const year = i + 1;
      const x = left + i * columnGap;
      const label = year === h + 1 ? 'AÑO FINAL' : `AÑO ${year}`;
      return `
        <g class="machine-stage-header">
          <rect x="${x - 70}" y="34" width="140" height="52"></rect>
          <text x="${x}" y="56" text-anchor="middle">${label}</text>
          <text x="${x}" y="74" text-anchor="middle" class="machine-stage-sub">${year === h + 1 ? 'desecho S' : 'decisión'}</text>
        </g>`;
    }).join('');

    const yTicks = Array.from({ length: maxAge }, (_, i) => {
      const age = i + 1;
      const y = top + (maxAge - age) * ageGap;
      return `<g><line class="machine-tick" x1="${left - 18}" y1="${y}" x2="${left - 4}" y2="${y}"></line><text class="machine-y-label" x="${left - 28}" y="${y + 5}" text-anchor="end">${age}</text></g>`;
    }).join('');

    const optimalSummary = (state.rutas_optimas || [])
      .map((route, index) => `<span class="machine-policy-chip"><strong>${index + 1}</strong><code>${esc(route.acciones.join(''))}</code></span>`)
      .join('');

    const startPos = pos(1, Number(state.edad_inicial));
    const finalY = top + ((maxAge - 1) * ageGap) / 2;

    this.container.innerHTML = `
      <section class="machine-diagram" aria-labelledby="machine-diagram-title">
        <header class="machine-diagram__header">
          <div>
            <p class="eyebrow">RED DE ESTADOS DEL PROBLEMA</p>
            <h4 id="machine-diagram-title">Edad de la máquina según el año de decisión</h4>
            <p class="machine-diagram__subhead">Cada círculo es un estado de edad. K conserva y avanza una edad; R reemplaza y lleva la máquina nueva a edad 1; S desecha al terminar el horizonte.</p>
          </div>
          <div class="machine-policy-summary">
            <span class="machine-policy-title">Políticas óptimas</span>
            ${optimalSummary || '<span class="machine-policy-empty">se muestran al completar el cálculo</span>'}
          </div>
        </header>

        <div class="machine-diagram__legend" aria-label="Leyenda del diagrama">
          <span><i class="machine-mark machine-mark--k"></i><strong>K</strong> Conservar</span>
          <span><i class="machine-mark machine-mark--r"></i><strong>R</strong> Reemplazar</span>
          <span><i class="machine-mark machine-mark--s"></i><strong>S</strong> Desechar</span>
          <span><i class="machine-mark machine-mark--active"></i>Paso actual</span>
        </div>

        <div class="machine-diagram__scroll diagram-viewport__scroll">
          <svg class="machine-svg" viewBox="0 0 ${width} ${height}" width="${width}" height="${height}" role="img" aria-label="Red de reemplazo de máquinas con años, edades, acciones K R y S">
            <defs>
              <marker id="${markerId}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">
                <path d="M 0 0 L 10 5 L 0 10 z"></path>
              </marker>
            </defs>
            <line class="machine-axis" x1="${left - 34}" y1="${height - 72}" x2="${finalX + 74}" y2="${height - 72}"></line>
            <line class="machine-axis" x1="${left - 34}" y1="${height - 72}" x2="${left - 34}" y2="${top - 48}"></line>
            <text class="machine-axis-title" x="${left + (years - 1) * columnGap / 2}" y="${height - 27}" text-anchor="middle">Año de decisión</text>
            <text class="machine-axis-title machine-axis-title--vertical" transform="translate(25,${top + ((maxAge - 1) * ageGap) / 2}) rotate(-90)" text-anchor="middle">Edad de la máquina</text>
            ${yTicks}
            ${stageLabels}
            <g class="machine-start-label">
              <text x="${startPos.x - 58}" y="${startPos.y - 36}" text-anchor="end">Inicio</text>
              <text x="${startPos.x - 58}" y="${startPos.y - 19}" text-anchor="end" class="machine-start-sub">edad ${state.edad_inicial}</text>
            </g>
            ${edgeSvg}
            ${nodeSvg}
            <g class="machine-final-node" transform="translate(${finalX}, ${finalY})">
              <rect x="-58" y="-29" width="116" height="58"></rect>
              <text x="0" y="7" text-anchor="middle">Final</text>
            </g>
          </svg>
        </div>

        <div class="machine-diagram__notes">
          <p><strong>Estado.</strong> El número dentro del círculo es la edad de la máquina al inicio del año.</p>
          <p><strong>Decisión.</strong> En cada nodo se comparan K y R usando la recurrencia hacia atrás.</p>
          <p><strong>Final.</strong> En el último año se conectan los estados alcanzables con S para recuperar su valor de desecho.</p>
        </div>
      </section>
      <section class="machine-table-grid">
        <article><h4>Datos por edad</h4>${this.renderDataTable(state)}</article>
        <article><h4>Resultados fᵢ(t)</h4>${this.renderDPTable(state)}</article>
      </section>`;
  }

  renderDataTable(state) {
    const rows = Array.from({ length: Number(state.edad_maxima) + 1 }, (_, age) => `
      <tr>
        <th scope="row">${age}</th>
        <td>${this.format(state.ingresos?.[age])}</td>
        <td>${this.format(state.costos_operacion?.[age])}</td>
        <td>${this.format(state.valores_desecho?.[age])}</td>
      </tr>`).join('');
    return `<div class="table-scroll"><table class="machine-table"><thead><tr><th>Edad t</th><th>Ingreso r(t)</th><th>Operación c(t)</th><th>Desecho s(t)</th></tr></thead><tbody>${rows}</tbody></table></div>`;
  }

  renderDPTable(state) {
    const dp = state.dp || {};
    const years = Object.keys(dp).map(Number).sort((a, b) => a - b);
    const ages = Array.from(new Set(years.flatMap((year) => Object.keys(dp[String(year)] || {}).map(Number)))).sort((a, b) => a - b);
    const headers = ages.map((age) => `<th>t=${age}</th>`).join('');
    const rows = years.map((year) => {
      const row = dp[String(year)] || {};
      const cells = ages.map((age) => `<td class="${Object.prototype.hasOwnProperty.call(row, String(age)) ? '' : 'is-empty-cell'}">${this.format(row[String(age)])}</td>`).join('');
      return `<tr><th scope="row">${year === Number(state.horizonte) + 1 ? 'Final' : `Año ${year}`}</th>${cells}</tr>`;
    }).join('');
    return `<div class="table-scroll"><table class="machine-table machine-dp-table"><thead><tr><th>Año</th>${headers}</tr></thead><tbody>${rows}</tbody></table></div>`;
  }

  format(value) {
    if (value === null || value === undefined || value === '') return '—';
    const n = Number(value);
    return Number.isFinite(n) ? new Intl.NumberFormat('es-MX', { maximumFractionDigits: 0 }).format(n) : this.escape(value);
  }

  escape(value) {
    return String(value).replace(/[&<>"']/g, (character) => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[character]));
  }
};
