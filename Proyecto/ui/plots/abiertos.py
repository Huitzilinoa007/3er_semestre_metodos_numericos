# Gráficas de los métodos abiertos: Newton, Secante, Punto Fijo y Müller.
from __future__ import annotations

import numpy as np
import plotly.graph_objects as go

from . import estilo as E


def _base(res, rango, titulo, f=None, nombre="f(x)"):
    # Aquí se arma lo común a todos: la curva en el rango elegido y los límites verticales.
    f = f or res.ctx["f"]
    xs = np.linspace(rango[0], rango[1], 600)
    ys = f(xs)
    lo, hi = E.rango_y(ys)
    fig = E.lienzo(titulo)
    E.curva(fig, xs, ys, nombre)
    fig.update_xaxes(range=list(rango), row=1, col=1)
    fig.update_yaxes(range=[lo, hi], row=1, col=1)
    return fig, xs, ys


def _linea(fig, x, y, nombre, color, dash="dash"):
    # Atajo para dibujar una línea auxiliar (tangente, secante, altura...) en la gráfica de la izquierda.
    fig.add_trace(go.Scatter(x=x, y=y, mode="lines", name=nombre, line=dict(color=color, dash=dash)), row=1, col=1)


def _punto(fig, x, y, nombre, color, size=10, texto=None):
    # Atajo para marcar un punto; si trae `texto` se escribe encima (por ejemplo el valor de la aproximación).
    fig.add_trace(go.Scatter(x=[x], y=[y], mode="markers+text" if texto else "markers", name=nombre,
                             text=[texto] if texto else None, textposition="top center",
                             marker=dict(color=color, size=size)), row=1, col=1)


def _titulo(k, valor, r, etiqueta="x"):
    # Título de la figura: iteración actual, aproximación y error (o N/A en la primera, que aún no tiene error).
    err = "N/A" if np.isnan(r["error"]) else f"{r['error']:.3e}"
    return f"Iteración {k}: {etiqueta} = {valor:.6f}, error = {err}"


def figura_newton(res, k, rango):
    r = res.df.iloc[k - 1]   # Fila de la iteración k (k empieza en 1 para el usuario; el DataFrame, en 0).
    xk, fx, x1, dfx = r["x"], r["f(x)"], r["x1"], r["f'(x)"]
    # Aquí se usa la base común (curva y límites) y luego se agrega lo propio de Newton: la tangente.
    fig, _, _ = _base(res, rango, "Método de la tangente")
    previos = res.df["x"].iloc[:k - 1]
    if len(previos):
        fig.add_trace(go.Scatter(x=previos, y=[0] * len(previos), mode="markers", name="Aproximaciones previas",
                                 marker=dict(color=E.GRIS, size=6)), row=1, col=1)
    # La línea punteada vertical muestra la altura f(xₖ) del punto desde donde sale la tangente.
    _linea(fig, [xk, xk], [0, fx], "Altura f(xₖ)", E.GRIS, "dot")
    xt = np.array(rango, dtype=float)   # Solo se necesitan los dos extremos del rango para trazar una recta.
    # La tangente es la recta y = f(xk) + f'(xk)·(x − xk); se dibuja en todo el ancho y el eje la recorta.
    _linea(fig, xt, fx + dfx * (xt - xk), "Tangente en xₖ", E.VIOLETA)
    # Punto de partida de esta iteración (cian) y, sobre el eje x, el cruce de la tangente: la nueva aproximación (ámbar).
    _punto(fig, xk, fx, f"(x_{k-1}, f)", E.CIAN)
    _punto(fig, x1, 0, f"x_{k}", E.AMBAR, 13, f"x = {x1:.4f}")
    E.panel_error(fig, res.df, k)   # A la derecha: cómo baja el error iteración tras iteración.
    return E.estilizar(fig, _titulo(k, x1, r))


