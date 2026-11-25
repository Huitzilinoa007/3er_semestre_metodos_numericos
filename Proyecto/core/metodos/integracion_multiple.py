# Integración doble  ∫_a^b ∫_{c(x)}^{d(x)} f(x, y) dy dx  con la regla del trapecio o Simpson 3/8 en cada dirección.
# Primero, para cada nodo x_i se integra en y (integral interior J_i); luego se integran los J_i en x.
import numpy as np
import pandas as pd

from .integracion import pesos_simpson38, pesos_trapecio


def _pesos(regla, n):
    if regla == "trapecio":
        return pesos_trapecio(n), 0.5
    return pesos_simpson38(n), 3 / 8


def integral_doble(f, a, b, c, d, n, m, regla):
    """f(x, y), c(x), d(x) numéricas. Devuelve (integral, tabla por nodo x_i, detalle por nodo)."""
    if n < 1 or m < 1:
        raise ValueError("n y m deben ser al menos 1.")
    wx, fx = _pesos(regla, n)
    wy, fy = _pesos(regla, m)
    h = (b - a) / n
    xs = a + h * np.arange(n + 1)
    filas, detalle = [], []
    for i, x in enumerate(xs):
        ci, di = c(x), d(x)
        k = (di - ci) / m
        ys = ci + k * np.arange(m + 1)
        fvals = np.array([f(x, y) for y in ys])
        if not np.all(np.isfinite(fvals)) or not np.isfinite(k):
            raise ValueError(f"f(x, y) o los límites no están definidos en x = {x:g}; revisa la región de integración.")
        J = fy * k * float(np.dot(wy, fvals))
        filas.append({"i": i, "xᵢ": x, "c(xᵢ)": ci, "d(xᵢ)": di, "kᵢ": k, "Jᵢ": J,
                      "peso": int(wx[i]), "peso·Jᵢ": wx[i] * J})
        detalle.append({"ys": ys, "f": fvals, "w": wy})
    df = pd.DataFrame(filas)
    total = fx * h * float(df["peso·Jᵢ"].sum())
    return total, df, detalle
