# Método de la secante: igual que Newton pero sin derivada; usa la recta que pasa por los dos últimos puntos.
# Misma fórmula de tu archivo original. Cambios de interfaz:
#   - tope de iteraciones `max_iter` (antes `while True` sin límite),
#   - mensaje claro si f(x0) == f(x1) (secante horizontal, división entre cero).
import pandas as pd


def secante(f, x0, x1, error, max_iter=100):
    # Si alguno de los dos puntos iniciales ya es raíz, no hay nada que iterar.
    if f(x0) == 0:
        return x0, pd.DataFrame()
    elif f(x1) == 0:
        return x1, pd.DataFrame()
    else:
        i = 0
        err_iterado = 0
        err_relativo = 0

        estructura = {
            'x_0': [], 'x_1': [], 'x_2': [],
            'f(x_0)': [], 'f(x_1)': [], 'f(x_2)': [],
            'error': [], 'error relativo': []
        }
        df = pd.DataFrame(estructura)
        x2 = x1  # Valor inicial para poder devolver algo aunque se agoten las iteraciones.

        while i < max_iter:
            # Aquí se revisa antes de dividir: si f(x1) = f(x0) la recta es horizontal y nunca cruza el eje x.
            if f(x1) == f(x0):
                raise ValueError("f(x0) y f(x1) son iguales: la secante es horizontal y el método no puede continuar.")

            # Fórmula de la secante: sustituye f'(x) por el cociente de diferencias de los dos últimos puntos.
            x2 = x1 - ((f(x1) * (x1 - x0)) / (f(x1) - f(x0)))

            if i > 0:
                err_iterado = abs(x2 - x1)
                err_relativo = err_iterado / abs(x2) if x2 != 0 else 0
            else:
                err_iterado = 0
                err_relativo = 0

            nueva_iter = pd.DataFrame([{
                'x_0': x0,
                'x_1': x1,
                'x_2': x2,
                'f(x_0)': f(x0),
                'f(x_1)': f(x1),
                'f(x_2)': f(x2),
                'error': err_iterado if i > 0 else "-",
                'error relativo': err_relativo if i > 0 else "-"
            }])

            df = pd.concat([df, nueva_iter], ignore_index=True)

            if i > 0 and err_iterado <= error:
                return x2, df

            # Ya con x2 se "corre la escalerita": x1 pasa a ser x0 y x2 pasa a ser x1 para la siguiente vuelta.
            x0 = x1
            x1 = x2
            i += 1

        return x2, df
