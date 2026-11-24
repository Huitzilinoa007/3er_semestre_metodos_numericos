# Paleta y estilo común de TODAS las gráficas Plotly (tema oscuro).
# Aquí se centralizan los colores porque así, si cambia la paleta de la app, se cambia en un solo lugar.
from __future__ import annotations

import numpy as np
import plotly.graph_objects as go  # graph_objects son las "piezas" de Plotly (líneas, puntos, barras).
from plotly.subplots import make_subplots  # make_subplots permite poner dos gráficas lado a lado en una sola figura.

# Colores (mismos que .streamlit/config.toml y styles.css, para que todo se vea de la misma familia).
SUPERFICIE = "#0F1620"   # Fondo del área de la gráfica.
REJILLA = "#1F2B3B"      # Líneas de cuadrícula, bien discretas.
TEXTO = "#E8EDF4"        # Texto principal.
GRIS = "#93A1B5"         # Ejes y series secundarias.
CIAN = "#38BDF8"         # Curva f(x) y acciones.
MENTA = "#34D399"        # Extremo a (y estados correctos).
VIOLETA = "#A78BFA"      # Extremo b, tangentes, cuerdas y parábolas.
AMBAR = "#FBBF24"        # Lo importante: la raíz y la iteración actual.
CORAL = "#FB7185"        # Errores y avisos.


def rango_y(y) -> tuple[float, float]:
    """Rango vertical robusto: ignora NaN/∞ y recorta asíntotas enormes; siempre incluye el 0."""
    y = np.asarray(y, dtype=float)
    y = y[np.isfinite(y)]   # Funciones como tan(x) o 1/x traen infinitos; se quitan para que no arruinen la escala.
    if y.size == 0:
        return -1.0, 1.0
    lo, hi = float(y.min()), float(y.max())
    if max(abs(lo), abs(hi)) > 1e6:
        # Con valores gigantes (asíntotas) se usan percentiles para que la curva "normal" siga viéndose.
        lo, hi = (float(v) for v in np.percentile(y, [2, 98]))
    lo, hi = min(lo, 0.0), max(hi, 0.0)   # Se incluye el 0 porque ahí está el eje donde cruza la raíz.
    pad = 0.08 * ((hi - lo) or 1.0)       # Un 8% de margen para que nada quede pegado al borde.
    return lo - pad, hi + pad


def lienzo(titulo_izq: str, titulo_der: str = "Convergencia del error absoluto", pesos=(0.62, 0.38)):
    # Dos gráficas en una fila: a la izquierda la geometría del método y a la derecha cómo baja el error.
    return make_subplots(rows=1, cols=2, column_widths=list(pesos), subplot_titles=(titulo_izq, titulo_der))


def estilizar(fig, titulo: str | None = None, alto: int = 520, margen_b: int = 90):
    fig.update_layout(
        template="plotly_dark", height=alto,   # plotly_dark ya trae fondo y textos para tema oscuro.
        paper_bgcolor="rgba(0,0,0,0)",         # Transparente para que se vea el fondo de la página.
        plot_bgcolor=SUPERFICIE,
        font=dict(family="DM Sans, sans-serif", color=TEXTO, size=13),
        margin=dict(t=100, b=margen_b, l=55, r=20),
        legend=dict(orientation="h", y=-0.2, x=0),
        hoverlabel=dict(bgcolor="#1A2330", font_color=TEXTO),
    )
    if titulo:
        fig.update_layout(title=dict(text=titulo, x=0, xanchor="left", font=dict(size=14, family="Sora, sans-serif")))
    fig.update_xaxes(gridcolor=REJILLA, zerolinecolor=GRIS, linecolor=GRIS, ticks="outside")
    fig.update_yaxes(gridcolor=REJILLA, zerolinecolor=GRIS, linecolor=GRIS, ticks="outside")
    fig.update_annotations(font=dict(size=13, color=GRIS))   # Estilo de los títulos de cada subgráfica.
    return fig


def curva(fig, xs, ys, nombre="f(x)"):
    # La curva de la función, siempre en cian y gruesa para que sea lo primero que se ve.
    fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", name=nombre, line=dict(color=CIAN, width=3)), row=1, col=1)


def panel_error(fig, df, k, columna="error", nombre="Error |xₖ − xₖ₋₁|", color=GRIS, col=2):
    """Curva de error en escala log; resalta la iteración k. Solo grafica errores > 0 (el log no admite 0)."""
    fig.update_xaxes(title_text="Iteración", row=1, col=col)
    fig.update_yaxes(title_text="Error (escala log)", type="log", row=1, col=col)
    d = df[["iter", columna]]
    d = d[d[columna].notna() & (d[columna] > 0)]
    if d.empty:
        # Si no hay nada que graficar se explica por qué, en lugar de dejar un recuadro vacío que parezca error.
        fig.add_annotation(
            text="Sin errores para graficar<br>(una sola iteración o error exacto 0)",
            xref=f"x{col} domain", yref=f"y{col} domain", x=0.5, y=0.5, showarrow=False,
            font=dict(color=GRIS, size=12))
        return
    # Primero la curva completa, tenue, para ver todo el camino que falta por recorrer.
    fig.add_trace(go.Scatter(x=d["iter"], y=d[columna], mode="lines", opacity=0.35, hoverinfo="skip",
                             line=dict(color=color, width=1.5), showlegend=False), row=1, col=col)
    # Encima, lo que ya pasó hasta la iteración k.
    hasta = d[d["iter"] <= k]
    fig.add_trace(go.Scatter(x=hasta["iter"], y=hasta[columna], mode="lines+markers", name=nombre,
                             line=dict(color=color, width=2), marker=dict(size=7)), row=1, col=col)
    # Y un aro ámbar alrededor de la iteración actual.
    actual = d[d["iter"] == k]
    if not actual.empty:
        fig.add_trace(go.Scatter(x=actual["iter"], y=actual[columna], mode="markers", hoverinfo="skip",
                                 showlegend=False,
                                 marker=dict(color=AMBAR, size=14, symbol="circle-open", line=dict(width=2.5))),
                      row=1, col=col)
