# Vista para los métodos que todavía no tienen lógica: avisa que están en desarrollo y dice dónde agregarlos.
from __future__ import annotations

import streamlit as st

from ui.components.seccion import titulo_pagina


def proximamente(categoria: str, nombre: str) -> None:
    # Se reutiliza el mismo encabezado de los demás métodos para que la página no se vea "rota" aunque esté vacía.
    titulo_pagina(f"Módulo activo: {categoria} ➔ {nombre}", nombre, "Este método todavía no está implementado.")
    # Un aviso (no un error) porque no es una falla: el método simplemente todavía no se programa.
    st.warning(
        f"El método de **{nombre}** está en desarrollo. Ya tienes la estructura lista para agregarlo: "
        "su lógica va en `core/metodos/`, su ejecutor en `core/ejecutores.py` y su entrada en `registry.py` "
        "(los pasos completos están en el README)."
    )
