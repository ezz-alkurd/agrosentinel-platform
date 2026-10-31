import 'dart:async';
import 'package:dartz/dartz.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:agri_drone_ai/core/errors/failures.dart';
import 'package:agri_drone_ai/features/notifications/data/datasources/notification_read_store.dart';
import 'package:agri_drone_ai/features/notifications/domain/entities/notification_entity.dart';
import 'package:agri_drone_ai/features/notifications/domain/repositories/notification_repository.dart';
import 'package:agri_drone_ai/features/notifications/domain/usecases/get_notifications_usecase.dart';
import 'package:agri_drone_ai/features/notifications/presentation/cubit/notifications_cubit.dart';
import 'package:agri_drone_ai/features/notifications/presentation/cubit/notifications_state.dart';

NotificationEntity event(String id) => NotificationEntity(id: id, title: 'Fire', body: 'Confirmed camera event',
  type: NotificationType.fire, latitude: 0, longitude: 0, locationLabel: 'Unavailable', timestamp: DateTime.utc(2026));
class TestRepository implements NotificationRepository {
  // A live event feed can close even when initial loading was cancelled before listening.
  final updates = StreamController<List<NotificationEntity>>.broadcast();
  final initial = Completer<Either<Failure, List<NotificationEntity>>>();
  @override
  Future<Either<Failure, List<NotificationEntity>>> getNotifications() => initial.future;
  @override
  Stream<List<NotificationEntity>> get liveStream => updates.stream;
}
void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  test('full snapshots add gap events, remove deleted events, and preserve local read state', () async {
    SharedPreferences.setMockInitialValues({});
    final repository = TestRepository();
    final cubit = NotificationsCubit(GetNotificationsUseCase(repository), NotificationReadStore(await SharedPreferences.getInstance()));
    repository.initial.complete(Right([event('old')]));
    await cubit.load();
    await cubit.markRead('old');
    var next = cubit.stream.firstWhere((state) => state is NotificationsLoaded && state.notifications.length == 2);
    repository.updates.add([event('new'), event('old')]);
    final snapshot = await next as NotificationsLoaded;
    expect(snapshot.unreadCount, 1);
    expect(snapshot.notifications.last.isRead, isTrue);
    next = cubit.stream.firstWhere((state) => state is NotificationsLoaded && state.notifications.isEmpty);
    repository.updates.add([]);
    await next;
    expect((cubit.state as NotificationsLoaded).unreadCount, 0);
    final error = cubit.stream.firstWhere((state) => state is NotificationsError);
    repository.updates.addError(StateError('Permission denied'));
    await error;
    await cubit.close(); await repository.updates.close();
  });
  test('closing during initial fetch cannot emit into a closed cubit', () async {
    SharedPreferences.setMockInitialValues({});
    final repository = TestRepository();
    final cubit = NotificationsCubit(GetNotificationsUseCase(repository), NotificationReadStore(await SharedPreferences.getInstance()));
    final loading = cubit.load();
    await Future<void>.delayed(Duration.zero);
    await cubit.close();
    repository.initial.complete(Right([event('old')]));
    await loading;
    await repository.updates.close();
  });
}
