import '../entities/detection_event_entity.dart';

abstract class DetectionsRepository {
  Stream<List<DetectionEventEntity>> watchEvents();
}
