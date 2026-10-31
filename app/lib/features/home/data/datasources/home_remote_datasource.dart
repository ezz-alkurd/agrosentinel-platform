import '../models/drone_status_model.dart';
abstract class HomeRemoteDataSource {
  Future<DroneStatusModel> getDroneStatus();
}
class HomeRemoteDataSourceImpl implements HomeRemoteDataSource {
  @override
  Future<DroneStatusModel> getDroneStatus() async {
    throw StateError('Flight telemetry is unavailable. No battery, weather or coverage readings have been supplied.');
  }
}
