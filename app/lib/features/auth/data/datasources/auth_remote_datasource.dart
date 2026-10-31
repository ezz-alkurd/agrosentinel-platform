import 'package:firebase_auth/firebase_auth.dart' as fb;
import '../models/user_model.dart';

abstract class AuthRemoteDataSource {
  Future<UserModel> login({required String email, required String password});
  Future<UserModel> signup({required String name, required String email, required String password});
  Future<void> logout();
  Future<void> sendPasswordReset({required String email});
  UserModel? get currentUser;
  Future<UserModel?> restoreSession();
}

class AuthRemoteDataSourceImpl implements AuthRemoteDataSource {
  final fb.FirebaseAuth _firebaseAuth;

  AuthRemoteDataSourceImpl({fb.FirebaseAuth? firebaseAuth})
      : _firebaseAuth = firebaseAuth ?? fb.FirebaseAuth.instance;

  @override
  UserModel? get currentUser {
    final user = _firebaseAuth.currentUser;
    if (user == null) return null;
    return _toModel(user);
  }

  @override
  Future<UserModel?> restoreSession() async {
    // The first event waits for Firebase to restore its persisted Android user.
    final user = await _firebaseAuth.authStateChanges().first;
    return user == null ? null : _toModel(user);
  }

  @override
  Future<UserModel> login({
    required String email,
    required String password,
  }) async {
    final credential = await _firebaseAuth.signInWithEmailAndPassword(
      email: email,
      password: password,
    );
    return _toModel(credential.user!);
  }

  @override
  Future<UserModel> signup({
    required String name,
    required String email,
    required String password,
  }) async {
    final credential = await _firebaseAuth.createUserWithEmailAndPassword(
      email: email,
      password: password,
    );
    // Save display name
    await credential.user!.updateDisplayName(name);
    await credential.user!.reload();
    return _toModel(_firebaseAuth.currentUser!);
  }

  @override
  Future<void> logout() => _firebaseAuth.signOut();

  @override
  Future<void> sendPasswordReset({required String email}) =>
      _firebaseAuth.sendPasswordResetEmail(email: email);

  // ── helpers ────────────────────────────────────────────────────────────────
  UserModel _toModel(fb.User user) => UserModel(
        id: user.uid,
        name: user.displayName ?? user.email?.split('@').first ?? 'Farmer',
        email: user.email ?? '',
        avatarUrl: user.photoURL,
        farmName: '',
        totalScans: 0,
        alertsToday: 0,
      );
}
