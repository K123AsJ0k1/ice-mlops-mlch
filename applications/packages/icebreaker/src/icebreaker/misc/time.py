
def time_edit_list(
    value_list: list,
    used_keys: any,
    time_name: any,
    start_time: int,
    end_time: int
) -> list:
    if 0 < start_time and 0 < end_time:
        total_time = (end_time-start_time)
        total_time = round(total_time, 5)
        if value_list[-1][used_keys[0]] == 'fill':
            value_list[-1][used_keys[0]] = time_name
            value_list[-1][used_keys[1]] = start_time
            value_list[-1][used_keys[2]] = end_time
            value_list[-1][used_keys[3]] = total_time
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
        if value_list[-1][used_keys[0]] == 'fill':
            value_list[-1][used_keys[0]] = time_name
            value_list[-1][used_keys[1]] = start_time
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
        for entry in reversed(value_list):
            if 0 == entry[used_keys[3]]:
                entry[used_keys[0]] = time_name
                entry[used_keys[2]] = end_time
                total_time = end_time - entry[used_keys[1]]
                total_time = round(total_time, 5)
                entry[used_keys[3]] = total_time
    return value_list

def time_orch_update(
    storage_parameters: any,
    orch_dict: any,
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