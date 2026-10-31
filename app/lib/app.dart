import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'core/di/injection.dart';
import 'core/l10n/app_l10n.dart';
import 'core/router/app_router.dart';
import 'core/theme/app_theme.dart';
import 'features/auth/presentation/bloc/auth_bloc.dart';
import 'features/settings/presentation/cubit/settings_cubit.dart';
import 'features/settings/presentation/cubit/settings_state.dart';

class AgroDroneApp extends StatelessWidget {
  const AgroDroneApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiBlocProvider(
      providers: [
        BlocProvider.value(value: sl<AuthBloc>()),
        BlocProvider.value(value: sl<SettingsCubit>()),
      ],
      child: BlocBuilder<SettingsCubit, SettingsState>(
        builder: (context, settings) {
          final selectedTheme = AppTheme.themeFor(settings.appTheme);

          // The palette IS the theme — each palette carries its own brightness
          // (e.g. forestLight → Brightness.light, neonDark → Brightness.dark).
          // We always pass the selected palette to `theme` and force
          // ThemeMode.light so Flutter uses `theme` unconditionally,
          // meaning the user's OS dark/light preference doesn't interfere
          // with the palette they chose in Settings.
          return MaterialApp.router(
            title: 'AgroSentinel',
            debugShowCheckedModeBanner: false,
            theme: selectedTheme,
            themeMode: ThemeMode.light,
            routerConfig: AppRouter.router,
            locale: Locale(settings.languageCode),
            supportedLocales: const [Locale('en'), Locale('ar')],
            localizationsDelegates: const [
              AppL10n.delegate,
              GlobalMaterialLocalizations.delegate,
              GlobalWidgetsLocalizations.delegate,
              GlobalCupertinoLocalizations.delegate,
            ],
          );
        },
      ),
    );
  }
}
