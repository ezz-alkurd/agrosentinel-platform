import json,tempfile,unittest
from pathlib import Path
from unittest.mock import Mock
import numpy as np
import requests
from api_transport import ApiTransport,DeliveryPending,validate_base_url
class ApiTransportTests(unittest.TestCase):
 def client(self,folder,response=200):
  session=Mock();session.headers={};session.request.return_value.status_code=response
  client=ApiTransport('https://example.invalid','a'*43,folder,session_factory=lambda:session,start_worker=False)
  return client,session
 def test_failed_upload_survives_restart_with_same_event_id(self):
  with tempfile.TemporaryDirectory() as folder:
   client,session=self.client(folder,503)
   with self.assertRaises(DeliveryPending):client.submit(np.zeros((20,20,3),dtype=np.uint8),'fire',.9,0,0,event_context={'confirmation_mode':'single_image'})
   files=list(client.root.glob('*/metadata.json'));self.assertEqual(len(files),1)
   event=json.loads(files[0].read_text());self.assertIsNone(event['gps_lat'])
   again,session2=self.client(folder);again.flush()
   sent=json.loads(session2.request.call_args.kwargs['data']['metadata'])
   self.assertEqual(sent['id'],event['id']);self.assertEqual(list(again.root.glob('*/metadata.json')),[])
 def test_device_credentials_are_headers_and_never_saved_in_outbox(self):
  with tempfile.TemporaryDirectory() as folder:
   client,session=self.client(folder,401)
   with self.assertRaises(DeliveryPending):client.submit(np.zeros((20,20,3),dtype=np.uint8),'Tomato___Late_blight',.96,0,0,kind='disease')
   raw=list(client.root.glob('*/metadata.json'))[0].read_text()
   self.assertNotIn(client.token,raw);self.assertEqual(session.headers['Authorization'],'Device '+client.token)
   self.assertEqual(json.loads(raw)['anomaly_type'],'disease')
 def test_repairing_does_not_upload_previous_accounts_queue(self):
  with tempfile.TemporaryDirectory() as folder:
   first,_=self.client(folder)
   other=ApiTransport('https://example.invalid','b'*43,folder,start_worker=False)
   self.assertNotEqual(first.root,other.root)
 def test_crop_validation_prevents_empty_evidence(self):
  with tempfile.TemporaryDirectory() as folder:
   client,session=self.client(folder)
   with self.assertRaises(ValueError):client.submit(np.zeros((20,20,3),dtype=np.uint8),'fire',.9,0,0,[5,5,5,5])
   session.request.assert_not_called()
 def test_upload_uses_original_source_and_model_checksum(self):
  with tempfile.TemporaryDirectory() as folder:
   client,session=self.client(folder)
   client.submit(np.zeros((20,20,3),dtype=np.uint8),'fire',.9,0,0,event_context={'source_type':'Recorded image','confirmation_mode':'single_image','fire_model_sha256':'f'*64})
   body=json.loads(session.request.call_args.kwargs['data']['metadata'])
   self.assertEqual(body['source_type'],'Recorded image');self.assertEqual(body['fire_model_sha256'],'f'*64)
 def test_insecure_remote_url_is_rejected(self):
  for url in ['http://example.com','https://u:p@example.com','https://example.com?token=secret']:
   with self.assertRaises(ValueError):validate_base_url(url)
  self.assertEqual(validate_base_url('http://127.0.0.1:5000/'),'http://127.0.0.1:5000')
if __name__=='__main__':unittest.main()
