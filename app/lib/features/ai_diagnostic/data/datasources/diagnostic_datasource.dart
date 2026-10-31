import 'dart:io';
import '../models/diagnosis_model.dart';
abstract class DiagnosticDataSource {
  Future<DiagnosisModel> analyzeImage(File image);
}
