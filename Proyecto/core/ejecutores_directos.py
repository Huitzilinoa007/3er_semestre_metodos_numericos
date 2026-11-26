# Ejecutores de los métodos "directos" (no iterativos): punto flotante, interpolación, derivación e integración.
# Igual que en ejecutores.py: texto del usuario -> parser -> método -> Resultado. Aquí no hay nada de Streamlit.
# La diferencia con los de raíces: en vez de una fila por iteración, la tabla tiene una fila por PASO del cálculo
# (una fila por nodo, por subintervalo, por cada h...). Cada Resultado trae en ctx["kpis"] sus propias tarjetas.
from __future__ import annotations

import math

import mpmath
import numpy as np
import sympy as sp

from .ejecutores import Resultado
from .formato import txt_num, txt_sci
from .metodos.derivacion import FORMULAS, derivacion
from .metodos.hermite import polinomio_hermite, tabla_hermite
from .metodos.integracion import cuadratura_adaptativa, regla_compuesta
from .metodos.integracion_multiple import integral_doble
from .metodos.neville import tabla_neville
from .metodos.punto_flotante import decimal_exacto, punto_flotante
from .metodos.punto_flotante_inverso import punto_flotante_inverso
from .parser import (X, Y, ErrorExpresion, compilar, compilar_xy, derivada, es_lista, latex_de, parsear,
                     parsear_lista)


# ----------------------------------------------------------------------------- utilidades
def _entero(valor, nombre, minimo=1, maximo=None):
    if valor is None or float(valor) != int(float(valor)):
        raise ValueError(f"{nombre} debe ser un número entero.")
    v = int(float(valor))
    if v < minimo:
        raise ValueError(f"{nombre} debe ser al menos {minimo}.")
    if maximo is not None and v > maximo:
        raise ValueError(f"{nombre} debe ser como máximo {maximo}.")
    return v


def _kpi_valor(etiqueta, valor, ayuda=None):
    return ("kpi_raiz", etiqueta, valor, ayuda)


def _kpi(etiqueta, valor, ayuda=None, clave="kpi_iter"):
    return (clave, etiqueta, valor, ayuda)


def _kpi_error(etiqueta, valor, ayuda=None):
    return ("kpi_error", etiqueta, valor, ayuda)


def _integral_referencia(expr, a, b):
    """Valor de referencia de ∫ f con cuadratura de alta precisión (mpmath); NaN si no se puede."""
    try:
        f = sp.lambdify(X, expr, modules=["mpmath"])
        mpmath.mp.dps = 20
        v = float(mpmath.quad(f, [a, b]))
        return v if math.isfinite(v) else float("nan")
    except Exception:  # Solo es una referencia: si falla, simplemente no se muestra el error real.
        return float("nan")


def _max_abs(expr, a, b):
    """max |expr| en [a, b] evaluando en una malla fina (para las cotas de error)."""
    try:
        g = compilar(expr)
        xs = np.linspace(min(a, b), max(a, b), 2001)
        v = np.abs(g(xs))
        v = v[np.isfinite(v)]
        return float(v.max()) if v.size else float("nan")
    except Exception:
        return float("nan")


def _valores_o_funcion(texto, xs, nombre):
    """El campo acepta una lista de valores o una función de x. Devuelve (valores, expr o None)."""
    if es_lista(texto):
        valores = parsear_lista(texto, nombre)
        if len(valores) != len(xs):
            raise ValueError(f"Hay {len(xs)} valores de x pero {len(valores)} en {nombre}; deben ser la misma cantidad.")
        return valores, None
    expr = parsear(texto)
    f = compilar(expr)
    valores = [f(x) for x in xs]
    if not all(np.isfinite(valores)):
        raise ValueError(f"La función de {nombre} no está definida en alguno de los nodos.")
    return valores, expr


def _nodos(texto, minimo=2):
    xs = parsear_lista(texto, "los nodos x")
    if len(xs) < minimo:
        raise ValueError(f"Se necesitan al menos {minimo} nodos.")
    if len(set(xs)) != len(xs):
        raise ValueError("Los nodos x deben ser todos distintos.")
    return xs


