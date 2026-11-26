# Plan de llenado de la tabla: dice EN QUÉ ORDEN se llena cada celda y QUÉ CELDAS SE USAN para calcularla.
# Aquí se separa el "plan" de la pantalla porque así la animación es solo "recorrer el plan",
# y quien agregue un método nuevo solo tiene que describir sus celdas (no tocar la interfaz).
#
# Idea clave: una celda es (fila, nombre_de_columna). Muchos métodos van "en escalerita": lo que sale
# en la última columna de una fila (x1, x_2, P3...) pasa a la primera columna de la fila siguiente.
# Esas dependencias entre filas son justo las "fuentes" que se resaltan en la animación.
from __future__ import annotations

import math
from dataclasses import dataclass

from .ejecutores import Resultado


@dataclass(frozen=True)
class Paso:
    fila: int                                # Fila (iteración) de la celda, empezando en 0.
    columna: str                             # Nombre de la columna en la tabla.
    fuentes: tuple[tuple[int, str], ...]     # Celdas que se usan para calcularla: (fila, columna).
    texto: str                               # Explicación corta de cómo se obtiene (se muestra mientras se llena).


@dataclass(frozen=True)
class Cuadro:
    # Un "cuadro" es una foto de la animación: cuántos pasos del plan ya están llenos y cuál se está calculando.
    hasta: int                  # Cuántos pasos del plan están llenos en este cuadro.
    activo: Paso | None         # Celda que se está calculando (None en las filas rápidas).
    fila_nueva: int | None      # Fila que acaba de aparecer completa (solo en las filas rápidas).
    rapido: bool                # True si el cuadro corresponde a filas rápidas (se espera menos tiempo).


def _r(fuentes, texto):
    # Atajo para escribir las reglas más corto: devuelve (lista de fuentes, texto).
    return (list(fuentes), texto)


# ----------------------------------------------------------------------------- reglas por método
# Cada función recibe la fila i (empezando en 0) y devuelve un diccionario columna -> (fuentes, texto).
# El orden en que se escriben las columnas en `ORDEN` es el orden en que se van llenando.
def _reglas_biseccion(i):
    p = i - 1  # Fila anterior (de ahí vienen los extremos nuevos).
    return {
        "a": _r([(p, "a"), (p, "c"), (p, "f(a)"), (p, "f(c)")], "a: se queda igual, o pasa a ser c si f(a)·f(c) > 0") if i else _r([], "dato inicial: límite a"),
        "b": _r([(p, "b"), (p, "c"), (p, "f(a)"), (p, "f(c)")], "b: se queda igual, o pasa a ser c si f(a)·f(c) < 0") if i else _r([], "dato inicial: límite b"),
        "c": _r([(i, "a"), (i, "b")], "c = (a + b) / 2"),
        "f(a)": _r([(i, "a")], "f(a): se evalúa f en a"),
        "f(b)": _r([(i, "b")], "f(b): se evalúa f en b"),
        "f(c)": _r([(i, "c")], "f(c): se evalúa f en c"),
        "error": _r([(i, "c"), (p, "c")], "error = |c − c anterior|") if i else _r([], "sin error en la primera iteración"),
        "error relativo": _r([(i, "error"), (i, "c")], "error relativo = error / |c|") if i else _r([], "sin error en la primera iteración"),
    }


def _reglas_falsa(i):
    r = _reglas_biseccion(i)
    # Aquí c depende de f(a) y f(b) (no del punto medio), por eso se cambian sus fuentes.
    r["c"] = _r([(i, "a"), (i, "b"), (i, "f(a)"), (i, "f(b)")], "c = b − f(b)·(a − b) / (f(a) − f(b))")
    return r


def _reglas_newton(i):
    p = i - 1
    return {
        "x": _r([(p, "x1")], "x = x1 de la fila anterior (la escalerita)") if i else _r([], "dato inicial: x₀"),
        "f(x)": _r([(i, "x")], "f(x): se evalúa f en x"),
        "f'(x)": _r([(i, "x")], "f'(x): se evalúa la derivada en x"),
        "x1": _r([(i, "x"), (i, "f(x)"), (i, "f'(x)")], "x1 = x − f(x) / f'(x)"),
        "error": _r([(i, "x1"), (i, "x")], "error = |x1 − x|"),
        "error relativo": _r([(i, "error"), (i, "x1")], "error relativo = error / |x1|"),
    }


