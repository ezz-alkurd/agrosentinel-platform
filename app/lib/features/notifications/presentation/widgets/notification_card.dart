import 'package:flutter/material.dart';
import '../../../../core/constants/app_colors.dart';
import '../../../../core/constants/app_dimensions.dart';
import '../../../../core/utils/extensions.dart';
import '../../domain/entities/notification_entity.dart';

class NotificationCard extends StatelessWidget {
  final NotificationEntity notification;
  final VoidCallback? onViewMap;
  final VoidCallback? onOpen;

  const NotificationCard({
    super.key,
    required this.notification,
    this.onViewMap,
    this.onOpen,
  });

  @override
  Widget build(BuildContext context) {
    final (color, faint, icon) = _typeStyle(notification.type);

    return AnimatedContainer(
      duration: const Duration(milliseconds: 300),
      margin: const EdgeInsets.only(bottom: AppDimensions.spaceSM),
      decoration: BoxDecoration(
        color: notification.isRead ? AppColors.backgroundCard : faint,
        borderRadius: BorderRadius.circular(AppDimensions.radiusLG),
        border: Border.all(
          color: notification.isRead ? AppColors.borderDim : color.withValues(alpha: 0.4),
        ),
      ),
      child: InkWell(
        onTap: onOpen,
        borderRadius: BorderRadius.circular(AppDimensions.radiusLG),
        child: Padding(
        padding: const EdgeInsets.all(AppDimensions.spaceMD),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _TypeIcon(icon: icon, color: color, faint: faint),
            const SizedBox(width: AppDimensions.spaceMD),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Expanded(
                        child: Text(
                          notification.title,
                          style: TextStyle(
                            color: notification.isRead
                                ? AppColors.textSecondary
                                : AppColors.textPrimary,
                            fontSize: 14,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ),
                      Text(
                        notification.timestamp.timeAgo(),
                        style: const TextStyle(
                            color: AppColors.textMuted, fontSize: 13),
                      ),
                    ],
                  ),
                  const SizedBox(height: 4),
                  Text(
                    notification.body,
                    style: const TextStyle(
                        color: AppColors.textSecondary, fontSize: 15),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                  const SizedBox(height: AppDimensions.spaceSM),
                  GestureDetector(
                    onTap: onViewMap,
                    child: Row(
                      children: [
                        const Icon(Icons.location_on_outlined,
                            color: AppColors.neonGreen, size: 13),
                        const SizedBox(width: 3),
                        Text(
                          notification.locationLabel,
                          style: const TextStyle(
                            color: AppColors.neonGreen,
                            fontSize: 14,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
      ),
    );
  }

  (Color, Color, IconData) _typeStyle(NotificationType type) => switch (type) {
        NotificationType.fire    => (AppColors.alertFire,    AppColors.alertFireFaint,    Icons.local_fire_department_rounded),
        NotificationType.disease => (AppColors.alertDisease, AppColors.alertDiseaseFaint, Icons.eco_rounded),
        NotificationType.warning => (AppColors.alertDisease, AppColors.alertDiseaseFaint, Icons.warning_amber_rounded),
        NotificationType.info    => (AppColors.neonGreen,    AppColors.neonGreenFaint,    Icons.info_outline_rounded),
      };
}

class _TypeIcon extends StatelessWidget {
  final IconData icon;
  final Color color;
  final Color faint;

  const _TypeIcon({required this.icon, required this.color, required this.faint});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(AppDimensions.spaceSM),
      decoration: BoxDecoration(
        color: faint,
        borderRadius: BorderRadius.circular(AppDimensions.radiusSM),
      ),
      child: Icon(icon, color: color, size: 20),
    );
  }
}
