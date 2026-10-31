using System.Security.Cryptography;
using System.Text;
using System.Windows;
using System.Windows.Media.Imaging;
namespace AgroSentinel.Desktop;
public partial class MainWindow {
 void UpdatePreview(){
  try{
   if(previewFile is not null&&File.Exists(previewFile)&&File.GetLastWriteTimeUtc(previewFile)>lastPreview){using var stream=new FileStream(previewFile,FileMode.Open,FileAccess.Read,FileShare.ReadWrite|FileShare.Delete);var bitmap=new BitmapImage();bitmap.BeginInit();bitmap.CacheOption=BitmapCacheOption.OnLoad;bitmap.StreamSource=stream;bitmap.EndInit();bitmap.Freeze();Preview.Source=bitmap;PreviewHint.Visibility=Visibility.Collapsed;lastPreview=File.GetLastWriteTimeUtc(previewFile);}
   var queued=0;if(connection is not null){var scope=Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(connection.BaseUrl+"\n"+connection.Token))).ToLowerInvariant()[..20];var folder=Path.Combine(ConnectionStore.DirectoryPath,"outbox",scope);if(Directory.Exists(folder))queued=Directory.EnumerateFiles(folder,"metadata.json",SearchOption.AllDirectories).Count();}
   QueueStatus.Text=queued>0?$"{queued} detection(s) saved locally, awaiting server upload.":"No pending uploads - phone Events refresh automatically.";
  }catch(IOException){}catch(NotSupportedException){}
 }
}
