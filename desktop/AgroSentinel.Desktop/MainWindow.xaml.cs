using System.ComponentModel;
using System.Diagnostics;
using System.Net.Http;
using System.Net.Http.Json;
using System.Text.Json;
using System.Windows;
using System.Windows.Threading;
namespace AgroSentinel.Desktop;
public partial class MainWindow : Window {
 readonly HttpClient http=new(){Timeout=TimeSpan.FromSeconds(20)};
 readonly DispatcherTimer timer=new(){Interval=TimeSpan.FromMilliseconds(300)};
 DeviceConnection? connection=ConnectionStore.Load();CancellationTokenSource? pairing;Process? process;
 string? previewFile,stopFile;DateTime lastPreview;bool closing;
 public MainWindow(){InitializeComponent();var configuredUrl=connection?.BaseUrl??Environment.GetEnvironmentVariable("AGROSENTINEL_API_URL");ApiUrl.Text=string.IsNullOrWhiteSpace(configuredUrl)?ConnectionStore.DefaultBaseUrl:configuredUrl;if(connection is not null)PairStatus.Text="Laptop paired. Device "+connection.DeviceId.ToString()[..8];LoadPreferences();timer.Tick+=(_,_)=>{UpdatePreview();UpdateSession();};timer.Start();}
 void Log(string text){Activity.AppendText(DateTime.Now.ToString("HH:mm:ss")+"  "+text+Environment.NewLine);if(Activity.Text.Length>22000)Activity.Text=Activity.Text[^18000..];Activity.ScrollToEnd();if(text.StartsWith("Running"))StateText.Text=SyncEnabled.IsChecked==true?"Monitoring · sync enabled":"Monitoring · local preview";}
 async Task<JsonElement> Read(HttpResponseMessage response){var body=await response.Content.ReadAsStringAsync();if(!response.IsSuccessStatusCode){string message=$"Server returned HTTP {(int)response.StatusCode}.";try{message=JsonDocument.Parse(body).RootElement.GetProperty("error").GetString()??message;}catch(JsonException){}catch(KeyNotFoundException){}throw new InvalidOperationException(message);}return JsonDocument.Parse(body).RootElement.Clone();}
 async void PairClick(object sender,RoutedEventArgs e){
  pairing?.Cancel();pairing=new();var ct=pairing.Token;PairButton.IsEnabled=false;
  try{
   var url=ConnectionStore.ValidateUrl(ApiUrl.Text);using(var health=await http.GetAsync(url+"/api/v1/health",ct)){await Read(health);}
   using var response=await http.PostAsJsonAsync(url+"/api/v1/pairing/request",new{name=Environment.MachineName},ct);var ticket=await Read(response);
   var code=ticket.GetProperty("code").GetString()!;var id=ticket.GetProperty("id").GetGuid();var token=ticket.GetProperty("poll_token").GetString()!;
   PairCode.Text=code[..4]+"-"+code[4..];PairStatus.Text="Phone → Settings → Server & paired devices. Enter this code within 10 minutes.";
   var expiry=ticket.GetProperty("expires_at").GetDateTimeOffset();
   while(DateTimeOffset.UtcNow<expiry){await Task.Delay(2500,ct);using var request=new HttpRequestMessage(HttpMethod.Get,url+$"/api/v1/pairing/{id}");request.Headers.Add("X-Pairing-Token",token);using var result=await http.SendAsync(request,ct);var state=await Read(result);
    if(state.GetProperty("status").GetString()=="paired"){connection=new(url,token,state.GetProperty("device_id").GetGuid());ConnectionStore.Save(connection);PairCode.Text="Paired";PairStatus.Text="Laptop connected to your phone account.";Log("Pairing complete. The upload credential is protected by Windows.");return;}
    if(state.GetProperty("status").GetString()=="expired")break;
   }PairStatus.Text="Pairing code expired. Choose Pair with phone again.";
  }catch(OperationCanceledException){PairStatus.Text="Pairing cancelled or timed out.";}catch(Exception error){PairStatus.Text=error.Message;Log("Connection: "+error.Message);}finally{PairButton.IsEnabled=true;}
 }
 void StopClick(object sender,RoutedEventArgs e){if(process is null||process.HasExited)return;stopRequested=true;if(stopFile is not null)File.WriteAllText(stopFile,"stop");StateText.Text="Stopping...";StopButton.IsEnabled=false;}
 async void WindowClosing(object? sender,CancelEventArgs e){
  SavePreferences();pairing?.Cancel();if(process is not null&&!process.HasExited&&!closing){e.Cancel=true;closing=true;StopClick(this,new RoutedEventArgs());var running=process;try{await running.WaitForExitAsync().WaitAsync(TimeSpan.FromSeconds(45));}catch(TimeoutException){if(!running.HasExited)running.Kill(true);}closing=false;Close();return;}timer.Stop();http.Dispose();
 }
}
