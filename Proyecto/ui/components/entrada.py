# Tarjeta de datos: los campos del método, los parámetros comunes y los botones (todo en horizontal).
# Aquí se arma con la información de `registry.py` para que todos los métodos tengan la misma tarjeta
# sin repetir código.
from __future__ import annotations

import html

import numpy as np
import streamlit as st

from core.parser import ErrorExpresion, compilar, es_lista, latex_de, parsear, parsear_lista
from registry import MetodoSpec
from ui.compat import contenedor

# Tolerancias posibles: 1e-1 ... 1e-12. Se usa un slider de potencias de 10 porque escribir 0.000001 a mano es propenso a errores.
TOLERANCIAS = [float(f"1e-{k}") for k in range(1, 13)]
VELOCIDADES = ["Sin animación", "Rápida", "Normal", "Lenta"]


def clave(spec: MetodoSpec, nombre: str) -> str:
    # Cada widget lleva el id del método en su clave para que dos métodos nunca compartan valores por accidente.
    return f"{spec.id}__{nombre}"


def _mensaje(clase: str, texto: str) -> None:
    # html.escape porque el texto del mensaje puede traer lo que escribió el usuario.
    st.markdown(f'<p class="msg {clase}">{html.escape(texto)}</p>', unsafe_allow_html=True)


def _vista_previa(campo, texto):
    """Muestra en LaTeX lo que el usuario escribe; si hay error de sintaxis lo explica junto al campo."""
    if not texto or not texto.strip():
        return None
    tipo = getattr(campo, "tipo", "funcion")
    try:
        if tipo == "numero":
            from core.metodos.punto_flotante import leer_numero
            leer_numero(texto)
            return None
        if tipo == "lista" or (tipo == "lista_o_funcion" and es_lista(texto)):
            valores = parsear_lista(texto)
            st.latex(rf"\left[{', '.join(f'{v:g}' for v in valores)}\right] \quad ({len(valores)}\ \text{{valores}})")
            return None
        variables = ("x", "y") if tipo == "funcion_xy" else ("x",)
        expr = parsear(texto, variables=variables)
    except (ErrorExpresion, ValueError) as exc:
        _mensaje("msg-error", str(exc))
        return None
    st.latex(f"{campo.simbolo or 'f'}({', '.join(variables)}) = {latex_de(expr)}")
    return expr


def _indicador_bolzano(expr, a, b) -> None:
    # Aquí se avisa en vivo si el intervalo sirve, porque es el error más común en los métodos cerrados.
    if expr is None or a is None or b is None or not a < b:
        return
    try:
        f = compilar(expr)
        fa, fb = f(float(a)), f(float(b))
    except Exception:  # Si algo falla aquí no se muestra nada: es solo una ayuda, no debe romper la tarjeta.
        return
    if not (np.isfinite(fa) and np.isfinite(fb)):
        _mensaje("msg-error", "f no está definida en alguno de los extremos del intervalo.")
    elif fa == 0 or fb == 0:
        _mensaje("msg-ok", "Uno de los extremos ya es raíz de f.")
    elif fa * fb < 0:
        _mensaje("msg-ok", f"f(a) = {fa:.4g} y f(b) = {fb:.4g} cambian de signo: el intervalo cumple Bolzano.")
    else:
        _mensaje("msg-error", f"f(a) = {fa:.4g} y f(b) = {fb:.4g} tienen el mismo signo: "
                              "no se puede garantizar una raíz en [a, b].")


def limpiar(spec: MetodoSpec) -> None:
    # Se usa como callback del botón "Limpiar": Streamlit lo ejecuta ANTES de redibujar, que es cuando se puede cambiar el valor de un widget.
    s = st.session_state
    for c in spec.campos_texto:
        s[clave(spec, c.key)] = ""
    for c in spec.campos_num:
        s[clave(spec, c.key)] = None
    for sufijo in ("res", "anim", "k"):
        s.pop(clave(spec, sufijo), None)