# ----------------------------------------------------------------------------- punto flotante
def _ej_punto_flotante(t, n, tol, nmax):
    formato = "doble" if "64" in (t.get("formato") or "") else "simple"
    rep, df, extra = punto_flotante(t["num"], formato)
    v = extra["valor"]
    err_abs = abs(rep.guardado - v)
    err_rel = (err_abs / abs(v)) if v != 0 else 0
    u = 2.0 ** -(extra["n_man"] + 1)   # Unidad de redondeo: la mitad del épsilon de máquina.
    eps = 2.0 ** -extra["n_man"]
    kpis = [
        _kpi_valor("Valor guardado", decimal_exacto(rep.guardado)[:22], "Valor exacto que queda en memoria."),
        _kpi("Hexadecimal", "0x" + rep.hexadecimal, f"{len(rep.bits)} bits"),
        _kpi_error("Error relativo", txt_sci(float(err_rel)), f"Cota: ε/2 = {u:.3e}"),
        _kpi("Épsilon de máquina", f"{eps:.3e}", f"2^-{extra['n_man']}", clave="kpi_estado_ok"),
    ]
    ctx = dict(rep=rep, formato=formato, err_abs=err_abs, err_rel=err_rel, eps=eps, u=u, kpis=kpis,
               nombre_paso="Paso", entradas=dict(num=t["num"]), **extra)
    return Resultado("punto_flotante", float(rep.guardado), df, True, tol, nmax, "bit", ctx)


def _ej_punto_flotante_dispatch(t, n, tol, nmax):
    # Un solo método en el menú con dos sentidos: decimal -> IEEE 754, o IEEE 754 (bits / hex) -> decimal.
    if "decimal" in (t.get("direccion") or "").split("→")[-1].lower():
        return _ej_punto_flotante_inverso(t, n, tol, nmax)
    return _ej_punto_flotante(t, n, tol, nmax)


def _ej_punto_flotante_inverso(t, n, tol, nmax):
    formato = "doble" if "64" in (t.get("formato") or "") else "simple"
    datos, df = punto_flotante_inverso(t["num"], formato)
    v = datos["valor"]
    textos = {"normal": "Número normal", "subnormal": "Subnormal", "cero": "Cero", "infinito": "Infinito", "nan": "NaN"}
    if v is None:
        valor_txt = ("−∞" if datos["s"] else "+∞") if datos["caso"] == "infinito" else "NaN"
        valor = float("nan") if datos["caso"] == "nan" else (float("-inf") if datos["s"] else float("inf"))
    else:
        valor_txt = decimal_exacto(v)[:22]
        valor = float(v)
    kpis = [_kpi_valor("Valor decimal", valor_txt, "Valor exacto que representan los bits."),
            _kpi("Hexadecimal", "0x" + datos["hexadecimal"], f"{len(datos['bits'])} bits"),
            _kpi("Exponente", f"E = {datos['E']}, e = {datos['E'] - datos['sesgo']}" if datos["caso"] == "normal"
                 else f"E = {datos['E']}", f"sesgo = {datos['sesgo']}"),
            _kpi("Tipo de número", textos[datos["caso"]], None, clave="kpi_estado_ok")]
    ctx = dict(datos=datos, formato=formato, kpis=kpis, nombre_paso="Bit", n_exp=datos["n_exp"],
               n_man=datos["n_man"], sesgo=datos["sesgo"], entradas=dict(num=t["num"]))
    return Resultado("punto_flotante_inv", valor, df, True, tol, nmax, "acumulado", ctx)


# ----------------------------------------------------------------------------- interpolación
def _ej_neville(t, n, tol, nmax):
    xs = _nodos(t["xs"])
    ys, expr = _valores_o_funcion(t["ys"], xs, "los valores f(xᵢ)")
    x = float(n["x"])
    valor, Q, df = tabla_neville(xs, ys, x)
    m = len(xs)
    estimado = abs(Q[m - 1, m - 1] - Q[m - 2, m - 2]) if m > 1 else float("nan")
    kpis = [_kpi_valor(f"P({txt_num(x, 4)})", txt_num(valor, 6), "Valor del polinomio interpolante en x."),
            _kpi("Grado del polinomio", str(m - 1), f"{m} nodos")]
    real = float("nan")
    if expr is not None:
        real = abs(compilar(expr)(x) - valor)
        kpis.append(_kpi_error("Error real", txt_sci(real), "|f(x) − P(x)|, porque diste f(x)."))
    kpis.append(_kpi_error("Estimación del error", txt_sci(estimado), "|Qₙₙ − Qₙ₋₁,ₙ₋₁|: cuánto cambió al agregar el último nodo."))
    ctx = dict(xs=xs, ys=ys, x=x, Q=Q, expr=expr, latex=latex_de(expr) if expr is not None else None,
               f=compilar(expr) if expr is not None else None, estimado=estimado, real=real, kpis=kpis,
               nombre_paso="Fila", entradas=dict(x=x))
    return Resultado("neville", valor, df, True, tol, nmax, "Q", ctx)


