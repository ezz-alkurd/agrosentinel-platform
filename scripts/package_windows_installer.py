"""Create a verified installer payload from the already-built portable app."""
from pathlib import Path
import hashlib,json,sys,zipfile
repo=Path(__file__).resolve().parent.parent
source=repo/'artifacts/AgroSentinel-Windows'
work=repo/'runtime/installer-build'
work.mkdir(parents=True,exist_ok=True)
for relative in ['AgroSentinel.exe','app/AgroSentinel.dll','worker/AgroSentinel.Worker.exe','runtime/dotnet.exe','models/demo-selection.json']:
    if not (source/relative).is_file():raise SystemExit('Build the Windows application first: missing '+relative)
files=sorted(p for p in source.rglob('*') if p.is_file())
if any(p.name in {'appsettings.Production.json','connection.bin'} for p in files):raise SystemExit('Private settings must not be bundled in the installer.')
selection=json.loads((source/'models/demo-selection.json').read_text())
for item in selection['artifacts'].values():
    if hashlib.sha256((source/item['path']).read_bytes()).hexdigest()!=item['sha256']:raise SystemExit('Bundled model checksum mismatch.')
payload=work/'payload.zip'
with zipfile.ZipFile(payload,'w',zipfile.ZIP_DEFLATED,compresslevel=1,allowZip64=True) as archive:
    archive.writestr('AgroSentinel-Windows/.agrosentinel-install','AgroSentinel.Desktop.Install.v1\n')
    for path in files:archive.write(path,'AgroSentinel-Windows/'+path.relative_to(source).as_posix())
    archive.write(work/'Uninstall.exe','AgroSentinel-Windows/Uninstall.exe')
sha=hashlib.sha256()
with payload.open('rb') as stream:
    for chunk in iter(lambda:stream.read(1024*1024),b''):sha.update(chunk)
(work/'ReleaseInfo.cs').write_text('namespace AgroSentinel.Setup { static class ReleaseInfo { internal const string PayloadSha256="'+sha.hexdigest()+'"; } }\n',encoding='utf-8')
print('Installer payload:',len(files)+2,'files;',round(payload.stat().st_size/1024/1024,1),'MB',flush=True)
