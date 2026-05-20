def set_bucket_name(
    bucket_target: str,
    bucket_prefix: str,
    bucket_user: str,
    debug_prints: bool
) -> any:
    try:
        from ..misc.general import set_formatted_user
    except ImportError as e:
        raise ImportError("storage/management failed to import", e)

    bucket_names = {
        'forwarder': bucket_prefix + '-for-air',
        'submitter': bucket_prefix + '-sub-air-' + set_formatted_user(user = bucket_user),
        'pipeline': bucket_prefix + '-pipe-' + set_formatted_user(user = bucket_user),
        'experiment': bucket_prefix + '-exp-' + set_formatted_user(user = bucket_user)
    }
    bucket_name = bucket_names[bucket_target]
    
    if debug_prints:
        print('User object bucket: ' + str(bucket_name))
    return bucket_name

def set_object_path(
    object_name: str,
    path_replacers: any,
    path_names: any,
    debug_prints: bool
):
    object_paths = {
        'root': 'name',
        'code': 'CODE/name',
        'data': 'DATA/name',
        'arti': 'ARTIFACTS/name',
        'mana': 'MANAGEMENT/name',
        'time': 'TIMES/name',
        'logs': 'LOGS/name',
        'metr': 'METRICS/name'
    }

    i = 0
    path_split = object_paths[object_name].split('/')
    for name in path_split:
        if name in path_replacers:
            replacer = path_replacers[name]
            if 0 < len(replacer):
                path_split[i] = replacer
        i = i + 1
    
    if not len(path_names) == 0:
        path_split.extend(path_names)

    object_path = '/'.join(path_split)
    
    if debug_prints:
        print('Used object path: ' + str(object_path))
    return object_path

def object_storage_interaction(
    storage_client: any,
    lock_parameters: any,
    lock_location: str,
    parameters: any, 
    object_data: any,
    object_metadata: any
) -> any: 
    try:
        from .misc import create_object_index
        from ..swift.setup import swift_client_check
        from ..swift.use import swift_create_or_update_object, swift_check_object_metadata, swift_get_object_content, swift_get_bucket_info
        from ..interactions.concurrency import concurrency_get_client, concurrency_check_lock, concurrency_get_lock, concurrency_release_lock
    except ImportError as e:
        raise ImportError("storage/management failed to import", e)

    output = None 
    if swift_client_check(storage_client = storage_client):
        bucket_name = set_bucket_name(
            bucket_target = parameters['bucket-target'],
            bucket_prefix = parameters['bucket-prefix'],
            bucket_user = parameters['bucket-user'],
            debug_prints = parameters['debug-prints']
        )
        object_path = set_object_path(
            object_name = parameters['object-name'],
            path_replacers = parameters['path-replacers'],
            path_names = parameters['path-names'],
            debug_prints = parameters['debug-prints']
        )

        operate_storage = True
        lock_expected = False
        lock_client = None
        lock_active = False
        lock_name = ''

        specified_lock_parameters = {}
        if lock_location in lock_parameters:
            print('Using ' + str(lock_location) + ' lock')
            specified_lock_parameters = lock_parameters[lock_location]

        if 0 < len(specified_lock_parameters):
            lock_expected = True

        if lock_expected:
            specified_lock_parameters['group'] = bucket_name
            specified_lock_parameters['resource'] = object_path

            lock_client = concurrency_get_client(
                lock_parameters = specified_lock_parameters
            )

        if lock_expected and not lock_client is None:
            lock_active, lock_name = concurrency_check_lock(
                lock_parameters = specified_lock_parameters,
                lock_client = lock_client
            )

        if lock_expected and not lock_active:
            lock_created, client_lock = concurrency_get_lock(
                lock_client = lock_client,
                lock_name = lock_name
            )

        if lock_expected and not lock_created:
            operate_storage = False

        if operate_storage:
            try:
                if parameters['mode'] == 'check' or parameters['mode'] == 'send':
                    output = swift_check_object_metadata(
                        swift_client = storage_client,
                        bucket_name = bucket_name,
                        object_path = object_path
                    )
                if parameters['mode'] == 'send':
                    perform = True
                    if not len(output['general-meta']) == 0 and not parameters['overwrite']:
                        perform = False
                    if perform:
                        output = swift_create_or_update_object(
                            swift_client = storage_client,
                            bucket_name = bucket_name,
                            object_path = object_path,
                            object_data = object_data,
                            object_metadata = object_metadata
                        )
                if parameters['mode'] == 'get':
                    temporary = swift_get_object_content(
                        swift_client = storage_client,
                        bucket_name = bucket_name,
                        object_path = object_path
                    )
                    if 'data' in temporary:
                        output = (
                            temporary['data'],
                            temporary['general-meta'], 
                            temporary['custom-meta']
                        )
                if parameters['mode'] == 'index' or parameters['mode'] == 'list':
                    bucket_info = swift_get_bucket_info(
                        swift_client = storage_client,
                        bucket_name = bucket_name
                    ) 
                    if parameters['mode'] == 'index':
                        output = create_object_index(
                            object_path = object_path,
                            bucket_objects = bucket_info['objects']
                        )
                    if parameters['mode'] == 'list':
                        output = bucket_info['objects']
            except Exception as e:
                print('Object storage interaction error: ' + str(e))
        
        if lock_expected and lock_created:
            lock_released = concurrency_release_lock(
                lock_client = lock_client,
                client_lock = client_lock
            )
    return output