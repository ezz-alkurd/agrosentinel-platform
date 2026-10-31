import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/constants/app_colors.dart';
import '../../../../core/di/injection.dart';
import '../../../ai_diagnostic/presentation/cubit/diagnostic_cubit.dart';
import '../../../detections/presentation/cubit/detections_cubit.dart';
import '../../../home/presentation/cubit/home_cubit.dart';
import '../../../map/presentation/cubit/map_cubit.dart';
import '../../../notifications/presentation/cubit/notifications_cubit.dart';
import '../../../notifications/presentation/cubit/notifications_state.dart';

class MainShellPage extends StatelessWidget {
  final Widget child;

  const MainShellPage({super.key, required this.child});

  @override
  Widget build(BuildContext context) {
    return MultiBlocProvider(
      providers: [
        BlocProvider(create: (_) => sl<HomeCubit>()),
        BlocProvider(create: (_) => sl<NotificationsCubit>()),
        BlocProvider(create: (_) => sl<MapCubit>()),
        BlocProvider(create: (_) => sl<DiagnosticCubit>()),
        BlocProvider(create: (_) => sl<DetectionsCubit>()),
      ],
      child: Scaffold(
        body: child,
        bottomNavigationBar: _BottomNav(),
      ),
    );
  }
}

class _BottomNav extends StatelessWidget {
  static const _tabs = [
    ('/home',          Icons.home_rounded,                 'Home'),
    ('/detections',    Icons.radar_outlined,               'Events'),
    ('/ai-diagnostic', Icons.eco_outlined,                 'Leaf scan'),
    ('/notifications', Icons.notifications_outlined,       'Alerts'),
    ('/settings',      Icons.settings_outlined,            'Settings'),
  ];

  int _indexFor(String location) {
    for (var i = 0; i < _tabs.length; i++) {
      if (location.startsWith(_tabs[i].$1)) return i;
    }
    return 0;
  }

  @override
  Widget build(BuildContext context) {
    final location = GoRouterState.of(context).matchedLocation;
    final currentIndex = _indexFor(location);

    return Container(
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surface,
        border: Border(top: BorderSide(color: Theme.of(context).dividerColor, width: 0.5)),
      ),
      child: BlocBuilder<NotificationsCubit, NotificationsState>(
        builder: (ctx, notifState) {
          final unread = notifState is NotificationsLoaded ? notifState.unreadCount : 0;

          return NavigationBar(
            selectedIndex: currentIndex,
            backgroundColor: Colors.transparent,
            surfaceTintColor: Colors.transparent,
            indicatorColor: Theme.of(context).colorScheme.primary.withValues(alpha: .12),
            height: 76,
            labelBehavior: NavigationDestinationLabelBehavior.alwaysShow,
            onDestinationSelected: (i) => context.go(_tabs[i].$1),
            destinations: _tabs.asMap().entries.map((e) {
              final isNotif = e.value.$1 == '/notifications';
              return NavigationDestination(
                icon: Badge(
                  isLabelVisible: isNotif && unread > 0,
                  label: Text(unread > 9 ? '9+' : unread.toString(),
                      style: const TextStyle(fontSize: 9)),
                  backgroundColor: AppColors.alertFire,
                  child: Icon(e.value.$2),
                ),
                label: e.value.$3,
              );
            }).toList(),
          );
        },
      ),
    );
  }
}
