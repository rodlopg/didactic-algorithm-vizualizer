"""Mochila 0/1 con recorrido didáctico celda por celda y backtracking."""

from __future__ import annotations

import math
from typing import Any

from .step_schema import crear_paso


class MochilaInputError(ValueError):
    """Error controlado para datos inválidos del sandbox."""


def default_payload() -> dict[str, Any]:
    """Ejemplo numérico de las diapositivas proporcionadas."""
    return {
        "beneficios": [16, 19, 23, 28],
        "pesos": [2, 3, 4, 5],
        "capacidad": 7,
    }


def _numero(valor: Any, contexto: str) -> float:
    try:
        numero = float(valor)
    except (TypeError, ValueError) as exc:
        raise MochilaInputError(f"El valor de {contexto} debe ser numérico.") from exc
    if not math.isfinite(numero):
        raise MochilaInputError(f"El valor de {contexto} debe ser finito.")
    return numero


def validar_entrada(
    beneficios: Any,
    pesos: Any,
    capacidad: Any,
) -> tuple[list[float], list[int], int]:
    if not isinstance(beneficios, list) or not beneficios:
        raise MochilaInputError("Agrega al menos un objeto con su beneficio.")
    if not isinstance(pesos, list) or len(pesos) != len(beneficios):
        raise MochilaInputError("Debe existir un peso por cada objeto.")
    if len(beneficios) > 12:
        raise MochilaInputError("Para mantener visible la tabla, usa como máximo 12 objetos.")

    capacidad_num = _numero(capacidad, "la capacidad")
    if capacidad_num < 0 or abs(capacidad_num - round(capacidad_num)) > 1e-9:
        raise MochilaInputError("La capacidad debe ser un entero mayor o igual que 0.")
    capacidad_int = int(round(capacidad_num))
    if capacidad_int > 40:
        raise MochilaInputError("Para mantener visible la tabla, usa una capacidad máxima de 40.")

    beneficios_num = [_numero(v, f"el beneficio del objeto {i + 1}") for i, v in enumerate(beneficios)]
    pesos_num: list[int] = []
    for i, valor in enumerate(pesos):
        peso = _numero(valor, f"el peso del objeto {i + 1}")
        if peso <= 0 or abs(peso - round(peso)) > 1e-9:
            raise MochilaInputError("Los pesos deben ser enteros positivos.")
        pesos_num.append(int(round(peso)))

    return beneficios_num, pesos_num, capacidad_int


def _fmt(value: float) -> str:
    if abs(value - round(value)) < 1e-9:
        return f"{int(round(value))}"
    return f"{value:.2f}"


def _tabla_visual(
    dp: list[list[float]],
    beneficios: list[float],
    pesos: list[int],
    capacidad: int,
    *,
    fila_activa: int | None = None,
    columna_activa: int | None = None,
    celdas_calculadas: list[list[int]] | None = None,
    celda_exclusion: tuple[int, int] | None = None,
    celda_inclusion: tuple[int, int] | None = None,
    celda_elegida: tuple[int, int] | None = None,
    backtracking: list[dict[str, Any]] | None = None,
    seleccionados: list[int] | None = None,
    capacidad_actual: int | None = None,
) -> dict[str, Any]:
    return {
        "tipo": "mochila_dp",
        "capacidad": capacidad,
        "beneficios": beneficios,
        "pesos": pesos,
        "dp": dp,
        "fila_activa": fila_activa,
        "columna_activa": columna_activa,
        "celdas_calculadas": celdas_calculadas or [],
        "celda_exclusion": list(celda_exclusion) if celda_exclusion else None,
        "celda_inclusion": list(celda_inclusion) if celda_inclusion else None,
        "celda_elegida": list(celda_elegida) if celda_elegida else None,
        "backtracking": backtracking or [],
        "seleccionados": seleccionados or [],
        "capacidad_actual": capacidad_actual,
    }


def _copiar_matriz(dp: list[list[float]]) -> list[list[float | None]]:
    """Mantiene ocultas las celdas todavía no calculadas."""
    return [row[:] for row in dp]


