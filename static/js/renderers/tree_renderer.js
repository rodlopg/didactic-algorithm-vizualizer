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
    const leafGap = 520;
    const nodeW = 236;
    const edgeLabelW = 236;
    const edgeLabelH = 62;

    const wrapLabel = (value, limit = 24) => {
      const words = String(value ?? '—').split(/\s+/);
      const lines = [];
      let line = '';
      words.forEach((word) => {
        const next = line ? `${line} ${word}` : word;
        if (next.length > limit && line) {
          lines.push(line);
          line = word;
        } else {
          line = next;
        }
      });
      if (line) lines.push(line);
      return lines.length ? lines : ['—'];
    };

    const labelsByNode = new Map(state.nodos.map((node) => [
      node.id,
      wrapLabel(node.es_hoja ? `Clase: ${node.prediccion || node.mayoria}` : `Pregunta: ${node.caracteristica}`),
    ]));
    const maxLabelLines = Math.max(1, ...Array.from(labelsByNode.values(), (lines) => lines.length));
    const nodeH = Math.max(94, 78 + maxLabelLines * 16);
    const depthGap = Math.max(250, nodeH + edgeLabelH + 22);

    const place = (nodeId, depth) => {
      const edges = children.get(nodeId) || [];
      if (!edges.length) {
        const x = leafCursor * leafGap + 160;
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
    const width = Math.max(560, Math.max(1, leafCursor - 1) * leafGap + nodeW + 120);
    const height = 180 + maxDepth * depthGap + nodeH;
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
      const klass = ['tree-edge-group', pathEdge ? 'is-path' : '', active ? 'is-active' : ''].filter(Boolean).join(' ');
      return `
        <g class="${klass}">
          <path class="tree-edge" d="M ${a.x} ${a.y + nodeH / 2} V ${midY} H ${b.x} V ${b.y - nodeH / 2}"></path>
          <g class="tree-edge-label-box" transform="translate(${midX}, ${midY})">
            <rect x="${-edgeLabelW / 2}" y="${-edgeLabelH / 2}" width="${edgeLabelW}" height="${edgeLabelH}"></rect>
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
      const labelLines = labelsByNode.get(node.id) || ['—'];
      const sumValue = node.suma_producto?.valor;
      const sumFormula = node.suma_producto?.formula || '';
      const sumLine = Number.isFinite(Number(sumValue)) ? `Σ p·I = ${fmt(sumValue)}` : '';
      const labelStartY = labelLines.length === 1 ? 28 : 20;
      const labelSvg = labelLines.map((line, index) => `<tspan x="${nodeW / 2}" y="${labelStartY + index * 16}">${this.escape(line)}</tspan>`).join('');
      const metaY = 21 + labelLines.length * 16 + 7;
      const sumY = metaY + 10;
      return `
        <g class="${classes}" transform="translate(${p.x - nodeW / 2}, ${p.y - nodeH / 2})">
          <rect class="tree-node-rect" width="${nodeW}" height="${nodeH}"></rect>
          <text class="tree-node-text" text-anchor="middle">${labelSvg}</text>
          <text class="tree-node-meta" x="${nodeW / 2}" y="${metaY}">${node.muestras} ejemplo${node.muestras === 1 ? '' : 's'}</text>
          ${sumLine ? `<g class="tree-node-sum-box"><rect x="12" y="${sumY}" width="${nodeW - 24}" height="22"></rect><text class="tree-node-sum" x="${nodeW / 2}" y="${sumY + 15}">${this.escape(sumLine)}</text></g>` : ''}
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
      <div class="tree-diagram-scroll diagram-viewport__scroll">
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
