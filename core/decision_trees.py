"""Generador paso a paso para árboles de decisión categóricos.

La interfaz se apoya en tres ideas estándar:
- Entropía + Ganancia de Información.
- Índice Gini + reducción de impureza.
- Selección recursiva de la mejor característica.

La presentación de estos conceptos no se encuentra en los archivos docentes
entregados para este proyecto, por lo que esta implementación no afirma
fidelidad literal a una diapositiva concreta.
"""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from dataclasses import dataclass
from math import log2
from typing import Any

from .step_schema import crear_paso


DEFAULT_DATASET: list[dict[str, str]] = [
    {"Clima": "Soleado", "Humedad": "Alta", "Viento": "Débil", "Jugar": "No"},
    {"Clima": "Soleado", "Humedad": "Alta", "Viento": "Fuerte", "Jugar": "No"},
    {"Clima": "Nublado", "Humedad": "Alta", "Viento": "Débil", "Jugar": "Sí"},
    {"Clima": "Nublado", "Humedad": "Alta", "Viento": "Fuerte", "Jugar": "Sí"},
    {"Clima": "Lluvia", "Humedad": "Alta", "Viento": "Débil", "Jugar": "Sí"},
    {"Clima": "Lluvia", "Humedad": "Normal", "Viento": "Débil", "Jugar": "Sí"},
    {"Clima": "Lluvia", "Humedad": "Normal", "Viento": "Fuerte", "Jugar": "No"},
    {"Clima": "Nublado", "Humedad": "Normal", "Viento": "Fuerte", "Jugar": "Sí"},
    {"Clima": "Soleado", "Humedad": "Normal", "Viento": "Débil", "Jugar": "Sí"},
    {"Clima": "Soleado", "Humedad": "Normal", "Viento": "Fuerte", "Jugar": "Sí"},
    {"Clima": "Lluvia", "Humedad": "Normal", "Viento": "Fuerte", "Jugar": "No"},
    {"Clima": "Nublado", "Humedad": "Alta", "Viento": "Débil", "Jugar": "Sí"},
    {"Clima": "Soleado", "Humedad": "Alta", "Viento": "Débil", "Jugar": "No"},
    {"Clima": "Lluvia", "Humedad": "Alta", "Viento": "Fuerte", "Jugar": "No"},
]


class ArbolInputError(ValueError):
    """Error controlado del sandbox; nunca debe llegar como traza al usuario."""


@dataclass(slots=True)
class TreeNode:
    id: str
    majority: str
    samples: list[int]
    depth: int
    feature: str | None = None
    prediction: str | None = None
    children: dict[str, "TreeNode"] | None = None

    def snapshot(self) -> dict[str, Any]:
        children = self.children or {}
        return {
            "id": self.id,
            "etiqueta": self.feature if self.feature else f"Clase: {self.prediction or self.majority}",
            "caracteristica": self.feature,
            "prediccion": self.prediction,
            "mayoria": self.majority,
            "muestras": len(self.samples),
            "profundidad": self.depth,
            "es_hoja": self.feature is None,
            "hijos": list(children),
        }


def _clean_dataset(dataset: Any, target: str, max_rows: int = 100) -> list[dict[str, str]]:
    if not isinstance(dataset, list) or not dataset:
        raise ArbolInputError(
            "Necesitamos al menos una fila de datos. Prueba con dos o más ejemplos para que el árbol pueda comparar patrones."
        )
    if len(dataset) > max_rows:
        raise ArbolInputError(f"El sandbox admite hasta {max_rows} filas para conservar una visualización clara.")

    clean: list[dict[str, str]] = []
    for index, row in enumerate(dataset, start=1):
        if not isinstance(row, dict):
            raise ArbolInputError(f"La fila {index} no tiene formato de registro. Cada fila debe ser un objeto con pares campo/valor.")
        normalized = {str(k).strip(): str(v).strip() for k, v in row.items() if str(k).strip()}
        if target not in normalized:
            raise ArbolInputError(f"La fila {index} no contiene la variable objetivo «{target}».")
        if not normalized[target]:
            raise ArbolInputError(f"La fila {index} tiene la clase objetivo vacía. Ese valor es necesario para aprender.")
        clean.append(normalized)

    fields = set().union(*(row.keys() for row in clean))
    if len(fields) < 2:
        raise ArbolInputError("Hace falta al menos una característica además de la variable objetivo.")
    return clean


def _feature_names(dataset: list[dict[str, str]], target: str) -> list[str]:
    names: list[str] = []
    for key in dataset[0].keys():
        if key != target and key not in names:
            names.append(key)
    return names


