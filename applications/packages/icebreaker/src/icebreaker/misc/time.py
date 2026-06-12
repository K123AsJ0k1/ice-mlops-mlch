
def time_edit_list(
    value_list: list,
    used_keys: list,
    time_name: any,
    start_time: int,
    end_time: int,
    time_index: int
) -> list:
    if 0 < start_time and 0 < end_time:
        total_time = (end_time-start_time)
        total_time = round(total_time, 5)
        if -1 < time_index and time_index < len(value_list):
            value_list[time_index][used_keys[0]] = time_name
            value_list[time_index][used_keys[1]] = start_time
            value_list[time_index][used_keys[2]] = end_time
            value_list[time_index][used_keys[3]] = total_time
        else:
            value_list.append(
                {
                    used_keys[0]: time_name, 
                    used_keys[1]: start_time, 
                    used_keys[2]: end_time, 
                    used_keys[3]: total_time
                }
            )
    elif 0 < start_time:
        if -1 < time_index and time_index < len(value_list):
            value_list[time_index][used_keys[0]] = time_name
            value_list[time_index][used_keys[1]] = start_time
        else:
            value_list.append(
                {
                    used_keys[0]: time_name, 
                    used_keys[1]: start_time, 
                    used_keys[2]: 0, 
                    used_keys[3]: 0
                }
            )
    elif 0 < end_time:
        if -1 < time_index and time_index < len(value_list):
            total_time = end_time - value_list[time_index][used_keys[1]]
            total_time = round(total_time, 5)
            value_list[time_index][used_keys[2]] = end_time
            value_list[time_index][used_keys[3]] = total_time
        else:
            for entry in reversed(value_list):
                if 0 == entry[used_keys[3]]:
                    entry[used_keys[0]] = time_name
                    entry[used_keys[2]] = end_time
                    total_time = end_time - entry[used_keys[1]]
                    total_time = round(total_time, 5)
                    entry[used_keys[3]] = total_time
    last_index = len(value_list) - 1 
    return value_list, last_index

def time_run_update(
    storage_client: any,
    storage_parameters: any,
    object_name: str,
    time_name: str,
    start_time: int,
    end_time: int,
    time_index: int
) -> bool:
    try:
        import pandas as pd
        from ..storage.management import object_storage_interaction
        from ..objects.use import objects_get_data, objects_store_data
    except ImportError as e: 
        raise ImportError("misc/time failed to import", e)

    object_list = object_storage_interaction(
        storage_client = storage_client,
        parameters = {
            'mode': 'list',
            'bucket-target': storage_parameters['bucket-target'],
            'bucket-prefix': storage_parameters['bucket-prefix'],
            'bucket-user': storage_parameters['bucket-user'],
            'object-name': 'root',
            'path-replacers': {
                'name': 'key'
            },
            'path-names': [],
            'overwrite': True,
            'debug-prints': True,
            'lock-parameters': {},
            'lock-location': ''
        }, 
        object_data = None,
        object_metadata = None
    ) 

    current_key_amount = 0
    existing_object_path = ''
    if 0 < len(object_list):
        for object_path, values in object_list.items():
            if object_name in object_path:
                checked_name = object_path.split('/')[-1].split('.')[0]
                if object_name == checked_name:
                    existing_object_path = object_path
                else:
                    current_key_amount += 1
    next_key = current_key_amount + 1

    time_dict_list = []
    object_type = 'time'
    used_object_name = object_name + '-' + str(next_key)
    name_replacer = used_object_name + '.parquet'
    stored_metadata = {'version': 1}
    if 0 < len(existing_object_path):
        formatted_data = objects_get_data(
            swift_client = storage_client,
            storage_parameters = {
                'bucket-target': storage_parameters['bucket-target'],
                'bucket-prefix': storage_parameters['bucket-prefix'],
                'bucket-user': storage_parameters['bucket-user'],
                'object-name': 'root',
                'object-serialization': 'parquet',
                'path-replacers': {
                    'name': existing_object_path
                },
                'path-names': [],
                'debug-prints': True,
                'lock-parameters': {},
                'lock-location': None,
                'overwrite': True
            },
            dict_format = False
        )
        time_dict_list = formatted_data[0].to_dict(orient = 'records')
        object_type = 'root'
        name_replacer = existing_object_path
        stored_metadata = formatted_data[-1]
        used_object_name = existing_object_path.split('/')[-1].split('.')[0]
        
    modified_dict_list, modified_dict_index = time_edit_list(
        value_list = time_dict_list,
        used_keys = [
            'name',
            'start',
            'end',
            'total'
        ],
        time_name = time_name,
        start_time = start_time,
        end_time = end_time,
        time_index = time_index
    )
    #print(modified_dict_list)
    stored_data = pd.DataFrame(modified_dict_list)
    #print(object_type, name_replacer)
    object_stored = objects_store_data(
        swift_client = storage_client,
        storage_parameters = {
            'bucket-target': storage_parameters['bucket-target'],
            'bucket-prefix': storage_parameters['bucket-prefix'],
            'bucket-user': storage_parameters['bucket-user'],
            'object-name': object_type,
            'object-serialization': 'parquet',
            'path-replacers': {
                'name': name_replacer
            },
            'path-names': [],
            'debug-prints': True,
            'lock-parameters': {},
            'lock-location': None,
            'overwrite': True
        },
        object_data = stored_data,
        object_metadata = stored_metadata
    )
    return object_stored, modified_dict_index, used_object_name
        
