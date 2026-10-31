using System.Diagnostics;
using System.Windows;
using Microsoft.Win32;
namespace AgroSentinel.Desktop;
public partial class MainWindow {
 void BrowseSource(object sender,RoutedEventArgs e){if(process is not null&&!process.HasExited)return;var picker=new OpenFileDialog{Filter="Images and videos|*.jpg;*.jpeg;*.png;*.webp;*.mp4;*.avi;*.mkv;*.mov|All files|*.*"};if(picker.ShowDialog()==true){SourceText.Text=picker.FileName;SourceMode.SelectedIndex=new[]{".jpg",".jpeg",".png",".webp"}.Contains(Path.GetExtension(picker.FileName).ToLowerInvariant())?1:0;}}
 void BrowseModel(object sender,RoutedEventArgs e){if(process is not null&&!process.HasExited)return;var picker=new OpenFileDialog{Filter="PyTorch model|*.pt"};if(picker.ShowDialog()==true)FireModel.Text=picker.FileName;}
 async void StartClick(object sender,RoutedEventArgs e)=>await Start(false);
 async void RetryClick(object sender,RoutedEventArgs e)=>await Start(true);
 string? FindRepo(){var folder=new DirectoryInfo(AppContext.BaseDirectory);while(folder is not null){if(File.Exists(Path.Combine(folder.FullName,"ai-backend","run_detection.py")))return folder.FullName;folder=folder.Parent;}return null;}
 async Task Start(bool syncOnly){
  if(process is not null&&!process.HasExited)return;
  try{
   SavePreferences();stopRequested=false;
   var sync=syncOnly||SyncEnabled.IsChecked==true;var url=ConnectionStore.ValidateUrl(ApiUrl.Text.Length==0&&!sync?"http://localhost":ApiUrl.Text);
   if(sync&&(connection is null||connection.BaseUrl!=url)){SettingsTabs.SelectedIndex=1;throw new InvalidOperationException("Pair this laptop with the phone at this website address first, or disable sync for a local preview.");}
   var work=Path.Combine(ConnectionStore.DirectoryPath,"runtime");Directory.CreateDirectory(work);previewFile=Path.Combine(work,"preview.jpg");stopFile=Path.Combine(work,"stop-"+Guid.NewGuid().ToString("N"));lastPreview=DateTime.MinValue;
   var bundled=Path.GetFullPath(Path.Combine(AppContext.BaseDirectory,"..","worker","AgroSentinel.Worker.exe"));var repo=FindRepo();var info=new ProcessStartInfo{UseShellExecute=false,RedirectStandardOutput=true,RedirectStandardError=true,CreateNoWindow=true};
   if(File.Exists(bundled))info.FileName=bundled;
   else{
    if(repo is null)throw new InvalidOperationException("The packaged detection worker is missing. Use the complete published application folder.");
    var local=Path.Combine(repo,".venv","Scripts","python.exe");var installed=Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),"Programs","Python","Python311","python.exe");
    info.FileName=File.Exists(local)?local:File.Exists(installed)?installed:"python.exe";info.ArgumentList.Add(Path.Combine(repo,"ai-backend","run_detection.py"));info.WorkingDirectory=repo;
   }
   info.ArgumentList.Add("--backend");info.ArgumentList.Add("api");
   if(syncOnly)info.ArgumentList.Add("--sync-only");
   else{
    info.ArgumentList.Add(SourceMode.SelectedIndex==1?"--image":"--source");info.ArgumentList.Add(SourceText.Text.Trim());
    if(SourceMode.SelectedIndex==0&&LoopVideo.IsChecked==true)info.ArgumentList.Add("--loop-video");
    info.ArgumentList.Add("--headless");info.ArgumentList.Add("--preview-file");info.ArgumentList.Add(previewFile);info.ArgumentList.Add("--stop-file");info.ArgumentList.Add(stopFile);
    info.ArgumentList.Add("--name");info.ArgumentList.Add(Environment.MachineName);
    if(ModelProfile.SelectedIndex==1)info.ArgumentList.Add("--no-disease");if(ModelProfile.SelectedIndex==2)info.ArgumentList.Add("--no-fire");
    if(FireModel.Text.Trim().Length>0){info.ArgumentList.Add("--fire-model");info.ArgumentList.Add(FireModel.Text.Trim());}
    if(!sync)info.ArgumentList.Add("--local-only");
   }
   info.Environment["PYTHONUTF8"]="1";info.Environment["PYTHONUNBUFFERED"]="1";info.Environment["YOLO_CONFIG_DIR"]=Path.Combine(work,"ultralytics");info.Environment["AGROSENTINEL_OUTBOX_DIR"]=Path.Combine(ConnectionStore.DirectoryPath,"outbox");info.Environment["AGROSENTINEL_DEVICE_NAME"]=Environment.MachineName;
   if(sync){info.Environment["AGROSENTINEL_API_URL"]=connection!.BaseUrl;info.Environment["AGROSENTINEL_DEVICE_TOKEN"]=connection.Token;}
   process=new Process{StartInfo=info};process.OutputDataReceived+=(_,line)=>{if(line.Data is not null)Dispatcher.BeginInvoke(()=>Log(line.Data));};process.ErrorDataReceived+=(_,line)=>{if(line.Data is not null)Dispatcher.BeginInvoke(()=>Log(line.Data));};
   StateText.Text=syncOnly?"Retrying uploads":"Loading models...";SetRunning(true);PreviewStatus.Text="Starting detection engine...";Preview.Source=null;PreviewHint.Visibility=Visibility.Visible;sessionStarted=DateTime.UtcNow;
   process.Start();process.BeginOutputReadLine();process.BeginErrorReadLine();await process.WaitForExitAsync();StateText.Text=process.ExitCode==0?(stopRequested?"Stopped":"Completed"):"Needs attention";PreviewStatus.Text=stopRequested?"Session stopped by you":process.ExitCode==0?"Analysis completed":"Engine stopped. Export activity to review the error.";Log("Detection engine exited with code "+process.ExitCode+".");
  }catch(Exception error){Log(error.Message);StateText.Text="Needs attention";}
  finally{SetRunning(false);sessionStarted=null;process?.Dispose();process=null;if(stopFile is not null&&File.Exists(stopFile))File.Delete(stopFile);}
 }
}