def _reglas_secante(i):
    p = i - 1
    return {
        "x_0": _r([(p, "x_1")], "x₀ = x₁ de la fila anterior (la escalerita)") if i else _r([], "dato inicial: x₀"),
        "x_1": _r([(p, "x_2")], "x₁ = x₂ de la fila anterior (la escalerita)") if i else _r([], "dato inicial: x₁"),
        "f(x_0)": _r([(i, "x_0")], "f(x₀): se evalúa f en x₀"),
        "f(x_1)": _r([(i, "x_1")], "f(x₁): se evalúa f en x₁"),
        "x_2": _r([(i, "x_0"), (i, "x_1"), (i, "f(x_0)"), (i, "f(x_1)")], "x₂ = x₁ − f(x₁)·(x₁ − x₀) / (f(x₁) − f(x₀))"),
        "f(x_2)": _r([(i, "x_2")], "f(x₂): se evalúa f en x₂"),
        "error": _r([(i, "x_2"), (i, "x_1")], "error = |x₂ − x₁|") if i else _r([], "sin error en la primera iteración"),
        "error relativo": _r([(i, "error"), (i, "x_2")], "error relativo = error / |x₂|") if i else _r([], "sin error en la primera iteración"),
    }


def _reglas_punto_fijo(i):
    p = i - 1
    return {
        "x0": _r([(p, "x1")], "x0 = x1 de la fila anterior (la escalerita)") if i else _r([], "dato inicial: x₀"),
        "x1": _r([(i, "x0")], "x1 = g(x0)"),
        "error": _r([(i, "x1"), (i, "x0")], "error = |x1 − x0|"),
    }


def _reglas_aitken(i):
    p = i - 1
    return {
        "x_n": _r([(p, "x_n+1")], "xₙ = xₙ₊₁ de la fila anterior (la escalerita)") if i else _r([], "dato inicial: x₀"),
        "x_n+1": _r([(p, "x_n+2")], "xₙ₊₁ = xₙ₊₂ de la fila anterior (la escalerita)") if i else _r([(i, "x_n")], "xₙ₊₁ = g(xₙ)"),
        "x_n+2": _r([(i, "x_n+1")], "xₙ₊₂ = g(xₙ₊₁)"),
        "aitken": _r([(i, "x_n"), (i, "x_n+1"), (i, "x_n+2")], "x̂ = xₙ − (xₙ₊₁ − xₙ)² / (xₙ₊₂ − 2xₙ₊₁ + xₙ)"),
        "error": _r([(i, "aitken"), (p, "aitken")], "error = |x̂ − x̂ anterior|") if i else _r([], "sin error en la primera iteración"),
    }


def _reglas_deflacion(i):
    p = i - 1
    return {
        "grado": _r([(p, "grado")], "grado = grado anterior − 1") if i else _r([], "grado del polinomio original"),
        "coeficientes": _r([(p, "coeficientes_resultantes")], "coeficientes = los que salieron de la división anterior (la escalerita)") if i else _r([], "coeficientes del polinomio original"),
        "x_inicial": _r([(p, "raiz")], "x inicial = la raíz de la etapa anterior (la escalerita)") if i else _r([], "dato inicial: x₀"),
        "raiz": _r([(i, "coeficientes"), (i, "x_inicial")], "raíz: se busca con Newton sobre el polinomio actual"),
        "iteraciones": _r([(i, "raiz")], "iteraciones que necesitó Newton"),
        "error": _r([(i, "raiz")], "error final de Newton en esta etapa"),
        "residuo": _r([(i, "coeficientes"), (i, "raiz")], "residuo de la división sintética"),
        "coeficientes_resultantes": _r([(i, "coeficientes"), (i, "raiz")], "división sintética: coeficientes del polinomio reducido"),
    }


def _reglas_muller(i):
    p = i - 1
    seis = [(i, "P0"), (i, "P1"), (i, "P2"), (i, "f(P0)"), (i, "f(P1)"), (i, "f(P2)")]
    return {
        "P0": _r([(p, "P1")], "P₀ = P₁ de la fila anterior (la escalerita)") if i else _r([], "dato inicial: P₀"),
        "P1": _r([(p, "P2")], "P₁ = P₂ de la fila anterior (la escalerita)") if i else _r([], "dato inicial: P₁"),
        "P2": _r([(p, "P3")], "P₂ = P₃ de la fila anterior (la escalerita)") if i else _r([], "dato inicial: P₂"),
        "f(P0)": _r([(i, "P0")], "f(P₀): se evalúa f en P₀"),
        "f(P1)": _r([(i, "P1")], "f(P₁): se evalúa f en P₁"),
        "f(P2)": _r([(i, "P2")], "f(P₂): se evalúa f en P₂"),
        "a": _r(seis, "a: coeficiente cuadrático de la parábola"),
        "b": _r(seis, "b: coeficiente lineal de la parábola"),
        "c": _r([(i, "f(P2)")], "c = f(P₂)"),
        "P3": _r([(i, "P2"), (i, "a"), (i, "b"), (i, "c")], "P₃ = P₂ − 2c / (b ± √(b² − 4ac))"),
        "error": _r([(i, "P3"), (i, "P2")], "error = |P₃ − P₂|"),
    }


