from core.decision_trees import DEFAULT_DATASET, build_steps


def test_build_steps_are_sequential():
    steps = build_steps(DEFAULT_DATASET, target="Jugar", criterion="entropy", max_depth=4)
    assert steps
    assert [step["paso"] for step in steps] == list(range(1, len(steps) + 1))
    assert all(step["total_pasos"] == len(steps) for step in steps)


def test_tree_has_visual_state_and_traversal():
    steps = build_steps(DEFAULT_DATASET, target="Jugar", criterion="gini", max_depth=3, sample_index=1)
    assert any(step["fase"] == "Evaluación de características" for step in steps)
    assert any(step["fase"] == "Recorrido guiado" for step in steps)
    assert all("estado_visual" in step for step in steps)


def test_tree_edges_include_branch_probabilities_and_weighted_sum():
    steps = build_steps(DEFAULT_DATASET, target="Jugar", criterion="entropy", max_depth=3)
    visual_states = [step["estado_visual"] for step in steps]
    with_edges = next(state for state in visual_states if state["aristas"])
    assert all("probabilidad" in edge and "aporte_ponderado" in edge for edge in with_edges["aristas"])
    assert any(node.get("suma_producto") for node in with_edges["nodos"] if not node["es_hoja"])
