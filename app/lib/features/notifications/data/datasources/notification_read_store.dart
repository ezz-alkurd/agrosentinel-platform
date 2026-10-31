import 'package:shared_preferences/shared_preferences.dart';

/// Persists which notifications the user has read.
/// (Firestore rules deny client writes, so read-state is kept locally.)
class NotificationReadStore {
  static const _key = 'read_notification_ids';
  final SharedPreferences _prefs;

  NotificationReadStore(this._prefs);

  Set<String> get _ids => _prefs.getStringList(_key)?.toSet() ?? <String>{};

  bool isRead(String id) => _ids.contains(id);

  Future<void> markRead(String id) async {
    final s = _ids..add(id);
    await _prefs.setStringList(_key, s.toList());
  }

  Future<void> markAll(Iterable<String> ids) async {
    final s = _ids..addAll(ids);
    await _prefs.setStringList(_key, s.toList());
  }
}
