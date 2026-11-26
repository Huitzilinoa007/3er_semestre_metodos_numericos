# Procedimiento paso a paso de los métodos directos (punto flotante, interpolación, derivación e integración).
# Mismo formato que procedimiento.py: listas de bloques (tipo, contenido) con tipo en {"titulo", "subtitulo", "texto", "latex"}.
# Cada método describe 4 cosas: planteamiento, datos, el desarrollo de UNA fila de la tabla y la conclusión.
from __future__ import annotations

import sympy as sp

from .formato import tex_num as N
from .formato import tex_sub as S
from .formato import tex_tol, txt_num, txt_sci
from .parser import X, Y, latex_de


def _sust(expr, valor, d) -> str:
    """LaTeX de expr con x reemplazada por el número entre paréntesis (igual que en procedimiento.py)."""
    simbolo = sp.Symbol(rf"{{\left({N(valor, d)}\right)}}")
    return latex_de(expr.subs(X, simbolo))


def _sust_xy(expr, x, y, d) -> str:
    sx = sp.Symbol(rf"{{\left({N(x, d)}\right)}}")
    sy = sp.Symbol(rf"{{\left({N(y, d)}\right)}}")
    return latex_de(expr.subs({X: sx, Y: sy}))


def _lista_tex(valores, d, maximo=8) -> str:
    partes = [N(v, d) for v in valores[:maximo]]
    if len(valores) > maximo:
        partes.append(r"\ldots")
    return r",\ ".join(partes)


# ============================================================================= PUNTO FLOTANTE
def _plan_pf(res, d):
    c = res.ctx
    return ("Un número en punto flotante IEEE 754 se guarda como signo, exponente (con sesgo) y mantisa. "
            "Primero se pasa el número a binario: la parte entera dividiendo entre 2 (los residuos, leídos de abajo "
            "hacia arriba, son los bits) y la parte fraccionaria multiplicando por 2 (la parte entera de cada producto "
            "es el siguiente bit). Luego se normaliza a la forma 1.m × 2^e y se redondea la mantisa al número de bits "
            "disponible.",
            [r"x = (-1)^{s}\,(1.m)_2 \times 2^{E - \text{sesgo}}",
             rf"\text{{precisión {c['formato']}: }} 1 \text{{ bit de signo}},\ {c['n_exp']} \text{{ de exponente}},\ "
             rf"{c['n_man']} \text{{ de mantisa}},\ \text{{sesgo}} = {c['sesgo']}"])


def _datos_pf(res, d):
    c, rep = res.ctx, res.ctx["rep"]
    return [("texto", f"Número a guardar: {c['entradas']['num'].strip()} en precisión {c['formato']} "
                      f"({1 + c['n_exp'] + c['n_man']} bits)."),
            ("latex", rf"s = {rep.signo} \quad (\text{{el número es {'negativo' if rep.signo else 'positivo o cero'}}})"),
            ("texto", "Se trabaja con el valor absoluto. La tabla muestra primero la parte entera y después la fraccionaria.")]


def _paso_pf(res, k, d):
    r = res.df.iloc[k - 1]
    if r["parte"] == "entera":
        if r["operación"] == "0":
            return [r"\text{La parte entera es } 0 \;\Rightarrow\; (0)_2"]
        num = r["operación"].split(" ")[0]
        return [rf"{num} \div 2 = {r['resultado']} \quad \text{{residuo}} = {int(r['bit'])}"]
    fr = r["operación"].split(" ")[0]
    return [rf"{fr} \times 2 = {r['resultado']} \;\Rightarrow\; \text{{bit}} = {int(r['bit'])}"]


def _agrupar(bits: str, n: int = 4) -> str:
    return r"\,".join(bits[i:i + n] for i in range(0, len(bits), n))


