# Gráficas de los métodos directos: punto flotante, interpolación, derivación e integración.
# Todas reciben (res, k, rango) como las de raíces: k es el paso (fila de la tabla) que se elige con el slider.
from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from core.metodos.hermite import polinomio_hermite
from core.metodos.neville import neville
from core.parser import compilar

from . import estilo as E


def _sola(titulo):
    return make_subplots(rows=1, cols=1, subplot_titles=(titulo,))


def _malla(rango, n=600):
    return np.linspace(rango[0], rango[1], n)


# ----------------------------------------------------------------------------- punto flotante
def figura_punto_flotante(res, k, rango=None):
    c = res.ctx
    rep = c["rep"]
    n_exp, n_man = c["n_exp"], c["n_man"]
    bits = rep.bits
    total = len(bits)
    colores, textos = [], []
    for i, b in enumerate(bits):
        colores.append(E.CORAL if i == 0 else (E.VIOLETA if i <= n_exp else E.CIAN))
        textos.append(b)
    # ¿Qué bit de la mantisa produjo el paso k? Los bits del número (sin el 1 inicial) van llenando la mantisa.
    resaltado = None
    fila = res.df.iloc[k - 1]
    if not c["cero"] and not rep.subnormal:
        cadena = c["bits_enteros"] + c["bits_frac"]
        pos_uno = cadena.index("1") if "1" in cadena else None
        n_ent = len(res.df[res.df["parte"] == "entera"])
        if fila["parte"] == "entera":
            # Las divisiones dan los bits de derecha a izquierda: el paso j da el bit j desde el final.
            idx = len(c["bits_enteros"]) - int(fila["paso"])
        else:
            idx = len(c["bits_enteros"]) + (int(fila["paso"]) - n_ent - 1)
        if pos_uno is not None and idx > pos_uno:
            j = idx - pos_uno - 1   # Posición dentro de la mantisa.
            if j < n_man:
                resaltado = 1 + n_exp + j
    ancho = 1.0
    fig = go.Figure()
    for i in range(total):
        borde = E.AMBAR if i == resaltado else "rgba(0,0,0,0)"
        fig.add_shape(type="rect", x0=i * ancho, x1=(i + 1) * ancho - 0.08, y0=0, y1=1,
                      fillcolor=colores[i], opacity=0.85 if i != resaltado else 1.0,
                      line=dict(color=borde, width=4), layer="below")
    fig.add_trace(go.Scatter(x=[i + 0.46 for i in range(total)], y=[0.5] * total, mode="text", text=textos,
                             textfont=dict(color="#0B0F14", size=14 if total <= 32 else 9), hoverinfo="skip",
                             showlegend=False))
    for nombre, x0, x1, color in (("signo", 0, 1, E.CORAL), ("exponente", 1, 1 + n_exp, E.VIOLETA),
                                  ("mantisa", 1 + n_exp, total, E.CIAN)):
        fig.add_annotation(x=(x0 + x1) / 2, y=1.25, text=nombre, showarrow=False, font=dict(color=color, size=13))
    fig.update_xaxes(visible=False, range=[-0.5, total + 0.5])
    fig.update_yaxes(visible=False, range=[-0.6, 1.6])
    nota = "" if resaltado is None else f" — el bit de este paso queda en la posición {resaltado - n_exp} de la mantisa"
    titulo = f"0x{rep.hexadecimal}  ·  paso {k}: bit = {int(fila['bit'])}{nota}"
    return E.estilizar(fig, titulo, alto=300, margen_b=30)


# ----------------------------------------------------------------------------- interpolación
def _rango_nodos(xs, extra=()):
    v = np.array(list(xs) + [e for e in extra if e is not None], dtype=float)
    lo, hi = v.min(), v.max()
    pad = 0.15 * ((hi - lo) or 1.0)
    return lo - pad, hi + pad


