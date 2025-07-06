import os
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from datetime import datetime
from checkplus import parse_ss_url, parse_vless_url, test_ss_connection, test_vless_ws, get_country_code

BASE_DIR = "keys"
OLD_FILE = os.path.join(BASE_DIR, "old.txt")
SKIP_FILE = os.path.join(BASE_DIR, "SKIP.txt")
LOG_FILE = os.path.join(BASE_DIR, "check_keys.log")

logging.basicConfig(
    filename=LOG_FILE,
    filemode='a',
    format='[%(asctime)s] %(levelname)s: %(message)s',
    level=logging.INFO,
)

def log(msg):
    print(msg)
    logging.info(msg)

def load_file_to_list(path):
    if not os.path.exists(path):
        return []
    with open(path, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]

def write_lines_to_file(path, lines_set):
    with open(path, 'w', encoding='utf-8') as f:
        for line in sorted(lines_set):
            f.write(line + '\n')

def save_ok_keys_by_country(ok_keys):
    for line in ok_keys:
        config = None
        if line.startswith("ss://"):
            config = parse_ss_url(line)
        elif line.startswith("vless://"):
            config = parse_vless_url(line)

        if config:
            country = get_country_code(config['host'])
        else:
            country = "XX"  # неизвестная страна

        path = os.path.join(BASE_DIR, f"{country}.txt")
        existing = set()
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                existing = set(x.strip() for x in f if x.strip())

        if line not in existing:
            with open(path, "a", encoding="utf-8") as f:
                f.write(line + "\n")

def check_key(line):
    try:
        if line.startswith("ss://"):
            config = parse_ss_url(line)
            if config:
                if test_ss_connection(config):
                    log(f"[✅ OK] SS {config['host']}:{config['port']}")
                    return (line, 'ok')
                else:
                    log(f"[❌ FAIL] SS {config['host']}:{config['port']}")
                    return (line, 'old')
            else:
                log(f"[❌ PARSE ERROR] {line}")
                return (line, 'old')

        elif line.startswith("vless://"):
            config = parse_vless_url(line)
            if config and config['params'].get('type') == 'ws':
                if test_vless_ws(config):
                    log(f"[✅ OK] VLESS {config['host']}:{config['port']}")
                    return (line, 'ok')
                else:
                    log(f"[❌ FAIL] VLESS {config['host']}:{config['port']}")
                    return (line, 'old')
            else:
                log(f"[⚠️ SKIP] VLESS unsupported type or parse error → {line}")
                return (line, 'skip')

        else:
            log(f"[⚠️ UNKNOWN] Unknown link type → {line}")
            return (line, 'skip')
    except Exception as e:
        log(f"[⚠️ ERROR] Exception on line check: {line} → {e}")
        return (line, 'skip')

def process_file(file_path):
    lines = load_file_to_list(file_path)
    results = []

    log(f"🔍 Начата проверка файла: {os.path.basename(file_path)} ({len(lines)} ключей)")

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(check_key, line): line for line in lines}
        for future in tqdm(as_completed(futures), total=len(lines), desc=f"Проверка {os.path.basename(file_path)}"):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                line = futures[future]
                log(f"[⚠️ ERROR] Ошибка при проверке ключа: {line} → {e}")
                results.append((line, 'skip'))

    return results

def update_files(results):
    ok_set = set()
    old_set = set()
    skip_set = set()

    for line, status in results:
        if status == 'ok':
            ok_set.add(line)
        elif status == 'old':
            old_set.add(line)
        elif status == 'skip':
            skip_set.add(line)

    # Сначала сохраняем OK ключи в country-файлы
    save_ok_keys_by_country(ok_set)

    old_lines = set(load_file_to_list(OLD_FILE))
    skip_lines = set(load_file_to_list(SKIP_FILE))

    # Затем удаляем из old и skip ключи, которые теперь OK
    old_lines = (old_lines | old_set) - ok_set
    skip_lines = (skip_lines | skip_set) - ok_set

    write_lines_to_file(OLD_FILE, old_lines)
    write_lines_to_file(SKIP_FILE, skip_lines)

    log(f"✅ Файлы обновлены. OK: {len(ok_set)}, OLD: {len(old_set)}, SKIP: {len(skip_set)}")

def main():
    log("🚀 Запуск проверки ключей")

    results_old = process_file(OLD_FILE)
    results_skip = process_file(SKIP_FILE)

    all_results = results_old + results_skip

    update_files(all_results)

    log("🏁 Проверка завершена")

if __name__ == "__main__":
    main()
