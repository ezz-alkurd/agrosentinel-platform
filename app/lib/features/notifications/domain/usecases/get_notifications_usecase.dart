import 'package:dartz/dartz.dart';
import '../../../../core/errors/failures.dart';
import '../entities/notification_entity.dart';
import '../repositories/notification_repository.dart';

class GetNotificationsUseCase {
  final NotificationRepository _repository;
  GetNotificationsUseCase(this._repository);

  Future<Either<Failure, List<NotificationEntity>>> call() =>
      _repository.getNotifications();

  Stream<List<NotificationEntity>> get liveStream => _repository.liveStream;
}
