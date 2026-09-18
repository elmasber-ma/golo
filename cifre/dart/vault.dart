// vault.dart - CLI espejo de mimapp/lib/services/crypto_vault.dart
// Mismo envelope: PRBX | ver=1 | salt16 | nonce12 | ct | tag16
// KDF: PBKDF2-HMAC-SHA256 200000 iter, AES-256-GCM.
// Uso: dart run vault.dart enc <pass> <src> [dst]
//      dart run vault.dart dec <pass> <src.prbx> [dst]
import 'dart:convert';
import 'dart:io';
import 'dart:math';
import 'dart:typed_data';
import 'package:cryptography/cryptography.dart';

const _magic = [0x50, 0x52, 0x42, 0x58];
const _version = 1, _saltLen = 16, _kdfIter = 200000;
final _algo = AesGcm.with256bits();
final _kdf = Pbkdf2(macAlgorithm: Hmac.sha256(), iterations: _kdfIter, bits: 256);

bool isEnvelope(Uint8List d) {
  if (d.length < 4 + 1 + _saltLen + 12 + 16) return false;
  for (var i = 0; i < 4; i++) {
    if (d[i] != _magic[i]) return false;
  }
  return true;
}

Future<Uint8List> encrypt(Uint8List plain, String pass) async {
  final r = Random.secure();
  final salt = Uint8List.fromList(List.generate(_saltLen, (_) => r.nextInt(256)));
  final nonce = _algo.newNonce();
  final key = await _kdf.deriveKey(secretKey: SecretKey(utf8.encode(pass)), nonce: salt);
  final box = await _algo.encrypt(plain, secretKey: key, nonce: nonce);
  final out = BytesBuilder()
    ..add(_magic)
    ..addByte(_version)
    ..add(salt)
    ..add(nonce)
    ..add(box.cipherText)
    ..add(box.mac.bytes);
  return out.toBytes();
}

Future<Uint8List?> decrypt(Uint8List data, String pass) async {
  if (!isEnvelope(data)) return null;
  try {
    var off = 4;
    if (data[off] != _version) return null;
    off += 1;
    final salt = Uint8List.sublistView(data, off, off + _saltLen);
    off += _saltLen;
    final nonce = Uint8List.sublistView(data, off, off + 12);
    off += 12;
    final ct = Uint8List.sublistView(data, off, data.length - 16);
    final mac = Mac(Uint8List.sublistView(data, data.length - 16));
    final key = await _kdf.deriveKey(secretKey: SecretKey(utf8.encode(pass)), nonce: salt);
    final clear = await _algo.decrypt(SecretBox(ct, mac: mac, nonce: nonce), secretKey: key);
    return Uint8List.fromList(clear);
  } catch (_) {
    return null;
  }
}

/// Lote v2: `global(cdn_pass + cdn)` = UN solo PRBX con el maestro
/// sobre pass pegada + contenido:
/// `PRBX(maestro, [LOTE][u32be len][pass][datos])`.
/// v1: PRBX directo (sin pass de lote).
/// El pass global descifra TODO: pass + dato origen.
class LoteAbierto {
  final int version; // 1 o 2
  final String passLote; // '' en v1
  final Uint8List contenido;
  const LoteAbierto({
    required this.version,
    required this.passLote,
    required this.contenido,
  });
}

/// Cifra un lote v2: `global(cdn_pass + cdn)` con el maestro.
/// Lo abre `decryptLote` (y el preset de Colab lo genera igual).
Future<Uint8List> encryptLote(
    Uint8List datos, String passMaestro, String passLote) async {
  final pb = utf8.encode(passLote);
  final plano = BytesBuilder()
    ..add([0x4C, 0x4F, 0x54, 0x45]) // LOTE
    ..add([(pb.length >> 24) & 0xFF, (pb.length >> 16) & 0xFF,
        (pb.length >> 8) & 0xFF, pb.length & 0xFF])
    ..add(pb)
    ..add(datos);
  return encrypt(plano.toBytes(), passMaestro);
}

Future<LoteAbierto?> decryptLote(Uint8List data, String passMaestro) async {  try {
    final pt = await decrypt(data, passMaestro);
    if (pt == null) return null;
    // v2: marca LOTE al inicio del claro.
    if (pt.length >= 8 &&
        pt[0] == 0x4C &&
        pt[1] == 0x4F &&
        pt[2] == 0x54 &&
        pt[3] == 0x45) {
      final len =
          ByteData.sublistView(pt, 4, 8).getUint32(0, Endian.big);
      if (len <= 0 || pt.length < 8 + len) return null;
      final passLote =
          utf8.decode(Uint8List.sublistView(pt, 8, 8 + len));
      final contenido = Uint8List.sublistView(pt, 8 + len);
      return LoteAbierto(
          version: 2, passLote: passLote, contenido: contenido);
    }
    return LoteAbierto(version: 1, passLote: '', contenido: pt);
  } catch (_) {
    return null;
  }
}

void main(List<String> args) async {  if (args.length < 3) {
    print('Uso: dart run vault.dart enc|dec <pass> <src> [dst]');
    exit(1);
  }
  final cmd = args[0], pass = args[1], src = args[2];
  final dst = args.length > 3 ? args[3] : null;
  if (cmd == 'enc') {
    final plain = await File(src).readAsBytes();
    final enc = await encrypt(plain, pass);
    final out = dst ?? '$src.prbx';
    await File(out).writeAsBytes(enc);
    print('OK cifrado -> $out (${enc.length} bytes)');
  } else if (cmd == 'dec') {
    final data = await File(src).readAsBytes();
    final pt = await decrypt(Uint8List.fromList(data), pass);
    if (pt == null) {
      print('FALLO: pass incorrecta o datos alterados');
      exit(2);
    }
    final out = dst ?? (src.endsWith('.prbx') ? src.substring(0, src.length - 5) : '$src.dec');
    await File(out).writeAsBytes(pt);
    print('OK descifrado -> $out (${pt.length} bytes)');
  }
}
