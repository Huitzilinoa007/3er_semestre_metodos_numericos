# Derivación numérica con fórmulas de 2 y de 5 puntos.
# Para ver el ORDEN del error se aplica la fórmula con h, h/2, h/4, …: si el error se divide entre 2 cada vez,
# la fórmula es O(h); si se divide entre 16, es O(h⁴).
import numpy as np
import pandas as pd

# Cada fórmula: (desplazamientos de los puntos en múltiplos de h, coeficientes, divisor del h, orden del error).
FORMULAS = {
    "2_adelante": ((0, 1), (-1, 1), 1, 1),                                  # [f(x0+h) − f(x0)] / h
    "2_atras": ((-1, 0), (-1, 1), 1, 1),                                    # [f(x0) − f(x0−h)] / h
    "5_centrada": ((-2, -1, 1, 2), (1, -8, 8, -1), 12, 4),                  # punto medio
    "5_extremo": ((0, 1, 2, 3, 4), (-25, 48, -36, 16, -3), 12, 4),          # punto extremo (progresiva)
}


def aplicar(f, x0, h, clave):
    desplaz, coefs, divisor, _ = FORMULAS[clave]
    valores = [f(x0 + s * h) for s in desplaz]
    aprox = sum(c * v for c, v in zip(coefs, valores)) / (divisor * h)
    return aprox, valores


def derivacion(f, x0, h, pasos, clave, exacta=None):
    """Aplica la fórmula con h, h/2, …, h/2^(pasos−1). Devuelve (última aproximación, tabla)."""
    desplaz = FORMULAS[clave][0]
    filas, err_prev = [], None
    for k in range(pasos):
        hk = h / 2 ** k
        aprox, valores = aplicar(f, x0, hk, clave)
        fila = {"k": k + 1, "h": hk}
        for s, v in zip(desplaz, valores):
            fila[_nombre(s)] = v
        fila["aproximación"] = aprox
        if exacta is not None:
            err = abs(aprox - exacta)
            fila["error real"] = err
            # Razón entre errores sucesivos: tiende a 2^orden (2 para O(h), 16 para O(h⁴)).
            fila["razón"] = (err_prev / err) if (err_prev is not None and err > 0) else np.nan
            err_prev = err
        filas.append(fila)
    return filas[-1]["aproximación"], pd.DataFrame(filas)


def _nombre(s):
    if s == 0:
        return "f(x₀)"
    signo = "+" if s > 0 else "−"
    mult = "" if abs(s) == 1 else str(abs(s))
    return f"f(x₀{signo}{mult}h)"
