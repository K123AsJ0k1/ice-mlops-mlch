# Check imports and inputs
def storage_task_object_interaction(
    swift_parameters: any,
    bucket_parameters: any,
    storage_parameters: any
) -> bool:
    try:
        from icebreaker.swift.setup import swift_setup_client
        from L4_interaction_dags.actions.storage_actions import (
            storage_action_orchestration_interaction,
            storage_action_logs_interaction,
            storage_action_metrics_interaction
        )
    except ImportError as e:
        raise ImportError("L4_interaction_dags/tasks/storage_tasks failed to import", e)

    print('Storage object interaction')
    object_stored = False

    data_type = storage_parameters['data-type']

    valid_types = [
        'object-orch',
        'object-logs',
        'object-metrics'
    ]
    print('Given data type: ' + str(data_type))
    if data_type in valid_types:
        swift_client = swift_setup_client(
            swift_parameters = swift_parameters
        )
        print('Swift connection created')
        if data_type == valid_types[0]:
            print('Orchestration interaction')
            object_stored = storage_action_orchestration_interaction(
                swift_client = swift_client,
                bucket_parameters = bucket_parameters,
                storage_parameters = storage_parameters
            )
        if data_type == valid_types[1]:
            print('Log interaction')
            object_stored = storage_action_logs_interaction(
                swift_client = swift_client,
                bucket_parameters = bucket_parameters,
                storage_parameters = storage_parameters
            )
        if data_type == valid_types[2]:
            print('Metrics interaction')
            object_stored = storage_action_metrics_interaction(
                swift_client = swift_client,
                bucket_parameters = bucket_parameters,
                storage_parameters = storage_parameters
            )
    return object_stored