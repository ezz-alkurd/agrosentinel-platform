import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../domain/usecases/toggle_language_usecase.dart';
import '../../domain/usecases/toggle_theme_usecase.dart';
import '../../domain/repositories/settings_repository.dart';
import 'settings_state.dart';

class SettingsCubit extends Cubit<SettingsState> {
  final SettingsRepository _repository;
  final ToggleThemeUseCase _toggleTheme;
  final ToggleLanguageUseCase _toggleLanguage;

  SettingsCubit({
    required SettingsRepository repository,
    required ToggleThemeUseCase toggleThemeUseCase,
    required ToggleLanguageUseCase toggleLanguageUseCase,
  })  : _repository = repository,
        _toggleTheme = toggleThemeUseCase,
        _toggleLanguage = toggleLanguageUseCase,
        super(const SettingsState());

  Future<void> loadSettings() async {
    final entity = await _repository.loadSettings();
    emit(state.copyWith(
      themeMode: entity.themeMode,
      languageCode: entity.languageCode,
      pushNotificationsEnabled: entity.pushNotificationsEnabled,
      appTheme: entity.appTheme,
    ));
  }

  Future<void> setTheme(ThemeMode mode) async {
    await _toggleTheme(mode);
    emit(state.copyWith(themeMode: mode));
  }

  Future<void> setLanguage(String code) async {
    await _toggleLanguage(code);
    emit(state.copyWith(languageCode: code));
  }

  Future<void> setPushNotifications(bool enabled) async {
    await _repository.savePushNotifications(enabled);
    emit(state.copyWith(pushNotificationsEnabled: enabled));
  }

  /// Switch to one of the 5 named color themes.
  Future<void> setAppTheme(String paletteId) async {
    await _repository.saveAppTheme(paletteId);
    emit(state.copyWith(appTheme: paletteId));
  }
}
