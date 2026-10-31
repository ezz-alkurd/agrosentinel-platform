"""Export the pinned tomato checkpoint and verify ONNX prediction parity."""
import argparse,sys,json,hashlib
from pathlib import Path
import numpy as np
import torch
from PIL import Image, ImageOps

class Probabilities(torch.nn.Module):
    def __init__(self,model):super().__init__();self.model=model
    def forward(self,x):
        result=self.model(x)
        return result[0] if isinstance(result,tuple) else result

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dependency-dir",help="Optional existing Python 3.11 ONNX dependency directory")
    args=parser.parse_args()
    if args.dependency_dir:sys.path.append(args.dependency_dir)
    import onnx,onnxruntime as ort
    repo=Path(__file__).resolve().parent.parent
    sys.path.insert(0,str(repo/"ai-backend"))
    from runtime_config import resolve_model
    from ultralytics import YOLO
    source=resolve_model("plant_disease_best.pt")
    model=YOLO(str(source))
    assert list(model.names.values())==["Tomato_Early_blight","Tomato_Late_blight","Tomato_healthy"]
    network=Probabilities(model.model.float().eval()).eval()
    target=repo/"app/assets/models/tomato_closeup.onnx";target.parent.mkdir(parents=True,exist_ok=True)
    torch.onnx.export(network,torch.zeros(1,3,224,224),str(target),opset_version=17,input_names=["images"],output_names=["probabilities"],dynamic_axes=None,dynamo=False)
    graph=onnx.load(str(target));onnx.checker.check_model(graph)
    session=ort.InferenceSession(str(target),providers=["CPUExecutionProvider"])
    checks=[]
    dataset=repo.parent/"data/plant/prepared/v1/ground_classification/test"
    for folder in ["tomato_early_blight","tomato_late_blight"]:
        for path in sorted((dataset/folder).glob("*"))[:3]:
            image=ImageOps.exif_transpose(Image.open(path)).convert("RGB");w,h=image.size
            if w<h:nw,nh=224,int(224*h/w)
            else:nw,nh=int(224*w/h),224
            image=image.resize((nw,nh),Image.Resampling.BILINEAR)
            x,y=round((nw-224)/2),round((nh-224)/2)
            image=image.crop((x,y,x+224,y+224))
            tensor=np.asarray(image).astype(np.float32).transpose(2,0,1)[None]/255
            with torch.no_grad():reference=network(torch.from_numpy(tensor)).numpy()
            actual=session.run(None,{"images":tensor})[0]
            delta=float(np.max(np.abs(reference-actual)))
            assert delta<1e-4 and reference.argmax()==actual.argmax()
            checks.append({"image":path.name,"max_probability_difference":delta,"probabilities":actual[0].tolist()})
    if len(checks) != 6: raise RuntimeError("Expected six real comparison photos; restore the rehearsal dataset before exporting")
    metadata={"model_id":"plant-closeup-demo-tomato-3","version":"2026-10-24","sha256":hashlib.sha256(target.read_bytes()).hexdigest(),"source_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),"input_name":"images","output_name":"probabilities","input_shape":[1,3,224,224],"labels":["Tomato___Early_blight","Tomato___Late_blight","Tomato___healthy"],"threshold":0.90,"preprocessing":"EXIF orientation; RGB; Pillow bilinear short-edge resize 224; center crop 224 with ties-to-even offsets; NCHW float32 /255; mean 0, std 1","supported_crop":"tomato","limitations":"Legacy model. Close-up tomato leaves only; no general-field or out-of-distribution validation.","onnx_bytes":target.stat().st_size,"export_checks":checks}
    (target.parent/"tomato_closeup.json").write_text(json.dumps(metadata,indent=2),encoding="utf-8")
    print(json.dumps({"model":str(target),"bytes":target.stat().st_size,"parity_samples":len(checks),"max_difference":max(r["max_probability_difference"] for r in checks)}),flush=True)

if __name__=="__main__":main()
