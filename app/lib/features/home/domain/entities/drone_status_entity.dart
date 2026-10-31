import 'package:equatable/equatable.dart';

enum DroneConnectionStatus { online, offline, idle, returning }

class DroneStatusEntity extends Equatable {
  final DroneConnectionStatus connectionStatus;
  final int batteryPercent;
  final int signalPercent;
  final double altitudeMeters;
  final double speedKmh;
  final double latitude;
  final double longitude;
  final String weatherCondition;
  final double temperatureCelsius;
  final int fieldCoveragePercent;

  const DroneStatusEntity({
    required this.connectionStatus,
    required this.batteryPercent,
    required this.signalPercent,
    required this.altitudeMeters,
    required this.speedKmh,
    required this.latitude,
    required this.longitude,
    required this.weatherCondition,
    required this.temperatureCelsius,
    required this.fieldCoveragePercent,
  });

  bool get isOnline => connectionStatus == DroneConnectionStatus.online;

  @override
  List<Object?> get props => [
        connectionStatus,
        batteryPercent,
        signalPercent,
        altitudeMeters,
        speedKmh,
        latitude,
        longitude,
        weatherCondition,
        temperatureCelsius,
        fieldCoveragePercent,
      ];
}
