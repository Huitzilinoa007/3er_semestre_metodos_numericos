# Registro de categorías y métodos: aquí se describe QUÉ campos pide cada método.
# Aquí se usa un registro (en lugar de escribir una página por método) porque así todos los métodos
# comparten la misma vista y agregar uno nuevo es solo describirlo.
from __future__ import annotations

from dataclasses import dataclass  # dataclass crea clases "de datos" sin escribir el __init__ a mano.


@dataclass(frozen=True)  # frozen=True para que nadie modifique un método por accidente mientras la app corre.
class Campo:
    key: str            # Nombre interno del campo (por ejemplo "a", "x0").
    label: str          # Lo que ve el usuario encima del campo.
    placeholder: str    # Texto gris de ejemplo; el campo empieza vacío (sin valores precargados).
    simbolo: str = ""   # Para campos de función: f, g o P (se usa en la vista previa LaTeX).
    ayuda: str = ""     # Texto del signo de interrogación junto al campo.


@dataclass(frozen=True)
class MetodoSpec:
    id: str                              # Identificador: debe coincidir con el de EJECUTORES, PLANES y las gráficas.
    nombre: str                          # Nombre que sale en el menú.
    categoria: str
    resumen: str                         # Una línea que explica el método (sale bajo el título).
    instruccion: str                     # Qué debe hacer el usuario (sale en la hoja en blanco).
    formula: str                         # Fórmula general en LaTeX.
    campos_texto: tuple[Campo, ...]      # Campos de función o polinomio.
    campos_num: tuple[Campo, ...]        # Campos numéricos (intervalos, valores iniciales...).
    bolzano: bool = False                # True en métodos cerrados: muestra en vivo si el intervalo cumple Bolzano.
    animacion_continua: bool = False     # True conserva la animación Plotly original (solo métodos cerrados).


RAICES = "Raíces de Ecuaciones"
INTERPOLACION = "Interpolación"
DERIVADAS = "Derivadas Numéricas"
INTEGRACION = "Integración Numérica"

# Campos de función que se repiten en varios métodos; se definen una vez para no copiarlos.
_F = Campo("f", "Función f(x)", "Ingresa tu función, ej: x**3 - 2*x - 5  o  sin(x) - x/2", "f",
           "Puedes escribir x^2 o x**2, 2x o 2*x, sen(x) o sin(x).")
_G = Campo("g", "Función de iteración g(x)", "Ingresa g(x) tal que x = g(x), ej: cos(x)  o  (x + 2)**(1/3)", "g",
           "Escribe la ecuación en la forma x = g(x) y captura solo g(x).")
_P = Campo("p", "Polinomio P(x)", "Ingresa el polinomio, ej: x**3 - 6*x**2 + 11*x - 6", "P",
           "Debe ser un polinomio en x, con coeficientes numéricos.")

