import 'dart:io';
import 'package:equatable/equatable.dart';
import '../../domain/entities/diagnosis_entity.dart';

abstract class DiagnosticState extends Equatable {
  const DiagnosticState();
  @override
  List<Object?> get props => [];
}

class DiagnosticInitial extends DiagnosticState {
  const DiagnosticInitial();
}

class DiagnosticImageSelected extends DiagnosticState {
  final File image;
  const DiagnosticImageSelected(this.image);
  @override
  List<Object?> get props => [image.path];
}

class DiagnosticAnalyzing extends DiagnosticState {
  final File image;
  const DiagnosticAnalyzing(this.image);
  @override
  List<Object?> get props => [image.path];
}

class DiagnosticResult extends DiagnosticState {
  final File image;
  final DiagnosisEntity diagnosis;
  const DiagnosticResult({required this.image, required this.diagnosis});
  @override
  List<Object?> get props => [image.path, diagnosis];
}

class DiagnosticError extends DiagnosticState {
  final String message;
  final File? image;
  const DiagnosticError(this.message, {this.image});
  @override
  List<Object?> get props => [message, image?.path];
}
