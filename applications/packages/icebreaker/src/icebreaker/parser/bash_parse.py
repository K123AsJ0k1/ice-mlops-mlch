def bash_parse_file(
    file_path: str,
    absolute_path: str,
    header_start: str
): 
    try:
        from ..parser.utility import utility_header_name
    except ImportError as e:
        raise ImportError("parser/env_parse failed to import", e)

    content = None
    with open(file_path, 'r') as f:
        content = f.read()

    parsed_material = []
    
    search_header = utility_header_name(
        absolute_path = absolute_path,
        start_prefix = header_start
    )
    
    formatted_code = content.strip()
    header = f"Bash {search_header}"
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