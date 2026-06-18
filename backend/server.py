import http.server
import socketserver
import json
import threading
import subprocess
from concurrent.futures import ThreadPoolExecutor

from const import PORT, VENDORS
from scanner import get_local_ip, is_private_ip, get_mac_mapping, get_hostname
from fingerprint import check_ports

class ThreadedHTTPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True

class SSEHandler(http.server.BaseHTTPRequestHandler):
    def end_headers(self):
        origin = self.headers.get('Origin')
        if origin and (origin.startswith('http://localhost') or origin.startswith('http://127.0.0.1')):
            self.send_header('Access-Control-Allow-Origin', origin)
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('Content-Security-Policy', "default-src 'self'")
        super().end_headers()

    def do_GET(self):
        if self.path == '/scan':
            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream')
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.send_header('Connection', 'keep-alive')
            self.end_headers()

            local_ip = get_local_ip()
            if not is_private_ip(local_ip):
                err_msg = {"error": True, "message": "Public interface scanning blocked for security"}
                try:
                    self.wfile.write(f"data: {json.dumps(err_msg)}\n\n".encode('utf-8'))
                    self.wfile.flush()
                except Exception:
                    pass
                return

            prefix = ".".join(local_ip.split('.')[:-1]) + "."
            arp_table = get_mac_mapping()
            
            progress_lock = threading.Lock()
            progress_count = 0

            def scan_host(i):
                nonlocal progress_count
                ip = f"{prefix}{i}"
                is_up = subprocess.run(['ping', '-n', '1', '-w', '150', ip], stdout=subprocess.DEVNULL, shell=False).returncode == 0
                
                with progress_lock:
                    progress_count += 1
                    progress_msg = {"progress": True, "count": progress_count}
                    try:
                        self.wfile.write(f"data: {json.dumps(progress_msg)}\n\n".encode('utf-8'))
                        self.wfile.flush()
                    except Exception:
                        return

                if is_up:
                    mac = arp_table.get(ip, "00:00:00:00:00:00")
                    ports_data = check_ports(ip)
                    data = {
                        "ip": ip, 
                        "mac": mac, 
                        "name": get_hostname(ip), 
                        "vendor": VENDORS.get(mac[:8], "Generic"),
                        "ports": ports_data
                    }
                    try:
                        self.wfile.write(f"data: {json.dumps(data)}\n\n".encode('utf-8'))
                        self.wfile.flush()
                    except Exception:
                        return

            with ThreadPoolExecutor(max_workers=50) as executor:
                executor.map(scan_host, range(1, 255))
            
            try:
                self.wfile.write(b"data: {\"done\": true}\n\n")
                self.wfile.flush()
            except Exception:
                pass
        else:
            self.send_error(404)

if __name__ == '__main__':
    with ThreadedHTTPServer(("127.0.0.1", PORT), SSEHandler) as httpd:
        httpd.serve_forever()