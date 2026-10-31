import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../constants/app_colors.dart';
import '../constants/app_dimensions.dart';

class AppTheme {
  AppTheme._();

  static ThemeData themeFor(String paletteId) =>
      _buildTheme(AppThemePalette.byId(paletteId));

  static ThemeData get darkTheme  => _buildTheme(AppThemePalette.neonDark);
  static ThemeData get lightTheme => _buildTheme(AppThemePalette.forestLight);

  static ThemeData _buildTheme(AppThemePalette p) {
    final isDark = p.brightness == Brightness.dark;
    final onPrimary = isDark ? Colors.black : Colors.white;

    return ThemeData(
      useMaterial3: true,
      brightness: p.brightness,
      fontFamily: 'Roboto',
      colorScheme: ColorScheme(
        brightness: p.brightness,
        primary: p.primary,
        onPrimary: onPrimary,
        secondary: p.secondary,
        onSecondary: onPrimary,
        surface: p.card,
        onSurface: p.text,
        error: AppColors.alertFire,
        onError: Colors.white,
      ),
      scaffoldBackgroundColor: p.scaffold,
      appBarTheme: AppBarTheme(
        backgroundColor: p.scaffold,
        elevation: 0,
        scrolledUnderElevation: 0,
        centerTitle: false,
        titleTextStyle: TextStyle(
          color: p.text,
          fontSize: 20,
          fontWeight: FontWeight.w700,
        ),
        iconTheme: IconThemeData(color: p.text),
        systemOverlayStyle: SystemUiOverlayStyle(
          statusBarColor: Colors.transparent,
          statusBarIconBrightness: isDark ? Brightness.light : Brightness.dark,
        ),
      ),
      cardTheme: CardThemeData(
        color: p.card,
        elevation: AppDimensions.cardElevation,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppDimensions.radiusLG),
          side: BorderSide(color: p.primary.withValues(alpha: 0.12)),
        ),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: p.primary,
          foregroundColor: onPrimary,
          minimumSize: const Size(double.infinity, 52),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(AppDimensions.radiusMD),
          ),
          textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700),
          elevation: 0,
        ),
      ),
      filledButtonTheme: FilledButtonThemeData(style: FilledButton.styleFrom(
        backgroundColor: p.primary, foregroundColor: onPrimary,
        minimumSize: const Size(double.infinity, 54),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        textStyle: const TextStyle(fontSize: 15, fontWeight: FontWeight.w600))),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: p.primary,
          minimumSize: const Size(double.infinity, 52),
          side: BorderSide(color: p.primary),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(AppDimensions.radiusMD),
          ),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: p.card,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(AppDimensions.radiusMD),
          borderSide: BorderSide(color: p.primary.withValues(alpha: 0.15)),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(AppDimensions.radiusMD),
          borderSide: BorderSide(color: p.primary.withValues(alpha: 0.15)),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(AppDimensions.radiusMD),
          borderSide: BorderSide(color: p.primary, width: 1.5),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(AppDimensions.radiusMD),
          borderSide: const BorderSide(color: AppColors.alertFire),
        ),
        focusedErrorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(AppDimensions.radiusMD),
          borderSide: const BorderSide(color: AppColors.alertFire, width: 1.5),
        ),
        labelStyle: TextStyle(color: p.textSub),
        hintStyle: TextStyle(color: p.textSub.withValues(alpha: 0.9)),
        errorStyle: const TextStyle(color: AppColors.alertFire),
      ),
      textTheme: TextTheme(
        displayLarge:   TextStyle(color: p.text, fontWeight: FontWeight.w700),
        headlineLarge:  TextStyle(color: p.text, fontWeight: FontWeight.w700, fontSize: 28),
        headlineMedium: TextStyle(color: p.text, fontWeight: FontWeight.w600, fontSize: 22),
        headlineSmall:  TextStyle(color: p.text, fontWeight: FontWeight.w600, fontSize: 18),
        titleLarge:     TextStyle(color: p.text, fontWeight: FontWeight.w600, fontSize: 16),
        titleMedium:    TextStyle(color: p.text, fontWeight: FontWeight.w600, fontSize: 16),
        bodyLarge:      TextStyle(color: p.text, fontSize: 17, height: 1.5),
        bodyMedium:     TextStyle(color: p.text, fontSize: 16, height: 1.5),
        bodySmall:      TextStyle(color: p.textSub, fontSize: 14, height: 1.5),
        labelLarge:     TextStyle(color: p.text, fontWeight: FontWeight.w600, fontSize: 14),
      ),
      dividerTheme: DividerThemeData(
        color: p.primary.withValues(alpha: 0.1),
        thickness: 1,
      ),
      switchTheme: SwitchThemeData(
        thumbColor: WidgetStateProperty.resolveWith(
          (s) => s.contains(WidgetState.selected) ? p.primary : p.textSub,
        ),
        trackColor: WidgetStateProperty.resolveWith(
          (s) => s.contains(WidgetState.selected)
              ? p.primary.withValues(alpha: 0.3)
              : p.primary.withValues(alpha: 0.08),
        ),
      ),
      navigationBarTheme: NavigationBarThemeData(
        backgroundColor: p.card,
        indicatorColor: p.primary.withValues(alpha: 0.15),
        labelTextStyle: WidgetStateProperty.resolveWith(
          (s) => TextStyle(
            color: s.contains(WidgetState.selected) ? p.primary : p.textSub,
            fontSize: 12,
            fontWeight: FontWeight.w600,
          ),
        ),
        iconTheme: WidgetStateProperty.resolveWith(
          (s) => IconThemeData(
            color: s.contains(WidgetState.selected) ? p.primary : p.textSub,
            size: 22,
          ),
        ),
      ),
    );
  }
}
