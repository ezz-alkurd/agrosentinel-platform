"""Firebase-authenticated WSGI photo API, also served locally by diagnose_api.py."""
import json
MAX_IMAGE_BYTES = 8 * 1024 * 1024

class Unauthorized(Exception): pass
class AuthUnavailable(Exception): pass

def verify_firebase_token(token):
    from firebase_config import initialize_firebase
    from firebase_admin import auth
    try:
        initialize_firebase()
        return auth.verify_id_token(token)
    except (auth.InvalidIdTokenError, auth.ExpiredIdTokenError, ValueError) as exc:
        raise Unauthorized() from exc
    except Exception as exc:
        raise AuthUnavailable() from exc

class PlantApplication:
    def __init__(self, engine, verifier=verify_firebase_token):
        self.engine, self.verifier = engine, verifier

    def __call__(self, environ, start_response):
        def reply(status, payload):
            data=json.dumps(payload).encode()
            headers=[("Content-Type","application/json"),("Content-Length",str(len(data))),
                     ("Cache-Control","no-store"),("X-Content-Type-Options","nosniff")]
            if status.startswith("503"): headers.append(("Retry-After","2"))
            start_response(status,headers)
            return [data]
        path=environ.get("PATH_INFO","").rstrip("/")
        method=environ.get("REQUEST_METHOD","")
        if path=="/health" and method=="GET":
            return reply("200 OK",{"status":"ok","model":self.engine.metadata(),"authentication":"firebase-id-token"})
        if path not in ("/diagnose","/api/v1/diagnose"):
            return reply("404 Not Found",{"error":"not_found"})
        if method!="POST": return reply("405 Method Not Allowed",{"error":"use_post"})
        auth_header=environ.get("HTTP_AUTHORIZATION","")
        if not auth_header.startswith("Bearer "):
            return reply("401 Unauthorized",{"error":"Sign in before analyzing a photo."})
        try:
            self.verifier(auth_header[7:])
        except Unauthorized:
            return reply("401 Unauthorized",{"error":"Your session expired. Sign in again."})
        except Exception:
            return reply("503 Service Unavailable",{"error":"Authentication service unavailable; retry later."})
        try: length=int(environ.get("CONTENT_LENGTH", "0"))
        except (TypeError,ValueError): return reply("400 Bad Request",{"error":"invalid_length"})
        if length<=0: return reply("400 Bad Request",{"error":"empty_image"})
        if length>MAX_IMAGE_BYTES: return reply("413 Payload Too Large",{"error":"Maximum image size is 8 MB."})
        content_type=environ.get("CONTENT_TYPE","").split(";")[0]
        if content_type not in ("application/octet-stream","image/jpeg","image/png","image/webp"):
            return reply("415 Unsupported Media Type",{"error":"Send raw JPEG, PNG or WebP bytes."})
        data=environ["wsgi.input"].read(length)
        if len(data)!=length: return reply("400 Bad Request",{"error":"incomplete_image"})
        try:
            return reply("200 OK",self.engine.analyze(data))
        except ValueError:
            return reply("400 Bad Request",{"error":"Invalid or unsupported image."})
        except RuntimeError:
            return reply("503 Service Unavailable",{"error":"Model busy; retry shortly."})
        except Exception:
            return reply("500 Internal Server Error",{"error":"Image analysis failed."})

def create_app():
    from plant_inference import PlantEngine
    return PlantApplication(PlantEngine())
