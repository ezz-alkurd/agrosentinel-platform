using System;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Reflection;
using System.Security.Cryptography;
using System.Threading.Tasks;
using System.Windows.Forms;
using Microsoft.Win32;

namespace AgroSentinel.Setup {
 static class Locations {
  internal const string ProductId="AgroSentinel.Desktop.Install.v1";
  internal const string Marker=".agrosentinel-install";
  internal const string RegistryPath=@"Software\Microsoft\Windows\CurrentVersion\Uninstall\AgroSentinel";
  internal static string Parent { get {return Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),"Programs");} }
  internal static string Target { get {return Path.GetFullPath(Path.Combine(Parent,"AgroSentinel"));} }
  internal static string StartMenu {get{return Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.Programs),"AgroSentinel.lnk");}}
  internal static string Desktop {get{return Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory),"AgroSentinel.lnk");}}
  internal static void CheckChild(string path) {
   var prefix=Path.GetFullPath(Parent).TrimEnd(Path.DirectorySeparatorChar)+Path.DirectorySeparatorChar;
   if(!Path.GetFullPath(path).StartsWith(prefix,StringComparison.OrdinalIgnoreCase))throw new IOException("Installation path is outside your Programs folder.");
  }
  internal static bool Owned(string folder) {return File.Exists(Path.Combine(folder,Marker))&&File.ReadAllText(Path.Combine(folder,Marker)).Trim()==ProductId;}
  internal static void DeleteOwned(string folder) {CheckChild(folder);if(Directory.Exists(folder)){if(!Owned(folder))throw new IOException("The folder does not belong to this installer.");Directory.Delete(folder,true);}}
  internal static void Launch() {Process.Start(new ProcessStartInfo(Path.Combine(Target,"AgroSentinel.exe")){WorkingDirectory=Target,UseShellExecute=true});}
 }
