"""Asignación dinámica de recursos con recorrido didáctico por etapas y estados."""

from __future__ import annotations

import math
from typing import Any

from .step_schema import crear_paso


class AsignacionInputError(ValueError):
    """Error controlado para datos inválidos del sandbox."""


def default_payload() -> dict[str, Any]:
    """Ejemplo de 5 brigadas y 3 países del material proporcionado."""
    return {
        "brigadas": 5,
        "etapas": ["País 1", "País 2", "País 3"],
        "rendimientos": [
            [0, 45, 70, 90, 105, 120],
            [0, 20, 45, 75, 110, 150],
            [0, 50, 70, 80, 100, 130],
        ],
    }


def _numero(valor: Any, contexto: str) -> float:
    try:
        numero = float(valor)
    except (TypeError, ValueError) as exc:
        raise AsignacionInputError(f"El valor de {contexto} debe ser numérico.") from exc
    if not math.isfinite(numero):
        raise AsignacionInputError(f"El valor de {contexto} debe ser finito.")
    return numero


def validar_entrada(brigadas: Any, etapas: Any, rendimientos: Any) -> tuple[int, list[str], list[list[float]]]:
    brigadas_num = _numero(brigadas, "el número de brigadas")
    if brigadas_num < 0 or abs(brigadas_num - round(brigadas_num)) > 1e-9:
        raise AsignacionInputError("El número de brigadas debe ser un entero mayor o igual que 0.")
    brigadas_int = int(round(brigadas_num))
    if brigadas_int > 20:
        raise AsignacionInputError("Para mantener visible la matriz, usa como máximo 20 brigadas.")

    if not isinstance(etapas, list) or not etapas:
        raise AsignacionInputError("Agrega al menos una etapa.")
    if len(etapas) > 8:
        raise AsignacionInputError("Para mantener visible la matriz, usa como máximo 8 etapas.")
    etapas_norm = [str(e).strip() for e in etapas]
    if any(not e for e in etapas_norm):
        raise AsignacionInputError("Cada etapa necesita un nombre.")

    if not isinstance(rendimientos, list) or len(rendimientos) != len(etapas_norm):
        raise AsignacionInputError("Debe existir una fila de rendimiento por cada etapa.")

    matriz: list[list[float]] = []
    expected = brigadas_int + 1
    for i, fila in enumerate(rendimientos, start=1):
        if not isinstance(fila, list) or len(fila) != expected:
            raise AsignacionInputError(
                f"La fila de rendimiento de la etapa {i} debe contener exactamente {expected} valores (0..B)."
            )
        numeros = [_numero(v, f"el rendimiento de la etapa {i}") for v in fila]
        if abs(numeros[0]) > 1e-9:
            raise AsignacionInputError(f"El rendimiento con 0 brigadas de la etapa {i} debe ser 0.")
        matriz.append(numeros)

    return brigadas_int, etapas_norm, matriz


def _fmt(value: float) -> str:
    return str(int(round(value))) if abs(value - round(value)) < 1e-9 else f"{value:.2f}"


def _matriz_visual(
    dp: list[list[float | None]],
    arg: list[list[int | None]],
    etapas: list[str],
    brigadas: int,
    *,
    etapa_activa: int | None = None,
    estado_activo: int | None = None,
    decision_activa: int | None = None,
    seleccionados: dict[int, int] | None = None,
    estado_backtracking: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "tipo": "asignacion_dp",
        "brigadas": brigadas,
        "etapas": etapas,
        "dp": dp,
        "decisiones_optimas": arg,
        "etapa_activa": etapa_activa,
        "estado_activo": estado_activo,
        "decision_activa": decision_activa,
        "seleccionados": {str(k): v for k, v in (seleccionados or {}).items()},
        "backtracking": estado_backtracking or [],
    }