def _conclusion_pf(res, d):
    c, rep = res.ctx, res.ctx["rep"]
    B = [("titulo", "Normalización, redondeo y resultado")]
    if c["cero"]:
        B.append(("texto", "El cero es un caso especial: exponente y mantisa con todos los bits en 0."))
    else:
        frac = c["bits_frac"] + (r"\ldots" if c["resto"] != 0 else "")
        B.append(("texto", "Juntando los bits de la parte entera (de abajo hacia arriba) y los de la fraccionaria:"))
        B.append(("latex", rf"|x| = ({c['bits_enteros']}.{frac or '0'})_2"))
        if rep.subnormal:
            B.append(("texto", "El número es tan pequeño que no se puede normalizar con el exponente mínimo: se guarda "
                               "como subnormal (exponente con todos los bits en 0 y sin el 1 implícito)."))
        else:
            B.append(("texto", f"Se recorre el punto para dejar un solo 1 a la izquierda (normalizar): e = {rep.exponente_real}."))
            B.append(("latex", rf"|x| \approx (1.{_agrupar(format(rep.mantisa, '0' + str(c['n_man']) + 'b'))})_2 "
                               rf"\times 2^{{{rep.exponente_real}}}"))
            B.append(("latex", rf"E = e + \text{{sesgo}} = {rep.exponente_real} + {c['sesgo']} = {rep.exponente_sesgado} "
                               rf"= ({format(rep.exponente_sesgado, '0' + str(c['n_exp']) + 'b')})_2"))
        texto_red = {"exacto": "Los bits que sobran son todos 0: el número se guarda EXACTO, sin error de redondeo.",
                     "hacia abajo": "Los bits que no caben valen menos de la mitad del último bit: se redondea hacia abajo (se cortan).",
                     "hacia arriba": "Los bits que no caben valen más de la mitad del último bit (o justo la mitad con "
                                     "último bit impar): se redondea hacia arriba, sumando 1 al último bit."}
        B.append(("texto", f"Mantisa de {c['n_man']} bits (sin el 1 implícito). {texto_red[rep.redondeo]}"))
    e_bits = rep.bits[1:1 + c["n_exp"]]
    m_bits = rep.bits[1 + c["n_exp"]:]
    B.append(("texto", "Los bits que quedan en memoria (signo | exponente | mantisa) y su forma hexadecimal:"))
    B.append(("latex", rf"\texttt{{{rep.bits[0]}}}\ |\ \texttt{{{e_bits}}}\ |\ \texttt{{{_agrupar(m_bits, 8)}}}"))
    B.append(("latex", rf"\text{{hex}} = \texttt{{0x{rep.hexadecimal}}}"))
    from .metodos.punto_flotante import decimal_exacto
    B.append(("texto", "Valor que realmente queda guardado y error de redondeo:"))
    B.append(("latex", rf"fl(x) = {decimal_exacto(rep.guardado)}"))
    B.append(("latex", rf"|x - fl(x)| = {N(float(c['err_abs']), d)}, \qquad "
                       rf"\frac{{|x - fl(x)|}}{{|x|}} = {N(float(c['err_rel']), d)} \le \frac{{\varepsilon}}{{2}} = {N(c['u'], d)}"))
    return B


# ============================================================================= NEVILLE
def _plan_neville(res, d):
    return ("Neville evalúa el polinomio interpolante en un punto x sin calcular sus coeficientes. Qᵢ,ⱼ es el valor "
            "en x del polinomio de grado j que pasa por los nodos xᵢ₋ⱼ, …, xᵢ. Cada celda se obtiene de dos celdas "
            "de la columna anterior, así que la tabla se llena en forma de escalera.",
            [r"Q_{i,0} = f(x_i)",
             r"Q_{i,j} = \frac{(x - x_{i-j})\,Q_{i,j-1} - (x - x_i)\,Q_{i-1,j-1}}{x_i - x_{i-j}}",
             r"P(x) = Q_{n,n}"])


def _datos_interp(res, d, con_derivada=False):
    c = res.ctx
    B = []
    if c.get("latex"):
        B.append(("texto", "Los valores se calcularon con la función que escribiste:"))
        B.append(("latex", rf"f(x) = {c['latex']}"))
    B.append(("texto", f"Nodos ({len(c['xs'])}):"))
    for i, xi in enumerate(c["xs"]):
        linea = rf"x_{{{i}}} = {N(xi, d)}, \qquad f(x_{{{i}}}) = {N(c['ys'][i], d)}"
        if con_derivada:
            linea += rf", \qquad f'(x_{{{i}}}) = {N(c['dys'][i], d)}"
        B.append(("latex", linea))
    if c.get("x") is not None:
        B.append(("texto", f"Punto donde se evalúa: x = {txt_num(c['x'], d)}."))
    return B


