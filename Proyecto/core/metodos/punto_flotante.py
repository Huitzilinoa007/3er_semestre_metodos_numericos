# Punto flotante (IEEE 754): cómo se guarda un número decimal en precisión simple (32 bits) o doble (64 bits).
# Se trabaja con fracciones EXACTAS (fractions.Fraction) para que los pasos no tengan errores de redondeo propios:
# así el único redondeo que aparece es el de IEEE 754, que es justo lo que se quiere estudiar.
from __future__ import annotations

import struct  # struct empaqueta el número como lo hace la computadora; se usa para comprobar el resultado.
from dataclasses import dataclass
from fractions import Fraction

import pandas as pd

# (bits de exponente, bits de mantisa, sesgo, formato de struct)
FORMATOS = {
    "simple": (8, 23, 127, ">f"),
    "doble": (11, 52, 1023, ">d"),
}
MAX_FILAS = 220   # Tope de filas de la tabla para que números muy chicos o muy grandes no la vuelvan eterna.


@dataclass
class Representacion:
    signo: int                 # 0 positivo, 1 negativo.
    exponente_real: int        # e en 1.m × 2^e (para subnormales, el exponente mínimo).
    exponente_sesgado: int     # E = e + sesgo (0 en subnormales).
    mantisa: int               # Los bits de la mantisa como entero (23 o 52 bits).
    bits: str                  # Cadena completa de 32 o 64 bits.
    hexadecimal: str
    guardado: Fraction         # Valor exacto que queda guardado.
    redondeo: str              # Qué pasó al redondear: "exacto", "hacia abajo", "hacia arriba".
    subnormal: bool


def leer_numero(texto: str) -> Fraction:
    """Convierte el texto en una fracción exacta: acepta 0.1, -118.625, 1e-3, 1/3."""
    limpio = (texto or "").strip().replace(" ", "").replace("−", "-")
    if not limpio:
        raise ValueError("Escribe un número decimal, por ejemplo 0.1 o -118.625.")
    try:
        return Fraction(limpio)
    except (ValueError, ZeroDivisionError) as exc:
        raise ValueError(f"«{texto}» no es un número válido. Ejemplos: 0.1, -118.625, 2.5e-3, 1/3.") from exc


def a_binario(n: int) -> str:
    return format(n, "b") if n else "0"


