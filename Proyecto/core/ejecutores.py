# Ejecutores: aquí se conecta todo el camino  texto del usuario -> parser -> método numérico -> Resultado.
# Aquí NO hay nada de Streamlit, por eso se puede probar con unittest sin abrir la app.
# Cada ejecutor valida datos, llama al método de `core/metodos/` (sin cambiar su matemática) y deja la tabla
# de iteraciones "limpia": columna `iter`, y errores numéricos con NaN en la primera fila (nunca el texto "-").
from __future__ import annotations

from dataclasses import dataclass, field  # dataclass crea clases "de datos" sin escribir __init__ a mano.

import numpy as np
import pandas as pd

from .metodos.aceleracion_aitken import aceleracion_aitken
from .metodos.biseccion import biseccion
from .metodos.deflacion import deflacion
from .metodos.falsa_posicion import falsa_posicion
from .metodos.muller import muller
from .metodos.newton_raphson import raiz_newton
from .metodos.punto_fijo import punto_fijo_validado
from .metodos.secante import secante
from .parser import coeficientes_polinomio, compilar, derivada, latex_de, parsear


class ErrorNumerico(ValueError):
    """El cálculo produjo valores no finitos (NaN o infinito)."""


@dataclass
class Resultado:
    # Aquí se guarda TODO lo que sale de un método en un solo objeto, para pasarlo fácil a tabla, gráfica y procedimiento.
    id: str                    # Identificador del método ("biseccion", "newton", ...).
    valor: object              # La solución: número, complejo o lista de raíces (deflación).
    df: pd.DataFrame           # Tabla de iteraciones (una fila por iteración).
    converged: bool            # ¿Se alcanzó la tolerancia?
    tol: float                 # Tolerancia que pidió el usuario.
    n_max: int                 # Máximo de iteraciones permitido.
    col_x: str                 # Columna de la tabla que guarda la aproximación de cada iteración.
    ctx: dict = field(default_factory=dict)  # Extras (función compilada, LaTeX, datos de entrada...) que usan la gráfica y el procedimiento.

    @property
    def n_filas(self) -> int:
        """Pasos navegables (filas de la tabla). En deflación es una etapa por raíz."""
        return int(len(self.df))

    @property
    def n_iter(self) -> int:
        # Deflación suma las iteraciones de Newton de todas sus etapas; en los demás es el número de filas.
        return int(self.ctx.get("iter_total", len(self.df)))

    @property
    def error_final(self) -> float:
        if "error_final" in self.ctx:
            return float(self.ctx["error_final"])
        if "error" in self.df.columns and len(self.df):
            v = self.df["error"].iloc[-1]
            return float(v) if pd.notna(v) else float("nan")
        return float("nan")


def indice_convergencia(res: Resultado):
    """Posición (empezando en 0) de la primera iteración que alcanza la tolerancia, o None."""
    # Deflación no tiene una "iteración de convergencia" única, y si no convergió tampoco la hay.
    if res.id == "deflacion" or "error" not in res.df.columns or not res.converged:
        return None
    for i, e in enumerate(res.df["error"].to_numpy()):
        if pd.notna(e) and e <= res.tol:
            return i
    return len(res.df) - 1 if res.converged else None


# ----------------------------------------------------------------------------- utilidades
def _a_numerico(serie: pd.Series) -> pd.Series:
    # Aquí se intenta convertir la columna a números porque los métodos a veces guardan texto ("-") o complejos mezclados.
    try:
        return pd.to_numeric(serie)
    except (ValueError, TypeError):
        pass
    try:
        z = serie.astype(complex)
        # Si todas las partes imaginarias son cero se deja como real, para que la tabla no muestre "+0.000i" por todos lados.
        return z.astype(float) if np.all(z.to_numpy().imag == 0) else z
    except (ValueError, TypeError):
        return serie


