import 'package:flutter_bloc/flutter_bloc.dart';
import '../../domain/usecases/get_drone_status_usecase.dart';
import 'home_state.dart';

class HomeCubit extends Cubit<HomeState> {
  final GetDroneStatusUseCase _getStatus;

  HomeCubit(this._getStatus) : super(const HomeInitial());

  Future<void> loadStatus() async {
    emit(const HomeLoading());
    final result = await _getStatus();
    result.fold(
      (f) => emit(HomeError(f.message)),
      (s) => emit(HomeLoaded(s)),
    );
  }

  Future<void> refresh() => loadStatus();
}
