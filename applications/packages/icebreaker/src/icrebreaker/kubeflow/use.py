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
    kfp_client: any,
    pipeline_function: any,
    run_name: str,
    experiment_name: str,
    pipeline_arguments: any,
    timeout: int
):
    try:
        import time as t
    except ImportError as e:
        raise ImportError("Failed to import", e)

    time_start = t.time()
    
    print('Submitting pipeline')
    run_details = kfp_client.create_run_from_pipeline_func(
        pipeline_func = pipeline_function,
        run_name = run_name,
        experiment_name = experiment_name,
        arguments = pipeline_arguments,
        enable_caching = True
    )

    run_status = kubeflow_wait_run(
        kfp_client = kfp_client,
        timeout = timeout,
        run_id = run_details.run_id
    )

    print('Run status: ' + str(run_status))
    
    time_end = t.time()

    total_time = time_end-time_start

    print('Pipeline total time', total_time)

    return total_time