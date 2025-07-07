def replace_after_hash(line: str, replacement: str = "ioio") -> str:
    if '#' in line:
        return line.rsplit('#', 1)[0] + '#' + replacement
    return line  # если "#" нет, оставляем как есть

def clean_file(input_file, output_file):
    seen = set()
    with open(input_file, 'r', encoding='utf-8') as infile, \
         open(output_file, 'w', encoding='utf-8') as outfile:
        for line in infile:
            stripped = line.strip()
            if stripped:
                cleaned_line = replace_after_hash(stripped)
                if cleaned_line not in seen:
                    outfile.write(cleaned_line + '\n')
                    seen.add(cleaned_line)

if __name__ == "__main__":
    input_path = "input.txt"    # имя исходного файла
    output_path = "cleaned.txt" # имя очищенного файла
    clean_file(input_path, output_path)
    print(f"Очищенные данные сохранены в {output_path}")
