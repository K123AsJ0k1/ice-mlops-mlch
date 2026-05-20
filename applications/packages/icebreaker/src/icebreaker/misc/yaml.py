import yaml
from pathlib import Path

def get_validated_yamls(
    relative_paths: list,
    yaml_validator: any
) -> dict:
    yaml_dicts = {}
    for relative_path in relative_paths:
        directory_path = Path.cwd()
        file_path = directory_path / relative_path
        yaml_dict = None
        with open(file_path, 'r') as f:
            yaml_dict = yaml.safe_load(f)
        file_name = str(file_path).split('/')[-1].split('.')[0]
        pydantic_validation = yaml_validator.model_validate(yaml_dict)
        yaml_dicts[file_name] = yaml_dict
    return yaml_dicts