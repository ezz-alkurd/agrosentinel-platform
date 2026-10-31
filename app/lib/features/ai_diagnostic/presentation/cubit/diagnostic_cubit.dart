import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:image_picker/image_picker.dart';
import '../../domain/usecases/analyze_image_usecase.dart';
import 'diagnostic_state.dart';

class DiagnosticCubit extends Cubit<DiagnosticState> {
  final AnalyzeImageUseCase _analyze;
  final ImagePicker _picker;
  int _generation = 0;
  DiagnosticCubit(this._analyze, {ImagePicker? picker})
      : _picker = picker ?? ImagePicker(), super(const DiagnosticInitial());

  Future<void> recoverLostImage() async {
    if (kIsWeb || defaultTargetPlatform != TargetPlatform.android) return;
    final generation = _generation;
    try {
      final response = await _picker.retrieveLostData();
      if (isClosed || generation != _generation || response.isEmpty) return;
      final files = response.files;
      if (files != null && files.isNotEmpty) {
        emit(DiagnosticImageSelected(File(files.first.path)));
      } else {
        emit(const DiagnosticError('The photo could not be recovered. Please select it again.'));
      }
    } catch (_) {
      // No pending photo must never prevent opening the analysis page.
    }
  }

  Future<void> pickImage(ImageSource source) async {
    if (state is DiagnosticAnalyzing) return;
    final generation = ++_generation;
    try {
      final picked = await _picker.pickImage(source: source, imageQuality: 85, maxWidth: 1280, maxHeight: 1280, requestFullMetadata: false);
      if (picked == null || isClosed || generation != _generation) return;
      emit(DiagnosticImageSelected(File(picked.path)));
    } catch (_) {
      if (!isClosed && generation == _generation) {
        emit(const DiagnosticError('Could not open the camera or gallery. Check photo permissions and try again.'));
      }
    }
  }
  Future<void> analyzeCurrentImage() async {
    final selected = state;
    final File? image = selected is DiagnosticImageSelected ? selected.image
      : selected is DiagnosticError ? selected.image : null;
    if (image == null) return;
    final generation = ++_generation;
    emit(DiagnosticAnalyzing(image));
    final result = await _analyze(image);
    if (isClosed || generation != _generation) return;
    result.fold((failure) => emit(DiagnosticError(failure.message, image: image)),
      (diagnosis) => emit(DiagnosticResult(image: image, diagnosis: diagnosis)));
  }
  void reset() { _generation++; emit(const DiagnosticInitial()); }
}
