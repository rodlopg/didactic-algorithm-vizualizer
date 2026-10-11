import pytest

from core.decision_trees import DEFAULT_TREE, ArbolInputError, build_steps


def test_default_tree_uses_probabilities_and_payoffs_not_entropy():
    steps = build_steps()
    assert steps
    assert [step["paso"] for step in steps] == list(range(1, len(steps) + 1))
    assert all(step["total_pasos"] == len(steps) for step in steps)
    assert not any("entropía" in step["formula"].lower() or "gini" in step["formula"].lower() for step in steps)
    assert any(step["fase"] == "Evaluación de un suceso" for step in steps)
    assert any(step["fase"] == "Valor esperado" for step in steps)
    assert any(step["fase"] == "Comparación de alternativas" for step in steps)
    final = steps[-1]
    assert final["variables"]["política_óptima"]["elegir"] == "Alto presupuesto"
    assert float(final["variables"]["valor_esperado_óptimo"].replace(",", ".")) == pytest.approx(2.8)


def test_each_chance_edge_displays_probability_and_expected_contribution():
    steps = build_steps()
    final_visual = steps[-1]["estado_visual"]
    chance_edges = [edge for edge in final_visual["aristas"] if edge["tipo"] == "chance"]
    assert chance_edges
    assert all(edge["probabilidad"] is not None for edge in chance_edges)
    assert all(edge["evaluada"] and edge["contribucion"] is not None for edge in chance_edges)
    assert all(node["tipo"] in {"decision", "chance", "terminal"} for node in final_visual["nodos"])


def test_probability_totals_must_equal_one():
    bad = {
        "type": "decision", "label": "Elegir",
        "options": [
            {"label": "A", "next": {"type": "chance", "label": "S", "events": [
                {"label": "Éxito", "probability": 0.6, "payoff": 10},
                {"label": "Fracaso", "probability": 0.3, "payoff": -2},
            ]}},
            {"label": "B", "payoff": 0},
        ],
    }
    with pytest.raises(ArbolInputError, match="deben sumar 1"):
        build_steps(bad)


def test_multilevel_tree_resolves_by_backward_induction():
    multi = {
        "type": "decision", "label": "Presupuesto temporada 1", "options": [
            {"label": "Bajo", "next": {"type": "chance", "label": "Resultado temporada 1 bajo", "events": [
                {"label": "Éxito", "probability": 0.6, "payoff": 5, "next": {"type": "decision", "label": "Temporada 2 tras éxito bajo", "options": [
                    {"label": "Bajo", "next": {"type": "chance", "label": "Temporada 2 bajo", "events": [
                        {"label": "Éxito", "probability": 0.65, "payoff": 6},
                        {"label": "Fracaso", "probability": 0.35, "payoff": -1.4},
                    ]}},
                    {"label": "Alto", "next": {"type": "chance", "label": "Temporada 2 alto", "events": [
                        {"label": "Éxito", "probability": 0.9, "payoff": 5.5},
                        {"label": "Fracaso", "probability": 0.1, "payoff": -2.2},
                    ]}},
                ]}},
                {"label": "Fracaso", "probability": 0.4, "payoff": -1, "next": {"type": "terminal", "label": "Cancelar la serie", "payoff": -0.1}},
            ]}},
            {"label": "Alto", "next": {"type": "chance", "label": "Resultado temporada 1 alto", "events": [
                {"label": "Éxito", "probability": 0.8, "payoff": 4, "next": {"type": "decision", "label": "Temporada 2 tras éxito alto", "options": [
                    {"label": "Bajo", "next": {"type": "chance", "label": "Temporada 2 bajo", "events": [
                        {"label": "Éxito", "probability": 0.55, "payoff": 7},
                        {"label": "Fracaso", "probability": 0.45, "payoff": -1.2},
                    ]}},
                    {"label": "Alto", "next": {"type": "chance", "label": "Temporada 2 alto", "events": [
                        {"label": "Éxito", "probability": 0.95, "payoff": 4.5},
                        {"label": "Fracaso", "probability": 0.05, "payoff": -2.5},
                    ]}},
                ]}},
                {"label": "Fracaso", "probability": 0.2, "payoff": -2, "next": {"type": "terminal", "label": "Cancelar la serie", "payoff": -0.3}},
            ]}},
        ],
    }
    steps = build_steps(multi)
    final = steps[-1]["variables"]
    assert float(final["valor_esperado_óptimo"].replace(",", ".")) == pytest.approx(6.06)
    assert final["política_óptima"]["elegir"] == "Alto"


def test_default_payload_has_decision_tree_structure():
    assert DEFAULT_TREE["type"] == "decision"
    assert len(DEFAULT_TREE["options"]) == 2
    assert all(option["next"]["type"] == "chance" for option in DEFAULT_TREE["options"])
