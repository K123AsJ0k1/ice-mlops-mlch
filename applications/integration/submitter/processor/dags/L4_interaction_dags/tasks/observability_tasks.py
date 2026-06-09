# check imports and function inputs
def observability_task_submitter_interaction(
    swift_parameters: any,
    bucket_parameters: any,
    storage_parameters: any  
) -> any:  
    try:
        from icebreaker.swift.setup import swift_setup_client
        from icebreaker.storage.management import object_storage_interaction
        from L4_interaction_dags.actions.observability_actions import (
            observability_action_airflow_interaction,
            observability_action_flower_interaction
        )
    except ImportError as e:
        raise ImportError("L4_interaction_dags/tasks/observability_tasks failed to import", e)

    print('Observability submitter interaction')
    # This uses apache-airflow-client==3.0.2
    # Updating will create changes, which show as validation errors
    # BE AWARE THAT ALL TIME IS IN UTC AND AIRFLOW UI SHOWS UTC+2 CORRECTED TIMES
    data_stored = False
    
    swift_client = swift_setup_client(
        swift_parameters = swift_parameters
    )
    # We might also need to save fastapi and celery logs
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
            'object-name': 'metr',
            'path-replacers': {
                'name': 'time-path'
            },
            'path-names': [],
            'overwrite': False
        },
        object_data = None,
        object_metadata = None 
    )
 
    data_stored = observability_action_flower_interaction(
        swift_client = swift_client,
        bucket_parameters = bucket_parameters,
        storage_parameters = storage_parameters,
        object_list = object_list
    )
    
    data_stored = observability_action_airflow_interaction(
        swift_client = swift_client,
        bucket_parameters = bucket_parameters,
        storage_parameters = storage_parameters,
        object_list = object_list
    )

    return data_stored