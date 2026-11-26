# Pruebas de la lógica (sin Streamlit). Se ejecutan con:  python -m unittest discover -s tests -v
# Aquí se usa unittest (viene con Python) porque no obliga a instalar nada extra para probar.
import re
import sys
import unittest
from pathlib import Path

# Se agrega la carpeta del proyecto al path para poder importar `core` desde aquí.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402

from core.ejecutores import (ErrorNumerico, ejecutar, indice_convergencia,  # noqa: E402
                             residuo_absoluto)
from core.escritura import prefijos_latex  # noqa: E402
from core.parser import (ErrorExpresion, coeficientes_polinomio, compilar,  # noqa: E402
                         parsear, parsear_funcion)
from core.procedimiento import a_markdown, bloques, detalle_iteracion, elegir_iteraciones  # noqa: E402
from core.tabla_pasos import calendario, plan_llenado  # noqa: E402

RAIZ_CUBICA = 2.0945514815423265   # Raíz real de x^3 - 2x - 5 = 0 (valor de referencia).

# Un caso de cada método; se reutilizan en varias pruebas.
CASOS = [
    ("biseccion", {"f": "x^3-2x-5"}, {"a": 2, "b": 3}),
    ("falsa_posicion", {"f": "x^3-2x-5"}, {"a": 2, "b": 3}),
    ("newton", {"f": "x^3-2x-5"}, {"x0": 2}),
    ("secante", {"f": "x^3-2x-5"}, {"x0": 2, "x1": 3}),
    ("punto_fijo", {"g": "cos(x)"}, {"x0": 1}),
    ("aitken", {"g": "cos(x)"}, {"x0": 1}),
    ("deflacion", {"p": "x^3-6x^2+11x-6"}, {"x0": 0.5}),
    ("muller", {"f": "x^3-2x-5"}, {"p0": 0, "p1": 1, "p2": 2}),
]


class TestParser(unittest.TestCase):
    def test_sintaxis_flexible(self):
        # Se comparan varias formas de escribir con el valor que debería dar en x = 1.7.
        x = 1.7
        for texto, esperado in [("x^2+3x-1", x**2 + 3*x - 1), ("2(x+1)^2", 2*(x+1)**2), ("x(x+1)", x*(x+1)),
                                ("sen(x)-x/2", np.sin(x) - x/2), ("e^x", np.exp(x)), ("3sin(x)", 3*np.sin(x)),
                                ("raiz(x)+ln(x)", np.sqrt(x) + np.log(x)), ("x²+3x³", x**2 + 3*x**3)]:
            self.assertAlmostEqual(compilar(parsear(texto))(x), esperado, places=12, msg=texto)

    def test_errores_en_espanol(self):
        # Todas estas entradas están mal escritas y deben dar ErrorExpresion (con mensaje para el usuario).
        for texto in ["", "x+", "(x+1", "x+1)", "y+x", "sinx", "foo(x)", "x=2", "|x|", "1,2"]:
            with self.assertRaises(ErrorExpresion, msg=texto):
                parsear(texto)

    def test_entradas_peligrosas_rechazadas(self):
        # Seguridad: nada que intente ejecutar código debe pasar el parser.
        for texto in ["__import__('os').system('ls')", "x.__class__", "().__class__.__mro__", "open('f')",
                      "exec('1')", "x" * 500, "lambda: 1"]:
            with self.assertRaises(ErrorExpresion, msg=texto[:30]):
                parsear(texto)

    def test_compat_parsear_funcion(self):
        f, latex = parsear_funcion("x**3 - 2*x - 5")
        self.assertAlmostEqual(f(RAIZ_CUBICA), 0, places=12)
        self.assertEqual(f(np.array([1.0, 2.0])).shape, (2,))   # También acepta arreglos (para graficar).
        self.assertIn("x^{3}", latex)

    def test_escalar_devuelve_float(self):
        # Los métodos esperan números normales; un arreglo de 0 dimensiones les daría problemas.
        self.assertIsInstance(compilar(parsear("x^2"))(3.0), float)

    def test_polinomio(self):
        self.assertEqual(coeficientes_polinomio(parsear("x^3-6x^2+11x-6")), [1.0, -6.0, 11.0, -6.0])
        for malo in ["sin(x)", "7"]:
            with self.assertRaises(ErrorExpresion):
                coeficientes_polinomio(parsear(malo))

    def test_sin_funciones_precargadas(self):
        with self.assertRaises(ErrorExpresion):
            parsear("")   # Un campo vacío nunca se interpreta como una función por defecto.


