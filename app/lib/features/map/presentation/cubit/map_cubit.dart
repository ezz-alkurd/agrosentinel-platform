import 'package:flutter_bloc/flutter_bloc.dart';
import '../../domain/usecases/get_map_data_usecase.dart';
import 'map_state.dart';

class MapCubit extends Cubit<MapState> {
  final GetMapDataUseCase _useCase;

  MapCubit(this._useCase) : super(const MapInitial());

  Future<void> loadMapData() async {
    emit(const MapLoading());

    final markersResult = await _useCase.getMarkers();
    final pathResult    = await _useCase.getDronePath();

    markersResult.fold(
      (f) => emit(MapError(f.message)),
      (markers) => pathResult.fold(
        (f) => emit(MapError(f.message)),
        (path) => emit(MapLoaded(markers: markers, path: path)),
      ),
    );
  }
}
