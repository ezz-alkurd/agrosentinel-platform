using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
namespace AgroSentinel.Desktop;
public sealed record DeviceConnection(string BaseUrl,string Token,Guid DeviceId);
public static class ConnectionStore {
 public const string DefaultBaseUrl="https://ezzeldeenalkurd-001-site2.ftempurl.com";
 public static string DirectoryPath=>Environment.GetEnvironmentVariable("AGROSENTINEL_APPDATA")??Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),"AgroSentinel");
 static string FilePath=>Path.Combine(DirectoryPath,"connection.bin");
 static readonly byte[] Entropy=Encoding.UTF8.GetBytes("AgroSentinel connection v1");
 public static DeviceConnection? Load(){try{return JsonSerializer.Deserialize<DeviceConnection>(ProtectedData.Unprotect(File.ReadAllBytes(FilePath),Entropy,DataProtectionScope.CurrentUser));}catch(Exception error) when(error is IOException or CryptographicException or JsonException){return null;}}
 public static void Save(DeviceConnection value){Directory.CreateDirectory(DirectoryPath);var data=ProtectedData.Protect(JsonSerializer.SerializeToUtf8Bytes(value),Entropy,DataProtectionScope.CurrentUser);var temporary=FilePath+".tmp";File.WriteAllBytes(temporary,data);File.Move(temporary,FilePath,true);}
 public static string ValidateUrl(string input){if(!Uri.TryCreate(input.Trim().TrimEnd('/'),UriKind.Absolute,out var uri)||!string.IsNullOrEmpty(uri.UserInfo)||!string.IsNullOrEmpty(uri.Query)||!string.IsNullOrEmpty(uri.Fragment)||(uri.Scheme!="https"&&!(uri.Scheme=="http"&&uri.IsLoopback)))throw new InvalidOperationException("Use the HTTPS website address without /api/v1. Loopback HTTP is supported for development.");return uri.AbsoluteUri.TrimEnd('/');}
}
