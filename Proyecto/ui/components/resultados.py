# Resultados: tarjetas KPI, gráfica interactiva (slider de iteraciones), animación continua y exportación.
# La tabla ya no vive aquí: se muestra antes, llenándose paso a paso (ver ui/components/tabla.py).
from __future__ import annotations

import streamlit as st

from core.ejecutores import Resultado, indice_convergencia, residuo_absoluto
from core.formato import txt_num, txt_sci
from core.procedimiento import a_markdown, detalle_iteracion, etiqueta_paso
from registry import MetodoSpec
from ui.compat import ancho_completo, contenedor
from ui.plots import construir_figura, figura_animada, rango_auto

_CONFIG_PLOTLY = {"displaylogo": False}   # Quita el logo de Plotly de la barra de la gráfica (ruido visual).


# ----------------------------------------------------------------------------- tarjetas KPI
def _valor_texto(res: Resultado, d: int) -> str:
    v = res.valor
    if isinstance(v, (list, tuple)):
        # Con varias raíces (deflación) se muestran las primeras tres para que quepan en la tarjeta.
        muestra = ", ".join(txt_num(x, min(d, 6)) for x in v[:3])
        return muestra + (" …" if len(v) > 3 else "")
    return txt_num(v, d)


def kpis(res: Resultado, d: int) -> None:
    if "kpis" in res.ctx:
        # Los métodos directos traen sus propias tarjetas (valor, referencia, error, cota…).
        for columna, (clave, etiqueta, valor, ayuda) in zip(st.columns(len(res.ctx["kpis"])), res.ctx["kpis"]):
            with columna, contenedor(clave):
                st.metric(etiqueta, valor, help=ayuda)
        return
    es_lista = isinstance(res.valor, (list, tuple))
    residuo = residuo_absoluto(res)
    ayuda_raiz = (f"Verificación: residuo = {txt_sci(residuo, 2)}" if residuo == residuo else None)
    if es_lista:
        ayuda_raiz = "Raíces: " + ", ".join(txt_num(r, d) for r in res.valor)

    # La clave de cada tarjeta (kpi_raiz, kpi_estado_ok...) sirve para que el CSS le dé su color:
    # ámbar para la raíz, menta si convergió y coral si no.
    clave_estado = "kpi_estado_ok" if res.converged else "kpi_estado_mal"
    tarjetas = [
        ("kpi_raiz", "Raíces encontradas" if es_lista else "Raíz aproximada", _valor_texto(res, d), ayuda_raiz),
        ("kpi_iter", "Iteraciones totales" if res.id == "deflacion" else "Iteraciones", str(res.n_iter),
         f"Máximo permitido: {res.n_max}"),
        ("kpi_error", "Error máximo" if res.id == "deflacion" else "Error final", txt_sci(res.error_final),
         f"Tolerancia: {txt_sci(res.tol, 0)}"),
        (clave_estado, "Estado", "Convergió" if res.converged else "No convergió",
         "La tolerancia se alcanzó." if res.converged else "Se agotaron las iteraciones sin alcanzar la tolerancia."),
    ]
    for columna, (clave, etiqueta, valor, ayuda) in zip(st.columns(4), tarjetas):
        with columna, contenedor(clave):
            st.metric(etiqueta, valor, help=ayuda)


# ----------------------------------------------------------------------------- inspector de iteraciones
def _mover(clave_k: str, delta: int, n: int) -> None:
    # Callback de "Anterior/Siguiente": se mueve de a una iteración sin salirse de [1, n].
    st.session_state[clave_k] = min(max(st.session_state.get(clave_k, 1) + delta, 1), n)


def _ir(clave_k: str, valor: int) -> None:
    st.session_state[clave_k] = valor


