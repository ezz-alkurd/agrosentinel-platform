import 'package:dartz/dartz.dart';
import '../../../../core/errors/failures.dart';
import '../entities/map_marker_entity.dart';

abstract class MapRepository {
  Future<Either<Failure, List<MapMarkerEntity>>> getMarkers();
  Future<Either<Failure, DronePathEntity>> getDronePath();
}
