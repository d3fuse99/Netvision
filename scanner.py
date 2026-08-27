import socket
import re
import subprocess
import platform
import ipaddress

def is_private_ip(ip):
    try:
        return ipaddress.ip_address(ip).is_private
    except ValueError:
        return False

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
    old_timeout = socket.getdefaulttimeout()
    try:
        socket.setdefaulttimeout(0.3)
        resolved = socket.gethostbyaddr(ip)[0]
        return re.sub(r'[^\w\.\-\s]', '', resolved)
    except Exception:
        return "Unknown Node"
    finally:
        socket.setdefaulttimeout(old_timeout)

def ping_host(ip):
    system = platform.system().lower()
    if system == "windows":
        cmd = ['ping', '-n', '1', '-w', '150', ip]
    else:
        cmd = ['ping', '-c', '1', '-W', '1', ip]
    try:
        return subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=False).returncode == 0
    except Exception:
        return False

def get_mac_mapping():
    mapping = {}
    system = platform.system().lower()
    try:
        if system == "windows":
            output = subprocess.check_output(["arp", "-a"], shell=False).decode('cp866', errors='ignore')
        else:
            output = subprocess.check_output(["arp", "-n"], shell=False).decode('utf-8', errors='ignore')
            
        for line in output.splitlines():
            match = re.search(r'(\d+\.\d+\.\d+\.\d+)\s+.*?([0-9a-fA-F]{2}[:-][0-9a-fA-F]{2}[:-][0-9a-fA-F]{2}[:-][0-9a-fA-F]{2}[:-][0-9a-fA-F]{2}[:-][0-9a-fA-F]{2})', line)
            if match:
                ip = match.group(1)
                mac = match.group(2).replace('-', ':').upper()
                mapping[ip] = mac
    except Exception:
        pass
    return mapping