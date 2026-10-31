import 'package:equatable/equatable.dart';
import '../../domain/entities/detection_event_entity.dart';

abstract class DetectionsState extends Equatable {
  const DetectionsState();
  @override
  List<Object?> get props => [];
}

class DetectionsInitial extends DetectionsState {
  const DetectionsInitial();
}

class DetectionsLoading extends DetectionsState {
  const DetectionsLoading();
}

class DetectionsLoaded extends DetectionsState {
  final List<DetectionEventEntity> events;
  const DetectionsLoaded(this.events);
  @override
  List<Object?> get props => [events];
}

class DetectionsError extends DetectionsState {
  final String message;
  const DetectionsError(this.message);
  @override
  List<Object?> get props => [message];
}
