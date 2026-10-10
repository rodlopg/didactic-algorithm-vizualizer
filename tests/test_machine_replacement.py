import unittest

from core.machine_replacement import build_steps


DEFAULT = {
    "horizonte": 4,
    "edad_inicial": 3,
    "edad_maxima": 6,
    "costo_adquisicion": 100000,
    "ingresos": [20000, 19000, 18500, 17200, 15500, 14000, 12200],
    "costos_operacion": [200, 600, 1200, 1500, 1700, 1800, 2200],
    "valores_desecho": [None, 80000, 60000, 50000, 30000, 10000, 5000],
}


class ReemplazoMaquinasTests(unittest.TestCase):
    def test_ejemplo_docente(self):
        steps = build_steps(**DEFAULT)
        final = steps[-1]
        self.assertEqual("reemplazo_maquinas", final["algoritmo"])
        self.assertEqual(55300, final["variables"]["ingreso_optimo"])
        self.assertEqual({"RKKR", "RRKK"}, set(final["variables"]["politicas_optimas"]))

    def test_estados_alcanzables_como_en_el_grafo(self):
        steps = build_steps(**DEFAULT)
        state = steps[-1]["estado_visual"]
        self.assertEqual([3], state["estados_por_anio"]["1"])
        self.assertEqual([1, 4], state["estados_por_anio"]["2"])
        self.assertEqual([1, 2, 5], state["estados_por_anio"]["3"])
        self.assertEqual([1, 2, 3, 6], state["estados_por_anio"]["4"])
        self.assertEqual([1, 2, 3, 4], state["estados_por_anio"]["5"])

    def test_decisiones_por_etapa(self):
        steps = build_steps(**DEFAULT)
        state = steps[-1]["estado_visual"]
        self.assertEqual(["R"], state["decisiones_optimas"]["1"]["3"])
        self.assertEqual(["K", "R"], state["decisiones_optimas"]["2"]["1"])
        self.assertEqual(["R"], state["decisiones_optimas"]["2"]["4"])
        self.assertEqual(["R"], state["decisiones_optimas"]["4"]["6"])

    def test_hay_acciones_k_r_y_s(self):
        steps = build_steps(**DEFAULT)
        actions = {edge["accion"] for edge in steps[-1]["estado_visual"]["aristas"]}
        self.assertTrue({"K", "R", "S"}.issubset(actions))

    def test_esquema(self):
        steps = build_steps(**DEFAULT)
        requeridos = {
            "algoritmo", "paso", "total_pasos", "fase", "titulo", "formula",
            "explicacion", "variables", "enfoque", "estado_visual"
        }
        for step in steps:
            self.assertTrue(requeridos.issubset(step))
            self.assertEqual(len(steps), step["total_pasos"])

    def test_valores_de_programacion_dinamica_del_ejemplo(self):
        steps = build_steps(**DEFAULT)
        state = steps[-1]["estado_visual"]
        self.assertEqual(79800, state["dp"]["4"]["1"])
        self.assertEqual(67300, state["dp"]["4"]["2"])
        self.assertEqual(49800, state["dp"]["4"]["3"])
        self.assertEqual(4800, state["dp"]["4"]["6"])
        self.assertEqual(85500, state["dp"]["2"]["1"])
        self.assertEqual(55300, state["dp"]["1"]["3"])

    def test_transiciones_respetan_k_y_r(self):
        steps = build_steps(**DEFAULT)
        edges = steps[-1]["estado_visual"]["aristas"]
        # Desde año 1 / edad 3: K -> edad 4 y R -> edad 1 en año 2.
        source = [e for e in edges if e["origen"] == "e1-t3"]
        self.assertEqual({"K", "R"}, {e["accion"] for e in source})
        self.assertEqual("e2-t4", next(e["destino"] for e in source if e["accion"] == "K"))
        self.assertEqual("e2-t1", next(e["destino"] for e in source if e["accion"] == "R"))


if __name__ == "__main__":
    unittest.main()
