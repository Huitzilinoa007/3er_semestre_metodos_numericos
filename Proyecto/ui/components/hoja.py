# Hoja de desarrollo: el procedimiento se "escribe" en vivo (texto palabra por palabra y ecuaciones por términos).
# Aquí se anima con pausas cortas entre fragmentos porque Streamlit no tiene un efecto de máquina de escribir propio.
from __future__ import annotations

import re
import time

import streamlit as st

from core.escritura import prefijos_latex
from ui.compat import contenedor

# (pausa por palabra, pausa por fragmento de ecuación) en segundos.
RETARDOS = {"Lenta": (0.06, 0.28), "Normal": (0.03, 0.13), "Rápida": (0.012, 0.05)}
# Los títulos van con #### y los subtítulos con ##### para que el CSS los distinga con colores y tamaños distintos.
_PREFIJO_TITULO = {"titulo": "#### ", "subtitulo": "##### "}


def _palabras(texto: str, pausa: float):
    # Se entrega una palabra a la vez (con su espacio) para que st.write_stream las vaya escribiendo.
    for token in re.findall(r"\S+\s*", texto):
        yield token
        time.sleep(pausa)


def escribir_hoja(bloques, velocidad: str = "Sin animación") -> None:
    """Dibuja los bloques en la hoja. Con velocidad "Sin animación" aparecen completos al instante."""
    animar = velocidad in RETARDOS
    p_texto, p_tex = RETARDOS.get(velocidad, (0.0, 0.0))
    with contenedor("hoja"):
        for tipo, contenido in bloques:
            if tipo in _PREFIJO_TITULO:
                md = _PREFIJO_TITULO[tipo] + contenido
                if animar:
                    st.write_stream(_palabras(md, p_texto))   # write_stream escribe el texto a medida que llega.
                else:
                    st.markdown(md)
            elif tipo == "texto":
                if animar:
                    st.write_stream(_palabras(contenido, p_texto))
                else:
                    st.markdown(contenido)
            elif tipo == "latex":
                if animar:
                    # Aquí se usa un espacio vacío (st.empty) que se va reemplazando: cada vuelta muestra un poco más de la ecuación.
                    lugar = st.empty()
                    for prefijo in prefijos_latex(contenido):
                        lugar.latex(prefijo)
                        time.sleep(p_tex)
                else:
                    st.latex(contenido)
            if animar:
                time.sleep(p_texto * 3)   # Una pausita entre bloques para que se note dónde termina cada uno.
