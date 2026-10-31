import '../../../../core/utils/event_time.dart';
import 'package:cached_network_image/cached_network_image.dart';
import '../../../../core/di/injection.dart';
import '../../../../core/network/field_api_client.dart';
import 'package:flutter/material.dart';

import '../../../../core/constants/app_colors.dart';
import '../../../../core/constants/app_dimensions.dart';
import '../../domain/entities/detection_event_entity.dart';

/// Full-screen detail view for a single detection event.
/// Navigated to by tapping a card on [DetectionsPage].
///
/// Shows:
///  • Full-size detection image (loaded from the private API evidence endpoint)
///  • Anomaly type badge + confidence
///  • Disease / smoke / fire label
///  • Timestamp, GPS coordinates, event status
///  • Short event ID
class DetectionDetailPage extends StatefulWidget {
  final DetectionEventEntity event;

  const DetectionDetailPage({super.key, required this.event});

  @override
  State<DetectionDetailPage> createState() => _DetectionDetailPageState();
}

class _DetectionDetailPageState extends State<DetectionDetailPage> {
  Future<String>? _imageUrlFuture;

  @override
  void initState() {
    super.initState();
    if (widget.event.imageUrl.isNotEmpty) _imageUrlFuture = Future.value(widget.event.imageUrl);
  }

  Future<void> _confirmDelete() async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (dctx) => AlertDialog(
        backgroundColor: AppColors.backgroundCard,
        title: const Text('Delete event?'),
        content: const Text(
            'This removes it from Events, Alerts and the Map. This cannot be undone.'),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(dctx, false),
              child: const Text('Cancel')),
          TextButton(
            onPressed: () => Navigator.pop(dctx, true),
            child: const Text('Delete',
                style: TextStyle(color: AppColors.alertFire)),
          ),
        ],
      ),
    );
    if (ok != true) return;
    try {
      await sl<FieldApiClient>().deleteEvent(widget.event.id);
    } catch (_) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Could not delete the event. Check your server connection.')));
      return;
    }
    if (mounted) Navigator.of(context).pop();
  }

  // ─── Helpers ────────────────────────────────────────────────────────────────

  ({Color fg, Color bg, IconData icon, String label}) _typeStyle(
      String anomalyType) {
    switch (anomalyType.toLowerCase()) {
      case 'fire':
        return (
          fg: AppColors.alertFire,
          bg: AppColors.alertFireFaint,
          icon: Icons.local_fire_department_rounded,
          label: 'FIRE DETECTED',
        );
      case 'smoke':
        return (
          fg: AppColors.statusWarning,
          bg: const Color(0x26FF9500),
          icon: Icons.cloud_outlined,
          label: 'SMOKE DETECTED',
        );
      default: // disease
        return (
          fg: AppColors.alertDisease,
          bg: AppColors.alertDiseaseFaint,
          icon: Icons.eco_rounded,
          label: 'DISEASE DETECTED',
        );
    }
  }

  // ─── Build ──────────────────────────────────────────────────────────────────

  @override
  Widget build(BuildContext context) {
    final event = widget.event;
    final style = _typeStyle(event.anomalyType);
    final formatted =
        displayEventTime(event.timestamp);
    final confidencePct = (event.confidence * 100).toStringAsFixed(1);
    final displayTitle = (event.diseaseName?.isNotEmpty == true)
        ? event.diseaseName!
        : event.anomalyType.toUpperCase();

    return Scaffold(
      backgroundColor: AppColors.backgroundDeep,
      body: CustomScrollView(
        slivers: [
          // ── App bar with hero image ──────────────────────────────────────────
          SliverAppBar(
            expandedHeight: 280,
            pinned: true,
            backgroundColor: AppColors.backgroundBase,
            iconTheme: const IconThemeData(color: AppColors.textPrimary),
            actions: [
              IconButton(
                icon: const Icon(Icons.delete_outline_rounded),
                tooltip: 'Delete event',
                onPressed: _confirmDelete,
              ),
            ],
            flexibleSpace: FlexibleSpaceBar(
              background: _buildHeroImage(),
            ),
          ),

          // ── Content ─────────────────────────────────────────────────────────
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.all(AppDimensions.spaceMD),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Type badge + confidence row
                  Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 12, vertical: 6),
                        decoration: BoxDecoration(
                          color: style.bg,
                          borderRadius: BorderRadius.circular(
                              AppDimensions.radiusFull),
                          border: Border.all(
                              color: style.fg.withValues(alpha: 0.4)),
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(style.icon, color: style.fg, size: 14),
                            const SizedBox(width: 6),
                            Text(
                              style.label,
                              style: TextStyle(
                                color: style.fg,
                                fontSize: 13,
                                fontWeight: FontWeight.w700,
                                letterSpacing: 0.8,
                              ),
                            ),
                          ],
                        ),
                      ),
                      const Spacer(),
                      _ConfidencePill(
                          confidence: event.confidence,
                          pct: confidencePct),
                    ],
                  ),

                  const SizedBox(height: AppDimensions.spaceMD),

                  // Main title (disease name or anomaly type)
                  Text(
                    displayTitle,
                    style: const TextStyle(
                      color: AppColors.textPrimary,
                      fontSize: 22,
                      fontWeight: FontWeight.w800,
                    ),
                  ),

                  const SizedBox(height: AppDimensions.spaceLG),

                  // Detail card
                  _DetailCard(
                    rows: [
                      _DetailRow(
                        icon: Icons.access_time_outlined,
                        label: 'Detected at',
                        value: formatted,
                      ),
                      _DetailRow(
                        icon: Icons.location_on_outlined,
                        label: 'GPS',
                        value: event.gpsLat == 0.0 && event.gpsLng == 0.0
                            ? 'No GPS data'
                            : '${event.gpsLat.toStringAsFixed(6)},  '
                                '${event.gpsLng.toStringAsFixed(6)}',
                        valueColor: event.gpsLat == 0.0
                            ? AppColors.textMuted
                            : AppColors.textPrimary,
                      ),
                      _DetailRow(
                        icon: Icons.info_outline_rounded,
                        label: 'Status',
                        value: event.status.toUpperCase(),
                        valueColor: event.status == 'new'
                            ? AppColors.alertFire
                            : AppColors.statusOnline,
                      ),
                      _DetailRow(
                        icon: Icons.tag_rounded,
                        label: 'Event ID',
                        value: event.id.length > 16
                            ? '${event.id.substring(0, 16)}…'
                            : event.id,
                      ),
                    ],
                  ),

                  const SizedBox(height: AppDimensions.spaceXL),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  // ─── Hero image ─────────────────────────────────────────────────────────────

  Widget _buildHeroImage() {
    if (_imageUrlFuture == null) {
      return _placeholder();
    }

    return FutureBuilder<String>(
      future: _imageUrlFuture,
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return _placeholder(
              child: const CircularProgressIndicator(
                  color: AppColors.neonGreen, strokeWidth: 2));
        }
        if (snapshot.hasError || !snapshot.hasData) {
          return _placeholder(
              child: const Icon(Icons.broken_image_outlined,
                  color: AppColors.textMuted, size: 48));
        }
        return CachedNetworkImage(
          imageUrl: snapshot.data!,
          cacheKey: widget.event.id,
          fit: BoxFit.cover,
          width: double.infinity,
          height: 280,
          placeholder: (_, __) => _placeholder(
              child: const CircularProgressIndicator(
                  color: AppColors.neonGreen, strokeWidth: 2)),
          errorWidget: (_, url, error) => _placeholder(
              child: const Icon(Icons.broken_image_outlined,
                  color: AppColors.textMuted, size: 48)),
        );
      },
    );
  }

  Widget _placeholder({Widget? child}) {
    return Container(
      color: AppColors.backgroundElevated,
      alignment: Alignment.center,
      child: child ?? const SizedBox.shrink(),
    );
  }
}

