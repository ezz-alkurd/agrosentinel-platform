import '../models/notification_model.dart';
abstract class NotificationDataSource {
  Future<List<NotificationModel>> getNotifications();
  Stream<List<NotificationModel>> get liveStream;
}
