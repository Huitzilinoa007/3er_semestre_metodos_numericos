# Gráficas de Aitken (sucesión acelerada) y Deflación (polinomio y raíces).
from __future__ import annotations

import numpy as np
import pandas as pd  # Aquí se usa pandas para armar una mini tabla con el error de la sucesión original y compararlo con el de Aitken.
import plotly.graph_objects as go

from . import estilo as E


def figura_aitken(res, k, rango=None):
    # `rango` no se usa aquí (Aitken grafica términos de una sucesión, no una curva), pero se recibe para que todas
    # las funciones de gráfica tengan la misma forma y el despachador pueda llamarlas igual.
    df = res.df
    n = df["iter"] - 1   # Los términos de Aitken se numeran desde 0.
    fig = E.lienzo("Sucesión original y acelerada", "Error entre términos consecutivos", pesos=(0.55, 0.45))
    fig.add_trace(go.Scatter(x=n, y=df["x_n"], mode="lines+markers", name="Punto fijo xₙ",
                             line=dict(color=E.GRIS), marker=dict(size=6)), row=1, col=1)
    fig.add_trace(go.Scatter(x=n, y=df["aitken"], mode="lines+markers", name="Aitken x̂ₙ",
                             line=dict(color=E.CIAN, width=3), marker=dict(size=6)), row=1, col=1)
    r = df.iloc[k - 1]
    # Marca ámbar en el término que se está viendo con el slider.
    fig.add_trace(go.Scatter(x=[k - 1], y=[r["aitken"]], mode="markers+text", showlegend=False,
                             text=[f"x̂ = {r['aitken']:.6f}"], textposition="top center",
                             marker=dict(color=E.AMBAR, size=13)), row=1, col=1)
    fig.update_xaxes(title_text="n", row=1, col=1)
    fig.update_yaxes(title_text="Valor", row=1, col=1)

    # A la derecha se comparan los dos errores: se nota cuánto más rápido baja el de Aitken.
    crudo = pd.DataFrame({"iter": df["iter"], "e_crudo": (df["x_n+1"] - df["x_n"]).abs()})
    E.panel_error(fig, crudo, k, "e_crudo", "Punto fijo |xₙ₊₁ − xₙ|", E.GRIS)
    E.panel_error(fig, df, k, "error", "Aitken |x̂ₙ − x̂ₙ₋₁|", E.CIAN)
    err = "N/A" if np.isnan(r["error"]) else f"{r['error']:.3e}"
    return E.estilizar(fig, f"Término {k - 1}: x̂ = {r['aitken']:.6f}, error = {err}")


def figura_deflacion(res, k, rango):
    f, df = res.ctx["f"], res.df
    raices = np.asarray(res.valor, dtype=float)   # Todas las raíces encontradas, en el orden en que salieron.
    xs = np.linspace(rango[0], rango[1], 600)
    ys = f(xs)
    lo, hi = E.rango_y(ys)

    fig = E.lienzo("Polinomio y raíces encontradas", "Error final de Newton por etapa")
    E.curva(fig, xs, ys, "P(x)")
    encontradas = raices[:k - 1]   # Las raíces de etapas anteriores quedan en cian; la actual resalta en ámbar.
    if len(encontradas):
        fig.add_trace(go.Scatter(x=encontradas, y=[0] * len(encontradas), mode="markers", name="Raíces previas",
                                 marker=dict(color=E.CIAN, size=10)), row=1, col=1)
    actual = raices[k - 1]   # La raíz de la etapa que se está viendo con el slider.
    fig.add_trace(go.Scatter(x=[actual], y=[0], mode="markers+text", name=f"Raíz {k}",
                             text=[f"r = {actual:.4f}"], textposition="top center",
                             marker=dict(color=E.AMBAR, size=13)), row=1, col=1)
    fig.update_xaxes(range=list(rango), row=1, col=1)
    fig.update_yaxes(range=[lo, hi], row=1, col=1)

    # Barras (y no líneas) porque cada etapa es independiente; la de la etapa actual va en ámbar.
    colores = [E.AMBAR if i == k else E.GRIS for i in df["iter"]]
    fig.add_trace(go.Bar(x=df["iter"], y=df["error"], marker_color=colores, showlegend=False), row=1, col=2)
    fig.update_xaxes(title_text="Etapa", dtick=1, row=1, col=2)
    fig.update_yaxes(title_text="Error (escala log)", type="log", row=1, col=2)
    return E.estilizar(fig, f"Etapa {k}: raíz r = {actual:.6f}, {int(df.iloc[k - 1]['iteraciones'])} iteraciones de Newton")
