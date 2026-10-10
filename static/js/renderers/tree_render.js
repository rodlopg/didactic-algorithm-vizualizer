window.renderers = window.renderers || {};

window.renderers['decision_tree'] = function(step) {
  const stage = document.getElementById('visual-stage');
  const vars = step.variables || {};

  let html = `<div style="padding:20px; background:#1e293b; border-radius:8px; border:1px solid #334155;">
    <h3 style="color:#38bdf8;margin-bottom:15px;">Métricas del Atributo</h3>`;

  if (vars.subsets) {
    html += `<table style="width:100%; text-align:left; color:white; border-collapse:collapse;">
      <tr style="border-bottom:1px solid gray;"><th>Valor</th><th>Muestras</th><th>Entropía H(S_v)</th><th>Gini</th></tr>`;
    vars.subsets.forEach(sub => {
      html += `<tr style="border-bottom:1px solid #333;"><td>${sub.value}</td><td>${sub.count}</td><td>${sub.entropy}</td><td>${sub.gini}</td></tr>`;
    });
    html += `</table>`;
  } else {
    html += `<p style="color:white; font-size:1.2rem;">Entropía Inicial: <b>${vars.base_entropy || '-'}</b></p>`;
  }
  html += `</div>`;
  stage.innerHTML = html;
};