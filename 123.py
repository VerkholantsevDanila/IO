import ssl
import socket
import base64
import hashlib
import urllib.parse
from urllib.parse import urlparse, parse_qs

def parse_vless_url(vless_url):
    assert vless_url.startswith("vless://")
    url = vless_url[8:]
    userinfo, rest = url.split('@', 1)
    uuid = userinfo

    if '#' in rest:
        rest, _ = rest.split('#', 1)
    if '?' in rest:
        addr, query = rest.split('?', 1)
        params = parse_qs(query)
    else:
        addr = rest
        params = {}

    host, port = addr.split(':')
    port = int(port)

    return {
        'uuid': uuid,
        'host': host,
        'port': port,
        'params': {k: v[0] for k, v in params.items()}
    }

def check_vless_ws(vless_config, timeout=5):
    host = vless_config['host']
    port = vless_config['port']
    path = vless_config['params'].get('path', '/')
    vhost = vless_config['params'].get('host', host)

    # WebSocket Handshake
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

        if "101 Switching Protocols" in response:
            print(f"[+] ✅ VLESS WS работает: {host}:{port}")
            return True
        else:
            print(f"[-] ❌ Ответ получен, но это не WebSocket: {host}:{port}")
            return False
    except Exception as e:
        print(f"[!] 💥 Ошибка подключения к {host}:{port} — {e}")
        return False

# === Пример использования ===

url = "vless://fab7bf9c-ddb9-4563-8a04-fb01ce6c0fbf@156.238.18.106:8880?encryption=none&security=none&type=ws&host=yd.laoyoutiao.link&path=%2FTelegram%F0%9F%87%A8%F0%9F%87%B3"
cfg = parse_vless_url(url)

if cfg['params'].get('type') == 'ws':
    check_vless_ws(cfg)
else:
    print("⚠️ Пока поддерживается только VLESS WS.")
