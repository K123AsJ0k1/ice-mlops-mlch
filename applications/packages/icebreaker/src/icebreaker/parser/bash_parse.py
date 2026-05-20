def bash_parse_file(
    file_path: str,
    absolute_path: str
): 
    content = None
    with open(file_path, 'r') as f:
        content = f.read()

    parsed_material = []
    formatted_code = content.strip()
    file_name = str(absolute_path).split('/')[-1].split('.')[0]
    header = f"Bash {file_name}"
    formatted_content = f"## {header}\n\n"
    formatted_content += f"This is from:{absolute_path}\n"
    formatted_content += f"```bash\n{formatted_code}\n```"
    
    parsed_material.append({
        'metadata': {},
        'topic': header,
        'material': {},
        'content': formatted_content,
        'paths': {}
    })

    return parsed_material