# Deflación polinomial: se encuentra una raíz con Newton, se divide el polinomio entre (x - raíz) con
# división sintética y se repite con el polinomio más chico hasta sacar todas las raíces reales.
# Misma lógica de tu archivo original. Cambios de interfaz:
#   - import relativo (el original `import newton_rapshon` falla dentro de un paquete),
#   - devuelve (raíces, tabla) con una fila por etapa para poder mostrarla en la app,
#   - `max_iter` se pasa a Newton.
import pandas as pd
import sympy as sp  # sympy saca los coeficientes del polinomio y deriva cada polinomio reducido.

from . import newton_raphson as newton  # Aquí se reutiliza tu Newton en lugar de repetir el código.


def division_sintetica(coefs, raiz):
    n = len(coefs)
    if n == 0:
        return [], 0

    # Regla de Ruffini: cada coeficiente nuevo = coeficiente viejo + (coeficiente nuevo anterior * raíz).
    nuevos_coefs = [coefs[0]]
    for i in range(1, n - 1):
        siguiente_coef = coefs[i] + nuevos_coefs[-1] * raiz
        nuevos_coefs.append(siguiente_coef)

    # El último valor sería el residuo: si la raíz es exacta, vale casi cero.
    residuo = coefs[-1] + nuevos_coefs[-1] * raiz
    return nuevos_coefs, residuo


def deflacion(expresion_str, x_inicial, error, max_iter=1000):
    x = sp.Symbol('x')
    expresion = sp.sympify(expresion_str)  # Acepta texto o una expresión ya hecha de SymPy.

    # Poly sirve para sacar los coeficientes de mayor a menor grado.
    polinomio = sp.Poly(expresion, x)
    coeficientes = [float(c) for c in polinomio.all_coeffs()]

    raices = []
    historial = []
    etapa = 0

    while len(coeficientes) > 1:
        # Aquí se reconstruyen f y f' del polinomio ACTUAL en cada vuelta, porque cada etapa trabaja con uno más chico.
        grado = len(coeficientes) - 1
        expresion_actual = sum(c * x**(grado - i) for i, c in enumerate(coeficientes))

        # lambdify con 'math' convierte la expresión en una función rápida de Python.
        f = sp.lambdify(x, expresion_actual, 'math')
        f_prima_simbolica = sp.diff(expresion_actual, x)
        f_prima_x = sp.lambdify(x, f_prima_simbolica, 'math')

        # Se encuentra una raíz con Newton.
        raiz, df_newton = newton.raiz_newton(f, f_prima_x, x_inicial, error, max_iter)
        raices.append(raiz)

        # Se baja el grado del polinomio con la división sintética.
        nuevos_coefs, residuo = division_sintetica(coeficientes, raiz)

        etapa += 1
        historial.append({
            'etapa': etapa,
            'grado': grado,
            'coeficientes': list(coeficientes),
            'x_inicial': x_inicial,
            'raiz': raiz,
            'iteraciones': max(len(df_newton), 1),
            'error': float(df_newton['error'].iloc[-1]) if len(df_newton) else 0.0,
            'residuo': residuo,
            'coeficientes_resultantes': list(nuevos_coefs),
        })

        coeficientes = nuevos_coefs

        if len(coeficientes) <= 1:
            break

        # Se usa la raíz recién hallada como punto de partida de la siguiente etapa.
        x_inicial = raiz

    return raices, pd.DataFrame(historial)
