# Encabezado de sección: título grande + una línea de explicación.
# Aquí se hace con HTML propio porque los títulos de Markdown no se distinguen lo suficiente entre sí;
# con esto cada bloque grande de la página (Procedimiento, Tabla, Resultados) se ve claramente separado.
from __future__ import annotations

import html  # html.escape evita que un texto con < o & rompa el HTML.

import streamlit as st

from ui.compat import pintar_html


def seccion(titulo: str, descripcion: str = "", acento: str = "cian") -> None:
    # `acento` (cian, violeta, menta, ambar) pinta la barra lateral del título: cada bloque grande tiene su color
    # y así, al hacer scroll, se distingue de un vistazo en qué parte de la página estás.
    sub = f"<p>{html.escape(descripcion)}</p>" if descripcion else ""
    pintar_html(st, f'<div class="seccion a-{acento}"><h2>{html.escape(titulo)}</h2>{sub}</div>')


def titulo_pagina(ruta: str, nombre: str, resumen: str) -> None:
    # Ruta pequeña arriba (dónde estás), nombre del método en grande y resumen en gris.
    pintar_html(
        st,
        f'<div class="encabezado"><span class="ruta">{html.escape(ruta)}</span>'
        f'<h1>{html.escape(nombre)}</h1><p>{html.escape(resumen)}</p></div>',
    )