def _normalizar(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy().reset_index(drop=True)
    df = df.rename(columns={"Error": "error"})  # Punto fijo usaba "Error" con mayúscula; se unifica con los demás.
    for col in df.columns:
        if df[col].dtype == object:
            # El "-" que ponían algunos métodos en la primera fila se cambia por NaN (que sí es número).
            df[col] = df[col].where(df[col] != "-", np.nan)
            df[col] = _a_numerico(df[col])
    if "iter" not in df.columns:
        df.insert(0, "iter", range(1, len(df) + 1))
    return df


def _finalizar(df: pd.DataFrame) -> pd.DataFrame:
    df = _normalizar(df)
    num = df.select_dtypes(include=[np.number])
    # Los errores pueden tener NaN legítimo (primera fila), así que se excluyen de la revisión de valores raros.
    num = num.drop(columns=[c for c in num.columns if str(c).startswith("error")])
    if num.size and not np.isfinite(num.to_numpy()).all():
        raise ErrorNumerico(
            "El cálculo produjo valores no finitos (NaN o ∞). Revisa que la función esté definida "
            "en los puntos que usa el método y prueba con otros valores iniciales."
        )
    return df


def _ctx(expr, f, **extra) -> dict:
    # Datos comunes que casi todos los métodos le pasan a la gráfica y al procedimiento.
    return dict(expr=expr, latex=latex_de(expr), f=f, **extra)


# ----------------------------------------------------------------------------- ejecutores
def _ej_cerrado(metodo_id, funcion):
    # Bisección y regla falsa se ejecutan igual (mismas entradas y salidas), por eso comparten esta "fábrica".
    def ejecutor(t, n, tol, nmax):
        expr = parsear(t["f"])
        f = compilar(expr)
        a, b = float(n["a"]), float(n["b"])
        if not a < b:
            raise ValueError("El límite a debe ser menor que el límite b.")
        raiz, df = funcion(f, a, b, tol, nmax)
        df = _finalizar(df)
        ult = df.iloc[-1]
        # Convergió si la última f(c) es casi cero, o si el error de la última fila ya cumple la tolerancia.
        conv = bool(abs(ult["f(c)"]) < 1e-14 or (len(df) > 1 and ult["error"] <= tol))
        return Resultado(metodo_id, raiz, df, conv, tol, nmax, "c",
                         _ctx(expr, f, a0=a, b0=b, entradas=dict(a=a, b=b)))
    return ejecutor


def _ej_newton(t, n, tol, nmax):
    expr = parsear(t["f"])
    f = compilar(expr)
    dexpr = derivada(expr)   # La derivada se calcula sola; el usuario solo escribe f(x).
    fp = compilar(dexpr)
    x0 = float(n["x0"])
    raiz, df = raiz_newton(f, fp, x0, tol, nmax)
    if df.empty:  # x0 ya era raíz: se arma una fila para que la tabla no quede vacía.
        df = pd.DataFrame([{"x": x0, "f(x)": 0.0, "x1": x0, "f'(x)": fp(x0), "error": 0.0, "error relativo": 0.0}])
    df = _finalizar(df)
    return Resultado("newton", raiz, df, True, tol, nmax, "x1",
                     _ctx(expr, f, fp=fp, dexpr=dexpr, latex_fp=latex_de(dexpr), entradas=dict(x0=x0)))


def _ej_secante(t, n, tol, nmax):
    expr = parsear(t["f"])
    f = compilar(expr)
    x0, x1 = float(n["x0"]), float(n["x1"])
    if x0 == x1:
        raise ValueError("x₀ y x₁ deben ser distintos.")
    raiz, df = secante(f, x0, x1, tol, nmax)
    if df.empty:  # Alguno de los dos puntos iniciales ya era raíz.
        df = pd.DataFrame([{"x_0": x0, "x_1": x1, "x_2": raiz, "f(x_0)": f(x0), "f(x_1)": f(x1),
                            "f(x_2)": f(raiz), "error": 0.0, "error relativo": 0.0}])
        conv = True
    else:
        df = _finalizar(df)
        conv = bool(len(df) > 1 and df["error"].iloc[-1] <= tol)
    return Resultado("secante", raiz, df, conv, tol, nmax, "x_2",
                     _ctx(expr, f, entradas=dict(x0=x0, x1=x1)))


def _ej_punto_fijo(t, n, tol, nmax):
    expr = parsear(t["g"])
    g = compilar(expr)
    dexpr = derivada(expr)   # g'(x) se necesita para comprobar que |g'(x0)| < 1.
    gp = compilar(dexpr)
    x0 = float(n["x0"])
    raiz, df = punto_fijo_validado(x0, g, gp, tol, nmax)
    df = _finalizar(df)
    return Resultado("punto_fijo", raiz, df, True, tol, nmax, "x1",
                     _ctx(expr, g, g=g, gp=gp, dexpr=dexpr, latex_gp=latex_de(dexpr), entradas=dict(x0=x0)))


def _ej_aitken(t, n, tol, nmax):
    expr = parsear(t["g"])
    g = compilar(expr)
    x0 = float(n["x0"])
    # Primero se genera la sucesión de punto fijo completa (x0, g(x0), g(g(x0)), ...) porque Aitken usa tres términos seguidos.
    xs = [x0]
    for _ in range(nmax + 2):
        xs.append(g(xs[-1]))

    filas, previo, conv = [], None, False
    for k in range(nmax):
        a_, b_, c_ = xs[k:k + 3]
        try:
            acel = aceleracion_aitken(a_, b_, c_)
        except ValueError:
            # Si el denominador es casi cero porque la sucesión ya no cambia, es que ya convergió; si no, es un error real.
            if abs(c_ - b_) <= tol:
                acel = c_
            else:
                raise
        err = np.nan if previo is None else abs(acel - previo)
        filas.append({"iter": k + 1, "x_n": a_, "x_n+1": b_, "x_n+2": c_, "aitken": acel, "error": err})
        if previo is not None and err <= tol:
            conv = True
            break
        previo = acel
    df = _finalizar(pd.DataFrame(filas))
    return Resultado("aitken", df["aitken"].iloc[-1], df, conv, tol, nmax, "aitken",
                     _ctx(expr, g, g=g, entradas=dict(x0=x0)))


def _ej_deflacion(t, n, tol, nmax):
    expr = parsear(t["p"])
    coefs = coeficientes_polinomio(expr)   # Esto también valida que de verdad sea un polinomio.
    x0 = float(n["x0"])
    raices, df = deflacion(expr, x0, tol, nmax)
    df = df.rename(columns={"etapa": "iter"}).reset_index(drop=True)  # "iter" para que la tabla y el slider funcionen igual que en los demás.
    return Resultado("deflacion", list(raices), df, True, tol, nmax, "raiz",
                     _ctx(expr, compilar(expr), coefs=coefs, entradas=dict(x0=x0),
                          iter_total=int(df["iteraciones"].sum()), error_final=float(df["error"].max())))


def _ej_muller(t, n, tol, nmax):
    expr = parsear(t["f"])
    f_cx = compilar(expr, complejo=True)   # Müller necesita evaluar con complejos.
    p0, p1, p2 = float(n["p0"]), float(n["p1"]), float(n["p2"])
    if len({p0, p1, p2}) < 3:
        raise ValueError("Los tres puntos iniciales P₀, P₁ y P₂ deben ser distintos.")
    raiz, df = muller(f_cx, p0, p1, p2, tol, nmax)
    df = _finalizar(df)
    valor = complex(raiz)
    # Si la parte imaginaria es solo "ruido" numérico, se muestra el resultado como real.
    if abs(valor.imag) <= 1e-12 * max(1.0, abs(valor.real)):
        valor = valor.real
    return Resultado("muller", valor, df, True, tol, nmax, "P3",
                     _ctx(expr, compilar(expr), f_cx=f_cx, entradas=dict(p0=p0, p1=p1, p2=p2)))


# Aquí se registra cada método con su ejecutor. Para agregar uno nuevo: escribe su función arriba y pon una línea aquí.
EJECUTORES = {
    "biseccion": _ej_cerrado("biseccion", biseccion),
    "falsa_posicion": _ej_cerrado("falsa_posicion", falsa_posicion),
    "newton": _ej_newton,
    "secante": _ej_secante,
    "punto_fijo": _ej_punto_fijo,
    "aitken": _ej_aitken,
    "deflacion": _ej_deflacion,
    "muller": _ej_muller,
}


def ejecutar(metodo: str, textos: dict, numeros: dict, tol: float, n_max: int) -> Resultado:
    # Punto único de entrada para la interfaz: así la app no necesita saber nada de cada método.
    return EJECUTORES[metodo](textos, numeros, tol, n_max)


def residuo_absoluto(res: Resultado) -> float:
    """|f(x*)| (o |g(x*) − x*| en punto fijo y Aitken) para comprobar qué tan buena es la solución."""
    v = res.valor
    try:
        if res.id in ("punto_fijo", "aitken"):
            return float(abs(res.ctx["g"](v) - v))
        if res.id == "muller":
            return float(abs(res.ctx["f_cx"](v)))
        if res.id == "deflacion":
            return float(max(abs(res.ctx["f"](r)) for r in v))
        return float(abs(res.ctx["f"](v)))
    except Exception:  # Aquí se atrapa todo porque esto es solo un dato de apoyo y nunca debe tirar la app.
        return float("nan")
