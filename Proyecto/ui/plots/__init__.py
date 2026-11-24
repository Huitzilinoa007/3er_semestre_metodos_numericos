# Despachador de gráficas: a partir del id del método elige la función que dibuja su figura.
from __future__ import annotations

import numpy as np

from .abiertos import figura_muller, figura_newton, figura_punto_fijo, figura_secante
from .cerrados import figura_cerrado, graficar_metodo_cerrado
from .secuencias import figura_aitken, figura_deflacion

# Aquí se registra la gráfica de cada método. Para uno nuevo: escribe su función en este paquete y agrega una línea.
_FIGURAS = {
    "biseccion": figura_cerrado,
    "falsa_posicion": figura_cerrado,
    "newton": figura_newton,
    "secante": figura_secante,
    "punto_fijo": figura_punto_fijo,
    "aitken": figura_aitken,
    "deflacion": figura_deflacion,
    "muller": figura_muller,
}


def _con_margen(valores, relativo=0.35, minimo=1.0):
    # Rango que encuadra todos los puntos con un margen (para que se vea la curva alrededor de las iteraciones).
    v = np.real(np.asarray(valores)).astype(float)
    v = v[np.isfinite(v)]
    if v.size == 0:
        return -5.0, 5.0
    lo, hi = float(v.min()), float(v.max())
    pad = max(relativo * (hi - lo), minimo)
    return lo - pad, hi + pad


def rango_auto(res) -> tuple[float, float]:
    """Rango del eje X que encuadra los puntos del método, con margen."""
    df, ctx = res.df, res.ctx
    if res.id in ("biseccion", "falsa_posicion"):
        a, b = ctx["a0"], ctx["b0"]
        pad = 0.25 * (b - a)
        return a - pad, b + pad
    if res.id == "newton":
        return _con_margen(np.concatenate([df["x"], df["x1"]]))
    if res.id == "secante":
        return _con_margen(np.concatenate([df["x_0"], df["x_1"], df["x_2"]]))
    if res.id == "punto_fijo":
        return _con_margen(np.concatenate([df["x0"], df["x1"]]))
    if res.id == "muller":
        return _con_margen(np.concatenate([df[c].to_numpy() for c in ("P0", "P1", "P2", "P3")]))
    if res.id == "deflacion":
        return _con_margen(np.asarray(res.valor, dtype=float))
    return -5.0, 5.0


def construir_figura(res, k: int, rango: tuple[float, float]):
    return _FIGURAS[res.id](res, k, rango)


def figura_animada(res, rango: tuple[float, float]):
    """Animación Plotly original (solo métodos cerrados)."""
    return graficar_metodo_cerrado(res.ctx["f"], res.df, rango)
