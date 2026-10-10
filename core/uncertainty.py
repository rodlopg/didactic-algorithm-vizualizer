"""Criterios de decisión bajo incertidumbre con recorrido didáctico."""

from __future__ import annotations

import math
from typing import Any

from .step_schema import crear_paso


class IncertidumbreInputError(ValueError):
    """Error controlado para datos inválidos del sandbox."""


def default_payload() -> dict[str, Any]:
    """Ejemplo numérico tomado del material docente proporcionado."""
    return {
        "alternativas": ["a1", "a2", "a3"],
        "estados": ["s1", "s2"],
        "pagos": [
            [15000, 8000],
            [14000, 17910],
            [4000, 7910],
        ],
        "alpha": 0.6,
        "criterio": "todos",
    }


def _numero(valor: Any, contexto: str) -> float:
    try:
        numero = float(valor)
    except (TypeError, ValueError) as exc:
        raise IncertidumbreInputError(f"El valor de {contexto} debe ser numérico.") from exc
    if not math.isfinite(numero):
        raise IncertidumbreInputError(f"El valor de {contexto} debe ser finito.")
    return numero


def validar_entrada(
    alternativas: list[Any],
    estados: list[Any],
    pagos: list[list[Any]],
    alpha: Any = 0.6,
) -> tuple[list[str], list[str], list[list[float]], float]:
    if not isinstance(alternativas, list) or not alternativas:
        raise IncertidumbreInputError("Agrega al menos una alternativa.")
    if not isinstance(estados, list) or not estados:
        raise IncertidumbreInputError("Agrega al menos un estado de la naturaleza.")
    if not isinstance(pagos, list) or len(pagos) != len(alternativas):
        raise IncertidumbreInputError("La matriz de pagos debe tener una fila por alternativa.")

    alternativas_texto = [str(x).strip() for x in alternativas]
    estados_texto = [str(x).strip() for x in estados]
    if any(not x for x in alternativas_texto) or any(not x for x in estados_texto):
        raise IncertidumbreInputError("Las alternativas y los estados no pueden estar vacíos.")
    if len(set(alternativas_texto)) != len(alternativas_texto):
        raise IncertidumbreInputError("Las alternativas deben tener nombres distintos.")
    if len(set(estados_texto)) != len(estados_texto):
        raise IncertidumbreInputError("Los estados deben tener nombres distintos.")

    pagos_num: list[list[float]] = []
    for i, fila in enumerate(pagos):
        if not isinstance(fila, list) or len(fila) != len(estados_texto):
            raise IncertidumbreInputError(
                f"La fila de {alternativas_texto[i]} debe contener exactamente {len(estados_texto)} pagos."
            )
        pagos_num.append([_numero(v, f"{alternativas_texto[i]} / {estados_texto[j]}") for j, v in enumerate(fila)])

    alpha_num = _numero(alpha, "α")
    if not 0 <= alpha_num <= 1:
        raise IncertidumbreInputError("El parámetro α debe estar entre 0 y 1.")
    return alternativas_texto, estados_texto, pagos_num, alpha_num


def _fmt(value: float) -> str:
    if abs(value - round(value)) < 1e-9:
        return f"{int(round(value)):,}".replace(",", " ")
    return f"{value:,.2f}".replace(",", " ")


def _matriz_visual(
    alternativas: list[str],
    estados: list[str],
    pagos: list[list[float]],
    *,
    criterio: str | None = None,
    fila_activa: int | None = None,
    columna_activa: int | None = None,
    resultados: list[float] | None = None,
    etiquetas_resultado: list[str] | None = None,
    filas_seleccionadas: list[int] | None = None,
    regret: list[list[float]] | None = None,
    maxima_columnas: list[float] | None = None,
) -> dict[str, Any]:
    return {
        "tipo": "matriz_decision",
        "criterio": criterio or "",
        "alternativas": alternativas,
        "estados": estados,
        "pagos": pagos,
        "fila_activa": fila_activa,
        "columna_activa": columna_activa,
        "resultados": resultados or [],
        "etiquetas_resultado": etiquetas_resultado or [],
        "filas_seleccionadas": filas_seleccionadas or [],
        "regret": regret or [],
        "maxima_columnas": maxima_columnas or [],
    }


def _paso(
    *,
    criterio: str,
    fase: str,
    titulo: str,
    formula: str,
    explicacion: str,
    variables: dict[str, Any],
    estado_visual: dict[str, Any],
    enfoque: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "criterio": criterio,
        "fase_local": fase,
        "titulo_local": titulo,
        "formula_local": formula,
        "explicacion_local": explicacion,
        "variables_local": variables,
        "estado_visual_local": estado_visual,
        "enfoque_local": enfoque,
    }


