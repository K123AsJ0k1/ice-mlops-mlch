def text_parse_file(
    file_path: str,
    absolute_path: str
):  
    content = None
    with open(file_path, 'r') as f:
        content = f.read()

    parsed_material = []
    if 'packages' in file_path.lower():
        directory = str(file_path).split('/')[0]
        header = f"Directory {directory} venv dependencies"
        formatted_content = f"## {header}\n\n"
        formatted_content += f"This is from:{absolute_path}\n```text\n{content}\n```"
        #print(formatted_content)
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
            file_name = str(absolute_path).split('/')[-1].split('.')[0]
            header = f"Log {file_name}"

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
    #else:
        # metrics
        #pass
    return parsed_material