def _ej_hermite(t, n, tol, nmax):
    xs = _nodos(t["xs"], minimo=1)
    ys, expr = _valores_o_funcion(t["ys"], xs, "los valores f(xᵢ)")
    texto_d = (t.get("dys") or "").strip()
    dexpr = None
    if texto_d:
        dys, dexpr = _valores_o_funcion(texto_d, xs, "las derivadas f'(xᵢ)")
    elif expr is not None:
        dexpr = derivada(expr)   # Si diste f(x) y no las derivadas, se calculan solas.
        dys = [compilar(dexpr)(x) for x in xs]
    else:
        raise ValueError("Escribe las derivadas f'(xᵢ), o da f(x) como función para calcularlas solas.")
    if len(xs) > 8:
        raise ValueError("Hermite con más de 8 nodos da un polinomio de grado > 15; usa como máximo 8 nodos.")
    z, Q, df = tabla_hermite(xs, ys, dys)
    H = polinomio_hermite(z, Q)
    H_exp = sp.expand(H)
    Hf = compilar(H_exp)
    x = n.get("x")
    x = None if x is None else float(x)
    valor = Hf(x) if x is not None else float("nan")
    kpis = [_kpi_valor(f"H({txt_num(x, 4)})" if x is not None else "Grado de H(x)",
                       txt_num(valor, 6) if x is not None else str(2 * len(xs) - 1),
                       "Valor del polinomio de Hermite en x."),
            _kpi("Grado de H(x)", str(2 * len(xs) - 1), f"{len(xs)} nodos, cada uno con f y f'")]
    real = float("nan")
    if expr is not None and x is not None:
        real = abs(compilar(expr)(x) - valor)
        kpis.append(_kpi_error("Error real", txt_sci(real), "|f(x) − H(x)|"))
    kpis.append(_kpi("Coeficiente principal", f"{Q[-1, -1]:.6g}", "Última diferencia dividida Q₂ₙ₊₁,₂ₙ₊₁",
                     clave="kpi_estado_ok"))
    ctx = dict(xs=xs, ys=ys, dys=dys, z=z, Q=Q, H=H, H_exp=H_exp, Hf=Hf, x=x, expr=expr, dexpr=dexpr,
               f=compilar(expr) if expr is not None else None, latex=latex_de(expr) if expr is not None else None,
               real=real, kpis=kpis, nombre_paso="Fila", entradas=dict(x=x))
    return Resultado("hermite", valor if x is not None else float("nan"), df, True, tol, nmax, "Q", ctx)


# ----------------------------------------------------------------------------- derivación
def _ej_derivacion(id_metodo):
    def ejecutor(t, n, tol, nmax):
        expr = parsear(t["f"])
        f = compilar(expr)
        x0, h = float(n["x0"]), float(n["h"])
        if h == 0:
            raise ValueError("h no puede ser cero.")
        pasos = _entero(n["pasos"], "El número de valores de h", 1, 30)
        opcion = (t.get("formula") or "").lower()
        if id_metodo == "derivada_2p":
            clave = "2_atras" if "atr" in opcion else "2_adelante"
        else:
            clave = "5_extremo" if "extremo" in opcion else "5_centrada"
        dexpr = derivada(expr)
        exacta = compilar(dexpr)(x0)
        exacta = exacta if np.isfinite(exacta) else None
        aprox, df = derivacion(f, x0, h, pasos, clave, exacta)
        num = df.drop(columns=["razón"], errors="ignore").select_dtypes(include=[np.number])
        if not np.all(np.isfinite(num.to_numpy())):
            raise ValueError("f no está definida en alguno de los puntos que usa la fórmula; prueba otro x₀ o un h más chico.")
        orden = FORMULAS[clave][3]
        # Cota teórica del error con la derivada que corresponde (f'' para 2 puntos, f⁽⁵⁾ para 5 puntos).
        orden_deriv = orden + 1
        dd = sp.diff(expr, X, orden_deriv)
        h_fin = h / 2 ** (pasos - 1)
        desplaz = FORMULAS[clave][0]
        lo, hi = x0 + min(desplaz) * h_fin, x0 + max(desplaz) * h_fin
        M = _max_abs(dd, lo, hi)
        constante = {"2_adelante": 1 / 2, "2_atras": 1 / 2, "5_centrada": 1 / 30, "5_extremo": 1 / 5}[clave]
        cota = constante * abs(h_fin) ** orden * M
        kpis = [_kpi_valor(f"f'({txt_num(x0, 4)}) ≈", txt_num(aprox, 8), f"Con h = {h_fin:g}"),
                _kpi("Valor exacto", txt_num(exacta, 8) if exacta is not None else "—",
                     f"f'(x) = {sp.sstr(dexpr)} (derivada simbólica)"),
                _kpi_error("Error real", txt_sci(abs(aprox - exacta)) if exacta is not None else "—",
                           f"Cota teórica: {cota:.3e}" if np.isfinite(cota) else None),
                _kpi("Orden del error", f"O(h{'⁴' if orden == 4 else ''})",
                     f"Al dividir h entre 2, el error se divide ≈ entre {2 ** orden}.", clave="kpi_estado_ok")]
        ctx = dict(expr=expr, f=f, dexpr=dexpr, latex=latex_de(expr), latex_d=latex_de(dexpr), x0=x0, h=h,
                   clave=clave, exacta=exacta, orden=orden, cota=cota, M=M, orden_deriv=orden_deriv,
                   constante=constante, kpis=kpis, nombre_paso="Paso", entradas=dict(x0=x0, h=h))
        return Resultado(id_metodo, aprox, df, True, tol, nmax, "aproximación", ctx)
    return ejecutor