# Aquí se registra cada método con (orden de llenado, función de reglas).
# Para un método nuevo basta con agregar una línea; si no aparece aquí, la tabla se llena fila por fila sin resaltar fuentes.
PLANES = {
    "biseccion": (["a", "b", "c", "f(a)", "f(b)", "f(c)", "error", "error relativo"], _reglas_biseccion),
    "falsa_posicion": (["a", "b", "f(a)", "f(b)", "c", "f(c)", "error", "error relativo"], _reglas_falsa),
    "newton": (["x", "f(x)", "f'(x)", "x1", "error", "error relativo"], _reglas_newton),
    "secante": (["x_0", "x_1", "f(x_0)", "f(x_1)", "x_2", "f(x_2)", "error", "error relativo"], _reglas_secante),
    "punto_fijo": (["x0", "x1", "error"], _reglas_punto_fijo),
    "aitken": (["x_n", "x_n+1", "x_n+2", "aitken", "error"], _reglas_aitken),
    "deflacion": (["grado", "coeficientes", "x_inicial", "raiz", "iteraciones", "error", "residuo", "coeficientes_resultantes"], _reglas_deflacion),
    "muller": (["P0", "P1", "P2", "f(P0)", "f(P1)", "f(P2)", "a", "b", "c", "P3", "error"], _reglas_muller),
}


# ----------------------------------------------------------------------------- métodos directos
# Estas reglas reciben también el Resultado (res) porque algunas dependen del contenido de la fila
# (por ejemplo, en punto flotante una fila puede ser de la parte entera o de la fraccionaria).
_QS = [f"Q_{j}" for j in range(30)]


def _reglas_punto_flotante(i, res):
    p = i - 1
    parte = res.df["parte"].iloc[i]
    anterior_igual = i > 0 and res.df["parte"].iloc[p] == parte
    if parte == "entera":
        op = _r([(p, "resultado")], "se divide entre 2 el cociente anterior") if anterior_igual else _r([], "parte entera del número")
        res_ = _r([(i, "operación")], "cociente de la división entre 2")
        bit = _r([(i, "operación")], "bit = residuo de la división (0 o 1)")
    else:
        op = (_r([(p, "resultado"), (p, "bit")], "se multiplica por 2 lo que quedó después del punto")
              if anterior_igual else _r([], "parte fraccionaria del número"))
        res_ = _r([(i, "operación")], "resultado de multiplicar por 2")
        bit = _r([(i, "resultado")], "bit = parte entera del resultado")
    return {"paso": _r([], "número de paso"), "parte": _r([], "parte del número que se convierte"),
            "operación": op, "resultado": res_, "bit": bit}


def _reglas_neville(i, res):
    reglas = {"i": _r([], "índice del nodo"), "xᵢ": _r([], "dato: nodo xᵢ"),
              "x − xᵢ": _r([(i, "xᵢ")], "distancia del punto x al nodo xᵢ"),
              "Q_0": _r([], "Qᵢ,₀ = f(xᵢ) (dato)")}
    for j in range(1, 30):
        if j <= i:
            reglas[f"Q_{j}"] = _r([(i, f"Q_{j - 1}"), (i - 1, f"Q_{j - 1}"), (i, "x − xᵢ"), (i - j, "x − xᵢ")],
                                 f"Q{i},{j} = [(x − x{i - j})·Q{i},{j - 1} − (x − x{i})·Q{i - 1},{j - 1}] / (x{i} − x{i - j})")
        else:
            reglas[f"Q_{j}"] = _r([], "no existe (arriba de la diagonal)")
    return reglas


