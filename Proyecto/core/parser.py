# Parser matemático: convierte lo que escribe el usuario ("x^2 + 3x") en una expresión que Python puede calcular.
# Aquí se usa SymPy (y no eval a secas) porque permite validar la entrada y derivar de forma simbólica.
from __future__ import annotations

import re  # re = expresiones regulares; sirve para buscar patrones raros en el texto antes de evaluarlo.

import numpy as np  # numpy evalúa la función en muchos puntos a la vez (necesario para dibujar la curva).
import sympy as sp  # sympy es álgebra simbólica: entiende "x**2" como objeto matemático, no solo como texto.
from sympy.core.function import AppliedUndef  # Representa una función desconocida como foo(x); se usa para detectarlas y avisar.
from sympy.parsing.sympy_parser import (
    convert_xor,                            # Convierte ^ en ** (potencia), como se escribe en papel.
    implicit_multiplication_application,    # Permite 2x o 3sin(x) sin escribir el *.
    parse_expr,                             # Lee el texto y lo vuelve una expresión de SymPy.
    standard_transformations,               # Reglas básicas de lectura (números, símbolos, etc.).
)

# Aquí se define x una sola vez porque todo el programa trabaja con una única variable.
X = sp.Symbol("x")
Y = sp.Symbol("y")   # Segunda variable: solo se acepta en las integrales dobles, f(x, y).
MAX_LONGITUD = 200  # Un tope de longitud evita que alguien pegue un texto enorme que trabe la app.


class ErrorExpresion(ValueError):
    """La expresión escrita por el usuario no es válida (la interfaz la muestra como error de sintaxis)."""


# Lista cerrada de funciones permitidas. Se usa un diccionario cerrado porque así el parser SOLO conoce estas
# funciones y no puede ejecutar nada más (seguridad).
_FUNCIONES = {
    "sin": sp.sin, "sen": sp.sin, "cos": sp.cos, "tan": sp.tan, "tg": sp.tan,
    "sec": sp.sec, "csc": sp.csc, "cot": sp.cot,
    "asin": sp.asin, "arcsin": sp.asin, "acos": sp.acos, "arccos": sp.acos,
    "atan": sp.atan, "arctan": sp.atan,
    "sinh": sp.sinh, "senh": sp.sinh, "cosh": sp.cosh, "tanh": sp.tanh,
    "exp": sp.exp, "log": sp.log, "ln": sp.log,
    "log10": lambda u: sp.log(u, 10), "log2": lambda u: sp.log(u, 2),
    "sqrt": sp.sqrt, "raiz": sp.sqrt, "cbrt": sp.cbrt, "abs": sp.Abs,
}
# Aquí se juntan funciones, la variable y las constantes (pi, e) que el usuario puede escribir.
_LOCAL = {**_FUNCIONES, "x": X, "X": X, "pi": sp.pi, "e": sp.E}
# __builtins__ vacío porque así el texto no tiene acceso a open(), import, etc.; solo a lo que le damos.
_GLOBAL = {
    "__builtins__": {},
    "Integer": sp.Integer, "Float": sp.Float, "Rational": sp.Rational,
    "Symbol": sp.Symbol, "Function": sp.Function,
}
_TRANSFORMACIONES = standard_transformations + (implicit_multiplication_application, convert_xor)

# Símbolos "bonitos" que se cambian por su equivalente de Python antes de leer la expresión.
_SUSTITUCIONES = {"²": "**2", "³": "**3", "·": "*", "×": "*", "÷": "/", "−": "-", "π": "pi"}
_CARACTERES_VALIDOS = re.compile(r"^[0-9A-Za-z+\-*/^().,\s]*$")  # Solo estos caracteres pasan; todo lo demás se rechaza.
_ATRIBUTO = re.compile(r"[A-Za-z_\)]\s*\.\s*[A-Za-z_]")          # Detecta cosas como x.__class__ (acceso a atributos).


def _normalizar(texto: str) -> str:
    for viejo, nuevo in _SUSTITUCIONES.items():
        texto = texto.replace(viejo, nuevo)
    # Aquí se inserta el * porque SymPy leería "x(x+1)" como una función llamada x, no como x multiplicado por (x+1).
    texto = re.sub(r"\b([xXyY])\s*\(", lambda m: m.group(1).lower() + "*(", texto)
    return texto.strip()