def tarjeta_datos(spec: MetodoSpec) -> dict:
    """Dibuja la tarjeta y devuelve lo capturado (los campos vacíos llegan como '' o None)."""
    with contenedor("datos"):
        textos, expr = {}, None
        for c in spec.campos_texto:
            # Aquí NO se pasa `value=`: así el campo empieza vacío y solo muestra el placeholder (sin función precargada).
            textos[c.key] = st.text_input(c.label, key=clave(spec, c.key), placeholder=c.placeholder,
                                          help=c.ayuda or None)
            expr = _vista_previa(c, textos[c.key])

        # Selectores (precisión, fórmula…): se guardan junto con los textos porque son texto.
        for o in spec.campos_opcion:
            textos[o.key] = st.radio(o.label, o.opciones, horizontal=True, key=clave(spec, o.key), help=o.ayuda or None)

        numeros = {}
        if spec.campos_num:
            for col, c in zip(st.columns(len(spec.campos_num)), spec.campos_num):
                with col:
                    # value=None deja el número vacío al abrir; el usuario debe escribirlo.
                    if c.tipo == "entero":
                        numeros[c.key] = st.number_input(c.label, value=None, placeholder=c.placeholder, step=1,
                                                         min_value=1, max_value=300, format="%d", key=clave(spec, c.key),
                                                         help=c.ayuda or None)
                    else:
                        numeros[c.key] = st.number_input(c.label, value=None, placeholder=c.placeholder, step=0.1,
                                                         format="%g", key=clave(spec, c.key), help=c.ayuda or None)
        if spec.bolzano:
            _indicador_bolzano(expr, numeros.get("a"), numeros.get("b"))

        # Solo se muestran los controles que usa el método (los de integración, por ejemplo, no tienen tolerancia).
        controles = [c for c in ("tol", "nmax") if c in spec.controles] + ["dec"]
        tol, n_max = 1e-6, 50
        for col, control in zip(st.columns(3 if len(controles) > 1 else [1, 2]), controles):
            with col:
                if control == "tol":
                    tol = st.select_slider("Tolerancia de error", options=TOLERANCIAS, value=1e-6,
                                           format_func=lambda v: f"{v:.0e}", key=clave(spec, "tol"))
                elif control == "nmax":
                    n_max = st.slider(spec.etiqueta_nmax, 1, 100, 50 if spec.etiqueta_nmax == "Máx. iteraciones" else 20,
                                      key=clave(spec, "nmax"))
                else:
                    decimales = st.slider("Decimales mostrados", 2, 12, 6, key=clave(spec, "dec"))

        # Aquí el usuario elige qué iteraciones se desarrollan en el procedimiento. Las opciones llegan hasta 100
        # (fijas) para que el valor por defecto [1, 2, 3] siempre sea válido, aunque el máximo de iteraciones sea menor.
        iteraciones = st.multiselect(
            spec.etiqueta_pasos, options=list(range(1, 101)), default=[1, 2, 3],
            key=clave(spec, "iters"),
            help="Se desarrollan las que elijas y, al final, siempre la última: la que lleva al resultado.")

        with st.expander("Opciones de vista"):
            auto = st.checkbox("Rango del eje X automático", value=True, key=clave(spec, "auto"))
            rango = None if auto else st.slider("Rango eje X de gráfica", -10.0, 10.0, (-5.0, 5.0),
                                                key=clave(spec, "rango"))
            velocidad = st.select_slider("Velocidad de las animaciones", VELOCIDADES, value="Normal",
                                         key=clave(spec, "vel"))

        b1, b2, _ = st.columns([1, 1, 5])
        calcular = b1.button("Calcular", type="primary", key=clave(spec, "calcular"))
        b2.button("Limpiar", key=clave(spec, "limpiar"), on_click=limpiar, args=(spec,))

    return dict(textos=textos, numeros=numeros, tol=tol, n_max=n_max, decimales=decimales, rango=rango,
                iteraciones=sorted(iteraciones), velocidad=velocidad, calcular=calcular)
