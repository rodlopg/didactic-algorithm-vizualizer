"""Construcción homogénea de pasos para la interfaz didáctica."""

from __future__ import annotations

from typing import Any


def crear_paso(
    *,
    algoritmo: str,
    paso: int,
    total_pasos: int,
    fase: str,
    titulo: str,
    formula: str,
    explicacion: str,
    variables: dict[str, Any],
    estado_visual: dict[str, Any],
    enfoque: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Devuelve el contrato visual compartido por todos los algoritmos."""
    return {
        "algoritmo": algoritmo,
        "paso": paso,
        "total_pasos": total_pasos,
        "fase": fase,
        "titulo": titulo,
        "formula": formula,
        "explicacion": explicacion,
        "variables": variables,
        "enfoque": enfoque or {"tipo": "global"},
        "estado_visual": estado_visual,
    }
