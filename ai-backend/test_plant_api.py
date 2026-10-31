import io,json,unittest
from plant_api import PlantApplication,Unauthorized,AuthUnavailable

class Engine:
    def metadata(self): return {"id":"test"}
    def analyze(self,data): return {"status":"prediction","label":"Tomato___Late_blight","confidence":.95}

def request(app,path="/diagnose",method="POST",token="Bearer test",body=b"image",length=None,content_type="image/jpeg"):
    response=[]
    environ={"PATH_INFO":path,"REQUEST_METHOD":method,"HTTP_AUTHORIZATION":token,"CONTENT_TYPE":content_type,"CONTENT_LENGTH":str(len(body) if length is None else length),"wsgi.input":io.BytesIO(body)}
    payload=b"".join(app(environ,lambda status,headers:response.append((status,headers))))
    return response[0][0],json.loads(payload)

class ApiTests(unittest.TestCase):
    def setUp(self):self.app=PlantApplication(Engine(),lambda token:{"uid":"unit-test-only"})
    def test_health_reports_actual_engine(self):self.assertEqual(request(self.app,"/health","GET")[1]["model"]["id"],"test")
    def test_missing_auth_is_rejected(self):self.assertTrue(request(self.app,token="")[0].startswith("401"))
    def test_invalid_token_is_rejected(self):
        def reject(token):raise Unauthorized()
        self.assertTrue(request(PlantApplication(Engine(),reject))[0].startswith("401"))
    def test_auth_connection_failure_is_unavailable_not_bad_credentials(self):
        def fail(token):raise AuthUnavailable()
        self.assertTrue(request(PlantApplication(Engine(),fail))[0].startswith("503"))
    def test_large_image_rejected_before_body_read(self):self.assertTrue(request(self.app,length=9*1024*1024)[0].startswith("413"))
    def test_empty_image_rejected(self):self.assertTrue(request(self.app,body=b"")[0].startswith("400"))
    def test_incomplete_image_rejected(self):self.assertTrue(request(self.app,length=100)[0].startswith("400"))
    def test_wrong_method_rejected(self):self.assertTrue(request(self.app,method="GET")[0].startswith("405"))
    def test_raw_image_contract(self):self.assertEqual(request(self.app)[1]["label"],"Tomato___Late_blight")
    def test_unknown_path(self):self.assertTrue(request(self.app,path="/unknown")[0].startswith("404"))

if __name__=="__main__":unittest.main()
