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
    tipo: str = "funcion"   # Campos de texto: "funcion", "funcion_xy" (f(x, y)), "lista" o "lista_o_funcion".
                            # Campos numéricos: "numero" o "entero".
    opcional: bool = False  # True si se puede dejar vacío (por ejemplo, las derivadas en Hermite si diste f(x)).


@dataclass(frozen=True)
class Opcion:
    # Un selector (por ejemplo "Precisión simple / doble" o "Hacia adelante / atrás").
    key: str
    label: str
    opciones: tuple[str, ...]
    ayuda: str = ""


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
    # ---- Lo siguiente lo usan los métodos que NO son de raíces (tienen otros controles y otros textos).
    campos_opcion: tuple[Opcion, ...] = ()
    controles: tuple[str, ...] = ("tol", "nmax")   # Controles comunes que se muestran: tolerancia y/o máx. iteraciones.
    etiqueta_nmax: str = "Máx. iteraciones"
    etiqueta_pasos: str = "Iteraciones a desarrollar en el procedimiento"
    titulo_tabla: str = "Tabla de iteraciones"
    desc_tabla: str = "Así se va llenando: cada celda nueva se calcula con las celdas resaltadas en azul."
    desc_resultados: str = "Solución, estado de convergencia y gráfica interactiva para recorrer cada iteración."


PUNTO_FLOTANTE = "Errores y Punto Flotante"
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

# ---------------------------------------------------------------------------------------------- Persona A
# Textos y campos de los métodos que no son de raíces. Se describen igual: un MetodoSpec por método.
_PASOS = "Pasos a desarrollar en el procedimiento"
_DIRECTO = dict(controles=(), etiqueta_pasos=_PASOS,
                desc_resultados="Resultado, comparación con el valor exacto y gráfica interactiva para recorrer cada paso.")
_XS = Campo("xs", "Nodos x₀, x₁, …, xₙ", "Separados por comas, ej: 1, 1.3, 1.6, 1.9, 2.2", tipo="lista",
            ayuda="Escribe los nodos separados por comas. Pueden ir en cualquier orden pero deben ser distintos.")
_YS = Campo("ys", "Valores f(xᵢ) — lista o función", "Lista: 0.7652, 0.6201, …  o una función, ej: cos(x)", "f",
            "Escribe tantos valores como nodos, separados por comas, o una función de x y se evalúa en los nodos.",
            tipo="lista_o_funcion")
_FX = Campo("f", "Función f(x)", "Ingresa tu función, ej: x*exp(x)  o  ln(x)", "f",
            "Puedes escribir x^2 o x**2, 2x o 2*x, sen(x) o sin(x).")
_FINT = Campo("f", "Función f(x) a integrar", "Ingresa tu función, ej: sin(x)  o  exp(-x^2)", "f",
              "Puedes escribir x^2 o x**2, 2x o 2*x, sen(x) o sin(x).")
_A = Campo("a", "Límite inferior a", "ej: 0")
_B = Campo("b", "Límite superior b", "ej: 3.1416  (puedes escribir 3.14159)")
_N = Campo("n", "Subintervalos n", "ej: 6", tipo="entero")
_N3 = Campo("n", "Subintervalos n (múltiplo de 3)", "ej: 6", tipo="entero", ayuda="Simpson 3/8 necesita n = 3, 6, 9, …")
_PASOS_H = Campo("pasos", "Cuántos valores de h", "ej: 5  (h, h/2, h/4, …)", tipo="entero",
                 ayuda="Se aplica la fórmula con h, h/2, h/4, … para ver cómo baja el error.")
_DOBLE_TEXTO = (Campo("f", "Función f(x, y)", "Ingresa f(x, y), ej: ln(x + 2y)  o  exp(y/x)", "f",
                      "Usa x y y como variables.", tipo="funcion_xy"),
                Campo("c", "Límite inferior en y: c(x)", "Número o función de x, ej: 1  o  x^3", "c"),
                Campo("d", "Límite superior en y: d(x)", "Número o función de x, ej: 1.5  o  x^2", "d"))

