# Tabla de iteraciones en HTML, con animación de llenado celda por celda.
# Aquí se dibuja la tabla con HTML propio (y no con st.dataframe) porque necesitamos pintar celdas sueltas:
# ámbar = la celda que se está calculando, azul = las celdas que se usan para calcularla.
# La animación NO sabe nada de los métodos: solo recorre el plan de `core/tabla_pasos.py`.
from __future__ import annotations

import html
import re
import time  # time.sleep hace una pausa entre cuadro y cuadro para que la animación se pueda seguir con la vista.

import numpy as np
import pandas as pd
import streamlit as st

from core.ejecutores import Resultado, indice_convergencia
from core.formato import txt_num
from core.tabla_pasos import calendario, plan_llenado
from ui.compat import pintar_html

# Mientras se anima, solo se ven las últimas filas para que la tabla no crezca sin fin y siempre se vea lo nuevo.
VENTANA = 12
# (pausa por celda, pausa por fila rápida) en segundos, según la velocidad elegida.
RETARDOS = {"Lenta": (0.35, 0.15), "Normal": (0.18, 0.08), "Rápida": (0.08, 0.03)}
ENTEROS = ("iter", "grado", "iteraciones", "i", "k", "paso", "nivel", "peso", "bit")
# Tabla de traducción para escribir subíndices bonitos: x_0 -> x₀, x_n+1 -> xₙ₊₁.
_SUBINDICES = str.maketrans("0123456789n+-", "₀₁₂₃₄₅₆₇₈₉ₙ₊₋")

LEYENDA = (
    '<div class="leyenda">'
    '<span><i class="chip chip-activa"></i>Celda que se calcula</span>'
    '<span><i class="chip chip-fuente"></i>Celdas que se usan para calcularla</span>'
    '<span><i class="chip chip-final"></i>Iteración donde se alcanza la tolerancia</span>'
    "</div>"
)


def etiqueta_columna(nombre) -> str:
    # Aquí se usa una expresión regular para cambiar "_0" por subíndice y que los encabezados se lean como en el papel.
    return re.sub(r"_([0-9n+\-]+)", lambda m: m.group(1).translate(_SUBINDICES), str(nombre))


def celda_texto(valor, col: str, d: int) -> str:
    """Texto de una celda: enteros sin decimales, errores en científica y el resto con d decimales."""
    if isinstance(valor, (list, tuple)):
        return ", ".join(f"{v:g}" for v in valor)   # Coeficientes de polinomios (deflación).
    if col in ENTEROS:
        return "—" if pd.isna(valor) else str(int(valor))
    if str(col).startswith("error"):
        return "—" if pd.isna(valor) else f"{valor:.3e}"
    if col == "razón":
        return "—" if pd.isna(valor) else f"{valor:.3f}"
    if isinstance(valor, (complex, np.complexfloating)):
        return txt_num(valor, d)
    if isinstance(valor, (float, np.floating)):
        if pd.isna(valor):
            return ""   # Celdas que no existen (por ejemplo, arriba de la diagonal en Neville) se dejan vacías.
        if valor != 0 and (abs(valor) < 10 ** (-d) or abs(valor) >= 1e9):
            return f"{valor:.{max(d - 2, 2)}e}"   # Muy chico o muy grande: en notación científica para no ver 0.000000.
        texto = f"{valor:.{d}f}"
        return texto[1:] if texto.startswith("-") and set(texto[1:]) <= set("0.") else texto
    return str(valor)


def texto_celdas(res: Resultado, d: int) -> list[list[str]]:
    # Se formatea TODA la tabla una sola vez; así cada cuadro de la animación solo elige qué celdas muestra.
    df = res.df
    return [[celda_texto(df.iat[i, j], str(df.columns[j]), d) for j in range(df.shape[1])] for i in range(len(df))]


