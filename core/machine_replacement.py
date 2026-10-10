"""Reemplazo de máquinas mediante programación dinámica.

Modelo tomado del ejemplo de reemplazo de máquinas de la presentación de
Programación Dinámica III:
- etapa i = año i;
- estado t = edad de la máquina al inicio del año i;
- acciones K = conservar y R = reemplazar;
- al final del horizonte se desecha la máquina (S).

La función f_i(t) representa el ingreso neto máximo desde el año i hasta el
final del horizonte, comenzando con una máquina de edad t.
"""

from __future__ import annotations

import math
from typing import Any

from .step_schema import crear_paso


class ReemplazoInputError(ValueError):
    """Error controlado del sandbox."""


def default_payload() -> dict[str, Any]:
    # Datos del ejemplo docente: I = $100,000; máquina inicial de 3 años;
    # horizonte n = 4; edad 6 obliga a reemplazar.
    return {
        "horizonte": 4,
        "edad_inicial": 3,
        "edad_maxima": 6,
        "costo_adquisicion": 100000,
        "ingresos": [20000, 19000, 18500, 17200, 15500, 14000, 12200],
        "costos_operacion": [200, 600, 1200, 1500, 1700, 1800, 2200],
        "valores_desecho": [None, 80000, 60000, 50000, 30000, 10000, 5000],
    }


def _numero(valor: Any, contexto: str) -> float:
    try:
        numero = float(valor)
    except (TypeError, ValueError) as exc:
        raise ReemplazoInputError(f"El valor de {contexto} debe ser numérico.") from exc
    if not math.isfinite(numero):
        raise ReemplazoInputError(f"El valor de {contexto} debe ser finito.")
    return numero


def validar_entrada(
    horizonte: Any,
    edad_inicial: Any,
    edad_maxima: Any,
    costo_adquisicion: Any,
    ingresos: Any,
    costos_operacion: Any,
    valores_desecho: Any,
) -> tuple[int, int, int, float, list[float], list[float], list[float | None]]:
    h_float = _numero(horizonte, "el horizonte")
    if h_float < 1 or abs(h_float - round(h_float)) > 1e-9:
        raise ReemplazoInputError("El horizonte debe ser un entero positivo.")
    h = int(round(h_float))
    if h > 12:
        raise ReemplazoInputError("Usa un horizonte máximo de 12 años para conservar la legibilidad del diagrama.")

    inicial_float = _numero(edad_inicial, "la edad inicial")
    max_float = _numero(edad_maxima, "la edad máxima")
    if inicial_float < 1 or abs(inicial_float - round(inicial_float)) > 1e-9:
        raise ReemplazoInputError("La edad inicial debe ser un entero positivo.")
    if max_float < 2 or abs(max_float - round(max_float)) > 1e-9:
        raise ReemplazoInputError("La edad máxima debe ser un entero de al menos 2 años.")
    inicial = int(round(inicial_float))
    max_age = int(round(max_float))
    if inicial > max_age:
        raise ReemplazoInputError("La edad inicial no puede superar la edad máxima.")

    compra = _numero(costo_adquisicion, "el costo de adquisición")
    if compra < 0:
        raise ReemplazoInputError("El costo de adquisición no puede ser negativo.")

    expected = max_age + 1
    if not isinstance(ingresos, list) or len(ingresos) != expected:
        raise ReemplazoInputError(f"Debes indicar {expected} ingresos: uno para cada edad t = 0..{max_age}.")
    if not isinstance(costos_operacion, list) or len(costos_operacion) != expected:
        raise ReemplazoInputError(f"Debes indicar {expected} costos de operación: uno para cada edad t = 0..{max_age}.")
    if not isinstance(valores_desecho, list) or len(valores_desecho) != expected:
        raise ReemplazoInputError(f"Debes indicar {expected} valores de desecho: uno para cada edad t = 0..{max_age}.")

    r = [_numero(v, f"el ingreso de la edad {i}") for i, v in enumerate(ingresos)]
    c = [_numero(v, f"el costo de operación de la edad {i}") for i, v in enumerate(costos_operacion)]
    s: list[float | None] = []
    for i, value in enumerate(valores_desecho):
        if value is None or value == "":
            s.append(None)
        else:
            n = _numero(value, f"el valor de desecho de la edad {i}")
            if n < 0:
                raise ReemplazoInputError("Los valores de desecho no pueden ser negativos.")
            s.append(n)
    if any(v < 0 for v in r):
        raise ReemplazoInputError("Los ingresos no pueden ser negativos.")
    if any(v < 0 for v in c):
        raise ReemplazoInputError("Los costos de operación no pueden ser negativos.")
    if s[1] is None:
        raise ReemplazoInputError("La máquina debe tener un valor de desecho para toda edad alcanzable, comenzando por t = 1.")
    return h, inicial, max_age, compra, r, c, s