def figura_secante(res, k, rango):
    r = res.df.iloc[k - 1]
    x0, x1, x2, f0, f1 = r["x_0"], r["x_1"], r["x_2"], r["f(x_0)"], r["f(x_1)"]
    # Misma base que Newton; lo propio de la secante es la recta que pasa por los dos últimos puntos.
    fig, _, _ = _base(res, rango, "Método de la secante")
    previos = res.df["x_2"].iloc[:k - 1]
    if len(previos):
        fig.add_trace(go.Scatter(x=previos, y=[0] * len(previos), mode="markers", name="Aproximaciones previas",
                                 marker=dict(color=E.GRIS, size=6)), row=1, col=1)
    if x1 != x0:   # Evita dividir entre cero al calcular la pendiente.
        xt = np.array(rango, dtype=float)
        _linea(fig, xt, f1 + (f1 - f0) / (x1 - x0) * (xt - x1), "Recta secante", E.VIOLETA)
    # Los dos puntos por los que pasa la secante (verde el más viejo, cian el más reciente) y, en ámbar, donde cruza el eje x.
    _punto(fig, x0, f0, "(x_{k-1}, f)", E.MENTA)
    _punto(fig, x1, f1, "(x_k, f)", E.CIAN)
    _punto(fig, x2, 0, f"x_{k + 1}", E.AMBAR, 13, f"x = {x2:.4f}")
    E.panel_error(fig, res.df, k)
    return E.estilizar(fig, _titulo(k, x2, r))


def figura_punto_fijo(res, k, rango):
    df, g = res.df, res.ctx["g"]   # Aquí la curva que se dibuja es g(x), no f(x), porque el método itera x = g(x).
    fig, xs, _ = _base(res, rango, "Diagrama de telaraña", f=g, nombre="g(x)")
    _linea(fig, xs, xs, "y = x", E.GRIS)   # La recta y = x: donde g(x) la cruza está la solución.
    # Telaraña: sube hasta g(x), va horizontal hasta y = x, y vuelve a subir; así se ve cómo se acerca al punto fijo.
    camino_x, camino_y = [df["x0"].iloc[0]], [0.0]
    for i in range(k):
        xi, xn = df["x0"].iloc[i], df["x1"].iloc[i]
        camino_x += [xi, xn]
        camino_y += [xn, xn]
    fig.add_trace(go.Scatter(x=camino_x, y=camino_y, mode="lines+markers", name="Iteraciones",
                             line=dict(color=E.VIOLETA, width=2), marker=dict(size=5)), row=1, col=1)
    r = df.iloc[k - 1]
    # El punto actual queda sobre la recta y = x (ámbar): ahí g(x) = x, que es justo un punto fijo.
    _punto(fig, r["x1"], r["x1"], f"x_{k}", E.AMBAR, 13, f"x = {r['x1']:.4f}")
    # El rango vertical debe mostrar tanto g(x) como la recta y = x, por eso se calcula con las dos juntas.
    lo, hi = E.rango_y(np.concatenate([g(np.linspace(rango[0], rango[1], 200)), xs]))
    fig.update_yaxes(range=[min(lo, rango[0]), max(hi, rango[1])], row=1, col=1)
    E.panel_error(fig, df, k)
    return E.estilizar(fig, _titulo(k, r["x1"], r))


def figura_muller(res, k, rango):
    df = res.df
    r = df.iloc[k - 1]
    # Aquí se dibuja f en el eje real y, encima, la parábola que Müller ajustó con los tres puntos de esta iteración.
    fig, _, _ = _base(res, rango, "Parábola por tres puntos (parte real)")
    xs = np.linspace(rango[0], rango[1], 600)
    z = xs - r["P2"]
    # La parábola es a(x−P2)² + b(x−P2) + c; con complejos solo se puede dibujar su parte real.
    parabola = np.real(r["a"] * z ** 2 + r["b"] * z + r["c"])
    _linea(fig, xs, parabola, "Parábola", E.VIOLETA)
    # Los tres puntos que definen la parábola, cada uno con su color para distinguirlos.
    for i, color in zip(range(3), (E.MENTA, E.GRIS, E.CIAN)):
        _punto(fig, np.real(r[f"P{i}"]), np.real(r[f"f(P{i})"]), f"P_{i}", color)
    p3 = r["P3"]   # La nueva aproximación: donde la parábola cruza el eje x (puede ser compleja).
    _punto(fig, np.real(p3), 0, "P_3", E.AMBAR, 13, f"P₃ = {np.real(p3):.4f}")
    if abs(np.imag(p3)) > 1e-12:
        fig.add_annotation(text="P₃ es complejo: se muestra su parte real", xref="x domain", yref="y domain",
                           x=0.02, y=0.97, showarrow=False, font=dict(color=E.CORAL, size=12), xanchor="left")
    E.panel_error(fig, df, k, nombre="Error |P₃ − P₂|")
    err = f"{r['error']:.3e}"
    return E.estilizar(fig, f"Iteración {k}: P₃ = {np.real(p3):.6f}{'+' if np.imag(p3) >= 0 else '-'}{abs(np.imag(p3)):.6f}i, error = {err}")
