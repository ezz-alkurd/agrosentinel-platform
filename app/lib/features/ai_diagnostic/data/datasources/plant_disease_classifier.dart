import '../../domain/entities/diagnosis_entity.dart';
import '../models/diagnosis_model.dart';

/// Class descriptions, not model-derived severity, treatment doses or affected areas.
class PlantDiseaseKnowledge {
  static DiagnosisModel diagnosisFor(String label, double confidence, {
    double threshold = .90, int? processingMilliseconds, String? modelId,
  }) {
    const names = {
      'Tomato___Early_blight': 'Early blight',
      'Tomato___Late_blight': 'Late blight',
      'Tomato___healthy': 'Healthy leaf class',
    };
    final validScore = confidence.isFinite && confidence >= 0 && confidence <= 1;
    final inconclusive = !validScore || confidence < threshold || !names.containsKey(label);
    return DiagnosisModel(
      diseaseName: inconclusive ? 'Inconclusive' : names[label]!,
      confidenceScore: validScore ? confidence : 0,
      description: inconclusive
        ? 'The model could not make a confident match. Retake a clear close-up with one tomato leaf filling the frame.'
        : "This image most closely matches the model's ${names[label]!.toLowerCase()} class. This model covers three tomato-leaf conditions only.",
      treatment: inconclusive ? 'Try another clear close-up.' : 'Inspect other leaves and confirm the condition before choosing treatment.',
      severity: DiseaseSeverity.none,
      isHealthy: !inconclusive && label == 'Tomato___healthy',
      isInconclusive: inconclusive,
      processingMilliseconds: processingMilliseconds,
      modelId: modelId,
    );
  }
}
