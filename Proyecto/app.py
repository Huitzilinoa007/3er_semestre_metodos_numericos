# Laboratorio Numérico Interactivo: punto de entrada de la app.
# Se ejecuta con:  streamlit run app.py
import re  # Expresiones regulares: se usan para convertir nombres de métodos en direcciones web (slugs).
import unicodedata  # Sirve para quitar acentos al armar esas direcciones (ej. "Bisección" -> "biseccion").

import streamlit as st  # Streamlit convierte este script de Python en una página web interactiva.

# set_page_config DEBE ser la primera instrucción de Streamlit, por eso va antes de importar el resto de la app.
st.set_page_config(page_title="Métodos Numéricos", layout="wide")

from registry import INTERPOLACION, DERIVADAS, INTEGRACION, PROXIMAMENTE, RAICES, metodos_de  # noqa: E402
from ui.theme import aplicar_tema  # noqa: E402
from ui.views.inicio import inicio  # noqa: E402
from ui.views.metodo import renderizar_metodo  # noqa: E402
from ui.views.proximamente import proximamente  # noqa: E402


def _slug(texto: str) -> str:
    # Aquí se quitan acentos y símbolos porque la dirección web de cada página debe ser simple (sin espacios ni tildes).
    ascii_ = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", ascii_.lower()).strip("-")


def _pagina_metodo(spec):
    # Streamlit pide una función sin argumentos por página; esta función interna "recuerda" cuál método es.
    def vista():
        renderizar_metodo(spec)
    vista.__name__ = spec.id
    return st.Page(vista, title=spec.nombre, url_path=spec.id)


def _pagina_proximamente(categoria: str, nombre: str):
    def vista():
        proximamente(categoria, nombre)
    vista.__name__ = _slug(nombre).replace("-", "_")
    return st.Page(vista, title=nombre, url_path=_slug(nombre))


def _construir_navegacion():
    # El diccionario es {sección del menú: [páginas]}; Streamlit lo convierte en un menú agrupado.
    paginas = {"Inicio": [st.Page(inicio, title="Inicio", default=True)],
               RAICES: [_pagina_metodo(m) for m in metodos_de(RAICES)]}
    for categoria in (INTERPOLACION, DERIVADAS, INTEGRACION):
        paginas[categoria] = [_pagina_proximamente(categoria, n) for n in PROXIMAMENTE[categoria]]
    try:
        return st.navigation(paginas, position="top")   # Menú arriba: deja todo el ancho para las gráficas.
    except TypeError:                                   # Versiones sin menú superior caen a la barra lateral.
        return st.navigation(paginas)


aplicar_tema()
_construir_navegacion().run()
