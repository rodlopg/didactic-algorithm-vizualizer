"""Árboles de decisión económicos con probabilidades, pagos y valor esperado.

La implementación sigue el enfoque de las presentaciones: nodos de decisión,
nodos de suceso/azar, pagos en los resultados y evaluación por inducción hacia
atrás. No calcula entropía, Gini ni ganancia de información.
"""
from __future__ import annotations

from copy import deepcopy
from math import isfinite
from typing import Any

from .step_schema import crear_paso


DEFAULT_TREE: dict[str, Any] = {
    "type": "decision",
    "label": "Elegir el presupuesto de la serie",
    "options": [
        {
            "label": "Bajo presupuesto",
            "next": {
                "type": "chance",
                "label": "Resultado con presupuesto bajo",
                "events": [
                    {"label": "Éxito", "probability": 0.6, "payoff": 5},
                    {"label": "Fracaso", "probability": 0.4, "payoff": -1},
                ],
            },
        },
        {
            "label": "Alto presupuesto",
            "next": {
                "type": "chance",
                "label": "Resultado con presupuesto alto",
                "events": [
                    {"label": "Éxito", "probability": 0.8, "payoff": 4},
                    {"label": "Fracaso", "probability": 0.2, "payoff": -2},
                ],
            },
        },
    ],
}


class ArbolInputError(ValueError):
    """Error de validación explicable en la interfaz."""


def default_payload() -> dict[str, Any]:
    return {"tree": deepcopy(DEFAULT_TREE)}


def _number(value: Any, context: str, *, min_value: float | None = None, max_value: float | None = None) -> float:
    if isinstance(value, bool):
        raise ArbolInputError(f"{context}: usa un número, no un valor verdadero/falso.")
    try:
        n = float(value)
    except (TypeError, ValueError):
        raise ArbolInputError(f"{context}: hace falta un número válido.") from None
    if not isfinite(n):
        raise ArbolInputError(f"{context}: el número debe ser finito.")
    if min_value is not None and n < min_value:
        raise ArbolInputError(f"{context}: el valor no puede ser menor que {min_value}.")
    if max_value is not None and n > max_value:
        raise ArbolInputError(f"{context}: el valor no puede superar {max_value}.")
    return n


