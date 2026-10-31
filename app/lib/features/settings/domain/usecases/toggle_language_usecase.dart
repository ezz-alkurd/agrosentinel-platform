import '../repositories/settings_repository.dart';

class ToggleLanguageUseCase {
  final SettingsRepository _repository;
  ToggleLanguageUseCase(this._repository);

  Future<void> call(String languageCode) => _repository.saveLanguageCode(languageCode);
}
