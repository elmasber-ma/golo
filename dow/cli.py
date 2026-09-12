#!/usr/bin/env python3
"""CLI deepbrid, llamable desde argumentos (colab cells / shell).
Uso:
  python -m dow.cli <TOKEN> <LINK>            # forma directa: token + link
  python -m dow.cli link <url> --key <TOKEN>  # forma explícita
  DEEPBRID_API_KEY=xxx python -m dow.cli link <url>
  python -m dow.cli hosts [TOKEN]             # hosters (token opcional)
  python -m dow.cli user <TOKEN>              # info cuenta
"""
import sys, json, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dow.deepbrid import generar_link, hosts, user_info

def _key_flag():
    if "--key" in sys.argv:
        i = sys.argv.index("--key")
        return sys.argv[i + 1] if i + 1 < len(sys.argv) else ""
    return ""

def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__); sys.exit(1)
    if a[0] in ("-h", "--help", "help"):
        print(__doc__); return
    if a[0] == "link":
        # link <url> [--key TOKEN]
        url = a[1] if len(a) > 1 else ""
        print(json.dumps(generar_link(url, _key_flag()), indent=2, ensure_ascii=False))
    elif a[0] == "hosts":
        print(json.dumps(hosts(), indent=2, ensure_ascii=False)[:2000])
    elif a[0] == "user":
        key = a[1] if len(a) > 1 else _key_flag()
        print(json.dumps(user_info(key), indent=2, ensure_ascii=False))
    elif len(a) >= 2:
        # forma directa: <TOKEN> <LINK>  (igual que mimapp: token primero)
        print(json.dumps(generar_link(a[1], a[0]), indent=2, ensure_ascii=False))
    else:
        print(__doc__); sys.exit(1)

if __name__ == "__main__":
    main()
