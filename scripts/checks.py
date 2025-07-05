import base64
import socket
import urllib.parse
from urllib.parse import parse_qs
import sys

def parse_ss_url(url):
    try:
        if '#' in url:
            url = url.split('#')[0]
        url = url[5:]  # strip ss://

        if '@' in url:
            creds_enc, server = url.split('@')
            creds_dec = base64.urlsafe_b64decode(creds_enc + '==').decode()
        else:
            decoded = base64.urlsafe_b64decode(url + '==').decode()
            creds_dec, server = decoded.rsplit('@', 1)

        method, password = creds_dec.split(':', 1)
        host, port = server.split(':')
        return {
            'type': 'ss',
            'method': method,
            'password': password,
            'host': host,
            'port': int(port)
        }
    except Exception as e:
        return None

def parse_vless_url(url):
    try:
        url = url[8:]  # strip vless://
        if '#' in url:
            url, _ = url.split('#', 1)
        if '@' not in url:
            return None
        userinfo, rest = url.split('@', 1)
        uuid = userinfo
        if '?' in rest:
            addr, query = rest.split('?', 1)
            params = parse_qs(query)
        else:
            addr = rest
            params = {}

        host, port = addr.split(':')
        return {
            'type': 'vless',
            'uuid': uuid,
            'host': host,
            'port': int(port),
            'params': {k: v[0] for k, v in params.items()}
        }
    except Exception as e:
        return None

def test_ss_connection(config, timeout=3):
    try:
        with socket.create_connection((config['host'], config['port']), timeout=timeout) as sock:
            return True
    except:
        return False

def test_vless_ws(config, timeout=5):
    host = config['host']
    port = config['port']
    path = config['params'].get('path', '/')
    vhost = config['params'].get('host', host)
    key = base64.b64encode(b'1234567890abcdef').decode()

    headers = (
        f"GET {path} HTTP/1.1\r\n"
        f"Host: {vhost}\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        f"Sec-WebSocket-Key: {key}\r\n"
        "Sec-WebSocket-Version: 13\r\n"
        "\r\n"
    )

    try:
        sock = socket.create_connection((host, port), timeout=timeout)
        sock.send(headers.encode())
        response = sock.recv(1024).decode(errors='ignore')
        sock.close()

        return "101 Switching Protocols" in response
    except:
        return False

def check_from_file(filename):
    with open(filename, 'r') as f:
        links = f.readlines()

    for link in links:
        link = link.strip()
        if not link or link.startswith("#"):
            continue

        if link.startswith("ss://"):
            config = parse_ss_url(link)
            if config:
                result = test_ss_connection(config)
                status = "✅ OK" if result else "❌ FAIL"
                print(f"[{status}] SS: {config['host']}:{config['port']}")
            else:
                print(f"[❌ PARSE ERROR] {link}")

        elif link.startswith("vless://"):
            config = parse_vless_url(link)
            if config and config['params'].get('type') == 'ws':
                result = test_vless_ws(config)
                status = "✅ OK" if result else "❌ FAIL"
                print(f"[{status}] VLESS WS: {config['host']}:{config['port']}")
            else:
                print(f"[⚠️ SKIP] Unsupported VLESS type or parse error: {link}")
        else:
            print(f"[⚠️ UNKNOWN] Unknown URL type: {link}")

if __name__ == "__main__":
    file = sys.argv[1] if len(sys.argv) > 1 else "links.txt"
    check_from_file(file)
