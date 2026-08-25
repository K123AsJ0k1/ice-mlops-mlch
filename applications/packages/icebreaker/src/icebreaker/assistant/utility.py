'''
def assistant_run_inference(
    inference_address: str,
    inference_path: str,
    sent_request: str
):
    try:
        from ..ray.use import ray_serve_route
        import time as t
    except ImportError as e:
        raise ImportError("assistant/utility failed to import", e)
    
    request_time_start = t.time()
    print('Sending request')
    status_code, route_output = ray_serve_route(
        route_address = inference_address,
        route_path = inference_path,
        route_type = 'POST',
        route_input = sent_request,
        timeout = 5
    )

    request_end_time = t.time()
    request_total_time = round(request_end_time-request_time_start,5)
    print(f'Spent seconds request: {request_total_time}')

    model_output = None
    model_metrics = None

    if status_code == 200:
        print('Request success')
        output_status = route_output['status']

        if output_status == 'success':
            model_output = route_output['text']
            model_metrics = route_output['efficiency-metrics']
    else:
        print('Request fail')
    return model_output, model_metrics, request_total_time
'''