def _paso_neville(res, k, d):
    c = res.ctx
    i, xs, Q, x = k - 1, c["xs"], c["Q"], c["x"]
    L = [rf"Q_{{{i},0}} = f(x_{{{i}}}) = {N(Q[i, 0], d)}"]
    for j in range(1, i + 1):
        L.append(rf"Q_{{{i},{j}}} = \frac{{({N(x, d)} - {S(xs[i - j], d)})\,{S(Q[i, j - 1], d)} - "
                 rf"({N(x, d)} - {S(xs[i], d)})\,{S(Q[i - 1, j - 1], d)}}}{{{N(xs[i], d)} - {S(xs[i - j], d)}}} = {N(Q[i, j], d)}")
    return L


def _conclusion_neville(res, d):
    c = res.ctx
    n = len(c["xs"]) - 1
    B = [("titulo", "Resultado"),
         ("latex", rf"P({N(c['x'], d)}) = Q_{{{n},{n}}} = {N(res.valor, d)}")]
    if n >= 1:
        B.append(("texto", "Estimación del error: lo que cambió el valor al agregar el último nodo."))
        B.append(("latex", rf"|Q_{{{n},{n}}} - Q_{{{n - 1},{n - 1}}}| = {N(c['estimado'], d)}"))
    if c.get("f") is not None:
        B.append(("texto", "Como diste f(x), también se puede medir el error real:"))
        B.append(("latex", rf"|f({N(c['x'], d)}) - P({N(c['x'], d)})| = {N(c['real'], d)}"))
    return B


# ============================================================================= HERMITE
def _plan_hermite(res, d):
    return ("El polinomio de Hermite pasa por los puntos y además tiene la pendiente f'(xᵢ) en cada uno; con n+1 nodos "
            "es de grado 2n+1. Se usan diferencias divididas con cada nodo repetido dos veces (z₂ᵢ = z₂ᵢ₊₁ = xᵢ); donde "
            "la diferencia dividida sería 0/0 se pone la derivada.",
            [r"z_{2i} = z_{2i+1} = x_i, \qquad Q_{2i,0} = Q_{2i+1,0} = f(x_i)",
             r"Q_{2i+1,1} = f'(x_i), \qquad Q_{2i,1} = \frac{Q_{2i,0} - Q_{2i-1,0}}{z_{2i} - z_{2i-1}}",
             r"Q_{i,j} = \frac{Q_{i,j-1} - Q_{i-1,j-1}}{z_i - z_{i-j}}",
             r"H(x) = Q_{0,0} + \sum_{k=1}^{2n+1} Q_{k,k}\,(x - z_0)(x - z_1)\cdots(x - z_{k-1})"])


def _paso_hermite(res, k, d):
    c = res.ctx
    i, z, Q = k - 1, c["z"], c["Q"]
    L = [rf"z_{{{i}}} = x_{{{i // 2}}} = {N(z[i], d)}, \qquad Q_{{{i},0}} = f(x_{{{i // 2}}}) = {N(Q[i, 0], d)}"]
    if i >= 1:
        if i % 2 == 1:
            L.append(rf"Q_{{{i},1}} = f'(x_{{{i // 2}}}) = {N(Q[i, 1], d)} \quad (\text{{nodo repetido}})")
        else:
            L.append(rf"Q_{{{i},1}} = \frac{{{N(Q[i, 0], d)} - {S(Q[i - 1, 0], d)}}}{{{N(z[i], d)} - {S(z[i - 1], d)}}} = {N(Q[i, 1], d)}")
    for j in range(2, i + 1):
        L.append(rf"Q_{{{i},{j}}} = \frac{{{N(Q[i, j - 1], d)} - {S(Q[i - 1, j - 1], d)}}}"
                 rf"{{{N(z[i], d)} - {S(z[i - j], d)}}} = {N(Q[i, j], d)}")
    return L


def _forma_newton(z, Q, d) -> str:
    terminos = [N(Q[0, 0], d)]
    factores = ""
    for k in range(1, len(z)):
        factores += rf"(x - {S(z[k - 1], d)})"
        coef = Q[k, k]
        signo = "-" if coef < 0 else "+"
        terminos.append(rf"{signo} {N(abs(coef), d)}\,{factores}")
    return " ".join(terminos)