def _reglas_hermite(i, res):
    reglas = {"i": _r([], "índice"), "zᵢ": _r([], f"zᵢ = x{i // 2} (cada nodo va dos veces)"),
              "Q_0": _r([], f"Qᵢ,₀ = f(x{i // 2}) (dato)")}
    if i == 0:
        reglas["Q_1"] = _r([], "no existe (arriba de la diagonal)")
    elif i % 2 == 1:
        reglas["Q_1"] = _r([], f"nodo repetido: Q{i},1 = f'(x{i // 2}) (dato)")
    else:
        reglas["Q_1"] = _r([(i, "Q_0"), (i - 1, "Q_0"), (i, "zᵢ"), (i - 1, "zᵢ")], f"Q{i},1 = (Q{i},0 − Q{i - 1},0) / (z{i} − z{i - 1})")
    for j in range(2, 30):
        if j <= i:
            reglas[f"Q_{j}"] = _r([(i, f"Q_{j - 1}"), (i - 1, f"Q_{j - 1}"), (i, "zᵢ"), (i - j, "zᵢ")],
                                 f"Q{i},{j} = (Q{i},{j - 1} − Q{i - 1},{j - 1}) / (z{i} − z{i - j})")
        else:
            reglas[f"Q_{j}"] = _r([], "no existe (arriba de la diagonal)")
    return reglas


def _reglas_derivada(i, res):
    p = i - 1
    fcols = [c for c in res.df.columns if str(c).startswith("f(")]
    reglas = {"k": _r([], "número de paso"),
              "h": _r([(p, "h")], "h = h anterior / 2") if i else _r([], "dato: h inicial"),
              "aproximación": _r([(i, "h")] + [(i, c) for c in fcols], "se aplica la fórmula con estos valores"),
              "error real": _r([(i, "aproximación")], "error = |aproximación − f'(x₀) exacta|"),
              "razón": _r([(p, "error real"), (i, "error real")], "razón = error anterior / error actual") if i else _r([], "sin error anterior")}
    for c in fcols:
        reglas[c] = _r([(i, "h")], f"se evalúa {c} con este h")
    return reglas


def _reglas_regla(i, res):
    p = i - 1
    return {"i": _r([], "índice del nodo"),
            "xᵢ": _r([(p, "xᵢ")], "xᵢ = xᵢ₋₁ + h") if i else _r([], "x₀ = a"),
            "f(xᵢ)": _r([(i, "xᵢ")], "se evalúa f en xᵢ"),
            "peso": _r([(i, "i")], "peso de la regla para este nodo"),
            "peso·f(xᵢ)": _r([(i, "peso"), (i, "f(xᵢ)")], "peso × f(xᵢ)"),
            "suma acumulada": _r([(p, "suma acumulada"), (i, "peso·f(xᵢ)")], "suma anterior + peso·f(xᵢ)") if i
            else _r([(i, "peso·f(xᵢ)")], "la suma empieza con el primer término")}


def _reglas_adaptativa(i, res):
    return {"paso": _r([], "número de paso"), "nivel": _r([], "nivel de división del subintervalo"),
            "a": _r([], "extremo izquierdo"), "b": _r([], "extremo derecho"),
            "S(a,b)": _r([(i, "a"), (i, "b")], "Simpson en todo [a, b]"),
            "S(a,m)+S(m,b)": _r([(i, "a"), (i, "b")], "Simpson en cada mitad, sumado"),
            "|diferencia|": _r([(i, "S(a,b)"), (i, "S(a,m)+S(m,b)")], "|S(a,m) + S(m,b) − S(a,b)|"),
            "15·tol": _r([(i, "nivel")], "15 × tolerancia (se parte a la mitad en cada nivel)"),
            "decisión": _r([(i, "|diferencia|"), (i, "15·tol")], "si |diferencia| < 15·tol se acepta; si no, se divide")}


def _reglas_doble(i, res):
    return {"i": _r([], "índice del nodo en x"),
            "xᵢ": _r([(i - 1, "xᵢ")], "xᵢ = xᵢ₋₁ + h") if i else _r([], "x₀ = a"),
            "c(xᵢ)": _r([(i, "xᵢ")], "límite inferior en y: c(xᵢ)"),
            "d(xᵢ)": _r([(i, "xᵢ")], "límite superior en y: d(xᵢ)"),
            "kᵢ": _r([(i, "c(xᵢ)"), (i, "d(xᵢ)")], "kᵢ = (d − c) / m"),
            "Jᵢ": _r([(i, "xᵢ"), (i, "c(xᵢ)"), (i, "kᵢ")], "integral interior en y con la regla elegida"),
            "peso": _r([(i, "i")], "peso de la regla para este nodo en x"),
            "peso·Jᵢ": _r([(i, "peso"), (i, "Jᵢ")], "peso × Jᵢ")}


