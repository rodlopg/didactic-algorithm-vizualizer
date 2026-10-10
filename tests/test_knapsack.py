import unittest

from core.knapsack import build_steps


class MochilaTests(unittest.TestCase):
    def test_ejemplo_fuente(self):
        steps = build_steps(beneficios=[16, 19, 23, 28], pesos=[2, 3, 4, 5], capacidad=7)
        self.assertEqual(38, len(steps))
        final = steps[-1]
        self.assertEqual(44, final["variables"]["beneficio_optimo"])
        self.assertEqual(7, final["variables"]["peso_total"])
        self.assertEqual([1, 0, 0, 1], final["variables"]["vector_binario"])
        self.assertEqual([1, 4], final["variables"]["objetos_seleccionados"])
        self.assertEqual(44, final["estado_visual"]["dp"][4][7])
        self.assertEqual([0, 0, 16, 19, 23, 35, 39, 44], final["estado_visual"]["dp"][4])

    def test_celda_que_no_cabe(self):
        steps = build_steps(beneficios=[10], pesos=[4], capacidad=2)
        step = next(s for s in steps if s["enfoque"].get("fila") == 1 and s["enfoque"].get("columna") == 2)
        self.assertFalse(step["variables"]["cabe"])
        self.assertEqual(0, step["variables"]["resultado"])

    def test_capacidad_cero(self):
        steps = build_steps(beneficios=[10, 5], pesos=[1, 2], capacidad=0)
        self.assertEqual([0, 0], steps[-1]["variables"]["vector_binario"])
        self.assertEqual(0, steps[-1]["variables"]["beneficio_optimo"])

    def test_esquema_comun(self):
        steps = build_steps(beneficios=[16, 19, 23, 28], pesos=[2, 3, 4, 5], capacidad=7)
        requeridos = {"algoritmo", "paso", "total_pasos", "fase", "titulo", "formula", "explicacion", "variables", "enfoque", "estado_visual"}
        for step in steps:
            self.assertTrue(requeridos.issubset(step))
            self.assertEqual("mochila_01", step["algoritmo"])
            self.assertEqual(len(steps), step["total_pasos"])


if __name__ == "__main__":
    unittest.main()


def test_recorrido_es_por_columnas():
    steps = build_steps(beneficios=[16, 19], pesos=[2, 3], capacidad=4)
    eval_steps = [s for s in steps if s["fase"] == "Llenar la tabla de programación dinámica"]
    pairs = [(s["enfoque"]["columna"], s["enfoque"]["fila"]) for s in eval_steps]
    assert pairs == [(d, k) for d in range(5) for k in range(1, 3)]