def _crear_pasos_criterio(
    criterio: str,
    alternativas: list[str],
    estados: list[str],
    pagos: list[list[float]],
    alpha: float,
) -> list[dict[str, Any]]:
    borrador: list[dict[str, Any]] = []
    n, m = len(alternativas), len(estados)

    if criterio == "laplace":
        borrador.append(_paso(
            criterio=criterio,
            fase="Preparar criterio de Laplace",
            titulo="Suponemos que todos los estados son igualmente probables",
            formula="P(s_j) = 1 / m",
            explicacion="Como no conocemos probabilidades de los estados, el criterio de Laplace los trata por igual. Después calcularemos el promedio de cada alternativa.",
            variables={"numero_de_estados": m, "probabilidad_asumida": 1 / m},
            estado_visual=_matriz_visual(alternativas, estados, pagos, criterio=criterio),
        ))
        promedios = []
        for i, alternativa in enumerate(alternativas):
            suma = sum(pagos[i])
            media = suma / m
            promedios.append(media)
            borrador.append(_paso(
                criterio=criterio,
                fase="Calcular promedio de cada alternativa",
                titulo=f"Promedio de {alternativa}",
                formula=f"L({alternativa}) = ({' + '.join(_fmt(v) for v in pagos[i])}) / {m} = {_fmt(media)}",
                explicacion="El promedio resume cuánto obtendríamos en esta alternativa al dar el mismo peso a todos los estados.",
                variables={"alternativa": alternativa, "suma_pagos": suma, "numero_estados": m, "promedio": media},
                estado_visual=_matriz_visual(alternativas, estados, pagos, criterio=criterio, fila_activa=i, resultados=promedios, etiquetas_resultado=["promedio"]),
                enfoque={"tipo": "fila", "fila": i, "etiqueta": alternativa},
            ))
        elegido = max(range(n), key=lambda i: promedios[i])
        borrador.append(_paso(
            criterio=criterio,
            fase="Seleccionar alternativa",
            titulo=f"Laplace selecciona {alternativas[elegido]}",
            formula=f"max({', '.join(_fmt(v) for v in promedios)}) = {_fmt(promedios[elegido])}",
            explicacion="Elegimos la alternativa con mayor promedio porque, bajo Laplace, todas las situaciones cuentan por igual.",
            variables={"promedios": promedios, "alternativa_elegida": alternativas[elegido], "valor_elegido": promedios[elegido]},
            estado_visual=_matriz_visual(alternativas, estados, pagos, criterio=criterio, resultados=promedios, etiquetas_resultado=["promedio"], filas_seleccionadas=[elegido]),
            enfoque={"tipo": "fila", "fila": elegido, "etiqueta": alternativas[elegido]},
        ))

    elif criterio == "wald":
        borrador.append(_paso(
            criterio=criterio,
            fase="Preparar criterio de Wald",
            titulo="Buscamos el peor pago de cada alternativa",
            formula="W(a_i) = min_j v(a_i, s_j)",
            explicacion="Wald es pesimista: antes de comparar alternativas, mira cuál sería el resultado menos favorable de cada una.",
            variables={"interpretacion": "máximo de los mínimos de fila"},
            estado_visual=_matriz_visual(alternativas, estados, pagos, criterio=criterio),
        ))
        minimos = []
        for i, alternativa in enumerate(alternativas):
            minimo = min(pagos[i])
            minimos.append(minimo)
            col = pagos[i].index(minimo)
            borrador.append(_paso(
                criterio=criterio,
                fase="Encontrar peor caso",
                titulo=f"Peor pago de {alternativa}",
                formula=f"W({alternativa}) = min({', '.join(_fmt(v) for v in pagos[i])}) = {_fmt(minimo)}",
                explicacion="Este número representa lo que todavía obtendríamos si a esta alternativa le tocara su estado más desfavorable.",
                variables={"alternativa": alternativa, "peor_pago": minimo, "estado_peor_caso": estados[col]},
                estado_visual=_matriz_visual(alternativas, estados, pagos, criterio=criterio, fila_activa=i, columna_activa=col, resultados=minimos, etiquetas_resultado=["mínimo"]),
                enfoque={"tipo": "celda", "fila": i, "columna": col, "etiqueta": f"{alternativa} / {estados[col]}"},
            ))
        elegido = max(range(n), key=lambda i: minimos[i])
        borrador.append(_paso(
            criterio=criterio,
            fase="Seleccionar alternativa",
            titulo=f"Wald selecciona {alternativas[elegido]}",
            formula=f"max({', '.join(_fmt(v) for v in minimos)}) = {_fmt(minimos[elegido])}",
            explicacion="Entre los peores casos, elegimos el que tiene el resultado más alto. Es la regla maximin para una matriz de beneficios.",
            variables={"minimos": minimos, "alternativa_elegida": alternativas[elegido], "valor_elegido": minimos[elegido]},
            estado_visual=_matriz_visual(alternativas, estados, pagos, criterio=criterio, resultados=minimos, etiquetas_resultado=["mínimo"], filas_seleccionadas=[elegido]),
            enfoque={"tipo": "fila", "fila": elegido, "etiqueta": alternativas[elegido]},
        ))

    elif criterio == "hurwicz":
        borrador.append(_paso(
            criterio=criterio,
            fase="Preparar criterio de Hurwicz",
            titulo=f"Combinamos optimismo y pesimismo con α = {alpha:g}",
            formula="H(a_i) = α · max(a_i) + (1 − α) · min(a_i)",
            explicacion="Hurwicz no se queda solo con el peor ni con el mejor caso: pondera ambos. α controla cuánto pesa el escenario favorable.",
            variables={"alpha": alpha, "peso_mejor_caso": alpha, "peso_peor_caso": 1 - alpha},
            estado_visual=_matriz_visual(alternativas, estados, pagos, criterio=criterio),
        ))
        valores = []
        for i, alternativa in enumerate(alternativas):
            mejor = max(pagos[i])
            peor = min(pagos[i])
            valor = alpha * mejor + (1 - alpha) * peor
            valores.append(valor)
            borrador.append(_paso(
                criterio=criterio,
                fase="Combinar mejor y peor caso",
                titulo=f"Índice de Hurwicz para {alternativa}",
                formula=f"H({alternativa}) = {alpha:g}·{_fmt(mejor)} + {1-alpha:g}·{_fmt(peor)} = {_fmt(valor)}",
                explicacion="Usamos el mejor y el peor pago de la fila y los combinamos según α. Así hacemos explícita nuestra actitud ante el riesgo sin inventar probabilidades.",
                variables={"alternativa": alternativa, "mejor_pago": mejor, "peor_pago": peor, "alpha": alpha, "indice_hurwicz": valor},
                estado_visual=_matriz_visual(alternativas, estados, pagos, criterio=criterio, fila_activa=i, resultados=valores, etiquetas_resultado=["Hurwicz"]),
                enfoque={"tipo": "fila", "fila": i, "etiqueta": alternativa},
            ))
        elegido = max(range(n), key=lambda i: valores[i])
        borrador.append(_paso(
            criterio=criterio,
            fase="Seleccionar alternativa",
            titulo=f"Hurwicz selecciona {alternativas[elegido]}",
            formula=f"max({', '.join(_fmt(v) for v in valores)}) = {_fmt(valores[elegido])}",
            explicacion="Elegimos la alternativa con el índice de Hurwicz más alto. Cambiar α puede cambiar la decisión y eso es parte de lo que este criterio hace visible.",
            variables={"indices": valores, "alpha": alpha, "alternativa_elegida": alternativas[elegido], "valor_elegido": valores[elegido]},
            estado_visual=_matriz_visual(alternativas, estados, pagos, criterio=criterio, resultados=valores, etiquetas_resultado=["Hurwicz"], filas_seleccionadas=[elegido]),
            enfoque={"tipo": "fila", "fila": elegido, "etiqueta": alternativas[elegido]},
        ))

    elif criterio == "savage":
        borrador.append(_paso(
            criterio=criterio,
            fase="Construir matriz de arrepentimiento",
            titulo="Primero encontramos el mejor pago de cada estado",
            formula="M_j = max_i v(a_i, s_j)",
            explicacion="Savage pregunta cuánto dejamos de ganar por no haber elegido la mejor alternativa cuando finalmente conocemos el estado que ocurrió.",
            variables={"interpretacion": "regret = mejor pago de la columna − pago observado"},
            estado_visual=_matriz_visual(alternativas, estados, pagos, criterio=criterio),
        ))
        maxima = [max(pagos[i][j] for i in range(n)) for j in range(m)]
        borrador.append(_paso(
            criterio=criterio,
            fase="Encontrar máximos por estado",
            titulo="Marcamos el mejor pago posible en cada columna",
            formula=" + ".join(f"M_{j+1} = {_fmt(maxima[j])}" for j in range(m)),
            explicacion="Cada máximo es el punto de referencia contra el cual mediremos el arrepentimiento de todas las alternativas.",
            variables={"maximos_por_estado": maxima, "estados": estados},
            estado_visual=_matriz_visual(alternativas, estados, pagos, criterio=criterio, columna_activa=0, maxima_columnas=maxima),
        ))
        regrets = [[maxima[j] - pagos[i][j] for j in range(m)] for i in range(n)]
        for i, alternativa in enumerate(alternativas):
            for j, estado in enumerate(estados):
                borrador.append(_paso(
                    criterio=criterio,
                    fase="Calcular arrepentimiento",
                    titulo=f"Arrepentimiento de {alternativa} si ocurre {estado}",
                    formula=f"R({alternativa},{estado}) = {_fmt(maxima[j])} − {_fmt(pagos[i][j])} = {_fmt(regrets[i][j])}",
                    explicacion="Medimos cuánto habríamos dejado de ganar frente a la mejor alternativa disponible para ese estado.",
                    variables={"alternativa": alternativa, "estado": estado, "mejor_pago_estado": maxima[j], "pago_actual": pagos[i][j], "arrepentimiento": regrets[i][j]},
                    estado_visual=_matriz_visual(alternativas, estados, pagos, criterio=criterio, fila_activa=i, columna_activa=j, regret=regrets, maxima_columnas=maxima),
                    enfoque={"tipo": "celda", "fila": i, "columna": j, "etiqueta": f"R({alternativa},{estado})"},
                ))
        max_regret = [max(row) for row in regrets]
        borrador.append(_paso(
            criterio=criterio,
            fase="Elegir el menor peor arrepentimiento",
            titulo="Comparamos el peor arrepentimiento de cada alternativa",
            formula="S(a_i) = max_j R(a_i,s_j)  →  min_i S(a_i)",
            explicacion="Savage protege contra el peor arrepentimiento. Por eso primero tomamos el máximo de cada fila de arrepentimientos y después elegimos el mínimo.",
            variables={"arrepentimiento_maximo_por_alternativa": max_regret},
            estado_visual=_matriz_visual(alternativas, estados, pagos, criterio=criterio, resultados=max_regret, etiquetas_resultado=["máx. arrepentimiento"], regret=regrets, maxima_columnas=maxima),
        ))
        elegido = min(range(n), key=lambda i: max_regret[i])
        borrador.append(_paso(
            criterio=criterio,
            fase="Seleccionar alternativa",
            titulo=f"Savage selecciona {alternativas[elegido]}",
            formula=f"min({', '.join(_fmt(v) for v in max_regret)}) = {_fmt(max_regret[elegido])}",
            explicacion="Elegimos la alternativa cuyo peor arrepentimiento es el menor. La decisión busca reducir al máximo la sensación de 'haber elegido mal' después de conocer el estado.",
            variables={"maximos_de_arrepentimiento": max_regret, "alternativa_elegida": alternativas[elegido], "valor_elegido": max_regret[elegido]},
            estado_visual=_matriz_visual(alternativas, estados, pagos, criterio=criterio, resultados=max_regret, etiquetas_resultado=["máx. arrepentimiento"], filas_seleccionadas=[elegido], regret=regrets, maxima_columnas=maxima),
            enfoque={"tipo": "fila", "fila": elegido, "etiqueta": alternativas[elegido]},
        ))

    else:
        raise IncertidumbreInputError(f"Criterio no reconocido: {criterio}.")

    return borrador


