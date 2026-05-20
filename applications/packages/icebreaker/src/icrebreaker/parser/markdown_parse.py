
def markdown_extract_materials(
    content: str
) -> dict:
    try:
        import re
    except ImportError as e:
        raise ImportError("Failed to import", e)

    # Should 1. be used instead of used-material-1
    ref_pattern = r'<span id="([^"]+)"></span>\s*\[(.*?)\]\((.*?)\)'
    matches = re.findall(ref_pattern, content)
    return {m[0]: {"name": m[1].strip(), "url": m[2].strip()} for m in matches}

def markdown_extract_paths(
    repository_path: str,
    file_path: str,
    content: str
) -> dict:
    try:
        import re
    except ImportError as e:
        raise ImportError("Failed to import", e)

    ref_paths = {}
    links = re.findall(r'\[.*?\]\((.*?)\)', content)
    # we will assume that links either referecen things in subfolder 
    # or partner folders. This means ./ and ../
    for link in links:
        if link.startswith('#'):
            continue
        if not '/' in link:
            continue
        if not '.' in link:
            continue
        
        source_relative_path = ''
        relative_path_split = link.split('/')
        if relative_path_split[0] == '.':
            source_relative_path = link[2:]
        if relative_path_split[0] == '..':
            source_relative_path = link[3:]
        
        if 0 < len(source_relative_path):
            source_directory = str(file_path).split('/')[0]
            absolute_path = repository_path + '/' + source_directory + '/' + source_relative_path
            ref_paths[link] = absolute_path
    return ref_paths

def markdown_parse_content(
    repository_path: str,
    file_path: str,
    content: str
) -> list:
    try:
        import re
        import frontmatter
    except ImportError as e:
        raise ImportError("Failed to import", e)

    content = frontmatter.loads(content)
    parsed_material = []
    if not content is None:
        yaml_metadata = content.metadata
        text_data = content.content
        pieces = re.split(r'\n## ', text_data)
        
        used_material = {}
        index = 1
        piece_amount = len(pieces)
        for piece in pieces[1:]:
            index += 1 
            lines = piece.strip().split('\n')
            header = lines[0].replace('#', '').strip()
            formatted_content = piece
            if header == 'Used material':
                used_material = markdown_extract_materials(
                    content = piece
                )
                continue
            
            if index == piece_amount:
                formatted_content = re.sub(r'^---$', '', formatted_content, flags=re.MULTILINE)
                
            paths = markdown_extract_paths(
                repository_path = repository_path,
                file_path = file_path,
                content = formatted_content
            )

            formatted_content = formatted_content.strip()
            parsed_material.append({
                'metadata': yaml_metadata,
                'topic': header,
                'material': used_material,
                'content': formatted_content,
                'paths': paths
            })
            
    return parsed_material