_ORDEN_DERIV = ["k", "h", "f(x₀−2h)", "f(x₀−h)", "f(x₀)", "f(x₀+h)", "f(x₀+2h)", "f(x₀+3h)", "f(x₀+4h)",
                "aproximación", "error real", "razón"]
_ORDEN_REGLA = ["i", "xᵢ", "f(xᵢ)", "peso", "peso·f(xᵢ)", "suma acumulada"]
_ORDEN_DOBLE = ["i", "xᵢ", "c(xᵢ)", "d(xᵢ)", "kᵢ", "Jᵢ", "peso", "peso·Jᵢ"]
PLANES.update({
    "punto_flotante": (["paso", "parte", "operación", "resultado", "bit"], _reglas_punto_flotante),
    "neville": (["i", "xᵢ", "x − xᵢ"] + _QS, _reglas_neville),
    "hermite": (["i", "zᵢ"] + _QS, _reglas_hermite),
    "derivada_2p": (_ORDEN_DERIV, _reglas_derivada),
    "derivada_5p": (_ORDEN_DERIV, _reglas_derivada),
    "trapecio": (_ORDEN_REGLA, _reglas_regla),
    "simpson38": (_ORDEN_REGLA, _reglas_regla),
    "adaptativa": (["paso", "nivel", "a", "b", "S(a,b)", "S(a,m)+S(m,b)", "|diferencia|", "15·tol", "decisión"],
                   _reglas_adaptativa),
    "doble_trapecio": (_ORDEN_DOBLE, _reglas_doble),
    "doble_simpson38": (_ORDEN_DOBLE, _reglas_doble),
})


def plan_llenado(res: Resultado) -> list[Paso]:
    """Lista de pasos (uno por celda) en el orden en que se van llenando."""
    columnas = list(res.df.columns)
    n = len(res.df)
    pasos: list[Paso] = []

    if res.id not in PLANES:
        # Plan genérico: fila por fila y sin fuentes. Así un método nuevo ya anima su tabla aunque aún no tenga plan propio.
        for i in range(n):
            pasos += [Paso(i, c, (), "") for c in columnas]
        return pasos

    orden, reglas = PLANES[res.id]
    for i in range(n):
        # El número de iteración siempre es lo primero que se escribe en la fila (si la tabla tiene esa columna).
        if "iter" in columnas:
            pasos.append(Paso(i, "iter", (), "número de iteración"))
        # Las reglas nuevas reciben también el resultado (para mirar el contenido de la fila).
        r = reglas(i, res) if reglas.__code__.co_argcount == 2 else reglas(i)
        for col in orden:
            if col not in columnas:
                continue
            fuentes, texto = r[col]
            # Se descartan fuentes inexistentes (fila negativa o columna que no está) para no resaltar celdas que no existen.
            validas = tuple((f, c) for f, c in fuentes if f >= 0 and c in columnas)
            pasos.append(Paso(i, col, validas, texto))
    return pasos


def calendario(plan: list[Paso], n_filas: int, filas_detalladas: int = 3, max_cuadros_rapidos: int = 40) -> list[Cuadro]:
    """Convierte el plan en cuadros de animación.

    Las primeras `filas_detalladas` filas se llenan celda por celda (con sus fuentes resaltadas).
    Las demás aparecen fila por fila, y si son demasiadas se agrupan para que la animación no se haga eterna.
    """
    # Aquí se indexa el plan por fila para saber dónde empieza y termina cada una.
    por_fila: dict[int, list[int]] = {}
    for idx, p in enumerate(plan):
        por_fila.setdefault(p.fila, []).append(idx)

    cuadros: list[Cuadro] = []
    for fila in range(min(filas_detalladas, n_filas)):
        for idx in por_fila[fila]:
            cuadros.append(Cuadro(idx + 1, plan[idx], None, False))

    restantes = list(range(filas_detalladas, n_filas))
    if restantes:
        # Con muchas filas se agrupan en bloques para no pasar de ~40 cuadros rápidos (que la espera no se vuelva larga).
        tam = max(1, math.ceil(len(restantes) / max_cuadros_rapidos))
        for i in range(0, len(restantes), tam):
            bloque = restantes[i:i + tam]
            hasta = por_fila[bloque[-1]][-1] + 1
            cuadros.append(Cuadro(hasta, None, bloque[-1], True))
    return cuadros
