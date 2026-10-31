import 'package:dartz/dartz.dart';
import '../../../../core/errors/failures.dart';
import '../../domain/entities/map_marker_entity.dart';
import '../../domain/repositories/map_repository.dart';
import '../datasources/map_datasource.dart';

class MapRepositoryImpl implements MapRepository {
  final MapDataSource _source;
  MapRepositoryImpl(this._source);

  @override
  Future<Either<Failure, List<MapMarkerEntity>>> getMarkers() async {
    try {
      final markers = await _source.getMarkers();
      return Right(markers);
    } catch (e) {
      return Left(ServerFailure(e.toString()));
    }
  }

  @override
  Future<Either<Failure, DronePathEntity>> getDronePath() async {
    try {
      final path = await _source.getDronePath();
      return Right(path);
    } catch (e) {
      return Left(ServerFailure(e.toString()));
    }
  }
}
