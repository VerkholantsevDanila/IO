#!/usr/bin/env python3
import asyncio
import subprocess
import tempfile
import os
import json
import re
import requests
import sys
from collections import defaultdict

IP_PATTERN = re.compile(r'@([\w\.\-]+):(\d+)')
UUID_PATTERN = re.compile(r'vless://([0-9a-fA-F\-]+)@')

TIMEOUT = 10.0
unreachable_logs = []

async def check_vless(url: str):
    try:
        uuid = UUID_PATTERN.search(url).group(1)
        ip, port = IP_PATTERN.search(url).groups()
        params = dict(re.findall(r'(\w+)=([^&]+)', url.split('?', 1)[1]))

        cfg = {
            "log": {"loglevel": "info"},
            "inbounds": [{
                "listen": "127.0.0.1",
                "port": 1080,
                "protocol": "socks",
                "settings": {"auth": "noauth"}
            }],
            "outbounds": [{
                "protocol": "vless",
                "settings": {
                    "vnext": [{
                        "address": ip,
                        "port": int(port),
                        "users": [{
                            "id": uuid,
                            "encryption": params.get("encryption", "none")
                        }]
                    }]
                },
                "streamSettings": {
                    "network": params.get("type", "tcp"),
                    "security": params.get("security", "none"),
                    **({
                        "wsSettings": {
                            "path": params.get("path", "/"),
                            "headers": {"Host": params.get("host", "")}
                        }
                    } if params.get("type") == "ws" else {}),
                    **({
                        "tcpSettings": {
                            "header": {"type": params.get("headerType", "none")}
                        }
                    } if params.get("type") == "tcp" else {}),
                    **({
                        "realitySettings": {
                            "serverName": params.get("sni", ""),
                            "fingerprint": params.get("fp", ""),
                            "publicKey": params.get("pbk", ""),
                            "shortId": params.get("sid", "")
                        }
                    } if params.get("security") == "reality" else {})
                }
            }],
            "routing": {"domainStrategy": "IPIfNonMatch"}
        }

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        tmp.write(json.dumps(cfg, indent=2).encode())
        tmp.close()

        print(f"🧪 Проверка: {ip}:{port} | UUID: {uuid}")
        proc = await asyncio.create_subprocess_exec(
            'xray', '-c', tmp.name,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=TIMEOUT)
            if proc.returncode == 0:
                resp = requests.get(f'http://ip-api.com/json/{ip}', timeout=5)
                country = resp.json().get('country', 'Unknown')
                os.unlink(tmp.name)
                return ip, port, country
            else:
                reason = stderr.decode().strip()
                print(f"❌ Ошибка: {ip}:{port} → {reason}")
                unreachable_logs.append(f"{ip}:{port} | xray error: {reason}")
        except asyncio.TimeoutError:
            proc.kill()
            print(f"⏰ Таймаут: {ip}:{port}")
            unreachable_logs.append(f"{ip}:{port} | timeout")
        finally:
            os.unlink(tmp.name)
    except Exception as e:
        print(f"💥 Ошибка обработки ссылки: {e}")
        unreachable_logs.append(f"{url} | error: {e}")
    return None

async def main():
    if len(sys.argv) >= 2:
        filepath = sys.argv[1]
    else:
        filepath = 'vless_list.txt'

    if not os.path.exists(filepath):
        print(f"❌ Файл {filepath} не найден.")
        return

    with open(filepath, 'r') as f:
        urls = [l.strip() for l in f if l.strip()]

    tasks = [check_vless(u) for u in urls]
    results = await asyncio.gather(*tasks)
    working = [r for r in results if r]
    groups = defaultdict(list)
    for ip, port, country in working:
        groups[country].append(f"{ip}:{port}")

    for country, ips in groups.items():
        fname = f"working_{country.replace(' ', '_')}.txt"
        with open(fname, 'w') as f:
            f.write('\n'.join(ips))

    if unreachable_logs:
        with open("unreachable.txt", 'w') as f:
            f.write('\n'.join(unreachable_logs))

    print(f"\n✅ Готово!\nРабочих: {len(working)}\nНерабочих: {len(unreachable_logs)}")

if __name__ == '__main__':
    asyncio.run(main())