def _conclusion_hermite(res, d):
    c = res.ctx
    B = [("titulo", "Polinomio y resultado"),
         ("texto", "Los coeficientes son la diagonal de la tabla (Q₀₀, Q₁₁, Q₂₂, …). En forma de Newton:"),
         ("latex", rf"H(x) = {_forma_newton(c['z'], c['Q'], min(d, 6))}"),
         ("texto", "Desarrollando los productos:"),
         ("latex", rf"H(x) = {latex_de(sp.N(c['H_exp'], min(d, 6) + 1))}")]
    if c.get("x") is not None:
        B.append(("latex", rf"H({N(c['x'], d)}) = {N(res.valor, d)}"))
        if c.get("f") is not None:
            B.append(("latex", rf"|f({N(c['x'], d)}) - H({N(c['x'], d)})| = {N(c['real'], d)}"))
    return B


# ============================================================================= DERIVACIÓN
_FORMULA_DERIV = {
    "2_adelante": (r"f'(x_0) \approx \frac{f(x_0 + h) - f(x_0)}{h}", r"\text{error} = -\frac{h}{2} f''(\xi)"),
    "2_atras": (r"f'(x_0) \approx \frac{f(x_0) - f(x_0 - h)}{h}", r"\text{error} = \frac{h}{2} f''(\xi)"),
    "5_centrada": (r"f'(x_0) \approx \frac{f(x_0 - 2h) - 8f(x_0 - h) + 8f(x_0 + h) - f(x_0 + 2h)}{12h}",
                   r"\text{error} = \frac{h^4}{30} f^{(5)}(\xi)"),
    "5_extremo": (r"f'(x_0) \approx \frac{-25f(x_0) + 48f(x_0 + h) - 36f(x_0 + 2h) + 16f(x_0 + 3h) - 3f(x_0 + 4h)}{12h}",
                  r"\text{error} = \frac{h^4}{5} f^{(5)}(\xi)"),
}
_TEXTO_DERIV = {
    "2_adelante": "La fórmula de 2 puntos aproxima la derivada con la pendiente de la recta secante entre x₀ y x₀ + h "
                  "(hacia adelante). Su error es proporcional a h: O(h).",
    "2_atras": "La fórmula de 2 puntos hacia atrás usa la secante entre x₀ − h y x₀. Su error es proporcional a h: O(h).",
    "5_centrada": "La fórmula de 5 puntos centrada (punto medio) usa f en x₀ ± h y x₀ ± 2h. Su error es O(h⁴): "
                  "al partir h a la mitad, el error baja unas 16 veces.",
    "5_extremo": "La fórmula de 5 puntos de punto extremo usa x₀, x₀ + h, …, x₀ + 4h (sirve en el borde de una tabla; "
                 "con h < 0 mira hacia atrás). Su error es O(h⁴).",
}


def _plan_deriv(res, d):
    clave = res.ctx["clave"]
    texto = _TEXTO_DERIV[clave] + " Para ver ese orden, la fórmula se aplica con h, h/2, h/4, … y se compara con la derivada exacta."
    return texto, list(_FORMULA_DERIV[clave])


def _datos_deriv(res, d):
    c = res.ctx
    hs = [c["h"] / 2 ** i for i in range(len(res.df))]
    return [("latex", rf"f(x) = {c['latex']}"),
            ("texto", "La derivada exacta (simbólica) solo se usa para medir el error real:"),
            ("latex", rf"f'(x) = {c['latex_d']} \;\Rightarrow\; f'({N(c['x0'], d)}) = {N(c['exacta'], d) if c['exacta'] is not None else r'\text{no definida}'}"),
            ("texto", f"Punto x₀ = {txt_num(c['x0'], d)}. Valores de h que se usan:"),
            ("latex", rf"h = {_lista_tex(hs, d)}")]


def _paso_deriv(res, k, d):
    from .metodos.derivacion import FORMULAS
    c = res.ctx
    r = res.df.iloc[k - 1]
    h = r["h"]
    desplaz, coefs, divisor, _ = FORMULAS[c["clave"]]
    L = [rf"h = {N(h, d)}"]
    columnas = [col for col in res.df.columns if col.startswith("f(")]
    for s, col in zip(desplaz, columnas):
        xs = c["x0"] + s * h
        L.append(rf"{_nombre_tex(s)} = f({N(xs, d)}) = {_sust(c['expr'], xs, d)} = {N(r[col], d)}")
    partes = []
    for i, (cf, col) in enumerate(zip(coefs, columnas)):
        signo = ("-" if cf < 0 else "") if i == 0 else (" - " if cf < 0 else " + ")
        magnitud = "" if abs(cf) == 1 else rf"{abs(cf)}\cdot "
        partes.append(signo + magnitud + S(r[col], d))
    numerador = "".join(partes)
    denom = f"{divisor}" + r"\cdot " + S(h, d) if divisor != 1 else S(h, d)
    L.append(rf"f'(x_0) \approx \frac{{{numerador}}}{{{denom}}} = {N(r['aproximación'], d)}")
    if "error real" in res.df.columns:
        L.append(rf"\text{{error real}} = |{N(r['aproximación'], d)} - {S(c['exacta'], d)}| = {N(r['error real'], d)}")
        if r["razón"] == r["razón"]:
            L.append(rf"\frac{{\text{{error anterior}}}}{{\text{{error actual}}}} = {N(r['razón'], 3)} \quad "
                     rf"(\text{{teórico: }} 2^{{{c['orden']}}} = {2 ** c['orden']})")
    return L


