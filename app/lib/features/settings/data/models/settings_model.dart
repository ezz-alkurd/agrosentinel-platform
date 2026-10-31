import 'package:flutter/material.dart';
import '../../domain/entities/settings_entity.dart';

class SettingsModel extends SettingsEntity {
  const SettingsModel({
    super.themeMode,
    super.languageCode,
    super.pushNotificationsEnabled,
    super.appTheme,
  });

  factory SettingsModel.fromPrefs({
    required String themeMode,
    required String languageCode,
    required bool pushNotifications,
    required String appTheme,
  }) =>
      SettingsModel(
        themeMode: ThemeMode.values.firstWhere(
          (e) => e.name == themeMode,
          orElse: () => ThemeMode.dark,
        ),
        languageCode: languageCode,
        pushNotificationsEnabled: pushNotifications,
        appTheme: appTheme,
      );
}
