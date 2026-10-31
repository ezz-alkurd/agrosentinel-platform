"""Assemble private runtime, selected models and packaged worker; no credentials."""
import hashlib,json,shutil,sys
from pathlib import Path
repo=Path(__file__).resolve().parent.parent
out=repo/'artifacts/AgroSentinel-Windows';out.mkdir(parents=True,exist_ok=True)
dotnet=Path(r'C:\Program Files\dotnet')
for relative in ['dotnet.exe','host/fxr/10.0.12','shared/Microsoft.NETCore.App/10.0.12','shared/Microsoft.WindowsDesktop.App/10.0.12']:
 source=dotnet/relative;target=out/'runtime'/relative
 target.parent.mkdir(parents=True,exist_ok=True)
 if source.is_dir():shutil.copytree(source,target,dirs_exist_ok=True)
 else:shutil.copy2(source,target)
selection=json.loads((repo/'models/demo-selection.json').read_text())
(out/'models').mkdir(exist_ok=True)
for name,item in selection['artifacts'].items():
 source=(repo/item['path']).resolve()
 if hashlib.sha256(source.read_bytes()).hexdigest()!=item['sha256']:raise ValueError('Model checksum mismatch')
 shutil.copy2(source,out/'models'/name);item['path']='models/'+name
(out/'models/demo-selection.json').write_text(json.dumps(selection,indent=2))
if len(sys.argv)>1:shutil.copytree(Path(sys.argv[1]),out/'worker',dirs_exist_ok=True)
print(out)