def _nombre_tex(s):
    if s == 0:
        return "f(x_0)"
    signo = "+" if s > 0 else "-"
    mult = "" if abs(s) == 1 else str(abs(s))
    return f"f(x_0 {signo} {mult}h)"


def _conclusion_deriv(res, d):
    c = res.ctx
    h_fin = res.df["h"].iloc[-1]
    B = [("titulo", "Resultado y análisis del error"),
         ("latex", rf"f'({N(c['x0'], d)}) \approx {N(res.valor, d)} \quad (h = {N(h_fin, d)})")]
    if c["exacta"] is not None:
        B.append(("latex", rf"\text{{error real}} = {N(abs(res.valor - c['exacta']), d)}"))
        razones = res.df["razón"].dropna()
        if len(razones):
            B.append(("texto", f"Cada vez que h se divide entre 2, el error se divide aproximadamente entre "
                               f"{razones.iloc[-1]:.2f}; la teoría dice {2 ** c['orden']} para una fórmula O(h"
                               f"{'⁴' if c['orden'] == 4 else ''}). Si h es demasiado pequeño, el redondeo de la "
                               "computadora empieza a dominar y la razón deja de cumplirse."))
    if c["cota"] == c["cota"]:
        orden_d = "f''" if c["orden_deriv"] == 2 else "f^{(5)}"
        B.append(("texto", "Cota teórica del error con el último h (máximo de la derivada en los puntos usados):"))
        B.append(("latex", rf"|\text{{error}}| \le {N(c['constante'], 4)}\,|h|^{{{c['orden']}}} \max|{orden_d}| = {N(c['cota'], d)}"))
    return B


# ============================================================================= TRAPECIO Y SIMPSON 3/8
def _plan_regla(res, d):
    if res.ctx["regla"] == "trapecio":
        return ("La regla del trapecio compuesta parte [a, b] en n subintervalos de ancho h y en cada uno reemplaza f por "
                "la recta que une sus extremos. Los extremos a y b pesan 1 y los nodos interiores pesan 2 (cada uno es "
                "lado de dos trapecios).",
                [r"h = \frac{b - a}{n}, \qquad x_i = a + i\,h",
                 r"\int_a^b f(x)\,dx \approx \frac{h}{2}\left[f(x_0) + 2\sum_{i=1}^{n-1} f(x_i) + f(x_n)\right]",
                 r"\text{error} = -\frac{(b - a)\,h^2}{12} f''(\mu)"])
    return ("La regla de Simpson 3/8 compuesta agrupa los subintervalos de 3 en 3 (n debe ser múltiplo de 3) y en cada "
            "grupo reemplaza f por la cúbica que pasa por sus 4 nodos. Los pesos son 1, 3, 3, 2, 3, 3, 2, …, 3, 3, 1.",
            [r"h = \frac{b - a}{n}, \qquad x_i = a + i\,h",
             r"\int_a^b f(x)\,dx \approx \frac{3h}{8}\left[f(x_0) + 3\sum_{i \not\equiv 0} f(x_i) + 2\sum_{i \equiv 0} f(x_i) + f(x_n)\right]",
             r"\text{error} = -\frac{(b - a)\,h^4}{80} f^{(4)}(\mu)"])


def _datos_regla(res, d):
    c = res.ctx
    return [("latex", rf"f(x) = {c['latex']}"),
            ("texto", f"Intervalo [a, b] = [{txt_num(c['a'], d)}, {txt_num(c['b'], d)}] con n = {c['n']} subintervalos:"),
            ("latex", rf"h = \frac{{{N(c['b'], d)} - {S(c['a'], d)}}}{{{c['n']}}} = {N(c['h'], d)}")]


