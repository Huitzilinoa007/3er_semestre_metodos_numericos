# Método de Newton-Raphson: usa la recta tangente en el punto actual; donde esa tangente cruza el eje x
# queda la siguiente aproximación.
import pandas as pd  # pandas arma la tabla de iteraciones.


def raiz_newton(f, f_prima_x, x, error, max_iter=1000, lanzar=True):
    """
    Método de Newton-Raphson puro.
    No realiza ningún print interno; devuelve la raíz encontrada y el DataFrame con el historial.
    """
    if f(x) == 0:
        # Si se le atina a la raíz desde el inicio, se devuelve una tabla vacía con sus columnas (no hay iteraciones que hacer).
        df_vacio = pd.DataFrame(columns=['x', 'f(x)', 'x1', "f'(x)", 'error', 'error relativo'])
        return x, df_vacio

    i = 0
    estructura = {
        'x': [], 'f(x)': [], 'x1': [], "f'(x)": [],
        'error': [], 'error relativo': []
    }
    df = pd.DataFrame(estructura)

    while i < max_iter:
        fx = f(x)
        f_prime_x = f_prima_x(x)

        # Aquí se evita dividir entre cero: con tangente horizontal el método no puede avanzar.
        if f_prime_x == 0:
            raise ValueError("Derivada cero detectada. El método no puede continuar.")

        # Fórmula de Newton: x_{k+1} = x_k - f(x_k) / f'(x_k)
        x1 = x - (fx / f_prime_x)
        err_iterado = abs(x1 - x)
        err_relativo = err_iterado / abs(x1) if x1 != 0 else 0

        nueva_iter = pd.DataFrame([{
            'x': x,
            'f(x)': fx,
            'x1': x1,
            "f'(x)": f_prime_x,
            'error': err_iterado,
            'error relativo': err_relativo
        }])
        df = pd.concat([df, nueva_iter], ignore_index=True)

        # Se exige al menos una vuelta (i > 0) antes de parar, como en tu versión original.
        if i > 0 and error >= err_iterado:
            return x1, df

        # Ya con x1 se sigue iterando poco a poco: el nuevo punto de partida es el que acabamos de calcular.
        x = x1
        i += 1

    # lanzar=False lo usa la app: así se puede mostrar la tabla de lo que sí se hizo y marcar "No convergió".
    if not lanzar:
        return x, df
    raise RuntimeError(f"Se alcanzó el límite máximo de {max_iter} iteraciones sin converger.")
