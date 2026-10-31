import 'dart:async';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:agri_drone_ai/features/auth/data/datasources/auth_remote_datasource.dart';
import 'package:agri_drone_ai/features/auth/data/models/user_model.dart';
import 'package:agri_drone_ai/features/auth/data/repositories/auth_repository_impl.dart';
import 'package:agri_drone_ai/features/settings/data/datasources/settings_local_datasource.dart';

class RestoringAuth implements AuthRemoteDataSource {
  final restored = Completer<UserModel?>();
  bool signedOut = false;
  @override
  UserModel? get currentUser => null;
  @override
  Future<UserModel?> restoreSession() => restored.future;
  @override
  Future<void> logout() async { signedOut = true; }
  @override
  Future<UserModel> login({required String email, required String password}) => throw UnimplementedError();
  @override
  Future<UserModel> signup({required String name, required String email, required String password}) => throw UnimplementedError();
  @override
  Future<void> sendPasswordReset({required String email}) => throw UnimplementedError();
}
void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  test('startup awaits restored account rather than treating initial null as logout', () async {
    final remote = RestoringAuth();
    final repository = AuthRepositoryImpl(remote);
    var finished = false;
    final result = repository.checkCurrentUser().then((value) { finished = true; return value; });
    await Future<void>.delayed(Duration.zero);
    expect(finished, isFalse);
    remote.restored.complete(const UserModel(id: 'restored-id', name: 'Restored account', email: 'restore@example.invalid'));
    final account = (await result).getOrElse(() => null);
    expect(account?.id, 'restored-id');
    expect(repository.currentUser?.id, 'restored-id');
    expect(remote.signedOut, isFalse);
  });
  test('requested dark appearance applies once and later theme choices persist', () async {
    SharedPreferences.setMockInitialValues({'app_theme': 'forestLight'});
    final preferences = await SharedPreferences.getInstance();
    final settings = SettingsLocalDataSourceImpl(preferences);
    expect(await settings.getAppTheme(), 'neonDark');
    await settings.saveAppTheme('forestLight');
    expect(await settings.getAppTheme(), 'forestLight');
  });
}
