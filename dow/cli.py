#!/usr/bin/env python3
"""CLI deepbrid. Uso:
  DEEPBRID_API_KEY=xxx python -m dow.cli link <url>      # genera link válido
  DEEPBRID_API_KEY=xxx python -m dow.cli hosts            # hosters
  DEEPBRID_API_KEY=xxx python -m dow.cli user             # cuenta
  python -m dow.cli link <url> --key xxx
"""
import sys, json, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dow.deepbrid import generar_link, hosts, user_info

def main():
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    cmd = sys.argv[1]
    key = ""
    if "--key" in sys.argv:
        key = sys.argv[sys.argv.index("--key") + 1]
    if cmd == "link":
        url = sys.argv[2] if len(sys.argv) > 2 else ""
        print(json.dumps(generar_link(url, key), indent=2, ensure_ascii=False))
    elif cmd == "hosts":
        print(json.dumps(hosts(), indent=2, ensure_ascii=False)[:2000])
    elif cmd == "user":
        print(json.dumps(user_info(key), indent=2, ensure_ascii=False))
    else:
        print(__doc__); sys.exit(1)

if __name__ == "__main__":
    main()
