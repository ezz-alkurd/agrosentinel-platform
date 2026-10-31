import 'dart:async';

import '../../../../core/network/field_api_client.dart';
import '../../../../core/di/injection.dart';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/constants/app_dimensions.dart';

/// Home status card.
///
/// Watches the `devices` collection. If ANY device has a fresh heartbeat
/// (the PC detector, or later a drone), shows a live "Device connected" state
/// with its type, location and uptime. Otherwise invites the user to connect.
class DeviceConnectionCard extends StatefulWidget {
  const DeviceConnectionCard({super.key});

  @override
  State<DeviceConnectionCard> createState() => _DeviceConnectionCardState();
}

class _DeviceConnectionCardState extends State<DeviceConnectionCard> {
  static const _staleAfter = Duration(seconds: 30);

  StreamSubscription<List<Map<String, dynamic>>>? _sub;
  Timer? _ticker;
  List<Map<String, dynamic>> _devices = [];
  bool _syncFailed = false;
  bool _waiting = true;

  @override
  void initState() {
    super.initState();
    _sub = sl<FieldApiClient>().watchDevices().listen((rows) {
      if (!mounted) return;
      setState(() { _waiting = false; _syncFailed = false; _devices = rows; });
    }, onError: (Object error) {
      if (mounted) setState(() { _syncFailed = true; _waiting = false; _devices = []; });
    });
    _ticker = Timer.periodic(const Duration(seconds: 3), (_) {
      if (mounted) setState(() {});
    });
  }

  @override
  void dispose() {
    _sub?.cancel();
    _ticker?.cancel();
    super.dispose();
  }

  bool _isLive(Map<String, dynamic> d) {
    if (d['online'] != true) return false;
    final ls = DateTime.tryParse(d['last_seen'] as String? ?? '');
    if (ls == null) return false;
    final age = DateTime.now().toUtc().difference(ls.toUtc());
    return !age.isNegative && age < _staleAfter;
  }

  Map<String, dynamic>? get _liveDevice {
    final live = _devices.where(_isLive).toList()
      ..sort((a, b) => (b['last_seen'] as String? ?? '')
          .compareTo(a['last_seen'] as String? ?? ''));
    return live.isEmpty ? null : live.first;
  }

  @override
  Widget build(BuildContext context) {
    if (_waiting || _syncFailed) return Padding(padding: const EdgeInsets.all(20), child: Text(_waiting ? 'Checking camera connection...' : 'Camera status unavailable. Check your connection and sign-in.'));
    final dev = _liveDevice;
    return dev != null ? _connected(context, dev) : _disconnected(context);
  }