def _paso_regla(res, k, d):
    c = res.ctx
    r = res.df.iloc[k - 1]
    i = int(r["i"])
    return [rf"x_{{{i}}} = a + {i}h = {N(c['a'], d)} + {i}\cdot{S(c['h'], d)} = {N(r['xᵢ'], d)}",
            rf"f(x_{{{i}}}) = {_sust(c['expr'], r['xᵢ'], d)} = {N(r['f(xᵢ)'], d)}",
            rf"w_{{{i}}}\,f(x_{{{i}}}) = {int(r['peso'])}\cdot{S(r['f(xᵢ)'], d)} = {N(r['peso·f(xᵢ)'], d)}",
            rf"\textstyle\sum = {N(r['suma acumulada'], d)}"]


def _conclusion_regla(res, d):
    c = res.ctx
    suma = res.df["peso·f(xᵢ)"].sum()
    factor = r"\frac{h}{2}" if c["regla"] == "trapecio" else r"\frac{3h}{8}"
    factor_num = c["h"] / 2 if c["regla"] == "trapecio" else 3 * c["h"] / 8
    B = [("titulo", "Resultado"),
         ("latex", rf"\int_{{{N(c['a'], d)}}}^{{{N(c['b'], d)}}} f(x)\,dx \approx {factor}\sum w_i f(x_i) = "
                   rf"{N(factor_num, d)}\cdot{S(suma, d)} = {N(res.valor, d)}")]
    if c["ref"] == c["ref"]:
        B.append(("texto", "Comparación con un valor de referencia de alta precisión:"))
        B.append(("latex", rf"|I - I_{{\text{{aprox}}}}| = |{N(c['ref'], d)} - {S(res.valor, d)}| = {N(abs(c['ref'] - res.valor), d)}"))
    if c["cota"] == c["cota"]:
        nombre, pot, den = ("f''", 2, 12) if c["regla"] == "trapecio" else ("f^{(4)}", 4, 80)
        B.append(("latex", rf"\text{{cota}} = \frac{{(b-a)\,h^{pot}}}{{{den}}}\max|{nombre}| = {N(c['cota'], d)}"))
    return B


# ============================================================================= CUADRATURA ADAPTATIVA
def _plan_adapt(res, d):
    return ("La cuadratura adaptativa usa Simpson 1/3 en un intervalo y lo compara con Simpson en sus dos mitades. Si la "
            "diferencia es pequeña, acepta; si no, parte el intervalo y cada mitad debe cumplir la mitad de la tolerancia. "
            "Así pone más puntos solo donde f cambia rápido.",
            [r"S(a, b) = \frac{b - a}{6}\left[f(a) + 4f(m) + f(b)\right], \qquad m = \frac{a + b}{2}",
             r"\left|S(a, m) + S(m, b) - S(a, b)\right| < 15\,\varepsilon \;\Rightarrow\; \text{se acepta } S(a, m) + S(m, b)",
             r"\text{si no: } [a, m] \text{ y } [m, b] \text{ con tolerancia } \varepsilon/2"])


def _datos_adapt(res, d):
    c = res.ctx
    return [("latex", rf"f(x) = {c['latex']}"),
            ("texto", f"Intervalo [{txt_num(c['a'], d)}, {txt_num(c['b'], d)}], tolerancia ε = {txt_sci(res.tol, 0)}, "
                      f"hasta {res.n_max} niveles de división.")]


def _paso_adapt(res, k, d):
    r = res.df.iloc[k - 1]
    m = (r["a"] + r["b"]) / 2
    signo = "<" if r["decisión"] == "acepta" else r"\ge"
    accion = {"acepta": r"\text{se acepta}", "divide": r"\text{se divide en dos}",
              "acepta (tope)": r"\text{se acepta por llegar al nivel máximo}"}[r["decisión"]]
    return [rf"[a, b] = [{N(r['a'], d)},\ {N(r['b'], d)}], \quad m = {N(m, d)} \quad (\text{{nivel }} {int(r['nivel'])})",
            rf"S(a, b) = {N(r['S(a,b)'], d)}, \qquad S(a, m) + S(m, b) = {N(r['S(a,m)+S(m,b)'], d)}",
            rf"|{N(r['S(a,m)+S(m,b)'], d)} - {S(r['S(a,b)'], d)}| = {N(r['|diferencia|'], d)} {signo} {N(r['15·tol'], d)}"
            rf" \;\Rightarrow\; {accion}"]


