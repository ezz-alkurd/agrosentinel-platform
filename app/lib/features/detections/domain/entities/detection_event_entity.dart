import 'package:equatable/equatable.dart';

class DetectionEventEntity extends Equatable {
  final String id;
  final String anomalyType;
  final double confidence;
  final double gpsLat;
  final double gpsLng;
  final DateTime timestamp;
  final String imageUrl;
  final String storagePath;
  final String status;
  final String? diseaseName;

  const DetectionEventEntity({
    required this.id,
    required this.anomalyType,
    required this.confidence,
    required this.gpsLat,
    required this.gpsLng,
    required this.timestamp,
    required this.imageUrl,
    required this.storagePath,
    required this.status,
    this.diseaseName,
  });

  @override
  List<Object?> get props => [id, anomalyType, confidence, gpsLat, gpsLng,
      timestamp, imageUrl, storagePath, status, diseaseName];
}
