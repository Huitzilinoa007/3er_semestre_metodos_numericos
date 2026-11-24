# Gráficas de los métodos cerrados (Bisección y Regla Falsa).
from __future__ import annotations

import numpy as np
import plotly.graph_objects as go

from . import estilo as E


def figura_cerrado(res, k, rango):
    """Foto estática de la iteración k (la controla el slider de la página)."""
    f, df = res.ctx["f"], res.df
    r = df.iloc[k - 1]   # k empieza en 1 (como lo ve el usuario); el DataFrame empieza en 0.
    xs = np.linspace(rango[0], rango[1], 600)   # 600 puntos bastan para que la curva se vea suave.
    ys = f(xs)
    lo, hi = E.rango_y(ys)

    fig = E.lienzo("Búsqueda geométrica")
    E.curva(fig, xs, ys)
    # Las rectas verticales marcan los extremos a y b del intervalo actual.
    fig.add_trace(go.Scatter(x=[r["a"], r["a"]], y=[lo, hi], mode="lines", name="a",
                             line=dict(color=E.MENTA, dash="dash")), row=1, col=1)
    fig.add_trace(go.Scatter(x=[r["b"], r["b"]], y=[lo, hi], mode="lines", name="b",
                             line=dict(color=E.VIOLETA, dash="dash")), row=1, col=1)
    if res.id == "falsa_posicion":
        # Solo la regla falsa dibuja la cuerda, porque c sale de donde ella cruza el eje x.
        fig.add_trace(go.Scatter(x=[r["a"], r["b"]], y=[r["f(a)"], r["f(b)"]], mode="lines+markers",
                                 name="Cuerda", line=dict(color=E.GRIS, dash="dashdot"),
                                 marker=dict(size=7)), row=1, col=1)
    previos = df["c"].iloc[:k - 1]
    if len(previos):
        fig.add_trace(go.Scatter(x=previos, y=[0] * len(previos), mode="markers", name="c anteriores",
                                 marker=dict(color=E.GRIS, size=6)), row=1, col=1)
    # La raíz c actual va en ámbar: es lo más importante de la gráfica.
    fig.add_trace(go.Scatter(
        x=[r["c"], r["c"]], y=[0, r["f(c)"]], mode="lines+markers+text", name="Raíz c",
        text=[f"c = {r['c']:.4f}", ""], textposition="top center",
        line=dict(color=E.AMBAR, dash="dot"), marker=dict(size=[12, 8], color=E.AMBAR)), row=1, col=1)
    fig.update_xaxes(range=list(rango), row=1, col=1)
    fig.update_yaxes(range=[lo, hi], row=1, col=1)
    E.panel_error(fig, df, k, nombre="Error |cᵢ − cᵢ₋₁|")

    err = "N/A (iteración 1)" if np.isnan(r["error"]) else f"{r['error']:.3e}"
    return E.estilizar(fig, f"Iteración {k}: c = {r['c']:.6f}, f(c) = {r['f(c)']:.2e}, error = {err}")


def graficar_metodo_cerrado(f, df, rango_x: tuple):
    """Animación Plotly original (Play/Pausa + slider), con la paleta nueva.

    Misma firma y comportamiento que tu `plotter.py`; ahora tolera NaN e infinitos en f(x).
    """
    x_vals = np.linspace(rango_x[0], rango_x[1], 400)
    y_vals = f(x_vals)
    y_min, y_max = E.rango_y(y_vals)

    fig = E.lienzo("Búsqueda geométrica paso a paso", "Convergencia del error absoluto", pesos=(0.65, 0.35))

    # Aquí se arma un "frame" por iteración: Plotly los reproduce uno tras otro para dar la animación.
    frames = []
    for idx, row in df.iterrows():
        it = int(row["iter"])
        err_txt = f"{row['error']:.6f}" if not np.isnan(row["error"]) else "N/A (Iter 1)"
        df_parcial = df.iloc[:idx + 1]   # El error se va dibujando hasta la iteración actual.
        frames.append(go.Frame(
            name=str(it),
            data=[
                go.Scatter(x=x_vals, y=y_vals, mode="lines", name="f(x)", line=dict(color=E.CIAN, width=3)),
                go.Scatter(x=[row["a"], row["a"]], y=[y_min, y_max], mode="lines", name="a",
                           line=dict(color=E.MENTA, dash="dash")),
                go.Scatter(x=[row["b"], row["b"]], y=[y_min, y_max], mode="lines", name="b",
                           line=dict(color=E.VIOLETA, dash="dash")),
                go.Scatter(x=[row["c"], row["c"]], y=[0, row["f(c)"]], mode="lines+markers+text", name="Raíz c",
                           text=[f"c = {row['c']:.4f}", ""], textposition="top center",
                           line=dict(color=E.AMBAR, dash="dot"), marker=dict(size=[12, 8], color=E.AMBAR)),
                go.Scatter(x=df_parcial["iter"], y=df_parcial["error"], mode="lines+markers",
                           name="Error |c_i - c_{i-1}|", line=dict(color=E.GRIS, width=2), marker=dict(size=8)),
            ],
            traces=[0, 1, 2, 3, 4],
            layout=go.Layout(title_text=f"Iteración {it}: c = {row['c']:.6f}, f(c) = {row['f(c)']:.2e}, error = {err_txt}"),
        ))

    # Estado inicial: la primera iteración (los 4 primeros trazos a la izquierda y el del error a la derecha).
    for trace in frames[0].data[:4]:
        fig.add_trace(trace, row=1, col=1)
    fig.add_trace(frames[0].data[4], row=1, col=2)

    fig.frames = frames
    fig.update_xaxes(range=[rango_x[0], rango_x[1]], row=1, col=1)
    fig.update_yaxes(range=[y_min, y_max], row=1, col=1)
    fig.update_xaxes(title_text="Iteración", row=1, col=2)
    fig.update_yaxes(title_text="Error (escala log)", type="log", row=1, col=2)

    E.estilizar(fig, frames[0].layout.title.text, alto=580, margen_b=110)
    fig.update_layout(
        updatemenus=[dict(
            type="buttons", showactive=False, x=0.0, y=-0.22, xanchor="left", yanchor="top",
            bgcolor="#1A2330", bordercolor=E.GRIS, font=dict(color=E.TEXTO),
            buttons=[
                dict(label="▶ Play", method="animate",
                     args=[None, dict(frame=dict(duration=700, redraw=True), fromcurrent=True)]),
                dict(label="⏸ Pausa", method="animate",
                     args=[[None], dict(frame=dict(duration=0, redraw=False), mode="immediate")]),
            ])],
        sliders=[dict(
            steps=[dict(method="animate", args=[[fr.name], dict(mode="immediate", frame=dict(duration=300, redraw=True))],
                        label=f" {fr.name}") for fr in frames],
            currentvalue=dict(prefix="Iteración: "), y=-0.05,
            bgcolor=E.REJILLA, activebgcolor=E.CIAN, bordercolor=E.GRIS, font=dict(color=E.TEXTO))],
    )
    return fig
