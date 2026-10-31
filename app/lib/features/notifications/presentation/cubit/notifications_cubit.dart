import 'dart:async';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../data/datasources/notification_read_store.dart';
import '../../domain/entities/notification_entity.dart';
import '../../domain/usecases/get_notifications_usecase.dart';
import 'notifications_state.dart';

class NotificationsCubit extends Cubit<NotificationsState> {
  final GetNotificationsUseCase _useCase;
  final NotificationReadStore _readStore;
  StreamSubscription<List<NotificationEntity>>? _liveSub;
  final List<NotificationEntity> _all = [];
  int _generation = 0;

  NotificationsCubit(this._useCase, this._readStore)
      : super(const NotificationsInitial());

  NotificationEntity _applyRead(NotificationEntity n) =>
      _readStore.isRead(n.id) ? n.copyWith(isRead: true) : n;

  Future<void> load() async {
    final generation = ++_generation;
    await _liveSub?.cancel();
    if (isClosed || generation != _generation) return;
    emit(const NotificationsLoading());
    final result = await _useCase();
    if (isClosed || generation != _generation) return;
    result.fold(
      (f) => emit(NotificationsError(f.message)),
      (list) {
        _all
          ..clear()
          ..addAll(list.map(_applyRead));
        _emitLoaded();
        _subscribeLive();
      },
    );
  }

  void _subscribeLive() {
    _liveSub?.cancel();
    _liveSub = _useCase.liveStream.listen((notifications) {
      if (isClosed) return;
      _all..clear()..addAll(notifications.map(_applyRead));
      _emitLoaded();
    }, onError: (Object error) {
      if (!isClosed) emit(NotificationsError('Could not sync alerts. Check your connection and sign-in.'));
    });
  }

  /// Mark a single notification read (e.g. when the user opens it).
  Future<void> markRead(String id) async {
    await _readStore.markRead(id);
    final i = _all.indexWhere((n) => n.id == id);
    if (i >= 0 && !_all[i].isRead) {
      _all[i] = _all[i].copyWith(isRead: true);
      _emitLoaded();
    }
  }

  Future<void> markAllRead() async {
    await _readStore.markAll(_all.map((n) => n.id));
    for (var i = 0; i < _all.length; i++) {
      _all[i] = _all[i].copyWith(isRead: true);
    }
    _emitLoaded();
  }

  void _emitLoaded() {
    if (isClosed) return;
    final unread = _all.where((n) => !n.isRead).length;
    emit(NotificationsLoaded(
        notifications: List.unmodifiable(_all), unreadCount: unread));
  }

  @override
  Future<void> close() async {
    _generation++;
    final subscription = _liveSub;
    _liveSub = null;
    await subscription?.cancel();
    return super.close();
  }
}