def time_orch_update(
    storage_parameters: any,
    orch_dict: any
):  
    try:
        import copy
        import time as t
        from .dict import update_nested_dict, get_dict_value, update_dict_value, create_nested_dict
    except ImportError as e:
        raise ImportError("Failed to import", e)

    changed_orch = copy.deepcopy(orch_dict)
    if 'general-time' in storage_parameters:
        general_time_path = 'times'
        current_times = get_dict_value(
            target_dict = changed_orch,
            key_path = general_time_path,
            separator = '-'
        )
        print(current_times)
        time_name = storage_parameters['general-time']['name'] + '|submitter-storage-interaction'
        time_start = storage_parameters['general-time']['start']
        time_end = t.time()

        updated_times = time_edit_list(
            value_list = current_times,
            used_keys = [
                'name',
                'start',
                'end',
                'total'
            ],
            time_name = time_name,
            start_time = time_start,
            end_time = time_end 
        )
        print(updated_times)
        update_dict_value(
            target_dict = changed_orch,
            key_path = general_time_path,
            separator = '-',
            new_value = updated_times
        )
        
    if 'platform-time' in storage_parameters:
        platform_time_target = storage_parameters['platform-time']['target']
        platform_time_path = 'platforms-' + platform_time_target + '-times'
        platform_time_name = storage_parameters['platform-time']['name']
        platform_time_start = storage_parameters['platform-time']['start']
        platform_time_end = storage_parameters['platform-time']['end']
        
        current_times = get_dict_value(
            target_dict = changed_orch,
            key_path = platform_time_path,
            separator = '-'
        )
        print(current_times)
        updated_times = time_edit_list(
            value_list = current_times,
            used_keys = [
                'name',
                'start',
                'end',
                'total'
            ],
            time_name = platform_time_name,
            start_time = platform_time_start,
            end_time = platform_time_end
        )
        print(updated_times)
        update_dict_value(
            target_dict = changed_orch,
            key_path = platform_time_path,
            separator = '-',
            new_value = updated_times
        )
    
    if 'job-time' in storage_parameters:
        job_time_target = storage_parameters['job-time']['target']
        jobs_path = 'platforms-' + job_time_target + '-jobs'
        jobs = get_dict_value(
            target_dict = changed_orch,
            key_path = jobs_path,
            separator = '-'
        )

        job_times = storage_parameters['job-time']['times']
        index = 0
        update_dict = create_nested_dict(
            target_dict = {},
            key_path = jobs_path,
            separator = '-'
        )
        job_time_updates = []
        for job in jobs:
            job_times_path = 'times'
            current_times = get_dict_value(
                target_dict = job,
                key_path = job_times_path,
                separator = '-'
            )   
            print(current_times)
            job_time_name = job_times[index]['name']
            job_time_start = job_times[index]['start']
            job_time_end = job_times[index]['end']

            updated_times = time_edit_list(
                value_list = current_times,
                used_keys = [
                    'name',
                    'start',
                    'end',
                    'total'
                ],
                time_name = job_time_name,
                start_time = job_time_start,
                end_time = job_time_end
            )
            print(updated_times)
            job_time_updates.append({
                'times': updated_times
            })
            index += 1
        print(job_time_updates)
        update_dict_value(
            target_dict = update_dict,
            key_path = jobs_path,
            separator = '-',
            new_value = job_time_updates
        )

        changed_orch = update_nested_dict(
            target_dict = changed_orch,
            update_dict = update_dict
        )

    return changed_orch