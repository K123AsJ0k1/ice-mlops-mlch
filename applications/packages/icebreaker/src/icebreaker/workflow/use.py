
def workflow_store_datasets(
    internal_material_parameters: str,
):
    try:
        import os
        from ..parser.use import parser_process_material
        from pathlib import Path
    except ImportError as e:
        raise ImportError("embeddings/use failed to import", e)

    # First process the tutorial material
    internal_material_path = Path(internal_material_parameters['material-path'])
    internal_material_prefix = internal_material_parameters['material-prefix']
    internal_material_exluded_directories = internal_material_parameters['excluded-material']
    internal_material_file_types = internal_material_parameters['file-types']
    internal_material_excluded_folders = internal_material_parameters['excluded-folders']
    internal_material_repository_name = internal_material_parameters['repository-name']
    internal_material_storage_folder = internal_material_parameters['storage-folder']
    internal_material_header_start = internal_material_parameters['header-start']
    
    for directory in internal_material_path.iterdir():
        target_directory = str(directory)
        directory_name = target_directory.split('/')[-1]
        if internal_material_prefix in directory_name:
            if not directory_name in internal_material_exluded_directories:
                material = parser_process_material(
                    directory = str(directory),
                    file_types = internal_material_file_types,
                    exclude_folders = internal_material_excluded_folders,
                    repository_name = internal_material_repository_name,
                    save_material = True,
                    storage_folder = internal_material_storage_folder,
                    storage_name = directory_name,
                    header_start = internal_material_header_start,
                    debug_prints = False
                )
                
        

    # Second, store them into Allas

    # Second, check if external material has been downlaoded
    # If not, download it, process it and store it into allas