def _normalise_tree(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise ArbolInputError("El árbol debe ser un objeto JSON. Usa el ejemplo inicial como plantilla.")
    counter = 0

    def normalise(node_raw: Any, path: str, depth: int) -> dict[str, Any]:
        nonlocal counter
        if depth > 8:
            raise ArbolInputError("El árbol admite hasta 8 niveles para mantener el diagrama legible.")
        if not isinstance(node_raw, dict):
            raise ArbolInputError(f"{path}: cada nodo debe ser un objeto JSON.")
        kind = str(node_raw.get("type", "")).strip().lower()
        if kind not in {"decision", "chance", "terminal"}:
            raise ArbolInputError(f"{path}: el tipo debe ser 'decision', 'chance' o 'terminal'.")
        label = str(node_raw.get("label", "")).strip()
        if not label:
            raise ArbolInputError(f"{path}: cada nodo necesita una etiqueta legible.")
        counter += 1
        if counter > 50:
            raise ArbolInputError("El árbol admite hasta 50 nodos internos para mantener la visualización clara.")
        if kind == "terminal":
            payoff = _number(node_raw.get("payoff"), f"Pago terminal de «{label}»")
            return {
                "id": f"node-{counter}", "type": "terminal", "label": label,
                "value": payoff, "calculated": True, "depth": depth, "branches": [],
                "best_branch": None, "terminal_payoff": payoff,
            }
        node: dict[str, Any] = {
            "id": f"node-{counter}", "type": kind, "label": label,
            "value": None, "calculated": False, "depth": depth, "branches": [],
            "best_branch": None,
        }
        branches_key = "options" if kind == "decision" else "events"
        branches = node_raw.get(branches_key)
        if not isinstance(branches, list) or len(branches) < 2:
            noun = "alternativas" if kind == "decision" else "sucesos"
            raise ArbolInputError(f"{path}: agrega al menos dos {noun}.")
        if len(branches) > 12:
            raise ArbolInputError(f"{path}: admite hasta 12 ramas en un mismo nodo.")
        probability_sum = 0.0
        for idx, raw_branch in enumerate(branches, start=1):
            branch_path = f"{path} → rama {idx}"
            if not isinstance(raw_branch, dict):
                raise ArbolInputError(f"{branch_path}: cada rama debe ser un objeto.")
            branch_label = str(raw_branch.get("label", "")).strip()
            if not branch_label:
                raise ArbolInputError(f"{branch_path}: escribe el nombre de la alternativa o suceso.")
            payoff = _number(raw_branch.get("payoff", 0), f"Pago de «{branch_label}»")
            probability: float | None = None
            if kind == "chance":
                if "probability" not in raw_branch:
                    raise ArbolInputError(f"{branch_path}: asigna una probabilidad entre 0 y 1.")
                probability = _number(raw_branch["probability"], f"Probabilidad de «{branch_label}»", min_value=0, max_value=1)
                probability_sum += probability
            child_raw = raw_branch.get("next")
            child: dict[str, Any] | None = None
            branch_payoff = payoff
            if child_raw is not None:
                child = normalise(child_raw, branch_path, depth + 1)
            else:
                # Hoja terminal implícita: el pago corresponde al resultado final.
                counter += 1
                if counter > 50:
                    raise ArbolInputError("El árbol admite hasta 50 nodos para mantener la visualización clara.")
                child = {
                    "id": f"node-{counter}", "type": "terminal", "label": branch_label,
                    "value": payoff, "calculated": True, "depth": depth + 1,
                    "branches": [], "best_branch": None, "terminal_payoff": payoff,
                }
                branch_payoff = 0.0
            node["branches"].append({
                "id": f"edge-{node['id']}-{idx}", "label": branch_label,
                "probability": probability, "payoff": branch_payoff,
                "terminal_payoff": payoff if raw_branch.get("next") is None else None,
                "child": child, "value": None, "contribution": None,
                "evaluated": False, "selected": False,
            })
        if kind == "chance" and abs(probability_sum - 1.0) > 0.001:
            raise ArbolInputError(
                f"{path}: las probabilidades deben sumar 1 (100 %); ahora suman {probability_sum:.4g}."
            )
        return node

    root = normalise(raw, "Nodo inicial", 0)
    if root["type"] != "decision":
        raise ArbolInputError("El árbol debe comenzar con un nodo de decisión.")
    return root


def _fmt(value: float | None) -> str:
    if value is None:
        return "—"
    return f"{value:,.4f}".rstrip("0").rstrip(".").replace(",", "X").replace(".", ",").replace("X", ".")


def _snapshot(root: dict[str, Any], active_node: str | None = None, active_edge: str | None = None) -> dict[str, Any]:
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []

    def walk(node: dict[str, Any]) -> None:
        kind = node["type"]
        nodes.append({
            "id": node["id"], "tipo": kind,
            "etiqueta": node["label"], "valor": node["value"],
            "calculado": node["calculated"], "profundidad": node["depth"],
            "terminal": kind == "terminal", "mejor_rama": node["best_branch"],
            "nodo_terminal_pago": node.get("terminal_payoff"),
        })
        for branch in node["branches"]:
            child = branch["child"]
            edges.append({
                "id": branch["id"], "origen": node["id"], "destino": child["id"],
                "etiqueta": branch["label"], "tipo": kind,
                "probabilidad": branch["probability"], "pago": branch["payoff"],
                "pago_terminal": branch["terminal_payoff"], "valor_alternativa": branch["value"],
                "contribucion": branch["contribution"], "evaluada": branch["evaluated"],
                "seleccionada": branch["selected"],
            })
            walk(child)

    walk(root)
    return {"tipo": "arbol_decision_bayes", "nodos": nodes, "aristas": edges,
            "nodo_activo": active_node, "arista_activa": active_edge,
            "maximizar": True}


def build_steps(tree: Any = None) -> list[dict[str, Any]]:
    """Evalúa un árbol económico con probabilidad y pago, resolviendo de abajo arriba."""
    root = _normalise_tree(DEFAULT_TREE if tree is None else tree)
    steps: list[dict[str, Any]] = []

    def append(fase: str, titulo: str, formula: str, explicacion: str,
               variables: dict[str, Any], active_node: str | None = None,
               active_edge: str | None = None) -> None:
        steps.append(crear_paso(
            algoritmo="arbol_decision_bayes", paso=len(steps) + 1, total_pasos=0,
            fase=fase, titulo=titulo, formula=formula, explicacion=explicacion,
            variables=variables, enfoque={"tipo": "nodo", "nodo": active_node, "arista": active_edge},
            estado_visual=_snapshot(root, active_node, active_edge),
        ))

    def walk_nodes(node: dict[str, Any]) -> tuple[float, list[tuple[str, float]]]:
        if node["type"] == "terminal":
            value = float(node["value"] or 0)
            return value, []

        # Primero se resuelven los subárboles que siguen a cada rama.
        child_values: dict[str, float] = {}
        for branch in node["branches"]:
            child_value, _ = walk_nodes(branch["child"])
            child_values[branch["id"]] = child_value

        if node["type"] == "chance":
            contributions: list[tuple[str, float]] = []
            for branch in node["branches"]:
                child_value = child_values[branch["id"]]
                probability = float(branch["probability"] or 0)
                immediate = float(branch["payoff"] or 0)
                reward_total = immediate + child_value
                contribution = probability * reward_total
                branch["contribution"] = contribution
                branch["evaluated"] = True
                contributions.append((branch["label"], contribution))
                event_description = f"p = {_fmt(probability)}; pago del suceso = {_fmt(reward_total)}"
                append(
                    "Evaluación de un suceso",
                    f"Calculamos el aporte de «{branch['label']}»",
                    f"p × (pago + valor futuro) = {_fmt(probability)} × {_fmt(reward_total)} = {_fmt(contribution)}",
                    f"El suceso «{branch['label']}» tiene probabilidad {_fmt(probability)}. Multiplicamos esa probabilidad por el pago del suceso más el valor de cualquier decisión posterior. Este es el aporte de esta rama al valor esperado.",
                    {"suceso": branch["label"], "probabilidad": event_description,
                     "pago_mas_valor_futuro": _fmt(reward_total), "aporte_esperado": _fmt(contribution)},
                    node["id"], branch["id"],
                )
            total = sum(value for _, value in contributions)
            node["value"] = total
            node["calculated"] = True
            terms = " + ".join(_fmt(value) for _, value in contributions)
            append(
                "Valor esperado",
                f"Obtenemos el valor esperado de «{node['label']}»",
                f"VE = Σ p(suceso) × pago total = {terms} = {_fmt(total)}",
                "Sumamos los aportes ponderados de todos los sucesos. Como sus probabilidades suman 1, el resultado representa el pago medio esperado para este nodo si se llega a él.",
                {"nodo_de_azar": node["label"], "aportes": {label: _fmt(value) for label, value in contributions},
                 "valor_esperado": _fmt(total)},
                node["id"],
            )
            return total, contributions

        # Nodo de decisión: comparar el pago total de cada alternativa y conservar el máximo.
        alternatives: list[tuple[dict[str, Any], float]] = []
        for branch in node["branches"]:
            child_value = child_values[branch["id"]]
            total_value = float(branch["payoff"] or 0) + child_value
            branch["value"] = total_value
            branch["evaluated"] = True
            alternatives.append((branch, total_value))
            append(
                "Comparación de alternativas",
                f"Evaluamos «{branch['label']}»",
                f"Pago inmediato + valor futuro = {_fmt(float(branch['payoff'] or 0))} + {_fmt(child_value)} = {_fmt(total_value)}",
                f"La alternativa «{branch['label']}» vale {_fmt(total_value)}. Si conduce a un nodo de azar, usamos el valor esperado que ya calculamos para ese subárbol; si es un resultado terminal, usamos su pago.",
                {"alternativa": branch["label"], "pago_inmediato": _fmt(float(branch["payoff"] or 0)),
                 "valor_siguiente": _fmt(child_value), "valor_total": _fmt(total_value)},
                node["id"], branch["id"],
            )
        best_branch, best_value = max(alternatives, key=lambda item: item[1])
        node["best_branch"] = best_branch["id"]
        for branch, _ in alternatives:
            branch["selected"] = branch["id"] == best_branch["id"]
        node["value"] = best_value
        node["calculated"] = True
        append(
            "Decisión óptima",
            f"Elegimos «{best_branch['label']}»",
            f"V* = máx({'; '.join(_fmt(value) for _, value in alternatives)}) = {_fmt(best_value)}",
            f"Comparamos los valores de todas las alternativas y conservamos la de mayor pago esperado. Esa es la decisión óptima para el nodo «{node['label']}».",
            {"alternativas": {branch["label"]: _fmt(value) for branch, value in alternatives},
             "alternativa_óptima": best_branch["label"], "valor_óptimo": _fmt(best_value)},
            node["id"], best_branch["id"],
        )
        return best_value, [(branch["label"], value) for branch, value in alternatives]

    append(
        "Preparación",
        "Identificamos decisiones, sucesos y pagos",
        "Valor de un nodo de azar = Σ p(s) × pago total; valor de un nodo de decisión = máx(alternativas)",
        "El árbol representa una decisión controlable (cuadrado) y sucesos aleatorios (círculos). Cada suceso tiene una probabilidad y cada resultado un pago. Resolveremos desde los resultados finales hacia la decisión inicial: primero los valores esperados y después la mejor alternativa.",
        {"alternativas_iniciales": [branch["label"] for branch in root["branches"]],
         "regla_de_azar": "sumar probabilidad × pago total", "regla_de_decisión": "elegir el mayor pago esperado"},
        root["id"],
    )
    optimum, _ = walk_nodes(root)
    append(
        "Solución final",
        f"Política óptima: valor esperado {_fmt(optimum)}",
        f"V*(inicio) = {_fmt(optimum)}",
        "La inducción hacia atrás ya ha resuelto todos los nodos. La rama resaltada desde el nodo inicial indica la decisión óptima; los nodos posteriores muestran sus valores esperados y los pagos de cada resultado.",
        {"valor_esperado_óptimo": _fmt(optimum), "política_óptima": _policy(root),
         "unidad": "millones, según el ejemplo de la presentación"},
        root["id"], root.get("best_branch"),
    )
    total = len(steps)
    for index, step in enumerate(steps, 1):
        step["paso"] = index
        step["total_pasos"] = total
    return steps


def _policy(node: dict[str, Any]) -> dict[str, Any]:
    if node["type"] == "terminal":
        return {"resultado": node["label"], "pago": _fmt(node["value"])}
    if node["type"] == "decision":
        branch = next((edge for edge in node["branches"] if edge["selected"]), None)
        if branch is None:
            return {"decisión": node["label"], "pendiente": True}
        return {"decisión": node["label"], "elegir": branch["label"], "continuación": _policy(branch["child"])}
    return {"suceso": node["label"], "continuaciones": [_policy(edge["child"]) for edge in node["branches"]]}
