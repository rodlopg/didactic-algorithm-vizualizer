import importlib.util
from pathlib import Path

MODULE_PATH = Path(__file__).parents[1] / "core" / "resource_allocation.py"
spec = importlib.util.spec_from_file_location("resource_test_module", MODULE_PATH)
# Cargamos como paquete real al ejecutar pytest desde el proyecto.
from core.resource_allocation import AsignacionInputError, build_steps, default_payload


def test_ejemplo_de_las_fuentes():
    data = default_payload()
    pasos = build_steps(**data)
    final = pasos[-1]
    assert final["variables"]["politica_optima"] == [1, 3, 1]
    assert final["variables"]["rendimiento_global"] == 170
    assert sum(final["variables"]["politica_optima"]) == 5


def test_tabla_optima_estado_inicial():
    pasos = build_steps(**default_payload())
    final = pasos[-1]
    dp = final["estado_visual"]["dp"]
    assert dp[0][5] == 170
    assert dp[1][5] == 160
    assert dp[2][5] == 130


def test_esquema_comun():
    pasos = build_steps(**default_payload())
    claves = {"algoritmo", "paso", "total_pasos", "fase", "titulo", "formula", "explicacion", "variables", "enfoque", "estado_visual"}
    assert all(claves <= set(p) for p in pasos)
    assert all(p["paso"] == i for i, p in enumerate(pasos, start=1))
    assert all(p["total_pasos"] == len(pasos) for p in pasos)


def test_rechaza_matriz_incompleta():
    data = default_payload()
    data["rendimientos"][0] = [0, 10]
    try:
        build_steps(**data)
    except AsignacionInputError as exc:
        assert "exactamente" in str(exc)
    else:
        raise AssertionError("Se esperaba AsignacionInputError")
