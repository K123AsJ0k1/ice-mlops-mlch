import ray
import time as t
import mlflow
import json
from icebreaker.swift.setup import swift_setup_client
from icebreaker.objects.use import objects_get_data
#from icebreaker.assistant.utility import assistant_query_requests
from icebreaker.assistant.utility import assistant_format_context
from icebreaker.mlflow.setup import mlflow_setup_client
from icebreaker.mlflow.use import mlflow_create_trace, mlflow_end_trace, mlflow_get_prompt
from icebreaker.mlflow.utility import mlflow_token_usage, mlflow_llm_cost, mlflow_llm_effiency
from icebreaker.generator.utility import generator_extract_output, generator_format_data
from icebreaker.objects.use import objects_store_data, objects_get_prefix_list
from icebreaker.storage.management import storage_set_object_path

@ray.remote(
    num_cpus = 0.4,
    memory = 0.2 * 1024 * 1024 * 1024
) 
def answer_dataset(
    worker_index: int,
    actor_index: int,
    assistant_ref: any,
    retrieval_ref: any,
    controller_ref: any,
    swift_parameters: dict,
    mlflow_parameters: dict,
    retrieval_parameters: dict,
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

    collection_name = retrieval_parameters['collection-name']
    query_type = retrieval_parameters['query-type']
    relevance_threshold = retrieval_parameters['relevance-threshold']
    query_limit = retrieval_parameters['query-limit']
    fusion_limit = retrieval_parameters['fusion-limit']
    batch_size = retrieval_parameters['batch-size']
    
    for row in processed_subset.to_dict(orient = 'records'):
        for name, metadata in assistant_prompts.items():
            #inputs_data = row['inputs']
            #expectations_data = row['expectations']
            query_text = row['query']
            query_weights = json.loads(row['internal-material-ranks'])

            # Remember to put multiple spans for MLflow traces
            
            assistant_prompt_replacements = {
                'query': query_text
            }
            
            if 'bc' in name:
                controller_prompt = mlflow_get_prompt(
                    mlflow_client = mlflow_client,
                    prompt_name = controller_prompts['input']['name'],
                    prompt_version = controller_prompts['input']['version'],
                    prompt_replacements = {
                        'query': query_text
                    }
                )

                sent_prompt = controller_prompt['prompt']
                used_config = controller_prompt['config']

                controller_span_input = {
                    'messages': sent_prompt
                }

                controller_input_request = controller_span_input | used_config

                print(controller_input_request)
                # run controller

            if 'rag' in name:
                retrieval_query = [query_text]
                retrieval_query_ref = ray.put(retrieval_query)
                retrieval_payload_ref = retrieval_ref.batch_generate_queries.remote(
                    key_name = dataset_name,
                    query_type = query_type,
                    collection_name = collection_name,
                    text_query_batch = retrieval_query_ref,
                    relevant_weights_batch = query_weights,
                    relevance_threshold = relevance_threshold,
                    query_limit = query_limit,
                    fusion_limit = fusion_limit,
                    batch_size = batch_size
                )
                retrieval_payload = ray.get(retrieval_payload_ref)

                assistant_prompt_replacements['content'] = assistant_format_context(
                    query_results = retrieval_payload['results'],
                    wrapper_tag = 'context',
                    metadata_keys = [
                        'part',
                        'document',
                        'chapter',
                        'index',
                        'absolute-path',
                        'relevance'
                    ],
                    material_key = 'ref-material',
                    path_key = 'ref-paths',
                    content_key = 'content'
                )
        
            assistant_prompt = mlflow_get_prompt(
                mlflow_client = mlflow_client,
                prompt_name = name,
                prompt_version = metadata['version'],
                prompt_replacements = assistant_prompt_replacements
            )

            sent_prompt = assistant_prompt['prompt']
            used_config = assistant_prompt['config']

            assistant_span_input = {
                'messages': sent_prompt
            }

            assistant_request = assistant_span_input | used_config

            print(assistant_request)
            # run assistant

            if 'bc' in name:
                controller_prompt = mlflow_get_prompt(
                    mlflow_client = mlflow_client,
                    prompt_name = controller_prompts['output']['name'],
                    prompt_version = controller_prompts['output']['version'],
                    prompt_replacements = {
                        'query': query_text,
                        'output': 'test'
                    }
                )

                sent_prompt = controller_prompt['prompt']
                used_config = controller_prompt['config']

                controller_span_output = {
                    'messages': sent_prompt
                }

                controller_output_request = controller_span_output | used_config

                print(controller_output_request)
                # run controller

    end_time = t.time()
    total_time = round(end_time-start_time,5)
    print('Spent seconds', total_time)
    return {}