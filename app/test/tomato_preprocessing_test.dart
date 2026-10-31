import 'dart:io';
import 'dart:typed_data';
import 'package:flutter_test/flutter_test.dart';
import 'package:agri_drone_ai/features/ai_diagnostic/data/datasources/tomato_preprocessing.dart';

void main() {
  // References generated independently with Python Pillow, used during training.
  for (final name in ['square', 'portrait', 'landscape', 'rotated']) {
    test('$name matches Pillow RGB resize, crop and NCHW normalization', () {
      final extension = name == 'rotated' ? 'jpg' : 'png';
      final actual = prepareTomatoImage(File('test/fixtures/$name.$extension').readAsBytesSync());
      final expected = File('test/fixtures/$name.rgb').readAsBytesSync();
      expect(actual.length, 3 * 224 * 224);
      var maximumDifference = 0.0;
      for (var pixel = 0; pixel < 224*224; pixel++) {
        for (var channel = 0; channel < 3; channel++) {
          final difference = (actual[channel*224*224+pixel] - expected[pixel*3+channel]/255).abs();
          if (difference > maximumDifference) maximumDifference = difference;
        }
      }
      // The rotated JPEG uses 4:4:4 color to isolate rotation/resize from chroma upsampling.
      // JPEG inverse-DCT rounding can still differ by a few integer RGB levels.
      expect(maximumDifference, lessThanOrEqualTo(name == 'rotated' ? 5/255 : 1e-6));
    });
  }
  test('invalid image bytes fail instead of manufacturing a prediction', () {
    expect(() => prepareTomatoImage(Uint8List.fromList([1,2,3])), throwsFormatException);
  });
}
