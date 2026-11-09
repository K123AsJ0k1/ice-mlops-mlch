import ray
import time as t
import mlflow
import json
from icebreaker.swift.setup import swift_setup_client
from icebreaker.objects.use import objects_get_data
from icebreaker.mlflow.setup import mlflow_setup_client
from icebreaker.mlflow.use import mlflow_create_trace, mlflow_end_trace
from icebreaker.objects.use import objects_store_data, objects_get_prefix_list
from icebreaker.storage.management import storage_set_object_path
from icebreaker.assistant.utility import assistant_format_data

from functions.controller import controller_input_check, controller_output_check
from functions.retrieval import retrieval_send_query
from functions.assistant import assistant_send_request

@ray.remote(
    num_cpus = 0.4,
    memory = 0.2 * 1024 * 1024 * 1024
) 
def answer_dataset(
    worker_index: int,
    actor_index: int,
    assistant_ref: any,
    assistant_parameters: dict,
    retrieval_ref: any,
    retrieval_parameters: dict,
    controller_ref: any,
    controller_parameters: dict,
    swift_parameters: dict,
    mlflow_parameters: dict,
    experiment_id: str,
    input_storage_parameters: dict,
    output_storage_parameters: dict,
    worker_input: list,
    assistant_prompts: dict,
    controller_prompts: dict
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
    range_split = worker_input[0].split('-')
    start_index = int(range_split[0])
    end_index = int(range_split[-1])
    dataset_name = input_storage_parameters['object-path'].split('/')[-1].split('.')[0]
    processed_subset = pandas_df.iloc[start_index:end_index]
    print(f'Amount of rows: {len(processed_subset)}')

    mlflow.set_experiment(
        experiment_id = experiment_id
    )

    trace_attributes = mlflow_parameters['trace-attributes']
    trace_attributes = trace_attributes | assistant_parameters 
    trace_attributes = trace_attributes | retrieval_parameters
    trace_attributes = trace_attributes | controller_parameters

    trace_name = mlflow_parameters['trace-name']
    trace_tags = mlflow_parameters['trace-tags']
    request_index = 0

    pipeline_data = []
    for row in processed_subset.to_dict(orient = 'records'):
        pipeline_record = {
            'status': 'ACCEPTED', # ACCEPTED, REFUSED_INPUT, REFUSED_OUTPUT
            'refusal-reason': '',
            'assistant-variant': '',
            'assistant-query': query_text,
            'assistant-data': {
                'input': {},
                'metrics': {},
                'output': {}
            },
            'input-controller-data': {
                'input': {},
                'metrics': {},
                'output': {}
            },
            'output-controller-data': {
                'input': {},
                'metrics': {},
                'output': {}
            }
        }

        for name, metadata in assistant_prompts.items():
            request_index += 1
            query_text = row['query'] 
            query_weights = json.loads(row['internal-material-ranks'])
            pipeline_record['assistant-variant'] = name
            print('Starting trace')
            root_span = mlflow_create_trace(
                mlflow_client = mlflow_client,  
                trace_name = trace_name,
                experiment_id = experiment_id,
                trace_attributes = trace_attributes,
                trace_tags = trace_tags,
                trace_input = {
                    'query': query_text
                }
            )
            trace_id = root_span.trace_id
            root_span_id = root_span.span_id

            assistant_prompt_replacements = {
                'query': query_text
            }

            input_behavior = {
                'reasoning': '', 
                'secret-leak': 0, 
                'off-topic': 0
            }
            output_behavior = {
                'reasoning': '', 
                'irrelevant': 0, 
                'verbose': 0, 
                'out-of-scope': 0
            }

            print(f'Request index: {request_index}')
            print(f'Prompt variant: {name}')
            trace_output = {
                'response': 'failed',
                'refusal-reason': 'unknown'
            }
            
            if 'pe-rag-bc' in name:
                input_behavior = controller_input_check(
                    mlflow_client = mlflow_client,
                    span_name = 'behavior-controller-input-check',
                    trace_id = trace_id,
                    root_span_id = root_span_id,
                    controller_prompts = controller_prompts,
                    query_text = query_text,
                    controller_ref = controller_ref,
                    trace_attributes = trace_attributes,
                    pipeline_record = pipeline_record
                )
                
            print(f'Input behavior: {input_behavior}')
            if input_behavior.get('secret-leak') == 1 or input_behavior.get('off-topic') == 1:
                reasons = []
                if input_behavior.get('secret-leak') == 1: reasons.append("SECRET_LEAK")
                if input_behavior.get('off-topic') == 1: reasons.append("OFF_TOPIC")

                given_response = 'REFUSED INPUT'
                refusal_reason = " | ".join(reasons)
                pipeline_record['status'] = given_response
                pipeline_record['refusal-reason'] = refusal_reason
                trace_output = {
                    'response': given_response,
                    'refusal-reason': refusal_reason
                }

            if input_behavior.get('secret-leak') == 0 and input_behavior.get('off-topic') == 0:
                if 'rag' in name:
                    assistant_prompt_replacements['content'] = retrieval_send_query(
                        mlflow_client = mlflow_client, 
                        span_name = 'retrieval-augmented-generation-query',
                        trace_id = trace_id,
                        root_span_id = root_span_id,
                        retrieval_parameters = retrieval_parameters,
                        query_text = query_text,
                        retrieval_ref = retrieval_ref,
                        dataset_name = dataset_name,
                        query_weights = query_weights
                    )

                coding_assistant_output = assistant_send_request(
                    mlflow_client = mlflow_client, 
                    span_name = 'coding-assistant-request',
                    trace_id = trace_id,
                    root_span_id = root_span_id,
                    prompt_name = name,
                    prompt_version = metadata['version'],
                    prompt_replacements = assistant_prompt_replacements,
                    assistant_ref = assistant_ref,
                    trace_attributes = trace_attributes,
                    pipeline_record = pipeline_record
                )

                trace_output = {
                    'response': coding_assistant_output,
                    'refusal-reason': 'empty'
                }
                if 'pe-rag-bc' in name:
                    output_behavior = controller_output_check(
                        mlflow_client = mlflow_client, 
                        span_name = 'behavior-controller-output-check',
                        trace_id = trace_id,
                        root_span_id = root_span_id,
                        controller_prompts = controller_prompts,
                        query_text = query_text,
                        controller_ref = controller_ref,
                        trace_attributes = trace_attributes,
                        assistant_output = coding_assistant_output,
                        pipeline_record = pipeline_record
                    )

            print(f'Output behavior: {output_behavior}')
            if output_behavior.get('irrelevant') == 1 or output_behavior.get('verbose') == 1 or output_behavior.get('out-of-scope') == 1:
                reasons = []
                if output_behavior.get('irrelevant') == 1: reasons.append("IRRELEVANT")
                if output_behavior.get('verbose') == 1: reasons.append("VERBOSE")
                if output_behavior.get('out-of-scope') == 1: reasons.append("OUT_OF_SCOPE")

                given_response = 'REFUSED OUTPUT'
                refusal_reason = " | ".join(reasons)
                pipeline_record['status'] = given_response
                pipeline_record['refusal-reason'] = refusal_reason
                trace_output = {
                    'response': given_response,
                    'refusal-reason': refusal_reason
                }
        
            print('Ending trace')
            mlflow_end_trace(
                mlflow_client = mlflow_client,
                trace_id = trace_id,
                trace_output = trace_output
            )

            pipeline_data.append(pipeline_record)

    mlflow.flush_trace_async_logging() 

    formatted_data = assistant_format_data(
        assistant_data = pipeline_data,
        assistant_parameters = trace_attributes,
        metric_columns = [
            'prompt-tokens',
            'completion-tokens',
            'total-tokens',
            'total-latency-sec',
            'prompt-processing-time-sec',
            'generation-time-sec',
            'input-tokens-per-sec',
            'output-tokens-per-sec',
            'time-to-first-token-sec',
            'tokens-per-second',
            'time-per-output-token-sec',
            'input-to-output-ratio',
            'context-window-utilization-pct',
            'characters',
            'user-prompt-length',
            'input-cost',
            'output-cost',
            'total-cost'
        ]
    )

    name_start_prefix = output_storage_parameters['name-start-prefix']
    assistant_model_name = trace_attributes['repo-id'].split('/')[-1]
    artifact = {
        'parameters': formatted_data['parameters'],
        'metrics': formatted_data['metrics']
    }

    artifact_object_name = 'arti'
    artifact_path_replacers = {
        'name': 'METRICS'
    }

    artifact_path_name = f'{name_start_prefix}-assistant-{assistant_model_name}-metrics-{trace_attributes['used-enviroment']}-{dataset_name}-'

    artifact_temp_path_name = [
        artifact_path_name
    ]

    artifact_path = storage_set_object_path(
        object_name = artifact_object_name,
        path_replacers = artifact_path_replacers,
        path_names = artifact_temp_path_name,
        debug_prints = False
    )

    object_list = objects_get_prefix_list(
        storage_client = swift_client,
        storage_parameters = output_storage_parameters,
        path_prefix = artifact_path
    )

    next_index = len(object_list) + 1
    
    artifact_path_name += f'run-{next_index}.pkl'
    
    output_storage_parameters['object-name'] = artifact_object_name
    output_storage_parameters['object-serialization'] = 'pickle'
    output_storage_parameters['path-replacers'] = artifact_path_replacers
    output_storage_parameters['path-names'] = [
        artifact_path_name
    ]
    output_storage_parameters['debug-prints'] = True
    output_storage_parameters['lock-parameters'] = {}
    output_storage_parameters['lock-location'] = None
    output_storage_parameters['overwrite'] = True
    
    artifact_stored = objects_store_data(
        swift_client = swift_client,
        storage_parameters = output_storage_parameters,
        object_data = artifact,
        object_metadata = {}
    )
    
    table_object_name = 'data'
    table_path_replacers = {
        'name': 'ANSWERS'
    }

    table_path_name = f'{name_start_prefix}-assistant-{assistant_model_name}-data-{trace_attributes['used-enviroment']}-{dataset_name}-'

    table_temp_path_name = [
        table_path_name
    ]

    artifact_path = storage_set_object_path(
        object_name = table_object_name,
        path_replacers = table_path_replacers,
        path_names = table_temp_path_name,
        debug_prints = False
    )

    object_list = objects_get_prefix_list(
        storage_client = swift_client,
        storage_parameters = output_storage_parameters,
        path_prefix = artifact_path
    )

    next_index = len(object_list) + 1

    table_path_name += f'run-{next_index}.parquet'
        
    output_storage_parameters['object-name'] = table_object_name
    output_storage_parameters['object-serialization'] = 'parquet'
    output_storage_parameters['path-replacers'] = table_path_replacers
    output_storage_parameters['path-names'] = [
        table_path_name
    ]
    output_storage_parameters['debug-prints'] = True
    output_storage_parameters['lock-parameters'] = {}
    output_storage_parameters['lock-location'] = None
    output_storage_parameters['overwrite'] = True
    
    table_stored = objects_store_data(
        swift_client = swift_client,
        storage_parameters = output_storage_parameters,
        object_data = formatted_data['table'],
        object_metadata = {}
    ) 
    
    formatted_data['identity'] = dataset_name
        
    end_time = t.time()
    total_time = round(end_time-start_time,5)
    print('Spent seconds', total_time)
    return formatted_data