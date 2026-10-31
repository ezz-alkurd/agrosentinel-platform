using System.Security.Cryptography;
using System.Text;
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Http;
namespace AgroSentinel.ControlApi;
public sealed class EvidenceStore(ApiOptions options,IWebHostEnvironment environment) {
 readonly SemaphoreSlim writeGate=new(1,1);
 public string Root=>Path.GetFullPath(Path.IsPathRooted(options.EvidenceDirectory)?options.EvidenceDirectory:Path.Combine(environment.ContentRootPath,options.EvidenceDirectory));
 public async Task<(string Key,string Hash)> Save(Guid device,Guid id,IFormFile file,CancellationToken ct){
  if(file.Length is <4 or >8*1024*1024)throw new ApiFault(400,"Evidence must be a JPEG photo of at most 8 MB.");
  using var data=new MemoryStream();await using(var input=file.OpenReadStream()){
   var block=new byte[81920];int read;while((read=await input.ReadAsync(block,ct))>0){if(data.Length+read>8*1024*1024)throw new ApiFault(413,"Evidence is too large.");await data.WriteAsync(block.AsMemory(0,read),ct);}
  }
  var bytes=data.ToArray();if(bytes.Length<4||bytes[0]!=255||bytes[1]!=216||bytes[2]!=255||bytes[^2]!=255||bytes[^1]!=217)throw new ApiFault(400,"Evidence must contain JPEG data.");
  var hash=Secrets.Hex(SHA256.HashData(bytes));var key=$"{device:N}/{id:N}-{hash}.jpg";var destination=Resolve(key);
  await writeGate.WaitAsync(ct);try{
   Directory.CreateDirectory(Root);if(File.Exists(destination))return(key,hash);
   var used=Directory.EnumerateFiles(Root,"*.jpg",SearchOption.AllDirectories).Sum(p=>new FileInfo(p).Length);
   if(used+bytes.Length>options.MaxEvidenceStorageBytes)throw new ApiFault(507,"Evidence storage limit reached. Ask the server operator to review retention.");
   Directory.CreateDirectory(Path.GetDirectoryName(destination)!);var temporary=destination+"."+Guid.NewGuid().ToString("N")+".tmp";
   try{await File.WriteAllBytesAsync(temporary,bytes,ct);File.Move(temporary,destination,false);}finally{if(File.Exists(temporary))File.Delete(temporary);}
  }finally{writeGate.Release();}return(key,hash);
 }
 public string Resolve(string key){var root=Root.TrimEnd(Path.DirectorySeparatorChar)+Path.DirectorySeparatorChar;var file=Path.GetFullPath(Path.Combine(root,key));if(!file.StartsWith(root,StringComparison.OrdinalIgnoreCase))throw new ApiFault(400,"Invalid evidence key.");return file;}
 byte[] Sign(Guid id,string owner,long expiry)=>HMACSHA256.HashData(Encoding.UTF8.GetBytes(options.MediaSigningKey),Encoding.UTF8.GetBytes($"{id:N}\n{owner}\n{expiry}"));
 public string Url(StoredEvent item){var expiry=DateTimeOffset.UtcNow.AddHours(1).ToUnixTimeSeconds();return options.PublicBaseUrl.TrimEnd('/')+$"/api/v1/events/{item.Id}/image?expires={expiry}&signature={Secrets.Hex(Sign(item.Id,item.OwnerUid,expiry))}";}
 public bool Verify(StoredEvent item,long expiry,string signature){
  var now=DateTimeOffset.UtcNow.ToUnixTimeSeconds();if(expiry<now||expiry>now+3660||signature.Length!=64)return false;
  try{return Secrets.Equal(Sign(item.Id,item.OwnerUid,expiry),Convert.FromHexString(signature));}catch(FormatException){return false;}
 }
}