def construir_html(columnas, matriz, llenas, fuentes, activa, fila_nueva, fila_final, desde, hasta) -> str:
    """HTML de la tabla mostrando las filas [desde, hasta). Cada celda lleva una clase CSS según su papel."""
    cab = "".join(f"<th>{html.escape(etiqueta_columna(c))}</th>" for c in columnas)
    filas = []
    for i in range(desde, hasta):
        celdas = []
        for j in range(len(columnas)):
            # Prioridad: la que se calcula > las que se usan > ya llena > todavía vacía.
            if activa == (i, j):
                clase = "activa"
            elif (i, j) in fuentes:
                clase = "fuente"
            elif llenas[i, j]:
                clase = "lleno"
            else:
                clase = "vacia"
            texto = html.escape(matriz[i][j]) if llenas[i, j] else ""
            celdas.append(f'<td class="{clase}">{texto}</td>')
        clase_fila = "fila-final" if i == fila_final else ("fila-nueva" if i == fila_nueva else "")
        filas.append(f'<tr class="{clase_fila}">' + "".join(celdas) + "</tr>")
    nota = f'<div class="tabla-nota">Se muestran las filas {desde + 1} a {hasta}</div>' if desde > 0 else ""
    return (f'<div class="tabla-wrap"><table class="tabla"><thead><tr>{cab}</tr></thead>'
            f'<tbody>{"".join(filas)}</tbody></table></div>{nota}')


def tabla_iteraciones(res: Resultado, d: int, velocidad: str) -> None:
    """Dibuja la tabla. Con velocidad válida se llena paso a paso; con "Sin animación" aparece completa."""
    columnas = [str(c) for c in res.df.columns]
    n = len(res.df)
    matriz = texto_celdas(res, d)
    fila_final = indice_convergencia(res)
    completas = np.ones((n, len(columnas)), dtype=bool)

    # La tercera muestra de color (iteración de convergencia) solo tiene sentido en los métodos iterativos.
    pintar_html(st, LEYENDA if fila_final is not None else re.sub(r'<span><i class="chip chip-final">.*?</span>', "", LEYENDA))
    lugar_paso = st.empty()    # Aquí se escribe qué celda se está calculando.
    lugar_tabla = st.empty()   # Un solo lugar que se redibuja en cada cuadro (así la tabla "se anima" en su sitio).

    if velocidad not in RETARDOS:
        pintar_html(lugar_tabla, construir_html(columnas, matriz, completas, set(), None, None, fila_final, 0, n))
        return

    pos = {c: j for j, c in enumerate(columnas)}
    plan = plan_llenado(res)
    cuadros = calendario(plan, n)
    llenas = np.zeros((n, len(columnas)), dtype=bool)
    t_celda, t_fila = RETARDOS[velocidad]
    hechos = 0

    for cuadro in cuadros:
        # Ya con este cuadro se marcan como llenas las celdas nuevas (solo las que faltaban, no se recalcula todo).
        for p in plan[hechos:cuadro.hasta]:
            llenas[p.fila, pos[p.columna]] = True
        hechos = cuadro.hasta
        ultima_fila = plan[cuadro.hasta - 1].fila
        desde = max(0, ultima_fila + 1 - VENTANA)

        activa, fuentes = None, set()
        if cuadro.activo is not None:
            p = cuadro.activo
            activa = (p.fila, pos[p.columna])
            fuentes = {(f, pos[c]) for f, c in p.fuentes}   # Aquí están las celdas "usadas" que se resaltan en azul.
            detalle = p.texto or "se llena la celda"
            pintar_html(lugar_paso, f'<p class="paso-texto"><b>Fila {p.fila + 1}</b> — <b>{html.escape(etiqueta_columna(p.columna))}</b>: '
                                    f'{html.escape(detalle)}</p>')
        else:
            pintar_html(lugar_paso, f'<p class="paso-texto">Se llena la fila {cuadro.fila_nueva + 1}…</p>')

        pintar_html(lugar_tabla, construir_html(columnas, matriz, llenas, fuentes, activa, cuadro.fila_nueva,
                                                None, desde, ultima_fila + 1))
        time.sleep(t_fila if cuadro.rapido else t_celda)

    # Al terminar se muestra la tabla completa, con la iteración de convergencia resaltada.
    lugar_paso.empty()
    pintar_html(lugar_tabla, construir_html(columnas, matriz, completas, set(), None, None, fila_final, 0, n))
