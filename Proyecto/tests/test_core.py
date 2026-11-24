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
                 ("biseccion", {"f": "log(x)"}, {"a": -2, "b": 2}, ErrorNumerico, "no finitos"),
                 ("newton", {"f": "x^2-1"}, {"x0": 0}, ValueError, "Derivada cero"),
                 ("secante", {"f": "x^2"}, {"x0": -1, "x1": 1}, ValueError, "horizontal"),
                 ("punto_fijo", {"g": "2*x"}, {"x0": 1}, ValueError, "diverg"),
                 ("deflacion", {"p": "x^2+1"}, {"x0": 0.5}, RuntimeError, "sin converger"),
                 ("deflacion", {"p": "sin(x)"}, {"x0": 0.5}, ErrorExpresion, "polinomio"),
                 ("muller", {"f": "x^2-4"}, {"p0": 1, "p1": 1, "p2": 2}, ValueError, "distintos")]
        for metodo, t, n, excepcion, fragmento in casos:
            with self.assertRaises(excepcion, msg=metodo) as ctx:
                ejecutar(metodo, t, n, 1e-8, 50)
            self.assertIn(fragmento, str(ctx.exception), metodo)


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
