import 'package:flutter/material.dart';
import '../../../../core/di/injection.dart';
import '../../../../core/network/field_api_client.dart';
import '../../../../core/utils/event_time.dart';

class ConnectDevicePage extends StatefulWidget {
  const ConnectDevicePage({super.key});
  @override
  State<ConnectDevicePage> createState() => _ConnectDevicePageState();
}
class _ConnectDevicePageState extends State<ConnectDevicePage> {
  final _api = sl<FieldApiClient>();
  late final TextEditingController _url = TextEditingController(text: _api.baseUrl);
  final _code = TextEditingController();
  final _name = TextEditingController(text: 'Field laptop');
  late Stream<List<Map<String, dynamic>>> _devices = _api.watchDevices();
  bool _busy = false;
  String? _message;
  String _serverStatus = 'Checking server connection...';
  @override
  void initState() {
    super.initState();
    _checkServer();
  }
  Future<void> _checkServer() async {
    try {
      await _api.health();
      if (mounted) setState(() => _serverStatus = 'Server connection verified.');
    } catch (_) {
      if (mounted) setState(() => _serverStatus = 'Server unavailable. Check your internet connection and try again.');
    }
  }
  @override
  void dispose() { _url.dispose(); _code.dispose(); _name.dispose(); super.dispose(); }
  Future<void> _act(Future<void> Function() action, String success) async {
    setState(() { _busy = true; _message = null; });
    try {
      await action();
      if (mounted) setState(() { _message = success; _devices = _api.watchDevices(); });
    } catch (error) {
      if (mounted) setState(() => _message = error.toString().replaceFirst('Bad state: ', ''));
    } finally { if (mounted) setState(() => _busy = false); }
  }
  Future<void> _revoke(Map<String, dynamic> device) async {
    final confirmed = await showDialog<bool>(context: context, builder: (context) => AlertDialog(
      title: const Text('Disconnect this laptop?'),
      content: const Text('Its upload credential will stop working. Pair it again to reconnect.'),
      actions: [TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancel')),
        TextButton(onPressed: () => Navigator.pop(context, true), child: const Text('Disconnect'))],
    ));
    if (confirmed == true) await _act(() => _api.revoke(device['id'] as String), 'Laptop disconnected.');
  }
  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final muted = cs.onSurface.withValues(alpha: .80);
    return Scaffold(appBar: AppBar(title: const Text('Server & paired devices')),
      body: ListView(padding: const EdgeInsets.all(22), children: [
        Text('One connected field.', style: TextStyle(color: cs.onSurface, fontSize: 32, fontWeight: FontWeight.w600, letterSpacing: -1)),
        const SizedBox(height: 12),
        Text('Your AgroSentinel server is already configured. Pair a laptop to receive its camera events. Your sign-in controls access to your events.', style: TextStyle(color: muted, height: 1.7)),
        const SizedBox(height: 28),
        Text(_serverStatus, style: TextStyle(color: muted, height: 1.7)),
        Align(alignment: Alignment.centerLeft, child: TextButton(onPressed: _busy ? null : _checkServer, child: const Text('Check connection'))),
        ExpansionTile(title: const Text('Advanced server settings'), childrenPadding: const EdgeInsets.symmetric(vertical: 12), children: [
          TextField(controller: _url, keyboardType: TextInputType.url, autocorrect: false, decoration: const InputDecoration(labelText: 'Website address', helperText: 'Already configured. Change only when moving the server.')),
          const SizedBox(height: 16),
          FilledButton(onPressed: _busy ? null : () => _act(() async { await _api.setBaseUrl(_url.text); await _api.health(); await _checkServer(); }, 'Server connection verified.'), child: const Text('Save server address')),
        ]),
        const SizedBox(height: 32),
        Text('Pair a laptop', style: TextStyle(color: cs.onSurface, fontSize: 23, fontWeight: FontWeight.w600)),
        const SizedBox(height: 10),
        Text('In the Windows app, choose Pair with phone. Enter its eight-character code here.', style: TextStyle(color: muted, height: 1.7)),
        const SizedBox(height: 18),
        TextField(controller: _code, textCapitalization: TextCapitalization.characters, maxLength: 9, autocorrect: false, decoration: const InputDecoration(labelText: 'Pairing code', hintText: 'ABCD-EFGH')),
        const SizedBox(height: 12),
        TextField(controller: _name, maxLength: 120, decoration: const InputDecoration(labelText: 'Laptop name')),
        const SizedBox(height: 16),
        OutlinedButton(onPressed: _busy ? null : () => _act(() => _api.claim(_code.text.trim(), _name.text.trim()), 'Laptop paired. You can start monitoring on Windows.'), child: const Text('Pair laptop')),
        if (_busy) const Padding(padding: EdgeInsets.all(20), child: Center(child: CircularProgressIndicator(strokeWidth: 2))),
        if (_message != null) Padding(padding: const EdgeInsets.symmetric(vertical: 18), child: Text(_message!, style: TextStyle(color: cs.primary, height: 1.7))),
        const SizedBox(height: 28),
        Row(children: [Text('Your devices', style: TextStyle(color: cs.onSurface, fontSize: 23, fontWeight: FontWeight.w600)), const Spacer(), IconButton(tooltip: 'Refresh', onPressed: () => setState(() => _devices = _api.watchDevices()), icon: const Icon(Icons.refresh))]),
        StreamBuilder<List<Map<String, dynamic>>>(stream: _devices, builder: (context, snapshot) {
          if (snapshot.hasError) return Padding(padding: const EdgeInsets.all(18), child: Text('Device list unavailable. Check your connection and make sure you are signed in.', style: TextStyle(color: muted)));
          if (!snapshot.hasData) return const Padding(padding: EdgeInsets.all(22), child: Center(child: CircularProgressIndicator(strokeWidth: 2)));
          if (snapshot.data!.isEmpty) return Padding(padding: const EdgeInsets.symmetric(vertical: 22), child: Text('No laptops paired yet.', style: TextStyle(color: muted)));
          return Column(children: snapshot.data!.map((device) {
            final lastSeen = parseEventTime(device['last_seen']);
            final age = DateTime.now().toUtc().difference(lastSeen.toUtc());
            final live = device['online'] == true && !age.isNegative && age < const Duration(seconds: 30);
            return Container(margin: const EdgeInsets.only(top: 12), decoration: BoxDecoration(color: cs.surface, borderRadius: BorderRadius.circular(18)), child: ListTile(
              contentPadding: const EdgeInsets.all(16), leading: Icon(Icons.laptop_windows, color: live ? cs.primary : muted),
              title: Text(device['name'] as String? ?? 'Laptop'),
              subtitle: Text(live ? 'Connected' : hasEventTime(lastSeen) ? 'Offline · ${displayEventTime(lastSeen)}' : 'Waiting for the first heartbeat'),
              trailing: IconButton(tooltip: 'Disconnect', onPressed: _busy ? null : () => _revoke(device), icon: const Icon(Icons.link_off)),
            ));
          }).toList());
        }),
        const SizedBox(height: 24), Text('Camera events refresh while the app is open. Offline leaf analysis works independently of this server.', style: TextStyle(color: muted, fontSize: 14, height: 1.7)),
      ]));
  }
}
