"""Authenticated ASP.NET transport with a durable local evidence outbox.
No Firebase admin credentials or SQL passwords are used by this client.
"""
import hashlib,json,os,threading,uuid
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlsplit
import cv2
import requests

class DeliveryPending(RuntimeError): pass

def validate_base_url(value):
    value=value.strip().rstrip('/')
    parsed=urlsplit(value)
    if parsed.username or parsed.password or parsed.query or parsed.fragment or not parsed.hostname:
        raise ValueError('Enter a website base URL without credentials, query or fragment.')
    if parsed.scheme!='https' and not(parsed.scheme=='http' and parsed.hostname in ('localhost','127.0.0.1','::1')):
        raise ValueError('The API needs HTTPS; loopback HTTP is allowed for development.')
    return value

class ApiTransport:
    def __init__(self,base_url,device_token,outbox=None,session_factory=requests.Session,start_worker=True):
        self.base_url=validate_base_url(base_url)
        if not 32<=len(device_token)<=128:raise ValueError('Pair this laptop with your phone before uploading.')
        self.token=device_token;self.factory=session_factory;self.sessions=threading.local();self.lock=threading.Lock();self.stopped=threading.Event()
        scope=hashlib.sha256((self.base_url+'\n'+device_token).encode()).hexdigest()[:20]
        base=Path(outbox or os.getenv('AGROSENTINEL_OUTBOX_DIR') or Path(__file__).resolve().parent.parent/'runtime/api-outbox')
        self.root=base/scope;self.root.mkdir(parents=True,exist_ok=True)
        self.worker=None
        if start_worker:
            self.worker=threading.Thread(target=self._retry,daemon=True);self.worker.start()
    @classmethod
    def from_environment(cls,**kwargs):
        return cls(os.getenv('AGROSENTINEL_API_URL',''),os.getenv('AGROSENTINEL_DEVICE_TOKEN',''),**kwargs)
    def session(self):
        if not hasattr(self.sessions,'http'):
            self.sessions.http=self.factory();self.sessions.http.headers.update({'Authorization':'Device '+self.token})
        return self.sessions.http
    def _request(self,method,path,**kwargs):
        response=self.session().request(method,self.base_url+'/api/v1'+path,timeout=(4,15),**kwargs)
        if response.status_code>=400:
            messages={401:'Device is unpaired or revoked; pair it again.',403:'This device cannot perform that operation.',409:'Event identity conflicts with previously stored content.',413:'Evidence exceeds the server upload limit.',429:'Server is busy; evidence remains queued.',503:'API or SQL Server is not configured or available.',507:'Server evidence storage is full.'}
            raise DeliveryPending(messages.get(response.status_code,f'API returned HTTP {response.status_code}; evidence remains queued.'))
        return response
    def submit(self,frame,label,confidence,lat,lng,bbox=None,event_context=None,kind='fire'):
        if not 0<=float(confidence)<=1:raise ValueError('Invalid confidence.')
        image=frame
        if bbox is not None:
            height,width=frame.shape[:2];x1,y1,x2,y2=map(int,bbox)
            x1=max(0,min(x1,width));x2=max(0,min(x2,width));y1=max(0,min(y1,height));y2=max(0,min(y2,height))
            if x2<=x1 or y2<=y1:raise ValueError('Empty evidence crop.')
            image=frame[y1:y2,x1:x2]
        ok,encoded=cv2.imencode('.jpg',image,[cv2.IMWRITE_JPEG_QUALITY,88])
        if not ok:raise ValueError('Cannot encode evidence image.')
        if len(encoded)>8*1024*1024:raise ValueError('Evidence exceeds 8 MB.')
        context=event_context or {};event_id=str(uuid.uuid4())
        metadata={'id':event_id,'anomaly_type':'disease' if kind=='disease' else label.lower(),'confidence':float(confidence),'gps_lat':float(lat) if(lat or lng) else None,'gps_lng':float(lng) if(lat or lng) else None,'captured_at':context.get('captured_at',datetime.now(timezone.utc).isoformat()),'disease_name':label if kind=='disease' else None,'source_type':context.get('source_type','Laptop camera'),'location_source':context.get('location_source','unavailable'),'confirmation_mode':context.get('confirmation_mode','continuous_2_seconds'),'fire_model_sha256':context.get('fire_model_sha256'),'plant_model_sha256':context.get('plant_model_sha256'),'plant_inference_kind':context.get('plant_inference_kind')}
        with self.lock:
            if len(list(self.root.glob('*/metadata.json')))>=500:raise RuntimeError('Local outbox is full (500 events). Restore sync before continuing.')
            temporary=self.root/('.'+event_id);temporary.mkdir()
            (temporary/'image.jpg').write_bytes(encoded.tobytes());(temporary/'metadata.json').write_text(json.dumps(metadata),encoding='utf-8');temporary.rename(self.root/event_id)
        print(f'[sync] Evidence queued locally: {event_id}',flush=True)
        self.flush()
    def flush(self):
        with self.lock:
            for item in sorted(self.root.glob('*/metadata.json'),key=lambda p:p.stat().st_mtime):
                if self.stopped.is_set():break
                folder=item.parent
                with (folder/'image.jpg').open('rb') as image:
                    self._request('POST','/events',data={'metadata':item.read_text(encoding='utf-8')},files={'image':('evidence.jpg',image,'image/jpeg')})
                event_id=folder.name
                (folder/'image.jpg').unlink();item.unlink();folder.rmdir()
                print(f'[sync] Uploaded to API: {event_id}',flush=True)
    def _retry(self):
        while not self.stopped.wait(8):
            try:self.flush()
            except Exception as error:print(f'[sync] Pending local evidence: {type(error).__name__}. Check API connectivity and pairing.',flush=True)
    def handle_fire_detection(self,frame,label,confidence,lat,lng,bbox=None,event_context=None):
        return self.submit(frame,label,confidence,lat,lng,bbox,event_context,'fire')
    def handle_disease_classification(self,frame,label,confidence,lat,lng,bbox=None,event_context=None):
        return self.submit(frame,label,confidence,lat,lng,bbox,event_context,'disease')
    def update_device_status(self,device_id,name,device_type,source,gps_lat,gps_lng,models,online=True,started_at=None):
        return self._request('POST','/agent/heartbeat',json={'name':name,'type':device_type,'source':str(source),'models':models,'online':online})
    def set_device_offline(self,device_id):
        self.stopped.set()
        try:self._request('POST','/agent/heartbeat',json={'name':os.getenv('AGROSENTINEL_DEVICE_NAME','Laptop'),'type':'Laptop camera','source':None,'models':[],'online':False})
        except Exception as error:print(f'[sync] Offline heartbeat unavailable: {type(error).__name__}. Presence will expire.',flush=True)
