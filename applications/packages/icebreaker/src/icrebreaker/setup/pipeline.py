
def create_pipeline_inputs(
    fragments_folder: str,
    fragments_prefix: str,
    fragments_order: list,
    details_folder: str,
    details_prefix: str,
    details_list: list,
    env_dict: str,
    input_list: any,
    output_folder: any,
    output_prefix: str
) -> any:
    try:
        from .fragments import compose_yaml_dict
    except ImportError as e:
        raise ImportError("Failed to import", e)

    pipeline_inputs = []
    index = 1
    for details_order in details_list:
        file_name = output_prefix.replace('[VERSION]', str(index))
        given_inputs = input_list[index-1]
        print('Generating file: ' + str(file_name))
        pipeline_input = compose_yaml_dict(
            fragments_folder = fragments_folder,
            fragments_prefix = fragments_prefix,
            fragments_order = fragments_order,
            details_folder = details_folder,
            details_prefix = details_prefix,
            details_order = details_order,
            env_dict = env_dict,
            dict_inputs = given_inputs,
            output_folder = output_folder,
            output_name = file_name
        )
        pipeline_inputs.append(pipeline_input)
        index += 1
    return pipeline_inputs

def send_pipeline_inputs(
    interaction_parameters: any,
    pipeline_inputs: any
) -> any:
    try:
        import time as t
        import copy
        from .interactions.integration import integration_task_interaction
    except ImportError as e:
        raise ImportError("Failed to import", e)

    route_outputs = []
    for pipeline_input in pipeline_inputs:
        time_start = t.time()
        route_data = copy.deepcopy(interaction_parameters)
        route_data['route-input']['input']['object-input'] = pipeline_input
        route_data['route-input']['input']['general-time'] = {
            'name': 'send-pipeline-inputs|jupyter|fastapi|celery|airflow',
            'start': time_start
        }
        
        task_output = integration_task_interaction(
            connection_parameters = route_data,
            task_name = 'tasks.submitter-requests',
            check_tries = 60,
            check_timeout = 1
        )

        route_outputs.append(task_output)
    return route_outputs

def get_pipeline_inputs(
    swift_client: any,
    storage_parameters: any,
    start_index: int,
    end_index: int
) -> any:
    try:
        import copy
        import pickle
        from .storage.management import object_storage_interaction
    except ImportError as e:
        raise ImportError("Failed to import", e)

    fetched_objects = []
    for number in range(start_index, end_index + 1):
        used_parameters = copy.deepcopy(storage_parameters)
        if not used_parameters['mode'] == 'get':
            used_parameters['mode'] = 'get'
        used_parameters['path-replacers']['name'] = str(number) + '.pkl'
        stored_object = object_storage_interaction(
            storage_client = swift_client,
            parameters = used_parameters,
            object_data = None,
            object_metadata = None
        )
        formatted_object = pickle.loads(stored_object[0])
        fetched_objects.append(formatted_object)
    return fetched_objects

def modify_pipeline_inputs(
    interaction_parameters: any,
    object_keys: list,
    details_list: list,
    modification_list: list
) -> any:
    try:
        import time as t
        import copy
        from .misc.dict import create_nested_dict, update_dict_value
        from .interactions.integration import integration_task_interaction
    except ImportError as e:
        raise ImportError("Failed to import", e)

    index = 0
    route_outputs = []
    for key in object_keys:
        time_start = t.time()
        route_data = copy.deepcopy(interaction_parameters)
        route_data['route-input']['input']['object-key'] = key
        route_data['route-input']['input']['general-time'] = {
            'name': 'modify-pipeline-inputs|jupyter|fastapi|celery|airflow',
            'start': time_start
        }
        
        modification_dict = {}
        for detail in details_list[index]:
            if len(modification_dict) == 0:
                modification_dict = create_nested_dict(
                    target_dict = {},
                    key_path = detail,
                    separator = '_'
                )

            update_dict_value(
                target_dict = modification_dict,
                key_path = detail,
                separator = '_',
                new_value = modification_list[index]
            )
        
        route_data['route-input']['input']['object-input'] = modification_dict
        
        task_output = integration_task_interaction(
            connection_parameters = route_data,
            task_name = 'tasks.submitter-requests',
            check_tries = 60,
            check_timeout = 1
        )
        
        route_outputs.append(task_output)
        index += 1
    return route_outputs

def generate_pipeline_files(
    env_dict: dict,
    input_paths: str,
    output_folder: str
):
    try:
        import re 
    except ImportError as e:
        raise ImportError("Failed to import", e)

    for input_path in input_paths:
        file_name = input_path.split('/')[-1]
        output_path = output_folder + '/' + file_name
        print('Using file: ', input_path)
        content = None
        with open(input_path, 'r') as f:
            content = f.read()
        pattern = r'\[([A-Z_1-9]+)\]'    
        updated_content = re.sub(
            pattern,
            lambda m: str(env_dict.get(m.group(1), m.group(0))),
            content
        ) 
        print('Writing file:', output_path)
        with open(output_path, 'w') as f:
            f.write(updated_content)
    
def store_pipeline_files(
    storage_client: any,
    file_parameters: any,
    pipeline_inputs: any
): 
    try:
        import time as t
        import copy
        from .misc.dict import get_dict_value
        from .storage.management import object_storage_interaction
    except ImportError as e:
        raise ImportError("Failed to import", e)

    pipeline_index = 1
    stored_files = []
    for pipeline_input in pipeline_inputs:
        for platform, values in pipeline_input['platforms'].items():
            files = get_dict_value(
                target_dict = values,
                key_path = 'files-send',
                separator = '-'
            )
            print('Checking files of input ' + str(pipeline_index) + ' with platform ' + str(platform))
            for file in files:
                file_source = file['transfer']['source']
                file_target = file['transfer']['target']

                target_place_split = file_target['place'].split('/')
                if target_place_split[0] == 'storage':
                    if target_place_split[1] == 'allas':
                        source_path_split = file_source['path'].split('/')[1:]
                        target_path_split = file_target['path'].split('/')[1:]
                        source_relative_path = '/'.join(source_path_split[1:])

                        source_file_path = file_parameters[source_path_split[0]] + '/' + source_relative_path
                        if not source_file_path in stored_files:
                            stored_data = None
                            with open(source_file_path, 'r') as f:
                                stored_data = f.read()
                            stored_metadata = {'version': 1}

                            print('Storing file in path: ', source_file_path)
                            bucket_target = target_place_split[-1]
                            object_stored = object_storage_interaction(
                                storage_client = storage_client,
                                parameters = {
                                    'mode': 'send',
                                    'bucket-target': bucket_target,
                                    'bucket-prefix': file_parameters['bucket-prefix'],
                                    'bucket-user': file_parameters['bucket-user'],
                                    'object-name': target_path_split[0],
                                    'path-replacers': {
                                        'name': target_path_split[1]
                                    },
                                    'path-names': target_path_split[2:],
                                    'overwrite': True
                                },
                                object_data = stored_data,
                                object_metadata = stored_metadata
                            )
                            if object_stored:
                                stored_files.append(source_file_path)
        pipeline_index += 1