  // ── Connected ──────────────────────────────────────────────────────────────
  Widget _connected(BuildContext context, Map<String, dynamic> d) {
    final cs = Theme.of(context).colorScheme;
    final name = (d['name'] ?? d['type'] ?? 'Device') as String;
    final lat = (d['gps_lat'] as num?)?.toDouble() ?? 0.0;
    final lng = (d['gps_lng'] as num?)?.toDouble() ?? 0.0;
    final loc = (lat == 0 && lng == 0)
        ? 'Location unavailable'
        : '${lat.toStringAsFixed(4)}, ${lng.toStringAsFixed(4)}';
    final models = (d['models'] as List?)?.join(' · ') ?? '';
    final started = DateTime.tryParse(d['started_at'] as String? ?? '');
    final uptime = started == null ? null : _fmtUptime(started);
    final liveCount = _devices.where(_isLive).length;

    return GestureDetector(
      onTap: () => context.go('/connect-device'),
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.all(AppDimensions.spaceLG),
        decoration: BoxDecoration(
          color: Theme.of(context).cardColor,
          borderRadius: BorderRadius.circular(AppDimensions.radiusLG),
          border: Border.all(color: cs.primary.withValues(alpha: 0.5)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: cs.primary.withValues(alpha: 0.14),
                    borderRadius: BorderRadius.circular(AppDimensions.radiusMD),
                  ),
                  child: Icon(Icons.videocam_rounded, color: cs.primary, size: 26),
                ),
                const SizedBox(width: AppDimensions.spaceMD),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          _Dot(color: cs.primary),
                          const SizedBox(width: 6),
                          Text(
                            liveCount > 1 ? '$liveCount devices connected' : 'Device connected',
                            style: TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.w700,
                              color: cs.primary,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 2),
                      Text(name,
                          style: const TextStyle(
                              fontSize: 14, fontWeight: FontWeight.w600)),
                    ],
                  ),
                ),
                Icon(Icons.chevron_right_rounded,
                    color: cs.onSurface.withValues(alpha: 0.4)),
              ],
            ),
            const SizedBox(height: AppDimensions.spaceMD),
            _row(context, Icons.location_on_outlined, loc),
            if (uptime != null) ...[
              const SizedBox(height: 6),
              _row(context, Icons.timer_outlined, 'Online for $uptime'),
            ],
            if (models.isNotEmpty) ...[
              const SizedBox(height: 6),
              _row(context, Icons.memory_rounded, 'Detecting: $models'),
            ],
          ],
        ),
      ),
    );
  }

  Widget _row(BuildContext context, IconData icon, String text) {
    final cs = Theme.of(context).colorScheme;
    return Row(
      children: [
        Icon(icon, size: 15, color: cs.onSurface.withValues(alpha: 0.55)),
        const SizedBox(width: 8),
        Expanded(
          child: Text(text,
              style: TextStyle(
                  fontSize: 12.5,
                  color: cs.onSurface.withValues(alpha: 0.75))),
        ),
      ],
    );
  }

  String _fmtUptime(DateTime start) {
    final d = DateTime.now().toUtc().difference(start.toUtc());
    if (d.inHours > 0) return '${d.inHours}h ${d.inMinutes % 60}m';
    if (d.inMinutes > 0) return '${d.inMinutes}m';
    return '${d.inSeconds}s';
  }

  // ── Disconnected ────────────────────────────────────────────────────────────
  Widget _disconnected(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final total = _devices.length;

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(AppDimensions.spaceLG),
      decoration: BoxDecoration(
        color: Theme.of(context).cardColor,
        borderRadius: BorderRadius.circular(AppDimensions.radiusLG),
        border: Border.all(color: cs.outline.withValues(alpha: 0.25)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: cs.primary.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(AppDimensions.radiusMD),
                ),
                child: Icon(Icons.sensors_off_rounded, color: cs.primary, size: 26),
              ),
              const SizedBox(width: AppDimensions.spaceMD),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('No camera connected',
                        style: TextStyle(
                            fontSize: 16, fontWeight: FontWeight.w700)),
                    const SizedBox(height: 4),
                    Text(
                      total > 0
                          ? '$total device${total == 1 ? '' : 's'} added · none online right now.'
                          : 'Connect a drone or camera to see live detections.',
                      style: TextStyle(
                        fontSize: 15,
                        color: cs.onSurface.withValues(alpha: 0.6),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: AppDimensions.spaceMD),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton.icon(
              onPressed: () => context.go('/connect-device'),
              icon: const Icon(Icons.add_link_rounded, size: 20),
              label: Text(total > 0 ? 'Manage devices' : 'Connect device'),
              style: ElevatedButton.styleFrom(
                backgroundColor: cs.primary,
                foregroundColor: cs.onPrimary,
                padding: const EdgeInsets.symmetric(vertical: 14),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(AppDimensions.radiusMD),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _Dot extends StatelessWidget {
  final Color color;
  const _Dot({required this.color});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 9,
      height: 9,
      decoration: BoxDecoration(
        color: color,
        shape: BoxShape.circle,
        boxShadow: [
          BoxShadow(color: color.withValues(alpha: 0.6), blurRadius: 6),
        ],
      ),
    );
  }
}
