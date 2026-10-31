import 'package:dartz/dartz.dart';
import '../../../../core/errors/failures.dart';
import '../entities/user_entity.dart';

abstract class AuthRepository {
  Future<Either<Failure, UserEntity>> login({
    required String email,
    required String password,
  });

  Future<Either<Failure, UserEntity>> signup({
    required String name,
    required String email,
    required String password,
  });

  Future<void> logout();

  /// Returns the currently signed-in user, or null when no session exists.
  Future<Either<Failure, UserEntity?>> checkCurrentUser();

  /// Sends a password-reset e-mail.
  Future<Either<Failure, void>> forgotPassword({required String email});

  UserEntity? get currentUser;
}
