import '../../../../core/network/field_api_client.dart';
import '../models/detection_event_model.dart';
abstract class DetectionsRemoteDataSource {
  Stream<List<DetectionEventModel>> watchEvents({int limit = 50});
}
class DetectionsRemoteDataSourceImpl implements DetectionsRemoteDataSource {
  final FieldApiClient api;
  DetectionsRemoteDataSourceImpl(this.api);
  @override
  Stream<List<DetectionEventModel>> watchEvents({int limit = 50}) => api.watchEvents().map((rows) => rows.take(limit).map(DetectionEventModel.fromJson).toList());
}
