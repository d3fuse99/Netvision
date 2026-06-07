import http.server
import socketserver
import subprocess
import json
import re
import socket
import platform
import threading
from concurrent.futures import ThreadPoolExecutor

PORT = 5005

VENDORS = {
    "84:D8:1B": "TP-Link", "00:0C:29": "VMware", "BC:D1:D3": "Apple",
    "40:8D:5C": "Samsung", "D8:07:B6": "Samsung", "9A:09:89": "Mobile",
    "B6:AA:47": "Generic", "D4:3A:2E": "Intel"
}

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def get_hostname(ip):
    try:
        resolved = socket.gethostbyaddr(ip)[0]
        return re.sub(r'[^\w\.\-\s]', '', resolved)
    except Exception:
        return "Unknown Node"

def get_mac_mapping():
    mapping = {}
    try:
        system_name = platform.system().lower()
        encoding = "cp866" if "windows" in system_name else "utf-8"
        output = subprocess.check_output(["arp", "-a"], shell=False).decode(encoding, errors="ignore")
        for line in output.split('\n'):
            ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
            mac_match = re.search(r'([0-9a-fA-F]{2}[:-][0-9a-fA-F]{2}[:-][0-9a-fA-F]{2}[:-][0-9a-fA-F]{2}[:-][0-9a-fA-F]{2}[:-][0-9a-fA-F]{2})', line)
            if ip_match and mac_match:
                ip = ip_match.group(1)
                mac = mac_match.group(1).replace('-', ':').upper()
                mapping[ip] = mac
    except Exception:
        pass
    return mapping

def grab_banner(ip, port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            s.connect((ip, port))
            if port == 22:
                banner = s.recv(1024).decode('utf-8', errors='ignore').strip()
                return re.sub(r'[^\w\.\-\s\:\/]', '', banner)
            elif port == 80:
                s.sendall(b"GET / HTTP/1.1\r\nHost: " + ip.encode() + b"\r\nConnection: close\r\n\r\n")
                response = s.recv(1024).decode('utf-8', errors='ignore')
                for line in response.split('\r\n'):
                    if line.upper().startswith("SERVER:"):
                        clean_line = re.sub(r'[^\w\.\-\s\:\/]', '', line)
                        return clean_line
    except Exception:
        pass
    return "Unknown Service"

def check_ports(ip):
    ports_to_check = {22: "SSH", 80: "HTTP", 443: "HTTPS", 445: "SMB"}
    open_ports = {}
    for port, service in ports_to_check.items():
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.3)
                if s.connect_ex((ip, port)) == 0:
                    banner = grab_banner(ip, port)
                    open_ports[str(port)] = {"service": service, "banner": banner}
        except Exception:
            pass
    return open_ports

class ThreadedHTTPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True

class SSEHandler(http.server.BaseHTTPRequestHandler):
    def end_headers(self):
        origin = self.headers.get('Origin')
        if origin:
            if origin.startswith('http://localhost') or origin.startswith('http://127.0.0.1') or origin == 'null':
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
            if local_ip == '127.0.0.1':
                self.send_error(500, "Internal Server Error: No active network interface detected")
                return

            prefix = ".".join(local_ip.split('.')[:-1]) + "."
            arp_table = get_mac_mapping()
            
            progress_lock = threading.Lock()
            progress_count = 0
            cancel_event = threading.Event()

            system_name = platform.system().lower()
            ping_cmd = ["ping", "-n", "1", "-w", "150"] if "windows" in system_name else ["ping", "-c", "1", "-W", "1"]

            def scan_host(i):
                nonlocal progress_count
                if cancel_event.is_set():
                    return

                ip = f"{prefix}{i}"
                is_up = subprocess.run(ping_cmd + [ip], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=False).returncode == 0
                
                with progress_lock:
                    progress_count += 1
                    progress_msg = {"progress": True, "count": progress_count}
                    try:
                        self.wfile.write(f"data: {json.dumps(progress_msg)}\n\n".encode('utf-8'))
                        self.wfile.flush()
                    except Exception:
                        cancel_event.set()
                        return

                if is_up and not cancel_event.is_set():
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
                        cancel_event.set()
                        return

            with ThreadPoolExecutor(max_workers=50) as executor:
                executor.map(scan_host, range(1, 255))
            
            if not cancel_event.is_set():
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