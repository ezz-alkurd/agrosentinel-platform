import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../features/ai_diagnostic/presentation/cubit/diagnostic_cubit.dart';
import 'package:go_router/go_router.dart';
import '../di/injection.dart';
import '../../features/auth/presentation/bloc/auth_bloc.dart';
import '../../features/auth/presentation/bloc/auth_state.dart';
import '../../features/auth/presentation/pages/login_page.dart';
import '../../features/auth/presentation/pages/signup_page.dart';
import '../../features/shell/presentation/pages/main_shell_page.dart';
import '../../features/home/presentation/pages/home_page.dart';
import '../../features/home/presentation/pages/connect_device_page.dart';
import '../../features/map/presentation/pages/map_page.dart';
import '../../features/notifications/presentation/pages/notifications_page.dart';
import '../../features/ai_diagnostic/presentation/pages/ai_diagnostic_page.dart';
import '../../features/settings/presentation/pages/settings_page.dart';
import '../../features/detections/presentation/pages/detections_page.dart';

class AppRouter {
  AppRouter._();

  static final GoRouter router = GoRouter(
    initialLocation: '/startup',
    refreshListenable: _AuthRefresh(sl<AuthBloc>().stream),
    redirect: (context, state) {
      final authState = sl<AuthBloc>().state;
      final isAuthenticated = authState is AuthAuthenticated;
      final isAuthRoute = state.matchedLocation == '/login' ||
          state.matchedLocation == '/signup';

      if (authState is AuthInitial) return '/startup';
      if (state.matchedLocation == '/startup') return isAuthenticated ? '/home' : '/login';
      if (state.matchedLocation == '/offline-analysis') return null;
      if (!isAuthenticated && !isAuthRoute) return '/login';
      if (isAuthenticated && isAuthRoute) return '/home';
      return null;
    },
    routes: [
      GoRoute(path: '/startup', builder: (_, __) => const Scaffold(
        body: Center(child: Column(mainAxisSize: MainAxisSize.min, children: [
          CircularProgressIndicator(), SizedBox(height: 20), Text('Restoring your session...'),
        ])))),
      GoRoute(
        path: '/login',
        builder: (_, __) => const LoginPage(),
      ),
      GoRoute(
        path: '/signup',
        builder: (_, __) => const SignupPage(),
      ),
      GoRoute(path: '/offline-analysis', builder: (_, __) => BlocProvider(
        create: (_) => sl<DiagnosticCubit>(), child: const AiDiagnosticPage(standalone: true))),
      ShellRoute(
        builder: (_, __, child) => MainShellPage(child: child),
        routes: [
          GoRoute(
            path: '/home',
            builder: (_, __) => const HomePage(),
          ),
          GoRoute(
            path: '/map',
            builder: (_, __) => const MapPage(),
          ),
          GoRoute(
            path: '/notifications',
            builder: (_, __) => const NotificationsPage(),
          ),
          GoRoute(
            path: '/ai-diagnostic',
            builder: (_, __) => const AiDiagnosticPage(),
          ),
          GoRoute(
            path: '/settings',
            builder: (_, __) => const SettingsPage(),
          ),
          GoRoute(
            path: '/detections',
            builder: (_, __) => const DetectionsPage(),
          ),
          GoRoute(
            path: '/connect-device',
            builder: (_, __) => const ConnectDevicePage(),
          ),
        ],
      ),
    ],
  );
}

/// Makes GoRouter re-evaluate its redirect whenever AuthBloc emits.
class _AuthRefresh extends ChangeNotifier {
  late final StreamSubscription<AuthState> _sub;

  _AuthRefresh(Stream<AuthState> stream) {
    _sub = stream.listen((_) => notifyListeners());
  }

  @override
  void dispose() {
    _sub.cancel();
    super.dispose();
  }
}
