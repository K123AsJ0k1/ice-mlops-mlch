 
def generator_repository_path(
    repository_name: str,
    directory: str
) -> str:
    try:
        from pathlib import Path 
    except ImportError as e:
        raise ImportError("parser/generator failed to import", e)

    target_directory = Path.cwd() / directory
    path_split = str(target_directory).split('/')
    index = 0
    for folder in path_split:
        if folder == repository_name:
            break
        index += 1
    joined_path = '/'.join(path_split[index:-1])
    return joined_path

def generator_chapter_number(
    file_name: str
) -> int:
    try:
        import re 
    except ImportError as e:
        raise ImportError("parser/generator failed to import", e)

    match = re.search(r'^(\d+)', file_name)
    chapter_number = None
    if match:
        chapter_number = int(match.group(1))
    return chapter_number

def generator_save_material(
    data: dict,
    folder: str,
    name: str
):
    try:
        from pathlib import Path 
        import json
    except ImportError as e:
        raise ImportError("parser/generator failed to import", e)

    if not folder[0] == '/':
        # Be aware that starting with /folder makes it absolute
        folder = Path(folder)
        folder.mkdir(parents=True, exist_ok=True)
        file_path = folder / f"{name}.json"
        print('Storing material to relative path:',file_path)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)

def generator_divide_material(
    repository_name: str,
    directory: str,
    file_types: list,
    exclude_folders: list,
    save_material: bool,
    storage_folder: str,
    storage_name: str
) -> int:
    try:
        import os
        from .markdown_parse import markdown_parse_content
        from .notebook_parse import notebook_parse_file
        from .python_parse import python_parse_file
        from .yaml_parse import yaml_parse_file
        from .text_parse import text_parse_file
        from .bash_parse import bash_parse_file
        from .env_parse import env_parse_file
        from .organizer import organizer_sort_material
    except ImportError as e:
        raise ImportError("parser/generator failed to import", e)
    
    repository_path = generator_repository_path(
        repository_name = repository_name,
        directory = directory
    )
    
    divided_material = {}
    part_number = directory.split('-')[-1]
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in exclude_folders]

        for file in files:
            file_path = os.path.join(root, file)
            path_split = str(file_path).split('/')
            file_name = path_split[-1]
            pieces = []
            
            parsing_strategy = ''
            header_type = ''
            chapter_number = 0
            before, match, after = str(file_path).partition(repository_path)
            absolute_path = f'{repository_path}{after}'
            file_type = file_name.split('.')[-1]
            if file_type in file_types:
                if file_type == 'md':
                    print('Parsing ' + str(file_path))
                    content = None
                    with open(file_path, 'r') as f:
                        content = f.read()

                    pieces = markdown_parse_content(
                        repository_path = repository_path,
                        file_path = file_path,
                        content = content
                    )

                    chapter_number = generator_chapter_number(
                        file_name = file_name
                    )
                    parsing_strategy = 'Header division'
                    header_type = 'Assigned topic'
                if file_type == 'ipynb':
                    print('Parsing ' + str(file_path))
                    pieces = notebook_parse_file(
                        repository_path = repository_path,
                        file_path = file_path
                    )

                    chapter_number = generator_chapter_number(
                        file_name = file_name
                    )
                    parsing_strategy = 'Header division'
                    header_type = 'Assigned topic'
                if file_type == 'py':
                    print('Parsing ' + str(file_path))
                    pieces = python_parse_file(
                        file_path = file_path,
                        absolute_path = absolute_path
                    )
                    parsing_strategy = 'AST formatting'
                    header_type = 'Functions and classes'
                if file_type == 'yaml':
                    print('Parsing ' + str(file_path))
                    pieces = yaml_parse_file(
                        file_path = file_path,
                        absolute_path = absolute_path
                    )
                    parsing_strategy = 'YAML loading'
                    header_type = 'Relevant key'
                if file_type == 'txt':
                    print('Parsing ' + str(file_path))
                    pieces = text_parse_file(
                        file_path = file_path,
                        absolute_path = absolute_path
                    )
                    parsing_strategy = 'Text loading'
                    header_type = 'Type and directory'
                if file_type == 'sh':
                    print('Parsing ' + str(file_path))
                    pieces = bash_parse_file(
                        file_path = file_path,
                        absolute_path = absolute_path
                    )
                    parsing_strategy = 'Bash loading'
                    header_type = 'Type and directory'
                if file_type == 'env':
                    print('Parsing ' + str(file_path))
                    pieces = env_parse_file(
                        file_path = file_path,
                        absolute_path = absolute_path
                    )
                    parsing_strategy = 'Env loading'
                    header_type = 'Type and directory'
            else:
                continue
            
            if 0 < len(pieces):
                divided_material[absolute_path] = []
                piece_index = 1
                
                for piece in pieces:
                    piece_content = piece['content']
                    piece_lines = len(piece_content.splitlines())
                    content_characters = len(piece_content)
                    divided_material[absolute_path].append({
                        'part': part_number,
                        'chapter': chapter_number,
                        'index': piece_index,
                        'strategy': parsing_strategy,
                        'header': header_type,
                        'topic': piece['topic'],
                        'absolute-path': absolute_path,
                        'metadata': piece['metadata'],
                        'content': piece['content'],
                        'rows': piece_lines,
                        'characters': content_characters,
                        'ref-material': piece['material'],
                        'ref-paths': piece['paths']
                    })
                    piece_index += 1
    
    sorted_material = organizer_sort_material(
        material_dict = divided_material
    )

    print('Amount of parsed files', len(sorted_material))
    if save_material:
        generator_save_material(
            data = sorted_material,
            folder = storage_folder,
            name = storage_name
        )
    
    sorted_material = None
    return sorted_material