# Inyecta el CSS de la aplicación (colores, tipografías, tarjetas, tabla...).
from __future__ import annotations

import re  # Se usa para quitar las líneas vacías del CSS en el modo de respaldo.
from pathlib import Path  # Path arma la ruta al archivo styles.css sin importar desde dónde se ejecute la app.

import streamlit as st

_RUTA_CSS = Path(__file__).with_name("styles.css")  # Siempre busca styles.css junto a este archivo.


def aplicar_tema() -> None:
    css = _RUTA_CSS.read_text(encoding="utf-8")
    try:
        # st.html no interpreta Markdown, así que el CSS llega tal cual.
        st.html(f"<style>{css}</style>")
    except Exception:
        # Respaldo: Markdown corta los bloques HTML en las líneas vacías, por eso se quitan antes.
        compacto = re.sub(r"\n\s*\n", "\n", css)
        st.markdown(f"<style>{compacto}</style>", unsafe_allow_html=True)
