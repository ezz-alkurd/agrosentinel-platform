import '../../../../core/utils/event_time.dart';
import 'dart:async';
import 'dart:math' show min, max;

import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';

import '../../../../core/constants/app_colors.dart';
import '../../../../core/constants/app_dimensions.dart';
// Hide the project's own LatLng so it doesn't clash with google_maps_flutter's LatLng.
import '../../domain/entities/map_marker_entity.dart' hide LatLng;
import '../cubit/map_cubit.dart';
import '../cubit/map_state.dart';
import '../widgets/map_legend.dart';

// ─── Dark / night map style ───────────────────────────────────────────────────
const _kDarkMapStyle = '''[
  {"elementType":"geometry","stylers":[{"color":"#1d2c4d"}]},
  {"elementType":"labels.text.fill","stylers":[{"color":"#8ec3b9"}]},
  {"elementType":"labels.text.stroke","stylers":[{"color":"#1a3646"}]},
  {"featureType":"administrative.country","elementType":"geometry.stroke","stylers":[{"color":"#4b6878"}]},
  {"featureType":"landscape.natural","elementType":"geometry","stylers":[{"color":"#023e58"}]},
  {"featureType":"poi","elementType":"geometry","stylers":[{"color":"#283d6a"}]},
  {"featureType":"poi","elementType":"labels.text.fill","stylers":[{"color":"#6f9ba5"}]},
  {"featureType":"poi.park","elementType":"geometry.fill","stylers":[{"color":"#023e58"}]},
  {"featureType":"road","elementType":"geometry","stylers":[{"color":"#304a7d"}]},
  {"featureType":"road","elementType":"labels.text.fill","stylers":[{"color":"#98a5be"}]},
  {"featureType":"road.highway","elementType":"geometry","stylers":[{"color":"#2c6675"}]},
  {"featureType":"road.highway","elementType":"labels.text.fill","stylers":[{"color":"#b0d5ce"}]},
  {"featureType":"transit","elementType":"labels.text.fill","stylers":[{"color":"#98a5be"}]},
  {"featureType":"water","elementType":"geometry","stylers":[{"color":"#0e1626"}]},
  {"featureType":"water","elementType":"labels.text.fill","stylers":[{"color":"#4e6d70"}]}
]''';

class MapPage extends StatefulWidget {
  const MapPage({super.key});

  @override
  State<MapPage> createState() => _MapPageState();
}

class _MapPageState extends State<MapPage> {
  final Completer<GoogleMapController> _controllerCompleter = Completer();

  static const _defaultZoom = 14.0;

  @override
  void initState() {
    super.initState();
    context.read<MapCubit>().loadMapData();
  }

  // ─── Map created ───────────────────────────────────────────────────────────

  void _onMapCreated(GoogleMapController controller) {
    if (!_controllerCompleter.isCompleted) {
      _controllerCompleter.complete(controller);
    }
  }

  // ─── Camera helpers ────────────────────────────────────────────────────────

  Future<void> _fitToMarkers(List<MapMarkerEntity> markers) async {
    if (markers.isEmpty) return;
    final ctrl = await _controllerCompleter.future;

    // Detections often share the same IP-based coordinates → one location.
    if (_group(markers).length <= 1) {
      final m = markers.first;
      await ctrl.animateCamera(
          CameraUpdate.newLatLngZoom(LatLng(m.latitude, m.longitude), 16.5));
      return;
    }

    double swLat = markers.first.latitude;
    double swLng = markers.first.longitude;
    double neLat = markers.first.latitude;
    double neLng = markers.first.longitude;
    for (final m in markers) {
      swLat = min(swLat, m.latitude);
      swLng = min(swLng, m.longitude);
      neLat = max(neLat, m.latitude);
      neLng = max(neLng, m.longitude);
    }
    const pad = 0.01;
    final bounds = LatLngBounds(
      southwest: LatLng(swLat - pad, swLng - pad),
      northeast: LatLng(neLat + pad, neLng + pad),
    );
    await ctrl.animateCamera(CameraUpdate.newLatLngBounds(bounds, 60));
  }

  // ─── Marker detail bottom sheet ────────────────────────────────────────────

