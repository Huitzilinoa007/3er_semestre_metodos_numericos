# Vista genérica de un método. TODOS los métodos pasan por aquí, por eso se ven y se comportan igual.
# Orden de la página:  datos -> procedimiento (se escribe) -> tabla (se llena) -> resultados + gráfica.
from __future__ import annotations

import streamlit as st

from core.ejecutores import ejecutar
from core.parser import ErrorExpresion
from core.procedimiento import bloques
from registry import MetodoSpec
from ui.components.entrada import clave, tarjeta_datos
from ui.components.hoja import escribir_hoja
from ui.components.resultados import mostrar_resultados
from ui.components.seccion import seccion, titulo_pagina
from ui.components.tabla import tabla_iteraciones
from ui.components.vacio import estado_vacio


def _reanimar(clave_anim: str) -> None:
    # Callback de "Repetir animación": al marcar que NO se ha animado, la siguiente pasada vuelve a animar.
    st.session_state[clave_anim] = False


def _calcular(spec: MetodoSpec, datos: dict) -> None:
    s = st.session_state
    # Primero se revisa que no falte ningún dato, para avisar con claridad en lugar de fallar adentro del método.
    faltan = [c.label for c in spec.campos_texto if not datos["textos"][c.key].strip()]
    faltan += [c.label for c in spec.campos_num if datos["numeros"][c.key] is None]
    if faltan:
        st.warning("Completa los campos: " + ", ".join(faltan) + ".")
        return
    try:
        res = ejecutar(spec.id, datos["textos"], datos["numeros"], datos["tol"], datos["n_max"])
    except ErrorExpresion as exc:                   # La función está mal escrita.
        s.pop(clave(spec, "res"), None)
        st.error(str(exc))
    except RuntimeError as exc:                     # El método agotó sus iteraciones sin converger.
        s.pop(clave(spec, "res"), None)
        st.warning(f"{exc} Prueba aumentar «Máx. iteraciones», relajar la tolerancia o cambiar los valores iniciales.")
    except ValueError as exc:                       # Bolzano, derivada nula, datos no válidos, etc.
        s.pop(clave(spec, "res"), None)
        st.warning(str(exc))
    except (ZeroDivisionError, OverflowError, FloatingPointError) as exc:
        s.pop(clave(spec, "res"), None)
        st.error(f"Operación inválida durante el cálculo: {exc}")
    except Exception as exc:  # noqa: BLE001 - aquí se atrapa todo porque la app nunca debe caerse por un caso raro.
        s.pop(clave(spec, "res"), None)
        st.error(f"Ocurrió un error inesperado: {exc}")
    else:
        s[clave(spec, "res")] = res        # El resultado se guarda para que sobreviva a los reruns (mover un slider, etc.).
        s[clave(spec, "anim")] = False     # Un resultado nuevo se anima una vez.
        s.pop(clave(spec, "k"), None)


def renderizar_metodo(spec: MetodoSpec) -> None:
    s = st.session_state
    k_res, k_anim = clave(spec, "res"), clave(spec, "anim")
    # Al llegar de nuevo a la página, Streamlit ya borró los widgets; aquí se borran también los resultados viejos
    # para que no aparezca una tabla de un cálculo con campos que ya están vacíos.
    if clave(spec, spec.campos_texto[0].key) not in s:
        for sufijo in ("res", "anim", "k"):
            s.pop(clave(spec, sufijo), None)

    titulo_pagina(f"Módulo activo: {spec.categoria} ➔ {spec.nombre}", spec.nombre, spec.resumen)
    st.latex(spec.formula)

    datos = tarjeta_datos(spec)
    if datos["calcular"]:
        _calcular(spec, datos)

    res = s.get(k_res)
    if res is None:
        estado_vacio(spec)   # Al abrir no se calcula nada: solo se ve la hoja en blanco con la guía.
        return

    d = datos["decimales"]
    # Se anima solo si es la primera vez que se muestra este resultado y el usuario no eligió "Sin animación".
    animar = (not s.get(k_anim, False)) and datos["velocidad"] != "Sin animación"
    # Se marca como "ya animado" ANTES de animar: si el usuario interrumpe (por ejemplo con "Saltar"),
    # la siguiente pasada ya muestra todo completo en vez de volver a empezar.
    s[k_anim] = True
    velocidad = datos["velocidad"] if animar else "Sin animación"

    # ---- 1) Procedimiento
    seccion("Procedimiento", "El desarrollo paso a paso con tus datos: se muestran las iteraciones que elegiste "
                             "y, al final, la última, que lleva al resultado.", "violeta")
    boton = st.empty()   # Un solo lugar para el botón: primero "Saltar", y al terminar todo, "Repetir".
    if animar:
        boton.button("Saltar animación", key=clave(spec, "saltar"))
    escribir_hoja(bloques(res, d, datos["iteraciones"]), velocidad)

    # ---- 2) Tabla que se va llenando
    seccion("Tabla de iteraciones", "Así se va llenando: cada celda nueva se calcula con las celdas resaltadas en azul.", "cian")
    tabla_iteraciones(res, d, velocidad)
    boton.button("Repetir animación", key=clave(spec, "repetir"), on_click=_reanimar, args=(k_anim,))

    # ---- 3) Resultados y gráfica (ya abajo, cuando termina lo anterior)
    seccion("Resultados", "Solución, estado de convergencia y gráfica interactiva para recorrer cada iteración.", "menta")
    mostrar_resultados(spec, res, d, datos["rango"], datos["iteraciones"])
