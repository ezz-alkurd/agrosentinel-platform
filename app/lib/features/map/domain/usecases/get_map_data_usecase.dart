import 'package:dartz/dartz.dart';
import '../../../../core/errors/failures.dart';
import '../entities/map_marker_entity.dart';
import '../repositories/map_repository.dart';

class GetMapDataUseCase {
  final MapRepository _repository;
  GetMapDataUseCase(this._repository);

  Future<Either<Failure, List<MapMarkerEntity>>> getMarkers() =>
      _repository.getMarkers();

  Future<Either<Failure, DronePathEntity>> getDronePath() =>
      _repository.getDronePath();
}
