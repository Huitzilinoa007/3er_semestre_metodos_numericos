# Corta una ecuación LaTeX en pedacitos válidos para poder "escribirla" poco a poco en pantalla.
# Aquí no se corta en cualquier lugar porque un `\frac{1}{` sin cerrar haría que KaTeX (el que dibuja LaTeX) muestre un error rojo.
from __future__ import annotations

# Comandos después de los cuales es seguro hacer un corte (no dejan nada abierto).
_CORTE_COMANDOS = {"cdot", "approx", "Rightarrow", "le", "ge", "quad", "qquad", "times"}
# Signos después de los cuales también se puede cortar: así la ecuación se ve escribiéndose término por término.
_CORTE_CARACTERES = "=+-,<>"


def prefijos_latex(tex: str) -> list[str]:
    cortes: list[int] = []
    profundidad = 0  # Cuenta las llaves { } abiertas; solo se corta cuando vale 0 (todo cerrado).
    izq_der = 0      # Cuenta los \left ... \right abiertos por la misma razón.
    i, n = 0, len(tex)
    while i < n:
        c = tex[i]
        if c == "\\":
            # Aquí se lee el nombre completo del comando (\frac, \left, ...) para saber qué es y no cortarlo a la mitad.
            j = i + 1
            while j < n and tex[j].isalpha():
                j += 1
            comando = tex[i + 1:j]
            if j == i + 1:  # Comandos de un solo símbolo, como \, o \; o \{
                j = i + 2
            if comando == "left":
                izq_der += 1
            elif comando == "right":
                izq_der -= 1
            if comando in _CORTE_COMANDOS and profundidad == 0 and izq_der == 0:
                cortes.append(j)
            i = j
            continue
        if c == "{":
            profundidad += 1
        elif c == "}":
            profundidad -= 1
        elif c in _CORTE_CARACTERES and profundidad == 0 and izq_der == 0 and i > 0:
            cortes.append(i + 1)
        i += 1

    prefijos, vistos = [], set()
    for corte in sorted(set(cortes)):
        pref = tex[:corte].rstrip()
        # Se evitan prefijos repetidos y el que ya sería la ecuación completa (esa se agrega al final).
        if pref and pref not in vistos and corte < n:
            vistos.add(pref)
            prefijos.append(pref)
    prefijos.append(tex)  # El último fotograma siempre es la ecuación completa.
    return prefijos
