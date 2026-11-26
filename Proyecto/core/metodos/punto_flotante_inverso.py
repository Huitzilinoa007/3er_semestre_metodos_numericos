# Punto flotante, sentido inverso: de la representación IEEE 754 (bits o hexadecimal) al número decimal.
# Se suma el valor de cada bit (exponente: potencias 2^k; mantisa: potencias 2^-j) con fracciones exactas.
from __future__ import annotations

import re
from fractions import Fraction

import pandas as pd

from .punto_flotante import FORMATOS


def leer_bits(texto: str, formato: str) -> str:
    """Acepta bits («0 01111011 1001…», con espacios, | o _) o hexadecimal («0x3DCCCCCD»). Devuelve la cadena de bits."""
    n_exp, n_man, _, _ = FORMATOS[formato]
    total = 1 + n_exp + n_man
    limpio = re.sub(r"[\s|_]", "", (texto or "").strip())
    if not limpio:
        raise ValueError("Escribe los bits (ej: 0 01111011 10011001100110011001101) o el hexadecimal (ej: 0x3DCCCCCD).")
    con_prefijo = limpio.lower().startswith("0x")
    if not con_prefijo and set(limpio) <= {"0", "1"} and len(limpio) == total:
        return limpio                                   # Cadena de bits completa.
    h = limpio[2:] if con_prefijo else limpio
    if re.fullmatch(r"[0-9A-Fa-f]+", h) and len(h) == total // 4:
        return format(int(h, 16), f"0{total}b")         # Hexadecimal: cada dígito son 4 bits.
    raise ValueError(f"En precisión {formato} escribe {total} bits (1 de signo, {n_exp} de exponente y {n_man} de "
                     f"mantisa) o {total // 4} dígitos hexadecimales (ej: 0x3DCCCCCD en simple). «{texto.strip()}» "
                     "no tiene ese tamaño o tiene caracteres no válidos.")


def punto_flotante_inverso(texto: str, formato: str = "simple"):
    """Devuelve (datos, tabla con una fila por bit de exponente y de mantisa)."""
    n_exp, n_man, sesgo, _ = FORMATOS[formato]
    bits = leer_bits(texto, formato)
    s, e_bits, m_bits = bits[0], bits[1:1 + n_exp], bits[1 + n_exp:]
    filas = []
    acumulado = 0
    for k, b in enumerate(e_bits):
        peso = 2 ** (n_exp - 1 - k)
        acumulado += int(b) * peso
        filas.append({"paso": len(filas) + 1, "parte": "exponente", "posición": f"2^{n_exp - 1 - k}",
                      "bit": int(b), "valor": str(peso), "aporte": str(int(b) * peso), "acumulado": str(acumulado)})
    E = int(e_bits, 2)
    frac = Fraction(0)
    for j, b in enumerate(m_bits, start=1):
        peso = Fraction(1, 2 ** j)
        frac += int(b) * peso
        filas.append({"paso": len(filas) + 1, "parte": "mantisa", "posición": f"2^-{j}", "bit": int(b),
                      "valor": _corto(peso), "aporte": _corto(int(b) * peso), "acumulado": _corto(frac)})
    signo = -1 if s == "1" else 1
    if E == 2 ** n_exp - 1:
        caso = "nan" if frac else "infinito"
        valor = None
    elif E == 0:
        caso = "cero" if frac == 0 else "subnormal"
        valor = signo * frac * Fraction(2) ** (1 - sesgo)
    else:
        caso = "normal"
        valor = signo * (1 + frac) * Fraction(2) ** (E - sesgo)
    datos = dict(bits=bits, s=int(s), e_bits=e_bits, m_bits=m_bits, E=E, frac=frac, caso=caso, valor=valor,
                 n_exp=n_exp, n_man=n_man, sesgo=sesgo, hexadecimal=f"{int(bits, 2):0{len(bits) // 4}X}")
    return datos, pd.DataFrame(filas)


def _corto(fr: Fraction) -> str:
    """Fracción en decimal exacto si es corta; si no, con 17 cifras significativas."""
    from .punto_flotante import _dec
    texto = _dec(fr, 17)
    return texto if len(texto) <= 24 else f"{float(fr):.17g}"
