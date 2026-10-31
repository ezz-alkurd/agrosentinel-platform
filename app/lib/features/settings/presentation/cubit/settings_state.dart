import 'package:equatable/equatable.dart';
import 'package:flutter/material.dart';

class SettingsState extends Equatable {
  final ThemeMode themeMode;
  final String languageCode;
  final bool pushNotificationsEnabled;
  final String appTheme;

  const SettingsState({
    this.themeMode = ThemeMode.dark,
    this.languageCode = 'en',
    this.pushNotificationsEnabled = true,
    this.appTheme = 'neonDark',
  });

  SettingsState copyWith({
    ThemeMode? themeMode,
    String? languageCode,
    bool? pushNotificationsEnabled,
    String? appTheme,
  }) =>
      SettingsState(
        themeMode: themeMode ?? this.themeMode,
        languageCode: languageCode ?? this.languageCode,
        pushNotificationsEnabled:
            pushNotificationsEnabled ?? this.pushNotificationsEnabled,
        appTheme: appTheme ?? this.appTheme,
      );

  bool get isDark => themeMode == ThemeMode.dark;

  @override
  List<Object?> get props =>
      [themeMode, languageCode, pushNotificationsEnabled, appTheme];
}
