# Procedimiento paso a paso (texto + LaTeX) de cada método.
# Devuelve listas de "bloques" (tipo, contenido) con tipo en {"titulo", "subtitulo", "texto", "latex"}.
# Aquí se arma una lista de bloques (y no se dibuja nada) porque así la misma información sirve para la
# animación en pantalla, para mostrarla de golpe y para exportarla a Markdown.
from __future__ import annotations

import sympy as sp

from .ejecutores import Resultado, indice_convergencia
from .formato import tex_num as N   # N = número en LaTeX (se abrevia porque se usa muchísimo en las fórmulas).
from .formato import tex_sub as S   # S = número listo para sustituir (entre paréntesis si es negativo).
from .formato import tex_tol, txt_num, txt_sci
from .parser import X, latex_de

CERRADOS = ("biseccion", "falsa_posicion")


# ----------------------------------------------------------------------------- utilidades
def _sust(expr, valor, d) -> str:
    """LaTeX de `expr` con x sustituida por el valor entre paréntesis: (1.5)^3 - 2(1.5) - 5."""
    # Aquí se sustituye x por un símbolo "disfrazado" con el número porque así SymPy conserva la forma de la fórmula
    # y la muestra con el valor puesto, en lugar de resolverla directamente.
    simbolo = sp.Symbol(rf"{{\left({N(valor, d)}\right)}}")
    return latex_de(expr.subs(X, simbolo))


def _limpio(c, d):
    # Coeficientes casi enteros se muestran como enteros (1 y no 1.000000) para que el polinomio se lea natural.
    return int(round(c)) if abs(c - round(c)) < 1e-9 else round(c, min(d, 4))


def _poli_tex(coefs, d) -> str:
    n = len(coefs) - 1
    expr = sum(_limpio(c, d) * X ** (n - i) for i, c in enumerate(coefs))
    return sp.latex(expr, order="lex")   # order="lex" para que salga de mayor a menor grado.


# ----------------------------------------------------------------------------- planteamiento
def _plan_cerrados(res, d):
    if res.id == "biseccion":
        return [r"c_k = \frac{a_k + b_k}{2}", r"E_k = |c_k - c_{k-1}|"]
    return [r"c_k = b - \frac{f(b)\,(a - b)}{f(a) - f(b)}", r"E_k = |c_k - c_{k-1}|"]


