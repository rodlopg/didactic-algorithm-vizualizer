# Didactic Algorithm Visualizer

Laboratorio educativo en Flask para hacer visibles, paso a paso, algoritmos de toma de decisiones y programación dinámica. Toda la interfaz y los mensajes dirigidos al estudiante están en español.

## Estado del proyecto

**Integración final completada.** El laboratorio reúne cinco módulos que comparten el mismo contrato de pasos y la misma experiencia de navegación.

1. **Árboles de decisión** — nodos de decisión y azar, probabilidades por suceso, pagos por resultado y valor esperado por inducción hacia atrás.
2. **Decisión bajo incertidumbre** — Laplace, Wald/Maximin, Hurwicz y Savage/Minimax Regret.
3. **Mochila 0/1** — programación dinámica celda por celda y backtracking.
4. **Asignación de recursos** — programación dinámica por etapas y estados y reconstrucción de la política.
5. **Reemplazo de máquinas** — programación dinámica por edad, año y acciones K/R/S.

## Arquitectura

```text
didactic-algorithm-vizualizer/
├── core/
│   ├── __init__.py
│   ├── step_schema.py              # Contrato JSON común
│   ├── decision_trees.py           # Motor de Árboles de Decisión
│   ├── uncertainty.py              # Motor de Incertidumbre
│   ├── knapsack.py                 # Motor de Mochila 0/1
│   └── resource_allocation.py      # Motor de Asignación de Recursos
│
├── static/
│   ├── css/
│   │   └── matrix.css              # Sistema visual compartido
│   └── js/
│       ├── renderers/
│       │   ├── tree_renderer.js
│       │   ├── uncertainty_renderer.js
│       │   ├── knapsack_renderer.js
│       │   ├── resource_renderer.js
│       │   └── machine_replacement_renderer.js
│       ├── controller.js            # Árboles
│       ├── uncertainty_controller.js
│       ├── knapsack_controller.js
│       ├── resource_controller.js
│       ├── machine_replacement_controller.js
│       ├── diagram_viewport.js      # Autoajuste, zoom y escala por eje
│       └── flip.js                  # Navegación FLIP
│
├── templates/
│   ├── index.html                   # Laboratorio 1 / portada
│   ├── incertidumbre.html            # Laboratorio 2
│   ├── mochila.html                 # Laboratorio 3
│   ├── asignacion.html              # Laboratorio 4
│   └── reemplazo.html               # Laboratorio 5
│
├── tests/
│   ├── test_decision_trees.py
│   ├── test_uncertainty.py
│   ├── test_knapsack.py
│   └── test_resource_allocation.py
│
├── app.py
├── requirements.txt
├── Pipfile
├── .python-version
├── render.yaml
├── .github/
│   └── workflows/
│       └── tests.yml               # CI de pruebas
├── .gitignore
└── README.md
```

## Dónde agregar cada cosa

**Lógica matemática:** `core/<algoritmo>.py`.

**Pasos didácticos:** se generan desde el motor usando `core/step_schema.py`. Cada paso contiene fase, título, fórmula, explicación, variables y estado visual.

**Visualización:** `static/js/renderers/<algoritmo>_renderer.js`. Para asignación de recursos, la vista de tabla se complementa con `resource_graph_renderer.js`, que dibuja el grafo de estados y decisiones.

**Controles:** `static/js/<algoritmo>_controller.js`.

**Viewport:** `templates/<algoritmo>.html`. Los diagramas SVG comparten `static/js/diagram_viewport.js`: cada actualización se encaja en el cuadro y los controles permiten zoom y escalas horizontal/vertical independientes.

**Estilos compartidos:** `static/css/matrix.css`.

**API Flask:** `app.py`.

**Verificación:** `tests/test_<algoritmo>.py`.

## Experiencia didáctica común

Cada laboratorio dispone de:

- Paso siguiente.
- Paso anterior.
- Reproducir / Auto-Animar.
- Pausar.
- Reiniciar.
- Velocidad variable.
- Foco visual de la operación activa.
- Inspector contextual con fase, fórmula exacta, explicación de “por qué” y variables actuales.
- Sandbox editable para explorar parámetros y casos límite.

La actualización estructural de la navegación utiliza FLIP; el movimiento visual del contenido evita animar propiedades de layout.

## Fidelidad a los materiales entregados

### Decisión bajo incertidumbre

