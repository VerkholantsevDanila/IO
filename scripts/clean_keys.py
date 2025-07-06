import os
import shutil
from checks import parse_ss_url, parse_vless_url, test_ss_connection, test_vless_ws

SOURCE_DIR = "./keys"
BACKUP_DIR = os.path.join(SOURCE_DIR, "backup")
SKIP_PATH = os.path.join(SOURCE_DIR, "SKIP.txt")
OLD_PATH = os.path.join(SOURCE_DIR, "old.txt")

seen_links = set()
collected_skip = set()
collected_old = set()

def backup_keys():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    print("📁 Создаём резервные копии в keys/backup")

    for fname in os.listdir(SOURCE_DIR):
        if not fname.endswith(".txt"):
            continue
        if fname in ["SKIP.txt", "old.txt"]:
            continue
        src = os.path.join(SOURCE_DIR, fname)
        dst = os.path.join(BACKUP_DIR, fname)
        shutil.copy2(src, dst)
        print(f"🗂️  Резерв: {fname} → backup")

def process_line(line):
    line = line.strip()
    if not line or line.startswith("#"):
        return None, "skip"

    if line in seen_links:
        return None, "duplicate"

    seen_links.add(line)

    if line.startswith("ss://"):
        config = parse_ss_url(line)
        if config:
            return (line, "ok") if test_ss_connection(config) else (line, "old")
        return line, "old"

    elif line.startswith("vless://"):
        config = parse_vless_url(line)
        if config and config['params'].get('type') == 'ws':
            return (line, "ok") if test_vless_ws(config) else (line, "old")
        return line, "skip"

    return line, "skip"

def append_unique(path, lines_set):
    if not lines_set:
        return
    existing = set()
    if os.path.exists(path):
        with open(path, "r") as f:
            existing = set(x.strip() for x in f if x.strip())

    with open(path, "w") as f:
        for line in sorted(existing | lines_set):
            f.write(line + "\n")

def process_file(original_path, output_path):
    with open(original_path, "r") as f:
        lines = f.readlines()

    new_lines = []

    for line in lines:
        result, status = process_line(line)
        if status == "ok" and result:
            new_lines.append(result + "\n")
        elif status == "skip" and result:
            collected_skip.add(result)
        elif status == "old" and result:
            collected_old.add(result)

    with open(output_path, "w") as f:
        f.writelines(new_lines)

def main():
    backup_keys()

    for fname in os.listdir(BACKUP_DIR):
        if not fname.endswith(".txt"):
            continue
        src_path = os.path.join(BACKUP_DIR, fname)
        dst_path = os.path.join(SOURCE_DIR, fname)
        print(f"🔍 Обработка файла: {fname}")
        process_file(src_path, dst_path)

    append_unique(SKIP_PATH, collected_skip)
    append_unique(OLD_PATH, collected_old)

    print("✅ Готово: плохие ключи перемещены, дубликаты удалены, резерв есть в ./keys/backup")

if __name__ == "__main__":
    main()
