import unittest

from core.uncertainty import build_steps, default_payload


class UncertaintyTests(unittest.TestCase):
    def setUp(self):
        self.data = default_payload()

    def test_laplace_example(self):
        steps = build_steps(**{**self.data, "criterio": "laplace"})
        final = steps[-1]
        self.assertEqual(final["variables"]["alternativa_elegida"], "a2")
        self.assertAlmostEqual(final["variables"]["valor_elegido"], 15955)

    def test_wald_example(self):
        steps = build_steps(**{**self.data, "criterio": "wald"})
        final = steps[-1]
        self.assertEqual(final["variables"]["alternativa_elegida"], "a2")
        self.assertEqual(final["variables"]["valor_elegido"], 14000)

    def test_hurwicz_alpha_point_six(self):
        steps = build_steps(**{**self.data, "criterio": "hurwicz", "alpha": 0.6})
        final = steps[-1]
        self.assertEqual(final["variables"]["alternativa_elegida"], "a2")
        self.assertAlmostEqual(final["variables"]["valor_elegido"], 16346)

    def test_savage_example(self):
        steps = build_steps(**{**self.data, "criterio": "savage"})
        final = steps[-1]
        self.assertEqual(final["variables"]["alternativa_elegida"], "a2")
        self.assertEqual(final["variables"]["valor_elegido"], 1000)

    def test_all_criteria_share_step_schema(self):
        steps = build_steps(**self.data)
        self.assertEqual(len(steps), 25)
        required = {"algoritmo", "paso", "total_pasos", "fase", "titulo", "formula", "explicacion", "variables", "enfoque", "estado_visual", "criterio"}
        self.assertTrue(all(required <= set(step) for step in steps))
        self.assertTrue(all(step["total_pasos"] == len(steps) for step in steps))


if __name__ == "__main__":
    unittest.main()
