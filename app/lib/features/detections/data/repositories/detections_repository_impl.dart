import '../../domain/entities/detection_event_entity.dart';
import '../../domain/repositories/detections_repository.dart';
import '../datasources/detections_remote_datasource.dart';

class DetectionsRepositoryImpl implements DetectionsRepository {
  final DetectionsRemoteDataSource _dataSource;

  DetectionsRepositoryImpl(this._dataSource);

  @override
  Stream<List<DetectionEventEntity>> watchEvents() =>
      _dataSource.watchEvents();
}
