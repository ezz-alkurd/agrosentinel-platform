import 'package:intl/intl.dart';

DateTime parseEventTime(Object? value) {
  if (value is DateTime) return value;
  if (value is String) return DateTime.tryParse(value) ?? DateTime.utc(1970);
  return DateTime.utc(1970);
}
bool hasEventTime(DateTime time) => time.millisecondsSinceEpoch > 0;
String displayEventTime(DateTime time, {String pattern = 'd MMM yyyy · HH:mm'}) =>
    hasEventTime(time) ? DateFormat(pattern).format(time.toLocal()) : 'Time unavailable';
