import socket
import re

def grab_banner(ip, port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.3)
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
                s.settimeout(0.1)
                if s.connect_ex((ip, port)) == 0:
                    banner = grab_banner(ip, port)
                    open_ports[str(port)] = {"service": service, "banner": banner}
        except Exception:
            pass
    return open_ports