# Integración numérica: regla del trapecio compuesta, Simpson 3/8 compuesta y cuadratura adaptativa (Simpson).
import numpy as np
import pandas as pd


def pesos_trapecio(n):
    w = np.full(n + 1, 2.0)
    w[0] = w[-1] = 1.0
    return w


def pesos_simpson38(n):
    if n % 3:
        raise ValueError(f"Simpson 3/8 necesita que n sea múltiplo de 3 (n = {n} no lo es). Prueba con n = {n + 3 - n % 3}.")
    w = np.array([1.0] + [2.0 if i % 3 == 0 else 3.0 for i in range(1, n)] + [1.0])
    return w


def regla_compuesta(f, a, b, n, regla):
    """regla: "trapecio" o "simpson38". Devuelve (integral, tabla con una fila por nodo)."""
    if n < 1:
        raise ValueError("El número de subintervalos n debe ser al menos 1.")
    h = (b - a) / n
    xs = a + h * np.arange(n + 1)
    ys = np.array([f(x) for x in xs])
    if not np.all(np.isfinite(ys)):
        malos = xs[~np.isfinite(ys)]
        raise ValueError(f"f no está definida (o es infinita) en x = {malos[0]:g}; la regla necesita f en todos los nodos.")
    w = pesos_trapecio(n) if regla == "trapecio" else pesos_simpson38(n)
    factor = h / 2 if regla == "trapecio" else 3 * h / 8
    prod = w * ys
    df = pd.DataFrame({"i": np.arange(n + 1), "xᵢ": xs, "f(xᵢ)": ys, "peso": w.astype(int),
                       "peso·f(xᵢ)": prod, "suma acumulada": np.cumsum(prod)})
    return factor * prod.sum(), df


def _simpson(f, a, fa, b, fb):
    m = (a + b) / 2
    fm = f(m)
    return m, fm, (b - a) / 6 * (fa + 4 * fm + fb)


def cuadratura_adaptativa(f, a, b, tol, max_nivel=20, max_filas=2000):
    """Simpson adaptativo (Burden, algoritmo 4.3): divide solo donde hace falta.

    En cada subintervalo compara S(a,b) con S(a,m) + S(m,b); si |diferencia| < 15·tol_local se acepta,
    si no, se parte a la mitad y cada mitad recibe la mitad de la tolerancia.
    Devuelve (integral, tabla con una fila por subintervalo revisado, ¿todos cumplieron la tolerancia?).
    """
    filas = []
    todo_ok = True
    fa, fb = f(a), f(b)
    m, fm, s_total = _simpson(f, a, fa, b, fb)
    pendientes = [(a, fa, b, fb, m, fm, s_total, tol, 1)]   # Pila: se procesa primero la mitad izquierda.
    total = 0.0
    while pendientes:
        a_, fa_, b_, fb_, m_, fm_, s1, tol_, nivel = pendientes.pop()
        ml, fml, s_izq = _simpson(f, a_, fa_, m_, fm_)
        mr, fmr, s_der = _simpson(f, m_, fm_, b_, fb_)
        s2 = s_izq + s_der
        dif = abs(s2 - s1)
        if not np.isfinite(s2):
            raise ValueError(f"f no está definida en algún punto de [{a_:g}, {b_:g}]; la cuadratura necesita f finita.")
        acepta = dif < 15 * tol_
        forzado = (not acepta) and nivel >= max_nivel
        if forzado:
            todo_ok = False
        filas.append({"paso": len(filas) + 1, "nivel": nivel, "a": a_, "b": b_, "S(a,b)": s1,
                      "S(a,m)+S(m,b)": s2, "|diferencia|": dif, "15·tol": 15 * tol_,
                      "decisión": "acepta" if acepta else ("acepta (tope)" if forzado else "divide")})
        if len(filas) > max_filas:
            raise RuntimeError(f"La cuadratura adaptativa revisó más de {max_filas} subintervalos sin terminar.")
        if acepta or forzado:
            total += s2
        else:
            # Se apila primero la derecha para que la izquierda se procese antes (orden natural de lectura).
            pendientes.append((m_, fm_, b_, fb_, mr, fmr, s_der, tol_ / 2, nivel + 1))
            pendientes.append((a_, fa_, m_, fm_, ml, fml, s_izq, tol_ / 2, nivel + 1))
    return total, pd.DataFrame(filas), todo_ok
