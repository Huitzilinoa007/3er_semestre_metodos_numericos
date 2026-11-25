# Funciones para convertir números en texto bonito (texto plano y LaTeX).
# Aquí se separa el formato del cálculo porque así el mismo número se muestra igual en la tabla, el procedimiento y las tarjetas.
from __future__ import annotations  # Aquí se usa para poder escribir tipos como `str | None` sin problemas en versiones viejas de Python.

import math  # math trae funciones básicas (log10, isinf) que no necesitan arreglos, por eso es más ligera que numpy.

import numpy as np  # numpy se usa solo para reconocer los números complejos de numpy (np.complexfloating).


def _es_complejo(x) -> bool:
    # Aquí se revisan los dos tipos de complejo (el de Python y el de numpy) porque Müller puede devolver cualquiera de los dos.
    return isinstance(x, (complex, np.complexfloating))


def _real_tex(x: float, d: int) -> str:
    if x != x:  # Un NaN es el único número distinto de sí mismo; así se detecta sin importar math.isnan.
        return r"\text{—}"
    if math.isinf(x):  # Los infinitos se escriben con su símbolo para que no salga "inf" en medio de una ecuación.
        return r"\infty" if x > 0 else r"-\infty"
    if x == 0:
        return "0"
    # Aquí se pasa a notación científica cuando el número es muy chico o muy grande, porque con d decimales se vería como 0.000000.
    if abs(x) < 10 ** (-d) or abs(x) >= 1e7:
        mantisa, exp = f"{x:.{max(min(d, 6) - 2, 2)}e}".split("e")
        return rf"{mantisa}\times10^{{{int(exp)}}}"
    return _sin_menos_cero(f"{x:.{d}f}")


def _sin_menos_cero(texto: str) -> str:
    # Un número como -2.4e-7 redondeado a 6 decimales sale "-0.000000"; ese signo confunde, así que se quita.
    return texto[1:] if texto.startswith("-") and set(texto[1:]) <= set("0.") else texto


def tex_num(x, d: int = 6) -> str:
    """Número en LaTeX (reales, complejos y notación científica para valores extremos)."""
    if _es_complejo(x):
        z = complex(x)
        # Ya con este valor, si la parte imaginaria es de "ruido" (menor a 1e-12) se trata como real para no ensuciar el resultado.
        if abs(z.imag) <= 1e-12 * max(1.0, abs(z.real)):
            return _real_tex(z.real, d)
        signo = "+" if z.imag >= 0 else "-"
        return f"{_real_tex(z.real, d)} {signo} {_real_tex(abs(z.imag), d)}i"
    return _real_tex(float(x), d)


def tex_sub(x, d: int = 6) -> str:
    """Igual que tex_num, pero entre paréntesis si es negativo o complejo (para sustituir en fórmulas)."""
    s = tex_num(x, d)
    # Aquí se agregan paréntesis porque "2 - -1" se lee mal; con paréntesis queda "2 - (-1)".
    if s.startswith("-") or " + " in s or " - " in s:
        return rf"\left({s}\right)"
    return s


def txt_num(x, d: int = 6) -> str:
    """Número en texto plano (para tarjetas y tabla)."""
    if _es_complejo(x):
        z = complex(x)
        if abs(z.imag) <= 1e-12 * max(1.0, abs(z.real)):
            return txt_num(z.real, d)
        signo = "+" if z.imag >= 0 else "-"
        return f"{z.real:.{d}f} {signo} {abs(z.imag):.{d}f}i"
    x = float(x)
    if x != x:
        return "—"
    return _sin_menos_cero(f"{x:.{d}f}")


def txt_sci(x, d: int = 3) -> str:
    """Notación científica en texto plano; se usa para los errores porque cambian muchísimo de tamaño."""
    x = float(x)
    return "—" if x != x else f"{x:.{d}e}"


def tex_tol(tol: float) -> str:
    # Aquí se intenta escribir la tolerancia como potencia de 10 (10^{-6}) porque es como la lee cualquiera.
    e = math.log10(tol)
    if abs(e - round(e)) < 1e-9:
        return rf"10^{{{int(round(e))}}}"
    return tex_num(tol, 8)
