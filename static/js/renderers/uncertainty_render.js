window.renderers = window.renderers || {};

window.renderers['uncertainty'] = function(step) {
  const stage = document.getElementById('visual-stage');
  const matrix = step.matrix_state || [];
  const active = step.active_elements || {};

  if (!matrix.length) return;
  const rows = matrix.length;
  const cols = matrix[0].length;

  let html = `<div class="matrix-container"><h3 style="color:white;margin-bottom:10px;">Matriz de Pagos/Arrepentimiento</h3>
              <div class="matrix-grid" style="grid-template-columns: repeat(${cols}, 1fr);">`;

  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      let classes = ['matrix-cell'];
      if (active.selected_alt === r) classes.push('primary');
      html += `<div class="${classes.join(' ')}">${matrix[r][c]}</div>`;
    }
  }
  html += `</div></div>`;
  stage.innerHTML = html;
};