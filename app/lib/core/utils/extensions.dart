import 'event_time.dart';
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

extension ContextX on BuildContext {
  ThemeData get theme       => Theme.of(this);
  TextTheme  get textTheme  => Theme.of(this).textTheme;
  ColorScheme get colorScheme => Theme.of(this).colorScheme;
  bool   get isDark        => Theme.of(this).brightness == Brightness.dark;
  double get screenWidth   => MediaQuery.sizeOf(this).width;
  double get screenHeight  => MediaQuery.sizeOf(this).height;
}

extension DateTimeX on DateTime {
  String get formattedTime     => DateFormat('HH:mm').format(this);
  String get formattedDate     => DateFormat('MMM dd, yyyy').format(this);
  String get formattedDateTime => DateFormat('MMM dd • HH:mm').format(this);

  String timeAgo() {
    if (!hasEventTime(this)) return 'Time unavailable';
    final diff = DateTime.now().difference(this);
    if (diff.inMinutes < 1) return 'Just now';
    if (diff.inHours   < 1) return '${diff.inMinutes}m ago';
    if (diff.inDays    < 1) return '${diff.inHours}h ago';
    return '${diff.inDays}d ago';
  }
}

extension StringX on String {
  String get capitalized  => isEmpty ? this : '${this[0].toUpperCase()}${substring(1)}';
  bool get isValidEmail   => RegExp(r'^[\w\-.]+@([\w-]+\.)+[\w-]{2,4}$').hasMatch(this);
  bool get isValidPassword => length >= 8;
}
