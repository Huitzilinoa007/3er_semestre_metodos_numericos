# Punto fijo: se reescribe f(x)=0 como x = g(x) y se itera x_{k+1} = g(x_k).
# Misma lógica de tu archivo original. Cambios de interfaz:
#   - `max_iter` ahora es parámetro (por defecto 1000, como antes) para que la app pueda controlarlo,
#   - el RuntimeError solo se lanza si de verdad NO convergió (antes también saltaba si convergía
#     justo en la última iteración permitida).
import pandas as pd


def punto_fijo_validado(x0, g, g_prime, tol, max_iter=1000):
    # Aquí se valida |g'(x0)| < 1 porque es la condición que asegura que la iteración se va acercando a la solución.
    derivada_inicial = abs(g_prime(x0))

    if derivada_inicial >= 1:
        raise ValueError("La derivada en el punto inicial es mayor o igual a 1. El método va a divergir.")

    x_prev = x0
    x_curr = g(x_prev)
    iter_count = 1

    columnas = ["x0", "x1", "Error"]
    df = pd.DataFrame(columns=columnas)
    df.loc[len(df)] = [x_prev, x_curr, abs(x_curr - x_prev)]

    # Ya con el primer valor, se va iterando poco a poquito hasta que dos valores seguidos casi no cambien.
    while abs(x_curr - x_prev) > tol and iter_count < max_iter:
        x_prev = x_curr
        x_curr = g(x_prev)
        iter_count += 1
        df.loc[len(df)] = [x_prev, x_curr, abs(x_curr - x_prev)]

    # Solo se avisa "no convergió" si al terminar el error sigue siendo mayor que la tolerancia.
    if abs(x_curr - x_prev) > tol:
        raise RuntimeError(f"Se alcanzó el límite de {max_iter} iteraciones sin converger.")

    return x_curr, df
