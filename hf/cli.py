#!/usr/bin/env python3
"""CLI HF. Uso (3 args):
  python -m hf.cli <HF_TOKEN> <FILE_O_DIR> <REPO_ID>
  Ej: python -m hf.cli hf_xxx ./modelo usuario/mi-modelo
  Opcionales: --repo-type model|dataset|space --path-in-repo DIR --private
  Siempre (archivos): renombra a <sha256>.<ext> antes de subir y
  borra el local si subio bien. El nombre en HF verifica solo.
  Token tambien via env HF_TOKEN (usa - como token para leer env).
"""
import hashlib
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from hf.upload import upload

def main():
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    opts = sys.argv[1:]
    if len(a) < 3 or a[0] in ("-h", "--help"):
        print(__doc__); sys.exit(1)
    token, local, repo = a[0], a[1], a[2]
    if token == "-":
        token = os.getenv("HF_TOKEN", "")
    rt = "model"
    if "--repo-type" in opts:
        rt = opts[opts.index("--repo-type") + 1]
    pir = "."
    if "--path-in-repo" in opts:
        pir = opts[opts.index("--path-in-repo") + 1]
    if os.path.isfile(local):
        h = hashlib.sha256()
        with open(local, "rb") as f:
            while True:
                t = f.read(1024 * 1024)
                if not t:
                    break
                h.update(t)
        _, ext = os.path.splitext(local)
        nuevo = os.path.join(os.path.dirname(os.path.abspath(local)),
                             h.hexdigest() + ext)
        os.rename(local, nuevo)
        local = nuevo
        print(f"nombre: {os.path.basename(local)}")
    print(upload(token, local, repo, pir, rt, "--private" in opts))
    # Solo llega acá si subió bien (upload lanza si falla).
    if os.path.isfile(local):
        os.remove(local)
        print(f"borrado local: {local}")

if __name__ == "__main__":
    main()
