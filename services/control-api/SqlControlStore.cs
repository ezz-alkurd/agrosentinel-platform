using System.Data;
using System.Text.Json;
using Microsoft.Data.SqlClient;
namespace AgroSentinel.ControlApi;
public sealed class SqlControlStore(ApiOptions options) : IControlStore {
 async Task<SqlConnection> Open(CancellationToken ct) {
  if(string.IsNullOrWhiteSpace(options.SqlConnection)) throw new ApiFault(503,"SQL Server connection is not configured.");
  var c=new SqlConnection(options.SqlConnection); try {await c.OpenAsync(ct);return c;} catch {await c.DisposeAsync();throw;}
 }
 static SqlCommand Cmd(SqlConnection c,string sql,params (string,object?)[] values) {
  var cmd=new SqlCommand(sql,c){CommandTimeout=15};foreach(var (key,value) in values) cmd.Parameters.AddWithValue(key,value??DBNull.Value);return cmd;
 }
 public async Task Ping(CancellationToken ct) {await using var c=await Open(ct);await using var cmd=Cmd(c,"SELECT Version FROM dbo.AgroSchemaVersion WHERE Version=1");if(await cmd.ExecuteScalarAsync(ct) is null)throw new ApiFault(503,"Database schema is not installed.");}
 public async Task CreatePair(PairingTicket t,string name,CancellationToken ct) {
  await using var c=await Open(ct);await using var cmd=Cmd(c,"DELETE FROM dbo.AgroPairings WHERE ExpiresAt<SYSUTCDATETIME(); INSERT dbo.AgroPairings(Id,CodeHash,TokenHash,Name,ExpiresAt) VALUES(@id,@code,@token,@name,@expires)",("@id",t.Id),("@code",Secrets.Hash(t.Code)),("@token",Secrets.Hash(t.PollToken)),("@name",name),("@expires",t.ExpiresAt));await cmd.ExecuteNonQueryAsync(ct);
 }
 public async Task<Guid> ClaimPair(string code,string owner,string? name,CancellationToken ct) {
  await using var c=await Open(ct);await using var tx=(SqlTransaction)await c.BeginTransactionAsync(IsolationLevel.Serializable,ct);
  await using var find=Cmd(c,"SELECT Id,TokenHash,Name FROM dbo.AgroPairings WITH (UPDLOCK,HOLDLOCK) WHERE CodeHash=@code AND DeviceId IS NULL AND ExpiresAt>SYSUTCDATETIME()",("@code",Secrets.Hash(code)));find.Transaction=tx;
  Guid pair;byte[] token;string deviceName;
  await using(var r=await find.ExecuteReaderAsync(ct)){if(!await r.ReadAsync(ct))throw new ApiFault(404,"Pairing code is invalid, expired or already claimed.");pair=r.GetGuid(0);token=(byte[])r[1];deviceName=name??r.GetString(2);}
  var id=Guid.NewGuid();await using var cmd=Cmd(c,"IF NOT EXISTS(SELECT 1 FROM dbo.AgroUsers WITH(UPDLOCK,HOLDLOCK) WHERE Uid=@owner) INSERT dbo.AgroUsers(Uid) VALUES(@owner); INSERT dbo.AgroDevices(Id,OwnerUid,Name,TokenHash) VALUES(@id,@owner,@name,@token); UPDATE dbo.AgroPairings SET DeviceId=@id WHERE Id=@pair;",("@owner",owner),("@id",id),("@name",deviceName),("@token",token),("@pair",pair));cmd.Transaction=tx;await cmd.ExecuteNonQueryAsync(ct);await tx.CommitAsync(ct);return id;
 }
 public async Task<PairingState?> PollPair(Guid id,string token,CancellationToken ct) {
  await using var c=await Open(ct);await using var cmd=Cmd(c,"SELECT DeviceId,ExpiresAt FROM dbo.AgroPairings WHERE Id=@id AND TokenHash=@token",("@id",id),("@token",Secrets.Hash(token)));await using var r=await cmd.ExecuteReaderAsync(ct);if(!await r.ReadAsync(ct))return null;var expires=r.GetFieldValue<DateTimeOffset>(1);return new(expires<DateTimeOffset.UtcNow?"expired":r.IsDBNull(0)?"pending":"paired",r.IsDBNull(0)?null:r.GetGuid(0),expires);
 }
 static DeviceRecord Device(SqlDataReader r)=>new(r.GetGuid(0),r.GetString(1),r.GetString(2),r.GetString(3),r.GetBoolean(4),r.IsDBNull(5)?null:r.GetFieldValue<DateTimeOffset>(5),r.IsDBNull(6)?null:r.GetString(6),JsonSerializer.Deserialize<string[]>(r.GetString(7))??[],r.GetBoolean(8));
 const string DeviceFields="Id,OwnerUid,Name,Type,Online,LastSeen,Source,Models,Revoked";
 public async Task<DeviceRecord?> AuthenticateDevice(string token,CancellationToken ct) {
  await using var c=await Open(ct);await using var cmd=Cmd(c,$"SELECT {DeviceFields} FROM dbo.AgroDevices WHERE TokenHash=@token AND Revoked=0",("@token",Secrets.Hash(token)));await using var r=await cmd.ExecuteReaderAsync(ct);return await r.ReadAsync(ct)?Device(r):null;
 }
 public async Task<IReadOnlyList<DeviceRecord>> Devices(string owner,CancellationToken ct) {
  await using var c=await Open(ct);await using var cmd=Cmd(c,$"SELECT {DeviceFields} FROM dbo.AgroDevices WHERE OwnerUid=@owner AND Revoked=0 ORDER BY CreatedAt DESC",("@owner",owner));await using var r=await cmd.ExecuteReaderAsync(ct);var rows=new List<DeviceRecord>();while(await r.ReadAsync(ct))rows.Add(Device(r));return rows;
 }
 public async Task Heartbeat(Guid id,DeviceHeartbeat h,CancellationToken ct) {
  await using var c=await Open(ct);await using var cmd=Cmd(c,"UPDATE dbo.AgroDevices SET Name=@name,Type=@type,Online=@online,LastSeen=SYSUTCDATETIME(),Source=@source,Models=@models WHERE Id=@id AND Revoked=0",("@name",h.Name),("@type",h.Type),("@online",h.Online),("@source",h.Source),("@models",JsonSerializer.Serialize(h.Models)),("@id",id));if(await cmd.ExecuteNonQueryAsync(ct)==0)throw new ApiFault(401,"Device has been revoked.");
 }
 public async Task<bool> RevokeDevice(Guid id,string owner,CancellationToken ct) {
  await using var c=await Open(ct);await using var cmd=Cmd(c,"UPDATE dbo.AgroDevices SET Revoked=1,Online=0 WHERE Id=@id AND OwnerUid=@owner AND Revoked=0",("@id",id),("@owner",owner));return await cmd.ExecuteNonQueryAsync(ct)>0;
 }
 const string EventFields="e.Id,e.DeviceId,d.OwnerUid,e.Metadata,e.ReceivedAt,e.EvidenceKey,e.ImageHash,e.PayloadHash";
 static StoredEvent ReadEvent(SqlDataReader r)=>new(r.GetGuid(0),r.GetGuid(1),r.GetString(2),JsonSerializer.Deserialize<EventUpload>(r.GetString(3),ApiJson.Options)!,r.GetFieldValue<DateTimeOffset>(4),r.GetString(5),r.GetString(6),r.GetString(7));
 public async Task<IReadOnlyList<StoredEvent>> Events(string owner,int limit,CancellationToken ct) {
  await using var c=await Open(ct);await using var cmd=Cmd(c,$"SELECT TOP(@limit) {EventFields} FROM dbo.AgroEvents e JOIN dbo.AgroDevices d ON d.Id=e.DeviceId WHERE d.OwnerUid=@owner AND e.DeletedAt IS NULL ORDER BY e.ReceivedAt DESC,e.Id DESC",("@owner",owner),("@limit",limit));await using var r=await cmd.ExecuteReaderAsync(ct);var rows=new List<StoredEvent>();while(await r.ReadAsync(ct))rows.Add(ReadEvent(r));return rows;
 }
 public async Task<StoredEvent?> Event(Guid id,CancellationToken ct) {
  await using var c=await Open(ct);await using var cmd=Cmd(c,$"SELECT {EventFields} FROM dbo.AgroEvents e JOIN dbo.AgroDevices d ON d.Id=e.DeviceId WHERE e.Id=@id AND e.DeletedAt IS NULL",("@id",id));await using var r=await cmd.ExecuteReaderAsync(ct);return await r.ReadAsync(ct)?ReadEvent(r):null;
 }
 public async Task<StoredEvent> SaveEvent(StoredEvent e,CancellationToken ct) {
  try {await using var c=await Open(ct);await using var cmd=Cmd(c,"INSERT dbo.AgroEvents(Id,DeviceId,AnomalyType,Confidence,CapturedAt,Metadata,EvidenceKey,ImageHash,PayloadHash) VALUES(@id,@device,@type,@conf,@capture,@meta,@key,@image,@payload)",("@id",e.Id),("@device",e.DeviceId),("@type",e.Data.AnomalyType),("@conf",e.Data.Confidence),("@capture",e.Data.CapturedAt),("@meta",JsonSerializer.Serialize(e.Data,ApiJson.Options)),("@key",e.EvidenceKey),("@image",e.ImageHash),("@payload",e.PayloadHash));await cmd.ExecuteNonQueryAsync(ct);}
  catch(SqlException ex) when(ex.Number is 2601 or 2627) {var existing=await Event(e.Id,ct);if(existing is null||existing.DeviceId!=e.DeviceId||existing.ImageHash!=e.ImageHash||existing.PayloadHash!=e.PayloadHash)throw new ApiFault(409,"Event ID already exists with different content.");return existing;}
  return (await Event(e.Id,ct))!;
 }
 public async Task<bool> DeleteEvent(Guid id,string owner,CancellationToken ct) {
  await using var c=await Open(ct);await using var cmd=Cmd(c,"UPDATE e SET DeletedAt=SYSUTCDATETIME() FROM dbo.AgroEvents e JOIN dbo.AgroDevices d ON d.Id=e.DeviceId WHERE e.Id=@id AND d.OwnerUid=@owner AND e.DeletedAt IS NULL",("@id",id),("@owner",owner));return await cmd.ExecuteNonQueryAsync(ct)>0;
 }
}