// ─── Sub-widgets ──────────────────────────────────────────────────────────────

class _ConfidencePill extends StatelessWidget {
  final double confidence;
  final String pct;

  const _ConfidencePill({required this.confidence, required this.pct});

  @override
  Widget build(BuildContext context) {
    final color = confidence >= 0.8
        ? AppColors.statusOnline
        : confidence >= 0.5
            ? AppColors.statusWarning
            : AppColors.statusOffline;

    return Container(
      padding:
          const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius:
            BorderRadius.circular(AppDimensions.radiusFull),
        border: Border.all(color: color.withValues(alpha: 0.4)),
      ),
      child: Text(
        '$pct% confidence',
        style: TextStyle(
          color: color,
          fontSize: 14,
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }
}

class _DetailCard extends StatelessWidget {
  final List<_DetailRow> rows;

  const _DetailCard({required this.rows});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(AppDimensions.spaceMD),
      decoration: BoxDecoration(
        color: AppColors.backgroundCard,
        borderRadius: BorderRadius.circular(AppDimensions.radiusLG),
        border: Border.all(color: AppColors.borderDim),
      ),
      child: Column(
        children: rows
            .expand((row) => [row, const Divider(color: AppColors.borderDim, height: 24)])
            .toList()
          ..removeLast(), // remove trailing divider
      ),
    );
  }
}

class _DetailRow extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;
  final Color? valueColor;

  const _DetailRow({
    required this.icon,
    required this.label,
    required this.value,
    this.valueColor,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Icon(icon, size: 16, color: AppColors.textSecondary),
        const SizedBox(width: 10),
        Text(
          label,
          style: const TextStyle(
            color: AppColors.textSecondary,
            fontSize: 15,
            fontWeight: FontWeight.w500,
          ),
        ),
        const Spacer(),
        Flexible(
          child: Text(
            value,
            textAlign: TextAlign.end,
            style: TextStyle(
              color: valueColor ?? AppColors.textPrimary,
              fontSize: 15,
              fontWeight: FontWeight.w500,
            ),
          ),
        ),
      ],
    );
  }
}