# Cada método tiene: (texto explicativo, función que devuelve sus fórmulas generales en LaTeX).
_PLANTEAMIENTO = {
    "biseccion": (
        "Se busca una raíz de f(x) = 0 en un intervalo [a, b]. Si f es continua y f(a)·f(b) < 0, el teorema de "
        "Bolzano asegura que hay una raíz dentro. En cada iteración se toma el punto medio y se conserva la mitad "
        "del intervalo donde f cambia de signo.",
        _plan_cerrados),
    "falsa_posicion": (
        "Igual que la bisección, pero el nuevo punto no es el punto medio: es donde la recta que une (a, f(a)) y "
        "(b, f(b)) cruza el eje x. Se conserva el subintervalo donde f cambia de signo.",
        _plan_cerrados),
    "newton": (
        "Se reemplaza f por su recta tangente en el punto actual; donde esa tangente cruza el eje x queda la "
        "siguiente aproximación. Necesita f'(x), que se calcula de forma simbólica, y que f'(x) ≠ 0.",
        lambda res, d: [r"x_{k+1} = x_k - \frac{f(x_k)}{f'(x_k)}", rf"f'(x) = {res.ctx['latex_fp']}",
                        r"E_{k+1} = |x_{k+1} - x_k|"]),
    "secante": (
        "Es Newton sin derivada: la tangente se sustituye por la recta (secante) que pasa por los dos últimos "
        "puntos. Necesita dos valores iniciales x₀ y x₁.",
        lambda res, d: [r"x_{k+1} = x_k - \frac{f(x_k)\,(x_k - x_{k-1})}{f(x_k) - f(x_{k-1})}",
                        r"E_{k+1} = |x_{k+1} - x_k|"]),
    "punto_fijo": (
        "La ecuación se escribe como x = g(x) y se itera x_{k+1} = g(x_k). La iteración converge cerca de la "
        "solución si |g'(x)| < 1; el programa verifica esa condición en el punto inicial.",
        lambda res, d: [r"x_{k+1} = g(x_k)", rf"g'(x) = {res.ctx['latex_gp']}", r"E_{k+1} = |x_{k+1} - x_k|"]),
    "aitken": (
        "Se genera la sucesión de punto fijo x_{k+1} = g(x_k) y se acelera su convergencia con la fórmula Δ² de "
        "Aitken, que usa tres términos consecutivos para estimar el límite.",
        lambda res, d: [r"x_{n+1} = g(x_n)",
                        r"\hat{x}_n = x_n - \frac{(x_{n+1} - x_n)^2}{x_{n+2} - 2x_{n+1} + x_n}",
                        r"E_n = |\hat{x}_n - \hat{x}_{n-1}|"]),
    "deflacion": (
        "Para un polinomio P(x) se encuentra una raíz r con Newton-Raphson, se divide P(x) entre (x − r) con "
        "división sintética y se repite el proceso con el polinomio de menor grado hasta agotar las raíces reales.",
        lambda res, d: [r"b_0 = a_0, \qquad b_i = a_i + r\,b_{i-1}", r"P(x) = (x - r)\,Q(x) + R, \qquad R = b_n"]),
    "muller": (
        "Se ajusta una parábola por tres puntos (P₀, f(P₀)), (P₁, f(P₁)), (P₂, f(P₂)) y se toma su cruce con el "
        "eje x más cercano a P₂ como nueva aproximación. Como usa raíces cuadradas, puede hallar raíces complejas.",
        lambda res, d: [r"p(x) = a\,(x - P_2)^2 + b\,(x - P_2) + c, \qquad c = f(P_2)",
                        r"P_3 = P_2 - \frac{2c}{b + \operatorname{sgn}(\operatorname{Re} b)\sqrt{b^2 - 4ac}}",
                        r"E = |P_3 - P_2|"]),
}


# ----------------------------------------------------------------------------- verificación inicial
def _verif_cerrados(res, d):
    expr, r0 = res.ctx["expr"], res.df.iloc[0]
    a, b, fa, fb = res.ctx["a0"], res.ctx["b0"], r0["f(a)"], r0["f(b)"]
    B = [("latex", rf"f(x) = {res.ctx['latex']}"),
         ("texto", f"Intervalo inicial [a, b] = [{txt_num(a, d)}, {txt_num(b, d)}]. Se evalúa f en los extremos:"),
         ("latex", rf"f(a) = {_sust(expr, a, d)} = {N(fa, d)}"),
         ("latex", rf"f(b) = {_sust(expr, b, d)} = {N(fb, d)}")]
    prod = fa * fb
    if prod < 0:
        B += [("latex", rf"f(a)\,f(b) = {S(fa, d)}\cdot{S(fb, d)} = {N(prod, d)} < 0"),
              ("texto", "Como f(a)·f(b) < 0 y f es continua, hay al menos una raíz en [a, b] (teorema de Bolzano).")]
    else:
        B.append(("texto", "Uno de los extremos ya es raíz de f, así que el método termina de inmediato."))
    return B


def _verif_newton(res, d):
    expr, r0 = res.ctx["expr"], res.df.iloc[0]
    x0, fx, fpx = r0["x"], r0["f(x)"], r0["f'(x)"]
    return [("latex", rf"f(x) = {res.ctx['latex']}"),
            ("texto", f"Valor inicial x₀ = {txt_num(x0, d)}."),
            ("latex", rf"f(x_0) = {_sust(expr, x0, d)} = {N(fx, d)}"),
            ("latex", rf"f'(x_0) = {_sust(res.ctx['dexpr'], x0, d)} = {N(fpx, d)}"),
            ("texto", "La derivada en x₀ no es cero, por lo que se puede iniciar." if fpx != 0
             else "x₀ ya es raíz de f.")]