def _conclusion_adapt(res, d):
    c = res.ctx
    ok = res.df[res.df["decisión"] != "divide"]
    B = [("titulo", "Resultado"),
         ("texto", f"Se suman los {len(ok)} subintervalos aceptados:")]
    partes = [N(v, min(d, 6)) for v in ok["S(a,m)+S(m,b)"].head(6)]
    resto = r" + \ldots" if len(ok) > 6 else ""
    B.append(("latex", rf"I \approx {' + '.join(partes)}{resto} = {N(res.valor, d)}".replace("+ -", "- ")))
    if c["ref"] == c["ref"]:
        B.append(("latex", rf"|I - I_{{\text{{aprox}}}}| = {N(abs(c['ref'] - res.valor), d)} \quad "
                           rf"(\text{{tolerancia pedida: }} {tex_tol(res.tol)})"))
    if c.get("aviso"):
        B.append(("texto", "Atención: " + c["aviso"]))
    return B


# ============================================================================= INTEGRAL DOBLE
def _plan_doble(res, d):
    trap = res.ctx["regla"] == "trapecio"
    nombre = "del trapecio" if trap else "de Simpson 3/8"
    factor = r"\frac{h}{2}" if trap else r"\frac{3h}{8}"
    factor_k = r"\frac{k_i}{2}" if trap else r"\frac{3k_i}{8}"
    extra = "" if trap else " Por eso n y m deben ser múltiplos de 3."
    return (f"La integral doble se resuelve como dos integrales simples, cada una con la regla {nombre}: para cada nodo "
            "xᵢ se integra en y entre c(xᵢ) y d(xᵢ) (integral interior Jᵢ); después se integran los Jᵢ en x." + extra,
            [r"\int_a^b \int_{c(x)}^{d(x)} f(x, y)\,dy\,dx",
             r"h = \frac{b - a}{n}, \qquad k_i = \frac{d(x_i) - c(x_i)}{m}, \qquad y_{ij} = c(x_i) + j\,k_i",
             rf"J_i = {factor_k}\sum_j w_j\,f(x_i, y_{{ij}}), \qquad I \approx {factor}\sum_i w_i\,J_i"])


def _datos_doble(res, d):
    c = res.ctx
    return [("latex", rf"f(x, y) = {c['latex']}"),
            ("latex", rf"a = {N(c['a'], d)}, \quad b = {N(c['b'], d)}, \quad c(x) = {c['latex_c']}, \quad d(x) = {c['latex_d']}"),
            ("latex", rf"n = {c['n']}, \quad m = {c['m']}, \quad h = {N(c['h'], d)}")]


def _paso_doble(res, k, d):
    c = res.ctx
    r = res.df.iloc[k - 1]
    i = int(r["i"])
    det = c["detalle"][i]
    trap = c["regla"] == "trapecio"
    L = [rf"x_{{{i}}} = {N(r['xᵢ'], d)}, \quad c(x_{{{i}}}) = {N(r['c(xᵢ)'], d)}, \quad d(x_{{{i}}}) = {N(r['d(xᵢ)'], d)}",
         rf"k_{{{i}}} = \frac{{{N(r['d(xᵢ)'], d)} - {S(r['c(xᵢ)'], d)}}}{{{c['m']}}} = {N(r['kᵢ'], d)}"]
    mostrar = len(det["ys"]) <= 7
    terminos = []
    for j, (y, fv, w) in enumerate(zip(det["ys"], det["f"], det["w"])):
        if mostrar:
            L.append(rf"f(x_{{{i}}}, y_{{{i}{j}}}) = f({N(r['xᵢ'], d)},\ {N(y, d)}) = {N(fv, d)} \quad (w = {int(w)})")
        terminos.append(rf"{int(w)}\cdot{S(fv, d)}" if mostrar else "")
    suma = float(sum(det["w"] * det["f"]))
    factor = r"\frac{k_i}{2}" if trap else r"\frac{3k_i}{8}"
    if mostrar:
        L.append(rf"J_{{{i}}} = {factor}\left[{' + '.join(terminos)}\right] = {N(r['Jᵢ'], d)}")
    else:
        L.append(rf"J_{{{i}}} = {factor}\sum_j w_j f(x_{{{i}}}, y_{{{i}j}}) = {factor}\cdot{S(suma, d)} = {N(r['Jᵢ'], d)}")
    L.append(rf"w_{{{i}}}\,J_{{{i}}} = {int(r['peso'])}\cdot{S(r['Jᵢ'], d)} = {N(r['peso·Jᵢ'], d)}")
    return L


