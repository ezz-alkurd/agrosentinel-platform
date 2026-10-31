import 'package:flutter/material.dart';
import '../../domain/entities/settings_entity.dart';
import '../../domain/repositories/settings_repository.dart';
import '../datasources/settings_local_datasource.dart';

class SettingsRepositoryImpl implements SettingsRepository {
  final SettingsLocalDataSource _local;
  SettingsRepositoryImpl(this._local);

  @override
  Future<SettingsEntity> loadSettings() async => SettingsEntity(
        themeMode: await _local.getThemeMode(),
        languageCode: await _local.getLanguageCode(),
        pushNotificationsEnabled: await _local.getPushNotifications(),
        appTheme: await _local.getAppTheme(),
      );

  @override
  Future<void> saveThemeMode(ThemeMode mode) => _local.saveThemeMode(mode);

  @override
  Future<void> saveLanguageCode(String code) => _local.saveLanguageCode(code);

  @override
  Future<void> savePushNotifications(bool enabled) =>
      _local.savePushNotifications(enabled);

  @override
  Future<void> saveAppTheme(String paletteId) =>
      _local.saveAppTheme(paletteId);
}
