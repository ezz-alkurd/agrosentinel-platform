import 'dart:async';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../domain/repositories/detections_repository.dart';
import 'detections_state.dart';

class DetectionsCubit extends Cubit<DetectionsState> {
  final DetectionsRepository _repository;
  StreamSubscription? _sub;

  DetectionsCubit(this._repository) : super(const DetectionsInitial());

  void watch() {
    emit(const DetectionsLoading());
    _sub?.cancel();
    _sub = _repository.watchEvents().listen(
      (events) { if (!isClosed) emit(DetectionsLoaded(events)); },
      onError: (Object error) { if (!isClosed) emit(const DetectionsError('Could not sync events. Check your connection and sign-in.')); },
    );
  }

  @override
  Future<void> close() {
    _sub?.cancel();
    return super.close();
  }
}
