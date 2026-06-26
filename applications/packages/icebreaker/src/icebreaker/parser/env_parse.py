def env_parse_file(
    file_path: str,
    absolute_path: str
): 
    redacted_lines = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
               redacted_lines.append(line)
               continue

            if '=' in line:
                key, value = line.split('=', 1)
                redacted_lines.append(f"{key}=[REDACTED]")
                continue

            redacted_lines.append(line)
    content = "\n".join(redacted_lines)

    parsed_material = []
    file_path_split = absolute_path.split('/')
    used_directory = file_path_split[-2]
    used_file = file_path_split[-1].split('.')[0]

    header = f"Env {used_directory} {used_file}"
    formatted_content = f"## {header}\n\n"
    formatted_content += f"This is from:{absolute_path}\n"
    formatted_content += f"```env\n{content}\n```"

    parsed_material.append({
        'metadata': {},
        'topic': header,
        'material': {},
        'content': formatted_content,
        'paths': {}
    })

    return parsed_material
