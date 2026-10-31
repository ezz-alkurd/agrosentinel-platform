import '../../domain/entities/user_entity.dart';

class UserModel extends UserEntity {
  const UserModel({
    required super.id,
    required super.name,
    required super.email,
    super.avatarUrl,
    super.farmName,
    super.totalScans,
    super.alertsToday,
  });

  factory UserModel.fromJson(Map<String, dynamic> json) => UserModel(
        id: json['id'] as String,
        name: json['name'] as String,
        email: json['email'] as String,
        avatarUrl: json['avatarUrl'] as String?,
        farmName: json['farmName'] as String? ?? '',
        totalScans: json['totalScans'] as int? ?? 0,
        alertsToday: json['alertsToday'] as int? ?? 0,
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'name': name,
        'email': email,
        'avatarUrl': avatarUrl,
        'farmName': farmName,
        'totalScans': totalScans,
        'alertsToday': alertsToday,
      };

}