def _validar(texto: str, local: dict | None = None) -> None:
    local = _LOCAL if local is None else local
    if not texto:
        raise ErrorExpresion("Escribe una expresión. Ejemplo: x**3 - 2*x - 5")
    if len(texto) > MAX_LONGITUD:
        raise ErrorExpresion(f"La expresión es demasiado larga (máximo {MAX_LONGITUD} caracteres).")
    if not _CARACTERES_VALIDOS.match(texto):
        malos = sorted({c for c in texto if not re.match(r"[0-9A-Za-z+\-*/^().,\s]", c)})
        raise ErrorExpresion(
            "Hay caracteres que no se pueden usar: " + " ".join(f"«{c}»" for c in malos)
            + ". Usa solo números, la variable x, operadores + - * / ^ y funciones como sin(x)."
            + (" Para el valor absoluto usa abs(x)." if "|" in malos else "")
        )
    if "__" in texto or _ATRIBUTO.search(texto):
        raise ErrorExpresion("La expresión contiene una construcción no permitida.")
    # Aquí se avisa antes de que SymPy falle, porque un nombre como "foo(" daría un mensaje confuso.
    for nombre in re.findall(r"([A-Za-z_][A-Za-z0-9_]*)\s*\(", texto):
        if nombre not in local:
            raise ErrorExpresion(
                f"No conozco la función «{nombre}». Disponibles: sin, cos, tan, exp, log, ln, sqrt, abs, entre otras."
            )
    # Se cuentan los paréntesis a mano para dar un mensaje claro de cuál falta.
    nivel = 0
    for c in texto:
        nivel += (c == "(") - (c == ")")
        if nivel < 0:
            raise ErrorExpresion("Hay un paréntesis de cierre «)» sin su paréntesis de apertura.")
    if nivel > 0:
        raise ErrorExpresion("Falta cerrar un paréntesis: hay más «(» que «)».")


def parsear(texto: str, variables: tuple[str, ...] = ("x",)) -> sp.Expr:
    """Convierte texto en una expresión SymPy en la variable x (o en x, y), o lanza ErrorExpresion."""
    original = (texto or "").strip()
    texto = _normalizar(original)
    # Aquí se arma el diccionario de nombres conocidos según las variables permitidas (x sola, o x y y).
    local = dict(_LOCAL)
    if "y" in variables:
        local.update({"y": Y, "Y": Y})
    _validar(texto, local)
    try:
        # Ya con el texto validado se lee con los diccionarios cerrados de arriba.
        expr = parse_expr(
            texto, local_dict=local, global_dict=dict(_GLOBAL),
            transformations=_TRANSFORMACIONES,
        )
    except Exception as exc:  # Aquí se atrapa todo porque SymPy lanza muchos tipos de error distintos para una mala sintaxis.
        raise ErrorExpresion(
            f"No pude interpretar «{original}». Revisa que no falten operadores, "
            "paréntesis o argumentos (por ejemplo, un «+» al final)."
        ) from exc

    if not isinstance(expr, sp.Expr):
        raise ErrorExpresion(f"«{original}» no es una expresión matemática válida (¿usaste comas o «=»?).")

    indefinidas = sorted({str(f.func) for f in expr.atoms(AppliedUndef)})
    if indefinidas:
        raise ErrorExpresion(
            "No conozco la función: " + ", ".join(indefinidas)
            + ". Funciones disponibles: sin, cos, tan, exp, log, ln, sqrt, abs, entre otras."
        )
    # Si quedó algún símbolo distinto de x (por ejemplo "sinx" se lee como s*i*n*x), se avisa en lugar de calcular algo raro.
    permitidas = {X} | ({Y} if "y" in variables else set())
    extra = sorted(str(s) for s in expr.free_symbols if s not in permitidas)
    if extra:
        nombres = " y ".join(variables)
        raise ErrorExpresion(
            f"Solo se admite{'n las variables' if len(variables) > 1 else ' la variable'} {nombres}; encontré: "
            + ", ".join(extra)
            + ". Revisa los nombres de las funciones (por ejemplo sin(x), no sinx)."
        )
    if expr.has(sp.I) or expr.has(sp.zoo) or expr.has(sp.nan) or expr.has(sp.oo):
        raise ErrorExpresion("La expresión no está definida o contiene números complejos / infinitos.")
    return expr


def derivada(expr: sp.Expr) -> sp.Expr:
    # Aquí se deriva de forma simbólica (exacta) porque Newton y Punto Fijo necesitan f'(x) sin que el usuario la escriba.
    return sp.diff(expr, X)


def latex_de(expr: sp.Expr) -> str:
    # ln_notation=True para que el logaritmo natural se muestre como "ln" (como en los libros) y no como "log".
    return sp.latex(expr, ln_notation=True)


