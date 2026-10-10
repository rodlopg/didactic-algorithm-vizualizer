/**
 * Diagrama interactivo de posibilidades para la asignación dinámica de recursos.
 *
 * El grafo representa el espacio de decisiones como una red por etapas:
 *   estado s_i --x_i--> estado s_{i+1} = s_i - x_i
 *
 * No calcula la solución. Solo la hace visible a partir del estado didáctico
 * producido por core/resource_allocation.py.
 */
window.ResourceGraphRenderer = class ResourceGraphRenderer {
  constructor(container) {
    this.container = container;
  }

  render(state, target) {
    if (!target || !state || !Array.isArray(state.etapas)) {
      return;
    }

    const brigadas = Number(state.brigadas);
    const etapas = state.etapas;
    if (!Number.isInteger(brigadas) || brigadas < 0 || !etapas.length) {
      target.innerHTML = '<p class="empty-state">No hay datos suficientes para dibujar el diagrama.</p>';
      return;
    }

    const activeStage = Number.isInteger(state.etapa_activa) ? state.etapa_activa : -1;
    const activeState = Number.isInteger(state.estado_activo) ? state.estado_activo : -1;
    const activeDecision = Number.isInteger(state.decision_activa) ? state.decision_activa : -1;
    const selections = state.seleccionados || {};
    const policyEdges = this.getPolicyEdges(brigadas, etapas.length, selections);
    const activeEdge = this.makeEdgeKey(activeStage, activeState, activeDecision);

    const columnCount = etapas.length + 1;
    const width = Math.max(980, 150 + columnCount * 210);
    const rowGap = brigadas <= 8 ? 64 : brigadas <= 14 ? 50 : 42;
    const top = 116;
    const bottom = 92;
    const height = Math.max(430, top + brigadas * rowGap + bottom);
    const left = 92;
    const right = 86;
    const columnGap = columnCount > 1 ? (width - left - right) / (columnCount - 1) : 0;
    const nodeRadius = brigadas > 14 ? 16 : 19;

    const position = (column, stateValue) => ({
      x: left + column * columnGap,
      y: top + stateValue * rowGap,
    });

    const stageHeaders = this.renderStageHeaders(etapas, position, width);
    const edges = this.renderEdges(
      brigadas,
      etapas,
      position,
      policyEdges,
      activeEdge,
      state,
      nodeRadius,
    );
    const nodes = this.renderNodes(
      brigadas,
      etapas.length,
      position,
      activeStage,
      activeState,
      activeDecision,
      state,
      nodeRadius,
    );

    const activeDescription = this.describeActive(state, etapas);
    const policyDescription = this.describePolicy(state, etapas, brigadas);

    target.innerHTML = `
      <section class="resource-graph" aria-labelledby="resource-graph-title">
        <header class="resource-graph__header">
          <div>
            <p class="eyebrow">MAPA DE POSIBILIDADES</p>
            <h4 id="resource-graph-title">Todas las asignaciones posibles y el paso que estamos ejecutando</h4>
          </div>
          <p class="resource-graph__status">${this.escape(activeDescription)}</p>
        </header>

        <div class="resource-graph__legend" aria-label="Leyenda del diagrama">
          <span><i class="legend-mark legend-mark--possible"></i> Posibilidad factible</span>
          <span><i class="legend-mark legend-mark--policy"></i> Política óptima</span>
          <span><i class="legend-mark legend-mark--active"></i> Paso actual</span>
          <span><i class="legend-node legend-node--active"></i> Estado activo</span>
        </div>

        <div class="resource-graph__scroll">
          <svg class="resource-graph__svg" viewBox="0 0 ${width} ${height}" width="${width}" height="${height}" role="img"
            aria-label="Grafo de estados y decisiones de asignación de brigadas">
            <defs>
              <marker id="resource-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
                <path d="M 0 0 L 10 5 L 0 10 z" fill="currentColor"></path>
              </marker>
            </defs>
            <g class="resource-graph__headers">${stageHeaders}</g>
            <g class="resource-graph__edges">${edges}</g>
            <g class="resource-graph__nodes">${nodes}</g>
          </svg>
        </div>

        <div class="resource-graph__explanation">
          <div>
            <strong>Cómo leerlo</strong>
            <p>Un nodo indica cuántas brigadas están disponibles. Cada flecha representa una decisión posible: asignar <code>xᵢ</code> brigadas y pasar las restantes al siguiente país.</p>
          </div>
          <div>
            <strong>Ruta reconstruida</strong>
            <p>${this.escape(policyDescription)}</p>
          </div>
        </div>
      </section>
    `;
  }

  renderStageHeaders(etapas, position, width) {
    const labels = ['INICIO', ...etapas.map((stage, index) => index === etapas.length - 1 ? `${this.escape(stage)} / FIN` : this.escape(stage))];
    return labels.map((label, column) => {
      const x = position(column, 0).x;
      const sub = column === 0
        ? 'B brigadas'
        : `x${this.toSubscript(column)} · s${this.toSubscript(column)}`;
      const boxWidth = 152;
      return `
        <g class="resource-stage-label">
          <rect x="${x - boxWidth / 2}" y="22" width="${boxWidth}" height="54"></rect>
          <text x="${x}" y="46" text-anchor="middle">${label}</text>
          <text x="${x}" y="65" text-anchor="middle" class="resource-stage-label__sub">${this.escape(sub)}</text>
        </g>
      `;
    }).join('');
  }

  renderEdges(brigadas, etapas, position, policyEdges, activeEdge, state, nodeRadius) {
    const fragments = [];
    for (let stage = 0; stage < etapas.length; stage += 1) {
      for (let sourceState = 0; sourceState <= brigadas; sourceState += 1) {
        for (let decision = 0; decision <= sourceState; decision += 1) {
          const targetState = sourceState - decision;
          const key = this.makeEdgeKey(stage, sourceState, decision);
          const isActive = key === activeEdge;
          const isPolicy = policyEdges.has(key);
          const from = position(stage, sourceState);
          const to = position(stage + 1, targetState);
          const dx = to.x - from.x;
          const curve = Math.max(12, Math.min(28, Math.abs(targetState - sourceState) * 3));
          const midX = from.x + dx * 0.52;
          const bend = targetState < sourceState ? -curve : targetState > sourceState ? curve : 0;
          const d = `M ${from.x + nodeRadius} ${from.y} C ${midX - 42} ${from.y + bend} ${midX + 42} ${to.y + bend} ${to.x - nodeRadius} ${to.y}`;

          const classes = [
            'resource-edge',
            isPolicy ? 'is-policy' : '',
            isActive ? 'is-active' : '',
          ].filter(Boolean).join(' ');
          const immediate = this.getImmediatePerformance(state, stage, decision);
          const labelY = (from.y + to.y) / 2 - 8;
          const label = isActive
            ? `<g class="resource-edge-label is-active" transform="translate(${midX}, ${labelY})">
                <rect x="-58" y="-19" width="116" height="40"></rect>
                <text x="0" y="-2" text-anchor="middle">x${this.toSubscript(stage + 1)} = ${decision}</text>
                <text x="0" y="14" text-anchor="middle">p = ${this.format(immediate)}</text>
              </g>`
            : isPolicy
              ? `<g class="resource-edge-label is-policy" transform="translate(${midX}, ${labelY})">
                  <rect x="-45" y="-15" width="90" height="28"></rect>
                  <text x="0" y="5" text-anchor="middle">x${this.toSubscript(stage + 1)} = ${decision}</text>
                </g>`
              : '';

          fragments.push(`
            <g class="resource-edge-group" data-edge="${key}">
              <path class="${classes}" d="${d}" marker-end="url(#resource-arrow)" aria-hidden="true">
                <title>${this.escape(`${etapas[stage]}: con ${sourceState} brigadas, asignar ${decision} y pasar ${targetState}.`)}</title>
              </path>
              ${label}
            </g>
          `);
        }
      }
    }
    return fragments.join('');
  }

  renderNodes(brigadas, stageCount, position, activeStage, activeState, activeDecision, state, nodeRadius) {
    const chunks = [];
    for (let column = 0; column <= stageCount; column += 1) {
      for (let stateValue = 0; stateValue <= brigadas; stateValue += 1) {
        const point = position(column, stateValue);
        const isActive = column === activeStage && stateValue === activeState;
        const targetIsActive = column === activeStage + 1 && activeStage >= 0 && Number.isInteger(activeDecision) && activeDecision >= 0 && stateValue === activeState - activeDecision;
        const isStart = column === 0 && stateValue === brigadas;
        const isPolicyNode = this.isPolicyNode(column, stateValue, brigadas, stageCount, state.seleccionados || {});
        const classes = [
          'resource-node',
          isActive || targetIsActive ? 'is-active' : '',
          isStart ? 'is-start' : '',
          isPolicyNode ? 'is-policy' : '',
        ].filter(Boolean).join(' ');
        const label = column === 0
          ? `B = ${brigadas}`
          : column === stageCount
            ? `s${this.toSubscript(stageCount)} = ${stateValue}`
            : `s${this.toSubscript(column)} = ${stateValue}`;

        chunks.push(`
          <g class="${classes}" transform="translate(${point.x}, ${point.y})">
            <circle r="${nodeRadius}"></circle>
            <text y="6" text-anchor="middle">${stateValue}</text>
            <title>${this.escape(label)}</title>
          </g>
        `);
      }
    }
    return chunks.join('');
  }

  getPolicyEdges(brigadas, stageCount, selections) {
    const edges = new Set();
    let sourceState = brigadas;
    for (let stage = 0; stage < stageCount; stage += 1) {
      const raw = selections[String(stage + 1)];
      if (raw === undefined || raw === null) break;
      const decision = Number(raw);
      if (!Number.isInteger(decision) || decision < 0 || decision > sourceState) break;
      edges.add(this.makeEdgeKey(stage, sourceState, decision));
      sourceState -= decision;
    }
    return edges;
  }

  isPolicyNode(column, stateValue, brigadas, stageCount, selections) {
    if (column === 0) return stateValue === brigadas;
    let sourceState = brigadas;
    for (let stage = 0; stage < column; stage += 1) {
      const raw = selections[String(stage + 1)];
      if (raw === undefined || raw === null) return false;
      const decision = Number(raw);
      if (!Number.isInteger(decision) || decision < 0 || decision > sourceState) return false;
      sourceState -= decision;
    }
    return sourceState === stateValue;
  }

  getImmediatePerformance(state, stage, decision) {
    if (!Array.isArray(state?.rendimientos) || !Array.isArray(state.rendimientos[stage])) {
      const candidates = state?.candidatos_evaluados;
      const candidate = Array.isArray(candidates)
        ? candidates.find((item) => Number(item.brigadas_etapa) === decision)
        : null;
      return candidate?.rendimiento_inmediato ?? 0;
    }
    return Number(state.rendimientos[stage][decision]);
  }

  describeActive(state, etapas) {
    const stage = Number(state?.etapa_activa);
    const source = Number(state?.estado_activo);
    const decision = Number(state?.decision_activa);
    if (!Number.isInteger(stage) || stage < 0 || stage >= etapas.length) {
      if (state?.seleccionados && Object.keys(state.seleccionados).length) return 'Reconstruyendo la política óptima.';
      return 'Avanza para ver cómo se recorre el grafo.';
    }
    const remaining = source - decision;
    return `${etapas[stage]} · s=${source} · probar x=${decision} · quedan ${remaining}`;
  }

  describePolicy(state, etapas, brigadas) {
    const selections = state?.seleccionados || {};
    const values = [];
    let remaining = brigadas;
    for (let i = 0; i < etapas.length; i += 1) {
      const raw = selections[String(i + 1)];
      if (raw === undefined || raw === null) break;
      const x = Number(raw);
      values.push(`${etapas[i]}: ${x}`);
      remaining -= x;
    }
    if (!values.length) return 'Todavía no se ha reconstruido una política. Las aristas finas representan todas las posibilidades factibles.';
    return `${values.join(' → ')}. Quedan ${remaining} brigadas al final.`;
  }

  makeEdgeKey(stage, sourceState, decision) {
    return `${stage}|${sourceState}|${decision}`;
  }

  toSubscript(value) {
    const map = ['₀', '₁', '₂', '₃', '₄', '₅', '₆', '₇', '₈', '₉'];
    return String(value).split('').map((char) => map[Number(char)] || char).join('');
  }

  format(value) {
    const numeric = Number(value);
    return Number.isFinite(numeric)
      ? new Intl.NumberFormat('es-MX', {maximumFractionDigits: 2}).format(numeric)
      : String(value);
  }

  escape(value) {
    return String(value).replace(/[&<>"']/g, (character) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[character]));
  }
};
