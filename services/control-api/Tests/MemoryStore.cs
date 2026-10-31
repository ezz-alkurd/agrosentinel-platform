using AgroSentinel.ControlApi;
namespace AgroSentinel.ApiChecks;
// Test-only implementation. Production always registers SqlControlStore.
sealed class MemoryStore : IControlStore {
 readonly Dictionary<Guid,(PairingTicket Ticket,string Name,Guid? Device)> pairs=[];
 readonly Dictionary<Guid,(DeviceRecord Record,string Token)> devices=[];
 readonly Dictionary<Guid,StoredEvent> events=[];readonly HashSet<Guid> deleted=[];
 public Task Ping(CancellationToken ct)=>Task.CompletedTask;
 public Task CreatePair(PairingTicket t,string name,CancellationToken ct){pairs.Add(t.Id,(t,name,null));return Task.CompletedTask;}
 public Task<Guid> ClaimPair(string code,string owner,string? name,CancellationToken ct){var pair=pairs.FirstOrDefault(p=>p.Value.Ticket.Code==code&&p.Value.Device is null&&p.Value.Ticket.ExpiresAt>DateTimeOffset.UtcNow);if(pair.Key==Guid.Empty)throw new ApiFault(404,"Pairing code unavailable.");var id=Guid.NewGuid();var data=pair.Value;devices.Add(id,(new(id,owner,name??data.Name,"Laptop camera",false,null,null,[],false),data.Ticket.PollToken));pairs[pair.Key]=(data.Ticket,data.Name,id);return Task.FromResult(id);}
 public Task<PairingState?> PollPair(Guid id,string token,CancellationToken ct){if(!pairs.TryGetValue(id,out var p)||p.Ticket.PollToken!=token)return Task.FromResult<PairingState?>(null);return Task.FromResult<PairingState?>(new(p.Device is null?"pending":"paired",p.Device,p.Ticket.ExpiresAt));}
 public Task<DeviceRecord?> AuthenticateDevice(string token,CancellationToken ct)=>Task.FromResult(devices.Values.Where(d=>d.Token==token&&!d.Record.Revoked).Select(d=>d.Record).FirstOrDefault());
 public Task<IReadOnlyList<DeviceRecord>> Devices(string owner,CancellationToken ct)=>Task.FromResult<IReadOnlyList<DeviceRecord>>(devices.Values.Where(d=>d.Record.OwnerUid==owner&&!d.Record.Revoked).Select(d=>d.Record).ToArray());
 public Task Heartbeat(Guid id,DeviceHeartbeat h,CancellationToken ct){var d=devices[id];devices[id]=(d.Record with{Name=h.Name,Type=h.Type,Source=h.Source,Online=h.Online,LastSeen=DateTimeOffset.UtcNow,Models=h.Models},d.Token);return Task.CompletedTask;}
 public Task<bool> RevokeDevice(Guid id,string owner,CancellationToken ct){if(!devices.TryGetValue(id,out var d)||d.Record.OwnerUid!=owner)return Task.FromResult(false);devices[id]=(d.Record with{Revoked=true},d.Token);return Task.FromResult(true);}
 public Task<IReadOnlyList<StoredEvent>> Events(string owner,int limit,CancellationToken ct)=>Task.FromResult<IReadOnlyList<StoredEvent>>(events.Values.Where(e=>e.OwnerUid==owner&&!deleted.Contains(e.Id)).Take(limit).ToArray());
 public Task<StoredEvent?> Event(Guid id,CancellationToken ct)=>Task.FromResult(!deleted.Contains(id)&&events.TryGetValue(id,out var e)?e:null);
 public Task<StoredEvent> SaveEvent(StoredEvent item,CancellationToken ct){if(events.TryGetValue(item.Id,out var old)){if(deleted.Contains(item.Id)||old.DeviceId!=item.DeviceId||old.ImageHash!=item.ImageHash||old.PayloadHash!=item.PayloadHash)throw new ApiFault(409,"Conflicting event identity.");return Task.FromResult(old);}events.Add(item.Id,item);return Task.FromResult(item);}
 public Task<bool> DeleteEvent(Guid id,string owner,CancellationToken ct){if(!events.TryGetValue(id,out var e)||e.OwnerUid!=owner)return Task.FromResult(false);deleted.Add(id);return Task.FromResult(true);}
}
