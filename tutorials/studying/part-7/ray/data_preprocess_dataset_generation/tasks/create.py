import ray
import time as t
import mlflow
from icebreaker.swift.setup import swift_setup_client
from icebreaker.objects.use import objects_get_data
from icebreaker.generator.utility import generator_make_requests
from icebreaker.mlflow.setup import mlflow_setup_client
from ..mlflow.use import mlflow_create_trace, mlflow_end_trace
from ..mlflow.utility import mlflow_token_usage, mlflow_llm_cost, mlflow_llm_effiency
from ..ray.utility import ray_run_inference
from ..generator.utility import generator_extract_output

@ray.remote(
    num_cpus = 1,
    memory = 0.2 * 1024 * 1024 * 1024
) 
def create_dataset(
    worker_index: int,
    actor_index: int,
    actor_ref: any,
    swift_parameters: any,
    mlflow_parameters: any,
    experiment_id: str,
    input_storage_parameters: dict,
    index_range: dict,
    used_prompts: dict
) -> any:
    start_time = t.time()
    print(f'Task {worker_index}, Actor {actor_index}')
    
    print('Setting up swift client')
    swift_client = swift_setup_client(
        swift_parameters = swift_parameters
    )
    print('Swift client setup') 

    print('Setup MLflow')  
    mlflow_client = mlflow_setup_client(
        mlflow_parameters = mlflow_parameters
    )
    
    data_object = objects_get_data(
        swift_client = swift_client,
        storage_parameters = {
            'bucket-target': input_storage_parameters['bucket-target'],
            'bucket-prefix': input_storage_parameters['bucket-prefix'],
            'bucket-user': input_storage_parameters['bucket-user'],
            'object-name': 'root',
            'object-serialization': input_storage_parameters['object-serialization'],
            'path-replacers': {
                'name': input_storage_parameters['object-path']
            },
            'path-names': [],
            'debug-prints': True,
            'lock-parameters': {},
            'lock-location': None,
            'overwrite': True
        },
        dict_format = False
    )  
    
    pandas_df = data_object[0]
    range_split = index_range.split('-')
    start_index = int(range_split[0])
    end_index = int(range_split[-1])
    dataset_name = input_storage_parameters['object-path'].split('/')[-1].split('.')[0]
    processed_subset = pandas_df.iloc[start_index:end_index]

    inference_requests = generator_make_requests(
        mlflow_client = mlflow_client,
        dataset_name = dataset_name,
        dataset_df = processed_subset,
        prompts = used_prompts
    )

    mlflow.set_experiment(
        experiment_id = experiment_id
    )

    trace_attributes = mlflow_parameters['trace-attributes']
    trace_name = mlflow_parameters['trace-name']
    trace_tags = mlflow_parameters['trace-tags']

    generator_data = {
        'parameters': trace_attributes,
        'inputs': [],
        'metrics': [],
        'outputs': []
    }
    sent_requests = 0
    for request in inference_requests:
        used_context = 0
        for key, value in request['metadata'].items():
            if 'prompt-length' in key:
                used_context += value

        if used_context < 2.5*trace_attributes['llm.n_ctx']:
            sent_prompt = request['prompt']
            used_config = request['config']
            prompt_metadata = request['metadata']
            prompt_metadata = prompt_metadata | used_config

            trace_input = {
                'messages': sent_prompt
            }

            generator_data['inputs'].append(trace_input)
        
            root_span = mlflow_create_trace(
                mlflow_client = mlflow_client,  
                trace_name = trace_name,
                experiment_id = experiment_id,
                trace_attributes = trace_attributes,
                trace_tags = trace_tags,
                trace_input = trace_input
            )
            
            root_span.set_attributes({f'request.{k}': v for k, v in used_config.items()})

            generator_request = trace_input | used_config

            request_ref = ray.put(generator_request)

            generator_ref = actor_ref.generate_output.remote(
                request = request_ref
            )
            sent_requests += 1
            generator_payload = ray.get(generator_ref)

            if generator_payload['status'] == 'success':
                generator_metrics = generator_payload['metrics']
                generator_metadata = generator_payload['metadata']
                generator_output = generator_payload['response']

                prompt_metadata['inference-server'] = generator_metadata['inference_server']
                prompt_metadata['model-name'] = generator_metadata['used_model']

                generator_data['metrics'].append(generator_metrics)
                
                root_span.set_attributes(
                    mlflow_token_usage(
                        input_tokens = generator_metrics['prompt-tokens'], 
                        output_tokens = generator_metrics['completion-tokens']
                    )
                )

                input_cost = trace_attributes['ice.utilization_cost_sec'] * generator_metrics['prompt-processing-time-sec']
                output_cost = trace_attributes['ice.utilization_cost_sec'] * generator_metrics['generation-time-sec']
                
                prompt_metadata['input-cost'] = input_cost
                prompt_metadata['output-cost'] = output_cost
                prompt_metadata['total-cost'] = input_cost + output_cost

                model_name = f'{trace_attributes['llm.model_repository']}-{trace_attributes['llm.model_quantization']}'
                root_span.set_attributes(
                    mlflow_llm_cost(
                        model_provider = trace_attributes['llm.inference_framework'], 
                        model_name = model_name, 
                        input_cost = input_cost, 
                        output_cost = output_cost
                    )
                )
                
                root_span.set_attributes(
                    mlflow_llm_effiency(
                        prompt_tokens = generator_metrics['prompt-tokens'],
                        completion_tokens = generator_metrics['completion-tokens'],
                        total_tokens = generator_metrics['total-tokens'],
                        prompt_processing_time = generator_metrics['prompt-processing-time-sec'],
                        generation_time = generator_metrics['generation-time-sec'],
                        input_tokens_per_sec = generator_metrics['input-tokens-per-sec'],
                        output_tokens_per_sec = generator_metrics['output-tokens-per-sec'],
                        total_latency = generator_metrics['total-latency-sec'],
                        time_to_first_token = generator_metrics['time-to-first-token-sec'],
                        tokens_per_second = generator_metrics['tokens-per-second'],
                        time_per_output_token = generator_metrics['time-per-output-token-sec'],
                        input_to_output_ratio = generator_metrics['input-to-output-ratio'],
                        context_window_utilization = generator_metrics['context-window-utilization-pct'],
                    )
                )
                
                extracted_output = generator_extract_output(
                    output = generator_output
                )

                trace_output = extracted_output | prompt_metadata

                generator_data['outputs'].append(trace_output)
                
                mlflow_end_trace(
                    mlflow_client = mlflow_client,
                    trace_id = root_span.trace_id,
                    trace_output = trace_output
                )

    # make the allas datasets have cluster name
   
    end_time = t.time()
    total_time = round(end_time-start_time,5)
    print('Spent seconds', total_time)
    return True