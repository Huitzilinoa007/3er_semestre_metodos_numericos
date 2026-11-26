# Método de Müller: ajusta una parábola por tres puntos y toma su cruce con el eje x como nueva aproximación.
# Como usa raíz cuadrada de un número que puede ser negativo, puede encontrar raíces complejas.
import pandas as pd
import cmath  # cmath = matemáticas con números complejos; aquí se usa porque el discriminante puede ser negativo.


def muller(f, P0, P1, P2, error, max_iter=1000, lanzar=True):
    estructura = {
        'P0': [], 'P1': [], 'P2': [],
        'f(P0)': [], 'f(P1)': [], 'f(P2)': [],
        'a': [], 'b': [], 'c': [], 'P3': [], 'error': []
    }
    df = pd.DataFrame(estructura)

    for i in range(max_iter):
        f0 = f(P0)
        f1 = f(P1)
        f2 = f(P2)
        c = f2

        # Determinante del sistema que define la parábola; si es cero los puntos están alineados y no hay parábola.
        delta = (P0 - P2) * (P1 - P2) * (P0 - P1)
        if delta == 0:
            # delta solo depende de las x: vale cero cuando dos de los tres puntos coinciden.
            raise ValueError("Dos de los tres puntos P₀, P₁, P₂ coinciden, así que no hay una parábola única "
                             "que pase por ellos. Prueba con otros puntos iniciales.")

        # Coeficientes a y b de la parábola "desplazada" para que pase por P2 (por eso c = f(P2)).
        a = ((P1 - P2) * (f0 - f2) - (P0 - P2) * (f1 - f2)) / delta
        b = ((P0 - P2)**2 * (f1 - f2) - (P1 - P2)**2 * (f0 - f2)) / delta

        # Aquí se usa cmath.sqrt (no math.sqrt) porque el discriminante puede salir negativo.
        discriminante = b**2 - 4 * a * c
        sqrt_disc = cmath.sqrt(discriminante)

        # Se elige el signo de b para que el denominador sea lo más grande posible (evita perder precisión).
        sign_b = 1 if b.real >= 0 else -1
        denominador = b + sign_b * sqrt_disc

        if denominador == 0:
            denominador = b - sign_b * sqrt_disc

        # Nueva aproximación: el cruce de la parábola con el eje x más cercano a P2.
        p3 = P2 - (2 * c) / denominador
        err_iterado = abs(p3 - P2)

        nueva_iter = pd.DataFrame([{
            'P0': P0, 'P1': P1, 'P2': P2,
            'f(P0)': f0, 'f(P1)': f1, 'f(P2)': f2,
            'a': a, 'b': b, 'c': c, 'P3': p3, 'error': err_iterado
        }])
        df = pd.concat([df, nueva_iter], ignore_index=True)

        # Si P3 ya es raíz exacta (f(P3) = 0) se termina aquí: seguir repetiría puntos y delta valdría cero.
        if err_iterado <= error or f(p3) == 0:
            return p3, df

        # Se "corre la escalerita": P1 pasa a ser P0, P2 pasa a ser P1 y P3 pasa a ser P2.
        P0 = P1
        P1 = P2
        P2 = p3

    if not lanzar:   # La app prefiere mostrar la tabla y marcar "No convergió".
        return P2, df
    raise RuntimeError(f"Se alcanzó el límite máximo de {max_iter} iteraciones sin converger.")