def build_steps(
    *,
    alternativas: list[Any],
    estados: list[Any],
    pagos: list[list[Any]],
    criterio: str = "todos",
    alpha: Any = 0.6,
) -> list[dict[str, Any]]:
    """Genera el recorrido completo de uno o de todos los criterios."""
    alternativas, estados, pagos, alpha = validar_entrada(alternativas, estados, pagos, alpha)
    criterios = ["laplace", "wald", "hurwicz", "savage"] if criterio == "todos" else [criterio]
    borradores: list[dict[str, Any]] = []
    for nombre in criterios:
        borradores.extend(_crear_pasos_criterio(nombre, alternativas, estados, pagos, alpha))

    total = len(borradores)
    pasos: list[dict[str, Any]] = []
    for i, item in enumerate(borradores, start=1):
        estado_visual = item["estado_visual_local"]
        pasos.append(crear_paso(
            algoritmo="decision_incertidumbre",
            paso=i,
            total_pasos=total,
            fase=item["fase_local"],
            titulo=item["titulo_local"],
            formula=item["formula_local"],
            explicacion=item["explicacion_local"],
            variables=item["variables_local"],
            estado_visual=estado_visual,
            enfoque=item["enfoque_local"],
        ) | {"criterio": item["criterio"]})
    return pasos
