def ray_run_inference(
    inference_address: str,
    inference_path: str,
    sent_request: str
):
    try:
        from ..ray.use import ray_serve_route
        import time as t
    except ImportError as e:
        raise ImportError("ray/utility failed to import", e)
    
    request_time_start = t.time()
    
    status_code, route_output = ray_serve_route(
        route_address = inference_address,
        route_path = inference_path,
        route_type = 'POST',
        route_input = sent_request,
        timeout = 5
    )
    request_end_time = t.time()
    request_total_time = round(request_end_time-request_time_start,5)
    
    model_output = {}
    if status_code == 200:
        print('Request success')
        output_status = route_output['status']

        if output_status == 'success':
            model_output = route_output
            model_output['request-total-time-sec'] = request_total_time
    else:
        print('Request fail')
    return model_output