@st.fragment
def inspector(res: Resultado, d: int, rango: tuple[float, float]) -> None:
    """Slider de iteraciones + gráfica + desarrollo LaTeX de la iteración elegida.

    Está marcado como fragmento porque así, al mover el slider, solo se vuelve a dibujar esta parte
    y no toda la página (ni se repite el procedimiento ni la tabla).
    """
    s = st.session_state
    n = res.n_filas
    clave_k = f"{res.id}__k"
    nombre_paso = res.ctx.get("nombre_paso", "Etapa" if res.id == "deflacion" else "Iteración")

    if n > 1:
        # Se ajusta el valor guardado por si un resultado nuevo tiene menos iteraciones que el anterior.
        s[clave_k] = min(max(int(s.get(clave_k, 1)), 1), n)
        c_ant, c_sig, c_slider, c_conv = st.columns([1.1, 1.1, 6, 2.4], vertical_alignment="bottom")
        c_ant.button("Anterior", key=f"{res.id}__prev", on_click=_mover, args=(clave_k, -1, n),
                     disabled=s[clave_k] <= 1)
        c_sig.button("Siguiente", key=f"{res.id}__next", on_click=_mover, args=(clave_k, 1, n),
                     disabled=s[clave_k] >= n)
        c_slider.slider(nombre_paso, 1, n, key=clave_k)
        idx = indice_convergencia(res)
        if idx is not None:
            c_conv.button("Ir a la convergencia", key=f"{res.id}__conv", on_click=_ir, args=(clave_k, idx + 1))
        k = int(s[clave_k])
    else:
        k = 1

    ancho_completo(st.plotly_chart, construir_figura(res, k, rango), key=f"{res.id}__fig", config=_CONFIG_PLOTLY)

    with contenedor("paso"):
        st.markdown(f"##### {etiqueta_paso(res, k)}")
        for linea in detalle_iteracion(res, k, d):
            st.latex(linea)


# ----------------------------------------------------------------------------- otras pestañas
def _animacion(res: Resultado, rango) -> None:
    st.caption("Animación continua de Plotly: usa Play y Pausa, o arrastra el control inferior.")
    ancho_completo(st.plotly_chart, figura_animada(res, rango), key=f"{res.id}__anim", config=_CONFIG_PLOTLY)


def _exportar(spec: MetodoSpec, res: Resultado, d: int, iteraciones) -> None:
    c1, c2 = st.columns(2)
    # utf-8-sig agrega una marca al inicio del archivo para que Excel abra bien los acentos y símbolos.
    c1.download_button("Descargar tabla (CSV)", res.df.to_csv(index=False).encode("utf-8-sig"),
                       file_name=f"{spec.id}_iteraciones.csv", mime="text/csv", key=f"{spec.id}__csv")
    c2.download_button("Descargar procedimiento (Markdown)", a_markdown(res, d, iteraciones).encode("utf-8"),
                       file_name=f"{spec.id}_procedimiento.md", mime="text/markdown", key=f"{spec.id}__md")
    st.caption("El procedimiento se exporta con las ecuaciones en LaTeX (entre $$ … $$).")


def mostrar_resultados(spec: MetodoSpec, res: Resultado, d: int, rango_manual, iteraciones) -> None:
    # Orden: primero las tarjetas (lo más importante), debajo las pestañas con la gráfica y la exportación.
    # Si el usuario no fijó un rango en el eje X, se calcula uno que encuadre todas las iteraciones.
    rango = tuple(rango_manual) if rango_manual else rango_auto(res)
    with contenedor("resultados", borde=False):
        kpis(res, d)
        nombres = ["Gráfica"] + (["Animación continua"] if spec.animacion_continua else []) + ["Exportar"]
        pestanas = st.tabs(nombres)   # Cada pestaña es un contexto `with` donde se dibuja su contenido.
        with pestanas[0]:
            inspector(res, d, rango)
        if spec.animacion_continua:
            with pestanas[1]:
                _animacion(res, rango)
        with pestanas[-1]:
            _exportar(spec, res, d, iteraciones)