def build_steps(
    *,
    beneficios: Any,
    pesos: Any,
    capacidad: Any,
) -> list[dict[str, Any]]:
    """Genera una ejecución completa: tabla DP y backtracking."""
    beneficios, pesos, capacidad = validar_entrada(beneficios, pesos, capacidad)
    n = len(beneficios)

    # La fuente define z_k(d) como la mejor solución con capacidad d
    # considerando los objetos 1..k.
    dp: list[list[float]] = [[0.0 for _ in range(capacidad + 1)] for _ in range(n + 1)]
    calculadas: list[list[int]] = []
    pasos_borrador: list[dict[str, Any]] = []

    pasos_borrador.append({
        "fase": "Preparar la tabla de programación dinámica",
        "titulo": "Construimos la tabla z_k(d) desde la capacidad 0",
        "formula": "z_k(d) = mejor beneficio con capacidad d usando objetos 1..k",
        "explicacion": "Cada columna fija una capacidad d y recorre los objetos uno por uno. Así el foco visual avanza de capacidad en capacidad, manteniendo disponibles las celdas que necesita la recurrencia.",
        "variables": {
            "objetos": n,
            "capacidad": capacidad,
            "fila_inicial": 0,
            "orden_recorrido": "por_columnas",
            "z_0_d": [0 for _ in range(capacidad + 1)],
        },
        "estado": _tabla_visual(dp, beneficios, pesos, capacidad),
        "enfoque": {"tipo": "global", "etiqueta": "z_k(d)"},
    })

    # Recorrido didáctico por columnas: fijamos una capacidad d y evaluamos
    # todos los objetos k antes de avanzar a la siguiente capacidad.
    for d in range(capacidad + 1):
        for k in range(1, n + 1):
            peso = pesos[k - 1]
            beneficio = beneficios[k - 1]
            celda = (k, d)
            if peso > d:
                dp[k][d] = dp[k - 1][d]
                calculadas.append([k, d])
                formula = f"z_{k}({d}) = z_{k - 1}({d}) = {_fmt(dp[k][d])}"
                explicacion = (
                    f"El objeto {k} pesa {peso}, pero la capacidad actual es {d}. "
                    "No cabe, así que conservamos la mejor solución de la fila anterior."
                )
                variables = {
                    "k": k,
                    "d": d,
                    "beneficio_objeto": beneficio,
                    "peso_objeto": peso,
                    "valor_sin_objeto": dp[k - 1][d],
                    "resultado": dp[k][d],
                    "cabe": False,
                }
                enfoque = {"tipo": "celda", "fila": k, "columna": d, "etiqueta": f"z_{k}({d})"}
                estado = _tabla_visual(
                    _copiar_matriz(dp), beneficios, pesos, capacidad,
                    fila_activa=k, columna_activa=d, celdas_calculadas=calculadas,
                    celda_elegida=celda,
                )
            else:
                capacidad_restante = d - peso
                valor_sin = dp[k - 1][d]
                valor_con = beneficio + dp[k - 1][capacidad_restante]
                dp[k][d] = max(valor_sin, valor_con)
                calculadas.append([k, d])
                ganador = "incluir" if valor_con > valor_sin else "excluir"
                if abs(valor_con - valor_sin) < 1e-9:
                    ganador = "empate"
                formula = (
                    f"z_{k}({d}) = max(z_{k - 1}({d}), "
                    f"{_fmt(beneficio)} + z_{k - 1}({capacidad_restante})) = {_fmt(dp[k][d])}"
                )
                explicacion = (
                    f"El objeto {k} sí cabe. Comparamos conservar la solución anterior ({_fmt(valor_sin)}) "
                    f"con incluir el objeto y completar la capacidad restante ({_fmt(valor_con)}). "
                    f"Aquí gana {ganador}."
                )
                variables = {
                    "k": k,
                    "d": d,
                    "beneficio_objeto": beneficio,
                    "peso_objeto": peso,
                    "capacidad_restante": capacidad_restante,
                    "valor_sin_objeto": valor_sin,
                    "valor_con_objeto": valor_con,
                    "resultado": dp[k][d],
                    "decision": ganador,
                    "cabe": True,
                }
                enfoque = {"tipo": "celda", "fila": k, "columna": d, "etiqueta": f"z_{k}({d})"}
                estado = _tabla_visual(
                    _copiar_matriz(dp), beneficios, pesos, capacidad,
                    fila_activa=k, columna_activa=d, celdas_calculadas=calculadas,
                    celda_exclusion=(k - 1, d),
                    celda_inclusion=(k - 1, capacidad_restante),
                    celda_elegida=celda,
                )

            pasos_borrador.append({
                "fase": "Llenar la tabla de programación dinámica",
                "titulo": f"Evaluar el objeto {k} con capacidad {d}",
                "formula": formula,
                "explicacion": explicacion,
                "variables": variables,
                "estado": estado,
                "enfoque": enfoque,
            })

    # Backtracking: empezamos en z_n(B) y regresamos a z_0(·).
    seleccionados: list[int] = []
    trazado: list[dict[str, Any]] = []
    k = n
    d = capacidad

    while k > 0:
        peso = pesos[k - 1]
        beneficio = beneficios[k - 1]
        actual = dp[k][d]
        sin_objeto = dp[k - 1][d]
        fue_incluido = d >= peso and abs(actual - (beneficio + dp[k - 1][d - peso])) < 1e-9 and actual > sin_objeto
        if fue_incluido:
            seleccionados.append(k)
            siguiente_d = d - peso
            trazado.append({"objeto": k, "accion": "incluido", "capacidad_antes": d, "capacidad_despues": siguiente_d})
            pasos_borrador.append({
                "fase": "Reconstruir la solución óptima (backtracking)",
                "titulo": f"El objeto {k} forma parte de la solución",
                "formula": f"z_{k}({d}) = {_fmt(beneficio)} + z_{k - 1}({siguiente_d})",
                "explicacion": (
                    f"Seguimos la celda que explica el valor óptimo. Incluir el objeto {k} produce {_fmt(actual)} "
                    f"y coincide con la solución óptima de la celda actual. Restamos su peso y continuamos."
                ),
                "variables": {
                    "k": k,
                    "capacidad_actual": d,
                    "objeto": k,
                    "peso_objeto": peso,
                    "beneficio_objeto": beneficio,
                    "seleccionados": sorted(seleccionados),
                    "capacidad_siguiente": siguiente_d,
                },
                "estado": _tabla_visual(
                    dp, beneficios, pesos, capacidad,
                    fila_activa=k, columna_activa=d, celdas_calculadas=calculadas,
                    celda_elegida=(k, d), backtracking=trazado,
                    seleccionados=sorted(seleccionados), capacidad_actual=d,
                ),
                "enfoque": {"tipo": "backtracking", "fila": k, "columna": d, "etiqueta": f"z_{k}({d})"},
            })
            d = siguiente_d
        else:
            trazado.append({"objeto": k, "accion": "excluido", "capacidad_antes": d, "capacidad_despues": d})
            pasos_borrador.append({
                "fase": "Reconstruir la solución óptima (backtracking)",
                "titulo": f"El objeto {k} no se selecciona",
                "formula": f"z_{k}({d}) = z_{k - 1}({d}) = {_fmt(actual)}",
                "explicacion": (
                    f"La mejor solución de la celda {k},{d} puede mantenerse sin el objeto {k}. "
                    "Por eso seguimos hacia la fila anterior con la misma capacidad."
                ),
                "variables": {
                    "k": k,
                    "capacidad_actual": d,
                    "objeto": k,
                    "peso_objeto": peso,
                    "beneficio_objeto": beneficio,
                    "seleccionados": sorted(seleccionados),
                    "capacidad_siguiente": d,
                },
                "estado": _tabla_visual(
                    dp, beneficios, pesos, capacidad,
                    fila_activa=k, columna_activa=d, celdas_calculadas=calculadas,
                    celda_elegida=(k, d), backtracking=trazado,
                    seleccionados=sorted(seleccionados), capacidad_actual=d,
                ),
                "enfoque": {"tipo": "backtracking", "fila": k, "columna": d, "etiqueta": f"z_{k}({d})"},
            })
        k -= 1

    seleccionados = sorted(seleccionados)
    vector = [1 if i in seleccionados else 0 for i in range(1, n + 1)]
    peso_total = sum(pesos[i - 1] for i in seleccionados)
    beneficio_total = sum(beneficios[i - 1] for i in seleccionados)

    pasos_borrador.append({
        "fase": "Resultado óptimo",
        "titulo": "Terminamos el backtracking y reconstruimos la solución",
        "formula": "Z* = z_n(B)",
        "explicacion": (
            f"La mejor combinación alcanza {_fmt(beneficio_total)} de beneficio con {_fmt(peso_total)} de peso. "
            f"El vector binario resultante es {{{', '.join(map(str, vector))}}}."
        ),
        "variables": {
            "beneficio_optimo": beneficio_total,
            "peso_total": peso_total,
            "capacidad": capacidad,
            "objetos_seleccionados": seleccionados,
            "vector_binario": vector,
        },
        "estado": _tabla_visual(
            dp, beneficios, pesos, capacidad,
            celdas_calculadas=calculadas, backtracking=trazado,
            seleccionados=seleccionados, capacidad_actual=peso_total,
        ),
        "enfoque": {"tipo": "resultado", "etiqueta": "Z*"},
    })

    total = len(pasos_borrador)
    return [
        crear_paso(
            algoritmo="mochila_01",
            paso=i,
            total_pasos=total,
            fase=item["fase"],
            titulo=item["titulo"],
            formula=item["formula"],
            explicacion=item["explicacion"],
            variables=item["variables"],
            estado_visual=item["estado"],
            enfoque=item["enfoque"],
        )
        for i, item in enumerate(pasos_borrador, start=1)
    ]