def _verif_secante(res, d):
    expr, r0 = res.ctx["expr"], res.df.iloc[0]
    x0, x1 = r0["x_0"], r0["x_1"]
    return [("latex", rf"f(x) = {res.ctx['latex']}"),
            ("texto", f"Valores iniciales x₀ = {txt_num(x0, d)} y x₁ = {txt_num(x1, d)}."),
            ("latex", rf"f(x_0) = {_sust(expr, x0, d)} = {N(r0['f(x_0)'], d)}"),
            ("latex", rf"f(x_1) = {_sust(expr, x1, d)} = {N(r0['f(x_1)'], d)}")]


def _verif_punto_fijo(res, d):
    x0 = res.ctx["entradas"]["x0"]
    gp0 = res.ctx["gp"](x0)
    return [("latex", rf"g(x) = {res.ctx['latex']}"),
            ("texto", f"Valor inicial x₀ = {txt_num(x0, d)}. Se verifica la condición de convergencia local:"),
            ("latex", rf"|g'(x_0)| = \left|{_sust(res.ctx['dexpr'], x0, d)}\right| = {N(abs(gp0), d)} < 1"),
            ("texto", "Se cumple |g'(x₀)| < 1, así que la iteración debe converger.")]


def _verif_aitken(res, d):
    expr, r0 = res.ctx["expr"], res.df.iloc[0]
    x0, x1, x2 = r0["x_n"], r0["x_n+1"], r0["x_n+2"]
    return [("latex", rf"g(x) = {res.ctx['latex']}"),
            ("texto", f"Con x₀ = {txt_num(x0, d)} se generan los primeros términos de la sucesión de punto fijo:"),
            ("latex", rf"x_1 = g(x_0) = {_sust(expr, x0, d)} = {N(x1, d)}"),
            ("latex", rf"x_2 = g(x_1) = {_sust(expr, x1, d)} = {N(x2, d)}")]


def _verif_deflacion(res, d):
    coefs = res.ctx["coefs"]
    return [("latex", rf"P(x) = {_poli_tex(coefs, d)}"),
            ("texto", f"Es un polinomio de grado {len(coefs) - 1}; se buscarán sus raíces reales una por una "
                      f"empezando desde x₀ = {txt_num(res.ctx['entradas']['x0'], d)}.")]


def _verif_muller(res, d):
    expr, r0 = res.ctx["expr"], res.df.iloc[0]
    B = [("latex", rf"f(x) = {res.ctx['latex']}"),
         ("texto", "Puntos iniciales y sus valores de la función:")]
    for i in range(3):
        p = r0[f"P{i}"]
        B.append(("latex", rf"P_{i} = {N(p, d)}, \qquad f(P_{i}) = {_sust(expr, p, d)} = {N(r0[f'f(P{i})'], d)}"))
    return B


_VERIFICACION = {"biseccion": _verif_cerrados, "falsa_posicion": _verif_cerrados, "newton": _verif_newton,
                 "secante": _verif_secante, "punto_fijo": _verif_punto_fijo, "aitken": _verif_aitken,
                 "deflacion": _verif_deflacion, "muller": _verif_muller}


# ----------------------------------------------------------------------------- detalle de una iteración
def _linea_error(simbolo, k, actual, previo, err, d):
    # Línea estándar del error: |valor nuevo − valor anterior| con los números sustituidos.
    return rf"E_{{{k}}} = |{simbolo}_{{{k}}} - {simbolo}_{{{k - 1}}}| = |{N(actual, d)} - {S(previo, d)}| = {N(err, d)}"