#if INSTALLER
 static class Payload {
  const string Prefix="AgroSentinel-Windows/";
  internal static Stream Open() {
   var stream=Assembly.GetExecutingAssembly().GetManifestResourceStream("AgroSentinel.Payload.zip");
   if(stream==null)throw new IOException("Installation files are missing.");
   using(var sha=SHA256.Create()) {
    var hash=BitConverter.ToString(sha.ComputeHash(stream)).Replace("-","").ToLowerInvariant();
    if(hash!=ReleaseInfo.PayloadSha256){stream.Dispose();throw new IOException("The setup file is damaged. Copy it again.");}
   }
   stream.Position=0;return stream;
  }
  internal static string Destination(string root,string name) {
   if(!name.StartsWith(Prefix,StringComparison.Ordinal))throw new IOException("Unexpected installation entry.");
   var relative=name.Substring(Prefix.Length).Replace('/',Path.DirectorySeparatorChar);
   if(relative.Length==0||Path.IsPathRooted(relative)||relative.Split(Path.DirectorySeparatorChar).Any(x=>x==".."||x=="."))throw new IOException("Invalid installation path.");
   var prefix=Path.GetFullPath(root).TrimEnd(Path.DirectorySeparatorChar)+Path.DirectorySeparatorChar;
   var full=Path.GetFullPath(Path.Combine(root,relative));
   if(!full.StartsWith(prefix,StringComparison.OrdinalIgnoreCase))throw new IOException("Invalid installation path.");
   return full;
  }
  internal static long Validate(ZipArchive zip,string root) {
   if(zip.Entries.Count>50000)throw new IOException("Unexpected installation size.");
   long total=0;
   foreach(var entry in zip.Entries){if(entry.FullName.EndsWith("/",StringComparison.Ordinal))continue;Destination(root,entry.FullName);total=checked(total+entry.Length);}
   if(total>8L*1024*1024*1024)throw new IOException("Unexpected installation size.");
   foreach(var required in new[]{"AgroSentinel.exe","app/AgroSentinel.dll","worker/AgroSentinel.Worker.exe","runtime/dotnet.exe","models/demo-selection.json","Uninstall.exe",Locations.Marker})
    if(zip.GetEntry(Prefix+required)==null)throw new IOException("Installation files are incomplete.");
   return total;
  }
  internal static void Extract(string root,Action<int,string> progress) {
   using(var stream=Open())using(var zip=new ZipArchive(stream,ZipArchiveMode.Read)) {
    Validate(zip,root);int count=0;
    Directory.CreateDirectory(root);
    foreach(var entry in zip.Entries) {
     if(entry.FullName.EndsWith("/",StringComparison.Ordinal))continue;
     var path=Destination(root,entry.FullName);Directory.CreateDirectory(Path.GetDirectoryName(path));
     using(var source=entry.Open())using(var destination=new FileStream(path,FileMode.CreateNew,FileAccess.Write,FileShare.None))source.CopyTo(destination);
     count++;if(count%30==0||count==zip.Entries.Count)progress((int)(100L*count/zip.Entries.Count),"Installing application files...");
    }
   }
  }
 }
 static class Install {
  static void Shortcut(string path) {
   dynamic shell=Activator.CreateInstance(Type.GetTypeFromProgID("WScript.Shell"));
   dynamic shortcut=shell.CreateShortcut(path);shortcut.TargetPath=Path.Combine(Locations.Target,"AgroSentinel.exe");
   shortcut.WorkingDirectory=Locations.Target;shortcut.Description="AgroSentinel field monitoring";shortcut.IconLocation=Path.Combine(Locations.Target,"AgroSentinel.exe")+",0";shortcut.Save();
  }
  internal static void Run(Action<int,string> progress) {
   Locations.CheckChild(Locations.Target);
   if(Directory.Exists(Locations.Target)&&!Locations.Owned(Locations.Target))throw new IOException("An unrelated folder already exists at the installation location.");
   long bytes;using(var stream=Payload.Open())using(var zip=new ZipArchive(stream,ZipArchiveMode.Read))bytes=Payload.Validate(zip,Locations.Target);
   if(new DriveInfo(Path.GetPathRoot(Locations.Target)).AvailableFreeSpace<bytes+100L*1024*1024)throw new IOException("There is not enough free space to install AgroSentinel.");
   Directory.CreateDirectory(Locations.Parent);
   var stage=Path.Combine(Locations.Parent,".AgroSentinel-install-"+Guid.NewGuid().ToString("N"));
   var backup=Path.Combine(Locations.Parent,".AgroSentinel-backup-"+Guid.NewGuid().ToString("N"));
   Locations.CheckChild(stage);Locations.CheckChild(backup);
   bool movedOld=false,movedNew=false;
   try {
    progress(0,"Verifying and extracting application files...");Payload.Extract(stage,progress);
    if(!Locations.Owned(stage))throw new IOException("Invalid installation marker.");
    if(Directory.Exists(Locations.Target)){Directory.Move(Locations.Target,backup);movedOld=true;}
    Directory.Move(stage,Locations.Target);movedNew=true;
    Shortcut(Locations.StartMenu);Shortcut(Locations.Desktop);
    using(var key=Registry.CurrentUser.CreateSubKey(Locations.RegistryPath)) {
     key.SetValue("DisplayName","AgroSentinel");key.SetValue("DisplayVersion","1.0.1");key.SetValue("Publisher","AgroSentinel Team");
     key.SetValue("InstallLocation",Locations.Target);key.SetValue("DisplayIcon",Path.Combine(Locations.Target,"AgroSentinel.exe"));
     key.SetValue("UninstallString","\""+Path.Combine(Locations.Target,"Uninstall.exe")+"\"");
     key.SetValue("NoModify",1,RegistryValueKind.DWord);key.SetValue("NoRepair",1,RegistryValueKind.DWord);
     key.SetValue("EstimatedSize",(int)(bytes/1024),RegistryValueKind.DWord);
    }
   } catch {
    if(movedNew)Locations.DeleteOwned(Locations.Target);
    if(movedOld&&Directory.Exists(backup))Directory.Move(backup,Locations.Target);
    throw;
   } finally {
    // Only remove our own staging folder after checking its resolved path and marker.
    if(Directory.Exists(stage)&&Locations.Owned(stage))Locations.DeleteOwned(stage);
   }
   if(movedOld){try{Locations.DeleteOwned(backup);}catch(IOException){}catch(UnauthorizedAccessException){}}
   progress(100,"Installed. Your server address is already configured.");
  }
 }
 sealed class SetupForm:Form {
  readonly Button action=new Button();readonly Label status=new Label();readonly ProgressBar progress=new ProgressBar();bool installed,busy;
  internal SetupForm() {
   Text="AgroSentinel Setup";ClientSize=new Size(590,370);FormBorderStyle=FormBorderStyle.FixedDialog;MaximizeBox=false;StartPosition=FormStartPosition.CenterScreen;
   BackColor=Color.FromArgb(242,245,241);Font=new Font("Segoe UI",11);Icon=Icon.ExtractAssociatedIcon(Assembly.GetExecutingAssembly().Location);
   Controls.Add(new Label{Text="AgroSentinel",Font=new Font("Segoe UI",27,FontStyle.Bold),ForeColor=Color.FromArgb(24,45,34),AutoSize=true,Location=new Point(28,25)});
   Controls.Add(new Label{Text="Field monitoring, ready for this laptop.",AutoSize=true,Location=new Point(31,85)});
   Controls.Add(new Label{Text="Includes the fire and tomato models, detection engine and Windows runtime.\nNo separate Python or .NET installation is needed.",Location=new Point(31,126),Size=new Size(530,60)});
   Controls.Add(new Label{Text="Installation folder:\n"+Locations.Target,Location=new Point(31,197),Size=new Size(530,49),Font=new Font("Segoe UI",9)});
   status.Text="Sign in on your phone and pair this laptop once after installation.";status.Location=new Point(31,254);status.Size=new Size(530,45);status.Font=new Font("Segoe UI",9);Controls.Add(status);
   progress.Location=new Point(31,310);progress.Size=new Size(355,20);Controls.Add(progress);
   action.Text="Install";action.Location=new Point(414,302);action.Size=new Size(143,43);action.BackColor=Color.FromArgb(36,93,67);action.ForeColor=Color.White;action.FlatStyle=FlatStyle.Flat;action.Click+=InstallClicked;Controls.Add(action);
   FormClosing+=(s,e)=>{if(busy)e.Cancel=true;};
  }
  async void InstallClicked(object sender,EventArgs e) {
   if(installed){Locations.Launch();Close();return;}
   busy=true;action.Enabled=false;
   try {
    await Task.Run(()=>Install.Run((value,text)=>BeginInvoke(new Action(()=>{progress.Value=value;status.Text=text;}))));
    installed=true;action.Text="Open app";status.Text="Installed. Open AgroSentinel and pair this laptop with your phone.";
   } catch(Exception error){status.Text="Installation failed. Close AgroSentinel if it is running, then try again.";MessageBox.Show(this,error.Message,"AgroSentinel Setup",MessageBoxButtons.OK,MessageBoxIcon.Error);}
   finally{busy=false;action.Enabled=true;}
  }
 }
