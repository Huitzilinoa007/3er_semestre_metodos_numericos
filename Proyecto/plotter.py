# plotter.py
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def graficar_metodo_cerrado(f, df, rango_x: tuple):
    x_vals = np.linspace(rango_x[0], rango_x[1], 400)
    y_vals = f(x_vals)
    y_min, y_max = float(np.min(y_vals)), float(np.max(y_vals))

    fig = make_subplots(
        rows=1, cols=2, 
        column_widths=[0.65, 0.35],
        subplot_titles=("Búsqueda Geométrica paso a paso", "Convergencia del Error Absoluto")
    )

    frames = []
    for idx, row in df.iterrows():
        it = int(row['iter'])
        err_txt = f"{row['error']:.6f}" if not np.isnan(row['error']) else "N/A (Iter 1)"
        
        # Recortamos el historial hasta la iteración actual para animar también la curva de error
        df_parcial = df.iloc[:idx+1]

        frames.append(go.Frame(
            name=str(it),
            data=[
                # Columna 1: Geometría (Trazos 0, 1, 2, 3)
                go.Scatter(x=x_vals, y=y_vals, mode="lines", name="f(x)", line=dict(color="#3b82f6", width=3)),
                go.Scatter(x=[row['a'], row['a']], y=[y_min, y_max], mode="lines", name="a", line=dict(color="#10b981", dash="dash")),
                go.Scatter(x=[row['b'], row['b']], y=[y_min, y_max], mode="lines", name="b", line=dict(color="#f59e0b", dash="dash")),
                go.Scatter(
                    x=[row['c'], row['c']], y=[0, row['f(c)']], 
                    mode="lines+markers+text", name="Raíz c",
                    text=[f"c = {row['c']:.4f}", ""], textposition="top center",
                    line=dict(color="#ef4444", dash="dot"),
                    marker=dict(size=[12, 8], color="#ef4444")
                ),
                # Columna 2: Curva de error (Trazo 4)
                go.Scatter(
                    x=df_parcial['iter'], y=df_parcial['error'], 
                    mode="lines+markers", name="Error |c_i - c_{i-1}|",
                    line=dict(color="#a855f7", width=2), marker=dict(size=8)
                )
            ],
            traces=[0, 1, 2, 3, 4],
            layout=go.Layout(title_text=f"Iteración {it} | c = {row['c']:.6f} | f(c) = {row['f(c)']:.2e} | Error = {err_txt}")
        ))

    # Añadir estado inicial a los subplots correspondientes
    for trace in frames[0].data[:4]:
        fig.add_trace(trace, row=1, col=1)
    fig.add_trace(frames[0].data[4], row=1, col=2)

    fig.frames = frames
    fig.update_xaxes(range=[rango_x[0], rango_x[1]], zeroline=True, zerolinewidth=2, zerolinecolor="gray", row=1, col=1)
    fig.update_yaxes(range=[y_min, y_max], zeroline=True, zerolinewidth=2, zerolinecolor="gray", row=1, col=1)
    fig.update_xaxes(title_text="Iteración", row=1, col=2)
    fig.update_yaxes(title_text="Error (Escala Log)", type="log", row=1, col=2)

    # plotter.py (Fragmento corregido)
    fig.update_layout(
        height=550,
        title_text=frames[0].layout.title.text,
        title_x=0.5,
        margin=dict(t=80, b=80), # Margen superior e inferior limpio
        updatemenus=[dict(
            type="buttons", 
            showactive=False, 
            x=0.0, 
            y=-0.22, # <-- Ubicado abajo de la gráfica, totalmente libre
            xanchor="left",
            yanchor="top",
            buttons=[
                dict(label="▶ Play", method="animate", args=[None, dict(frame=dict(duration=700, redraw=True), fromcurrent=True)]),
                dict(label="⏸ Pausa", method="animate", args=[[None], dict(frame=dict(duration=0, redraw=False), mode="immediate")])
            ]
        )],
        sliders=[dict(
            steps=[dict(method="animate", args=[[f.name], dict(mode="immediate", frame=dict(duration=300, redraw=True))], label=f" {f.name}") for f in frames],
            currentvalue=dict(prefix="Iteración: "),
            y=-0.05
        )]
    )

    return fig