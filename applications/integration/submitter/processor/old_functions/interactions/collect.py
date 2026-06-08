import pickle
import copy
import time as t

from functions.general import set_indexed_placeholders
from functions.dict import get_dict_value, create_nested_dict, update_dict_value

from functions.utility.misc import base_check_connection
from functions.utility.files import files_storage_path

from functions.swift.setup import swift_setup_client
from functions.storage.management import object_storage_interaction

from functions.actions.general import general_list_directory
from functions.actions.collect import collect_get_file, collect_get_sacct

from functions.utility.platform import platform_collect_commands
# Works
def check_job_validity(
    valid_jobs: list,
    job_index: int
) -> bool:
    valid = False
    for filter in valid_jobs:
        if filter == 'all':
            valid = True
            break
        if filter == str(job_index):
            valid = True
    return valid
# Works
def get_job_files(
    storage_parameters: any,
    lock_location: str,
    target_platform: str,
    platform_workspace: any,
    get_files: any,
    job_id: str,
    job_index: int
) -> list:
    platform_files = []
    for operation in get_files:
        print(operation)
        transfer = operation['transfer']
        transfer_source = transfer['source']
        transfer_target = transfer['target']
        valid_jobs = operation['jobs']
        operation_valid = check_job_validity(
            valid_jobs = valid_jobs,
            job_index = job_index
        )
        if operation_valid:
            if transfer_source['place'] == 'hpc':
                source_file_path = transfer_source['path']
                target_file_path = transfer_target['path']
                print(source_file_path)
                for workspace in platform_workspace:
                    workspace_path = workspace['path']
                    print(workspace_path)
                    if workspace_path in source_file_path:
                        if '{0}' in source_file_path:
                            source_file_path = set_indexed_placeholders(
                                text = source_file_path,
                                values = [
                                    job_id
                                ]
                            )
                            target_file_path = set_indexed_placeholders(
                                text = target_file_path,
                                values = [
                                    job_id
                                ]
                            )
                        
                        file_list = general_list_directory(
                            storage_parameters = storage_parameters,
                            lock_location = lock_location,
                            target_platform = target_platform,
                            target_path = workspace_path
                        )

                        source_file_name = source_file_path.split('/')[-1]
                        if source_file_name in file_list:
                            target_file_name = target_file_path.split('/')[-1]
                            local_name = target_platform + '-' + target_file_name
                            local_file_path = files_storage_path(
                                name = local_name
                            )
                            bucket_target = transfer_target['place'].split('/')[-1]
                            data_type = 'object-' + target_file_path.split('/')[1]
                            file_path = collect_get_file(
                                storage_parameters = storage_parameters,
                                lock_location = lock_location,
                                target_platform = target_platform,
                                local_file_path = local_file_path,
                                remote_file_path = source_file_path
                            )
                            platform_files.append({
                                'bucket-target':bucket_target, 
                                'data-type': data_type, 
                                'file-path': file_path
                            })
    return platform_files
# Works
def get_job_metrics(
    storage_parameters: any,
    lock_location: str,
    target_platform: str,
    job_id: str
) -> list:
    collect_commands = platform_collect_commands(
        target_platform = target_platform
    )
    platform_metrics = []
    if 0 < len(collect_commands):
        for name in collect_commands.keys():
            if name == 'slurm-sacct':
                sacct_path = collect_get_sacct(
                    storage_parameters = storage_parameters,
                    lock_location = lock_location,
                    target_platform = target_platform,
                    commands = collect_commands,
                    job_id = job_id
                )
                bucket_target = 'pipeline'
                data_type = 'object-metrics' 
                platform_metrics.append({
                    'bucket-target': bucket_target, 
                    'data-type': data_type, 
                    'file-path': sacct_path
                })
    return platform_metrics
