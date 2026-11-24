# Estado vacío: lo que se ve al abrir un método antes de calcular (hoja en blanco + guía de sintaxis).
from __future__ import annotations

import streamlit as st

from registry import MetodoSpec
from ui.compat import contenedor

# Tabla de sintaxis en Markdown; se usa Markdown porque Streamlit ya lo convierte en tabla sin código extra.
TABLA_SINTAXIS = """
| Operación | Cómo escribirla | Ejemplo |
|---|---|---|
| Potencia | `x^2` o `x**2` | `x^3 - 2x - 5` |
| Multiplicación implícita | `2x`, `3sin(x)`, `x(x+1)` | `2x + 3` |
| Raíz y exponencial | `sqrt(x)`, `exp(x)` | `exp(-x) - x` |
| Trigonométricas | `sin`, `cos`, `tan` (también `sen`) | `sin(x) - x/2` |
| Logaritmos | `log(x)` y `ln(x)` (naturales), `log10(x)` | `ln(x) - 1` |
| Valor absoluto | `abs(x)` | `abs(x) - 2` |
| Constantes | `pi`, `e` | `cos(pi*x)` |
"""


def tabla_sintaxis() -> None:
    # Se separa en su propia función porque la usan tanto la hoja en blanco como la pantalla de inicio.
    st.markdown(TABLA_SINTAXIS)


def estado_vacio(spec: MetodoSpec) -> None:
    # La clave "vacio" le da a este contenedor el mismo aspecto de hoja rayada que tiene el procedimiento.
    with contenedor("vacio"):
        st.markdown("#### Hoja en blanco")
        st.markdown(spec.instruccion)
        st.markdown("Sintaxis matemática admitida:")
        tabla_sintaxis()