def punto_flotante(texto: str, formato: str = "simple"):
    """Devuelve (Representacion, tabla de conversión a binario)."""
    n_exp, n_man, sesgo, fmt = FORMATOS[formato]
    v = leer_numero(texto)
    signo = 1 if v < 0 else 0
    a = abs(v)
    e_min = 1 - sesgo
    maximo = (2 - Fraction(1, 2 ** n_man)) * Fraction(2) ** sesgo
    if a > maximo:
        raise ValueError(f"|{texto}| es mayor que el máximo representable en precisión {formato} "
                         f"(≈ {float(maximo):.6g}): se guardaría como infinito (overflow).")

    # ---- 1) Tabla de conversión: parte entera por divisiones entre 2, parte fraccionaria por multiplicaciones por 2.
    entera = int(a)                  # int() trunca: la parte entera exacta.
    frac = a - entera
    filas = []
    n = entera
    while n > 0:
        filas.append({"paso": len(filas) + 1, "parte": "entera", "operación": f"{n} ÷ 2",
                      "resultado": str(n // 2), "bit": n % 2})
        n //= 2
    if entera == 0:
        filas.append({"paso": 1, "parte": "entera", "operación": "0", "resultado": "0", "bit": 0})
    bits_enteros = a_binario(entera)

    # Hasta dónde hace falta seguir con la parte fraccionaria: hasta tener la mantisa completa + 1 bit para redondear.
    if a == 0:
        e = e_min
    else:
        e = a.numerator.bit_length() - a.denominator.bit_length()
        if Fraction(2) ** e > a:
            e -= 1                       # Ahora 2^e <= a < 2^(e+1).
    e_guardado = max(e, e_min)
    ultima_pos = e_guardado - n_man - 1  # Posición (potencia de 2) del bit de redondeo.
    bits_frac = ""
    f = frac
    pos = -1
    while f != 0 and pos >= ultima_pos:
        if len(filas) >= MAX_FILAS:
            raise ValueError("El número necesita demasiados pasos para mostrarse en la tabla "
                             f"(más de {MAX_FILAS}); prueba con un número menos extremo.")
        doble = f * 2
        bit = int(doble >= 1)
        filas.append({"paso": len(filas) + 1, "parte": "fraccionaria", "operación": f"{_dec(f)} × 2",
                      "resultado": _dec(doble), "bit": bit})
        bits_frac += str(bit)
        f = doble - bit
        pos -= 1
    resto = f   # Lo que queda sin convertir (si no es 0, el número no cabe exacto en binario finito).

    # ---- 2) Redondeo al más cercano (empate: al par), que es el modo por defecto de IEEE 754.
    escala = Fraction(2) ** (e_guardado - n_man)            # Valor del último bit de la mantisa.
    q_exacto = a / escala                                   # Mantisa completa (con el 1 implícito) en unidades de ese bit.
    q = int(q_exacto)
    r = q_exacto - q
    if r > Fraction(1, 2) or (r == Fraction(1, 2) and q % 2 == 1):
        q += 1
        redondeo = "hacia arriba"
    else:
        redondeo = "exacto" if r == 0 else "hacia abajo"
    if q >= 2 ** (n_man + 1):     # El redondeo "acarreó" un bit más: 1.111…1 + 1 = 10.000…0
        q //= 2
        e_guardado += 1
    subnormal = q < 2 ** n_man   # Sin el 1 implícito: el número es subnormal (o cero).
    if e_guardado > sesgo:
        raise ValueError("Al redondear, el número se sale del rango (overflow): se guardaría como infinito.")
    E = 0 if subnormal else e_guardado + sesgo
    mantisa = q - (0 if subnormal else 2 ** n_man)
    bits = f"{signo}{E:0{n_exp}b}{mantisa:0{n_man}b}"
    hexa = f"{int(bits, 2):0{(1 + n_exp + n_man) // 4}X}"
    guardado = Fraction(q) * escala * (-1 if signo else 1)

    # Comprobación con la máquina: struct hace exactamente el mismo redondeo.
    maquina = struct.pack(fmt, float(v)).hex().upper()
    assert maquina == hexa or a == 0, (maquina, hexa)

    rep = Representacion(signo, e_guardado, E, mantisa, bits, hexa, guardado, redondeo, subnormal and a != 0)
    df = pd.DataFrame(filas)
    extra = dict(bits_enteros=bits_enteros, bits_frac=bits_frac, resto=resto, valor=v, e_normal=e,
                 n_exp=n_exp, n_man=n_man, sesgo=sesgo, cero=a == 0)
    return rep, df, extra


def _dec(fr: Fraction, cifras: int = 15) -> str:
    """Fracción en decimal: exacta si termina en pocas cifras, si no, con `cifras` dígitos significativos."""
    if fr.denominator == 1:
        return str(fr.numerator)
    # Un decimal termina si el denominador solo tiene factores 2 y 5; esos se escriben completos.
    den = fr.denominator
    for p in (2, 5):
        while den % p == 0:
            den //= p
    if den == 1:
        k = 0
        while (fr * 10 ** k).denominator != 1:
            k += 1
        if k <= 60:
            entero = fr * 10 ** k
            s = str(abs(entero.numerator)).rjust(k + 1, "0")
            texto = s[:-k] + "." + s[-k:]
            return ("-" if fr < 0 else "") + texto
    return f"{float(fr):.{cifras}g}"


def decimal_exacto(fr: Fraction) -> str:
    return _dec(fr, 17)