class TestMetodos(unittest.TestCase):
    def test_raices(self):
        esperados = {"biseccion": RAIZ_CUBICA, "falsa_posicion": RAIZ_CUBICA, "newton": RAIZ_CUBICA,
                     "secante": RAIZ_CUBICA, "muller": RAIZ_CUBICA, "punto_fijo": 0.7390851332151607,
                     "aitken": 0.7390851332151607}
        for metodo, textos, numeros in CASOS:
            res = ejecutar(metodo, textos, numeros, 1e-9, 60)
            self.assertTrue(res.converged, metodo)
            if metodo == "deflacion":
                np.testing.assert_allclose(sorted(res.valor), [1, 2, 3], atol=1e-7)
            else:
                self.assertAlmostEqual(np.real(res.valor), esperados[metodo], places=5, msg=metodo)

    def test_tabla_normalizada(self):
        for metodo, textos, numeros in CASOS:
            res = ejecutar(metodo, textos, numeros, 1e-8, 60)
            self.assertEqual(res.df.columns[0], "iter", metodo)
            self.assertEqual(res.df["iter"].tolist(), list(range(1, len(res.df) + 1)), metodo)
            self.assertFalse((res.df.astype(str) == "-").any().any(), metodo)   # Nunca debe quedar el texto "-".
            if "error" in res.df and metodo != "deflacion":
                self.assertEqual(res.df["error"].dtype, np.float64, metodo)

    def test_indice_convergencia_y_residuo(self):
        res = ejecutar("newton", {"f": "x^3-2x-5"}, {"x0": 2}, 1e-8, 50)
        self.assertEqual(indice_convergencia(res), len(res.df) - 1)
        self.assertLess(residuo_absoluto(res), 1e-9)

    def test_muller_raiz_compleja(self):
        res = ejecutar("muller", {"f": "x^2+1"}, {"p0": 0, "p1": 1, "p2": 2}, 1e-9, 50)
        self.assertAlmostEqual(abs(res.valor), 1.0, places=9)
        self.assertEqual(abs(np.imag(res.valor)), 1.0)

    def test_aitken_acelera(self):
        # Aitken debe necesitar menos iteraciones que el punto fijo "a secas".
        fijo = ejecutar("punto_fijo", {"g": "cos(x)"}, {"x0": 1}, 1e-8, 50)
        acel = ejecutar("aitken", {"g": "cos(x)"}, {"x0": 1}, 1e-8, 50)
        self.assertLess(acel.n_iter, fijo.n_iter)

    def test_extremo_que_ya_es_raiz(self):
        res = ejecutar("biseccion", {"f": "x^2-4"}, {"a": 2, "b": 5}, 1e-6, 20)
        self.assertEqual(res.valor, 2.0)
        self.assertTrue(res.converged)

    def test_no_converge_en_pocas_iteraciones(self):
        res = ejecutar("biseccion", {"f": "x^3-2x-5"}, {"a": 2, "b": 3}, 1e-12, 3)
        self.assertFalse(res.converged)
        self.assertIsNone(indice_convergencia(res))

    def test_fallas_con_mensaje_claro(self):
        # (método, textos, números, excepción esperada, fragmento que debe tener el mensaje)
        casos = [("biseccion", {"f": "x^2+1"}, {"a": -1, "b": 1}, ValueError, "Bolzano"),
                 ("biseccion", {"f": "x^2-4"}, {"a": 3, "b": 1}, ValueError, "menor"),
                 ("biseccion", {"f": "log(x)"}, {"a": -2, "b": 2}, ErrorNumerico, "no está definida"),
                 ("newton", {"f": "x^2-1"}, {"x0": 0}, ValueError, "Derivada cero"),
                 ("secante", {"f": "x^2"}, {"x0": -1, "x1": 1}, ValueError, "horizontal"),
                 ("deflacion", {"p": "x^2+1"}, {"x0": 0.5}, RuntimeError, "sin converger"),
                 ("deflacion", {"p": "sin(x)"}, {"x0": 0.5}, ErrorExpresion, "polinomio"),
                 ("muller", {"f": "x^2-4"}, {"p0": 1, "p1": 1, "p2": 2}, ValueError, "distintos"),
                 ("aitken", {"g": "x^2"}, {"x0": 2}, ValueError, "diverge"),
                 ("deflacion", {"p": "x^2+1"}, {"x0": 0.5}, RuntimeError, "Müller")]
        for metodo, t, n, excepcion, fragmento in casos:
            with self.assertRaises(excepcion, msg=metodo) as ctx:
                ejecutar(metodo, t, n, 1e-8, 50)
            self.assertIn(fragmento, str(ctx.exception), metodo)



