from pathlib import Path
import importlib.util
from PyInstaller.utils.hooks import collect_data_files, collect_submodules
repo=Path(SPEC).resolve().parent.parent
# charset_normalizer wheels can depend on a hashed mypy runtime at site-packages root.
site_packages=Path(importlib.util.find_spec('charset_normalizer').origin).parent.parent
charset_binaries=[(str(p),'.') for p in site_packages.glob('*__mypyc*.pyd')]
a=Analysis([str(repo/'ai-backend/run_detection.py')],pathex=[str(repo/'ai-backend')],binaries=charset_binaries,datas=collect_data_files('ultralytics'),hiddenimports=collect_submodules('ultralytics.nn')+['api_transport','runtime_config','detection_timing','gps'],hookspath=[],hooksconfig={'matplotlib':{'backends':['Agg']}},runtime_hooks=[],excludes=['tensorflow','keras','tensorboard','IPython','notebook','jupyter','tkinter','PyQt5','PyQt6','PySide2','PySide6','firebase_admin','google','detect_and_upload','firebase_config','firebase_diagnostics'],noarchive=False)
pyz=PYZ(a.pure)
exe=EXE(pyz,a.scripts,[],exclude_binaries=True,name='AgroSentinel.Worker',debug=False,strip=False,upx=False,console=True)
coll=COLLECT(exe,a.binaries,a.datas,strip=False,upx=False,name='AgroSentinel.Worker')
