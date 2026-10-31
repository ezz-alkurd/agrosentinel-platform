import 'package:equatable/equatable.dart';

enum MarkerType { fire, disease, drone, waypoint }

/// Lightweight latitude / longitude pair used in place of
/// `google_maps_flutter`'s LatLng so the project compiles without the SDK.
class LatLng extends Equatable {
  final double latitude;
  final double longitude;

  const LatLng(this.latitude, this.longitude);

  @override
  List<Object?> get props => [latitude, longitude];
}

class MapMarkerEntity extends Equatable {
  final String id;
  final double latitude;
  final double longitude;
  final MarkerType type;
  final String label;
  final DateTime detectedAt;

  const MapMarkerEntity({
    required this.id,
    required this.latitude,
    required this.longitude,
    required this.type,
    required this.label,
    required this.detectedAt,
  });

  LatLng get latLng => LatLng(latitude, longitude);

  @override
  List<Object?> get props =>
      [id, latitude, longitude, type, label, detectedAt];
}

class DronePathEntity extends Equatable {
  final List<LatLng> pathPoints;
  final LatLng? currentPosition;

  const DronePathEntity({
    this.pathPoints = const [],
    this.currentPosition,
  });

  @override
  List<Object?> get props => [pathPoints, currentPosition];
}