class TestCorrecciones(unittest.TestCase):
    """Errores encontrados en la revisión del 24/11/2026; cada prueba evita que vuelvan."""

    def test_polo_no_se_reporta_como_raiz(self):
        for metodo, f, a, b in (("biseccion", "1/x", -1, 2), ("biseccion", "tan(x)", 1, 2), ("falsa_posicion", "tan(x)", 1, 2)):
            res = ejecutar(metodo, {"f": f}, {"a": a, "b": b}, 1e-6, 100)
            self.assertFalse(res.converged, (metodo, f))
            self.assertIn("polo", res.ctx["aviso"])
        # Si c cae justo en el polo, el mensaje lo explica (antes decía "Convergió").
        with self.assertRaises(ErrorNumerico) as ctx:
            ejecutar("falsa_posicion", {"f": "1/x"}, {"a": -1, "b": 2}, 1e-6, 100)
        self.assertIn("asíntota", str(ctx.exception))

    def test_punto_fijo_no_rechaza_casos_que_convergen(self):
        # |g'(x0)| = e^0.5 > 1 pero la iteración sí converge a 0.567143…
        res = ejecutar("punto_fijo", {"g": "exp(-x)"}, {"x0": -0.5}, 1e-8, 100)
        self.assertTrue(res.converged)
        self.assertAlmostEqual(res.valor, 0.5671432904097838, places=6)
        self.assertIn("convergió", res.ctx["aviso"])

    def test_punto_fijo_que_diverge_muestra_tabla(self):
        res = ejecutar("punto_fijo", {"g": "2*x"}, {"x0": 1}, 1e-8, 30)
        self.assertFalse(res.converged)
        self.assertGreater(len(res.df), 1)

    def test_newton_y_muller_sin_converger_muestran_tabla(self):
        res = ejecutar("newton", {"f": "x^3-2x+2"}, {"x0": 0}, 1e-8, 20)   # Newton cicla entre 0 y 1.
        self.assertFalse(res.converged)
        self.assertEqual(len(res.df), 20)
        res = ejecutar("muller", {"f": "sqrt(x)"}, {"p0": -3, "p1": -2, "p2": -1}, 1e-8, 15)
        self.assertEqual(res.converged, bool(res.df["error"].iloc[-1] <= 1e-8))

    def test_muller_con_punto_inicial_que_ya_es_raiz(self):
        res = ejecutar("muller", {"f": "x^3-1"}, {"p0": 0, "p1": 1, "p2": 2}, 1e-8, 50)
        self.assertTrue(res.converged)
        self.assertAlmostEqual(abs(res.valor - 1), 0, places=10)

    def test_sin_menos_cero(self):
        from core.formato import tex_num, txt_num
        self.assertEqual(txt_num(-2.4e-9, 6), "0.000000")
        self.assertFalse(tex_num(-0.0, 6).startswith("-"))