def _class_counts(dataset: list[dict[str, str]], indices: list[int], target: str) -> Counter[str]:
    return Counter(dataset[i][target] for i in indices)


def _entropy(dataset: list[dict[str, str]], indices: list[int], target: str) -> float:
    counts = _class_counts(dataset, indices, target)
    total = len(indices)
    if not total:
        return 0.0
    return -sum((count / total) * log2(count / total) for count in counts.values() if count)


def _gini(dataset: list[dict[str, str]], indices: list[int], target: str) -> float:
    counts = _class_counts(dataset, indices, target)
    total = len(indices)
    if not total:
        return 0.0
    return 1.0 - sum((count / total) ** 2 for count in counts.values())


def _split_indices(dataset: list[dict[str, str]], indices: list[int], feature: str) -> dict[str, list[int]]:
    groups: dict[str, list[int]] = {}
    for i in indices:
        value = dataset[i].get(feature, "(vacío)") or "(vacío)"
        groups.setdefault(value, []).append(i)
    return dict(sorted(groups.items(), key=lambda item: item[0]))


def _weighted_impurity(
    dataset: list[dict[str, str]],
    groups: dict[str, list[int]],
    target: str,
    metric: str,
) -> float:
    total = sum(len(group) for group in groups.values())
    if not total:
        return 0.0
    fn = _entropy if metric == "entropy" else _gini
    return sum(len(group) / total * fn(dataset, group, target) for group in groups.values())


def _score_feature(dataset: list[dict[str, str]], indices: list[int], feature: str, target: str, metric: str) -> dict[str, Any]:
    groups = _split_indices(dataset, indices, feature)
    if metric == "entropy":
        parent = _entropy(dataset, indices, target)
        child = _weighted_impurity(dataset, groups, target, metric)
        score = parent - child
        return {"score": score, "parent": parent, "child": child, "groups": groups, "metric_name": "Ganancia de Información"}
    parent = _gini(dataset, indices, target)
    child = _weighted_impurity(dataset, groups, target, metric)
    score = parent - child
    return {"score": score, "parent": parent, "child": child, "groups": groups, "metric_name": "Reducción de Gini"}


def _fmt(value: float) -> str:
    return f"{value:.6f}".rstrip("0").rstrip(".")