Los criterios y ejemplos numéricos por defecto se basan en las presentaciones proporcionadas sobre decisión bajo incertidumbre. Se conserva la terminología de alternativas, estados, pagos, Laplace, Wald, Hurwicz y Savage. El ejemplo por defecto usa:

```text
        s1      s2
a1    15000    8000
a2    14000   17910
a3     4000    7910
```

El ejemplo del material concluye `a2` para Laplace y Wald; con `α=0.6`, el cálculo de Hurwicz también selecciona `a2`. La implementación de Savage construye la matriz de arrepentimientos a partir del máximo de cada columna.

### Mochila 0/1

El ejemplo de las diapositivas usa `B=7`, beneficios `[16,19,23,28]`, pesos `[2,3,4,5]` y obtiene beneficio óptimo `44` con el vector `{1,0,0,1}`. La implementación sigue la definición `z_k(d)` y la comparación inclusión/exclusión del objeto.

### Asignación dinámica de recursos

El material proporcionado usa 5 brigadas y 3 países, con las funciones de rendimiento mostradas en las diapositivas. La política reconstruida es:

```text
País 1 = 1
País 2 = 3
País 3 = 1
Rendimiento global = 170
```

La pantalla de asignación incluye, además de la tabla DP, un **diagrama de posibilidades por etapas y estados**. Cada nodo representa las brigadas disponibles y cada arista representa una decisión factible `xᵢ`, pasando al estado `sᵢ₊₁ = sᵢ − xᵢ`. Durante la animación, la arista correspondiente al paso actual se resalta y, durante el backtracking, se va marcando la política óptima. Las demás aristas permanecen visibles para que el estudiante pueda comparar el espacio completo de decisiones.

El diagrama se genera como SVG desde `static/js/renderers/resource_graph_renderer.js`; no es una imagen estática y se adapta a los parámetros del sandbox.

### Árboles de decisión

El laboratorio sigue las presentaciones **Toma de Decisiones sin experimentación** y **Toma de Decisiones sin experimentación II**. El árbol comienza con un nodo de decisión cuadrado; sus alternativas conducen a nodos de azar con sucesos, probabilidades y pagos terminales. Se resuelve de derecha a izquierda: cada nodo de azar calcula `VE = Σ p(s) × pago total` y cada nodo de decisión elige la alternativa con mayor valor.

El ejemplo inicial corresponde al presupuesto de una serie: bajo presupuesto tiene pagos `5` y `−1`, con probabilidades `0.6` y `0.4`; alto presupuesto tiene pagos `4` y `−2`, con probabilidades `0.8` y `0.2`. Los valores esperados son `2.6` y `2.8`; por tanto se elige el alto presupuesto. El segundo ejemplo recorre la extensión multinivel de las diapositivas: conserva el pago del fracaso de la primera temporada y muestra por separado el pago terminal de cancelar la serie; reproduce el valor esperado óptimo `6.06` de la primera decisión.

El usuario puede editar el árbol en JSON. Cada nodo `chance` usa `events`, donde cada suceso requiere `probability` y puede tener un `payoff` y un nodo posterior `next`; en una rama con continuación, el pago se suma al valor de ese subárbol. Los nodos `terminal` permiten modelar pagos acumulados, como cancelar una temporada. Las probabilidades en cada nodo de azar tienen que sumar `1` (100 %). El motor valida esta condición y muestra los pagos, aportes ponderados, valores esperados y alternativa óptima paso a paso. No se utiliza entropía ni ganancia de información.

## Rutas

### Pantallas

- `/` — Árboles de decisión y portada integrada.
- `/incertidumbre` — Decisión bajo incertidumbre.
- `/mochila` — Mochila 0/1.
- `/asignacion` — Asignación de recursos.
- `/reemplazo` — Reemplazo de máquinas.

### APIs

- `GET /api/estado`
- `GET /api/decision-tree/default`
- `POST /api/decision-tree/steps`
- `GET /api/uncertainty/default`
- `POST /api/uncertainty/steps`
- `GET /api/knapsack/default`
- `POST /api/knapsack/steps`
- `GET /api/resource-allocation/default`
- `POST /api/resource-allocation/steps`
- `GET /api/machine-replacement/default`
- `POST /api/machine-replacement/steps`

## Instalación local

```bash
pip install -r requirements.txt
python app.py
```

También se puede usar Pipenv:

```bash
pipenv install
pipenv run python app.py
```

En ejecución local, `app.py` intenta abrir automáticamente el navegador. En un servidor, la apertura automática se desactiva mediante `FLASK_ENV=production` o `DEPLOYMENT=render`.

