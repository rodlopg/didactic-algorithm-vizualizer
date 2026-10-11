window.TreeRenderer = class TreeRenderer {
  constructor(container) { this.container = container; }

  render(state) {
    if (!state || !Array.isArray(state.nodos) || state.nodos.length === 0) {
      this.container.innerHTML = '<p class="empty-state">No hay árbol visible todavía.</p>';
      return;
    }

    const nodeById = new Map(state.nodos.map((node) => [node.id, node]));
    const children = new Map(state.nodos.map((node) => [node.id, []]));
    (state.aristas || []).forEach((edge) => {
      if (children.has(edge.origen)) children.get(edge.origen).push(edge);
    });

    const NODE_W = 232;
    const NODE_H = 138;
    const LEAF_GAP = 420;
    const LEVEL_GAP = 280;
    const positions = new Map();
    let leafCursor = 0;

    const wrap = (value, limit = 23, maxLines = 3) => {
      const words = String(value ?? '—').split(/\s+/).flatMap((word) => word.length > limit ? (word.match(new RegExp(`.{1,${limit}}`, 'g')) || [word]) : [word]);
      const lines = [];
      let line = '';
      words.forEach((word) => {
        const next = line ? `${line} ${word}` : word;
        if (next.length > limit && line) { lines.push(line); line = word; }
        else line = next;
      });
      if (line) lines.push(line);
      if (lines.length > maxLines) {
        const kept = lines.slice(0, maxLines);
        kept[maxLines - 1] = `${kept[maxLines - 1].slice(0, Math.max(3, limit - 1))}…`;
        return kept;
      }
      return lines.length ? lines : ['—'];
    };

    const roots = state.nodos.filter((node) => !(state.aristas || []).some((edge) => edge.destino === node.id));
    const root = roots.find((node) => node.tipo === 'decision') || roots[0] || state.nodos[0];
    const place = (nodeId, depth) => {
      const branches = children.get(nodeId) || [];
      const node = nodeById.get(nodeId);
      if (!branches.length) {
        const x = 150 + leafCursor * LEAF_GAP;
        leafCursor += 1;
        positions.set(nodeId, {x, y: 138 + depth * LEVEL_GAP, depth});
        return x;
      }
      const xs = branches.map((edge) => place(edge.destino, depth + 1));
      const x = (xs[0] + xs[xs.length - 1]) / 2;
      positions.set(nodeId, {x, y: 138 + depth * LEVEL_GAP, depth});
      return x;
    };
    place(root.id, 0);

    // Todos los nodos, incluidos los de ramas profundas, quedan dentro del viewBox.
    const deepest = Math.max(0, ...Array.from(positions.values(), (position) => position.depth));
    const width = Math.max(520, 300 + Math.max(0, leafCursor - 1) * LEAF_GAP);
    const height = 276 + deepest * LEVEL_GAP;
    const fmt = (value, digits = 2) => {
      if (value === null || value === undefined || value === '') return '—';
      const n = Number(value);
      return Number.isFinite(n) ? new Intl.NumberFormat('es-MX', {maximumFractionDigits: digits}).format(n) : String(value);
    };
    const compact = (value, digits = 2) => {
      if (value === null || value === undefined || value === '') return '—';
      const n = Number(value);
      return Number.isFinite(n) ? n.toLocaleString('en-US', {maximumFractionDigits: digits, useGrouping: false}) : String(value);
    };

    const edgeSvg = (state.aristas || []).map((edge) => {
      const a = positions.get(edge.origen);
      const b = positions.get(edge.destino);
      if (!a || !b) return '';
      const startY = a.y + NODE_H / 2 - 1;
      const endY = b.y - NODE_H / 2 + 1;
      const midY = (startY + endY) / 2;
      const midX = (a.x + b.x) / 2;
      const dx = b.x - a.x;
      const pathEdge = edge.seleccionada ? 'is-selected' : '';
      const active = edge.id === state.arista_activa ? 'is-active' : '';
      let rows = [];
      if (edge.tipo === 'chance') {
        rows.push(`p = ${fmt(edge.probabilidad, 3)}`);
        if (edge.pago !== 0 && edge.pago !== null) rows.push(`Pago del suceso: ${fmt(edge.pago)}`);
        if (edge.evaluada && edge.contribucion !== null) rows.push(`Aporte esperado: ${fmt(edge.contribucion)}`);
      } else {
        if (edge.pago !== 0 && edge.pago !== null) rows.push(`Pago inmediato: ${fmt(edge.pago)}`);
        if (edge.evaluada && edge.valor_alternativa !== null) rows.push(`Valor alternativo: ${fmt(edge.valor_alternativa)}`);
        if (edge.seleccionada) rows.push('ALTERNATIVA ÓPTIMA');
      }
      if (!rows.length) rows.push(edge.tipo === 'decision' ? 'Alternativa disponible' : 'Suceso posible');
      const labelW = 202;
      const labelH = 26 + rows.length * 18;
      const labelY = midY - labelH / 2;
      const labelLines = rows.map((row, index) => `<text class="tree-edge-detail ${index === rows.length - 1 && row === 'ALTERNATIVA ÓPTIMA' ? 'tree-edge-detail--best' : ''}" x="${labelW / 2}" y="${23 + index * 18}">${this.escape(row)}</text>`).join('');
      const c1x = a.x + dx * 0.16;
      const c2x = b.x - dx * 0.16;
      const d = `M ${a.x} ${startY} C ${c1x} ${startY + (endY - startY) * 0.22}, ${c2x} ${endY - (endY - startY) * 0.22}, ${b.x} ${endY}`;
      return `<g class="tree-edge-group ${pathEdge} ${active}" data-edge="${this.escape(edge.id)}">
        <path class="tree-edge" d="${d}" />
        <g class="tree-edge-label-box" transform="translate(${midX - labelW / 2}, ${labelY})">
          <rect width="${labelW}" height="${labelH}" rx="10" />
          ${labelLines}
        </g>
      </g>`;
    }).join('');

    const nodeSvg = state.nodos.map((node) => {
      const p = positions.get(node.id);
      if (!p) return '';
      const lines = wrap(node.etiqueta, 24, 3);
      const active = node.id === state.nodo_activo ? 'is-active' : '';
      const best = node.mejor_rama ? 'has-best' : '';
      const typeLabel = node.tipo === 'decision' ? 'NODO DE DECISIÓN' : node.tipo === 'chance' ? 'NODO DE AZAR' : 'RESULTADO FINAL';
      const icon = node.tipo === 'decision'
        ? `<rect class="tree-node-symbol tree-node-symbol--decision" x="${NODE_W / 2 - 5}" y="12" width="10" height="10" />`
        : node.tipo === 'chance'
          ? `<circle class="tree-node-symbol tree-node-symbol--chance" cx="${NODE_W / 2}" cy="17" r="6" />`
          : `<path class="tree-node-symbol tree-node-symbol--terminal" d="M ${NODE_W / 2} 9 l 8 8 l -8 8 l -8 -8 z" />`;
      const titleStartY = 49;
      const titleSvg = lines.map((line, index) => `<tspan x="${NODE_W / 2}" y="${titleStartY + index * 16}">${this.escape(line)}</tspan>`).join('');
      let bottom = '';
      if (node.tipo === 'terminal') bottom = `Pago: ${fmt(node.valor)}`;
      else if (node.calculado) bottom = `${node.tipo === 'decision' ? 'Mejor valor' : 'Valor esperado'}: ${fmt(node.valor)}`;
      else bottom = 'Valor: pendiente';
      return `<g class="tree-node tree-node--${node.tipo} ${active} ${best}" transform="translate(${p.x - NODE_W / 2}, ${p.y - NODE_H / 2})" data-node="${this.escape(node.id)}">
        <rect class="tree-node-rect" width="${NODE_W}" height="${NODE_H}" rx="14" />
        ${icon}
        <text class="tree-node-type" x="${NODE_W / 2}" y="36">${typeLabel}</text>
        <text class="tree-node-text" text-anchor="middle">${titleSvg}</text>
        <line class="tree-node-separator" x1="16" y1="${NODE_H - 31}" x2="${NODE_W - 16}" y2="${NODE_H - 31}" />
        <text class="tree-node-value" x="${NODE_W / 2}" y="${NODE_H - 12}">${this.escape(bottom)}</text>
      </g>`;
    }).join('');

    this.container.innerHTML = `
      <div class="tree-legend" aria-label="Leyenda del árbol">
        <span><i class="tree-legend__square"></i> decisión controlable</span>
        <span><i class="tree-legend__circle"></i> suceso aleatorio</span>
        <span><i class="tree-legend__terminal"></i> pago final</span>
        <span><strong>p</strong> probabilidad de un suceso</span>
        <span><strong>VE</strong> valor esperado</span>
      </div>
      <div class="tree-diagram-scroll diagram-viewport__scroll">
        <svg class="tree-svg" viewBox="0 0 ${width} ${height}" role="img" aria-label="Árbol de decisión con nodos de decisión, sucesos, probabilidades y pagos">
          <g class="tree-edges">${edgeSvg}</g>
          <g class="tree-nodes">${nodeSvg}</g>
        </svg>
      </div>`;
  }

  escape(value) {
    return String(value).replace(/[&<>"']/g, (character) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[character]));
  }
};
