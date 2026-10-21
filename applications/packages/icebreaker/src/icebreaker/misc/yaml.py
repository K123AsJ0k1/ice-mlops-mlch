
def get_validated_yamls(
    relative_paths: list,
    yaml_validator: any,
    key_replacer: dict
) -> dict:
    try:
        import yaml
        from pathlib import Path
    except ImportError as e:
        raise ImportError("misc/dict failed to import", e)

    yaml_dicts = {}
    for relative_path in relative_paths:
        directory_path = Path.cwd()
        file_path = directory_path / relative_path
        yaml_dict = None
        with open(file_path, 'r') as f:
            yaml_dict = yaml.safe_load(f)
        file_name = str(file_path).split('/')[-1].split('.')[0]
        if not yaml_validator is None:
            pydantic_validation = yaml_validator.model_validate(yaml_dict)
        used_key = file_name
        if 0 < len(key_replacer):
            used_key = key_replacer[used_key]    
        yaml_dicts[used_key] = yaml_dict
    return yaml_dicts