# ---------------------------------------------------------------------------------------- Persona A
CASOS_A = [
    ("punto_flotante", {"num": "0.1", "formato": "Simple (32 bits)"}, {}),
    ("punto_flotante", {"num": "-118.625", "formato": "Doble (64 bits)"}, {}),
    ("neville", {"xs": "1, 1.3, 1.6, 1.9, 2.2", "ys": "0.7651977, 0.6200860, 0.4554022, 0.2818186, 0.1103623"}, {"x": 1.5}),
    ("hermite", {"xs": "1.3, 1.6, 1.9", "ys": "0.6200860, 0.4554022, 0.2818186",
                 "dys": "-0.5220232, -0.5698959, -0.5811571"}, {"x": 1.5}),
    ("derivada_2p", {"f": "ln(x)", "formula": "Hacia adelante"}, {"x0": 1.8, "h": 0.1, "pasos": 4}),
    ("derivada_5p", {"f": "x*exp(x)", "formula": "Centrada (punto medio)"}, {"x0": 2, "h": 0.1, "pasos": 3}),
    ("derivada_5p", {"f": "x*exp(x)", "formula": "Punto extremo"}, {"x0": 2, "h": 0.1, "pasos": 3}),
    ("trapecio", {"f": "sin(x)"}, {"a": 0, "b": np.pi, "n": 6}),
    ("simpson38", {"f": "sin(x)"}, {"a": 0, "b": np.pi, "n": 6}),
    ("adaptativa", {"f": "100/x^2*sin(10/x)"}, {"a": 1, "b": 3}),
    ("doble_trapecio", {"f": "ln(x+2y)", "c": "1", "d": "1.5"}, {"a": 1.4, "b": 2, "n": 4, "m": 2}),
    ("doble_simpson38", {"f": "exp(y/x)", "c": "x^3", "d": "x^2"}, {"a": 0.1, "b": 0.5, "n": 9, "m": 9}),
]


def _ej(metodo, t, n, tol=1e-6, nmax=20):
    return ejecutar(metodo, t, n, tol, nmax)


