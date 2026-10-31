"""Local authenticated plant photo API. The same app is hosted with Gunicorn."""
import argparse, socket, threading, time
from pathlib import Path
from socketserver import ThreadingMixIn
from wsgiref.simple_server import WSGIServer, WSGIRequestHandler, make_server
from plant_api import create_app

class Server(ThreadingMixIn, WSGIServer):
    daemon_threads=True
    def get_request(self):
        connection,address=super().get_request()
        connection.settimeout(20)
        return connection,address

class Handler(WSGIRequestHandler):
    def log_message(self, *args): pass

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host",default="127.0.0.1")
    parser.add_argument("--port",type=int,default=8008)
    parser.add_argument("--stop-file")
    args=parser.parse_args()
    application=create_app()
    with make_server(args.host,args.port,application,server_class=Server,handler_class=Handler) as server:
        print(f"Plant API listening on {args.host}:{args.port}; Firebase sign-in is required.",flush=True)
        print("For phone access on the same WiFi, explicitly use --host 0.0.0.0 and your laptop LAN IP.",flush=True)
        if args.stop_file:
            def watch_stop():
                while not Path(args.stop_file).exists(): time.sleep(.3)
                server.shutdown()
            threading.Thread(target=watch_stop,daemon=True).start()
        server.serve_forever()

if __name__=="__main__": main()
