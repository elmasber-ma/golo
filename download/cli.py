#!/usr/bin/env python3
"""CLI descarga estilo kurweb.gd. Uso:
  python -m download.cli <LINK> [DIR] [--file NOMBRE]
  Ej: python -m download.cli https://github.com/.../file.zip ./mis_descargas
Sin DIR (o DIR="-"): crudo a stdout (RAM por defecto, nada a disco).
Con DIR: como siempre (baja, empaqueta con relleno, devuelve ruta).
Mismos parametros que antes: con DIR el comportamiento no cambio.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from download.download import download

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__); sys.exit(1)
    link = sys.argv[1]
    args = [a for a in sys.argv[2:] if not a.startswith("--")]
    dest = args[0] if args else "-"
    fname = ""
    if "--file" in sys.argv:
        fname = sys.argv[sys.argv.index("--file") + 1]
    out = download(link, dest, fname)
    if out == "<stdout>":
        sys.stderr.write("OK -> <stdout>\n")
    else:
        print(f"OK -> {out} ({os.path.getsize(out)} bytes)")

if __name__ == "__main__":
    main()