class TestPersonaA(unittest.TestCase):
    def test_punto_flotante_contra_la_maquina(self):
        import struct
        for texto in ("0.1", "-118.625", "1/3", "1e-40", "3.4e38", "0", "0.5", "123456789"):
            for formato, fmt in (("Simple (32 bits)", ">f"), ("Doble (64 bits)", ">d")):
                res = _ej("punto_flotante", {"num": texto, "formato": formato}, {})
                from fractions import Fraction
                esperado = struct.pack(fmt, float(Fraction(texto))).hex().upper()
                self.assertEqual(res.ctx["rep"].hexadecimal, esperado, (texto, formato))
                self.assertEqual(res.valor, struct.unpack(fmt, bytes.fromhex(esperado))[0])
        res = _ej("punto_flotante", {"num": "0.1", "formato": "Simple (32 bits)"}, {})
        self.assertEqual(res.ctx["rep"].hexadecimal, "3DCCCCCD")
        self.assertLessEqual(res.ctx["err_rel"], res.ctx["u"])
        res = _ej("punto_flotante", {"num": "-118.625", "formato": "Simple (32 bits)"}, {})
        self.assertEqual(res.ctx["rep"].bits, "11000010111011010100000000000000")   # Ejemplo clásico.
        self.assertEqual(res.ctx["rep"].redondeo, "exacto")

    def test_interpolacion_burden(self):
        # Burden, ejemplos de Neville (sección 3.2) y Hermite (sección 3.4) con J0(x).
        self.assertAlmostEqual(_ej(*CASOS_A[2]).valor, 0.5118200, places=7)
        self.assertAlmostEqual(_ej(*CASOS_A[3]).valor, 0.5118277, places=7)
        res = _ej("neville", {"xs": "0, 1, 2, 3", "ys": "x^3 - 2x"}, {"x": 1.5})   # Cúbica: Neville la reproduce exacta.
        self.assertAlmostEqual(res.valor, 1.5 ** 3 - 3, places=12)
        res = _ej("hermite", {"xs": "0, 1", "ys": "x^3", "dys": ""}, {"x": 0.3})   # Derivadas automáticas.
        self.assertAlmostEqual(res.valor, 0.027, places=12)

    def test_derivadas_y_orden(self):
        exacta = 2 * np.exp(2) + np.exp(2) * 2   # d/dx (x e^x) en 2 = e^2 (1 + 2)
        exacta = 3 * np.exp(2)
        res = _ej("derivada_2p", {"f": "ln(x)", "formula": "Hacia adelante"}, {"x0": 1.8, "h": 0.1, "pasos": 1})
        self.assertAlmostEqual(res.valor, 0.5406722, places=6)        # Burden, ejemplo 1 de 4.1.
        res = _ej("derivada_5p", {"f": "x*exp(x)", "formula": "Centrada (punto medio)"}, {"x0": 2, "h": 0.1, "pasos": 1})
        self.assertAlmostEqual(res.valor, 22.166995, places=5)        # Burden, ejemplo 2 de 4.1.
        self.assertAlmostEqual(abs(res.valor - exacta), 1.73e-4, delta=1e-5)
        res = _ej("derivada_2p", {"f": "exp(x)", "formula": "Hacia atrás"}, {"x0": 0, "h": 0.1, "pasos": 4})
        self.assertAlmostEqual(res.df["razón"].iloc[-1], 2, delta=0.1)   # O(h): razón ≈ 2.
        res = _ej("derivada_5p", {"f": "exp(x)", "formula": "Centrada (punto medio)"}, {"x0": 0, "h": 0.4, "pasos": 3})
        self.assertAlmostEqual(res.df["razón"].iloc[-1], 16, delta=1)    # O(h⁴): razón ≈ 16.

    def test_integrales(self):
        self.assertAlmostEqual(_ej(*CASOS_A[7]).valor, 1.9540972, places=6)
        self.assertAlmostEqual(_ej(*CASOS_A[8]).valor, 2.0020098, places=6)
        res = _ej(*CASOS_A[9])
        self.assertAlmostEqual(res.valor, -1.4260247, places=5)       # Burden, ejemplo de 4.6.
        self.assertTrue(res.converged)
        # Simpson 3/8 integra cúbicas exactamente; el trapecio, rectas.
        self.assertAlmostEqual(_ej("simpson38", {"f": "x^3 - x"}, {"a": 0, "b": 2, "n": 3}).valor, 2.0, places=12)
        self.assertAlmostEqual(_ej("trapecio", {"f": "3x + 1"}, {"a": -1, "b": 2, "n": 1}).valor, 7.5, places=12)

    def test_integrales_dobles(self):
        res = _ej(*CASOS_A[10])
        self.assertAlmostEqual(res.valor, res.ctx["ref"], places=3)
        res = _ej(*CASOS_A[11])
        self.assertAlmostEqual(res.valor, 0.0333056, places=6)
        # Simpson 3/8 doble es exacto para polinomios de grado 3 en cada variable sobre un rectángulo.
        res = _ej("doble_simpson38", {"f": "x^3 y^2", "c": "0", "d": "1"}, {"a": 0, "b": 2, "n": 3, "m": 3})
        self.assertAlmostEqual(res.valor, 4 / 3, places=12)

    def test_errores_con_mensaje_claro(self):
        casos = [("punto_flotante", {"num": "abc", "formato": "Simple (32 bits)"}, {}, "no es un número"),
                 ("punto_flotante", {"num": "1e39", "formato": "Simple (32 bits)"}, {}, "máximo"),
                 ("neville", {"xs": "1, 1, 2", "ys": "1, 2, 3"}, {"x": 1.5}, "distintos"),
                 ("neville", {"xs": "1, 2, 3", "ys": "1, 2"}, {"x": 1.5}, "misma cantidad"),
                 ("hermite", {"xs": "1, 2", "ys": "1, 2", "dys": ""}, {"x": 1.5}, "derivadas"),
                 ("derivada_2p", {"f": "x^2", "formula": "Hacia adelante"}, {"x0": 1, "h": 0, "pasos": 2}, "cero"),
                 ("derivada_2p", {"f": "ln(x)", "formula": "Hacia atrás"}, {"x0": 0.05, "h": 0.1, "pasos": 2}, "definida"),
                 ("simpson38", {"f": "x"}, {"a": 0, "b": 1, "n": 4}, "múltiplo de 3"),
                 ("trapecio", {"f": "1/x"}, {"a": 0, "b": 1, "n": 4}, "definida"),
                 ("doble_simpson38", {"f": "x y", "c": "0", "d": "1"}, {"a": 0, "b": 1, "n": 3, "m": 2}, "múltiplo de 3")]
        for metodo, t, n, fragmento in casos:
            with self.assertRaises(ValueError, msg=(metodo, t)) as ctx:
                _ej(metodo, t, n)
            self.assertIn(fragmento, str(ctx.exception), (metodo, t))

    def test_procedimiento_tabla_y_grafica(self):
        from ui.plots import construir_figura, rango_auto
        for metodo, t, n in CASOS_A:
            res = _ej(metodo, t, n)
            for tipo, contenido in bloques(res, 6, [1, 2, 3]):
                if tipo == "latex":
                    self.assertTrue(all(_balanceado(p) for p in prefijos_latex(contenido)), (metodo, contenido))
            plan = plan_llenado(res)
            self.assertEqual(len(plan), res.df.size, metodo)
            llenas = set()
            for p in plan:
                for fuente in p.fuentes:
                    self.assertIn(fuente, llenas, f"{metodo}: {p.columna} usa {fuente} antes de llenarla")
                llenas.add((p.fila, p.columna))
            for k in range(1, res.n_filas + 1):
                self.assertTrue(detalle_iteracion(res, k, 6), metodo)
                construir_figura(res, k, rango_auto(res))
            self.assertIn("$$", a_markdown(res))

    def test_todos_los_metodos_del_menu_tienen_ejecutor(self):
        from core.ejecutores import EJECUTORES
        from registry import METODOS
        self.assertEqual(set(METODOS) - set(EJECUTORES), set())


