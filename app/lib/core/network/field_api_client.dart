import 'dart:async';
import 'package:dio/dio.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

class FieldApiClient {
  static const defaultBaseUrl = String.fromEnvironment(
    'AGROSENTINEL_API_URL',
    defaultValue: 'https://ezzeldeenalkurd-001-site2.ftempurl.com',
  );
  final SharedPreferences preferences;
  final FirebaseAuth? auth;
  final Dio _http;
  FieldApiClient(this.preferences, this.auth, {Dio? http})
      : _http = http ?? Dio(BaseOptions(connectTimeout: const Duration(seconds: 8), receiveTimeout: const Duration(seconds: 15)));
  String get baseUrl {
    final saved = preferences.getString('field_api_url')?.trim();
    return saved == null || saved.isEmpty ? defaultBaseUrl : saved;
  }
  Future<void> setBaseUrl(String value) async {
    final uri = Uri.tryParse(value.trim());
    final local = uri != null && kDebugMode && ['localhost', '127.0.0.1', '10.0.2.2'].contains(uri.host);
    if (uri == null || !uri.hasAuthority || uri.userInfo.isNotEmpty || uri.hasQuery || uri.hasFragment || !(uri.scheme == 'https' || local && uri.scheme == 'http')) {
      throw StateError('Enter the HTTPS website address.');
    }
    await preferences.setString('field_api_url', value.trim().replaceAll(RegExp(r'/+$'), ''));
  }
  Future<Response<dynamic>> request(String method, String route, {Object? data, bool authenticated = true, bool retry = true}) async {
    if (baseUrl.isEmpty) throw StateError('Set your website address in Settings → Server & paired devices.');
    final target = Uri.tryParse(baseUrl);
    final local = target != null && kDebugMode && ['localhost', '127.0.0.1', '10.0.2.2'].contains(target.host);
    if (target == null || !target.hasAuthority || target.userInfo.isNotEmpty || target.hasQuery || target.hasFragment || !(target.scheme == 'https' || local && target.scheme == 'http')) throw StateError('Configure a valid HTTPS website address.');
    String? token;
    if (authenticated) {
      final user = auth?.currentUser;
      if (user == null) throw StateError('Sign in to view camera events.');
      token = await user.getIdToken();
    }
    try {
      return await _http.request<dynamic>('$baseUrl/api/v1$route', data: data, options: Options(method: method, headers: token == null ? null : {'Authorization': 'Bearer $token'}));
    } on DioException catch (error) {
      if (authenticated && retry && error.response?.statusCode == 401) {
        await auth?.currentUser?.getIdToken(true);
        return request(method, route, data: data, retry: false);
      }
      final body = error.response?.data;
      throw StateError(body is Map && body['error'] is String ? body['error'] as String : 'Could not reach the AgroSentinel server. Check its address and your connection.');
    }
  }
  Future<List<Map<String, dynamic>>> _list(String route) async {
    final response = await request('GET', route);
    return (response.data as List).map((item) => Map<String, dynamic>.from(item as Map)).toList();
  }
  Future<List<Map<String, dynamic>>> events() => _list('/events?limit=100');
  Future<List<Map<String, dynamic>>> devices() => _list('/devices');
  Future<void> health() async { await request('GET', '/health', authenticated: false); }
  Future<void> claim(String code, String name) async { await request('POST', '/pairing/claim', data: {'code': code, 'name': name}); }
  Future<void> revoke(String id) async { await request('DELETE', '/devices/$id'); }
  Future<void> deleteEvent(String id) async { await request('DELETE', '/events/$id'); }
  Stream<List<Map<String, dynamic>>> _watch(Future<List<Map<String, dynamic>>> Function() fetch) {
    late StreamController<List<Map<String, dynamic>>> controller;
    var active = true;
    Future<void> poll() async {
      while (active) {
        try { final rows = await fetch(); if (active) controller.add(rows); }
        catch (error, stack) { if (active) controller.addError(error, stack); }
        if (active) await Future<void>.delayed(const Duration(seconds: 5));
      }
    }
    controller = StreamController<List<Map<String, dynamic>>>(onListen: poll, onCancel: () { active = false; });
    return controller.stream;
  }
  Stream<List<Map<String, dynamic>>> watchEvents() => _watch(events);
  Stream<List<Map<String, dynamic>>> watchDevices() => _watch(devices);
}
