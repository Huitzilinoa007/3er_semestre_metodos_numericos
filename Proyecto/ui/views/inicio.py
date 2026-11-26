# Pantalla de bienvenida (lo primero que se ve al abrir la app).
from __future__ import annotations

import streamlit as st

from ui.components.seccion import seccion, titulo_pagina
from ui.components.vacio import tabla_sintaxis


def inicio() -> None:
    # Encabezado de la bienvenida: mismo componente que usan los métodos, para que todo se vea uniforme.
    titulo_pagina("Inicio", "Métodos numéricos",
                  "Selecciona una categoría y un método en el menú de navegación para comenzar.")
    # Un aviso simple que indica el siguiente paso: elegir un método en el menú de arriba.
    st.info("Usa el menú de navegación para elegir una **Categoría** y un **Método** específico.")

    col1, col2 = st.columns(2)   # Dos columnas para que "qué puedes hacer" y "módulos" queden lado a lado.
    with col1:
        seccion("¿Qué puedes hacer aquí?", acento="violeta")
        st.markdown(
            "* **Seguir el procedimiento paso a paso** en LaTeX, escrito en vivo con tus datos.\n"
            "* **Ver cómo se llena la tabla** celda por celda, con las celdas que se usan resaltadas.\n"
            "* **Visualizar geometrías paso a paso** con animaciones fluidas de Plotly.\n"
            "* **Analizar la convergencia del error** en tiempo real mediante escalas logarítmicas."
        )
    with col2:
        seccion("Módulos disponibles", acento="cian")
        st.markdown(
            "- **Punto flotante:** cómo se guarda un número en IEEE 754 (simple y doble) y su error de redondeo.\n"
            "- **Raíces:** métodos cerrados y abiertos, aceleración de Aitken, deflación polinomial y Müller.\n"
            "- **Interpolación:** Neville y Hermite (Lagrange, diferencias divididas y splines en desarrollo).\n"
            "- **Derivadas:** fórmulas de 2 y 5 puntos (3 puntos y Richardson en desarrollo).\n"
            "- **Integrales:** trapecio, Simpson 3/8, cuadratura adaptativa e integrales dobles "
            "(Simpson 1/3, Romberg y Gauss en desarrollo)."
        )
    # La guía de sintaxis va escondida en un expander porque solo hace falta la primera vez.
    with st.expander("Sintaxis matemática admitida"):
        tabla_sintaxis()
