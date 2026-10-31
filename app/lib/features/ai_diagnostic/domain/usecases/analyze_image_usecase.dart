import 'dart:io';
import 'package:dartz/dartz.dart';
import '../../../../core/errors/failures.dart';
import '../entities/diagnosis_entity.dart';
import '../repositories/diagnostic_repository.dart';

class AnalyzeImageUseCase {
  final DiagnosticRepository _repository;
  AnalyzeImageUseCase(this._repository);

  Future<Either<Failure, DiagnosisEntity>> call(File image) =>
      _repository.analyzeImage(image);
}
