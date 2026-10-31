import 'dart:math' as math;
import 'dart:typed_data';
import 'package:image/image.dart' as img;

const tomatoInputSize = 224;
const _precision = 1 << 22;

/// Matches Pillow's separable, antialiased bilinear resize and center crop.
/// Runs through compute(), outside Flutter's UI isolate.
Float32List prepareTomatoImage(Uint8List bytes) {
  final image = _decodePhoto(bytes);
  final width = image.width, height = image.height;
  if (math.max(width, height) / math.min(width, height) > 4) {
    throw const FormatException('Crop the photo closer to the leaf before analyzing.');
  }
  final newWidth = width <= height ? 224 : (224 * width / height).floor();
  final newHeight = height <= width ? 224 : (224 * height / width).floor();
  final pixels = _resize(image.getBytes(order: img.ChannelOrder.rgb), width, height, newWidth, newHeight);
  final offsetX = _roundEven((newWidth - 224) / 2);
  final offsetY = _roundEven((newHeight - 224) / 2);
  final tensor = Float32List(3 * 224 * 224);
  for (var y = 0; y < 224; y++) {
    for (var x = 0; x < 224; x++) {
      final source = ((y + offsetY) * newWidth + x + offsetX) * 3;
      final index = y * 224 + x;
      for (var channel = 0; channel < 3; channel++) {
        tensor[channel * 224 * 224 + index] = pixels[source + channel] / 255;
      }
    }
  }
  return tensor;
}


img.Image _decodePhoto(Uint8List bytes) {
  const invalidPhoto = FormatException('Cannot read this image. Choose a JPEG, PNG or WebP photo.');
  if (bytes.length < 12) throw invalidPhoto;
  final img.Decoder decoder;
  if (bytes[0] == 0xff && bytes[1] == 0xd8 && bytes[2] == 0xff) {
    decoder = img.JpegDecoder();
  } else if (bytes[0] == 0x89 && bytes[1] == 0x50 && bytes[2] == 0x4e && bytes[3] == 0x47 &&
      bytes[4] == 0x0d && bytes[5] == 0x0a && bytes[6] == 0x1a && bytes[7] == 0x0a) {
    decoder = img.PngDecoder();
  } else if (bytes[0] == 0x52 && bytes[1] == 0x49 && bytes[2] == 0x46 && bytes[3] == 0x46 &&
      bytes[8] == 0x57 && bytes[9] == 0x45 && bytes[10] == 0x42 && bytes[11] == 0x50) {
    decoder = img.WebPDecoder();
  } else {
    throw invalidPhoto;
  }
  try {
    final info = decoder.startDecode(bytes);
    if (info == null) throw invalidPhoto;
    if (info.width < 1 || info.height < 1 || info.width * info.height > 20000000) {
      throw const FormatException('Choose a photo smaller than 20 megapixels.');
    }
    if (info.numFrames > 1) throw const FormatException('Choose a still photo rather than an animation.');
    final decoded = decoder.decodeFrame(0);
    if (decoded == null) throw invalidPhoto;
    return img.bakeOrientation(decoded).convert(format: img.Format.uint8, numChannels: 3);
  } on RangeError {
    throw invalidPhoto;
  } on img.ImageException {
    throw invalidPhoto;
  }
}

int _roundEven(double value) {
  final floor = value.floor();
  if (value - floor == .5) return floor.isEven ? floor : floor + 1;
  return value.round();
}

List<({int start, List<int> values})> _coefficients(int source, int target) {
  final scale = source / target;
  final filterScale = math.max(1.0, scale);
  return List.generate(target, (index) {
    final center = (index + .5) * scale;
    final start = math.max(0, (center - filterScale + .5).toInt());
    final end = math.min(source, (center + filterScale + .5).toInt());
    final values = List<double>.generate(end - start,
      (i) => math.max(0.0, 1 - ((i + start - center + .5) / filterScale).abs()));
    final total = values.fold<double>(0, (sum, value) => sum + value);
    return (start: start, values: values.map((value) => (value / total * _precision).round()).toList());
  });
}

Uint8List _resize(Uint8List source, int width, int height, int newWidth, int newHeight) {
  final horizontal = Uint8List(newWidth * height * 3);
  final weightsX = _coefficients(width, newWidth);
  for (var y = 0; y < height; y++) {
    for (var x = 0; x < newWidth; x++) {
      final weights = weightsX[x];
      for (var channel = 0; channel < 3; channel++) {
        var sum = _precision ~/ 2;
        for (var i = 0; i < weights.values.length; i++) {
          sum += source[(y * width + weights.start + i) * 3 + channel] * weights.values[i];
        }
        horizontal[(y * newWidth + x) * 3 + channel] = (sum >> 22).clamp(0, 255).toInt();
      }
    }
  }
  final output = Uint8List(newWidth * newHeight * 3);
  final weightsY = _coefficients(height, newHeight);
  for (var y = 0; y < newHeight; y++) {
    final weights = weightsY[y];
    for (var x = 0; x < newWidth; x++) {
      for (var channel = 0; channel < 3; channel++) {
        var sum = _precision ~/ 2;
        for (var i = 0; i < weights.values.length; i++) {
          sum += horizontal[((weights.start + i) * newWidth + x) * 3 + channel] * weights.values[i];
        }
        output[(y * newWidth + x) * 3 + channel] = (sum >> 22).clamp(0, 255).toInt();
      }
    }
  }
  return output;
}