def _tree_visual(
    root: TreeNode | None,
    active_node: str | None = None,
    path: list[str] | None = None,
    sample: dict[str, str] | None = None,
    active_feature: str | None = None,
    candidates: list[str] | None = None,
    target: str = "Jugar",
    criterion: str = "entropy",
    split_info: dict[str, Any] | None = None,
    active_edge_value: str | None = None,
    dataset: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """Serializa el árbol junto con probabilidades de ramas y suma-producto."""
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []

    source = dataset or []

    def impurity(indices: list[int]) -> float:
        return _entropy(source, indices, target) if criterion == "entropy" else _gini(source, indices, target)

    def walk(node: TreeNode) -> None:
        base = node.snapshot()
        child_items = list((node.children or {}).items())
        total = max(1, len(node.samples))
        child_stats: list[dict[str, Any]] = []
        for value, child in child_items:
            prob = len(child.samples) / total
            child_impurity = impurity(child.samples)
            contribution = prob * child_impurity
            child_stats.append({
                "valor": value,
                "probabilidad": prob,
                "impureza_hijo": child_impurity,
                "aporte_ponderado": contribution,
            })
            edges.append({
                "origen": node.id,
                "destino": child.id,
                "etiqueta": value,
                "probabilidad": prob,
                "muestras_hijo": len(child.samples),
                "muestras_padre": len(node.samples),
                "impureza_hijo": child_impurity,
                "aporte_ponderado": contribution,
            })
        if child_stats:
            weighted = sum(item["aporte_ponderado"] for item in child_stats)
            terms = " + ".join(
                f"{item['probabilidad']:.3f}·{item['impureza_hijo']:.3f}" for item in child_stats
            )
            base["suma_producto"] = {
                "formula": f"Σ p(v)·I(v) = {terms} = {weighted:.3f}",
                "valor": weighted,
                "terminos": child_stats,
            }
        elif split_info:
            groups = split_info.get("groups", {})
            total_split = max(1, sum(len(group) for group in groups.values()))
            fn = _entropy if criterion == "entropy" else _gini
            terms_data = []
            for value, group in groups.items():
                prob = len(group) / total_split
                imp = fn(source, group, target)
                terms_data.append((value, prob, imp, prob * imp))
            weighted = sum(item[3] for item in terms_data)
            terms = " + ".join(f"{prob:.3f}·{imp:.3f}" for _, prob, imp, _ in terms_data)
            base["suma_producto"] = {
                "formula": f"Σ p(v)·I(v) = {terms} = {weighted:.3f}",
                "valor": weighted,
                "terminos": [
                    {"valor": value, "probabilidad": prob, "impureza_hijo": imp, "aporte_ponderado": contribution}
                    for value, prob, imp, contribution in terms_data
                ],
            }
        nodes.append(base)
        for child in (node.children or {}).values():
            walk(child)

    if root is not None:
        walk(root)

    return {
        "tipo": "arbol",
        "nodos": nodes,
        "aristas": edges,
        "nodo_activo": active_node,
        "caracteristica_activa": active_feature,
        "caracteristicas_candidatas": candidates or [],
        "active_edge_value": active_edge_value,
        "camino": path or [],
        "muestra": sample or {},
        "criterio": criterion,
    }



def build_steps(
    dataset: Any = None,
    *,
    target: str = "Jugar",
    criterion: str = "entropy",
    max_depth: int = 6,
    sample_index: int = 0,
) -> list[dict[str, Any]]:
    """Construye los pasos pedagógicos de crecimiento y recorrido del árbol."""
    data = _clean_dataset(DEFAULT_DATASET if dataset is None else dataset, target)
    criterion = criterion if criterion in {"entropy", "gini"} else "entropy"
    try:
        max_depth = int(max_depth)
    except (TypeError, ValueError):
        max_depth = 6
    max_depth = min(max(1, max_depth), 8)
    try:
        sample_index = int(sample_index)
    except (TypeError, ValueError):
        sample_index = 0
    sample_index = min(max(0, sample_index), len(data) - 1)

    features = _feature_names(data, target)
    steps: list[dict[str, Any]] = []
    root: TreeNode | None = None
    node_counter = 0
    path_for_sample: list[str] = []

    def next_id() -> str:
        nonlocal node_counter
        node_counter += 1
        return f"n{node_counter}"

    def append(
        *,
        fase: str,
        titulo: str,
        formula: str,
        explicacion: str,
        variables: dict[str, Any],
        active_node: str | None = None,
        active_feature: str | None = None,
        candidates: list[str] | None = None,
        split_info: dict[str, Any] | None = None,
        active_edge_value: str | None = None,
    ) -> None:
        steps.append(
            crear_paso(
                algoritmo="arbol_decision",
                paso=len(steps) + 1,
                total_pasos=0,
                fase=fase,
                titulo=titulo,
                formula=formula,
                explicacion=explicacion,
                variables=variables,
                enfoque={"tipo": "nodo", "nodo": active_node, "caracteristica": active_feature},
                estado_visual=_tree_visual(
                    root,
                    active_node=active_node,
                    active_feature=active_feature,
                    candidates=candidates,
                    path=path_for_sample,
                    sample=data[sample_index],
                    target=target,
                    criterion=criterion,
                    split_info=split_info,
                    active_edge_value=active_edge_value,
                    dataset=data,
                ),
            )
        )

    root_indices = list(range(len(data)))
    root_majority = _class_counts(data, root_indices, target).most_common(1)[0][0]
    root = TreeNode(id=next_id(), majority=root_majority, samples=root_indices, depth=0)
    parent_metric = _entropy(data, root_indices, target) if criterion == "entropy" else _gini(data, root_indices, target)

    append(
        fase="Preparación",
        titulo="Partimos de todos los ejemplos",
        formula=("H(S) = -Σ p(c) log₂ p(c)" if criterion == "entropy" else "Gini(S) = 1 - Σ p(c)²"),
        explicacion=(
            "El árbol comienza observando todos los casos. Primero medimos qué tan mezcladas están las clases; esa medida nos servirá para juzgar cada posible separación."
        ),
        variables={
            "filas": len(root_indices),
            "clases": dict(_class_counts(data, root_indices, target)),
            "impureza_inicial": _fmt(parent_metric),
            "criterio": "Entropía + Ganancia de Información" if criterion == "entropy" else "Gini + Reducción de impureza",
        },
        active_node=root.id,
        candidates=features,
    )

    def grow(indices: list[int], available_features: list[str], depth: int, parent_node: TreeNode) -> None:
        counts = _class_counts(data, indices, target)
        majority = counts.most_common(1)[0][0]
        parent_node.majority = majority
        parent_node.samples = indices
        impurity = _entropy(data, indices, target) if criterion == "entropy" else _gini(data, indices, target)

        append(
            fase="Diagnóstico del nodo",
            titulo=f"¿Este grupo ya es suficientemente claro? (nivel {depth})",
            formula=("H(S) = -Σ p(c) log₂ p(c)" if criterion == "entropy" else "Gini(S) = 1 - Σ p(c)²"),
            explicacion=(
                f"Hay {len(indices)} ejemplos en este nodo. Si todos comparten la misma clase, ya no necesitamos dividirlos. Si no, buscamos la característica que más reduzca la mezcla."
            ),
            variables={
                "nivel": depth,
                "ejemplos": len(indices),
                "clases": dict(counts),
                "clase_mayoritaria": majority,
                "impureza": _fmt(impurity),
                "caracteristicas_disponibles": available_features,
            },
            active_node=parent_node.id,
            candidates=available_features,
        )

        if len(counts) == 1:
            parent_node.prediction = next(iter(counts))
            append(
                fase="Creación de hoja",
                titulo=f"Hoja: predecimos «{parent_node.prediction}»",
                formula="predicción = única clase presente en el nodo",
                explicacion="Todos los ejemplos de este grupo tienen la misma respuesta. Seguir separando no aportaría información nueva, así que cerramos esta rama.",
                variables={"prediccion": parent_node.prediction, "ejemplos": len(indices)},
                active_node=parent_node.id,
            )
            return

        if not available_features:
            parent_node.prediction = majority
            append(
                fase="Creación de hoja",
                titulo=f"No quedan características: usamos la mayoría ({majority})",
                formula="predicción = argmax_c frecuencia(c)",
                explicacion="Ya probamos todas las características disponibles. Para no inventar una regla nueva, la hoja toma la clase que aparece con mayor frecuencia en este grupo.",
                variables={"prediccion": majority, "frecuencia_clase": dict(counts)},
                active_node=parent_node.id,
            )
            return

        if depth >= max_depth:
            parent_node.prediction = majority
            append(
                fase="Límite del árbol",
                titulo=f"Alcanzamos la profundidad máxima: {majority}",
                formula="predicción = clase mayoritaria del nodo",
                explicacion="El sandbox detiene el crecimiento en este nivel para mantener un árbol manejable. La decisión más prudente aquí es usar la clase mayoritaria.",
                variables={"profundidad_maxima": max_depth, "prediccion": majority},
                active_node=parent_node.id,
            )
            return

        scores: list[tuple[str, dict[str, Any]]] = []
        for feature in available_features:
            result = _score_feature(data, indices, feature, target, criterion)
            scores.append((feature, result))
            group_summary = {value: len(group) for value, group in result["groups"].items()}
            if criterion == "entropy":
                formula = f"IG(S,{feature}) = { _fmt(result['parent']) } - { _fmt(result['child']) } = { _fmt(result['score']) }"
            else:
                formula = f"ΔGini(S,{feature}) = { _fmt(result['parent']) } - { _fmt(result['child']) } = { _fmt(result['score']) }"
            append(
                fase="Evaluación de características",
                titulo=f"Medimos «{feature}»",
                formula=formula,
                explicacion=f"Probamos esta característica como punto de separación. Buscamos que los grupos resultantes queden más puros; por eso nos interesa la mayor reducción de impureza.",
                variables={
                    "caracteristica": feature,
                    "impureza_padre": _fmt(result["parent"]),
                    "impureza_ponderada_hijos": _fmt(result["child"]),
                    "puntuacion": _fmt(result["score"]),
                    "particiones": group_summary,
                    "criterio": result["metric_name"],
                },
                active_node=parent_node.id,
                active_feature=feature,
                candidates=available_features,
            )

        scores.sort(key=lambda item: (-item[1]["score"], available_features.index(item[0])))
        best_feature, best_result = scores[0]
        parent_node.feature = best_feature
        parent_node.children = {}

        append(
            fase="Selección de característica",
            titulo=f"Elegimos «{best_feature}» para dividir el nodo",
            formula=f"mejor característica = argmax({', '.join(feature for feature, _ in scores)})",
            explicacion=f"«{best_feature}» produce la mayor reducción de impureza entre las opciones disponibles. El árbol gana claridad al usarla ahora.",
            variables={
                "caracteristica_elegida": best_feature,
                "puntuacion_elegida": _fmt(best_result["score"]),
                "puntuaciones": {feature: _fmt(result["score"]) for feature, result in scores},
            },
            active_node=parent_node.id,
            active_feature=best_feature,
            split_info=best_result,
        )

        remaining = [feature for feature in available_features if feature != best_feature]
        for value, child_indices in best_result["groups"].items():
            child = TreeNode(id=next_id(), majority=_class_counts(data, child_indices, target).most_common(1)[0][0], samples=child_indices, depth=depth + 1)
            parent_node.children[value] = child
            append(
                fase="Expansión del árbol",
                titulo=f"Abrimos la rama «{best_feature} = {value}»",
                formula=f"S_{value} = {{ejemplos con {best_feature} = {value}}}",
                explicacion=f"Ahora nos quedamos solo con los ejemplos que siguen la condición «{best_feature} = {value}». Esa rama podrá descubrir una regla más específica.",
                variables={
                    "caracteristica": best_feature,
                    "valor": value,
                    "ejemplos_en_rama": len(child_indices),
                    "clase_mayoritaria": child.majority,
                },
                active_node=child.id,
                active_feature=best_feature,
                split_info=best_result,
                active_edge_value=value,
            )
            grow(child_indices, remaining, depth + 1, child)

    grow(root_indices, features, 0, root)

    # Recorrido de un ejemplo seleccionado.
    node = root
    path_for_sample = []
    sample = data[sample_index]
    prediction: str | None = None
    append(
        fase="Recorrido guiado",
        titulo="Probamos una observación del conjunto",
        formula="seguir la rama cuyo valor coincide con la característica del ejemplo",
        explicacion="Con el árbol aprendido, ahora caminamos por una observación real. El objetivo es ver cómo una cadena de decisiones simples termina en una predicción.",
        variables={"indice_ejemplo": sample_index, "ejemplo": sample, "clase_real": sample[target]},
        active_node=root.id,
    )

    while node is not None:
        path_for_sample.append(node.id)
        if node.feature is None:
            prediction = node.prediction or node.majority
            append(
                fase="Recorrido guiado",
                titulo=f"Llegamos a la hoja: «{prediction}»",
                formula="predicción = valor almacenado en la hoja",
                explicacion=f"Esta es la respuesta final del recorrido. Comparamos después con la clase real del ejemplo para que puedas observar si el árbol acertó.",
                variables={
                    "prediccion": prediction,
                    "clase_real": sample[target],
                    "acierto": prediction == sample[target],
                    "camino": path_for_sample,
                },
                active_node=node.id,
            )
            break

        value = sample.get(node.feature, "(vacío)") or "(vacío)"
        child = (node.children or {}).get(value)
        append(
            fase="Recorrido guiado",
            titulo=f"Preguntamos: ¿{node.feature} = {value}?",
            formula=f"rama = hijo({node.feature} = {value})",
            explicacion=f"El árbol consulta la característica «{node.feature}» del ejemplo. Como vale «{value}», seguimos esa rama y no las demás.",
            variables={
                "caracteristica": node.feature,
                "valor_observado": value,
                "ramas_disponibles": list((node.children or {}).keys()),
                "rama_encontrada": child is not None,
            },
            active_node=node.id,
            active_feature=node.feature,
            active_edge_value=value,
        )
        if child is None:
            prediction = node.majority
            append(
                fase="Recorrido guiado",
                titulo=f"No existe esa rama; usamos la mayoría ({prediction})",
                formula="predicción = mayoría del nodo actual",
                explicacion="El valor del ejemplo no apareció mientras se entrenaba el árbol. Para que el sandbox siga siendo seguro, hacemos una predicción de respaldo usando la clase mayoritaria del nodo.",
                variables={"prediccion": prediction, "valor_no_visto": value, "clase_real": sample[target]},
                active_node=node.id,
            )
            break
        node = child

    if prediction is not None:
        append(
            fase="Cierre",
            titulo="El recorrido queda registrado",
            formula="acierto = (predicción = clase real)",
            explicacion="Terminamos comparando la predicción con la respuesta conocida. Este último paso convierte el recorrido en evidencia observable para aprender del comportamiento del árbol.",
            variables={
                "prediccion": prediction,
                "clase_real": sample[target],
                "acierto": prediction == sample[target],
                "total_nodos": node_counter,
            },
            active_node=path_for_sample[-1] if path_for_sample else root.id,
        )

    total = len(steps)
    for step in steps:
        step["total_pasos"] = total
    return steps


def default_payload() -> dict[str, Any]:
    """Configuración inicial segura para el frontend."""
    return {
        "dataset": deepcopy(DEFAULT_DATASET),
        "target": "Jugar",
        "criterion": "entropy",
        "max_depth": 4,
        "sample_index": 0,
    }