  void _showMarkerDetail(BuildContext context, MapMarkerEntity marker) {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      builder: (_) => _MarkerDetailSheet(marker: marker),
    );
  }

  // ─── Group detections that share a location ────────────────────────────────

  String _locKey(MapMarkerEntity m) =>
      '${m.latitude.toStringAsFixed(4)},${m.longitude.toStringAsFixed(4)}';

  Map<String, List<MapMarkerEntity>> _group(List<MapMarkerEntity> markers) {
    final g = <String, List<MapMarkerEntity>>{};
    for (final m in markers) {
      (g[_locKey(m)] ??= []).add(m);
    }
    return g;
  }

  void _showGroupDetail(BuildContext context, List<MapMarkerEntity> list) {
    if (list.length == 1) {
      _showMarkerDetail(context, list.first);
      return;
    }
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      builder: (_) => _GroupDetailSheet(
        markers: list,
        onSelect: (m) {
          Navigator.of(context).pop();
          _showMarkerDetail(context, m);
        },
      ),
    );
  }

  // ─── Build Google Maps marker set (one marker per location) ────────────────

  Set<Marker> _buildMarkers(
      BuildContext context, List<MapMarkerEntity> markers) {
    final groups = _group(markers);
    return groups.entries.map((e) {
      final list = e.value
        ..sort((a, b) => b.detectedAt.compareTo(a.detectedAt));
      final anyFire = list.any((m) => m.type == MarkerType.fire);
      final hue = anyFire ? BitmapDescriptor.hueRed : BitmapDescriptor.hueOrange;
      final first = list.first;
      final title =
          list.length == 1 ? first.label : '${list.length} detections here';
      return Marker(
        markerId: MarkerId(e.key),
        position: LatLng(first.latitude, first.longitude),
        icon: BitmapDescriptor.defaultMarkerWithHue(hue),
        infoWindow: InfoWindow(title: title),
        onTap: () => _showGroupDetail(context, list),
      );
    }).toSet();
  }

  // ─── Build ─────────────────────────────────────────────────────────────────

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Live Map')),
      body: BlocConsumer<MapCubit, MapState>(
        listenWhen: (prev, curr) => curr is MapLoaded,
        listener: (context, state) {
          if (state is MapLoaded && state.markers.isNotEmpty) {
            WidgetsBinding.instance.addPostFrameCallback(
              (_) => _fitToMarkers(state.markers),
            );
          }
        },
        builder: (context, state) {
          if (state is MapLoading || state is MapInitial) {
            return const Center(
              child: CircularProgressIndicator(color: AppColors.neonGreen),
            );
          }
          if (state is MapError) {
            return Center(
              child: Text(state.message,
                  style: const TextStyle(color: AppColors.alertFire)),
            );
          }

          final markers =
              state is MapLoaded ? state.markers : <MapMarkerEntity>[];

          if (markers.isEmpty) {
            return Center(child: Padding(padding: const EdgeInsets.all(32), child: Column(
              mainAxisSize: MainAxisSize.min, children: [
                Icon(Icons.location_off_outlined, size: 42, color: Theme.of(context).colorScheme.primary),
                const SizedBox(height: 18),
                const Text('No geotagged events yet', style: TextStyle(fontSize: 22, fontWeight: FontWeight.w600)),
                const SizedBox(height: 12),
                const Text('Camera events appear here when they contain a recorded location. No drone location or route has been supplied.', textAlign: TextAlign.center),
                const SizedBox(height: 20),
                OutlinedButton(onPressed: () => context.read<MapCubit>().loadMapData(), child: const Text('Refresh')),
              ])));
          }

          // Detection markers only — no drone marker or flight path (no drone yet).
          final gmMarkers = _buildMarkers(context, markers);

          return Stack(
            children: [
              // ── Google Map ─────────────────────────────────────────────────
              GoogleMap(
                style: _kDarkMapStyle,
                onMapCreated: _onMapCreated,
                initialCameraPosition: CameraPosition(
                  target: LatLng(markers.first.latitude, markers.first.longitude),
                  zoom: _defaultZoom,
                ),
                markers: gmMarkers,
                myLocationButtonEnabled: false,
                zoomControlsEnabled: false,
                mapToolbarEnabled: false,
              ),

              // ── Counter banner ─────────────────────────────────────────────
              Positioned(
                top: AppDimensions.spaceMD,
                left: AppDimensions.spaceMD,
                right: AppDimensions.spaceMD,
                child: _InfoBanner(markerCount: markers.length),
              ),

              // ── Legend ─────────────────────────────────────────────────────
              const Positioned(
                left: AppDimensions.spaceMD,
                bottom: AppDimensions.spaceLG,
                child: MapLegend(),
              ),

              // ── Fit + Refresh buttons ──────────────────────────────────────
              Positioned(
                right: AppDimensions.spaceMD,
                bottom: AppDimensions.spaceLG,
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    if (markers.isNotEmpty)
                      Padding(
                        padding: const EdgeInsets.only(bottom: 8),
                        child: FloatingActionButton.small(
                          heroTag: 'fit',
                          backgroundColor: AppColors.backgroundCard,
                          onPressed: () => _fitToMarkers(markers),
                          child: const Icon(Icons.fit_screen_rounded,
                              color: AppColors.neonGreen),
                        ),
                      ),
                    FloatingActionButton.small(
                      heroTag: 'refresh',
                      backgroundColor: AppColors.backgroundCard,
                      onPressed: () =>
                          context.read<MapCubit>().loadMapData(),
                      child: const Icon(Icons.refresh_rounded,
                          color: AppColors.neonGreen),
                    ),
                  ],
                ),
              ),
            ],
          );
        },
      ),
    );
  }
}

