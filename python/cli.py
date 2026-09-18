#!/usr/bin/env python3
"""CLI igual al CryptoVault de mimapp. Uso:
  python cli.py enc <pass> <src> [dst]   # cifra archivo -> .prbx
  python cli.py dec <pass> <src.prbx> [dst]  # descifra, verifica igualdad
Archivos grandes van por tramos (RAM constante), mismo envelope.
"""
import sys, getpass
from deps import ensure
from toolsec import Vault

def main():
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)
    print(f"motor: {'C rapido' if ensure() == 'c' else 'puro-python lento'}")
    cmd, passphrase, src = sys.argv[1], sys.argv[2], sys.argv[3]
    dst = sys.argv[4] if len(sys.argv) > 4 else None
    if passphrase in ("-", "ASK"):
        passphrase = getpass.getpass("pass: ")
    v = Vault(passphrase)
    if cmd == "enc":
        out = v.encrypt_file_stream(src, dst)
        print(f"OK cifrado -> {out}")
    elif cmd == "dec":
        out = v.decrypt_file_stream(src, dst)
        if out is None:
            print("FALLO: pass incorrecta o datos alterados")
            sys.exit(2)
        print(f"OK descifrado -> {out}")
    else:
        print("cmd debe ser enc|dec")
        sys.exit(1)

if __name__ == "__main__":
    main()
