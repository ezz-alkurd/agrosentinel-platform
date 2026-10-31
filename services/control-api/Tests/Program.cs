using System.IdentityModel.Tokens.Jwt;
using System.Net;
using System.Net.Http.Headers;
using System.Net.Http.Json;
using System.Security.Claims;
using System.Security.Cryptography;
using System.Security.Cryptography.X509Certificates;
using System.Text;
using System.Text.Json;
using AgroSentinel.ControlApi;
using AgroSentinel.ApiChecks;
using Microsoft.AspNetCore.Hosting.Server;
using Microsoft.AspNetCore.Hosting.Server.Features;
using Microsoft.IdentityModel.Tokens;

var checks=0;
void Assert(bool passed,string label){if(!passed)throw new Exception("FAIL: "+label);checks++;Console.WriteLine("PASS: "+label);}
using var rsa=RSA.Create(2048);
var certificate=new CertificateRequest("CN=Offline test certificate",rsa,HashAlgorithmName.SHA256,RSASignaturePadding.Pkcs1).CreateSelfSigned(DateTimeOffset.UtcNow.AddDays(-1),DateTimeOffset.UtcNow.AddDays(1));
const string kid="offline-test-key";
var key=new RsaSecurityKey(rsa){KeyId=kid};
string Token(string uid,string? audience=null,bool expired=false)=>new JwtSecurityTokenHandler().WriteToken(new JwtSecurityToken(issuer:"https://securetoken.google.com/agriculture-drone-e0dc0",audience:audience??"agriculture-drone-e0dc0",claims:[new Claim("sub",uid),new Claim("iat",DateTimeOffset.UtcNow.AddMinutes(-10).ToUnixTimeSeconds().ToString(),ClaimValueTypes.Integer64),new Claim("auth_time",DateTimeOffset.UtcNow.AddMinutes(-10).ToUnixTimeSeconds().ToString(),ClaimValueTypes.Integer64)],notBefore:DateTime.UtcNow.AddHours(-1),expires:expired?DateTime.UtcNow.AddMinutes(-5):DateTime.UtcNow.AddMinutes(30),signingCredentials:new(key,SecurityAlgorithms.RsaSha256)));
var root=Path.GetFullPath("runtime/api-checks-"+Guid.NewGuid().ToString("N"));
var builder=WebApplication.CreateBuilder();builder.Logging.ClearProviders();builder.WebHost.UseUrls("http://127.0.0.1:0");
builder.Configuration.AddInMemoryCollection(new Dictionary<string,string?>{{"ConnectionStrings:AgroSentinel","Test store only"},{"AgroSentinel:PublicBaseUrl","http://127.0.0.1:1"},{"AgroSentinel:MediaSigningKey",Secrets.Token()},{"AgroSentinel:EvidenceDirectory",root}});
builder.Services.AddAgroSentinelApi(builder.Configuration);builder.Services.AddSingleton<IControlStore,MemoryStore>();
builder.Services.AddSingleton<IFirebaseTokenValidator>(provider=>new FirebaseTokenValidator(new HttpClient(new CertificateHandler(JsonSerializer.Serialize(new Dictionary<string,string>{{kid,certificate.ExportCertificatePem()}}))),provider.GetRequiredService<ApiOptions>()));
await using var app=builder.Build();app.MapAgroSentinelApi();await app.StartAsync();var address=app.Services.GetRequiredService<IServer>().Features.Get<IServerAddressesFeature>()!.Addresses.Single();app.Services.GetRequiredService<ApiOptions>().PublicBaseUrl=address;
using var client=new HttpClient{BaseAddress=new Uri(address),Timeout=TimeSpan.FromSeconds(10)};
async Task<HttpResponseMessage> Request(HttpMethod method,string route,string? auth=null,object? json=null){var request=new HttpRequestMessage(method,route);if(auth is not null)request.Headers.Authorization=AuthenticationHeaderValue.Parse(auth);if(json is not null)request.Content=JsonContent.Create(json,options:ApiJson.Options);return await client.SendAsync(request);}
try{
 Assert((await client.GetAsync("/api/v1/health")).IsSuccessStatusCode,"configured API health");
 Assert((await client.GetAsync("/api/v1/events")).StatusCode==HttpStatusCode.Unauthorized,"anonymous event listing denied");
 Assert((await Request(HttpMethod.Get,"/api/v1/me","Bearer "+Token("alice","wrong-project"))).StatusCode==HttpStatusCode.Unauthorized,"wrong audience rejected with real RSA verification");
 Assert((await Request(HttpMethod.Get,"/api/v1/me","Bearer "+Token("alice",expired:true))).StatusCode==HttpStatusCode.Unauthorized,"expired token rejected");
 var alice="Bearer "+Token("alice");var bob="Bearer "+Token("bob");
 using var ticketResponse=await Request(HttpMethod.Post,"/api/v1/pairing/request",json:new PairingRequest("Test laptop"));ticketResponse.EnsureSuccessStatusCode();var ticket=await ticketResponse.Content.ReadFromJsonAsync<PairingTicket>(ApiJson.Options);Assert(ticket is not null,"pairing ticket created");
 using var claim=await Request(HttpMethod.Post,"/api/v1/pairing/claim",alice,new PairingClaim(ticket!.Code,"Owned laptop"));claim.EnsureSuccessStatusCode();var claimJson=await claim.Content.ReadFromJsonAsync<JsonElement>();var deviceId=claimJson.GetProperty("device_id").GetGuid();var device="Device "+ticket.PollToken;
 Assert((await Request(HttpMethod.Post,"/api/v1/pairing/claim",bob,new PairingClaim(ticket.Code,null))).StatusCode==HttpStatusCode.NotFound,"pairing code is single use");
 Assert((await Request(HttpMethod.Get,"/api/v1/events",device)).StatusCode==HttpStatusCode.Forbidden,"device cannot list user events");
 using var heartbeat=await Request(HttpMethod.Post,"/api/v1/agent/heartbeat",device,new DeviceHeartbeat("Laptop","IP camera","rtsp://name:password@example.invalid/live?token=secret",true,["fire","disease"]));heartbeat.EnsureSuccessStatusCode();
 using var ownDevices=await Request(HttpMethod.Get,"/api/v1/devices",alice);var owned=await ownDevices.Content.ReadFromJsonAsync<DeviceRecord[]>(ApiJson.Options);Assert(owned!.Length==1&&owned[0].Source=="rtsp://example.invalid","camera credentials stripped from presence");
 using var otherDevices=await Request(HttpMethod.Get,"/api/v1/devices",bob);Assert((await otherDevices.Content.ReadFromJsonAsync<DeviceRecord[]>(ApiJson.Options))!.Length==0,"other account sees no devices");
 var upload=new EventUpload(Guid.NewGuid(),"fire",.91,null,null,DateTimeOffset.UtcNow,null,"Recorded image","unavailable","single_image",null,null,null);
 var image=File.ReadAllBytes("presentation-web/wwwroot/images/fire-photo.jpg");
 async Task<HttpResponseMessage> Upload(EventUpload data){using var form=new MultipartFormDataContent();form.Add(new StringContent(JsonSerializer.Serialize(data,ApiJson.Options)),"metadata");form.Add(new ByteArrayContent(image),"image","evidence.jpg");using var request=new HttpRequestMessage(HttpMethod.Post,"/api/v1/events"){Content=form};request.Headers.Authorization=AuthenticationHeaderValue.Parse(device);return await client.SendAsync(request);}
 using var saved=await Upload(upload);saved.EnsureSuccessStatusCode();var eventData=await saved.Content.ReadFromJsonAsync<EventResponse>(ApiJson.Options);Assert(eventData!.DeviceId==deviceId,"event belongs to authenticated device");
 Assert((await Upload(upload)).IsSuccessStatusCode,"idempotent retry accepted");
 Assert((await Upload(upload with{Confidence=.92})).StatusCode==HttpStatusCode.Conflict,"same event ID with changed content rejected");
 using var bobEvents=await Request(HttpMethod.Get,"/api/v1/events",bob);Assert((await bobEvents.Content.ReadFromJsonAsync<EventResponse[]>(ApiJson.Options))!.Length==0,"other account sees no events");
 using var aliceEvents=await Request(HttpMethod.Get,"/api/v1/events",alice);Assert((await aliceEvents.Content.ReadFromJsonAsync<EventResponse[]>(ApiJson.Options))!.Length==1,"retry creates exactly one event");
 Assert((await client.GetAsync(eventData.ImageUrl)).IsSuccessStatusCode,"signed image download succeeds");
 Assert((await client.GetAsync($"/api/v1/events/{upload.Id}/image")).StatusCode==HttpStatusCode.Unauthorized,"unsigned image download denied");
 Assert((await client.GetAsync(eventData.ImageUrl.Replace("signature=","signature=0"))).StatusCode==HttpStatusCode.Unauthorized,"forged evidence signature denied");
 Assert((await Upload(upload with{Id=Guid.NewGuid(),Confidence=2})).StatusCode==HttpStatusCode.BadRequest,"invalid confidence rejected");
 Assert((await Request(HttpMethod.Delete,$"/api/v1/events/{upload.Id}",bob)).StatusCode==HttpStatusCode.NotFound,"other account cannot delete event");
 Assert((await Request(HttpMethod.Delete,$"/api/v1/devices/{deviceId}",alice)).StatusCode==HttpStatusCode.NoContent,"owner can revoke device");
 Assert((await Request(HttpMethod.Get,"/api/v1/agent",device)).StatusCode==HttpStatusCode.Unauthorized,"revoked device credential rejected");
 Console.WriteLine($"API CHECKS PASSED: {checks}. Test store and ephemeral RSA certificates only; no live Firebase or SQL writes.");
}finally{await app.StopAsync();}
sealed class CertificateHandler(string json):HttpMessageHandler {protected override Task<HttpResponseMessage> SendAsync(HttpRequestMessage request,CancellationToken ct)=>Task.FromResult(new HttpResponseMessage(HttpStatusCode.OK){Content=new StringContent(json,Encoding.UTF8,"application/json")});}
