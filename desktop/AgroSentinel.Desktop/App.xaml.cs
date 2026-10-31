using System.Windows;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Threading;
namespace AgroSentinel.Desktop;
public partial class App : Application {
 protected override void OnStartup(StartupEventArgs e){
  base.OnStartup(e);
  DispatcherUnhandledException+=(_,eventArgs)=>{MessageBox.Show(eventArgs.Exception.Message,"AgroSentinel",MessageBoxButton.OK,MessageBoxImage.Error);eventArgs.Handled=true;};
  var window=new MainWindow();
  if(e.Args.Length==2&&e.Args[0]=="--render-preview"){
   window.ShowInTaskbar=false;window.Left=-10000;window.Top=-10000;window.Show();
   Dispatcher.BeginInvoke(DispatcherPriority.ApplicationIdle,new Action(async ()=>{
    await Task.Delay(500);
    window.UpdateLayout();var content=(FrameworkElement)window.Content;content.UpdateLayout();var image=new RenderTargetBitmap((int)content.ActualWidth,(int)content.ActualHeight,96,96,PixelFormats.Pbgra32);image.Render(content);var encoder=new PngBitmapEncoder();encoder.Frames.Add(BitmapFrame.Create(image));using(var file=File.Create(e.Args[1]))encoder.Save(file);window.Close();Shutdown();
   }));
  }else window.Show();
 }
}
