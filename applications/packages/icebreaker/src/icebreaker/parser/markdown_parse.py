
def markdown_extract_materials(
    content: str
) -> dict:
    try:
        import re
    except ImportError as e:
        raise ImportError("parser/markdown_parse failed to import", e)

    # Should 1. be used instead of used-material-1
    ref_pattern = r'<span id="([^"]+)"></span>\s*\[(.*?)\]\((.*?)\)'
    matches = re.findall(ref_pattern, content)
    return {m[0]: {"name": m[1].strip(), "url": m[2].strip()} for m in matches}

def markdown_extract_piece_references(content: str, used_material: dict) -> dict:
    try:
        import re
    except ImportError as e:
        raise ImportError("parser/markdown_parse failed to import", e)
    
    if not used_material:
        return {}

    # Matches any markdown link pointing to an anchor ID: [label](#anchor_id)
    raw_anchors = re.findall(r'\[.*?\]\(#([^\)]+)\)', content)

    section_materials = {}
    # Iterate through raw_anchors in order of appearance
    for anchor in raw_anchors:
        anchor_clean = anchor.strip()

        # Helper logic to match anchor to key in used_material
        matched_key = None

        if anchor_clean in used_material:
            matched_key = anchor_clean
        elif f"#{anchor_clean}" in used_material:
            matched_key = f"#{anchor_clean}"
        else:
            # Fallback by numerical ID (e.g., 'user-material-1' -> key ending in '1')
            num_match = re.search(r'\d+$', anchor_clean)
            if num_match:
                digits = num_match.group(0)
                for key in used_material:
                    if (
                        key == digits
                        or key.endswith(f"-{digits}")
                        or key.endswith(f".{digits}")
                    ):
                        matched_key = key
                        break

        # Add to output dictionary if found and not already added
        if matched_key and matched_key not in section_materials:
            section_materials[matched_key] = used_material[matched_key]

    return section_materials

def markdown_extract_paths(
    repository_path: str,
    file_path: str,
    content: str
) -> dict:
    try:
        import re
    except ImportError as e:
        raise ImportError("parser/markdown_parse failed to import", e)

    ref_paths = {}
    links = re.findall(r'\[.*?\]\((.*?)\)', content)
    # we will assume that links either reference things in subfolder 
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
            absolute_path = f'{repository_path}{source_directory}/{source_relative_path}'
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
        raise ImportError("parser/markdown_parse failed to import", e)

    content = frontmatter.loads(content)
    if not content:
        return []

    yaml_metadata = content.metadata
    text_data = content.content
    pieces = re.split(r"\n## ", text_data)

    used_material = {}
    for piece in pieces[1:]:
        lines = piece.strip().split("\n")
        header = lines[0].replace("#", "").strip()
        if header == "Used material":
            used_material = markdown_extract_materials(content=piece)
            break
    
    parsed_material = []
    piece_amount = len(pieces)
    for index, piece in enumerate(pieces[1:], start=2):
        lines = piece.strip().split("\n")
        header = lines[0].replace("#", "").strip()

        # Skip emitting the reference block itself as a separate content piece
        if header == "Used material":
            continue

        formatted_content = piece
        if index == piece_amount:
            formatted_content = re.sub(
                r"^---$", "", formatted_content, flags=re.MULTILINE
            )

        paths = markdown_extract_paths(
            repository_path=repository_path,
            file_path=file_path,
            content=formatted_content,
        )

        # Filter used_material to only materials cited inside this specific section
        section_materials = markdown_extract_piece_references(
            content = formatted_content, 
            used_material = used_material
        )
        
        formatted_content = formatted_content.strip()
        parsed_material.append(
            {
                "metadata": yaml_metadata,
                "topic": header,
                "material": section_materials,  
                "content": formatted_content,
                "paths": paths,
            }
        )
    
    return parsed_material