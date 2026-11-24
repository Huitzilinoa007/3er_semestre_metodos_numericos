# Método de bisección: parte el intervalo [a, b] a la mitad una y otra vez hasta quedar muy cerca de la raíz.
import numpy as np   # Aquí se usa numpy porque necesitamos np.nan para marcar "sin dato" y que la columna siga siendo de números.
import pandas as pd  # pandas arma la tabla de iteraciones (DataFrame) que luego se muestra y se exporta.


def biseccion(f, a: float, b: float, error: float, n: int):
    # Aquí se evalúa f en los extremos porque el signo de f(a) y f(b) decide si hay una raíz adentro.
    fa, fb = float(f(a)), float(f(b))

    # 1. Primero se revisa si algún extremo ya es raíz (así no se hace trabajo de más y no falla el chequeo de signos).
    if abs(fa) < 1e-14:
        return a, pd.DataFrame([{'iter': 1, 'a': a, 'b': b, 'c': a, 'f(a)': fa, 'f(b)': fb, 'f(c)': fa, 'error': 0.0, 'error relativo': 0.0}])
    if abs(fb) < 1e-14:
        return b, pd.DataFrame([{'iter': 1, 'a': a, 'b': b, 'c': b, 'f(a)': fa, 'f(b)': fb, 'f(c)': fb, 'error': 0.0, 'error relativo': 0.0}])

    # 2. Teorema de Bolzano: si f(a) y f(b) tienen el mismo signo, no se puede garantizar una raíz en [a, b].
    if fa * fb > 0:
        raise ValueError(f"No se cumple Bolzano: f({a})={fa:.4f} y f({b})={fb:.4f} tienen el mismo signo.")

    historial = []       # Se guardan las filas en una lista y se arma el DataFrame al final: es mucho más rápido que agregar fila por fila.
    c_anterior = None    # Se necesita el c de la vuelta pasada para medir cuánto cambió la aproximación (el error).

    for i in range(1, n + 1):
        c = a + (b - a) / 2.0   # Punto medio escrito así porque evita desbordes con números muy grandes.
        fa, fb, fc = float(f(a)), float(f(b)), float(f(c))

        # En la iteración 1 no hay "c anterior"; se usa np.nan para que la columna siga siendo de tipo float.
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

        # Criterio de paro: raíz exacta o error menor a la tolerancia pedida.
        if abs(fc) < 1e-14 or (c_anterior is not None and err_iterado <= error):
            break

        # Ya con f(c) se queda con la mitad donde f cambia de signo; ahí sigue estando la raíz.
        if fa * fc < 0:
            b = c
        else:
            a = c

        c_anterior = c

    df = pd.DataFrame(historial)
    return c, df
