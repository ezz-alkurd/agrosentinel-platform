import 'dart:convert';
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import '../models/diagnosis_model.dart';
import 'diagnostic_datasource.dart';
import 'plant_disease_classifier.dart';
import 'tomato_preprocessing.dart';

class OnDeviceDiagnosticDataSource implements DiagnosticDataSource {
  final MethodChannel _channel;
  final AssetBundle _assets;
  OnDeviceDiagnosticDataSource({MethodChannel? channel, AssetBundle? assets})
      : _channel = channel ?? const MethodChannel('agrosentinel/plant_inference'),
        _assets = assets ?? rootBundle;

  @override
  Future<DiagnosisModel> analyzeImage(File image) async {
    if (kIsWeb || defaultTargetPlatform != TargetPlatform.android) {
      throw StateError('On-device analysis is available in the Android app.');
    }
    if (await image.length() > 8 * 1024 * 1024) {
      throw const FormatException('Choose a photo smaller than 8 MB.');
    }
    final metadata = jsonDecode(await _assets.loadString('assets/models/tomato_closeup.json')) as Map<String, dynamic>;
    final tensor = await compute(prepareTomatoImage, await image.readAsBytes());
    try {
      final response = await _channel.invokeMapMethod<String, dynamic>('analyze', {'input': tensor});
      if (response == null) throw StateError('The model returned no result.');
      final scores = (response['probabilities'] as List).cast<num>().map((n) => n.toDouble()).toList();
      final labels = (metadata['labels'] as List).cast<String>();
      if (scores.length != labels.length || scores.any((n) => !n.isFinite || n < 0 || n > 1)) {
        throw StateError('The model returned an invalid result.');
      }
      var best = 0;
      for (var index = 1; index < scores.length; index++) {
        if (scores[index] > scores[best]) best = index;
      }
      return PlantDiseaseKnowledge.diagnosisFor(labels[best], scores[best],
        threshold: (metadata['threshold'] as num).toDouble(),
        processingMilliseconds: (response['inferenceMs'] as num).round(),
        modelId: metadata['model_id'] as String);
    } on MissingPluginException {
      throw StateError('Install a fresh APK containing the on-device model runtime.');
    } on PlatformException catch (error) {
      throw StateError(error.code == 'BUSY'
          ? 'An analysis is already running. Please wait.'
          : 'The on-device model could not run. Restart the app or install the latest APK.');
    }
  }
}
