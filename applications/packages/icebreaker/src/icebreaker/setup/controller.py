def controller_create_files(
    controller_folder: str,
    template_prefix: str,
    configuration_values: any
) -> any:
    try:
        import yaml
        import os
    except ImportError as e:
        raise ImportError("Failed to import", e)
    created_files = []
    for root, dirs, files in os.walk(controller_folder):
        for file in files:
            if template_prefix in file:
                file_path = os.path.join(root, file)
                created_file_content = ''
                with open(file_path, 'r', encoding='utf-8') as f:
                    created_file_content = f.read()
                
                if 0 < len(configuration_values):
                    file_type = file.split('-')[0]
                    
                    if file_type in configuration_values:
                        file_configuration = configuration_values[file_type]
                        if 0 < len(file_configuration['values']):
                            if '.txt' in file:
                                for placeholder, value in file_configuration['values'].items():
                                    created_file_content = created_file_content.replace(placeholder, str(value))
                            if '.yaml' in file:
                                created_file_content = yaml.safe_load(created_file_content)
                                for key, value in file_configuration['values'].items():
                                    if key in created_file_content:
                                        created_file_content[key] = value
                                created_file_content = yaml.dump(created_file_content, default_flow_style = False)

                        created_file_path = file_configuration['file_path']
                        if 0 < len(created_file_path):
                            created_files.append({
                                'file_path': created_file_path,
                                'file_content': created_file_content
                            })
    return created_files       