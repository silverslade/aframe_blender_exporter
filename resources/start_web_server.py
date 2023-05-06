import sys
import time
import threading
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler

ip = "127.0.0.1"
port = 3600
url = f"http://{ip}:{port}"
server_address = (ip, port)

httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)

def start_server():
    httpd.serve_forever()

t = threading.Thread(target=start_server).start()
webbrowser.open_new(url)

print("-------------------------------------------------------------------")
print("Starting web server at "+url+", CTRL + C to stop and close")
print("-------------------------------------------------------------------")

while True:
    try:
        time.sleep(1)
    except KeyboardInterrupt:
        httpd.shutdown()
        sys.exit(0)