def compilar(expr: sp.Expr, complejo: bool = False):
    """Devuelve una función numérica rápida.

    - Real (por defecto): usa numpy; acepta números sueltos o arreglos y devuelve `float` si recibe un número.
    - Complejo (para Müller): evalúa siempre con complejos, así sqrt(-4) da 2i y no NaN.
    """
    if complejo:
        # lambdify convierte la expresión de SymPy en una función normal de Python; con "numpy" usa funciones vectorizadas.
        f_cx = sp.lambdify(X, expr, modules=["numpy"])

        def f_complejo(valor):
            # errstate silencia avisos de numpy (división entre cero) porque ya los manejamos revisando NaN/∞ al final.
            with np.errstate(all="ignore"):
                return f_cx(complex(valor))

        return f_complejo

    f_num = sp.lambdify(X, expr, modules=["numpy"])

    def f(valor):
        escalar = np.ndim(valor) == 0  # ndim == 0 significa "es un número suelto, no un arreglo".
        arr = np.asarray(valor, dtype=float)
        with np.errstate(all="ignore"):
            # broadcast_to cubre el caso de una función constante (f(x)=3), que devuelve un solo valor en vez de un arreglo.
            res = np.broadcast_to(f_num(arr), arr.shape).astype(float)
        return float(res) if escalar else res  # float() para que los métodos reciban números normales, no arreglos de 0 dimensiones.

    return f


def coeficientes_polinomio(expr: sp.Expr) -> list[float]:
    """Coeficientes (de mayor a menor grado) si `expr` es un polinomio de grado >= 1."""
    try:
        # Poly sirve para comprobar que de verdad es un polinomio y sacar sus coeficientes (los necesita la deflación).
        poli = sp.Poly(expr, X)
        coefs = [float(c) for c in poli.all_coeffs()]
    except (sp.PolynomialError, TypeError, ValueError) as exc:
        raise ErrorExpresion(
            "La expresión no es un polinomio en x. Ejemplo: x**3 - 6*x**2 + 11*x - 6"
        ) from exc
    if poli.degree() < 1:
        raise ErrorExpresion("El polinomio debe tener grado 1 o mayor.")
    return coefs


def parsear_funcion(texto: str):
    """Compatibilidad con tu `utils.parsear_funcion` original: devuelve (f_numérica, latex)."""
    expr = parsear(texto)
    return compilar(expr), latex_de(expr)


# ----------------------------------------------------------------------------- funciones de dos variables
def compilar_xy(expr: sp.Expr):
    """f(x, y) numérica (para las integrales dobles). Acepta números o arreglos del mismo tamaño."""
    f_num = sp.lambdify((X, Y), expr, modules=["numpy"])

    def f(x, y):
        escalar = np.ndim(x) == 0 and np.ndim(y) == 0
        xa, ya = np.broadcast_arrays(np.asarray(x, dtype=float), np.asarray(y, dtype=float))
        with np.errstate(all="ignore"):
            res = np.broadcast_to(f_num(xa, ya), xa.shape).astype(float)
        return float(res) if escalar else res

    return f


# ----------------------------------------------------------------------------- listas de números
def parsear_numero(texto: str) -> float:
    """Un número escrito por el usuario; acepta expresiones constantes como pi/4, 1/3 o sqrt(2)."""
    expr = parsear(texto)
    if expr.free_symbols:
        raise ErrorExpresion(f"«{texto.strip()}» debe ser un número, no una función de x.")
    valor = float(expr.evalf())
    if not np.isfinite(valor):
        raise ErrorExpresion(f"«{texto.strip()}» no es un número finito.")
    return valor


def parsear_lista(texto: str, nombre: str = "la lista") -> list[float]:
    """Lista de números separados por comas, punto y coma o espacios: «1, 2.5, pi/2»."""
    texto = (texto or "").strip()
    # Con comas o punto y coma se separa solo por ellos (así «2 pi» sigue siendo un número); si no, por espacios.
    separador = r"[;,]" if re.search(r"[;,]", texto) else r"\s+"
    piezas = [p.strip() for p in re.split(separador, texto) if p.strip()]
    if not piezas:
        raise ErrorExpresion(f"Escribe {nombre}: números separados por comas, por ejemplo 1, 1.3, 1.6.")
    if len(piezas) > 30:
        raise ErrorExpresion(f"{nombre.capitalize()} tiene demasiados valores (máximo 30).")
    valores = []
    for p in piezas:
        try:
            valores.append(parsear_numero(p))
        except ErrorExpresion as exc:
            raise ErrorExpresion(f"En {nombre}: «{p}» no es un número válido. Separa los valores con comas.") from exc
    return valores


def es_lista(texto: str) -> bool:
    """True si el texto parece una lista de números (y no una función de x)."""
    try:
        parsear_lista(texto)
        return True
    except ErrorExpresion:
        return False
