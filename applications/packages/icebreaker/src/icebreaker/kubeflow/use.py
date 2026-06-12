# works with kfp=2.16.1
def kubeflow_wait_run(
    kfp_client: any,
    timeout: int,
    run_id: str
):
    try:
        import time as t
    except ImportError as e:
        raise ImportError("Failed to import", e)

    start = t.time()
    run_status = None
    print('Checking kubeflow run: ' + str(run_id))
    while t.time() - start <= timeout:
        run_details = kfp_client.get_run(
            run_id = run_id
        )
        run_status = run_details.state
        print('Run status: ' + str(run_status))
        if run_status == 'FAILED':
            run_status = False
            break
        if run_status == 'SUCCEEDED':
            run_status = True
            break
        if run_status == 'ERROR':
            run_status = True
            break
        t.sleep(10)
    return run_status

def kubeflow_manage_run(
    storage_client: any,
    kfp_client: any,
    pipeline_function: any,
    run_name: str,
    experiment_name: str,
    pipeline_arguments: any,
    timeout: int,
    cache_steps: bool,
    time_update_object: any
):
    try:
        import time as t
        from ..misc.time import time_run_update
        from ..misc.dict import fill_all_nested_dict_values, update_nested_dict
    except ImportError as e:
        raise ImportError("Failed to import", e)

    time_start = t.time()
    time_storage_parameters = pipeline_arguments['storage']['time-storage']
    time_object_name = time_storage_parameters['object-name']
    time_stored_1, time_index_1, time_name_1 = time_run_update(
        storage_client = storage_client,
        storage_parameters = time_storage_parameters,
        object_name = time_object_name,
        time_name = 'kubeflow-pipeline',
        start_time = time_start,
        end_time = 0,
        time_index = -1
    )
    
    name_update = {
        'time-storage': {
            'object-name': time_name_1
        }
    }

    updated_time_object = fill_all_nested_dict_values(
        target_dict = time_update_object,
        fill_values = {
            'storage': name_update,
            'general': name_update
        }
    )

    updated_pipeline_arguments = update_nested_dict(
        target_dict = pipeline_arguments,
        update_dict = updated_time_object
    )
    print('Submitting pipeline')
    run_details = kfp_client.create_run_from_pipeline_func(
        pipeline_func = pipeline_function,
        run_name = run_name,
        experiment_name = experiment_name,
        arguments = updated_pipeline_arguments,
        enable_caching = cache_steps
    )

    run_status = kubeflow_wait_run(
        kfp_client = kfp_client,
        timeout = timeout,
        run_id = run_details.run_id
    )

    print('Run status: ' + str(run_status))
    
    time_end = t.time()
    time_stored_2, time_index_2, time_name_2 = time_run_update(
        storage_client = storage_client,
        storage_parameters = time_storage_parameters,
        object_name = time_name_1,
        time_name = 'kubeflow-pipeline',
        start_time = 0,
        end_time = time_end,
        time_index = time_index_1
    )
    total_time = time_end-time_start
    print('Pipeline total time', total_time)
    return None