# Método de Neville: evalúa el polinomio interpolante en un punto x SIN calcular sus coeficientes.
# Cada Q[i][j] es el valor en x del polinomio que pasa por los puntos x_{i-j}, ..., x_i;
# se arma una tabla triangular ("escalerita") donde cada celda sale de dos celdas de la columna anterior.
import numpy as np
import pandas as pd


def neville(xs, ys, x):
    """Devuelve (P(x) = Q[n][n], matriz Q completa con NaN arriba de la diagonal)."""
    n = len(xs)
    Q = np.full((n, n), np.nan)
    Q[:, 0] = ys   # Primera columna: los valores f(x_i) (polinomios de grado 0).
    for i in range(1, n):
        for j in range(1, i + 1):
            # Fórmula de Neville: combina el polinomio de los puntos i-j..i-1 con el de i-j+1..i.
            Q[i, j] = ((x - xs[i - j]) * Q[i, j - 1] - (x - xs[i]) * Q[i - 1, j - 1]) / (xs[i] - xs[i - j])
    return Q[n - 1, n - 1], Q


def tabla_neville(xs, ys, x):
    valor, Q = neville(xs, ys, x)
    n = len(xs)
    filas = []
    for i in range(n):
        fila = {"i": i, "xᵢ": xs[i], "x − xᵢ": x - xs[i]}
        for j in range(n):
            fila[f"Q_{j}"] = Q[i, j]
        filas.append(fila)
    return valor, Q, pd.DataFrame(filas)
