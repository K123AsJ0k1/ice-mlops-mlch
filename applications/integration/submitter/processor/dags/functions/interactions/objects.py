import pickle

from functions.dict import get_dict_value

from functions.swift.setup import swift_setup_client
from functions.storage.management import object_storage_interaction
  
def objects_get_operated(
    swift_parameters: any,
    bucket_parameters: any,
    storage_parameters: any,
    process_parameters: any
) -> list:
    swift_client = swift_setup_client(
        swift_parameters = swift_parameters
    )

    bucket_target = bucket_parameters['target']
    bucket_prefix = bucket_parameters['prefix']
    bucket_user = bucket_parameters['user']
    debug_prints = storage_parameters['debug-prints']

    object_list = object_storage_interaction(
        storage_client = swift_client,
        lock_parameters = storage_parameters['lock'],
        lock_location = storage_parameters['airflow-lock-location'],
        parameters = {
            'mode': 'list',
            'bucket-target': bucket_target,
            'bucket-prefix': bucket_prefix,
            'bucket-user': bucket_user,
            'debug-prints': debug_prints,
            'object-name': 'mana',
            'path-replacers': {
                'name': 'key'
            },
            'path-names': [],
            'overwrite': False
        },
        object_data = None,
        object_metadata = None 
    )
    
    interacted_platforms = {}
    object_limit = process_parameters['object-limit']
    interaction_limit = process_parameters['interaction-limit']
    # Later consider how to remove unneeded objects
    # Prehaps moving completed objects into another path helps
    # Consider if key should be kept incremental after removals
    if 0 < len(object_list):
        checked_objects = 0
        for object_path in object_list.keys():
            if object_limit <= checked_objects:
                break
            checked_objects += 1
    
            object_name = object_path.split('/')[-1]
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

            platforms = orch_data['platforms'].keys()
            for name in platforms:
                platform_states_path = 'platforms-' + name + '-state'
                order_states_path = platform_states_path + '-order'
                interaction_states_path = platform_states_path + '-interaction'
                submitter_states_path = platform_states_path + '-submitter'

                order_states = get_dict_value(
                    target_dict = orch_data,
                    key_path = order_states_path,
                    separator = '-'
                )

                interaction_states = get_dict_value(
                    target_dict = orch_data,
                    key_path = interaction_states_path,
                    separator = '-'
                )

                submitter_states = get_dict_value(
                    target_dict = orch_data,
                    key_path = submitter_states_path,
                    separator = '-'
                )
                
                if not name in interacted_platforms:
                    interacted_platforms[name] = {
                        'fill': [],
                        'setup': [],
                        'run': []
                    }
                
                if not submitter_states['halted']:
                    if not interaction_states['running'] or not interaction_states['complete']:
                        if not order_states['stop'] :
                            if order_states['config']:
                                all_interactions = len(interacted_platforms[name]['fill']) + len(interacted_platforms[name]['setup']) + len(interacted_platforms[name]['run'])
                                if all_interactions < interaction_limit:
                                    if not interaction_states['filled']:
                                        interacted_platforms[name]['fill'].append(object_name)
                                        continue
                                    if not interaction_states['setup']:
                                        interacted_platforms[name]['setup'].append(object_name)
                                        continue
                                    if order_states['start']:
                                        # state order start and stop override job specific order
                                        # Add this
                                        interacted_platforms[name]['run'].append(object_name)
                                        continue
     
    sequence_dag_inputs = []
    platform_order = process_parameters['platform-order']
    for platform in platform_order:
        print(platform,interacted_platforms[platform])
        expand_input = {
            'trigger_dag_id': 'submitter-interaction-sequence',
            'conf': {
                'swift-parameters': swift_parameters,
                'bucket-parameters': bucket_parameters,
                'storage-parameters': storage_parameters,
                'platform-parameters': {
                    'name': platform,
                    'object-names': interacted_platforms[platform]
                }
            }
        }
        sequence_dag_inputs.append(expand_input)
    return sequence_dag_inputs
# Maybe consider refactoring these two into one later
def objects_get_monitored(
    swift_parameters: any,
    bucket_parameters: any,
    storage_parameters: any,
    process_parameters: any
):
    swift_client = swift_setup_client(
        swift_parameters = swift_parameters
    )

    bucket_target = bucket_parameters['target']
    bucket_prefix = bucket_parameters['prefix']
    bucket_user = bucket_parameters['user']
    debug_prints = storage_parameters['debug-prints']

    object_list = object_storage_interaction(
        storage_client = swift_client,
        lock_parameters = storage_parameters['lock'],
        lock_location = storage_parameters['airflow-lock-location'],
        parameters = {
            'mode': 'list',
            'bucket-target': bucket_target,
            'bucket-prefix': bucket_prefix,
            'bucket-user': bucket_user,
            'debug-prints': debug_prints,
            'object-name': 'mana',
            'path-replacers': {
                'name': 'key'
            },
            'path-names': [],
            'overwrite': False
        },
        object_data = None,
        object_metadata = None 
    )
    
    interacted_platforms = {}
    object_limit = process_parameters['object-limit']
    interaction_limit = process_parameters['interaction-limit']
    if 0 < len(object_list):
        checked_objects = 0
        for object_path in object_list.keys():
            if object_limit <= checked_objects:
                break
            checked_objects += 1
    
            object_name = object_path.split('/')[-1]
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

            platforms = orch_data['platforms'].keys()
            for name in platforms:
                platform_states_path = 'platforms-' + name + '-state'
                interaction_states_path = platform_states_path + '-interaction'

                interaction_states = get_dict_value(
                    target_dict = orch_data,
                    key_path = interaction_states_path,
                    separator = '-'
                )

                if not name in interacted_platforms:
                    interacted_platforms[name] = {
                        'check': [],
                        'collect': []
                    }
                
                if not interaction_states['cleaned']:
                    if interaction_states['running']:
                        all_interactions = len(interacted_platforms[name]['check']) + len(interacted_platforms[name]['collect'])
                        if all_interactions < interaction_limit:
                            if not interaction_states['complete']:
                                interacted_platforms[name]['check'].append(object_name)
                                continue
                            if not interaction_states['stored']:
                                interacted_platforms[name]['collect'].append(object_name)
                                continue
                                 
    sequence_dag_inputs = []
    platform_order = process_parameters['platform-order']
    for platform in platform_order:
        print(platform,interacted_platforms[platform])
        expand_input = {
            'trigger_dag_id': 'submitter-checking-sequence',
            'conf': {
                'swift-parameters': swift_parameters,
                'bucket-parameters': bucket_parameters,
                'storage-parameters': storage_parameters,
                'platform-parameters': {
                    'name': platform,
                    'object-names': interacted_platforms[platform]
                }
            }
        }
        sequence_dag_inputs.append(expand_input)
    return sequence_dag_inputs