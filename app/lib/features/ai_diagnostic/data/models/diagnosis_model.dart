import '../../domain/entities/diagnosis_entity.dart';

class DiagnosisModel extends DiagnosisEntity {
  const DiagnosisModel({
    required super.diseaseName,
    required super.confidenceScore,
    required super.description,
    required super.treatment,
    required super.severity,
    required super.isHealthy,
    super.affectedAreas,
    super.isInconclusive,
    super.processingMilliseconds,
    super.modelId,
  });

  factory DiagnosisModel.fromJson(Map<String, dynamic> json) => DiagnosisModel(
        diseaseName: json['diseaseName'] as String,
        confidenceScore: (json['confidenceScore'] as num).toDouble(),
        description: json['description'] as String,
        treatment: json['treatment'] as String,
        severity: DiseaseSeverity.values.byName(json['severity'] as String),
        isHealthy: json['isHealthy'] as bool,
        affectedAreas: List<String>.from(json['affectedAreas'] as List? ?? []),
        isInconclusive: json['isInconclusive'] as bool? ?? false,
        processingMilliseconds: (json['processingMilliseconds'] as num?)?.toInt(),
        modelId: json['modelId'] as String?,
      );

}
