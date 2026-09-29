#!/usr/bin/env python3
"""CLI igual al CryptoVault de mimapp. Uso:
  python cli.py enc <pass> [src] [dst]                  # cifra -> .prbx
  python cli.py dec <pass> [src] [dst]                  # descifra
  python cli.py enc-lote <maestro> <pass_lote> [src] [dst]  # lote v2 en un paso
  python cli.py lote <pass_lote> <src> <dst>            # pega pass+datos (legacy)
`-` = stdin/stdout. Sin src/dst todo va por pipes en RAM (nada en claro
toca disco). Archivo->archivo usa streaming por tramos (RAM constante).
Los mensajes van a stderr para no ensuciar los pipes.
"""
import contextlib
import sys, getpass
from deps import ensure
from toolsec import Vault, encrypt_lote


def _aviso(msg):
    sys.stderr.write(msg + "\n")


def _leer(src):
    if src is None or src == "-":
        return sys.stdin.buffer.read()
    with open(src, "rb") as f:
        return f.read()


def _escribir(dst, data, defecto=None):
    if dst == "-" or (dst is None and defecto is None):
        sys.stdout.buffer.write(data)
        sys.stdout.buffer.flush()
        return "<stdout>"
    out = dst or defecto
    with open(out, "wb") as f:
        f.write(data)
    return out


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    with contextlib.redirect_stdout(sys.stderr):
        motor = ensure()
    _aviso(f"motor: {'C rapido' if motor == 'c' else 'puro-python lento'}")
    cmd = sys.argv[1]
    if cmd == "enc-lote":
        if len(sys.argv) < 4:
            print("uso: cli.py enc-lote <maestro> <pass_lote> [src] [dst|-]")
            sys.exit(1)
        maestro, pass_lote = sys.argv[2], sys.argv[3]
        src = sys.argv[4] if len(sys.argv) > 4 else None
        dst = sys.argv[5] if len(sys.argv) > 5 else None
        if maestro in ("-", "ASK"):
            maestro = getpass.getpass("maestro: ")
        raw = _leer(src)
        out = _escribir(dst, encrypt_lote(raw, maestro, pass_lote),
                        (src + ".prbx") if src and src != "-" else None)
        _aviso(f"OK lote cifrado -> {out}")
        return
    passphrase, src = sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None
    dst = sys.argv[4] if len(sys.argv) > 4 else None
    if passphrase in ("-", "ASK"):
        passphrase = getpass.getpass("pass: ")
    v = Vault(passphrase)
    if cmd == "enc":
        if src is not None and src != "-" and dst not in (None, "-"):
            out = v.encrypt_file_stream(src, dst or (src + ".prbx"))
        else:
            out = _escribir(dst, v.encrypt(_leer(src)),
                            (src + ".prbx") if src and src != "-" else None)
        _aviso(f"OK cifrado -> {out}")
    elif cmd == "dec":
        if src is not None and src != "-" and dst not in (None, "-"):
            out = v.decrypt_file_stream(src, dst)
        else:
            pt = v.decrypt(_leer(src))
            if pt is None:
                _aviso("FALLO: pass incorrecta o datos alterados")
                sys.exit(2)
            defecto = None
            if src and src != "-":
                defecto = src[:-5] if src.endswith(".prbx") else (src + ".dec")
            out = _escribir(dst, pt, defecto)
        if out is None:
            _aviso("FALLO: pass incorrecta o datos alterados")
            sys.exit(2)
        _aviso(f"OK descifrado -> {out}")
    elif cmd == "lote":
        if src is None or dst is None or src == "-" or dst == "-":
            print("uso: cli.py lote <pass_lote> <src> <dst> (archivos)")
            sys.exit(1)
        sha = v.empaquetar_lote(passphrase, src, dst)
        _aviso(f"LOTE {dst} {sha}")
    else:
        print("cmd debe ser enc|dec|enc-lote|lote")
        sys.exit(1)

if __name__ == "__main__":
    main()
