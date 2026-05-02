import http.server, socketserver, subprocess, json, re, socket, time, threading

PORT = 5005

VENDORS = {
    "84:D8:1B": "TP-Link", "00:0C:29": "VMware", "BC:D1:D3": "Apple",
    "40:8D:5C": "Samsung", "D8:07:B6": "Samsung", "9A:09:89": "Mobile/Generic"
}

def get_device_details(ip):
    start = time.time()
    ping_proc = subprocess.run(['ping', '-n', '1', '-w', '200', ip], stdout=subprocess.DEVNULL)
    latency = f"{round((time.time() - start) * 1000)}ms" if ping_proc.returncode == 0 else "Timed out"
    
    ports = []
    os_hint = "Unknown OS"
    check_ports = {22: "SSH", 80: "HTTP", 443: "HTTPS", 445: "SMB"}
    
    for p, name in check_ports.items():
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.05)
            if s.connect_ex((ip, p)) == 0:
                ports.append(name)
                if p == 445: os_hint = "Windows"
                if p == 22: os_hint = "Linux/Unix/Mobile"
    return ports, latency, os_hint

class ScannerHandler(http.server.BaseHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

    def do_GET(self):
        if self.path == '/scan':
            base_ip = "192.168.0."
            for i in range(100, 115):
                threading.Thread(target=lambda q: subprocess.run(['ping', '-n', '1', '-w', '10', q], stdout=subprocess.DEVNULL), args=(f"{base_ip}{i}",)).start()
            
            time.sleep(1)
            output = subprocess.check_output(("arp", "-a")).decode('cp866')
            devices = []
            
            for line in output.split('\n'):
                match = re.search(r'(192\.168\.0\.(?!255)\d+)\s+([0-9a-f-]+)', line)
                if match:
                    ip, mac = match.group(1), match.group(2).replace('-', ':').upper()
                    ports, latency, os_type = get_device_details(ip)
                    devices.append({
                        'ip': ip, 'mac': mac, 'vendor': VENDORS.get(mac[:8], "Generic Device"),
                        'ports': ports, 'latency': latency, 'os': os_type
                    })

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(devices).encode())

socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("", PORT), ScannerHandler) as httpd:
    httpd.serve_forever()