"""
vault V2 - compatible con Dart mimapp/lib/services/crypto_vault.dart
Solo cifrado fuerte (sin XOR).

Formato envelope v1:
  MAGIC "PRBX" | version u8=1 | salt 16B | nonce 12B | ciphertext | tag 16B

KDF: PBKDF2-HMAC-SHA256, 200000 iter, 32 bytes, pwd=utf8(passphrase)
AEAD: AES-256-GCM, nonce 12B aleatorio, AAD vacio.

Backend: usa `cryptography` si esta instalado (rapido),
si no usa implementacion pura-python (lenta pero sin dependencias).
"""
from __future__ import annotations
import hashlib
import os
import secrets

MAGIC = b"PRBX"
VERSION = 1
SALT_LEN = 16
NONCE_LEN = 12
TAG_LEN = 16
KDF_ITER = 200000


def is_envelope(data: bytes) -> bool:
    return len(data) >= 4 + 1 + SALT_LEN + NONCE_LEN + TAG_LEN and data[0:4] == MAGIC


def _derive_key(passphrase: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", passphrase.encode("utf-8"), salt, KDF_ITER, dklen=32)


# ---------------------------------------------------------------- AES-GCM
def _has_lib() -> bool:
    """True si está `cryptography` (motor C, streaming)."""
    try:
        import cryptography.hazmat.primitives.ciphers  # noqa
        return True
    except ImportError:
        return False


def _aesgcm_encrypt(key: bytes, nonce: bytes, plain: bytes) -> bytes:
    """Retorna ciphertext+tag(16). Intenta cryptography, si no puro-python."""
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        return AESGCM(key).encrypt(nonce, plain, None)
    except ImportError:
        return _aesgcm_pure_encrypt(key, nonce, plain)


def _aesgcm_decrypt(key: bytes, nonce: bytes, ct_and_tag: bytes) -> bytes:
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        return AESGCM(key).decrypt(nonce, ct_and_tag, None)
    except ImportError:
        return _aesgcm_pure_decrypt(key, nonce, ct_and_tag)


# ------------------------- AES-256 puro-python + GHASH (fallback) ----------
# S-box AES estandar
_SBOX = (
    0x63,0x7c,0x77,0x7b,0xf2,0x6b,0x6f,0xc5,0x30,0x01,0x67,0x2b,0xfe,0xd7,0xab,0x76,
    0xca,0x82,0xc9,0x7d,0xfa,0x59,0x47,0xf0,0xad,0xd4,0xa2,0xaf,0x9c,0xa4,0x72,0xc0,
    0xb7,0xfd,0x93,0x26,0x36,0x3f,0xf7,0xcc,0x34,0xa5,0xe5,0xf1,0x71,0xd8,0x31,0x15,
    0x04,0xc7,0x23,0xc3,0x18,0x96,0x05,0x9a,0x07,0x12,0x80,0xe2,0xeb,0x27,0xb2,0x75,
    0x09,0x83,0x2c,0x1a,0x1b,0x6e,0x5a,0xa0,0x52,0x3b,0xd6,0xb3,0x29,0xe3,0x2f,0x84,
    0x53,0xd1,0x00,0xed,0x20,0xfc,0xb1,0x5b,0x6a,0xcb,0xbe,0x39,0x4a,0x4c,0x58,0xcf,
    0xd0,0xef,0xaa,0xfb,0x43,0x4d,0x33,0x85,0x45,0xf9,0x02,0x7f,0x50,0x3c,0x9f,0xa8,
    0x51,0xa3,0x40,0x8f,0x92,0x9d,0x38,0xf5,0xbc,0xb6,0xda,0x21,0x10,0xff,0xf3,0xd2,
    0xcd,0x0c,0x13,0xec,0x5f,0x97,0x44,0x17,0xc4,0xa7,0x7e,0x3d,0x64,0x5d,0x19,0x73,
    0x60,0x81,0x4f,0xdc,0x22,0x2a,0x90,0x88,0x46,0xee,0xb8,0x14,0xde,0x5e,0x0b,0xdb,
    0xe0,0x32,0x3a,0x0a,0x49,0x06,0x24,0x5c,0xc2,0xd3,0xac,0x62,0x91,0x95,0xe4,0x79,
    0xe7,0xc8,0x37,0x6d,0x8d,0xd5,0x4e,0xa9,0x6c,0x56,0xf4,0xea,0x65,0x7a,0xae,0x08,
    0xba,0x78,0x25,0x2e,0x1c,0xa6,0xb4,0xc6,0xe8,0xdd,0x74,0x1f,0x4b,0xbd,0x8b,0x8a,
    0x70,0x3e,0xb5,0x66,0x48,0x03,0xf6,0x0e,0x61,0x35,0x57,0xb9,0x86,0xc1,0x1d,0x9e,
    0xe1,0xf8,0x98,0x11,0x69,0xd9,0x8e,0x94,0x9b,0x1e,0x87,0xe9,0xce,0x55,0x28,0xdf,
    0x8c,0xa1,0x89,0x0d,0xbf,0xe6,0x42,0x68,0x41,0x99,0x2d,0x0f,0xb0,0x54,0xbb,0x16,
)
_RCON = (0x01,0x02,0x04,0x08,0x10,0x20,0x40,0x80,0x1b,0x36)

def _xtime(a: int) -> int:
    return ((a << 1) ^ 0x1b) & 0xff if a & 0x80 else (a << 1) & 0xff

def _mix_col(c0,c1,c2,c3):
    t0=c0^c1^c2^c3
    u=c0
    r0=c0^_xtime(c0^c1); r1=c1^_xtime(c1^c2); r2=c2^_xtime(c2^c3); r3=c3^_xtime(c3^u)
    return r0^ t0 ^ 0 if False else (r0, r1, r2, r3)

def _aes256_expand(key: bytes) -> list:
    # retorna lista de 60 words de 32b
    Nk, Nb, Nr = 8, 4, 14
    w = [int.from_bytes(key[i*4:(i+1)*4], "big") for i in range(Nk)]
    for i in range(Nk, Nb*(Nr+1)):
        temp = w[i-1]
        if i % Nk == 0:
            # RotWord + SubWord + Rcon
            temp = (((_SBOX[(temp>>16)&0xff])<<24)|((_SBOX[(temp>>8)&0xff])<<16)|((_SBOX[temp&0xff])<<8)|(_SBOX[(temp>>24)&0xff]))
            temp ^= (_RCON[i//Nk-1] << 24)
        elif i % Nk == 4:
            temp = ((_SBOX[(temp>>24)&0xff]<<24)|(_SBOX[(temp>>16)&0xff]<<16)|(_SBOX[(temp>>8)&0xff]<<8)|(_SBOX[temp&0xff]))
        w.append(w[i-Nk] ^ temp)
    return w

def _gmul(a: int, b: int) -> int:
    p = 0
    for _ in range(8):
        if b & 1:
            p ^= a
        hi = a & 0x80
        a = (a << 1) & 0xff
        if hi:
            a ^= 0x1b
        b >>= 1
    return p


def _aes_block_encrypt(block: bytes, w: list) -> bytes:
    s = list(block)
    # AddRoundKey 0
    for i in range(16):
        s[i] ^= (w[i//4] >> (24-8*(i%4))) & 0xff
    Nr = 14
    for rnd in range(1, Nr+1):
        # SubBytes
        s = [_SBOX[b] for b in s]
        # ShiftRows
        s = [s[0],s[5],s[10],s[15], s[4],s[9],s[14],s[3], s[8],s[13],s[2],s[7], s[12],s[1],s[6],s[11]]
        if rnd != Nr:
            for c in range(4):
                a0,a1,a2,a3 = s[c*4],s[c*4+1],s[c*4+2],s[c*4+3]
                s[c*4]   = _gmul(a0,2)^_gmul(a1,3)^a2^a3
                s[c*4+1] = a0^_gmul(a1,2)^_gmul(a2,3)^a3
                s[c*4+2] = a0^a1^_gmul(a2,2)^_gmul(a3,3)
                s[c*4+3] = _gmul(a0,3)^a1^a2^_gmul(a3,2)
        # AddRoundKey
        base = rnd*4
        for i in range(16):
            s[i] ^= (w[base+i//4] >> (24-8*(i%4))) & 0xff
    return bytes(s)

_R64 = 0xE1000000000000000000000000000000  # R para GHASH (128 bits)

def _gf_mul(x: int, y: int) -> int:
    z = 0
    v = y
    for i in range(128):
        if (x >> (127-i)) & 1:
            z ^= v
        if v & 1:
            v = (v >> 1) ^ _R64
        else:
            v >>= 1
    return z & ((1 << 128) - 1)

def _ghash(h: int, aad: bytes, ct: bytes) -> int:
    x = 0
    for data in (aad, ct):
        for i in range(0, len(data), 16):
            blk = data[i:i+16].ljust(16, b"\x00")
            x = _gf_mul(x ^ int.from_bytes(blk, "big"), h)
    ln = (len(aad)*8).to_bytes(8,"big") + (len(ct)*8).to_bytes(8,"big")
    x = _gf_mul(x ^ int.from_bytes(ln, "big"), h)
    return x

def _inc32(b: bytes) -> bytes:
    v = int.from_bytes(b, "big")
    lo = (v & 0xffffffff) + 1 & 0xffffffff
    return ((v & ~0xffffffff) | lo).to_bytes(16, "big")

def _aesgcm_pure_encrypt(key: bytes, nonce: bytes, plain: bytes) -> bytes:
    assert len(key) == 32 and len(nonce) == 12
    w = _aes256_expand(key)
    H = int.from_bytes(_aes_block_encrypt(b"\x00"*16, w), "big")
    j0 = nonce + b"\x00\x00\x00\x01"
    # CTR
    ct = bytearray()
    ctr = _inc32(j0)
    for i in range(0, len(plain), 16):
        ks = _aes_block_encrypt(ctr, w)
        blk = plain[i:i+16]
        ct += bytes(a ^ b for a, b in zip(blk, ks))
        ctr = _inc32(ctr)
    ct = bytes(ct)
    s = _ghash(H, b"", ct)
    tag = (int.from_bytes(_aes_block_encrypt(j0, w), "big") ^ s).to_bytes(16, "big")
    return ct + tag

def _aesgcm_pure_decrypt(key: bytes, nonce: bytes, ct_and_tag: bytes) -> bytes:
    assert len(key) == 32 and len(nonce) == 12
    if len(ct_and_tag) < 16:
        raise ValueError("ciphertext muy corto")
    ct, tag = ct_and_tag[:-16], ct_and_tag[-16:]
    w = _aes256_expand(key)
    H = int.from_bytes(_aes_block_encrypt(b"\x00"*16, w), "big")
    j0 = nonce + b"\x00\x00\x00\x01"
    s = _ghash(H, b"", ct)
    expect = (int.from_bytes(_aes_block_encrypt(j0, w), "big") ^ s).to_bytes(16, "big")
    if expect != tag:
        raise ValueError("auth fail: passphrase incorrecta o datos alterados")
    pt = bytearray()
    ctr = _inc32(j0)
    for i in range(0, len(ct), 16):
        ks = _aes_block_encrypt(ctr, w)
        blk = ct[i:i+16]
        pt += bytes(a ^ b for a, b in zip(blk, ks))
        ctr = _inc32(ctr)
    return bytes(pt)


# ---------------------------------------------------------------- envelope
def encrypt(plain: bytes, passphrase: str) -> bytes:
    salt = secrets.token_bytes(SALT_LEN)
    nonce = secrets.token_bytes(NONCE_LEN)
    key = _derive_key(passphrase, salt)
    ct_tag = _aesgcm_encrypt(key, nonce, bytes(plain))
    return MAGIC + bytes([VERSION]) + salt + nonce + ct_tag


def decrypt(data: bytes, passphrase: str) -> bytes | None:
    if not is_envelope(data):
        return None
    try:
        off = 4
        if data[off] != VERSION:
            return None
        off += 1
        salt = bytes(data[off:off+SALT_LEN]); off += SALT_LEN
        nonce = bytes(data[off:off+NONCE_LEN]); off += NONCE_LEN
        ct_tag = bytes(data[off:])
        if len(ct_tag) < TAG_LEN:
            return None
        key = _derive_key(passphrase, salt)
        return _aesgcm_decrypt(key, nonce, ct_tag)
    except Exception:
        return None


# ---------------------------------------------------------------- lote v2
# global(cdn_pass + cdn): UN solo PRBX con el maestro sobre
# pass pegada + contenido: PRBX(maestro, [LOTE][u32be len][pass][datos]).
import struct as _struct


def encrypt_lote(datos: bytes, maestro: str, pass_lote: str) -> bytes:
    pb = pass_lote.encode("utf-8")
    plano = b"LOTE" + _struct.pack(">I", len(pb)) + pb + bytes(datos)
    return encrypt(plano, maestro)


def decrypt_lote(data: bytes, maestro: str) -> tuple[str, bytes] | None:
    """Retorna (pass_lote, contenido). v1 -> ('', contenido)."""
    pt = decrypt(bytes(data), maestro)
    if pt is None:
        return None
    if len(pt) >= 8 and pt[:4] == b"LOTE":
        (ln,) = _struct.unpack(">I", pt[4:8])
        if ln <= 0 or len(pt) < 8 + ln:
            return None
        return (pt[8:8 + ln].decode("utf-8"), pt[8 + ln:])
    return ("", pt)


class Vault:
    """API simple, misma semantica que CryptoVault Dart."""
    def __init__(self, passphrase: str):
        self.passphrase = passphrase

    def encrypt(self, plain: bytes) -> bytes:
        return encrypt(bytes(plain), self.passphrase)

    def decrypt(self, data: bytes) -> bytes | None:
        return decrypt(bytes(data), self.passphrase)

    def encrypt_file(self, src: str, dst: str | None = None) -> str:
        with open(src, "rb") as f:
            raw = f.read()
        enc = self.encrypt(raw)
        out = dst or (src + ".prbx")
        with open(out, "wb") as f:
            f.write(enc)
        return out

    def encrypt_file_stream(self, src: str, dst: str | None = None,
                            tramo: int = 1024 * 1024) -> str:
        """Cifra por tramos, RAM constante. Mismo envelope v1 (Dart lo abre).
        Sin lib C usa el método entero (lento, solo archivos chicos)."""
        out = dst or (src + ".prbx")
        if not _has_lib():
            return self.encrypt_file(src, out)
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        salt = secrets.token_bytes(SALT_LEN)
        nonce = secrets.token_bytes(NONCE_LEN)
        key = _derive_key(self.passphrase, salt)
        enc = Cipher(algorithms.AES(key), modes.GCM(nonce)).encryptor()
        with open(src, "rb") as fin, open(out, "wb") as fout:
            fout.write(MAGIC + bytes([VERSION]) + salt + nonce)
            while True:
                trozo = fin.read(tramo)
                if not trozo:
                    break
                fout.write(enc.update(bytes(trozo)))
            fout.write(enc.finalize() + enc.tag)
        return out

    def decrypt_file(self, src: str, dst: str | None = None) -> str | None:
        with open(src, "rb") as f:
            raw = f.read()
        pt = self.decrypt(raw)
        if pt is None:
            return None
        if dst is None:
            dst = src[:-5] if src.endswith(".prbx") else (src + ".dec")
        with open(dst, "wb") as f:
            f.write(pt)
        return dst

    def encrypt_lote_file(self, src: str, maestro: str, pass_lote: str,
                          dst: str | None = None) -> str:
        """Lote v2: pass pegada + contenido, todo con el maestro."""
        with open(src, "rb") as f:
            raw = f.read()
        out = dst or (src + ".prbx")
        with open(out, "wb") as f:
            f.write(encrypt_lote(raw, maestro, pass_lote))
        return out

    def decrypt_lote_file(self, src: str, maestro: str,
                          dst: str | None = None) -> tuple[str, str] | None:
        """Abre lote v1/v2. Retorna (pass_lote, path_contenido)."""
        with open(src, "rb") as f:
            raw = f.read()
        r = decrypt_lote(raw, maestro)
        if r is None:
            return None
        pass_lote, contenido = r
        if dst is None:
            dst = src[:-5] if src.endswith(".prbx") else (src + ".dec")
        with open(dst, "wb") as f:
            f.write(contenido)
        return (pass_lote, dst)

    def decrypt_file_stream(self, src: str, dst: str | None = None,
                            tramo: int = 1024 * 1024) -> str | None:
        """Descifra por tramos, RAM constante. Sin lib C usa el entero."""
        if dst is None:
            dst = src[:-5] if src.endswith(".prbx") else (src + ".dec")
        if not _has_lib():
            return self.decrypt_file(src, dst)
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        total = os.path.getsize(src)
        cabeza = 4 + 1 + SALT_LEN + NONCE_LEN
        if total < cabeza + TAG_LEN:
            return None
        with open(src, "rb") as fin:
            mag = fin.read(4)
            ver = fin.read(1)
            if mag != MAGIC or not ver or ver[0] != VERSION:
                return None
            salt = fin.read(SALT_LEN)
            nonce = fin.read(NONCE_LEN)
            key = _derive_key(self.passphrase, salt)
            # El tag va al final: se lee primero y entra en el modo.
            fin.seek(total - TAG_LEN)
            tag = fin.read(TAG_LEN)
            if len(tag) != TAG_LEN:
                return None
            fin.seek(cabeza)
            dec = Cipher(
                algorithms.AES(key), modes.GCM(nonce, tag)).decryptor()
            try:
                with open(dst, "wb") as fout:
                    queda = total - cabeza - TAG_LEN
                    while queda > 0:
                        trozo = fin.read(min(tramo, queda))
                        if not trozo:
                            raise ValueError("corte")
                        queda -= len(trozo)
                        fout.write(dec.update(trozo))
                    fout.write(dec.finalize())
            except Exception:
                try:
                    os.remove(dst)
                except OSError:
                    pass
                return None
        return dst
