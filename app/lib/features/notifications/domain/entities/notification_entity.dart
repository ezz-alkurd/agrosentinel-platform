import 'package:equatable/equatable.dart';

enum NotificationType { fire, disease, info, warning }

class NotificationEntity extends Equatable {
  final String id;
  final String title;
  final String body;
  final NotificationType type;
  final double latitude;
  final double longitude;
  final String locationLabel;
  final DateTime timestamp;
  final bool isRead;

  const NotificationEntity({
    required this.id,
    required this.title,
    required this.body,
    required this.type,
    required this.latitude,
    required this.longitude,
    required this.locationLabel,
    required this.timestamp,
    this.isRead = false,
  });

  NotificationEntity copyWith({bool? isRead}) => NotificationEntity(
        id: id,
        title: title,
        body: body,
        type: type,
        latitude: latitude,
        longitude: longitude,
        locationLabel: locationLabel,
        timestamp: timestamp,
        isRead: isRead ?? this.isRead,
      );

  @override
  List<Object?> get props =>
      [id, title, body, type, latitude, longitude, locationLabel, timestamp, isRead];
}
