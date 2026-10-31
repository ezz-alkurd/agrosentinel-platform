using System.Diagnostics;
using System.Text.Json;
using System.Windows;
using Microsoft.Win32;
namespace AgroSentinel.Desktop;
public partial class MainWindow {
 DateTime? sessionStarted; bool stopRequested;
 string SettingsPath => Path.Combine(ConnectionStore.DirectoryPath,"preferences.json");
 record Preferences(string Source,int SourceMode,int Profile,bool Sync,bool Loop,string FireModel);
 void LoadPreferences(){
  try{if(!File.Exists(SettingsPath))return;var value=JsonSerializer.Deserialize<Preferences>(File.ReadAllText(SettingsPath));if(value is null)return;
   SourceText.Text=value.Source;SourceMode.SelectedIndex=Math.Clamp(value.SourceMode,0,1);ModelProfile.SelectedIndex=Math.Clamp(value.Profile,0,2);SyncEnabled.IsChecked=value.Sync;LoopVideo.IsChecked=value.Loop;FireModel.Text=value.FireModel;
  }catch(Exception error)when(error is IOException or JsonException or UnauthorizedAccessException){Log("Could not restore preferences. Using defaults.");}
 }
 void SavePreferences(){try{Directory.CreateDirectory(ConnectionStore.DirectoryPath);File.WriteAllText(SettingsPath,JsonSerializer.Serialize(new Preferences(SourceText.Text,SourceMode.SelectedIndex,ModelProfile.SelectedIndex,SyncEnabled.IsChecked==true,LoopVideo.IsChecked==true,FireModel.Text)));}catch(Exception error)when(error is IOException or UnauthorizedAccessException){Log("Could not save preferences.");}}
 void SetRunning(bool running){StartButton.IsEnabled=RetryButton.IsEnabled=PairButton.IsEnabled=!running;StopButton.IsEnabled=running;SyncEnabled.IsEnabled=SourceMode.IsEnabled=SourceText.IsEnabled=ModelProfile.IsEnabled=LoopVideo.IsEnabled=FireModel.IsEnabled=ApiUrl.IsEnabled=!running;}
 void UpdateSession(){
  SessionTime.Text="Session "+(sessionStarted is null?"00:00:00":(DateTime.UtcNow-sessionStarted.Value).ToString(@"hh\:mm\:ss"));
  if(sessionStarted is not null&&lastPreview!=DateTime.MinValue&&!stopRequested){var age=DateTime.UtcNow-lastPreview;PreviewStatus.Text=age.TotalSeconds>10?"Waiting for camera / stream. Reconnecting automatically...":"Preview updated "+Math.Max(0,(int)age.TotalSeconds)+"s ago - inference on this laptop";}
 }
 void WindowKeys(object sender,System.Windows.Input.KeyEventArgs e){
  var control=(System.Windows.Input.Keyboard.Modifiers&System.Windows.Input.ModifierKeys.Control)!=0;
  if(e.Key==System.Windows.Input.Key.F5){e.Handled=true;if((System.Windows.Input.Keyboard.Modifiers&System.Windows.Input.ModifierKeys.Shift)!=0)StopClick(this,new RoutedEventArgs());else if(StartButton.IsEnabled)StartClick(this,new RoutedEventArgs());}
  else if(control&&e.Key==System.Windows.Input.Key.O){e.Handled=true;BrowseSource(this,new RoutedEventArgs());}
  else if(control&&e.Key==System.Windows.Input.Key.S){e.Handled=true;ExportActivity(this,new RoutedEventArgs());}
  else if(e.Key==System.Windows.Input.Key.F1){e.Handled=true;HelpClick(this,new RoutedEventArgs());}
 }
 void ConnectionClick(object sender,RoutedEventArgs e)=>SettingsTabs.SelectedIndex=1;
 void ExitClick(object sender,RoutedEventArgs e)=>Close();
 void OpenDataClick(object sender,RoutedEventArgs e){Directory.CreateDirectory(ConnectionStore.DirectoryPath);Process.Start(new ProcessStartInfo(ConnectionStore.DirectoryPath){UseShellExecute=true});}
 void ClearActivity(object sender,RoutedEventArgs e)=>Activity.Clear();
 void ExportActivity(object sender,RoutedEventArgs e){var picker=new SaveFileDialog{Filter="Text log|*.txt",FileName="AgroSentinel-activity-"+DateTime.Now.ToString("yyyyMMdd-HHmm")+".txt"};if(picker.ShowDialog()==true)try{File.WriteAllText(picker.FileName,Activity.Text);}catch(Exception error)when(error is IOException or UnauthorizedAccessException){MessageBox.Show(this,error.Message,"Could not export activity");}}
 void HelpClick(object sender,RoutedEventArgs e)=>MessageBox.Show(this,"1. Connection tab: generate a pairing code and enter it in phone Settings > Server & paired devices.\n\n2. Monitor tab: choose camera 0, a video file, or a stream address. Choose models and Start monitoring.\n\n3. Stop ends the session. Live sources reconnect automatically; Repeat video keeps clips running. Single photo analyzes once.\n\n4. Confirmed events sync to phone Events while the phone app is open. Pending evidence retries automatically.\n\nUse File > Export activity to save a troubleshooting log.","Getting started",MessageBoxButton.OK,MessageBoxImage.Information);
 void AboutClick(object sender,RoutedEventArgs e)=>MessageBox.Show(this,"AgroSentinel 1.0.1\nField monitoring for Windows\n\nFire detection and close-up tomato leaf analysis run on this laptop. Confirmed events sync to your paired phone account.","About AgroSentinel",MessageBoxButton.OK,MessageBoxImage.Information);
}
