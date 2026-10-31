import '../../../../core/utils/event_time.dart';
import '../../../../core/network/field_api_client.dart';
import '../../domain/entities/notification_entity.dart';
import '../models/notification_model.dart';
import 'notification_datasource.dart';

/// Real notifications backed by the authenticated ASP.NET event API.
/// Each saved detection event becomes an in-app alert.
class NotificationApiDataSource implements NotificationDataSource {
  final FieldApiClient api;
  NotificationApiDataSource(this.api);
  @override
  Future<List<NotificationModel>> getNotifications() async => (await api.events()).map((row) => _map(row['id'] as String, row)).toList();
  @override
  Stream<List<NotificationModel>> get liveStream => api.watchEvents().map((rows) => rows.map((row) => _map(row['id'] as String, row)).toList());

  NotificationModel _map(String id, Map<String, dynamic> d) {
    final anomaly = (d['anomaly_type'] as String? ?? '').toLowerCase();
    final conf = (d['confidence'] as num?)?.toDouble();
    final confidence = conf != null && conf.isFinite && conf >= 0 && conf <= 1
      ? '${(conf * 100).round()}% confidence' : 'confidence unavailable';
    final disease = d['disease_name'] as String?;

    NotificationType type;
    String title;
    String body;
    switch (anomaly) {
      case 'fire':
        type = NotificationType.fire;
        title = 'Fire Detected';
        body = 'Fire detected ($confidence).';
        break;
      case 'smoke':
        type = NotificationType.fire;
        title = 'Smoke Detected';
        body = 'Smoke detected ($confidence).';
        break;
      case 'disease':
        type = NotificationType.disease;
        title = 'Plant Disease Detected';
        final name = (disease ?? 'Disease').replaceAll('___', ' — ').replaceAll('_', ' ');
        body = '$name ($confidence).';
        break;
      default:
        type = NotificationType.info;
        title = 'Detection';
        body = anomaly.isEmpty ? 'New detection event.' : anomaly;
    }

    final lat = (d['gps_lat'] as num?)?.toDouble() ?? 0.0;
    final lng = (d['gps_lng'] as num?)?.toDouble() ?? 0.0;
    final ts = parseEventTime(d['timestamp']);
    final loc = (lat == 0 && lng == 0)
        ? 'Location unavailable'
        : '${lat.toStringAsFixed(4)}, ${lng.toStringAsFixed(4)}';

    return NotificationModel(
      id: id,
      title: title,
      body: body,
      type: type,
      latitude: lat,
      longitude: lng,
      locationLabel: loc,
      timestamp: ts,
      isRead: (d['status'] as String? ?? 'new') != 'new',
    );
  }
}
