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
        for extremo, nombre in ((a, "a"), (b, "b")):
            if not np.isfinite(f(extremo)):
                raise ErrorNumerico(f"f no está definida en el extremo {nombre} = {extremo:g}; elige un intervalo donde f exista.")
        raiz, df = funcion(f, a, b, tol, nmax)
        malos = df[~np.isfinite(df["f(c)"].astype(float))]
        if len(malos):
            # El punto c cayó justo donde f no existe: casi siempre es una asíntota (polo) dentro de [a, b].
            c_malo = float(malos["c"].iloc[0])
            raise ErrorNumerico(f"En la iteración {int(malos['iter'].iloc[0])} el método cayó en c = {c_malo:.6g}, donde f no "
                                "está definida (división entre cero o asíntota). Bolzano necesita f continua en [a, b]: "
                                "si hay una asíntota en el intervalo, el cambio de signo no indica una raíz.")
        df = _finalizar(df)
        ult = df.iloc[-1]
        # Convergió si la última f(c) es casi cero, o si el error de la última fila ya cumple la tolerancia.
        conv = bool(abs(ult["f(c)"]) < 1e-14 or (len(df) > 1 and ult["error"] <= tol))
        extra = {}
        # Bolzano solo garantiza raíz si f es CONTINUA. Con un polo (1/x, tan x) el intervalo se encoge igual,
        # pero alrededor de la asíntota: |f(c)| crece en vez de bajar. Si al final |f(c)| es mayor que en los
        # extremos originales, no es una raíz: se marca como "No convergió" y se explica.
        fc_final, escala = abs(float(ult["f(c)"])), max(abs(float(df.iloc[0]["f(a)"])), abs(float(df.iloc[0]["f(b)"])), 1.0)
        if fc_final > escala:
            conv = False
            extra["aviso"] = (f"El intervalo se cerró alrededor de x ≈ {raiz:.6g}, pero ahí |f(c)| = {fc_final:.3g} es enorme: "
                              "no es una raíz, es una discontinuidad (un polo). Bolzano necesita que f sea continua "
                              "en [a, b]; elige un intervalo que no contenga asíntotas.")
        return Resultado(metodo_id, raiz, df, conv, tol, nmax, "c",
                         _ctx(expr, f, a0=a, b0=b, entradas=dict(a=a, b=b), **extra))
    return ejecutor


def _ej_newton(t, n, tol, nmax):
    expr = parsear(t["f"])
    f = compilar(expr)
    dexpr = derivada(expr)   # La derivada se calcula sola; el usuario solo escribe f(x).
    fp = compilar(dexpr)
    x0 = float(n["x0"])
    raiz, df = raiz_newton(f, fp, x0, tol, nmax, lanzar=False)
    if df.empty:  # x0 ya era raíz: se arma una fila para que la tabla no quede vacía.
        df = pd.DataFrame([{"x": x0, "f(x)": 0.0, "x1": x0, "f'(x)": fp(x0), "error": 0.0, "error relativo": 0.0}])
    df = _finalizar(df)
    # Convergió si el último error cumple la tolerancia (con nmax agotado se devuelve la tabla y se marca que no).
    conv = bool(df["error"].iloc[-1] <= tol and (len(df) > 1 or df["f(x)"].iloc[0] == 0))
    return Resultado("newton", raiz, df, conv, tol, nmax, "x1",
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
    if not np.isfinite(g(x0)):
        raise ErrorNumerico(f"g no está definida en x₀ = {x0:g}.")
    raiz, df = punto_fijo_validado(x0, g, gp, tol, nmax, estricto=False)
    df = df.replace([np.inf, -np.inf], np.nan).dropna(subset=["x1"])   # Si diverge, se quitan los valores no finitos.
    if df.empty:
        raise ErrorNumerico("La iteración produjo valores no finitos desde el primer paso; prueba con otro x₀.")
    df = _finalizar(df)
    raiz = float(df["x1"].iloc[-1])
    conv = bool(df["error"].iloc[-1] <= tol)
    extra = {}
    gp0 = abs(gp(x0))
    if gp0 >= 1:
        # Antes esto bloqueaba el cálculo. Ahora solo se avisa, porque lo que importa es |g'| cerca del punto fijo.
        extra["aviso"] = (f"|g'(x₀)| = {gp0:.4g} ≥ 1: la condición de convergencia no se cumple en x₀. "
                          + ("Aun así la iteración convergió, porque cerca del punto fijo |g'(x)| < 1."
                             if conv else "La iteración no convergió; prueba otra g(x) u otro x₀."))
    elif not conv:
        extra["aviso"] = "La iteración no alcanzó la tolerancia con las iteraciones permitidas."
    return Resultado("punto_fijo", raiz, df, conv, tol, nmax, "x1",
                     _ctx(expr, g, g=g, gp=gp, dexpr=dexpr, latex_gp=latex_de(dexpr), entradas=dict(x0=x0), **extra))


def _ej_aitken(t, n, tol, nmax):
    expr = parsear(t["g"])
    g = compilar(expr)
    x0 = float(n["x0"])
    # Primero se genera la sucesión de punto fijo completa (x0, g(x0), g(g(x0)), ...) porque Aitken usa tres términos seguidos.
    xs = [x0]
    for _ in range(nmax + 2):
        try:
            siguiente = g(xs[-1])
        except OverflowError:
            siguiente = float("inf")
        if not np.isfinite(siguiente) or abs(siguiente) > 1e150:
            # Antes aquí salía el error crudo de Python "(34, 'Numerical result out of range')".
            raise ValueError(f"La sucesión x_(k+1) = g(x_k) diverge desde x₀ = {x0:g}: sus valores crecen sin límite "
                             f"(x_{len(xs)} ya no es un número finito). Aitken solo acelera sucesiones que convergen; "
                             "prueba con otra g(x) u otro x₀.")
        xs.append(siguiente)

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
    try:
        raices, df = deflacion(expr, x0, tol, nmax)
    except RuntimeError as exc:
        raise RuntimeError(f"Newton no encontró una raíz real ({exc}) Es probable que al polinomio le queden "
                           "raíces complejas, que Newton con valores reales no puede hallar: usa el método de Müller, "
                           "que sí las encuentra.") from exc
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
    raiz, df = muller(f_cx, p0, p1, p2, tol, nmax, lanzar=False)
    df = _finalizar(df)
    conv = bool(df["error"].iloc[-1] <= tol or f_cx(raiz) == 0)
    valor = complex(raiz)
    # Si la parte imaginaria es solo "ruido" numérico, se muestra el resultado como real.
    if abs(valor.imag) <= 1e-12 * max(1.0, abs(valor.real)):
        valor = valor.real
    return Resultado("muller", valor, df, conv, tol, nmax, "P3",
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


# Los métodos directos (punto flotante, interpolación, derivación, integración) viven en su propio archivo
# para no mezclarlos con los de raíces; aquí solo se suman al mismo diccionario.
from .ejecutores_directos import EJECUTORES_DIRECTOS  # noqa: E402

EJECUTORES.update(EJECUTORES_DIRECTOS)


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
