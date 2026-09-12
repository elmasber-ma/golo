#!/usr/bin/env python3
"""CLI descarga estilo kurweb.gd. Uso:
  python -m download.cli <LINK> <DIR> [--file NOMBRE]
  Ej: python -m download.cli https://github.com/.../file.zip ./mis_descargas
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from download.download import download

def main():
    if len(sys.argv) < 3 or sys.argv[1] in ("-h", "--help"):
        print(__doc__); sys.exit(1)
    link, dest = sys.argv[1], sys.argv[2]
    fname = ""
    if "--file" in sys.argv:
        fname = sys.argv[sys.argv.index("--file") + 1]
    out = download(link, dest, fname)
    print(f"OK -> {out} ({os.path.getsize(out)} bytes)")

if __name__ == "__main__":
    main()
