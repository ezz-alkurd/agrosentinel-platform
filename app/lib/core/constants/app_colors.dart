import 'package:flutter/material.dart';

class AppColors {
  AppColors._();

  // ─── Premium Emerald Dark (default) ─────────────────────────────────────────
  static const Color backgroundDeep     = Color(0xFF101813);
  static const Color backgroundBase     = Color(0xFF131E18);
  static const Color backgroundCard     = Color(0xFF1B2820);
  static const Color backgroundElevated = Color(0xFF23342A);

  static const Color neonGreen      = Color(0xFF8DC6A0);
  static const Color neonGreenDim   = Color(0xFF4E9270);
  static const Color neonGreenFaint = Color(0x268DC6A0);

  static const Color alertFire         = Color(0xFFF04438);
  static const Color alertFireFaint    = Color(0x26F04438);
  static const Color alertDisease      = Color(0xFFF79009);
  static const Color alertDiseaseFaint = Color(0x26F79009);

  static const Color textPrimary   = Color(0xFFEAF1EC);
  static const Color textSecondary = Color(0xFFB9C9BE);
  static const Color textMuted     = Color(0xFFB9C9BE);
  static const Color textInverse   = Color(0xFF101813);

  static const Color statusOnline  = Color(0xFF8DC6A0);
  static const Color statusWarning = Color(0xFFF79009);
  static const Color statusOffline = Color(0xFFF04438);
  static const Color statusIdle    = Color(0xFFB9C9BE);

  static const Color borderDim  = Color(0xFF304536);
  static const Color borderGlow = Color(0xFF8DC6A0);

  static const LinearGradient neonGreenGradient = LinearGradient(
    colors: [neonGreen, neonGreenDim],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  static const LinearGradient cardGradient = LinearGradient(
    colors: [backgroundCard, backgroundElevated],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );
}

// ─── Per-theme palette — used by ThemePicker & AppTheme ──────────────────────

class AppThemePalette {
  final String id;
  final String label;
  final String emoji;
  final Color scaffold;
  final Color card;
  final Color primary;
  final Color secondary;
  final Color text;
  final Color textSub;
  final Brightness brightness;
  final List<Color> gradientColors;

  const AppThemePalette({
    required this.id,
    required this.label,
    required this.emoji,
    required this.scaffold,
    required this.card,
    required this.primary,
    required this.secondary,
    required this.text,
    required this.textSub,
    required this.brightness,
    required this.gradientColors,
  });

  static const neonDark = AppThemePalette(
    id: 'neonDark',
    label: 'Forest Dark',
    emoji: '',
    scaffold: Color(0xFF101813),
    card: Color(0xFF1B2820),
    primary: Color(0xFF8DC6A0),
    secondary: Color(0xFF4E9270),
    text: Color(0xFFEAF1EC),
    textSub: Color(0xFFB9C9BE),
    brightness: Brightness.dark,
    gradientColors: [Color(0xFF8DC6A0), Color(0xFF4E9270)],
  );

  static const oceanBlue = AppThemePalette(
    id: 'oceanBlue',
    label: 'Ocean Blue',
    emoji: '',
    scaffold: Color(0xFF060E1F),
    card: Color(0xFF0D1E3C),
    primary: Color(0xFF00D4FF),
    secondary: Color(0xFF0099CC),
    text: Color(0xFFD6EAF8),
    textSub: Color(0xFFADC9DE),
    brightness: Brightness.dark,
    gradientColors: [Color(0xFF00D4FF), Color(0xFF0066AA)],
  );

  static const sunsetEmber = AppThemePalette(
    id: 'sunsetEmber',
    label: 'Sunset Ember',
    emoji: '',
    scaffold: Color(0xFF1A0D0A),
    card: Color(0xFF2D1410),
    primary: Color(0xFFFF6B35),
    secondary: Color(0xFFE84A1A),
    text: Color(0xFFFDF0EC),
    textSub: Color(0xFFD8B8AE),
    brightness: Brightness.dark,
    gradientColors: [Color(0xFFFF6B35), Color(0xFFFF3B30)],
  );

  static const forestLight = AppThemePalette(
    id: 'forestLight',
    label: 'Forest Light',
    emoji: '',
    scaffold: Color(0xFFE9F0EC),
    card: Color(0xFFFFFFFF),
    primary: Color(0xFF2D6A4F),
    secondary: Color(0xFF52B788),
    text: Color(0xFF1B3A2D),
    textSub: Color(0xFF40594C),
    brightness: Brightness.light,
    gradientColors: [Color(0xFF52B788), Color(0xFF2D6A4F)],
  );

  static const galaxyPurple = AppThemePalette(
    id: 'galaxyPurple',
    label: 'Galaxy Purple',
    emoji: '',
    scaffold: Color(0xFF0A0614),
    card: Color(0xFF150D2A),
    primary: Color(0xFFA855F7),
    secondary: Color(0xFF7C3AED),
    text: Color(0xFFEDE9FE),
    textSub: Color(0xFFC6B8DF),
    brightness: Brightness.dark,
    gradientColors: [Color(0xFFA855F7), Color(0xFF7C3AED)],
  );

  static const List<AppThemePalette> all = [
    neonDark,
    oceanBlue,
    sunsetEmber,
    forestLight,
    galaxyPurple,
  ];

  static AppThemePalette byId(String id) =>
      all.firstWhere((p) => p.id == id, orElse: () => neonDark);
}
