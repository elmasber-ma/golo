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

void main(List<String> args) async {
  if (args.length < 3) {
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
