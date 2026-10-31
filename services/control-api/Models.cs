using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
namespace AgroSentinel.ControlApi;
public sealed class ApiOptions {
 public string? SqlConnection {get;set;}
 public string FirebaseProjectId {get;set;} = "agriculture-drone-e0dc0";
 public string PublicBaseUrl {get;set;} = "";
 public string MediaSigningKey {get;set;} = "";
 public string EvidenceDirectory {get;set;} = "App_Data/evidence";
 public long MaxEvidenceStorageBytes {get;set;} = 1_073_741_824;
}
public sealed record PairingRequest(string? Name);
public sealed record PairingClaim(string Code, string? Name);
public sealed record PairingTicket(Guid Id, string Code, string PollToken, DateTimeOffset ExpiresAt);
public sealed record PairingState(string Status, Guid? DeviceId, DateTimeOffset ExpiresAt);
public sealed record DeviceRecord(Guid Id, string OwnerUid, string Name, string Type, bool Online, DateTimeOffset? LastSeen, string? Source, string[] Models, bool Revoked);
public sealed record DeviceHeartbeat(string Name, string Type, string? Source, bool Online, string[] Models);
public sealed record EventUpload(Guid Id, string AnomalyType, double Confidence, double? GpsLat, double? GpsLng, DateTimeOffset CapturedAt, string? DiseaseName, string SourceType, string LocationSource, string ConfirmationMode, string? FireModelSha256, string? PlantModelSha256, string? PlantInferenceKind);
public sealed record StoredEvent(Guid Id, Guid DeviceId, string OwnerUid, EventUpload Data, DateTimeOffset Timestamp, string EvidenceKey, string ImageHash, string PayloadHash);
public sealed record EventResponse(Guid Id, Guid DeviceId, string AnomalyType, double Confidence, double? GpsLat, double? GpsLng, DateTimeOffset Timestamp, DateTimeOffset CapturedAt, string? DiseaseName, string SourceType, string LocationSource, string ConfirmationMode, string Status, string ImageUrl, string StoragePath);
public sealed class ApiFault(int status, string message) : Exception(message) { public int Status {get;} = status; }
public static class ApiJson {public static readonly JsonSerializerOptions Options = new(JsonSerializerDefaults.Web){PropertyNamingPolicy=JsonNamingPolicy.SnakeCaseLower};}
public static class Secrets {
 public static string Token() => Convert.ToBase64String(RandomNumberGenerator.GetBytes(32)).TrimEnd('=').Replace('+','-').Replace('/','_');
 public static byte[] Hash(string value) => SHA256.HashData(Encoding.UTF8.GetBytes(value));
 public static string Hex(byte[] value) => Convert.ToHexString(value).ToLowerInvariant();
 public static bool Equal(byte[] a, byte[] b) => CryptographicOperations.FixedTimeEquals(a,b);
}
public interface IControlStore {
 Task Ping(CancellationToken ct);
 Task CreatePair(PairingTicket ticket, string name, CancellationToken ct);
 Task<Guid> ClaimPair(string code, string owner, string? name, CancellationToken ct);
 Task<PairingState?> PollPair(Guid id, string token, CancellationToken ct);
 Task<DeviceRecord?> AuthenticateDevice(string token, CancellationToken ct);
 Task<IReadOnlyList<DeviceRecord>> Devices(string owner, CancellationToken ct);
 Task Heartbeat(Guid id, DeviceHeartbeat heartbeat, CancellationToken ct);
 Task<bool> RevokeDevice(Guid id, string owner, CancellationToken ct);
 Task<IReadOnlyList<StoredEvent>> Events(string owner, int limit, CancellationToken ct);
 Task<StoredEvent?> Event(Guid id, CancellationToken ct);
 Task<StoredEvent> SaveEvent(StoredEvent item, CancellationToken ct);
 Task<bool> DeleteEvent(Guid id, string owner, CancellationToken ct);
}
