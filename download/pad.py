"""pad.py - genera el .txt de relleno aleatorio (10-20 MB).

Se usa al descargar: al lado del archivo bajado se agrega este txt de texto
aleatorio y despues se empaqueta todo junto. El relleno sale de os.urandom
mapeado a un alfabeto con translate(), asi que va a ~1 GB/s y es aleatorio de
verdad (no PRNG sembrado).

    from download.pad import generar
    generar("relleno.txt", mb=15)
"""
from __future__ import annotations

import os
import random

# Letras, digitos y signos. El salto de linea se mete aparte.
ALFABETO = (
    "abcdefghijklmnopqrstuvwxyz"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789"
    ".,;:!?-_/()[]{}<>@#$%&*+=~^|"
)
SALTO_CADA = 96      # 1 de cada ~96 caracteres es un \n
CHUNK = 4 * 1024 * 1024


def _tabla() -> bytes:
    """Tabla de traduccion de 256 bytes: cada byte -> un caracter del alfabeto."""
    base = ALFABETO.encode()
    tabla = bytearray(256)
    for i in range(256):
        tabla[i] = base[i % len(base)]
    cada = max(1, 256 // SALTO_CADA)
    for i in range(0, 256, cada):
        tabla[i] = 0x0A
    return bytes(tabla)


_TABLA = _tabla()


# El relleno va de 10 a 20MB, sorteado cada vez.
MB_MIN, MB_MAX = 10.0, 20.0


def mb_aleatorio() -> float:
    """Sortea el tamano del relleno, entre 10 y 20MB."""
    return random.uniform(MB_MIN, MB_MAX)


def generar(destino: str) -> str:
    """Escribe el relleno de texto aleatorio (10-20MB) en destino."""
    objetivo = int(mb_aleatorio() * 1024 * 1024)
    escritos = 0
    with open(destino, "wb") as f:
        while escritos < objetivo:
            n = min(CHUNK, objetivo - escritos)
            f.write(os.urandom(n).translate(_TABLA))
            escritos += n
    return destino


def generar_stream():
    """Generador del relleno (10-20MB sorteados), para escribirlo directo
    dentro del zip sin dejarlo en disco."""
    quedan = int(mb_aleatorio() * 1024 * 1024)
    while quedan > 0:
        n = min(CHUNK, quedan)
        yield os.urandom(n).translate(_TABLA)
        quedan -= n