# ----------------------------------------------------------------------------- integración simple
def _ej_regla(id_metodo, regla):
    def ejecutor(t, n, tol, nmax):
        expr = parsear(t["f"])
        f = compilar(expr)
        a, b = float(n["a"]), float(n["b"])
        if a == b:
            raise ValueError("Los límites a y b deben ser distintos.")
        m = _entero(n["n"], "El número de subintervalos n", 1, 300)
        valor, df = regla_compuesta(f, a, b, m, regla)
        h = (b - a) / m
        ref = _integral_referencia(expr, a, b)
        if regla == "trapecio":
            dd, const, pot, nombre_d = sp.diff(expr, X, 2), 1 / 12, 2, "f''"
        else:
            dd, const, pot, nombre_d = sp.diff(expr, X, 4), 1 / 80, 4, "f⁽⁴⁾"
        M = _max_abs(dd, a, b)
        cota = const * abs(b - a) * abs(h) ** pot * M
        kpis = [_kpi_valor("Integral aproximada", txt_num(valor, 8), f"n = {m}, h = {h:g}"),
                _kpi("Valor de referencia", txt_num(ref, 8) if ref == ref else "—",
                     "Cuadratura de alta precisión (mpmath), solo para comparar."),
                _kpi_error("Error real", txt_sci(abs(valor - ref)) if ref == ref else "—",
                           f"Cota teórica: {cota:.3e}" if np.isfinite(cota) else None),
                _kpi("Cota del error", txt_sci(cota) if np.isfinite(cota) else "—",
                     f"(b−a)·h^{pot}·max|{nombre_d}| / {int(1 / const)}", clave="kpi_estado_ok")]
        ctx = dict(expr=expr, f=f, latex=latex_de(expr), a=a, b=b, n=m, h=h, ref=ref, cota=cota, M=M,
                   regla=regla, kpis=kpis, nombre_paso="Nodo", entradas=dict(a=a, b=b))
        return Resultado(id_metodo, valor, df, True, tol, nmax, "suma acumulada", ctx)
    return ejecutor