METODOS_PERSONA_A = (
    MetodoSpec(
        "punto_flotante", "Punto flotante (IEEE 754)", PUNTO_FLOTANTE,
        "Cómo guarda la computadora un número decimal: signo, exponente y mantisa, y cuánto error se comete.",
        "Escribe un número decimal (por ejemplo 0.1 o -118.625) y elige la precisión.",
        r"x = (-1)^{s}\,(1.m)_2 \times 2^{E - \text{sesgo}}",
        (Campo("num", "Número decimal", "ej: 0.1   -118.625   2.5e-3   1/3", "x",
               "Se usa el valor EXACTO que escribes (0.1 es exactamente 1/10), no el float de Python.", tipo="numero"),),
        (), campos_opcion=(Opcion("formato", "Precisión", ("Simple (32 bits)", "Doble (64 bits)")),),
        titulo_tabla="Tabla de conversión a binario",
        desc_tabla="Parte entera: divisiones entre 2 (el residuo es el bit). Parte fraccionaria: multiplicaciones por 2 "
                   "(la parte entera del resultado es el bit).", **_DIRECTO),
    MetodoSpec(
        "neville", "Neville", INTERPOLACION,
        "Evalúa el polinomio interpolante en un punto con una tabla triangular, sin calcular sus coeficientes.",
        "Escribe los nodos, sus valores (o una función) y el punto x donde quieres evaluar.",
        r"Q_{i,j} = \dfrac{(x - x_{i-j})\,Q_{i,j-1} - (x - x_i)\,Q_{i-1,j-1}}{x_i - x_{i-j}}",
        (_XS, _YS), (Campo("x", "Evaluar en x", "ej: 1.5"),),
        titulo_tabla="Tabla de Neville", **_DIRECTO),
    MetodoSpec(
        "hermite", "Hermite", INTERPOLACION,
        "Polinomio que pasa por los puntos y además respeta la derivada en cada uno (diferencias divididas con nodos repetidos).",
        "Escribe los nodos, f(xᵢ) y f'(xᵢ). Si das f(x) como función, las derivadas se calculan solas.",
        r"H(x) = Q_{0,0} + \sum_{k=1}^{2n+1} Q_{k,k} \prod_{j=0}^{k-1}(x - z_j)",
        (_XS, _YS, Campo("dys", "Derivadas f'(xᵢ) — lista o función (opcional)", "ej: -0.5220, -0.5699, -0.5812",
                         "f'", "Déjalo vacío si en f(xᵢ) escribiste una función: se deriva sola.",
                         tipo="lista_o_funcion", opcional=True)),
        (Campo("x", "Evaluar en x (opcional)", "ej: 1.5", opcional=True),),
        titulo_tabla="Tabla de diferencias divididas (nodos repetidos)", **_DIRECTO),
    MetodoSpec(
        "derivada_2p", "Derivación por 2 puntos", DERIVADAS,
        "Aproxima f'(x₀) con la pendiente de una secante; el error es proporcional a h.",
        "Escribe f(x), el punto x₀, el paso h y cuántas veces quieres partir h a la mitad.",
        r"f'(x_0) \approx \dfrac{f(x_0 + h) - f(x_0)}{h}",
        (_FX,), (Campo("x0", "Punto x₀", "ej: 1.8"), Campo("h", "Paso h", "ej: 0.1"), _PASOS_H),
        campos_opcion=(Opcion("formula", "Fórmula", ("Hacia adelante", "Hacia atrás")),),
        titulo_tabla="Tabla de aproximaciones", **_DIRECTO),
    MetodoSpec(
        "derivada_5p", "Derivación por 5 puntos", DERIVADAS,
        "Fórmulas de 5 puntos (centrada o de extremo) con error O(h⁴).",
        "Escribe f(x), el punto x₀, el paso h y cuántas veces quieres partir h a la mitad.",
        r"f'(x_0) \approx \dfrac{f(x_0 - 2h) - 8f(x_0 - h) + 8f(x_0 + h) - f(x_0 + 2h)}{12h}",
        (_FX,), (Campo("x0", "Punto x₀", "ej: 2"), Campo("h", "Paso h", "ej: 0.1"), _PASOS_H),
        campos_opcion=(Opcion("formula", "Fórmula", ("Centrada (punto medio)", "Punto extremo")),),
        titulo_tabla="Tabla de aproximaciones", **_DIRECTO),
    MetodoSpec(
        "trapecio", "Regla del trapecio", INTEGRACION,
        "Regla del trapecio compuesta: reemplaza f por rectas en n subintervalos.",
        "Escribe f(x), los límites a y b y el número de subintervalos n.",
        r"\int_a^b f(x)\,dx \approx \dfrac{h}{2}\left[f(x_0) + 2\sum_{i=1}^{n-1} f(x_i) + f(x_n)\right]",
        (_FINT,), (_A, _B, _N), titulo_tabla="Tabla de nodos", **_DIRECTO),
    MetodoSpec(
        "simpson38", "Regla de Simpson 3/8", INTEGRACION,
        "Simpson 3/8 compuesta: reemplaza f por cúbicas en grupos de 3 subintervalos.",
        "Escribe f(x), los límites a y b y un número de subintervalos n múltiplo de 3.",
        r"\int_a^b f(x)\,dx \approx \dfrac{3h}{8}\left[f_0 + 3f_1 + 3f_2 + 2f_3 + \cdots + 3f_{n-1} + f_n\right]",
        (_FINT,), (_A, _B, _N3), titulo_tabla="Tabla de nodos", **_DIRECTO),
    MetodoSpec(
        "adaptativa", "Cuadratura adaptativa", INTEGRACION,
        "Simpson adaptativo: parte el intervalo solo donde hace falta hasta cumplir la tolerancia.",
        "Escribe f(x) y los límites a y b; ajusta la tolerancia y el máximo de niveles.",
        r"|S(a,m) + S(m,b) - S(a,b)| < 15\,\varepsilon",
        (_FINT,), (_A, _B),
        controles=("tol", "nmax"), etiqueta_nmax="Máx. niveles de división", etiqueta_pasos=_PASOS,
        titulo_tabla="Subintervalos revisados",
        desc_resultados="Resultado, subintervalos usados y gráfica interactiva para recorrer cada paso."),
    MetodoSpec(
        "doble_trapecio", "Integración doble: trapecio", INTEGRACION,
        "∫∫ f(x, y) dy dx sobre una región con límites c(x), d(x), aplicando el trapecio en x y en y.",
        "Escribe f(x, y), los límites en x (a, b), los límites en y (c(x), d(x)) y los subintervalos n y m.",
        r"\int_a^b \int_{c(x)}^{d(x)} f(x, y)\,dy\,dx",
        _DOBLE_TEXTO, (_A, _B, Campo("n", "Subintervalos en x (n)", "ej: 4", tipo="entero"),
                       Campo("m", "Subintervalos en y (m)", "ej: 4", tipo="entero")),
        titulo_tabla="Integrales interiores por nodo xᵢ", **_DIRECTO),
    MetodoSpec(
        "doble_simpson38", "Integración doble: Simpson 3/8", INTEGRACION,
        "∫∫ f(x, y) dy dx sobre una región con límites c(x), d(x), aplicando Simpson 3/8 en x y en y.",
        "Escribe f(x, y), los límites en x (a, b), los límites en y (c(x), d(x)) y n, m múltiplos de 3.",
        r"\int_a^b \int_{c(x)}^{d(x)} f(x, y)\,dy\,dx",
        _DOBLE_TEXTO, (_A, _B, Campo("n", "Subintervalos en x (n, múltiplo de 3)", "ej: 3", tipo="entero"),
                       Campo("m", "Subintervalos en y (m, múltiplo de 3)", "ej: 3", tipo="entero")),
        titulo_tabla="Integrales interiores por nodo xᵢ", **_DIRECTO),
)
METODOS.update({m.id: m for m in METODOS_PERSONA_A})

# Métodos que aparecen en el menú pero todavía NO tienen lógica (se muestran "en desarrollo").
# Cuando alguien termine uno: bórralo de esta lista y agrégale su MetodoSpec en METODOS (arriba).
# (Son los de la Persona B.)
PROXIMAMENTE = {
    PUNTO_FLOTANTE: [],
    INTERPOLACION: ["Lagrange", "Diferencias divididas", "Splines cúbicos"],
    DERIVADAS: ["Derivación por 3 puntos", "Extrapolación de Richardson"],
    INTEGRACION: ["Regla de Simpson 1/3", "Integración de Romberg", "Cuadratura gaussiana",
                  "Integración doble: Simpson 1/3"],
}
CATEGORIAS = (PUNTO_FLOTANTE, RAICES, INTERPOLACION, DERIVADAS, INTEGRACION)   # Orden del menú.


def metodos_de(categoria: str) -> list[MetodoSpec]:
    # Devuelve los métodos de una categoría en el orden en que se declararon arriba.
    return [m for m in METODOS.values() if m.categoria == categoria]