def _balanceado(s):
    # Revisa que las llaves y los \left/\right de un fragmento de LaTeX estén cerrados.
    nivel = 0
    for ch in re.sub(r"\\[{}]", "", s):
        nivel += (ch == "{") - (ch == "}")
        if nivel < 0:
            return False
    return nivel == 0 and s.count(r"\left") == s.count(r"\right")


class TestProcedimiento(unittest.TestCase):
    def test_bloques_para_todos_los_metodos(self):
        for metodo, textos, numeros in CASOS + [("muller", {"f": "x^2+1"}, {"p0": 0, "p1": 1, "p2": 2})]:
            res = ejecutar(metodo, textos, numeros, 1e-8, 60)
            for d in (3, 6, 10):   # Con distintas precisiones decimales.
                cuerpo = bloques(res, d, [1, 2, 3])
                tipos = {t for t, _ in cuerpo}
                self.assertTrue({"titulo", "texto", "latex"} <= tipos, metodo)
            for k in range(1, res.n_filas + 1):
                self.assertTrue(detalle_iteracion(res, k, 6), metodo)
            self.assertIn("$$", a_markdown(res))

    def test_siempre_incluye_la_iteracion_final(self):
        # Pedido: se muestran las iteraciones elegidas y, al final, la última (la que lleva al resultado).
        res = ejecutar("biseccion", {"f": "x^3-2x-5"}, {"a": 2, "b": 3}, 1e-8, 60)
        for seleccion in ([1, 2, 3], [1, 5, 10], [], [res.n_filas], [1, 2, 3, 999]):
            subs = [c for t, c in bloques(res, 6, seleccion) if t == "subtitulo"]
            self.assertIn(f"Iteración {res.n_filas}", subs[-1], seleccion)
            self.assertIn("final", subs[-1])
            self.assertEqual(len(subs), len(set(subs)), "no se repite ninguna iteración")

    def test_seleccion_ignora_numeros_fuera_de_rango(self):
        res = ejecutar("newton", {"f": "x^3-2x-5"}, {"x0": 2}, 1e-8, 60)
        elegidas, falta_final = elegir_iteraciones(res, [0, 1, 2, 3, 500, -4])
        self.assertEqual(elegidas, [1, 2, 3])
        self.assertTrue(falta_final)   # Newton tiene más de 3 filas, así que la última se agrega aparte.

    def test_toda_ecuacion_se_puede_escribir_progresivamente(self):
        # Cada fotograma de la animación de escritura debe ser LaTeX válido (balanceado).
        for metodo, textos, numeros in CASOS:
            res = ejecutar(metodo, textos, numeros, 1e-8, 60)
            for tipo, contenido in bloques(res, 6, [1, 2, 3, 4, 5]):
                if tipo == "latex":
                    prefijos = prefijos_latex(contenido)
                    self.assertEqual(prefijos[-1], contenido)
                    self.assertTrue(all(_balanceado(p) for p in prefijos), (metodo, contenido))