def _ej_adaptativa(t, n, tol, nmax):
    expr = parsear(t["f"])
    f = compilar(expr)
    a, b = float(n["a"]), float(n["b"])
    if not a < b:
        raise ValueError("El límite a debe ser menor que b.")
    valor, df, ok = cuadratura_adaptativa(f, a, b, tol, max_nivel=nmax)
    ref = _integral_referencia(expr, a, b)
    aceptados = df[df["decisión"] != "divide"]
    kpis = [_kpi_valor("Integral aproximada", txt_num(valor, 10), f"Tolerancia: {txt_sci(tol, 0)}"),
            _kpi("Subintervalos usados", str(len(aceptados)), f"{len(df)} revisados, nivel máximo {int(df['nivel'].max())}"),
            _kpi_error("Error real", txt_sci(abs(valor - ref)) if ref == ref else "—",
                       f"Referencia (mpmath): {ref:.12g}" if ref == ref else None),
            ("kpi_estado_ok" if ok else "kpi_estado_mal", "Estado", "Cumplió" if ok else "Tope de niveles",
             "Todos los subintervalos cumplieron la tolerancia." if ok else
             "Algunos subintervalos se aceptaron por llegar al nivel máximo sin cumplir la tolerancia.")]
    ctx = dict(expr=expr, f=f, latex=latex_de(expr), a=a, b=b, ref=ref, kpis=kpis, nombre_paso="Paso",
               entradas=dict(a=a, b=b))
    if not ok:
        ctx["aviso"] = (f"Algunos subintervalos llegaron al nivel máximo ({nmax}) sin cumplir la tolerancia y se "
                        "aceptaron así. Sube «Máx. niveles» o relaja la tolerancia.")
    return Resultado("adaptativa", valor, df, ok, tol, nmax, "S(a,m)+S(m,b)", ctx)


# ----------------------------------------------------------------------------- integración doble
def _referencia_doble(expr, a, b, cexpr, dexpr):
    try:
        mpmath.mp.dps = 15
        f = sp.lambdify((X, Y), expr, modules=["mpmath"])
        c = sp.lambdify(X, cexpr, modules=["mpmath"])
        d = sp.lambdify(X, dexpr, modules=["mpmath"])
        v = float(mpmath.quad(lambda x: mpmath.quad(lambda y: f(x, y), [c(x), d(x)]), [a, b]))
        return v if math.isfinite(v) else float("nan")
    except Exception:
        return float("nan")


def _ej_doble(id_metodo, regla):
    def ejecutor(t, n, tol, nmax):
        expr = parsear(t["f"], variables=("x", "y"))
        cexpr, dexpr = parsear(t["c"]), parsear(t["d"])
        f, c, d = compilar_xy(expr), compilar(cexpr), compilar(dexpr)
        a, b = float(n["a"]), float(n["b"])
        if a == b:
            raise ValueError("Los límites a y b deben ser distintos.")
        nx = _entero(n["n"], "n (subintervalos en x)", 1, 60)
        my = _entero(n["m"], "m (subintervalos en y)", 1, 60)
        valor, df, detalle = integral_doble(f, a, b, c, d, nx, my, regla)
        ref = _referencia_doble(expr, a, b, cexpr, dexpr)
        kpis = [_kpi_valor("Integral doble aproximada", txt_num(valor, 8), f"n = {nx}, m = {my}"),
                _kpi("Valor de referencia", txt_num(ref, 8) if ref == ref else "—", "Cuadratura de alta precisión (mpmath)."),
                _kpi_error("Error real", txt_sci(abs(valor - ref)) if ref == ref else "—"),
                _kpi("Evaluaciones de f", str((nx + 1) * (my + 1)), "(n + 1)(m + 1) nodos", clave="kpi_estado_ok")]
        ctx = dict(expr=expr, f=f, c=c, d=d, cexpr=cexpr, dexpr=dexpr, latex=latex_de(expr),
                   latex_c=latex_de(cexpr), latex_d=latex_de(dexpr), a=a, b=b, n=nx, m=my, h=(b - a) / nx,
                   detalle=detalle, ref=ref, regla=regla, kpis=kpis, nombre_paso="Nodo xᵢ", entradas=dict(a=a, b=b))
        return Resultado(id_metodo, valor, df, True, tol, nmax, "Jᵢ", ctx)
    return ejecutor


EJECUTORES_DIRECTOS = {
    "punto_flotante": _ej_punto_flotante_dispatch,
    "neville": _ej_neville,
    "hermite": _ej_hermite,
    "derivada_2p": _ej_derivacion("derivada_2p"),
    "derivada_5p": _ej_derivacion("derivada_5p"),
    "trapecio": _ej_regla("trapecio", "trapecio"),
    "simpson38": _ej_regla("simpson38", "simpson38"),
    "adaptativa": _ej_adaptativa,
    "doble_trapecio": _ej_doble("doble_trapecio", "trapecio"),
    "doble_simpson38": _ej_doble("doble_simpson38", "simpson38"),
}

# Ids de los métodos directos (la interfaz los usa para mostrar sus propias tarjetas y textos).
DIRECTOS = set(EJECUTORES_DIRECTOS) | {"punto_flotante_inv"}
_ = ErrorExpresion   # Se re-exporta para que quien importe este módulo tenga a mano la excepción del parser.
