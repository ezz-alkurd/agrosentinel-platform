import '../../../../core/utils/event_time.dart';
import '../../domain/entities/detection_event_entity.dart';

class DetectionEventModel extends DetectionEventEntity {
  const DetectionEventModel({
    required super.id,
    required super.anomalyType,
    required super.confidence,
    required super.gpsLat,
    required super.gpsLng,
    required super.timestamp,
    required super.imageUrl,
    required super.storagePath,
    required super.status,
    super.diseaseName,
  });

  factory DetectionEventModel.fromJson(Map<String, dynamic> d) {
    return DetectionEventModel(
      id: d['id'] as String,
      anomalyType: d['anomaly_type'] as String? ?? '',
      confidence: (d['confidence'] as num?)?.toDouble() ?? 0.0,
      gpsLat: (d['gps_lat'] as num?)?.toDouble() ?? 0.0,
      gpsLng: (d['gps_lng'] as num?)?.toDouble() ?? 0.0,
      timestamp: parseEventTime(d['timestamp']),
      imageUrl: d['image_url'] as String? ?? '',
      storagePath: d['storage_path'] as String? ?? '',
      status: d['status'] as String? ?? 'new',
      diseaseName: d['disease_name'] as String?,
    );
  }
}