def figura_neville(res, k, rango):
    c = res.ctx
    xs, ys, x = np.array(c["xs"]), np.array(c["ys"]), c["x"]
    gx = _malla(rango)
    fig = E.lienzo("Polinomios de Neville", "Valor Qᵢ,ᵢ al agregar cada nodo")
    if c.get("f") is not None:
        fig.add_trace(go.Scatter(x=gx, y=c["f"](gx), mode="lines", name="f(x)",
                                 line=dict(color=E.GRIS, width=2, dash="dot")), row=1, col=1)
    # Polinomio que pasa por los nodos 0..k−1 (el de la fila actual) y el completo, tenue.
    usados = k
    p_k = [neville(xs[:usados], ys[:usados], t)[0] for t in gx]
    p_n = [neville(xs, ys, t)[0] for t in gx]
    fig.add_trace(go.Scatter(x=gx, y=p_n, mode="lines", name=f"P (grado {len(xs) - 1})",
                             line=dict(color=E.CIAN, width=1.5, dash="dash"), opacity=0.6), row=1, col=1)
    fig.add_trace(go.Scatter(x=gx, y=p_k, mode="lines", name=f"P con nodos 0..{k - 1} (grado {k - 1})",
                             line=dict(color=E.CIAN, width=3)), row=1, col=1)
    fig.add_trace(go.Scatter(x=xs, y=ys, mode="markers", name="Nodos",
                             marker=dict(color=[E.AMBAR if i == k - 1 else E.MENTA for i in range(len(xs))], size=10)),
                  row=1, col=1)
    q = c["Q"][k - 1, k - 1]
    fig.add_trace(go.Scatter(x=[x], y=[q], mode="markers+text", name=f"Q{k - 1},{k - 1}",
                             text=[f"{q:.6f}"], textposition="top center",
                             marker=dict(color=E.AMBAR, size=13, symbol="diamond")), row=1, col=1)
    lo, hi = E.rango_y(np.concatenate([ys, np.array(p_n, dtype=float)]))
    fig.update_yaxes(range=[lo, hi], row=1, col=1)
    fig.update_xaxes(range=list(rango), row=1, col=1)
    diag = [c["Q"][i, i] for i in range(len(xs))]
    fig.add_trace(go.Scatter(x=list(range(len(xs))), y=diag, mode="lines+markers", name="Qᵢ,ᵢ",
                             line=dict(color=E.VIOLETA)), row=1, col=2)
    fig.add_trace(go.Scatter(x=[k - 1], y=[q], mode="markers", showlegend=False,
                             marker=dict(color=E.AMBAR, size=14, symbol="circle-open", line=dict(width=3))), row=1, col=2)
    fig.update_xaxes(title_text="i", dtick=1, row=1, col=2)
    return E.estilizar(fig, f"Fila i = {k - 1}: Q{k - 1},{k - 1} = P(x) con los nodos 0..{k - 1} = {q:.8f}")


