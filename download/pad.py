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


def generar(destino: str, mb: float = 15.0) -> str:
    """Escribe mb megas de texto aleatorio en destino. Devuelve la ruta."""
    objetivo = int(mb * 1024 * 1024)
    if objetivo <= 0:
        raise ValueError("mb tiene que ser mayor a 0")
    escritos = 0
    with open(destino, "wb") as f:
        while escritos < objetivo:
            n = min(CHUNK, objetivo - escritos)
            f.write(os.urandom(n).translate(_TABLA))
            escritos += n
    return destino


def generar_stream(mb: float = 15.0):
    """Generador, para escribir el relleno directo dentro del zip sin
    dejarlo en disco."""
    quedan = int(mb * 1024 * 1024)
    while quedan > 0:
        n = min(CHUNK, quedan)
        yield os.urandom(n).translate(_TABLA)
        quedan -= n
