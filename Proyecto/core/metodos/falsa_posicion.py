# Método de la falsa posición (regla falsa): como la bisección, pero el nuevo punto es donde la recta
# que une (a, f(a)) con (b, f(b)) cruza el eje x.
# Misma fórmula de tu archivo original; solo se adaptó la interfaz para Streamlit:
#   - se quitaron input() y print() porque en Streamlit congelarían la app,
#   - se agregó el tope de iteraciones `n` porque antes el ciclo podía no terminar nunca,
#   - ahora devuelve (c, tabla) igual que la bisección.
import numpy as np
import pandas as pd


def falsa_posicion(f, a: float, b: float, error: float, n: int = 100):
    fa, fb = float(f(a)), float(f(b))

    # Si un extremo ya es raíz se devuelve de inmediato, igual que en bisección.
    if abs(fa) < 1e-14:
        return a, pd.DataFrame([{'iter': 1, 'a': a, 'b': b, 'c': a, 'f(a)': fa, 'f(b)': fb, 'f(c)': fa, 'error': 0.0, 'error relativo': 0.0}])
    if abs(fb) < 1e-14:
        return b, pd.DataFrame([{'iter': 1, 'a': a, 'b': b, 'c': b, 'f(a)': fa, 'f(b)': fb, 'f(c)': fb, 'error': 0.0, 'error relativo': 0.0}])

    # Aquí se pide cambio de signo porque sin él la recta entre los extremos no garantiza una raíz en el intervalo.
    if fa * fb > 0:
        raise ValueError(f"No se cumple Bolzano: f({a})={fa:.4f} y f({b})={fb:.4f} tienen el mismo signo.")

    historial = []
    c_anterior = None

    for i in range(1, n + 1):
        fa, fb = float(f(a)), float(f(b))
        # Aquí está la fórmula de la regla falsa: el cruce con el eje x de la recta que une los extremos.
        c = b - ((fb * (a - b)) / (fa - fb))
        fc = float(f(c))

        if c_anterior is None:
            err_iterado = np.nan
            err_relativo = np.nan
        else:
            err_iterado = abs(c - c_anterior)
            err_relativo = err_iterado / abs(c) if c != 0 else 0.0

        historial.append({
            'iter': i, 'a': a, 'b': b, 'c': c,
            'f(a)': fa, 'f(b)': fb, 'f(c)': fc,
            'error': err_iterado, 'error relativo': err_relativo
        })

        if abs(fc) < 1e-14 or (c_anterior is not None and err_iterado <= error):
            break

        # Se conserva el subintervalo donde f cambia de signo (la raíz sigue ahí).
        if fa * fc < 0:
            b = c
        else:
            a = c

        c_anterior = c

    return c, pd.DataFrame(historial)
