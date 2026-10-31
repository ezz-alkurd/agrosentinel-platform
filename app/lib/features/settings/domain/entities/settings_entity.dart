import 'package:equatable/equatable.dart';
import 'package:flutter/material.dart';

class SettingsEntity extends Equatable {
  final ThemeMode themeMode;
  final String languageCode;
  final bool pushNotificationsEnabled;
  final String appTheme;

  const SettingsEntity({
    this.themeMode = ThemeMode.dark,
    this.languageCode = 'en',
    this.pushNotificationsEnabled = true,
    this.appTheme = 'neonDark',
  });

  SettingsEntity copyWith({
    ThemeMode? themeMode,
    String? languageCode,
    bool? pushNotificationsEnabled,
    String? appTheme,
  }) =>
      SettingsEntity(
        themeMode: themeMode ?? this.themeMode,
        languageCode: languageCode ?? this.languageCode,
        pushNotificationsEnabled:
            pushNotificationsEnabled ?? this.pushNotificationsEnabled,
        appTheme: appTheme ?? this.appTheme,
      );

  @override
  List<Object?> get props =>
      [themeMode, languageCode, pushNotificationsEnabled, appTheme];
}
