import 'package:flutter/material.dart';

/// Custom in-app localisation delegate — no code-generation required.
/// Supports English and Arabic with full RTL switching via MaterialApp locale.
class AppL10n {
  final Locale locale;
  AppL10n(this.locale);

  static AppL10n of(BuildContext context) =>
      Localizations.of<AppL10n>(context, AppL10n) ?? AppL10n(const Locale('en'));

  static const LocalizationsDelegate<AppL10n> delegate = _AppL10nDelegate();

  bool get isAr => locale.languageCode == 'ar';

  // Navigation
  String get appName       => isAr ? 'زراعة ذكية' : 'AgroDrone AI';
  String get dashboard     => isAr ? 'لوحة التحكم' : 'Dashboard';
  String get map           => isAr ? 'الخريطة' : 'Map';
  String get notifications => isAr ? 'الإشعارات' : 'Notifications';
  String get aiHub         => isAr ? 'الذكاء الاصطناعي' : 'AI Hub';
  String get settings      => isAr ? 'الإعدادات' : 'Settings';

  // Auth
  String get login          => isAr ? 'تسجيل الدخول' : 'Login';
  String get signup         => isAr ? 'إنشاء حساب' : 'Sign Up';
  String get email          => isAr ? 'البريد الإلكتروني' : 'Email';
  String get password       => isAr ? 'كلمة المرور' : 'Password';
  String get fullName       => isAr ? 'الاسم الكامل' : 'Full Name';
  String get welcomeBack    => isAr ? 'مرحباً بعودتك' : 'Welcome back';
  String get logout         => isAr ? 'تسجيل الخروج' : 'Logout';

  // Home
  String get fieldOverview  => isAr ? 'نظرة عامة على الحقل' : 'Field Overview';
  String get liveTracking   => isAr ? 'تتبع مباشر' : 'Live Tracking';
  String get plantDiagnosis => isAr ? 'تشخيص النبات' : 'Plant Diagnosis';
  String get alerts         => isAr ? 'التنبيهات' : 'Alerts';
  String get batteryLevel   => isAr ? 'مستوى البطارية' : 'Battery';
  String get signalStrength => isAr ? 'قوة الإشارة' : 'Signal';
  String get altitude       => isAr ? 'الارتفاع' : 'Altitude';
  String get speed          => isAr ? 'السرعة' : 'Speed';
  String get totalScans     => isAr ? 'إجمالي الفحوصات' : 'Total Scans';
  String get alertsToday    => isAr ? 'تنبيهات اليوم' : 'Alerts Today';

  // Drone
  String get droneConnected    => isAr ? 'الطائرة متصلة' : 'Drone Online';
  String get droneDisconnected => isAr ? 'الطائرة غير متصلة' : 'Drone Offline';

  // Notifications
  String get fireDetected    => isAr ? 'حريق مكتشف' : 'Fire Detected';
  String get diseaseDetected => isAr ? 'مرض نباتي' : 'Disease Detected';
  String get noNotifications => isAr ? 'لا توجد إشعارات' : 'No notifications yet';
  String get viewOnMap       => isAr ? 'عرض على الخريطة' : 'View on Map';

  // AI Hub
  String get analyzing      => isAr ? 'جاري التحليل...' : 'Analyzing...';
  String get uploadImage    => isAr ? 'رفع صورة' : 'Upload Image';
  String get takePhoto      => isAr ? 'التقاط صورة' : 'Take Photo';
  String get analysisResult => isAr ? 'نتيجة التحليل' : 'Analysis Result';
  String get confidence     => isAr ? 'الثقة' : 'Confidence';
  String get treatment      => isAr ? 'العلاج الموصى به' : 'Recommended Treatment';
  String get healthy        => isAr ? 'صحي' : 'Healthy';
  String get tapToAnalyze   => isAr ? 'اضغط لبدء التحليل' : 'Tap to start analysis';

  // Settings
  String get darkMode        => isAr ? 'الوضع الداكن' : 'Dark Mode';
  String get language        => isAr ? 'اللغة' : 'Language';
  String get arabic          => isAr ? 'العربية' : 'Arabic';
  String get english         => isAr ? 'الإنجليزية' : 'English';
  String get pushNotifications => isAr ? 'الإشعارات الفورية' : 'Push Notifications';
  String get appearance      => isAr ? 'المظهر' : 'Appearance';
  String get account         => isAr ? 'الحساب' : 'Account';
  String get about           => isAr ? 'حول التطبيق' : 'About';
  String get version         => isAr ? 'الإصدار' : 'Version';
}

class _AppL10nDelegate extends LocalizationsDelegate<AppL10n> {
  const _AppL10nDelegate();

  @override
  bool isSupported(Locale locale) => ['en', 'ar'].contains(locale.languageCode);

  @override
  Future<AppL10n> load(Locale locale) async => AppL10n(locale);

  @override
  bool shouldReload(covariant LocalizationsDelegate<AppL10n> old) => false;
}
