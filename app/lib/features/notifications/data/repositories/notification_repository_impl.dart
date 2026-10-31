import 'package:dartz/dartz.dart';
import '../../../../core/errors/failures.dart';
import '../../domain/entities/notification_entity.dart';
import '../../domain/repositories/notification_repository.dart';
import '../datasources/notification_datasource.dart';

class NotificationRepositoryImpl implements NotificationRepository {
  final NotificationDataSource _source;
  NotificationRepositoryImpl(this._source);

  @override
  Future<Either<Failure, List<NotificationEntity>>> getNotifications() async {
    try {
      final list = await _source.getNotifications();
      return Right(list);
    } catch (e) {
      return Left(ServerFailure(e.toString()));
    }
  }

  @override
  Stream<List<NotificationEntity>> get liveStream => _source.liveStream;
}
