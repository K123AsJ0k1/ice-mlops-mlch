def env_parse_file(
    file_path: str,
    absolute_path: str,
    header_start: str
): 
    try:
        from ..parser.utility import utility_header_name
    except ImportError as e:
        raise ImportError("parser/env_parse failed to import", e)

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

    search_header = utility_header_name(
        absolute_path = absolute_path,
        start_prefix = header_start
    )
    parsed_material = []

    header = f"Env {search_header}"
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
