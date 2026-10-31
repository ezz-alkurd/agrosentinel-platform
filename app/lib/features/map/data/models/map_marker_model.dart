import '../../domain/entities/map_marker_entity.dart';

class MapMarkerModel extends MapMarkerEntity {
  const MapMarkerModel({
    required super.id,
    required super.latitude,
    required super.longitude,
    required super.type,
    required super.label,
    required super.detectedAt,
  });

  factory MapMarkerModel.fromJson(Map<String, dynamic> json) => MapMarkerModel(
        id: json['id'] as String,
        latitude: (json['latitude'] as num).toDouble(),
        longitude: (json['longitude'] as num).toDouble(),
        type: MarkerType.values.byName(json['type'] as String),
        label: json['label'] as String,
        detectedAt: DateTime.parse(json['detectedAt'] as String),
      );

}
