"""Build secret-free doctor and plant-hosting handoffs from pinned artifacts."""
import hashlib,json,shutil,zipfile
from pathlib import Path
REPO=Path(__file__).resolve().parent.parent
OUT=REPO.parent/"deliverables"
BACKEND=["run_detection.py","detect_and_upload.py","firebase_config.py","firebase_diagnostics.py","gps.py","runtime_config.py","detection_timing.py","verify_live_demo.py","demo_launcher.py","diagnose_api.py","plant_api.py","plant_inference.py","requirements-doctor.txt","test_live_demo.py","test_combined_demo.py","test_plant_api.py","test_firebase_diagnostics.py"]

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    selection=json.loads((REPO/"models/demo-selection.json").read_text())
    doctor=OUT/"AgroSentinel-Doctor-Demo";doctor.mkdir(parents=True,exist_ok=True)
    for relative in ["ai-backend","models","scripts","examples","mobile"]:(doctor/relative).mkdir(exist_ok=True)
    for name in BACKEND:shutil.copy2(REPO/"ai-backend"/name,doctor/"ai-backend"/name)
    for name in ["Setup-DoctorLaptop.ps1","Start-LiveDemo.ps1","Build-DemoMobile.ps1"]:shutil.copy2(REPO/"scripts"/name,doctor/"scripts"/name)
    packaged=json.loads(json.dumps(selection))
    for name,artifact in selection["artifacts"].items():
        source=(REPO/artifact["path"]).resolve()
        if sha(source)!=artifact["sha256"]:raise ValueError("Selected model hash mismatch")
        shutil.copy2(source,doctor/"models"/name)
        packaged["artifacts"][name]["original_source"]=artifact["path"]
        packaged["artifacts"][name]["path"]="models/"+name
    (doctor/"models/demo-selection.json").write_text(json.dumps(packaged,indent=2))
    for report in (REPO/"models").glob("demo-*.json"):
        if report.name!="demo-selection.json":shutil.copy2(report,doctor/"models"/report.name)
    shutil.copy2(REPO/"docs/DOCTOR_DEMO_HANDOFF.md",doctor/"READ-ME.md")
    shutil.copy2(REPO/"docs/LAPTOP_FIRE_AND_PLANT.md",doctor/"LAPTOP_FIRE_AND_PLANT.md")
    (doctor/"SETUP.cmd").write_text('@echo off\r\npowershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\\Setup-DoctorLaptop.ps1"\r\npause\r\n', newline="")
    (doctor/"START_DEMO.cmd").write_text('@echo off\r\nif not exist "%~dp0.venv\\Scripts\\pythonw.exe" (echo Run SETUP.cmd first. & pause & exit /b 1)\r\nstart "AgroSentinel" "%~dp0.venv\\Scripts\\pythonw.exe" "%~dp0ai-backend\\demo_launcher.py"\r\n', newline="")
    (doctor/"mobile/READ-ME.txt").write_text("No new APK has been built in this environment. Build it from the source repository with scripts/Build-DemoMobile.ps1, then place the resulting APK here before handoff. Do not give the doctor an old APK as if it includes the new bundled on-device model.\n")
    shutil.copy2(REPO/"docs/MOBILE_ON_DEVICE_HANDOFF.md",doctor/"mobile/MOBILE_ON_DEVICE_HANDOFF.md")
    for old,new in [("fire-photo.jpg","wildfire.jpg"),("field-photo.jpg","field-negative.jpg"),("leaf-photo.jpg","leaf-negative.jpg")]:shutil.copy2(REPO/"presentation-web/wwwroot/images"/old,doctor/"examples"/new)
    tomato=json.loads((REPO/"models/demo-tomato-smoke-checks.json").read_text())
    for i,row in enumerate(tomato):shutil.copy2(REPO.parent/row["image"],doctor/"examples"/(f"tomato-{i+1}-"+row["expected"]+".jpg"))
    (doctor/"examples/READ-ME.txt").write_text("Wildfire, field and leaf photographs are the existing licensed website examples; see source project's PHOTO-CREDITS.md. Tomato examples are the six existing PlantWild test samples used in the recorded rehearsal check; see reports for expected labels, original paths and predictions. These are recordings/photographs, not live camera evidence.\n")
    cloud=OUT/"AgroSentinel-Plant-Cloud-Context";cloud.mkdir(parents=True,exist_ok=True)
    for folder in ["ai-backend","models"]:(cloud/folder).mkdir(exist_ok=True)
    for name in ["plant_api.py","plant_inference.py","runtime_config.py","firebase_config.py"]:shutil.copy2(REPO/"ai-backend"/name,cloud/"ai-backend"/name)
    for name in ["Dockerfile",".dockerignore","README.md"]:shutil.copy2(REPO/"deployment/plant-photo-api"/name,cloud/name)
    shutil.copy2(REPO/"ai-backend/requirements-doctor.txt",cloud/"requirements-doctor.txt")
    shutil.copy2(doctor/"models/plant_disease_best.pt",cloud/"models/plant_disease_best.pt")
    cloud_manifest={**packaged,"artifacts":{"plant_disease_best.pt":packaged["artifacts"]["plant_disease_best.pt"]}}
    (cloud/"models/demo-selection.json").write_text(json.dumps(cloud_manifest,indent=2))
    for folder,archive in [(doctor,OUT/"AgroSentinel-Doctor-Demo.zip"),(cloud,OUT/"AgroSentinel-Plant-Cloud-Context.zip")]:
        files=sorted(p for p in folder.rglob("*") if p.is_file() and not any(part in {"__pycache__", ".venv", "runtime"} for part in p.relative_to(folder).parts) and p.suffix not in {".pyc", ".pyo"})
        for path in files:
            if path.name.lower().startswith("serviceaccount") or ".secrets" in path.parts or path.suffix in [".pem",".key"]:raise ValueError("Credential unexpectedly present in handoff")
        with zipfile.ZipFile(archive,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=3) as z:
            for path in files:z.write(path,path.relative_to(folder).as_posix())
        with zipfile.ZipFile(archive) as z:
            if z.testzip() is not None:raise ValueError("Archive integrity failure")
        print(json.dumps({"archive":str(archive),"bytes":archive.stat().st_size,"files":len(files),"private_credentials_included":False}))

if __name__=="__main__":main()
