
def organize_chapter_check(
    absolute_path: str
) -> bool:
    try:
        import re 
    except ImportError as e:
        raise ImportError("Failed to import", e)

    file_name = absolute_path.split('/')[-1]
    return re.match(r'^\d+', file_name)
 
def organizer_sort_material(
    material_dict: dict
) -> list:
    try:
        import re 
    except ImportError as e:
        raise ImportError("Failed to import", e)

    ordered_list = []
    seen_list = set()
    primary_chapters = sorted([path for path in material_dict.keys() if organize_chapter_check(path)])
    
    for chapter_path in primary_chapters:
        chapter_pieces = material_dict[chapter_path]

        if chapter_path not in ordered_list:
            ordered_list.append(chapter_path)
        
        for piece in chapter_pieces:
            ref_path = piece['ref-paths']
            for relative_path, absolute_path in ref_path.items():
                chapter_pattern = r'(?<!\d)\d{2}(?!\d)'
                if not bool(re.search(chapter_pattern, absolute_path)):
                    if not absolute_path in seen_list:
                        seen_list.add(absolute_path)
                        ordered_list.append(absolute_path)
    
    remaining_files = sorted([path for path in material_dict.keys() if path not in ordered_list])
    ordered_list = ordered_list + remaining_files
    
    sorted_material = []
    for file_path in ordered_list:
        if file_path in material_dict:
            sorted_material.append(
                material_dict[file_path]
            )

    return sorted_material