def _it_cerrados(res, k, d):
    r = res.df.iloc[k - 1]   # k empieza en 1 (como lo ve el usuario) y las filas del DataFrame empiezan en 0.
    expr = res.ctx["expr"]
    a, b, c, fa, fb, fc = (r[v] for v in ("a", "b", "c", "f(a)", "f(b)", "f(c)"))
    if res.id == "biseccion":
        L = [rf"c_{{{k}}} = \frac{{a + b}}{{2}} = \frac{{{S(a, d)} + {S(b, d)}}}{{2}} = {N(c, d)}"]
    else:
        L = [rf"c_{{{k}}} = b - \frac{{f(b)\,(a - b)}}{{f(a) - f(b)}} = {S(b, d)} - "
             rf"\frac{{{S(fb, d)}\,({N(a, d)} - {S(b, d)})}}{{{S(fa, d)} - {S(fb, d)}}} = {N(c, d)}"]
    L.append(rf"f(c_{{{k}}}) = {_sust(expr, c, d)} = {N(fc, d)}")
    if abs(fc) < 1e-14:
        L.append(r"f(c) = 0 \;\Rightarrow\; c \text{ es una raíz exacta}")
    else:
        prod = fa * fc
        # Aquí se muestra con qué mitad se queda el método, porque es la decisión clave de cada iteración.
        if prod < 0:
            L.append(rf"f(a)\,f(c) = {S(fa, d)}\cdot{S(fc, d)} = {N(prod, d)} < 0 \;\Rightarrow\; "
                     rf"\text{{nuevo intervalo }} [{N(a, d)},\ {N(c, d)}]")
        else:
            L.append(rf"f(a)\,f(c) = {S(fa, d)}\cdot{S(fc, d)} = {N(prod, d)} > 0 \;\Rightarrow\; "
                     rf"\text{{nuevo intervalo }} [{N(c, d)},\ {N(b, d)}]")
    if k > 1:
        L.append(_linea_error("c", k, c, res.df.iloc[k - 2]["c"], r["error"], d))
    return L


def _it_newton(res, k, d):
    r = res.df.iloc[k - 1]
    x, fx, x1, fpx = r["x"], r["f(x)"], r["x1"], r["f'(x)"]
    expr, dexpr = res.ctx["expr"], res.ctx["dexpr"]
    # Cada iteración de Newton se explica en 4 líneas: evaluar f, evaluar f', aplicar la fórmula y medir el error.
    return [rf"f(x_{{{k - 1}}}) = {_sust(expr, x, d)} = {N(fx, d)}",
            rf"f'(x_{{{k - 1}}}) = {_sust(dexpr, x, d)} = {N(fpx, d)}",
            rf"x_{{{k}}} = {S(x, d)} - \frac{{{S(fx, d)}}}{{{S(fpx, d)}}} = {N(x1, d)}",
            _linea_error("x", k, x1, x, r["error"], d)]


def _it_secante(res, k, d):
    r = res.df.iloc[k - 1]
    x0, x1, x2, f0, f1 = r["x_0"], r["x_1"], r["x_2"], r["f(x_0)"], r["f(x_1)"]
    # Primero los dos valores de f que ya se tienen y luego la fórmula de la secante con los números puestos.
    L = [rf"f(x_{{{k - 1}}}) = {N(f0, d)}, \qquad f(x_{{{k}}}) = {N(f1, d)}",
         rf"x_{{{k + 1}}} = {S(x1, d)} - \frac{{{S(f1, d)}\,({S(x1, d)} - {S(x0, d)})}}"
         rf"{{{S(f1, d)} - {S(f0, d)}}} = {N(x2, d)}"]
    if k > 1:
        L.append(rf"E_{{{k + 1}}} = |x_{{{k + 1}}} - x_{{{k}}}| = |{N(x2, d)} - {S(x1, d)}| = {N(r['error'], d)}")
    return L


def _it_punto_fijo(res, k, d):
    r = res.df.iloc[k - 1]
    x0, x1 = r["x0"], r["x1"]
    # Punto fijo es la iteración más corta: se evalúa g en el punto anterior y se mide cuánto cambió.
    return [rf"x_{{{k}}} = g(x_{{{k - 1}}}) = {_sust(res.ctx['expr'], x0, d)} = {N(x1, d)}",
            _linea_error("x", k, x1, x0, r["error"], d)]


def _it_aitken(res, k, d):
    r = res.df.iloc[k - 1]
    n = k - 1   # En Aitken los términos se numeran desde 0 (x_0, x_1, ...), por eso n = k - 1.
    a, b, c, acel = r["x_n"], r["x_n+1"], r["x_n+2"], r["aitken"]
    L = [rf"\hat{{x}}_{{{n}}} = x_{{{n}}} - \frac{{(x_{{{n + 1}}} - x_{{{n}}})^2}}"
         rf"{{x_{{{n + 2}}} - 2x_{{{n + 1}}} + x_{{{n}}}}}"
         rf" = {S(a, d)} - \frac{{({S(b, d)} - {S(a, d)})^2}}{{{S(c, d)} - 2\cdot{S(b, d)} + {S(a, d)}}} = {N(acel, d)}"]
    if k > 1:
        prev = res.df.iloc[k - 2]["aitken"]
        L.append(rf"E_{{{n}}} = |\hat{{x}}_{{{n}}} - \hat{{x}}_{{{n - 1}}}| = |{N(acel, d)} - {S(prev, d)}| = {N(r['error'], d)}")
    return L


