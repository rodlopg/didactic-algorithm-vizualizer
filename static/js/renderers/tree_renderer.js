window.TreeRenderer = class TreeRenderer {
  constructor(container) {
    this.container = container;
  }

  render(state) {
    if (!state || !Array.isArray(state.nodos) || !state.nodos.length) {
      this.container.innerHTML = '<p class="empty-state">No hay árbol visible todavía.</p>';
      return;
    }

    const children = new Map();
    state.nodos.forEach((node) => children.set(node.id, []));
    (state.aristas || []).forEach((edge) => {
      if (children.has(edge.origen)) children.get(edge.origen).push(edge);
    });

    const positions = new Map();
    let leafCursor = 0;
    const depthGap = 168;
    const leafGap = 238;
    const nodeW = 198;
    const nodeH = 84;

    const place = (nodeId, depth) => {
      const edges = children.get(nodeId) || [];
      if (!edges.length) {
        const x = leafCursor * leafGap + 150;
        leafCursor += 1;
        positions.set(nodeId, {x, y: 75 + depth * depthGap});
        return x;
      }
      const xs = edges.map((edge) => place(edge.destino, depth + 1));
      const x = (xs[0] + xs[xs.length - 1]) / 2;
      positions.set(nodeId, {x, y: 75 + depth * depthGap});
      return x;
    };

    const root = state.nodos.find((node) => node.profundidad === 0) || state.nodos[0];
    place(root.id, root.profundidad || 0);

    const maxDepth = Math.max(...state.nodos.map((node) => node.profundidad || 0), 0);
    const width = Math.max(1040, (leafCursor + 1) * leafGap);
    const height = 150 + (maxDepth + 1) * depthGap;
    const pathNodes = new Set(state.camino || []);

    const fmt = (value) => {
      const n = Number(value);
      return Number.isFinite(n) ? n.toFixed(3).replace(/0+$/, '').replace(/\.$/, '') : String(value ?? '—');
    };

    const edgeSvg = (state.aristas || []).map((edge) => {
      const a = positions.get(edge.origen);
      const b = positions.get(edge.destino);
      if (!a || !b) return '';
      const midY = (a.y + b.y) / 2;
      const midX = (a.x + b.x) / 2;
      const active = state.nodo_activo === edge.origen && state.active_edge_value === edge.etiqueta;
      const pathEdge = pathNodes.has(edge.origen) && pathNodes.has(edge.destino);
      const labelWidth = 232;
      const labelHeight = 62;
      const klass = ['tree-edge-group', pathEdge ? 'is-path' : '', active ? 'is-active' : ''].filter(Boolean).join(' ');
      return `
        <g class="${klass}">
          <path class="tree-edge" d="M ${a.x} ${a.y + nodeH / 2} V ${midY} H ${b.x} V ${b.y - nodeH / 2}"></path>
          <g class="tree-edge-label-box" transform="translate(${midX}, ${midY})">
            <rect x="${-labelWidth / 2}" y="${-labelHeight / 2}" width="${labelWidth}" height="${labelHeight}"></rect>
            <text class="tree-edge-label" x="0" y="-21" text-anchor="middle">${this.escape(edge.etiqueta)}</text>
            <text class="tree-edge-prob" x="0" y="0" text-anchor="middle">p = ${edge.muestras_hijo}/${edge.muestras_padre} = ${fmt(edge.probabilidad)}</text>
            <text class="tree-edge-contrib" x="0" y="21" text-anchor="middle">p·I = ${fmt(edge.aporte_ponderado)}</text>
          </g>
        </g>`;
    }).join('');

    const nodeSvg = state.nodos.map((node) => {
      const p = positions.get(node.id);
      if (!p) return '';
      const classes = [
        'tree-node',
        node.id === state.nodo_activo ? 'is-active' : '',
        pathNodes.has(node.id) ? 'is-path' : '',
      ].filter(Boolean).join(' ');
      const label = node.es_hoja ? `Clase: ${node.prediccion || node.mayoria}` : `Pregunta: ${node.caracteristica}`;
      const sumValue = node.suma_producto?.valor;
      const sumFormula = node.suma_producto?.formula || '';
      const sumLine = Number.isFinite(Number(sumValue)) ? `Σ p·I = ${fmt(sumValue)}` : '';
      return `
        <g class="${classes}" transform="translate(${p.x - nodeW / 2}, ${p.y - nodeH / 2})">
          <rect class="tree-node-rect" width="${nodeW}" height="${nodeH}"></rect>
          <text class="tree-node-text" x="${nodeW / 2}" y="24">${this.escape(label)}</text>
          <text class="tree-node-meta" x="${nodeW / 2}" y="45">${node.muestras} ejemplo${node.muestras === 1 ? '' : 's'}</text>
          ${sumLine ? `<g class="tree-node-sum-box"><rect x="12" y="53" width="${nodeW - 24}" height="22"></rect><text class="tree-node-sum" x="${nodeW / 2}" y="68">${this.escape(sumLine)}</text></g>` : ''}
          ${sumFormula ? `<title>${this.escape(sumFormula)}</title>` : ''}
        </g>`;
    }).join('');

    this.container.innerHTML = `
      <div class="tree-legend">
        <span><i class="tree-legend__branch"></i> rama posible</span>
        <span><i class="tree-legend__path"></i> camino activo</span>
        <span><strong>p = n/N</strong> probabilidad de rama</span>
        <span><strong>p·I</strong> aporte ponderado</span>
        <span><strong>Σ p·I</strong> suma-producto del nodo</span>
      </div>
      <div class="tree-diagram-scroll">
        <svg class="tree-svg" viewBox="0 0 ${width} ${height}" role="img" aria-label="Árbol de decisión con probabilidades y suma-producto">
          ${edgeSvg}
          ${nodeSvg}
        </svg>
      </div>`;
  }

  escape(value) {
    return String(value).replace(/[&<>"']/g, (character) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[character]));
  }
};