class TestPlanDeTabla(unittest.TestCase):
    def test_el_plan_cubre_todas_las_celdas(self):
        for metodo, textos, numeros in CASOS:
            res = ejecutar(metodo, textos, numeros, 1e-8, 60)
            plan = plan_llenado(res)
            self.assertEqual(len(plan), len(res.df) * len(res.df.columns), metodo)
            celdas = {(p.fila, p.columna) for p in plan}
            self.assertEqual(len(celdas), len(plan), f"{metodo}: ninguna celda se repite")

    def test_las_fuentes_ya_estan_llenas_cuando_se_usan(self):
        # Una celda solo puede usar celdas que ya se llenaron antes (si no, la animación mostraría algo imposible).
        for metodo, textos, numeros in CASOS:
            res = ejecutar(metodo, textos, numeros, 1e-8, 60)
            llenas = set()
            for p in plan_llenado(res):
                for fuente in p.fuentes:
                    self.assertIn(fuente, llenas, f"{metodo}: {p.columna} usa {fuente} antes de llenarla")
                llenas.add((p.fila, p.columna))

    def test_escalerita_hacia_la_derecha(self):
        # En los métodos "de escalera", la primera columna de una fila sale de la última de la fila anterior.
        casos = {"newton": ("x", "x1"), "secante": ("x_0", "x_1"), "punto_fijo": ("x0", "x1"), "muller": ("P0", "P1")}
        for metodo, (columna, origen) in casos.items():
            textos, numeros = next((t, n) for m, t, n in CASOS if m == metodo)
            res = ejecutar(metodo, textos, numeros, 1e-8, 60)
            paso = next(p for p in plan_llenado(res) if p.fila == 1 and p.columna == columna)
            self.assertIn((0, origen), paso.fuentes, metodo)

    def test_calendario_termina_con_todo_lleno_y_no_es_eterno(self):
        for metodo, textos, numeros in CASOS:
            # Tolerancia muy chica y hasta 100 iteraciones (el máximo de la app) para tener tablas largas.
            res = ejecutar(metodo, textos, numeros, 1e-10, 100)
            plan = plan_llenado(res)
            cuadros = calendario(plan, len(res.df))
            self.assertEqual(cuadros[-1].hasta, len(plan), metodo)
            self.assertLessEqual(len(cuadros), 3 * len(res.df.columns) + 40, metodo)   # Tope de cuadros.


if __name__ == "__main__":
    unittest.main()
