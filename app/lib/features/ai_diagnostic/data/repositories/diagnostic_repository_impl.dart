import 'dart:io';
import 'package:dartz/dartz.dart';
import '../../../../core/errors/failures.dart';
import '../../domain/entities/diagnosis_entity.dart';
import '../../domain/repositories/diagnostic_repository.dart';
import '../datasources/diagnostic_datasource.dart';

class DiagnosticRepositoryImpl implements DiagnosticRepository {
  final DiagnosticDataSource _source;
  DiagnosticRepositoryImpl(this._source);

  @override
  Future<Either<Failure, DiagnosisEntity>> analyzeImage(File image) async {
    try {
      final result = await _source.analyzeImage(image);
      return Right(result);
    } catch (e) {
      return Left(ServerFailure(e.toString()));
    }
  }
}