def _it_deflacion(res, k, d):
    r = res.df.iloc[k - 1]
    coefs, nuevos = r["coeficientes"], r["coeficientes_resultantes"]
    raiz = r["raiz"]
    L = [rf"P_{{{int(r['grado'])}}}(x) = {_poli_tex(coefs, d)}",
         rf"\text{{Newton desde }} x_0 = {N(r['x_inicial'], d)}: \quad r_{{{k}}} \approx {N(raiz, d)} "
         rf"\quad ({int(r['iteraciones'])}\ \text{{iteraciones}}, \; E = {N(r['error'], d)})"]
    if len(nuevos):
        L.append(rf"P_{{{int(r['grado'])}}}(x) = (x - {S(raiz, d)})\left({_poli_tex(nuevos, d)}\right) + {N(r['residuo'], d)}")
    else:
        L.append(rf"R = {N(r['residuo'], d)}")
    return L


def _it_muller(res, k, d):
    r = res.df.iloc[k - 1]
    # Müller en 4 líneas: valores de f en los tres puntos, coeficientes de la parábola, nuevo punto P₃ y error.
    return [rf"f(P_0) = {N(r['f(P0)'], d)}, \quad f(P_1) = {N(r['f(P1)'], d)}, \quad f(P_2) = {N(r['f(P2)'], d)}",
            rf"a = {N(r['a'], d)}, \quad b = {N(r['b'], d)}, \quad c = f(P_2) = {N(r['c'], d)}",
            rf"P_3 = P_2 - \frac{{2c}}{{b + \operatorname{{sgn}}(\operatorname{{Re}} b)\sqrt{{b^2 - 4ac}}}} = {N(r['P3'], d)}",
            rf"E = |P_3 - P_2| = |{N(r['P3'], d)} - {S(r['P2'], d)}| = {N(r['error'], d)}"]


_ITERACION = {"biseccion": _it_cerrados, "falsa_posicion": _it_cerrados, "newton": _it_newton,
              "secante": _it_secante, "punto_fijo": _it_punto_fijo, "aitken": _it_aitken,
              "deflacion": _it_deflacion, "muller": _it_muller}


def detalle_iteracion(res: Resultado, k: int, d: int = 6) -> list[str]:
    """Líneas LaTeX que desarrollan la iteración k (empezando en 1) con los valores ya sustituidos."""
    return _ITERACION[res.id](res, k, d)


def etiqueta_paso(res: Resultado, k: int, final: bool = False) -> str:
    nombre = "Etapa" if res.id == "deflacion" else "Iteración"
    if final:
        # La última fila es la que da el resultado si convergió; si no, es simplemente la última que se hizo.
        return f"{nombre} {k} (final: " + ("la que da el resultado)" if res.converged else "la última realizada)")
    return f"{nombre} {k}"


# ----------------------------------------------------------------------------- conclusión
def _residuo(res):
    v = res.valor
    if res.id in ("punto_fijo", "aitken"):
        g = res.ctx["g"]
        return r"|g(x^{*}) - x^{*}|", abs(g(v) - v)
    if res.id == "muller":
        return r"|f(x^{*})|", abs(res.ctx["f_cx"](v))
    return r"f(x^{*})", res.ctx["f"](v)


