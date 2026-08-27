import socket
import re

def grab_banner(s, port, ip):
    try:
        if port == 22:
            banner = s.recv(1024).decode('utf-8', errors='ignore').strip()
            return re.sub(r'[^\w\.\-\s\:\/]', '', banner)
        elif port == 80:
            request = f"GET / HTTP/1.1\r\nHost: {ip}\r\nConnection: close\r\n\r\n"
            s.sendall(request.encode('utf-8'))
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
                s.settimeout(0.2)
                if s.connect_ex((ip, port)) == 0:
                    banner = grab_banner(s, port, ip) if port in [22, 80] else service
                    open_ports[str(port)] = {"service": service, "banner": banner}
        except Exception:
            pass
    return open_ports