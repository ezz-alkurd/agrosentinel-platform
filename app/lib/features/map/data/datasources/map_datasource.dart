import '../../../../core/utils/event_time.dart';
import '../../../../core/network/field_api_client.dart';
import '../../domain/entities/map_marker_entity.dart';
import '../models/map_marker_model.dart';

abstract class MapDataSource {
  Future<List<MapMarkerModel>> getMarkers();
  Future<DronePathEntity> getDronePath();
}

class MapDataSourceImpl implements MapDataSource {
  final FieldApiClient api;
  MapDataSourceImpl(this.api);
  @override
  Future<List<MapMarkerModel>> getMarkers() async {
    final rows = await api.events();
    return rows
        .map((d) {
          final lat = (d['gps_lat'] as num?)?.toDouble() ?? 0.0;
          final lng = (d['gps_lng'] as num?)?.toDouble() ?? 0.0;
          if (lat == 0.0 && lng == 0.0) return null; // skip placeholder coords

          final anomalyType = d['anomaly_type'] as String? ?? '';
          final label = (d['disease_name'] as String?)?.isNotEmpty == true
              ? d['disease_name'] as String
              : anomalyType.toUpperCase();

          return MapMarkerModel(
            id: d['id'] as String,
            latitude: lat,
            longitude: lng,
            type: (anomalyType == 'fire' || anomalyType == 'smoke') ? MarkerType.fire : MarkerType.disease,
            label: label,
            detectedAt: parseEventTime(d['timestamp']),
          );
        })
        .whereType<MapMarkerModel>()
        .toList();
  }

  /// Flight telemetry has not been connected. Do not invent a path or position.
  @override
  Future<DronePathEntity> getDronePath() async => const DronePathEntity();
}