def build_steps(*, brigadas: Any, etapas: Any, rendimientos: Any) -> list[dict[str, Any]]:
    """Genera todos los pasos: optimización hacia atrás y reconstrucción de política."""
    brigadas, etapas, rendimientos = validar_entrada(brigadas, etapas, rendimientos)
    n = len(etapas)

    # f_i(s): mejor rendimiento desde la etapa i cuando quedan s brigadas.
    dp: list[list[float | None]] = [[None] * (brigadas + 1) for _ in range(n)]
    arg: list[list[int | None]] = [[None] * (brigadas + 1) for _ in range(n)]
    borradores: list[dict[str, Any]] = [
        {
            "fase": "Preparar etapas y estados",
            "titulo": "Representamos el problema como etapas y estados",
            "formula": "f_i(s) = mejor rendimiento desde la etapa i con s brigadas disponibles",
            "explicacion": (
                "Cada etapa corresponde a un país. El estado indica cuántas brigadas siguen disponibles "
                "para esa etapa y las siguientes. Así podemos resolver problemas pequeños y reutilizar sus resultados."
            ),
            "variables": {
                "etapas": etapas,
                "brigadas_totales": brigadas,
                "estado_inicial": brigadas,
                "principio": "resolver hacia atrás y reutilizar soluciones óptimas",
            },
            "estado": _matriz_visual(dp, arg, etapas, brigadas),
            "enfoque": {"tipo": "global", "etiqueta": "etapas / estados"},
        }
    ]

    # Programación hacia atrás: última etapa -> primera.
    for i in range(n - 1, -1, -1):
        for s in range(brigadas + 1):
            mejor = None
            mejor_x = None
            for x in range(s + 1):
                futuro = 0.0 if i == n - 1 else float(dp[i + 1][s - x])
                inmediato = rendimientos[i][x]
                candidato = inmediato + futuro
                if mejor is None or candidato > mejor:
                    mejor = candidato
                    mejor_x = x

                # Revelamos el cálculo candidato por candidato.
                candidatos_previos = []
                for x2 in range(x + 1):
                    futuro2 = 0.0 if i == n - 1 else float(dp[i + 1][s - x2])
                    candidatos_previos.append({
                        "brigadas_etapa": x2,
                        "restantes": s - x2,
                        "rendimiento_inmediato": rendimientos[i][x2],
                        "rendimiento_futuro": futuro2,
                        "total": rendimientos[i][x2] + futuro2,
                    })

                borradores.append({
                    "fase": "Optimizar etapa y estado",
                    "titulo": f"Evaluar {etapas[i]} con {s} brigadas disponibles: probar x={x}",
                    "formula": (
                        f"candidato = p_{i+1}({x}) + "
                        f"f_{i+2}({s - x}) = {_fmt(inmediato)} + {_fmt(futuro)} = {_fmt(candidato)}"
                        if i < n - 1
                        else f"candidato = p_{i+1}({x}) = {_fmt(inmediato)}"
                    ),
                    "explicacion": (
                        f"Probamos asignar {x} brigadas a {etapas[i]}. "
                        "El resto queda disponible para las etapas siguientes. "
                        "La mejor opción será el candidato con mayor rendimiento total."
                    ),
                    "variables": {
                        "etapa": i + 1,
                        "nombre_etapa": etapas[i],
                        "estado_s": s,
                        "decision_x": x,
                        "brigadas_restantes": s - x,
                        "rendimiento_inmediato": inmediato,
                        "rendimiento_futuro": futuro,
                        "candidato": candidato,
                        "mejor_hasta_ahora": mejor,
                        "candidatos_evaluados": candidatos_previos,
                    },
                    "estado": _matriz_visual(
                        dp, arg, etapas, brigadas,
                        etapa_activa=i, estado_activo=s, decision_activa=x,
                    ),
                    "enfoque": {"tipo": "celda", "fila": i, "columna": s, "etiqueta": f"f_{i+1}({s})"},
                })

            dp[i][s] = float(mejor)
            arg[i][s] = int(mejor_x)

            borradores.append({
                "fase": "Fijar óptimo del estado",
                "titulo": f"Óptimo de {etapas[i]} con estado {s}",
                "formula": (
                    f"f_{i+1}({s}) = max_x [p_{i+1}(x) + f_{i+2}({s}-x)] = {_fmt(mejor)}"
                    if i < n - 1
                    else f"f_{i+1}({s}) = max_x p_{i+1}(x) = {_fmt(mejor)}"
                ),
                "explicacion": (
                    f"Después de comparar todas las asignaciones posibles de 0 a {s} brigadas, "
                    f"la mejor decisión para este estado es asignar {mejor_x} brigadas a {etapas[i]}. "
                    "Guardamos el resultado porque será reutilizado por las etapas anteriores."
                ),
                "variables": {
                    "etapa": i + 1,
                    "nombre_etapa": etapas[i],
                    "estado_s": s,
                    "mejor_decision_x": mejor_x,
                    "valor_optimo": mejor,
                    "tabla_etapa": dp[i],
                },
                "estado": _matriz_visual(
                    dp, arg, etapas, brigadas,
                    etapa_activa=i, estado_activo=s, decision_activa=mejor_x,
                ),
                "enfoque": {"tipo": "celda", "fila": i, "columna": s, "etiqueta": f"f_{i+1}({s})"},
            })

    # Reconstrucción de la política óptima.
    seleccionados: dict[int, int] = {}
    trazado: list[dict[str, Any]] = []
    s = brigadas
    for i in range(n):
        x = int(arg[i][s])
        siguiente = s - x
        seleccionados[i + 1] = x
        trazado.append({
            "etapa": i + 1,
            "nombre_etapa": etapas[i],
            "brigadas_asignadas": x,
            "estado_antes": s,
            "estado_despues": siguiente,
        })
        borradores.append({
            "fase": "Reconstruir la política óptima",
            "titulo": f"Asignar {x} brigadas a {etapas[i]}",
            "formula": f"x_{i+1} = {x}; estado siguiente = {s} - {x} = {siguiente}",
            "explicacion": (
                f"Partimos del estado inicial con {s} brigadas. La tabla nos dice que la decisión óptima "
                f"en {etapas[i]} es {x}. Seguimos al estado restante para reconstruir la política completa."
            ),
            "variables": {
                "etapa": i + 1,
                "decision_x": x,
                "estado_antes": s,
                "estado_despues": siguiente,
                "politica_parcial": dict(seleccionados),
            },
            "estado": _matriz_visual(
                dp, arg, etapas, brigadas,
                etapa_activa=i, estado_activo=s, decision_activa=x,
                seleccionados=seleccionados, estado_backtracking=trazado,
            ),
            "enfoque": {"tipo": "backtracking", "fila": i, "columna": s, "etiqueta": f"x_{i+1}"},
        })
        s = siguiente

    total = sum(rendimientos[i - 1][x] for i, x in seleccionados.items())
    vector = [seleccionados[i + 1] for i in range(n)]
    borradores.append({
        "fase": "Resultado global",
        "titulo": "La política óptima queda reconstruida",
        "formula": "F* = f_1(B)",
        "explicacion": (
            f"La política asigna {', '.join(f'{etapas[i]}: {vector[i]}' for i in range(n))}. "
            f"El rendimiento global es {_fmt(total)}. La suma de brigadas utilizadas es {sum(vector)}."
        ),
        "variables": {
            "brigadas_totales": brigadas,
            "politica_optima": vector,
            "rendimiento_global": total,
            "brigadas_utilizadas": sum(vector),
            "brigadas_sobrantes": brigadas - sum(vector),
        },
        "estado": _matriz_visual(
            dp, arg, etapas, brigadas,
            etapa_activa=0, estado_activo=brigadas,
            seleccionados=seleccionados, estado_backtracking=trazado,
        ),
        "enfoque": {"tipo": "resultado", "etiqueta": "f_1(B)"},
    })

    total_pasos = len(borradores)
    return [
        crear_paso(
            algoritmo="asignacion_recursos",
            paso=i,
            total_pasos=total_pasos,
            fase=item["fase"],
            titulo=item["titulo"],
            formula=item["formula"],
            explicacion=item["explicacion"],
            variables=item["variables"],
            estado_visual=item["estado"],
            enfoque=item["enfoque"],
        )
        for i, item in enumerate(borradores, start=1)
    ]