#endif
 static class Program {
  [STAThread] static int Main(string[] args) {
   Application.EnableVisualStyles();Application.SetCompatibleTextRenderingDefault(false);
#if INSTALLER
   if(args.Length==2&&args[0]=="--verify-payload") {
    try{using(var stream=Payload.Open())using(var zip=new ZipArchive(stream,ZipArchiveMode.Read)){var bytes=Payload.Validate(zip,Path.Combine(Path.GetTempPath(),"AgroSentinel-check"));File.WriteAllText(args[1],"PASS: embedded payload checksum, required files and safe extraction paths. Files="+zip.Entries.Count+" Bytes="+bytes);return 0;}}
    catch(Exception ex){File.WriteAllText(args[1],"FAIL: "+ex.GetType().Name+": "+ex.Message);return 1;}
   }
   if(args.Length==3&&args[0]=="--extract-test") {
    try{if(Directory.Exists(args[1])&&Directory.EnumerateFileSystemEntries(args[1]).Any())throw new IOException("Test directory must be empty.");Payload.Extract(args[1],(p,s)=>{});File.WriteAllText(args[2],"PASS: embedded setup files extracted without installing or registering the app.");return 0;}
    catch(Exception ex){File.WriteAllText(args[2],"FAIL: "+ex.GetType().Name+": "+ex.Message);return 1;}
   }
   Application.Run(new SetupForm());return 0;
#else
   try {
    Locations.CheckChild(Locations.Target);if(!Locations.Owned(Locations.Target))throw new IOException("A valid AgroSentinel installation was not found.");
    if(args.Length==0){var temporary=Path.Combine(Path.GetTempPath(),"AgroSentinel-uninstall-"+Guid.NewGuid().ToString("N")+".exe");File.Copy(Assembly.GetExecutingAssembly().Location,temporary);Process.Start(new ProcessStartInfo(temporary,"--remove"){UseShellExecute=true});return 0;}
    if(args.Length!=1||args[0]!="--remove")return 1;
    if(MessageBox.Show("Uninstall AgroSentinel from this laptop?","AgroSentinel",MessageBoxButtons.YesNo,MessageBoxIcon.Question)!=DialogResult.Yes)return 0;
    Locations.DeleteOwned(Locations.Target);
    if(File.Exists(Locations.StartMenu))File.Delete(Locations.StartMenu);if(File.Exists(Locations.Desktop))File.Delete(Locations.Desktop);
    Registry.CurrentUser.DeleteSubKeyTree(Locations.RegistryPath,false);MessageBox.Show("AgroSentinel has been uninstalled.","AgroSentinel");return 0;
   }catch(Exception ex){MessageBox.Show("Could not uninstall AgroSentinel. Close the app and try again.\n"+ex.Message,"AgroSentinel");return 1;}
#endif
  }
 }
}
