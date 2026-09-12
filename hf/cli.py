#!/usr/bin/env python3
"""CLI HF. Uso (3 args):
  python -m hf.cli <HF_TOKEN> <FILE_O_DIR> <REPO_ID>
  Ej: python -m hf.cli hf_xxx ./modelo usuario/mi-modelo
  Opcionales: --repo-type model|dataset|space --path-in-repo DIR --private
  Token tambien via env HF_TOKEN (usa - como token para leer env).
"""
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
    print(upload(token, local, repo, pir, rt, "--private" in opts))

if __name__ == "__main__":
    main()
