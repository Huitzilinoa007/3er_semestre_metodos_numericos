# Utilidades para que el mismo código funcione en distintas versiones de Streamlit.
# Aquí se concentran porque Streamlit ha ido renombrando parámetros y así el resto del código no se ensucia con try/except.
from __future__ import annotations

import streamlit as st  # streamlit es la librería que dibuja la página web a partir de código Python.


def contenedor(key: str | None = None, borde: bool = True):
    """`st.container` con borde y `key` (la key genera la clase CSS `st-key-<key>` para poder darle estilo)."""
    try:
        return st.container(border=borde, key=key)
    except TypeError:  # Versiones viejas no aceptan `key` en container.
        return st.container(border=borde)


def ancho_completo(funcion, *args, **kwargs):
    """Ejecuta un elemento a todo el ancho: `width="stretch"` o, en versiones previas, `use_container_width`."""
    try:
        return funcion(*args, width="stretch", **kwargs)
    except Exception:  # Aquí se atrapa cualquier error porque cada versión falla de forma distinta con el parámetro nuevo.
        return funcion(*args, use_container_width=True, **kwargs)


def pintar_html(lugar, texto: str) -> None:
    """Dibuja HTML en `st` o en un `st.empty()`. Cae a markdown con HTML si la versión no tiene `.html`."""
    try:
        lugar.html(texto)
    except Exception:
        lugar.markdown(texto, unsafe_allow_html=True)
