import 'package:flutter_bloc/flutter_bloc.dart';
import '../../domain/repositories/auth_repository.dart';
import '../../domain/usecases/login_usecase.dart';
import '../../domain/usecases/signup_usecase.dart';
import 'auth_event.dart';
import 'auth_state.dart';

class AuthBloc extends Bloc<AuthEvent, AuthState> {
  final AuthRepository _repository;
  final LoginUseCase _login;
  final SignupUseCase _signup;

  AuthBloc({
    required AuthRepository repository,
    required LoginUseCase loginUseCase,
    required SignupUseCase signupUseCase,
  })  : _repository = repository,
        _login = loginUseCase,
        _signup = signupUseCase,
        super(const AuthInitial()) {
    on<AuthCheckRequested>(_onCheckAuth);
    on<AuthLoginRequested>(_onLogin);
    on<AuthSignupRequested>(_onSignup);
    on<AuthLogoutRequested>(_onLogout);
    on<AuthForgotPasswordRequested>(_onForgotPassword);
  }

  /// Called at startup — restores an existing Firebase session.
  Future<void> _onCheckAuth(
    AuthCheckRequested event,
    Emitter<AuthState> emit,
  ) async {
    final result = await _repository.checkCurrentUser();
    result.fold(
      (f) => emit(const AuthUnauthenticated()),
      (user) => user != null
          ? emit(AuthAuthenticated(user))
          : emit(const AuthUnauthenticated()),
    );
  }

  Future<void> _onLogin(
    AuthLoginRequested event,
    Emitter<AuthState> emit,
  ) async {
    emit(const AuthLoading());
    final result = await _login(email: event.email, password: event.password);
    result.fold(
      (f) => emit(AuthError(f.message)),
      (u) => emit(AuthAuthenticated(u)),
    );
  }

  Future<void> _onSignup(
    AuthSignupRequested event,
    Emitter<AuthState> emit,
  ) async {
    emit(const AuthLoading());
    final result = await _signup(
      name: event.name,
      email: event.email,
      password: event.password,
    );
    result.fold(
      (f) => emit(AuthError(f.message)),
      (u) => emit(AuthAuthenticated(u)),
    );
  }

  Future<void> _onLogout(
    AuthLogoutRequested event,
    Emitter<AuthState> emit,
  ) async {
    await _repository.logout();
    emit(const AuthUnauthenticated());
  }

  Future<void> _onForgotPassword(
    AuthForgotPasswordRequested event,
    Emitter<AuthState> emit,
  ) async {
    emit(const AuthLoading());
    final result = await _repository.forgotPassword(email: event.email);
    result.fold(
      (f) => emit(AuthError(f.message)),
      (_) => emit(AuthPasswordResetSent(event.email)),
    );
  }
}
