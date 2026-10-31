import 'package:equatable/equatable.dart';
import '../../domain/entities/map_marker_entity.dart';

abstract class MapState extends Equatable {
  const MapState();
  @override
  List<Object?> get props => [];
}

class MapInitial extends MapState {
  const MapInitial();
}

class MapLoading extends MapState {
  const MapLoading();
}

class MapLoaded extends MapState {
  final List<MapMarkerEntity> markers;
  final DronePathEntity path;

  const MapLoaded({required this.markers, required this.path});

  @override
  List<Object?> get props => [markers, path];
}

class MapError extends MapState {
  final String message;
  const MapError(this.message);
  @override
  List<Object?> get props => [message];
}
