import base64
import socket
import re

def parse_ss_url(url):
    if not url.startswith("ss://"):
        return None
    url = url.strip()[5:].split('#')[0]  # удалить 'ss://' и комментарий
    try:
        if '@' in url:
            creds_enc, server = url.split('@')
            creds_dec = base64.urlsafe_b64decode(creds_enc + '==').decode()
        else:
            decoded = base64.urlsafe_b64decode(url + '==').decode()
            creds_dec, server = decoded.rsplit('@', 1)

        method, password = creds_dec.split(':', 1)
        host, port = server.split(':')
        return {
            'method': method,
            'password': password,
            'host': host,
            'port': int(port)
        }
    except Exception as e:
        return None

def test_ss_connection(config, timeout=3):
    try:
        with socket.create_connection((config['host'], config['port']), timeout=timeout) as sock:
            return True
    except:
        return False

def check_from_file(filename):
    with open(filename, 'r') as f:
        links = f.readlines()

    for link in links:
        link = link.strip()
        if not link:
            continue
        parsed = parse_ss_url(link)
        if parsed:
            result = test_ss_connection(parsed)
            status = "✅ OK" if result else "❌ FAIL"
            print(f"[{status}] {parsed['host']}:{parsed['port']}")
        else:
            print(f"[❌ PARSE ERROR] {link}")

if __name__ == "__main__":
    check_from_file("ss_links.txt")
