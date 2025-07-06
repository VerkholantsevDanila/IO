def clean_file(input_file, output_file):
    seen = set()
    with open(input_file, 'r', encoding='utf-8') as infile, \
         open(output_file, 'w', encoding='utf-8') as outfile:
        for line in infile:
            stripped = line.strip()
            if stripped and stripped not in seen:
                outfile.write(stripped + '\n')
                seen.add(stripped)

if __name__ == "__main__":
    input_path = "input.txt"    # имя исходного файла
    output_path = "cleaned.txt" # имя очищенного файла
    clean_file(input_path, output_path)
    print(f"Очищенные данные сохранены в {output_path}")
