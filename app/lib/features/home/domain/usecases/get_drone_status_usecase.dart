import 'package:dartz/dartz.dart';
import '../../../../core/errors/failures.dart';
import '../entities/drone_status_entity.dart';
import '../repositories/home_repository.dart';

class GetDroneStatusUseCase {
  final HomeRepository _repository;
  GetDroneStatusUseCase(this._repository);

  Future<Either<Failure, DroneStatusEntity>> call() => _repository.getDroneStatus();
}
