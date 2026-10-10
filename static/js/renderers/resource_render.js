window.renderers = window.renderers || {};

window.renderers['resource_allocation'] = function(step) {
  const stage = document.getElementById('visual-stage');
  const vars = step.variables || {};

  let html = `<div style="padding:20px; background:#1e293b; border-radius:8px; border:1px solid #334155;">
    <h3 style="color:#38bdf8;margin-bottom:15px;">Evaluaciones de Asignación</h3>`;

  if (vars.evaluations) {
    html += `<table style="width:100%; text-align:left; color:white; border-collapse:collapse;">
      <tr style="border-bottom:1px solid gray;"><th>Asignado (x)</th><th>Total Calculado</th></tr>`;
    vars.evaluations.forEach(ev => {
      let isBest = (ev.x === vars.best_x);
      html += `<tr style="border-bottom:1px solid #333; ${isBest ? 'color:#34d399; font-weight:bold;' : ''}">
                 <td>${ev.x}</td><td>${ev.total} ${isBest ? '★' : ''}</td></tr>`;
    });
    html += `</table>`;
  }
  html += `</div>`;
  stage.innerHTML = html;
};