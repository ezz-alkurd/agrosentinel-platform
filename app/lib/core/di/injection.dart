import '../network/field_api_client.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:get_it/get_it.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../../features/ai_diagnostic/data/datasources/diagnostic_datasource.dart';
import '../../features/ai_diagnostic/data/datasources/on_device_diagnostic_datasource.dart';
import '../../features/ai_diagnostic/data/repositories/diagnostic_repository_impl.dart';
import '../../features/ai_diagnostic/domain/repositories/diagnostic_repository.dart';
import '../../features/ai_diagnostic/domain/usecases/analyze_image_usecase.dart';
import '../../features/ai_diagnostic/presentation/cubit/diagnostic_cubit.dart';

import '../../features/auth/data/datasources/auth_remote_datasource.dart';
import '../../features/auth/data/repositories/auth_repository_impl.dart';
import '../../features/auth/domain/repositories/auth_repository.dart';
import '../../features/auth/domain/usecases/login_usecase.dart';
import '../../features/auth/domain/usecases/signup_usecase.dart';
import '../../features/auth/presentation/bloc/auth_bloc.dart';

import '../../features/home/data/datasources/home_remote_datasource.dart';
import '../../features/home/data/repositories/home_repository_impl.dart';
import '../../features/home/domain/repositories/home_repository.dart';
import '../../features/home/domain/usecases/get_drone_status_usecase.dart';
import '../../features/home/presentation/cubit/home_cubit.dart';

import '../../features/map/data/datasources/map_datasource.dart';
import '../../features/map/data/repositories/map_repository_impl.dart';
import '../../features/map/domain/repositories/map_repository.dart';
import '../../features/map/domain/usecases/get_map_data_usecase.dart';
import '../../features/map/presentation/cubit/map_cubit.dart';

import '../../features/notifications/data/datasources/notification_datasource.dart';
import '../../features/notifications/data/datasources/notification_api_datasource.dart';
import '../../features/notifications/data/datasources/notification_read_store.dart';
import '../../features/notifications/data/repositories/notification_repository_impl.dart';
import '../../features/notifications/domain/repositories/notification_repository.dart';
import '../../features/notifications/domain/usecases/get_notifications_usecase.dart';
import '../../features/notifications/presentation/cubit/notifications_cubit.dart';

import '../../features/detections/data/datasources/detections_remote_datasource.dart';
import '../../features/detections/data/repositories/detections_repository_impl.dart';
import '../../features/detections/domain/repositories/detections_repository.dart';
import '../../features/detections/presentation/cubit/detections_cubit.dart';
import '../../features/settings/data/datasources/settings_local_datasource.dart';
import '../../features/settings/data/repositories/settings_repository_impl.dart';
import '../../features/settings/domain/repositories/settings_repository.dart';
import '../../features/settings/domain/usecases/toggle_language_usecase.dart';
import '../../features/settings/domain/usecases/toggle_theme_usecase.dart';
import '../../features/settings/presentation/cubit/settings_cubit.dart';

final sl = GetIt.instance;

Future<void> setupInjection() async {
  // ── External ──────────────────────────────────────────────────────────────
  final sharedPrefs = await SharedPreferences.getInstance();
  sl.registerLazySingleton(() => sharedPrefs);

  // Firebase — real instance (replaced by mock in tests)
  sl.registerLazySingleton<FirebaseAuth>(() => FirebaseAuth.instance);
  sl.registerLazySingleton(() => FieldApiClient(sharedPrefs, sl<FirebaseAuth>()));


  // ── Data Sources ──────────────────────────────────────────────────────────
  sl.registerLazySingleton<AuthRemoteDataSource>(
    () => AuthRemoteDataSourceImpl(firebaseAuth: sl()),
  );
  sl.registerLazySingleton<HomeRemoteDataSource>(() => HomeRemoteDataSourceImpl());
  sl.registerLazySingleton<NotificationDataSource>(() => NotificationApiDataSource(sl()));
  sl.registerLazySingleton(() => NotificationReadStore(sl()));
  sl.registerLazySingleton<MapDataSource>(() => MapDataSourceImpl(sl()));
  sl.registerLazySingleton<DiagnosticDataSource>(() => OnDeviceDiagnosticDataSource());
  sl.registerLazySingleton<DetectionsRemoteDataSource>(() => DetectionsRemoteDataSourceImpl(sl()));
  sl.registerLazySingleton<SettingsLocalDataSource>(
    () => SettingsLocalDataSourceImpl(sl()),
  );

  // ── Repositories ──────────────────────────────────────────────────────────
  sl.registerLazySingleton<AuthRepository>(() => AuthRepositoryImpl(sl()));
  sl.registerLazySingleton<HomeRepository>(() => HomeRepositoryImpl(sl()));
  sl.registerLazySingleton<NotificationRepository>(
    () => NotificationRepositoryImpl(sl()),
  );
  sl.registerLazySingleton<MapRepository>(() => MapRepositoryImpl(sl()));
  sl.registerLazySingleton<DiagnosticRepository>(
    () => DiagnosticRepositoryImpl(sl()),
  );
  sl.registerLazySingleton<DetectionsRepository>(() => DetectionsRepositoryImpl(sl()));
  sl.registerLazySingleton<SettingsRepository>(() => SettingsRepositoryImpl(sl()));

  // ── Use Cases ─────────────────────────────────────────────────────────────
  sl.registerLazySingleton(() => LoginUseCase(sl()));
  sl.registerLazySingleton(() => SignupUseCase(sl()));
  sl.registerLazySingleton(() => GetDroneStatusUseCase(sl()));
  sl.registerLazySingleton(() => GetNotificationsUseCase(sl()));
  sl.registerLazySingleton(() => GetMapDataUseCase(sl()));
  sl.registerLazySingleton(() => AnalyzeImageUseCase(sl()));
  sl.registerLazySingleton(() => ToggleThemeUseCase(sl()));
  sl.registerLazySingleton(() => ToggleLanguageUseCase(sl()));

  // ── Presentation (BLoC / Cubit) ───────────────────────────────────────────
  // AuthBloc is a singleton so GoRouter can subscribe to its stream.
  // It now receives the repository directly so it can call checkCurrentUser.
  sl.registerLazySingleton(
    () => AuthBloc(
      repository: sl(),
      loginUseCase: sl(),
      signupUseCase: sl(),
    ),
  );

  // SettingsCubit is singleton (drives MaterialApp theme/locale)
  sl.registerLazySingleton(
    () => SettingsCubit(
      repository: sl(),
      toggleThemeUseCase: sl(),
      toggleLanguageUseCase: sl(),
    ),
  );

  // Per-screen cubits are factories (new instance each navigation)
  sl.registerFactory(() => HomeCubit(sl()));
  sl.registerFactory(() => NotificationsCubit(sl(), sl()));
  sl.registerFactory(() => MapCubit(sl()));
  sl.registerFactory(() => DiagnosticCubit(sl()));
  sl.registerFactory(() => DetectionsCubit(sl()));
}
