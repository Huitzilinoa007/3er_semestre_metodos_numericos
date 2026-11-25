# Interpolación de Hermite con diferencias divididas: el polinomio pasa por los puntos (x_i, f(x_i)) Y además
# tiene la misma pendiente f'(x_i) en cada uno. El truco: cada nodo se repite dos veces (z_{2i} = z_{2i+1} = x_i)
# y donde la diferencia dividida sería 0/0 se pone la derivada.
import numpy as np
import pandas as pd
import sympy as sp


def hermite(xs, ys, dys):
    """Devuelve (z, Q) con Q la tabla de diferencias divididas (2n x 2n, NaN arriba de la diagonal)."""
    n = len(xs)
    m = 2 * n
    z = np.repeat(np.asarray(xs, dtype=float), 2)   # Cada nodo dos veces.
    Q = np.full((m, m), np.nan)
    for i in range(n):
        Q[2 * i, 0] = Q[2 * i + 1, 0] = ys[i]
        Q[2 * i + 1, 1] = dys[i]   # Nodo repetido: la primera diferencia dividida es la derivada.
        if i > 0:
            Q[2 * i, 1] = (Q[2 * i, 0] - Q[2 * i - 1, 0]) / (z[2 * i] - z[2 * i - 1])
    for i in range(2, m):
        for j in range(2, i + 1):
            Q[i, j] = (Q[i, j - 1] - Q[i - 1, j - 1]) / (z[i] - z[i - j])
    return z, Q


def polinomio_hermite(z, Q, hasta=None):
    """H(x) = Q00 + Q11 (x − z0) + Q22 (x − z0)(x − z1) + …  (hasta el término `hasta`, incluido)."""
    x = sp.Symbol("x")
    m = len(z) if hasta is None else hasta + 1
    H, producto = sp.Integer(0), sp.Integer(1)
    for k in range(m):
        H += sp.Float(Q[k, k], 15) * producto
        producto *= (x - sp.Float(z[k], 15))
    return H


def tabla_hermite(xs, ys, dys):
    z, Q = hermite(xs, ys, dys)
    filas = []
    for i in range(len(z)):
        fila = {"i": i, "zᵢ": z[i]}
        for j in range(len(z)):
            fila[f"Q_{j}"] = Q[i, j]
        filas.append(fila)
    return z, Q, pd.DataFrame(filas)
