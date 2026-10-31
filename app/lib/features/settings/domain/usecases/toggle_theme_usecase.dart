import 'package:flutter/material.dart';
import '../repositories/settings_repository.dart';

class ToggleThemeUseCase {
  final SettingsRepository _repository;
  ToggleThemeUseCase(this._repository);

  Future<void> call(ThemeMode mode) => _repository.saveThemeMode(mode);
}