// ─── Info banner ──────────────────────────────────────────────────────────────

class _InfoBanner extends StatelessWidget {
  final int markerCount;
  const _InfoBanner({required this.markerCount});

  @override
  Widget build(BuildContext context) {
    final label = markerCount == 0
        ? 'No detections yet — run the Python uploader to see events here'
        : '$markerCount detection${markerCount == 1 ? '' : 's'} loaded from Firestore';

    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: AppDimensions.spaceMD,
        vertical: AppDimensions.spaceSM,
      ),
      decoration: BoxDecoration(
        color: AppColors.backgroundCard.withValues(alpha: 0.92),
        borderRadius: BorderRadius.circular(AppDimensions.radiusMD),
        border: Border.all(color: AppColors.borderDim),
      ),
      child: Row(
        children: [
          Icon(
            markerCount == 0
                ? Icons.info_outline
                : Icons.check_circle_outline_rounded,
            size: 16,
            color: markerCount == 0
                ? AppColors.textSecondary
                : AppColors.neonGreen,
          ),
          const SizedBox(width: AppDimensions.spaceSM),
          Expanded(
            child: Text(
              label,
              style: TextStyle(
                color: markerCount == 0
                    ? AppColors.textSecondary
                    : AppColors.textPrimary,
                fontSize: 12,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// ─── Marker detail bottom sheet ───────────────────────────────────────────────

class _MarkerDetailSheet extends StatelessWidget {
  final MapMarkerEntity marker;
  const _MarkerDetailSheet({required this.marker});

  @override
  Widget build(BuildContext context) {
    final isFire = marker.type == MarkerType.fire;
    final color = isFire ? AppColors.alertFire : AppColors.alertDisease;
    final icon = isFire
        ? Icons.local_fire_department_rounded
        : Icons.eco_rounded;
    final typeLabel = isFire ? 'FIRE DETECTED' : 'DISEASE DETECTED';
    final timeFormatted =
        displayEventTime(marker.detectedAt);

    return Container(
      margin: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppColors.backgroundCard,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: color.withValues(alpha: 0.3)),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // Handle
          Container(
            width: 40,
            height: 4,
            margin: const EdgeInsets.only(top: 12, bottom: 16),
            decoration: BoxDecoration(
              color: AppColors.borderDim,
              borderRadius: BorderRadius.circular(2),
            ),
          ),

          // Type badge
          Container(
            padding:
                const EdgeInsets.symmetric(horizontal: 12, vertical: 5),
            decoration: BoxDecoration(
              color: color.withValues(alpha: 0.12),
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: color.withValues(alpha: 0.4)),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(icon, color: color, size: 16),
                const SizedBox(width: 6),
                Text(
                  typeLabel,
                  style: TextStyle(
                    color: color,
                    fontSize: 12,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 0.8,
                  ),
                ),
              ],
            ),
          ),

          const SizedBox(height: 16),

          // Label / disease name
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 24),
            child: Text(
              marker.label,
              textAlign: TextAlign.center,
              style: const TextStyle(
                color: AppColors.textPrimary,
                fontSize: 18,
                fontWeight: FontWeight.w700,
              ),
            ),
          ),

          const SizedBox(height: 16),

          // Detail rows
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 24),
            child: Column(
              children: [
                _DetailRow(
                  icon: Icons.location_on_outlined,
                  label: 'GPS',
                  value: '${marker.latitude.toStringAsFixed(5)}, '
                      '${marker.longitude.toStringAsFixed(5)}',
                ),
                const SizedBox(height: 10),
                _DetailRow(
                  icon: Icons.access_time_outlined,
                  label: 'Detected',
                  value: timeFormatted,
                ),
                const SizedBox(height: 10),
                _DetailRow(
                  icon: Icons.tag_rounded,
                  label: 'ID',
                  value: marker.id
                      .substring(0, min(marker.id.length, 12)),
                ),
              ],
            ),
          ),

          const SizedBox(height: 20),

          // Close button
          Padding(
            padding: const EdgeInsets.fromLTRB(24, 0, 24, 24),
            child: SizedBox(
              width: double.infinity,
              child: OutlinedButton(
                onPressed: () => Navigator.of(context).pop(),
                style: OutlinedButton.styleFrom(
                  foregroundColor: color,
                  side: BorderSide(color: color.withValues(alpha: 0.5)),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                  minimumSize: const Size(double.infinity, 44),
                ),
                child: const Text('Close'),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// ─── Detail row ───────────────────────────────────────────────────────────────

class _DetailRow extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;

  const _DetailRow({
    required this.icon,
    required this.label,
    required this.value,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Icon(icon, size: 15, color: AppColors.textSecondary),
        const SizedBox(width: 8),
        Text(
          '$label  ',
          style: const TextStyle(
            color: AppColors.textSecondary,
            fontSize: 12,
            fontWeight: FontWeight.w500,
          ),
        ),
        Expanded(
          child: Text(
            value,
            textAlign: TextAlign.end,
            style: const TextStyle(
              color: AppColors.textPrimary,
              fontSize: 13,
            ),
          ),
        ),
      ],
    );
  }
}

// ─── Group detail sheet (multiple detections at one location) ─────────────────

class _GroupDetailSheet extends StatelessWidget {
  final List<MapMarkerEntity> markers;
  final void Function(MapMarkerEntity) onSelect;

  const _GroupDetailSheet({required this.markers, required this.onSelect});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.all(12),
      constraints: BoxConstraints(
        maxHeight: MediaQuery.of(context).size.height * 0.6,
      ),
      decoration: BoxDecoration(
        color: AppColors.backgroundCard,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AppColors.borderDim),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 40,
            height: 4,
            margin: const EdgeInsets.only(top: 12, bottom: 12),
            decoration: BoxDecoration(
              color: AppColors.borderDim,
              borderRadius: BorderRadius.circular(2),
            ),
          ),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 20),
            child: Row(
              children: [
                Text(
                  '${markers.length} detections at this location',
                  style: const TextStyle(
                    color: AppColors.textPrimary,
                    fontSize: 15,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 8),
          Flexible(
            child: ListView.separated(
              shrinkWrap: true,
              padding: const EdgeInsets.fromLTRB(12, 4, 12, 16),
              itemCount: markers.length,
              separatorBuilder: (_, __) => const SizedBox(height: 6),
              itemBuilder: (_, i) {
                final m = markers[i];
                final isFire = m.type == MarkerType.fire;
                final color =
                    isFire ? AppColors.alertFire : AppColors.alertDisease;
                final icon = isFire
                    ? Icons.local_fire_department_rounded
                    : Icons.eco_rounded;
                final time = displayEventTime(m.detectedAt);
                return Material(
                  color: AppColors.backgroundElevated,
                  borderRadius: BorderRadius.circular(12),
                  child: InkWell(
                    borderRadius: BorderRadius.circular(12),
                    onTap: () => onSelect(m),
                    child: Padding(
                      padding: const EdgeInsets.all(12),
                      child: Row(
                        children: [
                          Icon(icon, color: color, size: 20),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  m.label,
                                  style: const TextStyle(
                                    color: AppColors.textPrimary,
                                    fontSize: 14,
                                    fontWeight: FontWeight.w600,
                                  ),
                                ),
                                Text(
                                  time,
                                  style: const TextStyle(
                                    color: AppColors.textMuted,
                                    fontSize: 12,
                                  ),
                                ),
                              ],
                            ),
                          ),
                          const Icon(Icons.chevron_right_rounded,
                              color: AppColors.textSecondary),
                        ],
                      ),
                    ),
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}
