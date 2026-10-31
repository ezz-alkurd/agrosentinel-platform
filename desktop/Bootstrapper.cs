using System;using System.IO;using System.Diagnostics;using System.Windows.Forms;
class Bootstrapper {
 [STAThread] static void Main(){try{string root=AppDomain.CurrentDomain.BaseDirectory;var info=new ProcessStartInfo(Path.Combine(root,"runtime","dotnet.exe"),"\""+Path.Combine(root,"app","AgroSentinel.dll")+"\"");info.UseShellExecute=false;info.CreateNoWindow=true;info.WorkingDirectory=root;info.EnvironmentVariables["DOTNET_ROOT"]=Path.Combine(root,"runtime");info.EnvironmentVariables["DOTNET_MULTILEVEL_LOOKUP"]="0";Process.Start(info);}catch(Exception error){MessageBox.Show("Keep the complete application folder together.\n"+error.Message,"AgroSentinel");}}
}
