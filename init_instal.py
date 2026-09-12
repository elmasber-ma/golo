#!/usr/bin/env python3
"""init_instal.py - instala dependencias de golo si faltan.
Cifrado: `cryptography` (opcional, hay fallback puro-python).
HF: `huggingface_hub` (requerido para hf/).
Uso: python init_instal.py
"""
import importlib.util
import subprocess
import sys

DEPS = [
    ("huggingface_hub", "huggingface_hub>=0.25.0", True),
]
OPTIONAL = [
    # solo con --full: en Termux compilar cryptography cuelga, hay fallback puro
    ("cryptography", "cryptography>=42.0.0"),
]


def main():
    full = "--full" in sys.argv
    pip = [sys.executable, "-m", "pip", "install", "-q"]
    ok = True
    for mod, spec, required in DEPS:
        if importlib.util.find_spec(mod) is not None:
            print(f"OK {mod}")
            continue
        print(f"falta {mod}, instalando {spec}...", flush=True)
        r = subprocess.run(pip + [spec])
        if r.returncode != 0:
            msg = f"FALLO instalar {spec}"
            print(msg)
            if required:
                ok = False
            else:
                print(f"(opcional: se usa fallback puro-python sin {mod})")
        else:
            print(f"OK {mod} instalado")
    if full:
        for mod, spec in OPTIONAL:
            if importlib.util.find_spec(mod) is not None:
                print(f"OK {mod}")
                continue
            print(f"opcional {mod}, instalando {spec}...", flush=True)
            r = subprocess.run(pip + [spec])
            print(("OK " + mod) if r.returncode == 0 else
                  f"skip {mod} (se usa fallback puro-python)")
    else:
        print("tip: --full instala cryptography (opcional, lento en Termux)")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
