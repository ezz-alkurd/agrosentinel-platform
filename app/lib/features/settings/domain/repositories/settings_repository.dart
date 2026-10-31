import 'package:flutter/material.dart';
import '../entities/settings_entity.dart';

abstract class SettingsRepository {
  Future<SettingsEntity> loadSettings();
  Future<void> saveThemeMode(ThemeMode mode);
  Future<void> saveLanguageCode(String code);
  Future<void> savePushNotifications(bool enabled);
  Future<void> saveAppTheme(String paletteId);
}
