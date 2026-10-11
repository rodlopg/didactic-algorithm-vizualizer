"""Punto de entrada de Didactic Algorithm Visualizer."""

from __future__ import annotations

import json
import os
import threading
import webbrowser

from flask import Flask, jsonify, render_template, request

from core.decision_trees import ArbolInputError, build_steps, default_payload
from core.uncertainty import IncertidumbreInputError, build_steps as build_uncertainty_steps, default_payload as uncertainty_default_payload
from core.knapsack import MochilaInputError, build_steps as build_knapsack_steps, default_payload as knapsack_default_payload
from core.resource_allocation import AsignacionInputError, build_steps as build_resource_steps, default_payload as resource_default_payload
from core.machine_replacement import ReemplazoInputError, build_steps as build_machine_steps, default_payload as machine_default_payload

app = Flask(__name__)


def _es_ejecucion_local() -> bool:
    entorno = os.getenv("FLASK_ENV", "").lower()
    despliegue = os.getenv("DEPLOYMENT", "").lower()
    return entorno != "production" and despliegue not in {"production", "render", "cloud"}


def _abrir_navegador(port: int) -> None:
    if not _es_ejecucion_local():
        return

    def abrir() -> None:
        webbrowser.open_new(f"http://127.0.0.1:{port}/")

    threading.Timer(1.0, abrir).start()


@app.get("/")
def inicio():
    tree_json = json.dumps(default_payload()["tree"], ensure_ascii=False, indent=2)
    return render_template("index.html", default_tree_json=tree_json)


@app.get("/api/estado")
def estado():
    return jsonify({"ok": True, "mensaje": "El motor didáctico está disponible.", "idioma": "es", "fase": 7, "algoritmos": 5})


@app.get("/api/decision-tree/default")
def decision_tree_default():
    return jsonify(default_payload())


@app.post("/api/decision-tree/steps")
def decision_tree_steps():
    body = request.get_json(silent=True) or {}
    try:
        tree = body.get("tree")
        if isinstance(tree, str):
            tree = json.loads(tree)
        steps = build_steps(tree=tree)
    except (ArbolInputError, json.JSONDecodeError) as exc:
        return jsonify({"ok": False, "mensaje": str(exc), "tipo": "arbol_decision"}), 400
    except Exception:
        app.logger.exception("No se pudo construir el árbol de decisión económico")
        return jsonify({
            "ok": False,
            "mensaje": "No pudimos construir el árbol. Revisa las probabilidades, los pagos y la estructura del JSON.",
            "tipo": "arbol_decision",
        }), 400

    return jsonify({"ok": True, "pasos": steps})

@app.get("/incertidumbre")
def incertidumbre():
    return render_template("incertidumbre.html")


@app.get("/api/uncertainty/default")
def uncertainty_default():
    return jsonify(uncertainty_default_payload())


@app.get("/mochila")
def mochila():
    return render_template("mochila.html")


@app.get("/api/knapsack/default")
def knapsack_default():
    return jsonify(knapsack_default_payload())


@app.post("/api/knapsack/steps")
def knapsack_steps():
    body = request.get_json(silent=True) or {}
    try:
        steps = build_knapsack_steps(
            beneficios=body.get("beneficios", []),
            pesos=body.get("pesos", []),
            capacidad=body.get("capacidad", 7),
        )
    except MochilaInputError as exc:
        return jsonify({"ok": False, "mensaje": str(exc), "tipo": "aprendizaje"}), 400
    except Exception:
        return jsonify({
            "ok": False,
            "mensaje": "No pudimos construir la tabla. Revisa que beneficios y pesos tengan la misma longitud y que los pesos sean enteros positivos.",
            "tipo": "aprendizaje",
        }), 400
    return jsonify({"ok": True, "pasos": steps})


@app.get("/asignacion")
def asignacion():
    return render_template("asignacion.html")


@app.get("/api/resource-allocation/default")
def resource_allocation_default():
    return jsonify(resource_default_payload())


@app.post("/api/resource-allocation/steps")
def resource_allocation_steps():
    body = request.get_json(silent=True) or {}
    try:
        steps = build_resource_steps(
            brigadas=body.get("brigadas", 5),
            etapas=body.get("etapas", []),
            rendimientos=body.get("rendimientos", []),
        )
    except AsignacionInputError as exc:
        return jsonify({"ok": False, "mensaje": str(exc), "tipo": "aprendizaje"}), 400
    except Exception:
        return jsonify({
            "ok": False,
            "mensaje": "No pudimos construir esta asignación. Revisa el número de etapas y que cada fila tenga los rendimientos de 0 a B.",
            "tipo": "aprendizaje",
        }), 400
    return jsonify({"ok": True, "pasos": steps})


@app.get("/reemplazo")
def reemplazo():
    return render_template("reemplazo.html")


@app.get("/api/machine-replacement/default")
def machine_replacement_default():
    return jsonify(machine_default_payload())


@app.post("/api/machine-replacement/steps")
def machine_replacement_steps():
    body = request.get_json(silent=True) or {}
    try:
        steps = build_machine_steps(
            horizonte=body.get("horizonte", 4),
            edad_inicial=body.get("edad_inicial", 3),
            edad_maxima=body.get("edad_maxima", 6),
            costo_adquisicion=body.get("costo_adquisicion", 100000),
            ingresos=body.get("ingresos", []),
            costos_operacion=body.get("costos_operacion", []),
            valores_desecho=body.get("valores_desecho", []),
        )
    except ReemplazoInputError as exc:
        return jsonify({"ok": False, "mensaje": str(exc), "tipo": "aprendizaje"}), 400
    except Exception:
        return jsonify({"ok": False, "mensaje": "No pudimos construir el problema de reemplazo. Revisa horizonte, costos y valores residuales.", "tipo": "aprendizaje"}), 400
    return jsonify({"ok": True, "pasos": steps})


@app.post("/api/uncertainty/steps")
def uncertainty_steps():
    body = request.get_json(silent=True) or {}
    try:
        steps = build_uncertainty_steps(
            alternativas=body.get("alternativas", []),
            estados=body.get("estados", []),
            pagos=body.get("pagos", []),
            criterio=str(body.get("criterio", "todos")),
            alpha=body.get("alpha", 0.6),
        )
    except IncertidumbreInputError as exc:
        return jsonify({"ok": False, "mensaje": str(exc), "tipo": "aprendizaje"}), 400
    except Exception:
        return jsonify({"ok": False, "mensaje": "No pudimos construir este recorrido. Revisa la matriz y sus valores numéricos.", "tipo": "aprendizaje"}), 400
    return jsonify({"ok": True, "pasos": steps})


@app.errorhandler(404)
def recurso_no_encontrado(_error):
    return jsonify({"ok": False, "mensaje": "No encontramos esa ruta. Regresa al inicio para continuar."}), 404


def ejecutar() -> None:
    host = os.getenv("HOST", "127.0.0.1")
    try:
        port = int(os.getenv("PORT", "5000"))
    except ValueError:
        port = 5000
    _abrir_navegador(port)
    app.run(host=host, port=port, debug=False, use_reloader=False)


if __name__ == "__main__":
    ejecutar()
