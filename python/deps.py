"""Dependencias automáticas (Colab y PC).
Uso:
    python deps.py            # instala lo que falte y dice el motor
    from deps import ensure; ensure()   # desde otro script/CLI
Sin lib C igual anda (fallback puro-python, lento).
"""
import subprocess
import sys

REQUERIDOS = ["cryptography>=42.0.0"]


def motor() -> str:
    """'c' = motor C rápido, 'puro' = fallback sin dependencias."""
    try:
        import cryptography.hazmat.primitives.ciphers  # noqa
        return "c"
    except ImportError:
        return "puro"


def ensure() -> str:
    """Instala lo que falte (pip, silencioso). Retorna el motor."""
    m = motor()
    if m == "c":
        return m
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--quiet",
             *REQUERIDOS],
            check=True,
            capture_output=True,
            timeout=300,
        )
    except Exception as e:
        print(f"deps: no se pudo instalar ({e}), sigo en puro-python")
        return "puro"
    return motor()


if __name__ == "__main__":
    print(f"motor: {'C rapido' if ensure() == 'c' else 'puro-python lento'}")
