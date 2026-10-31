"""Small Windows rehearsal launcher. Does not simulate events or phone delivery."""
import os,queue,subprocess,sys,threading,uuid
from pathlib import Path
import tkinter as tk
from tkinter import ttk,filedialog,messagebox
ROOT=Path(__file__).resolve().parent.parent

PROFILES = ("Fire + tomato leaves", "Fire only", "Tomato leaves only")


def detection_arguments(mode, source, profile, backend):
    if mode == "Read-only connection check":
        return [str(backend / "verify_live_demo.py"), "--firebase"]
    if profile not in PROFILES:
        raise ValueError("Choose a detection profile.")
    args = [str(backend / "run_detection.py"), "--backend", "firebase"]
    if mode == "Single recorded image":
        args += ["--image", source]
    elif mode == "Camera or recorded video":
        args += ["--source", source, "--name", "Laptop detection"]
    else:
        raise ValueError("Choose a source mode.")
    if profile == "Fire only": args += ["--no-disease"]
    if profile == "Tomato leaves only": args += ["--no-fire"]
    return args


class Launcher:
    def __init__(self,window):
        self.window=window;self.process=None;self.events=queue.Queue();self.stop_path=None
        window.title("AgroSentinel | Laptop to phone");window.geometry("900x700")
        box=ttk.Frame(window,padding=22);box.pack(fill="both",expand=True)
        ttk.Label(box,text="AgroSentinel",font=("Segoe UI",24,"bold")).pack(anchor="w")
        ttk.Label(box,text="Fire / tomato disease -> Firebase event -> signed-in phone app",font=("Segoe UI",11)).pack(anchor="w",pady=(4,15))
        ttk.Label(box,text="Plant scope: one close-up tomato leaf filling the frame. Early blight / late blight / healthy.").pack(anchor="w")
        ttk.Label(box,text="Phone alerts here mean the foreground Alerts / Events feed; background push is separate.").pack(anchor="w",pady=(3,15))
        self.mode=tk.StringVar(value="Read-only connection check")
        ttk.Combobox(box,textvariable=self.mode,state="readonly",values=["Read-only connection check","Camera or recorded video","Single recorded image"]).pack(fill="x",pady=(0,12))
        self.profile=tk.StringVar(value=PROFILES[0])
        ttk.Label(box,text="Detection models").pack(anchor="w")
        ttk.Combobox(box,textvariable=self.profile,state="readonly",values=PROFILES).pack(fill="x",pady=(3,12))
        row=ttk.Frame(box);row.pack(fill="x")
        ttk.Label(row,text="Camera index / source").pack(side="left")
        self.source=tk.StringVar(value="0");ttk.Entry(row,textvariable=self.source).pack(side="left",fill="x",expand=True,padx=10)
        ttk.Button(row,text="Browse",command=self.browse).pack(side="left")
        row=ttk.Frame(box);row.pack(fill="x",pady=12)
        ttk.Label(row,text="Private Firebase key").pack(side="left")
        self.key=tk.StringVar(value=str(ROOT/".secrets/serviceAccountKey.json"))
        ttk.Entry(row,textvariable=self.key).pack(side="left",fill="x",expand=True,padx=10)
        ttk.Button(row,text="Choose",command=self.choose_key).pack(side="left")
        controls=ttk.Frame(box);controls.pack(fill="x",pady=(0,12))
        self.start_button=ttk.Button(controls,text="Start",command=self.start);self.start_button.pack(side="left")
        self.stop_button=ttk.Button(controls,text="Stop",command=self.stop,state="disabled");self.stop_button.pack(side="left",padx=10)
        self.status=tk.StringVar(value="Ready — first run the read-only check.");ttk.Label(controls,textvariable=self.status).pack(side="left",padx=10)
        self.log=tk.Text(box,wrap="word",font=("Consolas",10),state="disabled");self.log.pack(fill="both",expand=True)
        self.window.after(150,self.poll);window.protocol("WM_DELETE_WINDOW",self.close)
    def browse(self):
        path=filedialog.askopenfilename(title="Choose an existing recording or image")
        if path:self.source.set(path)
    def choose_key(self):
        path=filedialog.askopenfilename(filetypes=[("Service-account JSON","*.json")])
        if path:self.key.set(path)
    def start(self):
        if self.process and self.process.poll() is None:return
        key=Path(self.key.get())
        if not key.is_file():messagebox.showerror("Configuration needed","Choose the separately supplied private Firebase credential. It is not included in the handoff ZIP.");return
        env=os.environ.copy();env["FIREBASE_KEY_PATH"]=str(key);env["YOLO_CONFIG_DIR"]=str(ROOT/"runtime/ultralytics");env["PYTHONUTF8"]="1";env["PYTHONUNBUFFERED"]="1"
        mode=self.mode.get();backend=ROOT/"ai-backend"
        args=detection_arguments(mode,self.source.get(),self.profile.get(),backend)
        if mode != "Read-only connection check":
            self.events.put("Models: " + self.profile.get())
            self.events.put("Plant matches apply only to close-up tomato leaves; confidence does not reject unrelated objects.")
        python=Path(sys.executable)
        if python.name.lower()=="pythonw.exe":python=python.with_name("python.exe")
        self.stop_path=ROOT/"runtime"/("stop-"+uuid.uuid4().hex)
        self.stop_path.parent.mkdir(parents=True,exist_ok=True)
        if mode!="Read-only connection check":args += ["--stop-file",str(self.stop_path)]
        flags=subprocess.CREATE_NO_WINDOW if os.name=="nt" else 0
        self.process=subprocess.Popen([str(python),*args],cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding="utf-8",errors="replace",creationflags=flags)
        process=self.process
        self.status.set("Running — phone receipt is verified on the phone.");self.start_button.config(state="disabled");self.stop_button.config(state="normal")
        def read():
            for line in process.stdout:self.events.put(line.rstrip())
            self.events.put(f"Process exited with code {process.wait()}.")
        threading.Thread(target=read,daemon=True).start()
    def poll(self):
        while not self.events.empty():
            line=self.events.get();self.log.config(state="normal");self.log.insert("end",line+"\n");self.log.see("end");self.log.config(state="disabled")
        if self.process and self.process.poll() is not None:
            self.status.set("Finished. Check the log and the actual phone.");self.start_button.config(state="normal");self.stop_button.config(state="disabled")
        self.window.after(150,self.poll)
    def stop(self):
        if self.process and self.process.poll() is None:
            if self.stop_path:self.stop_path.write_text("stop",encoding="ascii")
            self.status.set("Stopping; waiting for pending uploads.")
    def close(self):
        if self.process and self.process.poll() is None:
            self.stop();messagebox.showinfo("Stopping","Wait for the process to finish, then close the launcher.");return
        self.window.destroy()

if __name__=="__main__":
    window=tk.Tk();Launcher(window);window.mainloop()
