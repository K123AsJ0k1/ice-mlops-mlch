def text_parse_file(
    file_path: str,
    absolute_path: str,
    header_start: str
):  
    try:
        from ..parser.utility import utility_header_name
    except ImportError as e:
        raise ImportError("parser/text_parse failed to import", e)

    content = None
    with open(file_path, 'r') as f:
        content = f.read()

    search_header = utility_header_name(
        absolute_path = absolute_path,
        start_prefix = header_start
    )
    parsed_material = []
    if 'packages' in file_path.lower():
        header = f"Python Venv {search_header} dependencies"
        formatted_content = f"## {header}\n\n"
        formatted_content += f"This is from:{absolute_path}\n```text\n{content}\n```"
        
        parsed_material.append({
            'metadata': {},
            'topic': header,
            'material': {},
            'content': formatted_content,
            'paths': {}
        })
    else:
        lines = content.splitlines()
        max_rows = 500
        for i in range(0, len(lines), max_rows):
            chunk_lines = lines[i:i + max_rows]
            part_num = (i // max_rows) + 1
            header = f"Text {search_header}"

            formatted_content = f"## {header}\n\n"
            formatted_content += f"This is from:{absolute_path} (Part {part_num}, Index {i})\n"
            formatted_content += "```text\n" + "\n".join(chunk_lines) + "\n```"
            
            parsed_material.append({
                'metadata': {},
                'topic': header,
                'material': {},
                'content': formatted_content,
                'paths': {}
            })
    return parsed_material