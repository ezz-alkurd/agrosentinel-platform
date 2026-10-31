import 'package:dartz/dartz.dart';
import '../../../../core/errors/failures.dart';
import '../../domain/entities/drone_status_entity.dart';
import '../../domain/repositories/home_repository.dart';
import '../datasources/home_remote_datasource.dart';

class HomeRepositoryImpl implements HomeRepository {
  final HomeRemoteDataSource _remote;
  HomeRepositoryImpl(this._remote);

  @override
  Future<Either<Failure, DroneStatusEntity>> getDroneStatus() async {
    try {
      final model = await _remote.getDroneStatus();
      return Right(model);
    } catch (e) {
      return Left(ServerFailure(e.toString()));
    }
  }
}
