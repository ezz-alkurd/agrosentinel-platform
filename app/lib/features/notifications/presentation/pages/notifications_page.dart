import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';
import 'package:shimmer/shimmer.dart';
import '../../../../core/constants/app_colors.dart';
import '../../../../core/constants/app_dimensions.dart';
import '../../domain/entities/notification_entity.dart';
import '../cubit/notifications_cubit.dart';
import '../cubit/notifications_state.dart';
import '../widgets/notification_card.dart';

class NotificationsPage extends StatefulWidget {
  const NotificationsPage({super.key});

  @override
  State<NotificationsPage> createState() => _NotificationsPageState();
}

class _NotificationsPageState extends State<NotificationsPage> {
  NotificationType? _filter;

  @override
  void initState() {
    super.initState();
    context.read<NotificationsCubit>().load();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.backgroundDeep,
      appBar: AppBar(
        title: const Text('Notifications'),
        actions: [
          BlocBuilder<NotificationsCubit, NotificationsState>(
            builder: (ctx, state) {
              if (state is NotificationsLoaded && state.unreadCount > 0) {
                return TextButton(
                  onPressed: () => ctx.read<NotificationsCubit>().markAllRead(),
                  child: const Text(
                    'Mark all read',
                    style: TextStyle(color: AppColors.neonGreen, fontSize: 14),
                  ),
                );
              }
              return const SizedBox.shrink();
            },
          ),
        ],
      ),
      body: Column(
        children: [
          _FilterChips(
            current: _filter,
            onChanged: (f) => setState(() => _filter = f),
          ),
          Expanded(
            child: BlocBuilder<NotificationsCubit, NotificationsState>(
              builder: (ctx, state) {
                if (state is NotificationsLoading || state is NotificationsInitial) {
                  return _ShimmerList();
                }
                if (state is NotificationsError) {
                  return _EmptyState(
                    icon: Icons.error_outline,
                    message: state.message,
                    color: AppColors.alertFire,
                  );
                }
                if (state is NotificationsLoaded) {
                  final items = _filter == null
                      ? state.notifications
                      : state.notifications
                          .where((n) => n.type == _filter)
                          .toList();

                  if (items.isEmpty) {
                    return const _EmptyState(
                      icon: Icons.notifications_off_outlined,
                      message: 'No notifications yet',
                    );
                  }

                  return ListView.builder(
                    padding: const EdgeInsets.all(AppDimensions.spaceMD),
                    itemCount: items.length,
                    itemBuilder: (_, i) => NotificationCard(
                      notification: items[i],
                      onOpen: () =>
                          ctx.read<NotificationsCubit>().markRead(items[i].id),
                      onViewMap: () {
                        ctx.read<NotificationsCubit>().markRead(items[i].id);
                        context.go('/map');
                      },
                    ),
                  );
                }
                return const SizedBox.shrink();
              },
            ),
          ),
        ],
      ),
    );
  }
}

class _FilterChips extends StatelessWidget {
  final NotificationType? current;
  final ValueChanged<NotificationType?> onChanged;

  const _FilterChips({required this.current, required this.onChanged});

  @override
  Widget build(BuildContext context) {
    final filters = <String, NotificationType?>{
      'All': null,
      'Fire': NotificationType.fire,
      'Disease': NotificationType.disease,
      'Warning': NotificationType.warning,
      'Info': NotificationType.info,
    };

    return SizedBox(
      height: 48,
      child: ListView(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: AppDimensions.spaceMD),
        children: filters.entries.map((e) {
          final selected = current == e.value;
          return Padding(
            padding: const EdgeInsets.only(right: AppDimensions.spaceSM),
            child: FilterChip(
              label: Text(e.key),
              selected: selected,
              onSelected: (_) => onChanged(e.value),
              backgroundColor: AppColors.backgroundCard,
              selectedColor: AppColors.neonGreenFaint,
              labelStyle: TextStyle(
                color: selected ? AppColors.neonGreen : AppColors.textSecondary,
                fontWeight: selected ? FontWeight.w600 : FontWeight.w400,
                fontSize: 14,
              ),
              side: BorderSide(
                color: selected ? AppColors.neonGreen : AppColors.borderDim,
              ),
              checkmarkColor: AppColors.neonGreen,
              showCheckmark: false,
              padding: const EdgeInsets.symmetric(horizontal: 4),
            ),
          );
        }).toList(),
      ),
    );
  }
}

class _ShimmerList extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Shimmer.fromColors(
      baseColor: AppColors.backgroundCard,
      highlightColor: AppColors.backgroundElevated,
      child: ListView.builder(
        padding: const EdgeInsets.all(AppDimensions.spaceMD),
        itemCount: 4,
        itemBuilder: (_, __) => Container(
          height: 90,
          margin: const EdgeInsets.only(bottom: AppDimensions.spaceSM),
          decoration: BoxDecoration(
            color: AppColors.backgroundCard,
            borderRadius: BorderRadius.circular(AppDimensions.radiusLG),
          ),
        ),
      ),
    );
  }
}

class _EmptyState extends StatelessWidget {
  final IconData icon;
  final String message;
  final Color color;

  const _EmptyState({
    required this.icon,
    required this.message,
    this.color = AppColors.textMuted,
  });

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, color: color, size: 48),
          const SizedBox(height: AppDimensions.spaceMD),
          Text(message,
              style: const TextStyle(color: AppColors.textSecondary, fontSize: 14)),
        ],
      ),
    );
  }
}
