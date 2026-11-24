# PLANTILLA para un método nuevo (el guion bajo del nombre evita que se confunda con un método real).
# Cómo usarla: copia este archivo, cámbiale el nombre (por ejemplo `trapecio.py`) y sigue la guía del README.
#
# Regla de oro: la función devuelve (resultado, tabla) y la tabla lleva UNA FILA POR ITERACIÓN.
# Aquí se pide una columna 'iter' empezando en 1 porque el slider, la tabla animada y el procedimiento la usan.
import numpy as np   # np.nan marca "sin dato" (por ejemplo el error de la primera fila) sin romper el tipo float.
import pandas as pd  # La tabla de iteraciones es un DataFrame.


def mi_metodo(f, x0: float, tolerancia: float, max_iter: int):
    filas = []  # Se arma una lista de diccionarios y al final el DataFrame; así es más rápido que agregar filas una por una.
    x = x0
    for i in range(1, max_iter + 1):
        # TODO: aquí va la fórmula de tu método (usa f(x) como si fuera una función normal de Python).
        x_nuevo = x
        error = np.nan if i == 1 else abs(x_nuevo - x)
        filas.append({"iter": i, "x": x, "x_nuevo": x_nuevo, "error": error})
        # Ya con el error de esta vuelta se decide si se para o se sigue iterando poco a poco.
        if i > 1 and error <= tolerancia:
            break
        x = x_nuevo
    return x_nuevo, pd.DataFrame(filas)