def _fmt(value: float | None) -> str:
    if value is None:
        return "—"
    return str(int(round(value))) if abs(value - round(value)) < 1e-9 else f"{value:.2f}"


def _edge_key(anio: int, edad: int, accion: str, destino: int | None = None) -> str:
    return f"{anio}:{edad}:{accion}:{'' if destino is None else destino}"


def _estado_visual(
    *,
    h: int,
    inicial: int,
    max_age: int,
    compra: float,
    ingresos: list[float],
    costos: list[float],
    desechos: list[float | None],
    estados: dict[int, list[int]],
    nodos: list[dict[str, Any]],
    aristas: list[dict[str, Any]],
    dp: dict[int, dict[int, float]],
    decisiones: dict[int, dict[int, list[str]]],
    anio_activo: int | None = None,
    edad_activa: int | None = None,
    decision_activa: str | None = None,
    rutas_optimas: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "tipo": "reemplazo_maquinas",
        "horizonte": h,
        "edad_inicial": inicial,
        "edad_maxima": max_age,
        "costo_adquisicion": compra,
        "ingresos": ingresos,
        "costos_operacion": costos,
        "valores_desecho": desechos,
        "estados_por_anio": {str(k): v for k, v in estados.items()},
        "nodos": nodos,
        "aristas": aristas,
        "dp": {str(i): {str(t): value for t, value in row.items()} for i, row in dp.items()},
        "decisiones_optimas": {str(i): {str(t): actions for t, actions in row.items()} for i, row in decisiones.items()},
        "anio_activo": anio_activo,
        "edad_activa": edad_activa,
        "decision_activa": decision_activa,
        "rutas_optimas": rutas_optimas or [],
    }


def _build_reachable_graph(h: int, inicial: int, max_age: int) -> tuple[dict[int, list[int]], list[dict[str, Any]], list[dict[str, Any]]]:
    estados: dict[int, set[int]] = {1: {inicial}}
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []

    for anio in range(1, h + 2):
        estados.setdefault(anio, set())
        for edad in sorted(estados[anio]):
            nodes.append({"id": f"e{anio}-t{edad}", "anio": anio, "edad": edad})
        if anio == h + 1:
            continue
        next_states = estados.setdefault(anio + 1, set())
        for edad in sorted(estados[anio]):
            # Conservar: solo si la máquina no alcanza la edad límite al inicio.
            # Una máquina de edad max_age debe reemplazarse.
            if edad < max_age:
                next_age = edad + 1
                next_states.add(next_age)
                edges.append({
                    "id": _edge_key(anio, edad, "K", next_age),
                    "anio": anio,
                    "origen": f"e{anio}-t{edad}",
                    "destino": f"e{anio+1}-t{next_age}",
                    "edad_origen": edad,
                    "edad_destino": next_age,
                    "accion": "K",
                    "etiqueta": "K",
                    "tipo": "decision",
                })
            # Reemplazar: la nueva máquina tiene edad 1 al inicio del siguiente año.
            next_states.add(1)
            edges.append({
                "id": _edge_key(anio, edad, "R", 1),
                "anio": anio,
                "origen": f"e{anio}-t{edad}",
                "destino": f"e{anio+1}-t1",
                "edad_origen": edad,
                "edad_destino": 1,
                "accion": "R",
                "etiqueta": "R",
                "tipo": "decision",
            })

    final_id = "final"
    for edad in sorted(estados[h + 1]):
        edges.append({
            "id": _edge_key(h + 1, edad, "S", None),
            "anio": h + 1,
            "origen": f"e{h+1}-t{edad}",
            "destino": final_id,
            "edad_origen": edad,
            "edad_destino": None,
            "accion": "S",
            "etiqueta": "S",
            "tipo": "final",
        })
    return {i: sorted(values) for i, values in estados.items()}, nodes, edges


