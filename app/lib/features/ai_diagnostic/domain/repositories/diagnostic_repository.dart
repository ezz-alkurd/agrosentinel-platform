import 'dart:io';
import 'package:dartz/dartz.dart';
import '../../../../core/errors/failures.dart';
import '../entities/diagnosis_entity.dart';

abstract class DiagnosticRepository {
  Future<Either<Failure, DiagnosisEntity>> analyzeImage(File image);
}
