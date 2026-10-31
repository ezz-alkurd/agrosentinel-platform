using System.Globalization;
using System.IdentityModel.Tokens.Jwt;
using System.Security.Claims;
using System.Security.Cryptography.X509Certificates;
using System.Text.Encodings.Web;
using Microsoft.AspNetCore.Authentication;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using Microsoft.IdentityModel.Tokens;
namespace AgroSentinel.ControlApi;
public interface IFirebaseTokenValidator {Task<ClaimsPrincipal> Validate(string token,CancellationToken ct);}
public sealed class FirebaseTokenValidator(HttpClient http,ApiOptions options) : IFirebaseTokenValidator {
 readonly SemaphoreSlim gate=new(1,1);SecurityKey[] keys=[];DateTimeOffset expires;
 async Task<SecurityKey[]> Keys(CancellationToken ct){
  await gate.WaitAsync(ct);try{
   if(keys.Length>0&&expires>DateTimeOffset.UtcNow)return keys;
   using var response=await http.GetAsync("https://www.googleapis.com/robot/v1/metadata/x509/securetoken@system.gserviceaccount.com",ct);response.EnsureSuccessStatusCode();
   var data=System.Text.Json.JsonSerializer.Deserialize<Dictionary<string,string>>(await response.Content.ReadAsStringAsync(ct))??throw new SecurityTokenException("Signing certificates unavailable.");
   keys=data.Select(pair=>(SecurityKey)new X509SecurityKey(X509Certificate2.CreateFromPem(pair.Value)){KeyId=pair.Key}).ToArray();
   expires=DateTimeOffset.UtcNow.AddSeconds(Math.Clamp(response.Headers.CacheControl?.MaxAge?.TotalSeconds??3600,60,86400));return keys;
  }finally{gate.Release();}
 }
 public async Task<ClaimsPrincipal> Validate(string token,CancellationToken ct){
  if(token.Length>16000)throw new SecurityTokenException("Token is too long.");
  var handler=new JwtSecurityTokenHandler{MapInboundClaims=false};
  var principal=handler.ValidateToken(token,new TokenValidationParameters{ValidateIssuer=true,ValidIssuer="https://securetoken.google.com/"+options.FirebaseProjectId,ValidateAudience=true,ValidAudience=options.FirebaseProjectId,ValidateLifetime=true,RequireExpirationTime=true,RequireSignedTokens=true,ValidateIssuerSigningKey=true,IssuerSigningKeys=await Keys(ct),ValidAlgorithms=[SecurityAlgorithms.RsaSha256],ClockSkew=TimeSpan.FromSeconds(60)},out _);
  var uid=principal.FindFirstValue("sub");
  if(string.IsNullOrWhiteSpace(uid)||uid.Length>128)throw new SecurityTokenException("Invalid Firebase subject.");
  var now=DateTimeOffset.UtcNow.ToUnixTimeSeconds();
  foreach(var name in new[]{"iat","auth_time"})if(!long.TryParse(principal.FindFirstValue(name),NumberStyles.Integer,CultureInfo.InvariantCulture,out var value)||value<0||value>now+60)throw new SecurityTokenException("Invalid token time.");
  ((ClaimsIdentity)principal.Identity!).AddClaim(new Claim("actor_kind","user"));return principal;
 }
}
public sealed class ApiAuthenticationHandler(IOptionsMonitor<AuthenticationSchemeOptions> options,ILoggerFactory logger,UrlEncoder encoder,IFirebaseTokenValidator validator,IControlStore store) : AuthenticationHandler<AuthenticationSchemeOptions>(options,logger,encoder) {
 protected override async Task<AuthenticateResult> HandleAuthenticateAsync(){
  var header=Request.Headers.Authorization.ToString();if(string.IsNullOrEmpty(header))return AuthenticateResult.NoResult();
  try{
   ClaimsPrincipal principal;
   if(header.StartsWith("Bearer ",StringComparison.OrdinalIgnoreCase))principal=await validator.Validate(header[7..],Context.RequestAborted);
   else if(header.StartsWith("Device ",StringComparison.OrdinalIgnoreCase)){
    var token=header[7..];if(token.Length is <32 or >128)return AuthenticateResult.Fail("Invalid device credential.");
    var device=await store.AuthenticateDevice(token,Context.RequestAborted);if(device is null)return AuthenticateResult.Fail("Device is unknown or revoked.");
    principal=new ClaimsPrincipal(new ClaimsIdentity([new Claim("sub",device.OwnerUid),new Claim("actor_kind","device"),new Claim("device_id",device.Id.ToString())],Scheme.Name));
   }else return AuthenticateResult.Fail("Unsupported authorization scheme.");
   return AuthenticateResult.Success(new AuthenticationTicket(principal,Scheme.Name));
  }catch(SecurityTokenException){return AuthenticateResult.Fail("Invalid or expired token.");}
 }
}
