import 'dart:typed_data';
import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:agri_drone_ai/core/network/field_api_client.dart';
class Adapter implements HttpClientAdapter {
 RequestOptions? last;
 @override
 Future<ResponseBody> fetch(RequestOptions options, Stream<Uint8List>? requestStream, Future<void>? cancelFuture) async {
  last = options;
  return ResponseBody.fromString('{"status":"ok"}', 200, headers: {Headers.contentTypeHeader: [Headers.jsonContentType]});
 }
 @override
 void close({bool force = false}) {}
}
void main() {
 TestWidgetsFlutterBinding.ensureInitialized();
 test('fresh installs and blank saved settings use the hosted server without setup', () async {
  for (final values in <Map<String, Object>>[{}, {'field_api_url': ''}]) {
   SharedPreferences.setMockInitialValues(values);
   final adapter = Adapter(); final dio = Dio()..httpClientAdapter = adapter;
   final client = FieldApiClient(await SharedPreferences.getInstance(), null, http: dio);
   await client.health();
   expect(client.baseUrl, 'https://ezzeldeenalkurd-001-site2.ftempurl.com');
   expect(adapter.last!.uri.toString(), '${FieldApiClient.defaultBaseUrl}/api/v1/health');
   expect(adapter.last!.headers['Authorization'], isNull);
  }
 });
 test('configuration persists a website root and health targets its API', () async {
  SharedPreferences.setMockInitialValues({});
  final adapter = Adapter(); final dio = Dio()..httpClientAdapter = adapter;
  final client = FieldApiClient(await SharedPreferences.getInstance(), null, http: dio);
  await client.setBaseUrl('https://example.invalid/');
  await client.health();
  expect(adapter.last!.uri.toString(), 'https://example.invalid/api/v1/health');
  expect(adapter.last!.headers['Authorization'], isNull);
  expect(client.baseUrl, 'https://example.invalid');
 });
 test('remote HTTP and credential-bearing addresses are rejected', () async {
  SharedPreferences.setMockInitialValues({});
  final client = FieldApiClient(await SharedPreferences.getInstance(), null);
  for (final address in ['http://example.invalid', 'https://user:password@example.invalid', 'https://example.invalid?token=secret']) {
   await expectLater(client.setBaseUrl(address), throwsStateError);
  }
 });
 test('camera requests require sign-in and never invent events', () async {
  SharedPreferences.setMockInitialValues({'field_api_url':'https://example.invalid'});
  final client = FieldApiClient(await SharedPreferences.getInstance(), null);
  await expectLater(client.events(), throwsStateError);
 });
}
