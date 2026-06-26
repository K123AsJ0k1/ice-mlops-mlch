def text_parse_file(
    file_path: str,
    absolute_path: str
):  
    content = None
    with open(file_path, 'r') as f:
        content = f.read()

    parsed_material = []
    file_path_split = absolute_path.split('/')
    used_directory = file_path_split[-2]
    used_file = file_path_split[-1].split('.')[0]
    if 'packages' in file_path.lower():
        header = f"Directory {used_directory} {used_file} venv dependencies"
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
            header = f"Log {used_directory} {used_file}"

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