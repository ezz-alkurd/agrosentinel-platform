import 'package:flutter/material.dart';
import '../../../../core/constants/app_colors.dart';
import '../../../../core/constants/app_dimensions.dart';
import '../../domain/entities/drone_status_entity.dart';

class DroneStatusCard extends StatelessWidget {
  final DroneStatusEntity status;

  const DroneStatusCard({super.key, required this.status});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(AppDimensions.spaceMD),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [Color(0xFF1C2333), Color(0xFF21262D)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(AppDimensions.radiusLG),
        border: Border.all(
          color: status.isOnline ? AppColors.neonGreen.withValues(alpha: 0.3) : AppColors.borderDim,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              _PulsingDot(online: status.isOnline),
              const SizedBox(width: AppDimensions.spaceSM),
              Text(
                status.isOnline ? 'Drone Online' : 'Drone Offline',
                style: TextStyle(
                  color: status.isOnline ? AppColors.neonGreen : AppColors.alertFire,
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const Spacer(),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: AppColors.neonGreenFaint,
                  borderRadius: BorderRadius.circular(AppDimensions.radiusFull),
                ),
                child: Text(
                  '${status.fieldCoveragePercent}% covered',
                  style: const TextStyle(
                    color: AppColors.neonGreen,
                    fontSize: 13,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: AppDimensions.spaceMD),
          Row(
            children: [
              Expanded(child: _MetricTile(icon: Icons.battery_charging_full_rounded, label: 'Battery', value: '${status.batteryPercent}%', color: _batteryColor(status.batteryPercent))),
              Expanded(child: _MetricTile(icon: Icons.signal_cellular_alt_rounded, label: 'Signal', value: '${status.signalPercent}%', color: AppColors.neonGreen)),
              Expanded(child: _MetricTile(icon: Icons.height_rounded, label: 'Altitude', value: '${status.altitudeMeters.toStringAsFixed(0)}m')),
              Expanded(child: _MetricTile(icon: Icons.speed_rounded, label: 'Speed', value: '${status.speedKmh.toStringAsFixed(1)}km/h')),
            ],
          ),
          const SizedBox(height: AppDimensions.spaceMD),
          Row(
            children: [
              const Icon(Icons.wb_sunny_outlined, color: AppColors.textMuted, size: 14),
              const SizedBox(width: AppDimensions.spaceSM),
              Text(
                '${status.weatherCondition}  •  ${status.temperatureCelsius.toStringAsFixed(1)}°C',
                style: const TextStyle(color: AppColors.textSecondary, fontSize: 15),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Color _batteryColor(int pct) {
    if (pct > 50) return AppColors.neonGreen;
    if (pct > 20) return AppColors.alertDisease;
    return AppColors.alertFire;
  }
}

class _MetricTile extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;
  final Color color;

  const _MetricTile({
    required this.icon,
    required this.label,
    required this.value,
    this.color = AppColors.textPrimary,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Icon(icon, color: color, size: 20),
        const SizedBox(height: 4),
        Text(value,
            style: TextStyle(color: color, fontSize: 15, fontWeight: FontWeight.w700)),
        Text(label,
            style: const TextStyle(color: AppColors.textMuted, fontSize: 12)),
      ],
    );
  }
}

class _PulsingDot extends StatefulWidget {
  final bool online;
  const _PulsingDot({required this.online});

  @override
  State<_PulsingDot> createState() => _PulsingDotState();
}

class _PulsingDotState extends State<_PulsingDot>
    with SingleTickerProviderStateMixin {
  late AnimationController _ctrl;
  late Animation<double> _anim;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 1),
    )..repeat(reverse: true);
    _anim = Tween(begin: 0.4, end: 1.0).animate(_ctrl);
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final color = widget.online ? AppColors.neonGreen : AppColors.alertFire;
    return FadeTransition(
      opacity: _anim,
      child: Container(
        width: 8,
        height: 8,
        decoration: BoxDecoration(color: color, shape: BoxShape.circle),
      ),
    );
  }
}