# Métodos que YA tienen lógica. Para agregar uno nuevo, copia un bloque MetodoSpec y cambia sus datos.
METODOS: dict[str, MetodoSpec] = {m.id: m for m in (
    MetodoSpec(
        "biseccion", "Bisección", RAICES,
        "Divide el intervalo a la mitad en cada paso y conserva la mitad donde f cambia de signo.",
        "Escribe f(x) y un intervalo [a, b] donde f cambie de signo; después presiona Calcular.",
        r"c_k = \dfrac{a_k + b_k}{2}", (_F,),
        (Campo("a", "Límite a", "ej: 1"), Campo("b", "Límite superior b", "ej: 3")),
        bolzano=True, animacion_continua=True),
    MetodoSpec(
        "falsa_posicion", "Regla Falsa", RAICES,
        "Usa el cruce con el eje x de la recta que une los extremos del intervalo.",
        "Escribe f(x) y un intervalo [a, b] donde f cambie de signo; después presiona Calcular.",
        r"c_k = b - \dfrac{f(b)\,(a-b)}{f(a)-f(b)}", (_F,),
        (Campo("a", "Límite a", "ej: 1"), Campo("b", "Límite superior b", "ej: 3")),
        bolzano=True, animacion_continua=True),
    MetodoSpec(
        "newton", "Newton-Raphson", RAICES,
        "Sigue la recta tangente en cada punto; la derivada se calcula automáticamente.",
        "Escribe f(x) y un valor inicial x₀ cercano a la raíz; la derivada se obtiene sola.",
        r"x_{k+1} = x_k - \dfrac{f(x_k)}{f'(x_k)}", (_F,),
        (Campo("x0", "Valor inicial x₀", "ej: 2"),)),
    MetodoSpec(
        "secante", "Secante", RAICES,
        "Reemplaza la derivada de Newton por la pendiente entre los dos últimos puntos.",
        "Escribe f(x) y dos valores iniciales distintos x₀ y x₁.",
        r"x_{k+1} = x_k - \dfrac{f(x_k)\,(x_k - x_{k-1})}{f(x_k) - f(x_{k-1})}", (_F,),
        (Campo("x0", "Valor inicial x₀", "ej: 1"), Campo("x1", "Valor inicial x₁", "ej: 2"))),
    MetodoSpec(
        "punto_fijo", "Punto Fijo", RAICES,
        "Itera x = g(x); verifica |g'(x₀)| < 1 y calcula g'(x) automáticamente.",
        "Escribe g(x) (la ecuación en la forma x = g(x)) y un valor inicial x₀.",
        r"x_{k+1} = g(x_k)", (_G,),
        (Campo("x0", "Valor inicial x₀", "ej: 1"),)),
    MetodoSpec(
        "aitken", "Aceleración de Aitken", RAICES,
        "Acelera la sucesión de punto fijo con la fórmula Δ² de Aitken.",
        "Escribe g(x) y un valor inicial x₀; se acelera la sucesión x_{k+1} = g(x_k).",
        r"\hat{x}_n = x_n - \dfrac{(x_{n+1}-x_n)^2}{x_{n+2}-2x_{n+1}+x_n}", (_G,),
        (Campo("x0", "Valor inicial x₀", "ej: 1"),)),
    MetodoSpec(
        "deflacion", "Deflación", RAICES,
        "Encuentra todas las raíces reales de un polinomio con Newton y división sintética.",
        "Escribe un polinomio P(x) y un valor inicial x₀ para empezar a buscar raíces.",
        r"P(x) = (x - r)\,Q(x) + R", (_P,),
        (Campo("x0", "Valor inicial x₀", "ej: 0.5"),)),
    MetodoSpec(
        "muller", "Müller", RAICES,
        "Ajusta una parábola por tres puntos; puede encontrar raíces complejas.",
        "Escribe f(x) y tres valores iniciales distintos P₀, P₁ y P₂.",
        r"P_3 = P_2 - \dfrac{2c}{b + \operatorname{sgn}(b)\sqrt{b^2 - 4ac}}", (_F,),
        (Campo("p0", "Punto P₀", "ej: 0"), Campo("p1", "Punto P₁", "ej: 1"), Campo("p2", "Punto P₂", "ej: 2"))),
)}

# Métodos que aparecen en el menú pero todavía NO tienen lógica (se muestran "en desarrollo").
# Cuando alguien termine uno: bórralo de esta lista y agrégale su MetodoSpec en METODOS (arriba).
# Neville va en Interpolación porque es un método de interpolación (no de raíces), por eso no lleva código todavía.
PROXIMAMENTE = {
    INTERPOLACION: ["Lagrange", "Neville", "Diferencias Divididas de Newton", "Splines Cúbicos"],
    DERIVADAS: ["Diferencias Finitas (Adelante, Atrás, Centradas)"],
    INTEGRACION: ["Regla del Trapecio", "Regla de Simpson 1/3", "Regla de Simpson 3/8"],
}


def metodos_de(categoria: str) -> list[MetodoSpec]:
    # Devuelve los métodos de una categoría en el orden en que se declararon arriba.
    return [m for m in METODOS.values() if m.categoria == categoria]
