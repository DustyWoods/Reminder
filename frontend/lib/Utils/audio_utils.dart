import 'dart:typed_data';

Float32List convertBytesToFloat32(Uint8List bytes) {
  final pcmData = Float32List(bytes.length ~/ 2);
  final byteData = bytes.buffer.asByteData();
  for (var i = 0; i < pcmData.length; i++) {
    pcmData[i] = byteData.getInt16(i * 2, Endian.little) / 32768.0;
  }
  return pcmData;
}