def _conclusion_doble(res, d):
    c = res.ctx
    suma = res.df["peso·Jᵢ"].sum()
    trap = c["regla"] == "trapecio"
    factor, fnum = (r"\frac{h}{2}", c["h"] / 2) if trap else (r"\frac{3h}{8}", 3 * c["h"] / 8)
    B = [("titulo", "Resultado"),
         ("latex", rf"I \approx {factor}\sum_i w_i J_i = {N(fnum, d)}\cdot{S(suma, d)} = {N(res.valor, d)}")]
    if c["ref"] == c["ref"]:
        B.append(("latex", rf"|I - I_{{\text{{aprox}}}}| = |{N(c['ref'], d)} - {S(res.valor, d)}| = {N(abs(c['ref'] - res.valor), d)}"))
    return B


# ============================================================================= registro
# id -> (planteamiento, datos, paso, conclusión, título de la sección de pasos)
METODOS = {
    "punto_flotante": (_plan_pf, _datos_pf, _paso_pf, _conclusion_pf, "Conversión a binario"),
    "neville": (_plan_neville, _datos_interp, _paso_neville, _conclusion_neville, "Filas de la tabla de Neville"),
    "hermite": (_plan_hermite, lambda r, d: _datos_interp(r, d, True), _paso_hermite, _conclusion_hermite,
                "Filas de la tabla de diferencias divididas"),
    "derivada_2p": (_plan_deriv, _datos_deriv, _paso_deriv, _conclusion_deriv, "Aplicación con cada h"),
    "derivada_5p": (_plan_deriv, _datos_deriv, _paso_deriv, _conclusion_deriv, "Aplicación con cada h"),
    "trapecio": (_plan_regla, _datos_regla, _paso_regla, _conclusion_regla, "Nodos"),
    "simpson38": (_plan_regla, _datos_regla, _paso_regla, _conclusion_regla, "Nodos"),
    "adaptativa": (_plan_adapt, _datos_adapt, _paso_adapt, _conclusion_adapt, "Subintervalos revisados"),
    "doble_trapecio": (_plan_doble, _datos_doble, _paso_doble, _conclusion_doble, "Integrales interiores (una por nodo xᵢ)"),
    "doble_simpson38": (_plan_doble, _datos_doble, _paso_doble, _conclusion_doble, "Integrales interiores (una por nodo xᵢ)"),
}


def etiqueta_paso_directo(res, k: int, final: bool = False) -> str:
    nombre = res.ctx.get("nombre_paso", "Paso")
    if res.id in ("neville", "hermite", "trapecio", "simpson38", "doble_trapecio", "doble_simpson38"):
        texto = f"{nombre} i = {k - 1}"
    else:
        texto = f"{nombre} {k}"
    return texto + (" (el último)" if final else "")


def bloques_directo(res, d, iteraciones, elegir_iteraciones):
    plan, datos, paso, conclusion, titulo_pasos = METODOS[res.id]
    texto, formulas = plan(res, d)
    B = [("titulo", "Planteamiento"), ("texto", texto)]
    B += [("latex", f) for f in formulas]
    B.append(("titulo", "Datos"))
    B += datos(res, d)
    elegidas, falta_final = elegir_iteraciones(res, iteraciones)
    B.append(("titulo", titulo_pasos))
    for k in elegidas:
        B.append(("subtitulo", etiqueta_paso_directo(res, k, final=(k == res.n_filas))))
        B += [("latex", linea) for linea in paso(res, k, d)]
    if falta_final:
        if elegidas and res.n_filas - elegidas[-1] > 1:
            B.append(("texto", "…los pasos intermedios se calculan exactamente igual (están todos en la tabla). "
                               "Se muestra ahora el último:"))
        B.append(("subtitulo", etiqueta_paso_directo(res, res.n_filas, final=True)))
        B += [("latex", linea) for linea in paso(res, res.n_filas, d)]
    B += conclusion(res, d)
    return B


def detalle_directo(res, k, d):
    return METODOS[res.id][2](res, k, d)
