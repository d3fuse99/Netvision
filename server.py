import http.server, socketserver, subprocess, json, re, socket, time, threading
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
    except: ip = '127.0.0.1'
    finally: s.close()
    return ip

def get_hostname(ip):
    try: return socket.gethostbyaddr(ip)[0]
    except: return "Unknown Node"

def get_mac_mapping():
    mapping = {}
    try:
        output = subprocess.check_output(("arp", "-a")).decode('cp866')
        for line in output.split('\n'):
            match = re.search(r'(\d+\.\d+\.\d+\.\d+)\s+([0-9a-f-]+)', line)
            if match:
                mapping[match.group(1)] = match.group(2).replace('-', ':').upper()
    except: pass
    return mapping

def grab_banner(ip, port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.3)
            s.connect((ip, port))
            if port == 22:
                return s.recv(1024).decode('utf-8', errors='ignore').strip()
            elif port == 80:
                s.sendall(b"GET / HTTP/1.1\r\nHost: " + ip.encode() + b"\r\n\r\n")
                response = s.recv(1024).decode('utf-8', errors='ignore')
                for line in response.split('\r\n'):
                    if line.upper().startswith("SERVER:"):
                        return line
    except: pass
    return "Unknown Service"

def check_ports(ip):
    ports_to_check = {22: "SSH", 80: "HTTP", 443: "HTTPS", 445: "SMB"}
    open_ports = {}
    for port, service in ports_to_check.items():
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.1)
                if s.connect_ex((ip, port)) == 0:
                    banner = grab_banner(ip, port)
                    open_ports[str(port)] = {"service": service, "banner": banner}
        except: pass
    return open_ports

class ThreadedHTTPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True

class SSEHandler(http.server.BaseHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

    def do_GET(self):
        if self.path == '/scan':
            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream')
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('Connection', 'keep-alive')
            self.end_headers()

            prefix = ".".join(get_local_ip().split('.')[:-1]) + "."
            arp_table = get_mac_mapping()
            
            progress_lock = threading.Lock()
            progress_count = 0

            def scan_host(i):
                nonlocal progress_count
                ip = f"{prefix}{i}"
                is_up = subprocess.run(['ping', '-n', '1', '-w', '150', ip], stdout=subprocess.DEVNULL).returncode == 0
                
                with progress_lock:
                    progress_count += 1
                    progress_msg = {"progress": True, "count": progress_count}
                    try:
                        self.wfile.write(f"data: {json.dumps(progress_msg)}\n\n".encode())
                        self.wfile.flush()
                    except: return

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
                        self.wfile.write(f"data: {json.dumps(data)}\n\n".encode())
                        self.wfile.flush()
                    except: return

            with ThreadPoolExecutor(max_workers=50) as executor:
                executor.map(scan_host, range(1, 255))
            
            try:
                self.wfile.write(b"data: {\"done\": true}\n\n")
                self.wfile.flush()
            except: pass
        else: self.send_error(404)

print(f"Server started on port {PORT}")
with ThreadedHTTPServer(("", PORT), SSEHandler) as httpd:
    httpd.serve_forever()