def build_steps(
    *,
    horizonte: Any,
    edad_inicial: Any,
    edad_maxima: Any,
    costo_adquisicion: Any,
    ingresos: Any,
    costos_operacion: Any,
    valores_desecho: Any,
) -> list[dict[str, Any]]:
    h, inicial, max_age, compra, r, c, s = validar_entrada(
        horizonte, edad_inicial, edad_maxima, costo_adquisicion, ingresos, costos_operacion, valores_desecho
    )

    estados, nodos, aristas = _build_reachable_graph(h, inicial, max_age)
    dp: dict[int, dict[int, float]] = {h + 1: {age: float(s[age] or 0.0) for age in estados[h + 1]}}
    decisiones: dict[int, dict[int, list[str]]] = {h + 1: {age: ["S"] for age in estados[h + 1]}}
    candidatos: dict[int, dict[int, dict[str, float]]] = {}
    borradores: list[dict[str, Any]] = []

    common_kwargs = dict(
        h=h, inicial=inicial, max_age=max_age, compra=compra, ingresos=r, costos=c,
        desechos=s, estados=estados, nodos=nodos, aristas=aristas, dp=dp, decisiones=decisiones,
    )

    borradores.append({
        "fase": "Datos del problema",
        "titulo": "Identificamos etapas, estados y acciones",
        "formula": "Etapa = año i · Estado = edad t · Acciones = K (conservar) o R (reemplazar)",
        "explicacion": (
            f"Comenzamos en el año 1 con una máquina de {inicial} años. "
            f"El horizonte tiene {h} años y una máquina de {max_age} años debe reemplazarse al inicio del año correspondiente."
        ),
        "variables": {
            "horizonte": h,
            "edad_inicial": inicial,
            "edad_maxima": max_age,
            "costo_adquisicion": compra,
            "ingreso_edad_0": r[0],
            "costo_operacion_edad_0": c[0],
        },
        "estado": _estado_visual(**common_kwargs),
        "enfoque": {"tipo": "modelo", "etiqueta": "etapas + estados"},
    })

    # Base del último estado: al terminar el horizonte se desecha la máquina.
    for age in estados[h + 1]:
        value = dp[h + 1][age]
        borradores.append({
            "fase": "Condición terminal",
            "titulo": f"F_{h+1}({age}) = valor de desecho",
            "formula": f"F_{h+1}({age}) = s({age}) = {_fmt(s[age])}",
            "explicacion": f"Ya no quedan años de operación. La máquina de {age} años se desecha y recuperamos su valor de desecho.",
            "variables": {"anio": h + 1, "edad": age, "valor_desecho": s[age], "F": value},
            "estado": _estado_visual(**common_kwargs, anio_activo=h + 1, edad_activa=age, decision_activa="S"),
            "enfoque": {"tipo": "terminal", "anio": h + 1, "edad": age},
        })

    # Programación hacia atrás.
    for anio in range(h, 0, -1):
        dp[anio] = {}
        decisiones[anio] = {}
        candidatos[anio] = {}
        for age in estados[anio]:
            values: dict[str, float] = {}
            if age < max_age:
                keep = r[age] - c[age] + dp[anio + 1][age + 1]
                values["K"] = keep
            replace = r[0] + (s[age] or 0.0) - c[0] - compra + dp[anio + 1][1]
            values["R"] = replace
            candidatos[anio][age] = values
            best = max(values.values())
            best_actions = [action for action, value in values.items() if abs(value - best) < 1e-9]
            dp[anio][age] = best
            decisiones[anio][age] = best_actions

            # Enriquecemos las aristas con los valores calculados para el estado.
            for edge in aristas:
                if edge["anio"] != anio or edge["edad_origen"] != age or edge["tipo"] != "decision":
                    continue
                edge["valor"] = values.get(edge["accion"])
                edge["es_optima"] = edge["accion"] in best_actions

            formula_parts: list[str] = []
            if "K" in values:
                formula_parts.append(
                    f"K: r({age})−c({age})+F_{anio+1}({age+1}) = {_fmt(values['K'])}"
                )
            else:
                formula_parts.append(f"K: no permitido; al inicio del año {anio} la edad ya es {max_age}")
            formula_parts.append(
                f"R: r(0)+s({age})−c(0)−I+F_{anio+1}(1) = {_fmt(values['R'])}"
            )
            borradores.append({
                "fase": f"Etapa {anio} · Evaluación",
                "titulo": f"Evaluamos conservar o reemplazar una máquina de {age} años",
                "formula": "\n".join(formula_parts),
                "explicacion": (
                    "Conservar suma el ingreso del año, resta su operación y continúa con una máquina un año más vieja. "
                    "Reemplazar vende la máquina actual, compra una nueva y continúa con una máquina de 1 año."
                ),
                "variables": {
                    "anio": anio,
                    "edad": age,
                    "ingreso_actual": r[age],
                    "costo_operacion_actual": c[age],
                    "valor_desecho_actual": s[age],
                    "candidato_K": values.get("K"),
                    "candidato_R": values.get("R"),
                    "mejor_ingreso": best,
                    "decisiones_optimas": best_actions,
                },
                "estado": _estado_visual(**common_kwargs, anio_activo=anio, edad_activa=age),
                "enfoque": {"tipo": "comparacion", "anio": anio, "edad": age},
            })
            borradores.append({
                "fase": f"Etapa {anio} · Selección",
                "titulo": f"F_{anio}({age}) toma la mejor acción: {' o '.join(best_actions)}",
                "formula": f"F_{anio}({age}) = max({', '.join(_fmt(v) for v in values.values())}) = {_fmt(best)}",
                "explicacion": (
                    f"Guardamos la(s) acción(es) con mayor ingreso neto. "
                    f"Este resultado queda disponible para las etapas anteriores."
                ),
                "variables": {"anio": anio, "edad": age, "F": best, "acciones_optimas": best_actions},
                "estado": _estado_visual(**common_kwargs, anio_activo=anio, edad_activa=age, decision_activa=best_actions[0]),
                "enfoque": {"tipo": "seleccion", "anio": anio, "edad": age},
            })

    # Enumeramos todas las políticas óptimas desde el estado inicial.
    def enumerate_policies(anio: int, age: int, actions: list[str], nodes_path: list[str]) -> list[dict[str, Any]]:
        if anio == h + 1:
            return [{"acciones": actions[:], "nodos": nodes_path[:]}]
        result: list[dict[str, Any]] = []
        for action in decisiones[anio][age]:
            next_age = age + 1 if action == "K" else 1
            result.extend(enumerate_policies(anio + 1, next_age, actions + [action], nodes_path + [f"e{anio+1}-t{next_age}"]))
        return result

    policies = enumerate_policies(1, inicial, [], [f"e1-t{inicial}"])
    # Deduplicar por secuencia de acciones, por si un caso límite genera el mismo recorrido.
    unique: dict[str, dict[str, Any]] = {"".join(item["acciones"]): item for item in policies}
    policies = [unique[key] for key in sorted(unique)]

    for index, policy in enumerate(policies, start=1):
        borradores.append({
            "fase": "Reconstrucción de la política óptima",
            "titulo": f"Política óptima {index}: {''.join(policy['acciones'])}",
            "formula": " → ".join(policy["acciones"]) + " → S",
            "explicacion": (
                "Seguimos las decisiones óptimas guardadas en sentido directo. "
                "Al terminar el horizonte, la máquina se desecha."
            ),
            "variables": {
                "politica": "".join(policy["acciones"]),
                "nodos": policy["nodos"],
                "ingreso_optimo": dp[1][inicial],
            },
            "estado": _estado_visual(**common_kwargs, rutas_optimas=policies),
            "enfoque": {"tipo": "backtracking", "politica": "".join(policy["acciones"])},
        })

    optimal_paths = []
    for policy in policies:
        edge_keys = []
        for i, action in enumerate(policy["acciones"], start=1):
            age = int(policy["nodos"][i - 1].split("-t")[1])
            next_age = age + 1 if action == "K" else 1
            edge_keys.append(_edge_key(i, age, action, next_age))
        last_age = int(policy["nodos"][-1].split("-t")[1])
        edge_keys.append(_edge_key(h + 1, last_age, "S", None))
        optimal_paths.append({**policy, "aristas": edge_keys})

    final_state = _estado_visual(**common_kwargs, rutas_optimas=optimal_paths)
    borradores.append({
        "fase": "Resultado óptimo",
        "titulo": "Ingresos máximos y políticas óptimas",
        "formula": f"F_1({inicial}) = {_fmt(dp[1][inicial])}",
        "explicacion": (
            f"Con una máquina de {inicial} años al inicio del año 1, el ingreso neto máximo es {_fmt(dp[1][inicial])}. "
            f"En este ejemplo existen {len(optimal_paths)} políticas óptimas."
        ),
        "variables": {
            "ingreso_optimo": dp[1][inicial],
            "politicas_optimas": ["".join(item["acciones"]) for item in optimal_paths],
            "horizonte": h,
            "edad_inicial": inicial,
        },
        "estado": final_state,
        "enfoque": {"tipo": "resultado", "etiqueta": "F_1(t_0)"},
    })

    total = len(borradores)
    return [
        crear_paso(
            algoritmo="reemplazo_maquinas",
            paso=index + 1,
            total_pasos=total,
            fase=item["fase"],
            titulo=item["titulo"],
            formula=item["formula"],
            explicacion=item["explicacion"],
            variables=item["variables"],
            estado_visual=item["estado"],
            enfoque=item["enfoque"],
        )
        for index, item in enumerate(borradores)
    ]