# Works    
def collect_platform_interaction(
    swift_parameters: any,
    bucket_parameters: any,
    storage_parameters: any,
    platfrom_parameters: any   
) -> any:
    storage_dag_inputs = []
    platform_name = platfrom_parameters['name']
    target_platform = 'hpc-' + platform_name
    connection_exists = base_check_connection(
        connection_id = target_platform
    )
    print('Checking connections for ' + str(target_platform))
    if connection_exists:
        platform_collect_objects = platfrom_parameters['object-names']['collect']
        print('Checking amount of objects ' + str(len(platform_collect_objects)))
        if 0 < len(platform_collect_objects):
            collect_commands = platform_collect_commands(
                target_platform = target_platform
            )
            if 0 < len(collect_commands):
                swift_client = swift_setup_client(
                    swift_parameters = swift_parameters
                )
                bucket_target = bucket_parameters['target']
                bucket_prefix = bucket_parameters['prefix']
                bucket_user = bucket_parameters['user']
                debug_prints = storage_parameters['debug-prints']

                time_name = 'submitter-trigger|beat|celery|airflow|submitter-monitoring-sequence|submitter-collect-operation'
                
                interaction_timeout = False
                for object_name in platform_collect_objects:
                    platform_start_time = t.time()
                    orch_object = object_storage_interaction(
                        storage_client = swift_client,
                        lock_parameters = storage_parameters['lock'],
                        lock_location = storage_parameters['airflow-lock-location'],
                        parameters = {
                            'mode': 'get',
                            'bucket-target': bucket_target,
                            'bucket-prefix': bucket_prefix,
                            'bucket-user': bucket_user,
                            'debug-prints': debug_prints,
                            'object-name': 'mana',
                            'path-replacers': {
                                'name': object_name
                            },
                            'path-names': [],
                            'overwrite': False
                        },
                        object_data = None,
                        object_metadata = None
                    )
                    orch_data = pickle.loads(orch_object[0])

                    platform_path = 'platforms-' + platform_name
                    state_path = platform_path + '-state'
                    interaction_path = state_path + '-interaction'
                    submitter_path = state_path + '-submitter'
                    properties_workspaces_path = platform_path + '-properties-workspaces'
                    get_files_path = platform_path + '-files-get'
                    jobs_path = platform_path + '-jobs'
                    
                    platform_workspace = get_dict_value(
                        target_dict = orch_data,
                        key_path = properties_workspaces_path,
                        separator = '-'
                    )

                    get_files = get_dict_value(
                        target_dict = orch_data,
                        key_path = get_files_path,
                        separator = '-'
                    )

                    jobs = get_dict_value(
                        target_dict = orch_data,
                        key_path = jobs_path,
                        separator = '-'
                    )

                    update_dict = create_nested_dict(
                        target_dict = {},
                        key_path = state_path,
                        separator = '-'
                    ) 
                    
                    job_index = 0
                    update_list = []
                    job_times = []
                    platform_files = []
                    platform_metrics = []
                    for job in jobs:
                        job_start_time = t.time()
                        job_id = job['id']
                        job_status = job['status']
                        job_interaction = job_status['interaction']
                        job_submitter = job_status['submitter']
                        print(job_submitter)
                        print(job_interaction)
                        if job_submitter['halted']:
                            if not job_interaction['stored']:
                                platform_files = get_job_files(
                                    storage_parameters = storage_parameters,
                                    lock_location = storage_parameters['airflow-lock-location'],
                                    target_platform = target_platform,
                                    platform_workspace = platform_workspace,
                                    get_files = get_files,
                                    job_id = job_id,
                                    job_index = job_index
                                )
                                
                                if interaction_timeout:
                                    t.sleep(20)

                                platform_metrics = get_job_metrics(
                                    storage_parameters = storage_parameters,
                                    lock_location = storage_parameters['airflow-lock-location'],
                                    target_platform = target_platform,
                                    job_id = job_id
                                )
                                interaction_timeout = True

                                update_list.append({
                                    'status': {
                                        'interaction': {
                                            'stored': True
                                        },
                                        'submitter': {
                                            'success': True
                                        }
                                    }
                                })

                                job_end_time = t.time()
                                job_times.append(
                                    {
                                        'name': time_name,
                                        'start': job_start_time,
                                        'end': job_end_time
                                    }
                                )

                        job_index += 1

                    if 0 < len(update_list):
                        update_dict_value(
                            target_dict = update_dict,
                            key_path = jobs_path,
                            separator = '-',
                            new_value = update_list
                        )   

                        update_dict_value(
                            target_dict = update_dict,
                            key_path = interaction_path,
                            separator = '-',
                            new_value = {
                                'stored': True
                            }
                        )

                        update_dict_value(
                            target_dict = update_dict,
                            key_path = submitter_path,
                            separator = '-',
                            new_value = {
                                'success': True
                            }
                        )

                        print(update_dict)
                        print(platform_files)
                        print(platform_metrics)
                        if 0 < len(platform_files) or 0 < len(platform_metrics):
                            combined_data = platform_files + platform_metrics
                            print(combined_data)
                            for data_features in combined_data:
                                temp_bucket_parameters = copy.deepcopy(bucket_parameters)  
                                temp_bucket_parameters['target'] = data_features['bucket-target']
                                temp_storage_parameters = copy.deepcopy(storage_parameters)
                                temp_storage_parameters['store-action'] = 'create'
                                temp_storage_parameters['data-type'] = data_features['data-type']
                                temp_storage_parameters['file-path'] = data_features['file-path'] 

                                expand_input = {
                                    'trigger_dag_id': 'submitter-storage-interaction',
                                    'conf': {
                                        'swift-parameters': swift_parameters,
                                        'bucket-parameters': temp_bucket_parameters,
                                        'storage-parameters': temp_storage_parameters
                                    }
                                }
                                storage_dag_inputs.append(expand_input)

                        modified_storage_parameters = copy.deepcopy(storage_parameters)
                        modified_storage_parameters['object-key'] = object_name.split('.')[0]
                        modified_storage_parameters['object-input'] = update_dict

                        if 'general-time' in modified_storage_parameters:
                            modified_storage_parameters['general-time']['name'] = modified_storage_parameters['general-time']['name'] + '|submitter-collect-operation'

                        modified_storage_parameters['job-time'] = {
                            'target': platform_name,
                            'times': job_times
                        }

                        platform_end_time = t.time()
                        modified_storage_parameters['platform-time'] = {
                            'target': platform_name,
                            'name': time_name,
                            'start': platform_start_time, 
                            'end': platform_end_time
                        }

                        expand_input = {
                            'trigger_dag_id': 'submitter-storage-interaction',
                            'conf': {
                                'swift-parameters': swift_parameters,
                                'bucket-parameters': bucket_parameters,
                                'storage-parameters': modified_storage_parameters
                            }
                        }
                        storage_dag_inputs.append(expand_input)
    return storage_dag_inputs