def _conclusion(res, d, omitidas):
    B = [("titulo", "Criterio de paro y conclusión")]
    if res.id == "deflacion":
        B.append(("texto", "Cada raíz se obtuvo con Newton-Raphson sobre el polinomio reducido. Raíces reales encontradas:"))
        for i, r in enumerate(res.valor, 1):
            B.append(("latex", rf"r_{{{i}}} \approx {N(r, d)}"))
        return B
    B.append(("texto", f"El método se detiene cuando el error entre dos aproximaciones consecutivas es menor o igual "
                       f"que la tolerancia ({txt_sci(res.tol, 0)}), o cuando se agotan las iteraciones permitidas."))
    idx = indice_convergencia(res)
    if res.converged and idx is not None:
        err = res.df["error"].iloc[idx]
        B.append(("texto", f"La tolerancia se alcanza en la iteración {idx + 1}:"))
        B.append(("latex", rf"E_{{{idx + 1}}} = {N(err, d)} \le {tex_tol(res.tol)}"))
    else:
        B.append(("texto", f"Se agotaron las {res.n_max} iteraciones permitidas sin alcanzar la tolerancia. "
                           "Aumenta el máximo de iteraciones, relaja la tolerancia o cambia los valores iniciales."))
        if res.error_final == res.error_final:
            B.append(("latex", rf"E_{{{res.n_iter}}} = {N(res.error_final, d)} > {tex_tol(res.tol)}"))
    etiqueta, valor = _residuo(res)
    B.append(("texto", "Aproximación final y verificación:"))
    B.append(("latex", rf"x^{{*}} \approx {N(res.valor, d)}"))
    B.append(("latex", rf"{etiqueta} = {N(valor, d)}"))
    if omitidas:
        B.append(("texto", "Las iteraciones que no se desarrollaron siguen exactamente el mismo procedimiento; "
                           "puedes revisarlas una por una con el control de iteraciones y con la tabla."))
    return B


# ----------------------------------------------------------------------------- principal
def elegir_iteraciones(res: Resultado, seleccion) -> tuple[list[int], bool]:
    """Devuelve (iteraciones a desarrollar, ¿hay que agregar la final aparte?).

    Se desarrollan las que eligió el usuario (solo las que existen) y SIEMPRE se agrega al final la última,
    que es la que lleva al resultado. Así, aunque haya 40 iteraciones, el procedimiento termina en el resultado.
    """
    n = res.n_filas
    validas = sorted({int(k) for k in (seleccion or []) if 1 <= int(k) <= n})
    return validas, (n not in validas)


def bloques(res: Resultado, d: int = 6, iteraciones=(1, 2, 3)) -> list[tuple[str, str]]:
    texto, formulas = _PLANTEAMIENTO[res.id]
    B: list[tuple[str, str]] = [("titulo", "Planteamiento"), ("texto", texto)]
    B += [("latex", f) for f in formulas(res, d)]
    B.append(("titulo", "Datos y verificación"))
    B += _VERIFICACION[res.id](res, d)

    elegidas, falta_final = elegir_iteraciones(res, iteraciones)
    B.append(("titulo", "Etapas desarrolladas" if res.id == "deflacion" else "Iteraciones desarrolladas"))
    for k in elegidas:
        B.append(("subtitulo", etiqueta_paso(res, k, final=(k == res.n_filas))))
        B += [("latex", linea) for linea in detalle_iteracion(res, k, d)]
    if falta_final:
        # Aquí se avisa que se saltan pasos para que el usuario entienda por qué el número de iteración "da un salto".
        if elegidas and res.n_filas - elegidas[-1] > 1:
            B.append(("texto", "…las iteraciones intermedias se calculan exactamente igual. "
                               "Se muestra ahora la última, que lleva al resultado final:"))
        B.append(("subtitulo", etiqueta_paso(res, res.n_filas, final=True)))
        B += [("latex", linea) for linea in detalle_iteracion(res, res.n_filas, d)]

    omitidas = len(elegidas) + (1 if falta_final else 0) < res.n_filas
    B += _conclusion(res, d, omitidas)
    return B


def a_markdown(res: Resultado, d: int = 6, iteraciones=(1, 2, 3)) -> str:
    """Procedimiento completo en Markdown con LaTeX (para el botón de exportar)."""
    partes = []
    for tipo, contenido in bloques(res, d, iteraciones):
        if tipo == "titulo":
            partes.append(f"\n### {contenido}\n")
        elif tipo == "subtitulo":
            partes.append(f"\n#### {contenido}\n")
        elif tipo == "texto":
            partes.append(contenido + "\n")
        else:
            partes.append(f"$$\n{contenido}\n$$\n")   # $$ ... $$ es como Markdown marca una ecuación en bloque.
    return "\n".join(partes)
