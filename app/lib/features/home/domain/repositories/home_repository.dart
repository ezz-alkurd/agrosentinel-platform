import 'package:dartz/dartz.dart';
import '../../../../core/errors/failures.dart';
import '../entities/drone_status_entity.dart';

abstract class HomeRepository {
  Future<Either<Failure, DroneStatusEntity>> getDroneStatus();
}
