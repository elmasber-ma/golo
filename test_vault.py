"""Pruebas de igualdad Python (las mismas corre el cuaderno tras clonar)."""
from toolsec import Vault, is_envelope, MAGIC, VERSION

def test_roundtrip(passphrase="test-pass-123"):
    v = Vault(passphrase)
    for msg in [b"hola", b"", "ñandú-日本語".encode(), bytes(range(256)), b"A"*5000]:
        enc = v.encrypt(msg)
        assert is_envelope(enc), "sin MAGIC PRBX"
        assert enc[:4] == MAGIC and enc[4] == VERSION
        dec = v.decrypt(enc)
        assert dec == msg, f"desigualdad para {msg[:20]!r}"
    # pass incorrecta -> None
    v2 = Vault("otra-pass")
    assert v2.decrypt(v.encrypt(b"secreto")) is None
    # datos alterados -> None
    enc = bytearray(v.encrypt(b"datos"))
    enc[-1] ^= 1
    assert v.decrypt(bytes(enc)) is None
    print("OK todas las pruebas de igualdad")

if __name__ == "__main__":
    test_roundtrip()
