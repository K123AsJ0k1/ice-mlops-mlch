import ray
import time as t
import mlflow
import json
from icebreaker.swift.setup import swift_setup_client
from icebreaker.objects.use import objects_get_data
from icebreaker.controller.utility import controller_extract_output
from icebreaker.assistant.utility import assistant_format_context
from icebreaker.mlflow.setup import mlflow_setup_client
from icebreaker.mlflow.use import mlflow_create_trace, mlflow_end_trace, mlflow_get_prompt, mlflow_start_span, mlflow_end_span
from icebreaker.mlflow.utility import mlflow_token_usage, mlflow_llm_cost, mlflow_llm_effiency
from icebreaker.generator.utility import generator_extract_output, generator_format_data
from icebreaker.objects.use import objects_store_data, objects_get_prefix_list
from icebreaker.storage.management import storage_set_object_path

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
    for row in processed_subset.to_dict(orient = 'records'):
        for name, metadata in assistant_prompts.items():
            request_index += 1
            query_text = row['query']
            query_weights = json.loads(row['internal-material-ranks'])
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
                    trace_attributes = trace_attributes
                )
                
            print(f'Input behavior: {input_behavior}')
            if input_behavior.get('secret-leak') == 1 or input_behavior.get('off-topic') == 1:
                reasons = []
                if input_behavior.get('secret-leak') == 1: reasons.append("SECRET_LEAK")
                if input_behavior.get('off-topic') == 1: reasons.append("OFF_TOPIC")

                trace_output = {
                    'response': 'REFUSED INPUT',
                    'refusal-reason': " | ".join(reasons)
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
                    trace_attributes = trace_attributes 
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
                        assistant_output = coding_assistant_output
                    )

            print(f'Output behavior: {output_behavior}')
            if output_behavior.get('irrelevant') == 1 or output_behavior.get('verbose') == 1 or output_behavior.get('out-of-scope') == 1:
                reasons = []
                if output_behavior.get('irrelevant') == 1: reasons.append("IRRELEVANT")
                if output_behavior.get('verbose') == 1: reasons.append("VERBOSE")
                if output_behavior.get('out-of-scope') == 1: reasons.append("OUT_OF_SCOPE")
                
                trace_output = {
                    'response': 'REFUSED OUTPUT',
                    'refusal-reason': " | ".join(reasons)
                }
        
            print('Ending trace')
            mlflow_end_trace(
                mlflow_client = mlflow_client,
                trace_id = trace_id,
                trace_output = trace_output
            )

    mlflow.flush_trace_async_logging()
            
    end_time = t.time()
    total_time = round(end_time-start_time,5)
    print('Spent seconds', total_time)
    return {}