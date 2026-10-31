import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

abstract class SettingsLocalDataSource {
  Future<ThemeMode> getThemeMode();
  Future<String> getLanguageCode();
  Future<bool> getPushNotifications();
  Future<String> getAppTheme();
  Future<void> saveThemeMode(ThemeMode mode);
  Future<void> saveLanguageCode(String code);
  Future<void> savePushNotifications(bool enabled);
  Future<void> saveAppTheme(String paletteId);
}

class SettingsLocalDataSourceImpl implements SettingsLocalDataSource {
  final SharedPreferences _prefs;

  static const _keyTheme    = 'theme_mode';
  static const _keyLang     = 'language_code';
  static const _keyPush     = 'push_notifications';
  static const _keyAppTheme = 'app_theme';

  SettingsLocalDataSourceImpl(this._prefs);

  @override
  Future<ThemeMode> getThemeMode() async {
    final val = _prefs.getString(_keyTheme) ?? 'dark';
    return ThemeMode.values.firstWhere((e) => e.name == val,
        orElse: () => ThemeMode.dark);
  }

  @override
  Future<String> getLanguageCode() async =>
      _prefs.getString(_keyLang) ?? 'en';

  @override
  Future<bool> getPushNotifications() async =>
      _prefs.getBool(_keyPush) ?? true;

  @override
  Future<String> getAppTheme() async {
    // Apply the requested dark appearance once; later choices remain user-controlled.
    if (!(_prefs.getBool('readability_v2') ?? false)) {
      final saved = _prefs.getString(_keyAppTheme);
      if (saved == null || saved == 'forestLight') {
        await _prefs.setString(_keyAppTheme, 'neonDark');
      }
      await _prefs.setBool('readability_v2', true);
    }
    return _prefs.getString(_keyAppTheme) ?? 'neonDark';
  }

  @override
  Future<void> saveThemeMode(ThemeMode mode) async =>
      _prefs.setString(_keyTheme, mode.name);

  @override
  Future<void> saveLanguageCode(String code) async =>
      _prefs.setString(_keyLang, code);

  @override
  Future<void> savePushNotifications(bool enabled) async =>
      _prefs.setBool(_keyPush, enabled);

  @override
  Future<void> saveAppTheme(String paletteId) async =>
      _prefs.setString(_keyAppTheme, paletteId);
}
