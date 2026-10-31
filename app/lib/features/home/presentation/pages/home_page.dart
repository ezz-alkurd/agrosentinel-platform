import '../../../../core/network/field_api_client.dart';
import '../../../../core/di/injection.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/utils/event_time.dart';
import '../../../auth/presentation/bloc/auth_bloc.dart';
import '../../../auth/presentation/bloc/auth_state.dart';
import '../../../detections/data/models/detection_event_model.dart';
import '../../../detections/presentation/pages/detection_detail_page.dart';
import '../../../notifications/presentation/cubit/notifications_cubit.dart';
import '../widgets/device_connection_card.dart';

class HomePage extends StatefulWidget {
  const HomePage({super.key});
  @override
  State<HomePage> createState() => _HomePageState();
}
class _HomePageState extends State<HomePage> {
  int _revision = 0;
  @override
  void initState() { super.initState(); context.read<NotificationsCubit>().load(); }
  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final muted = cs.onSurface.withValues(alpha: .80);
    return Scaffold(body: SafeArea(bottom: false, child: RefreshIndicator(
      onRefresh: () async { setState(() => _revision++); await context.read<NotificationsCubit>().load(); },
      child: ListView(physics: const AlwaysScrollableScrollPhysics(), padding: const EdgeInsets.fromLTRB(22, 20, 22, 32), children: [
        Row(children: [Image.asset('assets/branding/agrosentinel-mark.png', width: 38, height: 38), const SizedBox(width: 11),
          Text('AgroSentinel', style: TextStyle(color: cs.onSurface, fontSize: 22, letterSpacing: -.7, fontWeight: FontWeight.w700)),
          const Spacer(), IconButton(onPressed: () => context.go('/settings'), icon: const Icon(Icons.tune_outlined), tooltip: 'Settings')]),
        const SizedBox(height: 26),
        BlocBuilder<AuthBloc, AuthState>(builder: (context, state) {
          final name = state is AuthAuthenticated ? state.user.name.trim().split(' ').first : '';
          return Text(name.isEmpty ? 'YOUR FIELD COMPANION' : 'WELCOME, ${name.toUpperCase()}', style: TextStyle(color: cs.primary, fontSize: 12, letterSpacing: 1.8, fontWeight: FontWeight.w700));
        }),
        const SizedBox(height: 12),
        Text('Your field overview', style: TextStyle(color: cs.onSurface, fontSize: 34, height: 1.08, fontWeight: FontWeight.w600, letterSpacing: -1.0)),
        const SizedBox(height: 14),
        Text('A closer look at your crops. A clear view of your camera events.', style: TextStyle(color: muted, fontSize: 14, height: 1.7)),
        const SizedBox(height: 26),
        Container(padding: const EdgeInsets.all(24), decoration: BoxDecoration(color: cs.primary.withValues(alpha: .10), borderRadius: BorderRadius.circular(24), border: Border.all(color: cs.primary.withValues(alpha: .15))),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Row(children: [Icon(Icons.center_focus_strong_outlined, color: cs.primary, size: 26), const Spacer(), Text('WORKS OFFLINE', style: TextStyle(color: cs.primary, fontSize: 11, letterSpacing: 1.4, fontWeight: FontWeight.w700))]),
            const SizedBox(height: 22), Text('Tomato leaf analysis', style: TextStyle(color: cs.onSurface, fontSize: 25, letterSpacing: -.6, fontWeight: FontWeight.w600)),
            const SizedBox(height: 10), Text('Capture one leaf and analyze it on this phone. No upload or laptop connection needed.', style: TextStyle(color: muted, fontSize: 15, height: 1.7)),
            const SizedBox(height: 22), FilledButton(onPressed: () => context.go('/ai-diagnostic'), child: const Text('Analyze a leaf')),
          ])),
        const SizedBox(height: 28),
        Text('Connected monitoring', style: TextStyle(color: cs.onSurface, fontSize: 21, fontWeight: FontWeight.w600)),
        const SizedBox(height: 7), Text('Camera presence and events sync through your account.', style: TextStyle(color: muted, fontSize: 14, height: 1.7)),
        const SizedBox(height: 16), const DeviceConnectionCard(),
        Align(alignment: Alignment.centerRight, child: TextButton.icon(onPressed: () => context.go('/map'), icon: const Icon(Icons.map_outlined, size: 18), label: const Text('Event map'))),
        const SizedBox(height: 12),
        Row(children: [Text('Latest camera events', style: TextStyle(color: cs.onSurface, fontSize: 20, fontWeight: FontWeight.w600)), const Spacer(), TextButton(onPressed: () => context.go('/detections'), child: const Text('View all'))]),
        _RecentEvents(key: ValueKey(_revision), onRetry: () => setState(() => _revision++)),
      ]),
    )));
  }
}
class _RecentEvents extends StatefulWidget {
  final VoidCallback onRetry;
  const _RecentEvents({super.key, required this.onRetry});
  @override
  State<_RecentEvents> createState() => _RecentEventsState();
}
class _RecentEventsState extends State<_RecentEvents> {
  late final _stream = sl<FieldApiClient>().watchEvents();
  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final muted = cs.onSurface.withValues(alpha: .80);
    return StreamBuilder<List<Map<String, dynamic>>>(stream: _stream, builder: (context, snapshot) {
      if (snapshot.hasError) return Padding(padding: const EdgeInsets.all(20), child: Column(children: [Text('Could not load camera events. Check your connection and sign-in.', style: TextStyle(color: muted)), TextButton(onPressed: widget.onRetry, child: const Text('Retry'))]));
      if (!snapshot.hasData) return const Padding(padding: EdgeInsets.all(28), child: Center(child: CircularProgressIndicator(strokeWidth: 2)));
      if (snapshot.data!.isEmpty) {
        return Container(width: double.infinity, padding: const EdgeInsets.all(24), decoration: BoxDecoration(color: cs.surface, borderRadius: BorderRadius.circular(18)),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Text('No camera events yet', style: TextStyle(color: cs.onSurface, fontSize: 17, fontWeight: FontWeight.w600)), const SizedBox(height: 9), Text('Confirmed detections from a connected source will appear here.', style: TextStyle(color: muted, height: 1.7))]));
      }
      return Column(children: [
        ...snapshot.data!.take(3).map((doc) {
          final event = DetectionEventModel.fromJson(doc);
          final isFire = event.anomalyType == 'fire' || event.anomalyType == 'smoke';
          final rawName = event.diseaseName ?? event.anomalyType;
          final title = rawName.isEmpty ? 'Camera event' : rawName.replaceAll('___', ' · ').replaceAll('_', ' ');
          return Container(margin: const EdgeInsets.only(bottom: 10), decoration: BoxDecoration(color: cs.surface, borderRadius: BorderRadius.circular(16)), child: ListTile(
            contentPadding: const EdgeInsets.symmetric(horizontal: 17, vertical: 10),
            leading: Icon(isFire ? Icons.local_fire_department_outlined : Icons.eco_outlined, color: isFire ? const Color(0xFFEAB171) : cs.primary),
            title: Text(title, maxLines: 1, overflow: TextOverflow.ellipsis, style: TextStyle(color: cs.onSurface, fontWeight: FontWeight.w600)),
            subtitle: Text(displayEventTime(event.timestamp), style: TextStyle(color: muted, fontSize: 13)),
            trailing: Icon(Icons.arrow_forward_ios, size: 13, color: muted),
            onTap: () => Navigator.of(context).push(MaterialPageRoute<void>(builder: (_) => DetectionDetailPage(event: event))),
          ));
        }),
      ]);
    });
  }
}
