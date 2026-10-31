import 'package:equatable/equatable.dart';

class UserEntity extends Equatable {
  final String id;
  final String name;
  final String email;
  final String? avatarUrl;
  final String farmName;
  final int totalScans;
  final int alertsToday;

  const UserEntity({
    required this.id,
    required this.name,
    required this.email,
    this.avatarUrl,
    this.farmName = '',
    this.totalScans = 0,
    this.alertsToday = 0,
  });

  @override
  List<Object?> get props => [id, name, email, avatarUrl, farmName, totalScans, alertsToday];
}