def figura_hermite(res, k, rango):
    c = res.ctx
    xs, ys, dys = np.array(c["xs"]), np.array(c["ys"]), np.array(c["dys"])
    gx = _malla(rango)
    fig = _sola("Polinomio de Hermite (se construye término por término)")
    if c.get("f") is not None:
        fig.add_trace(go.Scatter(x=gx, y=c["f"](gx), mode="lines", name="f(x)",
                                 line=dict(color=E.GRIS, width=2, dash="dot")), row=1, col=1)
    yh = c["Hf"](gx)
    fig.add_trace(go.Scatter(x=gx, y=yh, mode="lines", name="H(x) completo", line=dict(color=E.CIAN, width=1.5),
                             opacity=0.35), row=1, col=1)
    parcial = compilar(polinomio_hermite(c["z"], c["Q"], hasta=k - 1))(gx)
    fig.add_trace(go.Scatter(x=gx, y=parcial, mode="lines", name=f"Hasta el término Q{k - 1},{k - 1}",
                             line=dict(color=E.CIAN, width=3)), row=1, col=1)
    # Pequeñas tangentes en cada nodo para ver que H respeta la pendiente.
    ancho = 0.06 * (rango[1] - rango[0])
    for xi, yi, di in zip(xs, ys, dys):
        fig.add_trace(go.Scatter(x=[xi - ancho, xi + ancho], y=[yi - di * ancho, yi + di * ancho], mode="lines",
                                 line=dict(color=E.VIOLETA, width=3), showlegend=False, hoverinfo="skip"), row=1, col=1)
    fig.add_trace(go.Scatter(x=xs, y=ys, mode="markers", name="Nodos (con su pendiente)",
                             marker=dict(color=[E.AMBAR if i == (k - 1) // 2 else E.MENTA for i in range(len(xs))], size=10)),
                  row=1, col=1)
    if c.get("x") is not None:
        fig.add_trace(go.Scatter(x=[c["x"]], y=[res.valor], mode="markers+text", name="H(x)",
                                 text=[f"{res.valor:.6f}"], textposition="top center",
                                 marker=dict(color=E.AMBAR, size=13, symbol="diamond")), row=1, col=1)
    lo, hi = E.rango_y(np.concatenate([ys, yh]))
    fig.update_yaxes(range=[lo, hi])
    fig.update_xaxes(range=list(rango))
    return E.estilizar(fig, f"Fila i = {k - 1}: se agrega el término de grado {k - 1} (coeficiente Q{k - 1},{k - 1} = {c['Q'][k - 1, k - 1]:.6g})")


# ----------------------------------------------------------------------------- derivación
def figura_derivada(res, k, rango):
    from core.metodos.derivacion import FORMULAS
    c = res.ctx
    r = res.df.iloc[k - 1]
    h = r["h"]
    x0, f = c["x0"], c["f"]
    gx = _malla(rango)
    fig = E.lienzo("Recta con la pendiente aproximada", "Error real según h")
    E.curva(fig, gx, f(gx))
    desplaz = FORMULAS[c["clave"]][0]
    px = np.array([x0 + s * h for s in desplaz])
    fig.add_trace(go.Scatter(x=px, y=f(px), mode="markers", name="Puntos que usa la fórmula",
                             marker=dict(color=E.MENTA, size=10)), row=1, col=1)
    y0 = f(x0)
    if c["exacta"] is not None:
        fig.add_trace(go.Scatter(x=gx, y=y0 + c["exacta"] * (gx - x0), mode="lines", name="Tangente exacta",
                                 line=dict(color=E.GRIS, dash="dot")), row=1, col=1)
    fig.add_trace(go.Scatter(x=gx, y=y0 + r["aproximación"] * (gx - x0), mode="lines", name="Pendiente aproximada",
                             line=dict(color=E.AMBAR, width=2.5, dash="dash")), row=1, col=1)
    lo, hi = E.rango_y(f(gx))
    fig.update_yaxes(range=[lo, hi], row=1, col=1)
    fig.update_xaxes(range=list(rango), row=1, col=1)
    if "error real" in res.df.columns:
        d = res.df[res.df["error real"] > 0]
        fig.add_trace(go.Scatter(x=d["h"].abs(), y=d["error real"], mode="lines+markers", name="Error real",
                                 line=dict(color=E.CIAN)), row=1, col=2)
        if r["error real"] > 0:
            fig.add_trace(go.Scatter(x=[abs(h)], y=[r["error real"]], mode="markers", showlegend=False,
                                     marker=dict(color=E.AMBAR, size=14, symbol="circle-open", line=dict(width=3))),
                          row=1, col=2)
        fig.update_xaxes(title_text="|h| (escala log)", type="log", row=1, col=2)
        fig.update_yaxes(title_text="Error (escala log)", type="log", row=1, col=2)
    return E.estilizar(fig, f"Paso {k}: h = {h:g}, f'(x₀) ≈ {r['aproximación']:.8f}")


def rango_derivada(res):
    c = res.ctx
    h = abs(c["h"])
    from core.metodos.derivacion import FORMULAS
    desplaz = FORMULAS[c["clave"]][0]
    lo, hi = c["x0"] + min(desplaz) * h, c["x0"] + max(desplaz) * h
    pad = max(0.6 * (hi - lo), 0.5)
    return lo - pad, hi + pad


# ----------------------------------------------------------------------------- integración
def figura_regla(res, k, rango):
    c = res.ctx
    f, df = c["f"], res.df
    xs, ys = df["xᵢ"].to_numpy(), df["f(xᵢ)"].to_numpy()
    gx = _malla(rango)
    fig = E.lienzo("Área aproximada", "Contribución de cada nodo (peso·f(xᵢ))")
    E.curva(fig, gx, f(gx))
    i_k = k - 1
    if c["regla"] == "trapecio":
        for i in range(len(xs) - 1):
            activo = i == i_k - 1 or (i_k == 0 and i == 0)
            fig.add_trace(go.Scatter(x=[xs[i], xs[i], xs[i + 1], xs[i + 1], xs[i]], y=[0, ys[i], ys[i + 1], 0, 0],
                                     fill="toself", mode="lines", line=dict(color=E.AMBAR if activo else E.VIOLETA, width=1),
                                     fillcolor="rgba(251,191,36,0.35)" if activo else "rgba(167,139,250,0.18)",
                                     showlegend=False, hoverinfo="skip"), row=1, col=1)
    else:
        for g in range(0, len(xs) - 1, 3):
            px, py = xs[g:g + 4], ys[g:g + 4]
            coef = np.polyfit(px, py, 3)
            tx = np.linspace(px[0], px[-1], 60)
            ty = np.polyval(coef, tx)
            activo = g <= max(i_k - 1, 0) < g + 3
            fig.add_trace(go.Scatter(x=np.concatenate([[px[0]], tx, [px[-1], px[0]]]), y=np.concatenate([[0], ty, [0, 0]]),
                                     fill="toself", mode="lines", line=dict(color=E.AMBAR if activo else E.VIOLETA, width=1),
                                     fillcolor="rgba(251,191,36,0.35)" if activo else "rgba(167,139,250,0.18)",
                                     showlegend=False, hoverinfo="skip"), row=1, col=1)
    fig.add_trace(go.Scatter(x=xs, y=ys, mode="markers", name="Nodos",
                             marker=dict(color=[E.AMBAR if i == i_k else E.MENTA for i in range(len(xs))], size=9)),
                  row=1, col=1)
    lo, hi = E.rango_y(f(gx))
    fig.update_yaxes(range=[lo, hi], row=1, col=1)
    fig.update_xaxes(range=list(rango), row=1, col=1)
    fig.add_trace(go.Bar(x=df["i"], y=df["peso·f(xᵢ)"], showlegend=False,
                         marker_color=[E.AMBAR if i == i_k else E.GRIS for i in df["i"]]), row=1, col=2)
    fig.update_xaxes(title_text="i", row=1, col=2)
    r = df.iloc[i_k]
    return E.estilizar(fig, f"Nodo i = {i_k}: x = {r['xᵢ']:.6f}, peso {int(r['peso'])}, suma acumulada = {r['suma acumulada']:.6f}")


def rango_integral(res):
    a, b = sorted((res.ctx["a"], res.ctx["b"]))
    pad = 0.08 * (b - a)
    return a - pad, b + pad


def figura_adaptativa(res, k, rango):
    c = res.ctx
    f, df = c["f"], res.df
    gx = _malla(rango, 1200)
    fig = E.lienzo("Subintervalos (los aceptados quedan sombreados)", "Nivel de cada subintervalo aceptado",
                   pesos=(0.6, 0.4))
    E.curva(fig, gx, f(gx))
    hechos = df.iloc[:k]
    aceptados = hechos[hechos["decisión"] != "divide"]
    for _, r in aceptados.iterrows():
        tx = np.linspace(r["a"], r["b"], 40)
        fig.add_trace(go.Scatter(x=np.concatenate([[r["a"]], tx, [r["b"], r["a"]]]), y=np.concatenate([[0], f(tx), [0, 0]]),
                                 fill="toself", mode="lines", line=dict(color=E.VIOLETA, width=1),
                                 fillcolor="rgba(167,139,250,0.22)", showlegend=False, hoverinfo="skip"), row=1, col=1)
    r = df.iloc[k - 1]
    lo, hi = E.rango_y(f(gx))
    color = E.MENTA if r["decisión"] != "divide" else E.CORAL
    fig.add_trace(go.Scatter(x=[r["a"], r["a"], r["b"], r["b"], r["a"]], y=[lo, hi, hi, lo, lo], mode="lines",
                             name=f"Paso {k}: {r['decisión']}", line=dict(color=E.AMBAR, width=2)), row=1, col=1)
    fig.add_vline(x=(r["a"] + r["b"]) / 2, line=dict(color=color, dash="dot"), row=1, col=1)
    fig.update_yaxes(range=[lo, hi], row=1, col=1)
    fig.update_xaxes(range=list(rango), row=1, col=1)
    todos = df[df["decisión"] != "divide"]
    fig.add_trace(go.Bar(x=(todos["a"] + todos["b"]) / 2, y=todos["nivel"], width=(todos["b"] - todos["a"]) * 0.95,
                         marker_color=[E.AMBAR if p == k else E.GRIS for p in todos["paso"]], showlegend=False),
                  row=1, col=2)
    fig.update_xaxes(title_text="x", row=1, col=2)
    fig.update_yaxes(title_text="nivel", row=1, col=2)
    return E.estilizar(fig, f"Paso {k}: [{r['a']:.6g}, {r['b']:.6g}], |diferencia| = {r['|diferencia|']:.3e} → {r['decisión']}")


def figura_doble(res, k, rango=None):
    c = res.ctx
    df = res.df
    fig = E.lienzo("Región y nodos (color = peso wᵢ·wⱼ)", "Integrales interiores Jᵢ")
    a, b = c["a"], c["b"]
    gx = np.linspace(a, b, 300)
    cy, dy = c["c"](gx), c["d"](gx)
    fig.add_trace(go.Scatter(x=np.concatenate([gx, gx[::-1]]), y=np.concatenate([cy, dy[::-1]]), fill="toself",
                             mode="lines", line=dict(color=E.CIAN, width=1.5), fillcolor="rgba(56,189,248,0.10)",
                             name="Región"), row=1, col=1)
    px, py, pw = [], [], []
    for i, det in enumerate(c["detalle"]):
        for y, w in zip(det["ys"], det["w"]):
            px.append(df["xᵢ"].iloc[i])
            py.append(y)
            pw.append(df["peso"].iloc[i] * w)
    fig.add_trace(go.Scatter(x=px, y=py, mode="markers", name="Nodos (xᵢ, yᵢⱼ)",
                             marker=dict(color=pw, colorscale="Viridis", size=8, showscale=False)), row=1, col=1)
    det = c["detalle"][k - 1]
    xk = df["xᵢ"].iloc[k - 1]
    fig.add_trace(go.Scatter(x=[xk] * len(det["ys"]), y=det["ys"], mode="lines+markers", name=f"x{k - 1} (integral interior)",
                             line=dict(color=E.AMBAR, width=3), marker=dict(size=11, color=E.AMBAR)), row=1, col=1)
    fig.update_xaxes(title_text="x", row=1, col=1)
    fig.update_yaxes(title_text="y", row=1, col=1)
    fig.add_trace(go.Bar(x=df["xᵢ"], y=df["Jᵢ"], showlegend=False,
                         marker_color=[E.AMBAR if i == k - 1 else E.GRIS for i in df["i"]]), row=1, col=2)
    fig.update_xaxes(title_text="xᵢ", row=1, col=2)
    r = df.iloc[k - 1]
    return E.estilizar(fig, f"Nodo i = {k - 1}: x = {r['xᵢ']:.6f}, J = {r['Jᵢ']:.8f}, peso {int(r['peso'])}")


FIGURAS_DIRECTAS = {
    "punto_flotante": figura_punto_flotante,
    "neville": figura_neville,
    "hermite": figura_hermite,
    "derivada_2p": figura_derivada,
    "derivada_5p": figura_derivada,
    "trapecio": figura_regla,
    "simpson38": figura_regla,
    "adaptativa": figura_adaptativa,
    "doble_trapecio": figura_doble,
    "doble_simpson38": figura_doble,
}


def rango_directo(res):
    if res.id in ("neville", "hermite"):
        return _rango_nodos(res.ctx["xs"], [res.ctx.get("x")])
    if res.id.startswith("derivada"):
        return rango_derivada(res)
    if res.id in ("trapecio", "simpson38", "adaptativa", "doble_trapecio", "doble_simpson38"):
        return rango_integral(res)
    return -5.0, 5.0
