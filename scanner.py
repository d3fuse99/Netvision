import socket
import re
import subprocess

def is_private_ip(ip):
    patterns = [
        re.compile(r'^10\.\d+\.\d+\.\d+$'),
        re.compile(r'^172\.(1[6-9]|2\d|3[0-1])\.\d+\.\d+$'),
        re.compile(r'^192\.168\.\d+\.\d+$')
    ]
    return any(p.match(ip) for p in patterns)

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
        output = subprocess.check_output(["arp", "-a"], shell=False).decode('cp866')
        for line in output.split('\n'):
            match = re.search(r'(\d+\.\d+\.\d+\.\d+)\s+([0-9a-f-]+)', line, re.IGNORECASE)
            if match:
                mapping[match.group(1)] = match.group(2).replace('-', ':').upper()
    except Exception:
        pass
    return mapping