## Pruebas

```bash
python -m unittest discover -s tests -q
```

La suite integrada contiene pruebas matemáticas y de esquema para los cinco motores.

## Despliegue en Render

El repositorio incluye `render.yaml`, `.python-version` y `requirements.txt`. La configuración utiliza Python, instala las dependencias con `pip install -r requirements.txt` y sirve Flask mediante Gunicorn.

Conectando el repositorio en Render no hace falta crear manualmente estos valores si se utiliza el Blueprint definido en `render.yaml`. También se puede configurar el servicio manualmente con Build Command `pip install -r requirements.txt` y Start Command `gunicorn app:app`.

## Consideraciones

El proyecto no utiliza React, Vue, Tailwind, Bootstrap, Sass, Less, iconos externos ni CDNs de fuentes. La interfaz se apoya en HTML semántico, CSS nativo y JavaScript vanilla.

La prueba automatizada disponible en este entorno valida los motores Python y la sintaxis JavaScript. El arranque real de Flask requiere instalar las dependencias de `requirements.txt` en el entorno donde se ejecutará la aplicación.


## Cambios recientes

### Mochila 0/1: recorrido por columnas
La tabla `z_k(d)` ahora se revela por columnas: para cada capacidad `d` se recorren los objetos `k=1..n`. La recurrencia no cambia; cambia deliberadamente el orden didáctico del foco visual.

### Árboles de decisión: pagos por resultado e inducción hacia atrás
El árbol diferencia alternativas controlables y sucesos aleatorios. Cada suceso muestra la probabilidad asignada; cada resultado terminal muestra su pago; y las ramas muestran el aporte `p × pago total`. Los nodos de azar muestran el valor esperado y los nodos de decisión resaltan la alternativa de mayor valor. Las probabilidades de cada nodo de azar se validan para sumar 1.

### Reemplazo de máquinas
Se agregó el laboratorio `/reemplazo` siguiendo el ejemplo de **Programación Dinámica III**: la etapa `i` es el año `i`, el estado `t` es la edad de la máquina al inicio de ese año y las acciones son `K` (conservar) o `R` (reemplazar). Al terminar el horizonte se realiza `S` (desechar).

La recurrencia implementada es la del ejemplo docente:

`fᵢ(t) = max { r(t) − c(t) + fᵢ₊₁(t+1),  r(0) + s(t) − c(0) − I + fᵢ₊₁(1) }`

La primera alternativa corresponde a **K** y la segunda a **R**. La condición terminal es `fₙ₊₁(t)=s(t)`. En el ejemplo proporcionado: edad inicial `3`, horizonte `4`, costo de adquisición `100,000` y edad máxima `6`. El resultado es `f₁(3)=55,300`, con políticas óptimas `RKKR` y `RRKK`.

El diagrama es una red temporal con eje horizontal **Año de decisión**, eje vertical **Edad de la máquina**, nodos por estado, arcos `K` y `R`, arcos `S` hacia `Final`, y resaltado del paso activo.

## Datos visibles antes de ejecutar

Cada laboratorio genera una ficha **Datos del problema** antes de los controles de reproducción. La ficha se actualiza con los inputs y sirve como comprobación visual del problema que se va a resolver.

- Árboles: nodos de decisión y azar, caminos terminales, probabilidad de ruta y pago acumulado.
- Incertidumbre: matriz de pagos, alternativas, estados y α de Hurwicz.
- Mochila 0/1: objetos con identificador `I`, beneficio `Gᵢ` y peso `Vᵢ`.
- Asignación: brigadas, etapas y matriz de rendimientos.
- Reemplazo: edad, ingreso `r(t)`, operación `c(t)` y desecho `s(t)`.

## Reemplazo de máquinas: modelo docente

La pantalla de reemplazo usa el ejemplo de Programación Dinámica III proporcionado: etapa = año, estado = edad de la máquina, acciones K (conservar) y R (reemplazar), con S (desechar) al final del horizonte. El diagrama usa el mismo eje conceptual de **Año de decisión × Edad de la máquina** y hace visibles las transiciones K/R y el destino Final.

Con los datos del ejemplo, el cálculo hacia atrás produce `f₁(3) = 55,300` y las dos políticas óptimas `RKKR` y `RRKK`.

## Apariencia

El menú global incluye cambio de **Tema** (`Sistema`, `Claro`, `Oscuro`) y **Acento** (`Rojo`, `Cobalto`, `Naranja`). La selección se conserva en `localStorage` del navegador.

