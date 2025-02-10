import tkinter as tk
import threading
import os
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse as urlparse
from tools import get_mac_address, load_devices, save_devices
from config import hostName, serverPort, devices_file
from gui import DeviceGUI


# Custom request handler class
class MyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse.urlparse(self.path)
        print(f"received GET")
        if parsed_path.path == "/register":
            """ Register the device without requiring 'rows' and 'columns' """
            device_ip = self.client_address[0]
            print(f"registering {device_ip}")
            mac_address = get_mac_address(device_ip)

            if not mac_address:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(b"Failed to retrieve MAC address.\n")
                return

            devices = load_devices()
            if mac_address not in devices:
                devices[mac_address] = {"ip": device_ip, "entries": []}
                save_devices(devices)

            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Device registered successfully.\n")

        elif parsed_path.path == "/devices":
            """ Return all registered devices in JSON format """
            devices = load_devices()
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(bytes(json.dumps(devices, indent=4), "utf-8"))

        elif parsed_path.path == "/device_config":
            """ ESP32 requests its configuration (rows & columns) """
            device_ip = self.client_address[0]
            mac_address = get_mac_address(device_ip)

            if not mac_address:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(b"Failed to retrieve MAC address.\n")
                return

            devices = load_devices()
            if mac_address in devices and devices[mac_address]["rows"] and devices[mac_address]["columns"]:
                config = devices[mac_address]  # Assuming one config per device
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(bytes(json.dumps(config), "utf-8"))
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"Configuration not found.\n")

        else:
            self.send_response(404)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Not Found.\n")


# Start the HTTP server in a separate thread
def start_server():
    webServer = HTTPServer((hostName, serverPort), MyServer)
    print(f"Server started http://{hostName}:{serverPort}")
    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass
    webServer.server_close()
    print("Server stopped.")

# Main execution
if __name__ == "__main__":
    if not os.path.exists(devices_file):
        with open(devices_file, "w") as f:
            json.dump({}, f)

    threading.Thread(target=start_server, daemon=True).start()
    root = tk.Tk()
    app = DeviceGUI(root)
    root.mainloop()
