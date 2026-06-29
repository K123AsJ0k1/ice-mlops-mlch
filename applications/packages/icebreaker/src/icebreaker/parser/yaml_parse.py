 
def yaml_parse_file(
    file_path: str,
    absolute_path: str,
    header_start: str
): 
    try:
        import yaml
        from ..parser.utility import utility_header_name
    except ImportError as e:
        raise ImportError("parser/yaml_parse failed to import", e)

    content = None
    # This makes --- into their own chunks
    with open(file_path, 'r') as f:
        content = [doc for doc in yaml.safe_load_all(f) if not doc is None]
    
    search_header = utility_header_name(
        absolute_path = absolute_path,
        start_prefix = header_start
    )

    parsed_material = []
    for i, document in enumerate(content):
        if not document:
            continue

        if 'kind' in document: 
            resource_name = document['kind']
            resource_header = f"YAML {search_header} Kubernetes {resource_name}"
            formatted_resource_content = f"## {resource_header}\n\n"
            formatted_resource_content += f"This is from:{absolute_path}\n"
            formatted_resource_content += f"```yaml\n{yaml.dump(document, sort_keys=False)}```"
            
            parsed_material.append({
                'metadata': {},
                'topic': resource_header,
                'material': {},
                'content': formatted_resource_content,
                'paths': {}
            })

            continue

        if 'services' in document:
            global_keys = {k: document[k] for k in ['networks', 'volumes', 'secrets', 'configs'] if k in document}
            services = document.get('services', {})

            for service_name, config in services.items():
                service_header = f"YAML {search_header} Docker Compose {service_name}"
                formatted_service_content = f"## {service_header}\n\n"
                formatted_service_content += f"This is from:{absolute_path}\n"

                mini_compose = {
                    "services": {service_name: config}
                }
                
                used_globals = {}
                for key, items in global_keys.items():
                    used_in_service = []
                    if key == 'networks' and 'networks' in config:
                        used_in_service = config['networks']
                    elif key == 'secrets' and 'secrets' in config:
                        used_in_service = [s if isinstance(s, str) else s.get('source') for s in config['secrets']]
                    
                    filtered_items = {name: items[name] for name in used_in_service if name in items}
                    if filtered_items:
                        used_globals[key] = filtered_items

                mini_compose.update(used_globals)
                formatted_service_content += f"```yaml\n{yaml.dump(mini_compose, sort_keys=False)}```"
                parsed_material.append({
                    'metadata': {},
                    'topic': service_header,
                    'material': {},
                    'content': formatted_service_content,
                    'paths': {}
                })

            if global_keys:
                infra_header = f"YAML {search_header} Docker Compose configuration"
                formatted_infra_content = f"## {infra_header}\n\n"
                formatted_infra_content += f"This is from:{absolute_path}\n"
                formatted_infra_content += f"```yaml\n{yaml.dump(global_keys, sort_keys=False)}\n```"
                
                parsed_material.append({
                    'metadata': {},
                    'topic': infra_header,
                    'material': {},
                    'content': formatted_infra_content,
                    'paths': {}
                })
            
            continue

        first_key = next(iter(document))
        header = f"YAML {search_header} {first_key}"
        formatted_content = f"## {header}\n\n"
        if 'resources' in document:
            file_path_split = absolute_path.split('/')
            used_file = file_path_split[-1].split('.')[0]
            if 'kustomization' in used_file:
                header = f"YAML {search_header} Kubernetes Kustomize"
                formatted_content = f"## {header}\n\n"
            
        formatted_content += f"This is from:{absolute_path}\n"
        formatted_content += f"```yaml\n{yaml.dump(document)}```"

        parsed_material.append({
            'metadata': {},
            'topic': header,
            'material': {},
            'content': formatted_content,
            'paths': {}
        })

    return parsed_material