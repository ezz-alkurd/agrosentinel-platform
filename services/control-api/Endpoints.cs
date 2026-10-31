using System.Security.Claims;
using System.Security.Cryptography;
using System.Text.Json;
using System.Threading.RateLimiting;
using Microsoft.AspNetCore.Authentication;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Http.Features;
using Microsoft.AspNetCore.RateLimiting;
using Microsoft.Data.SqlClient;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.DependencyInjection.Extensions;
using Microsoft.Extensions.Logging;
namespace AgroSentinel.ControlApi;
public static class ControlApiExtensions {
 public static IServiceCollection AddAgroSentinelApi(this IServiceCollection services,IConfiguration config){
  var options=new ApiOptions();config.GetSection("AgroSentinel").Bind(options);options.SqlConnection=config.GetConnectionString("AgroSentinel")??options.SqlConnection;
  services.AddSingleton(options);services.TryAddSingleton<IControlStore,SqlControlStore>();services.AddSingleton<EvidenceStore>();
  services.AddHttpClient<IFirebaseTokenValidator,FirebaseTokenValidator>(c=>c.Timeout=TimeSpan.FromSeconds(10));
  services.AddAuthentication("Agro").AddScheme<AuthenticationSchemeOptions,ApiAuthenticationHandler>("Agro",_=>{});
  services.AddAuthorization(o=>{o.AddPolicy("User",p=>p.RequireAuthenticatedUser().RequireClaim("actor_kind","user"));o.AddPolicy("Device",p=>p.RequireAuthenticatedUser().RequireClaim("actor_kind","device"));});
  services.ConfigureHttpJsonOptions(o=>o.SerializerOptions.PropertyNamingPolicy=JsonNamingPolicy.SnakeCaseLower);
  services.Configure<FormOptions>(o=>{o.MultipartBodyLengthLimit=10*1024*1024;o.ValueLengthLimit=16384;o.MultipartHeadersLengthLimit=8192;});
  services.AddRateLimiter(o=>{o.RejectionStatusCode=429;o.AddPolicy("pair",context=>RateLimitPartition.GetFixedWindowLimiter(context.User.FindFirstValue("sub")??context.Connection.RemoteIpAddress?.ToString()??"unknown",_=>new(){PermitLimit=20,Window=TimeSpan.FromMinutes(1),QueueLimit=0}));o.AddPolicy("pair_poll",context=>RateLimitPartition.GetFixedWindowLimiter(context.Connection.RemoteIpAddress?.ToString()??"unknown",_=>new(){PermitLimit=120,Window=TimeSpan.FromMinutes(1),QueueLimit=0}));o.AddConcurrencyLimiter("ingest",x=>{x.PermitLimit=4;x.QueueLimit=0;});});
  return services;
 }
 static string Owner(HttpContext context)=>context.User.FindFirstValue("sub")!;
 static Guid Device(HttpContext context)=>Guid.Parse(context.User.FindFirstValue("device_id")!);
 static string Name(string? value,string fallback,int max=120){value=(value??fallback).Trim();if(value.Length is 0||value.Length>max)throw new ApiFault(400,"Name has an invalid length.");return value;}
 static EventResponse Response(StoredEvent e,EvidenceStore media)=>new(e.Id,e.DeviceId,e.Data.AnomalyType,e.Data.Confidence,e.Data.GpsLat,e.Data.GpsLng,e.Timestamp,e.Data.CapturedAt,e.Data.DiseaseName,e.Data.SourceType,e.Data.LocationSource,e.Data.ConfirmationMode,"new",media.Url(e),$"api/events/{e.Id}/image");
 static void Validate(EventUpload d){
  if(d.Id==Guid.Empty||d.AnomalyType is not("fire" or "smoke" or "disease")||!double.IsFinite(d.Confidence)||d.Confidence is <0 or >1)throw new ApiFault(400,"Invalid detection metadata.");
  if(d.CapturedAt.Year<2020||d.CapturedAt>DateTimeOffset.UtcNow.AddMinutes(5))throw new ApiFault(400,"Capture time is invalid.");
  if(d.GpsLat.HasValue&&(!double.IsFinite(d.GpsLat.Value)||d.GpsLat is < -90 or >90)||d.GpsLng.HasValue&&(!double.IsFinite(d.GpsLng.Value)||d.GpsLng is < -180 or >180))throw new ApiFault(400,"Coordinates are invalid.");
  if(d.AnomalyType=="disease"&&(string.IsNullOrWhiteSpace(d.DiseaseName)||d.DiseaseName.Length>120))throw new ApiFault(400,"Disease label is required.");
  if(d.SourceType?.Length is null or >80||d.LocationSource?.Length is null or >40||d.ConfirmationMode is not("single_image" or "continuous_2_seconds"))throw new ApiFault(400,"Source provenance is invalid.");
  foreach(var hash in new[]{d.FireModelSha256,d.PlantModelSha256})if(hash is not null&&(hash.Length!=64||!hash.All(Uri.IsHexDigit)))throw new ApiFault(400,"Model checksum is invalid.");
  if(d.PlantInferenceKind?.Length>60)throw new ApiFault(400,"Plant inference kind is too long.");
 }
 public static WebApplication MapAgroSentinelApi(this WebApplication app){
  app.Use(async(context,next)=>{
   if(!context.Request.Path.StartsWithSegments("/api/v1")){await next();return;}
   context.Response.Headers["X-Content-Type-Options"]="nosniff";
   var configuration=context.RequestServices.GetRequiredService<ApiOptions>();
   if(!context.Request.Path.Equals("/api/v1/health")&&(string.IsNullOrWhiteSpace(configuration.SqlConnection)||configuration.MediaSigningKey.Length<32||!Uri.TryCreate(configuration.PublicBaseUrl,UriKind.Absolute,out var configuredUri)||(configuredUri.Scheme!="https"&&!configuredUri.IsLoopback))){context.Response.StatusCode=503;await context.Response.WriteAsJsonAsync(new{error="API hosting configuration is incomplete."});return;}
   try{await next();}
   catch(ApiFault ex){context.Response.StatusCode=ex.Status;await context.Response.WriteAsJsonAsync(new{error=ex.Message},context.RequestAborted);}
   catch(SqlException ex){
    app.Logger.LogError(ex,"API SQL Server dependency unavailable ({TraceId})",context.TraceIdentifier);
    var code=ex.Number switch{18456=>"sql_login_failed",4060=>"sql_database_unavailable",208=>"sql_schema_missing",229=>"sql_permission_denied",-2=>"sql_timeout",_=>"sql_connection_failed"};
    context.Response.StatusCode=503;
    await context.Response.WriteAsJsonAsync(new{error=code,sql_error_number=ex.Number,trace_id=context.TraceIdentifier},context.RequestAborted);
   }
   catch(Exception ex) when(ex is IOException or HttpRequestException){app.Logger.LogError(ex,"API dependency unavailable ({TraceId})",context.TraceIdentifier);context.Response.StatusCode=503;await context.Response.WriteAsJsonAsync(new{error="A backend dependency is unavailable. Check server configuration.",trace_id=context.TraceIdentifier},context.RequestAborted);}
   catch(Exception ex) when(ex is JsonException or InvalidDataException or BadHttpRequestException){context.Response.StatusCode=400;await context.Response.WriteAsJsonAsync(new{error="Invalid request body."},context.RequestAborted);}
   catch(Exception ex) when(!context.Response.HasStarted){
    app.Logger.LogError(ex,"Unhandled API failure ({TraceId})",context.TraceIdentifier);
    context.Response.StatusCode=500;
    await context.Response.WriteAsJsonAsync(new{error="api_internal_error",trace_id=context.TraceIdentifier},context.RequestAborted);
   }
  });
  app.UseAuthentication();app.UseAuthorization();app.UseRateLimiter();
  var api=app.MapGroup("/api/v1");
  api.MapGet("/health",async(IControlStore store,ApiOptions options,CancellationToken ct)=>{
   if(options.MediaSigningKey.Length<32||!Uri.TryCreate(options.PublicBaseUrl,UriKind.Absolute,out var uri)||uri.Scheme!="https"&&!uri.IsLoopback)return Results.Json(new{status="not_configured",error="Configure SQL Server, PublicBaseUrl and a random MediaSigningKey of at least 32 characters."},statusCode:503);
   await store.Ping(ct);return Results.Ok(new{status="ok",storage="sql_server",service="AgroSentinel API"});
  });
  api.MapGet("/me",(HttpContext c)=>Results.Ok(new{uid=Owner(c)})).RequireAuthorization("User");
  api.MapPost("/pairing/request",async(PairingRequest body,IControlStore store,CancellationToken ct)=>{
   const string alphabet="ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
   var ticket=new PairingTicket(Guid.NewGuid(),new string(Enumerable.Range(0,8).Select(_=>alphabet[RandomNumberGenerator.GetInt32(alphabet.Length)]).ToArray()),Secrets.Token(),DateTimeOffset.UtcNow.AddMinutes(10));
   await store.CreatePair(ticket,Name(body.Name,"AgroSentinel laptop"),ct);return Results.Ok(ticket);
  }).RequireRateLimiting("pair");
  api.MapGet("/pairing/{id:guid}",async(Guid id,HttpContext c,IControlStore store,CancellationToken ct)=>{
   var token=c.Request.Headers["X-Pairing-Token"].ToString();if(token.Length is <32 or >128)return Results.Unauthorized();var state=await store.PollPair(id,token,ct);return state is null?Results.NotFound():Results.Ok(state);
  }).RequireRateLimiting("pair_poll");
  api.MapPost("/pairing/claim",async(PairingClaim body,HttpContext c,IControlStore store,CancellationToken ct)=>{
   var code=(body.Code??"").Replace("-","").Replace(" ","").ToUpperInvariant();if(code.Length!=8)throw new ApiFault(400,"Enter the eight-character pairing code.");
   var id=await store.ClaimPair(code,Owner(c),body.Name is null?null:Name(body.Name,"Laptop"),ct);return Results.Ok(new{device_id=id});
  }).RequireAuthorization("User").RequireRateLimiting("pair");
  api.MapGet("/devices",async(HttpContext c,IControlStore store,CancellationToken ct)=>Results.Ok(await store.Devices(Owner(c),ct))).RequireAuthorization("User");
  api.MapDelete("/devices/{id:guid}",async(Guid id,HttpContext c,IControlStore store,CancellationToken ct)=>await store.RevokeDevice(id,Owner(c),ct)?Results.NoContent():Results.NotFound()).RequireAuthorization("User");
  api.MapGet("/agent",(HttpContext c)=>Results.Ok(new{device_id=Device(c)})).RequireAuthorization("Device");
  api.MapPost("/agent/heartbeat",async(DeviceHeartbeat h,HttpContext c,IControlStore store,CancellationToken ct)=>{
   var type=Name(h.Type,"Laptop camera",80);string? source=h.Source;
   if(source?.Length>2000)throw new ApiFault(400,"Source is too long.");
   if(Uri.TryCreate(source,UriKind.Absolute,out var uri)&&uri.Scheme is "rtsp" or "rtsps" or "http" or "https" or "rtmp")source=uri.Scheme+"://"+uri.Host+(uri.IsDefaultPort?"":":"+uri.Port);
   if(source?.Length>200)source=Path.GetFileName(source);if(source?.Length>200)source=source[..200];
   if(h.Models is null||h.Models.Length>10||h.Models.Any(m=>m is null||m.Length>40))throw new ApiFault(400,"Invalid active-model list.");
   await store.Heartbeat(Device(c),h with{Name=Name(h.Name,"Laptop"),Type=type,Source=source},ct);return Results.NoContent();
  }).RequireAuthorization("Device");
  api.MapGet("/events",async(int? limit,HttpContext c,IControlStore store,EvidenceStore media,CancellationToken ct)=>Results.Ok((await store.Events(Owner(c),Math.Clamp(limit??50,1,100),ct)).Select(e=>Response(e,media)))).RequireAuthorization("User");
  api.MapPost("/events",async(HttpRequest request,HttpContext context,IControlStore store,EvidenceStore media,ApiOptions options,CancellationToken ct)=>{
   if(options.MediaSigningKey.Length<32)throw new ApiFault(503,"Evidence signing key is not configured.");
   if(!request.HasFormContentType)throw new ApiFault(400,"Use multipart form fields metadata and image.");var form=await request.ReadFormAsync(ct);
   var text=form["metadata"].ToString();if(text.Length is 0 or >16384)throw new ApiFault(400,"Detection metadata is missing or too large.");
   var data=JsonSerializer.Deserialize<EventUpload>(text,ApiJson.Options)??throw new ApiFault(400,"Metadata is invalid.");Validate(data);
   var file=form.Files.GetFile("image")??throw new ApiFault(400,"Evidence image is required.");
   var device=Device(context);var saved=await media.Save(device,data.Id,file,ct);
   var payload=Secrets.Hex(SHA256.HashData(JsonSerializer.SerializeToUtf8Bytes(data,ApiJson.Options)));
   var item=await store.SaveEvent(new(data.Id,device,Owner(context),data,DateTimeOffset.UtcNow,saved.Key,saved.Hash,payload),ct);return Results.Ok(Response(item,media));
  }).RequireAuthorization("Device").RequireRateLimiting("ingest").DisableAntiforgery();
  api.MapDelete("/events/{id:guid}",async(Guid id,HttpContext c,IControlStore store,CancellationToken ct)=>await store.DeleteEvent(id,Owner(c),ct)?Results.NoContent():Results.NotFound()).RequireAuthorization("User");
  api.MapGet("/events/{id:guid}/image",async(Guid id,long? expires,string? signature,HttpContext c,IControlStore store,EvidenceStore media,CancellationToken ct)=>{
   var item=await store.Event(id,ct);if(item is null)return Results.NotFound();
   var owner=c.User.FindFirstValue("actor_kind")=="user"&&Owner(c)==item.OwnerUid;
   if(!owner&&(!expires.HasValue||signature is null||!media.Verify(item,expires.Value,signature)))return Results.Unauthorized();
   var file=media.Resolve(item.EvidenceKey);if(!File.Exists(file))return Results.NotFound();c.Response.Headers.CacheControl="private, max-age=300";return Results.File(file,"image/jpeg",enableRangeProcessing:true);
  });return app;
 }
}
