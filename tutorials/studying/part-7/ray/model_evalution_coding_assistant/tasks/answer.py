import ray
import time as t
import mlflow
import json
from icebreaker.swift.setup import swift_setup_client
from icebreaker.objects.use import objects_get_data
#from icebreaker.assistant.utility import assistant_query_requests
from icebreaker.controller.utility import controller_extract_output
from icebreaker.assistant.utility import assistant_format_context
from icebreaker.mlflow.setup import mlflow_setup_client
from icebreaker.mlflow.use import mlflow_create_trace, mlflow_end_trace, mlflow_get_prompt,mlflow_start_span
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

    collection_name = retrieval_parameters['collection-name']
    query_type = retrieval_parameters['query-type']
    relevance_threshold = retrieval_parameters['relevance-threshold']
    query_limit = retrieval_parameters['query-limit']
    fusion_limit = retrieval_parameters['fusion-limit']
    batch_size = retrieval_parameters['batch-size']

    mlflow.set_experiment(
        experiment_id = experiment_id
    )

    trace_attributes = mlflow_parameters['trace-attributes']
    trace_attributes = trace_attributes | assistant_parameters 
    trace_attributes = trace_attributes | retrieval_parameters
    trace_attributes = trace_attributes | controller_parameters

    trace_name = mlflow_parameters['trace-name']
    trace_tags = mlflow_parameters['trace-tags']
    
    for row in processed_subset.to_dict(orient = 'records'):
        for name, metadata in assistant_prompts.items():
            query_text = row['query']
            query_weights = json.loads(row['internal-material-ranks'])

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

            trace_output = {}
            if 'pe-rag-bc' in name:
                input_bc_span = mlflow_start_span(
                    mlflow_client = mlflow_client, 
                    span_name = 'behavior-controller-input-check',
                    trace_id = trace_id,
                    span_id = root_span_id
                )

                controller_prompt = mlflow_get_prompt(
                    mlflow_client = mlflow_client,
                    prompt_name = controller_prompts['input']['name'],
                    prompt_version = controller_prompts['input']['version'],
                    prompt_replacements = {
                        'query': query_text
                    }
                )

                sent_prompt = controller_prompt['prompt']
                controller_config = controller_prompt['config']

                controller_input = {
                    'messages': sent_prompt
                }

                input_bc_span.set_attributes({f'request.{k}': v for k, v in controller_config.items()})

                input_bc_span.set_inputs(controller_input)

                input_controller_request = controller_input | controller_config

                controller_request_ref = ray.put(input_controller_request)

                input_controller_ref = controller_ref.generate_output.remote(
                    request = controller_request_ref
                )

                input_controller_payload = ray.get(input_controller_ref)
                if input_controller_payload['status'] == 'success':
                    try:
                        input_controller_metrics = input_controller_payload['metrics']
                        input_controller_output = input_controller_payload['response']

                        input_bc_span.set_attributes(
                            mlflow_token_usage(
                                input_tokens = input_controller_metrics['prompt-tokens'], 
                                output_tokens = input_controller_metrics['completion-tokens']
                            )
                        )
            
                        input_cost = trace_attributes['utilization-cost-sec'] * input_controller_metrics['prompt-processing-time-sec']
                        output_cost = trace_attributes['utilization-cost-sec'] * input_controller_metrics['generation-time-sec']
                        
                        model_name = f'{trace_attributes['repo-id']}-{trace_attributes['file-name']}'
                        model_name = model_name.replace('*','')
                        input_bc_span.set_attributes(
                            mlflow_llm_cost(
                                model_provider = trace_attributes['inference-framework'], 
                                model_name = model_name, 
                                input_cost = input_cost, 
                                output_cost = output_cost
                            )
                        )
            
                        input_bc_span.set_attributes(
                            mlflow_llm_effiency(
                                prompt_tokens = input_controller_metrics['prompt-tokens'],
                                completion_tokens = input_controller_metrics['completion-tokens'],
                                total_tokens = input_controller_metrics['total-tokens'],
                                prompt_processing_time = input_controller_metrics['prompt-processing-time-sec'],
                                generation_time = input_controller_metrics['generation-time-sec'],
                                input_tokens_per_sec = input_controller_metrics['input-tokens-per-sec'],
                                output_tokens_per_sec = input_controller_metrics['output-tokens-per-sec'],
                                total_latency = input_controller_metrics['total-latency-sec'],
                                time_to_first_token = input_controller_metrics['time-to-first-token-sec'],
                                tokens_per_second = input_controller_metrics['tokens-per-second'],
                                time_per_output_token = input_controller_metrics['time-per-output-token-sec'],
                                input_to_output_ratio = input_controller_metrics['input-to-output-ratio'],
                                context_window_utilization = input_controller_metrics['context-window-utilization-pct'],
                            )
                        )

                        input_behavior = controller_extract_output(
                            output = input_controller_output
                        )
                        input_bc_span.set_outputs({
                            'output': input_behavior
                        })
                    except Exception:
                        input_behavior = {
                            'reasoning': 'Malformed JSON returned by guardrail', 
                            'secret-leak': 0, 
                            'off-topic': 0
                        }

            if input_behavior.get('secret-leak') == 0 or input_behavior.get('off-topic') == 0:
                if 'rag' in name:
                    retrieval_span = mlflow_start_span(
                        mlflow_client = mlflow_client, 
                        span_name = 'retrieval-augmented-generation-query',
                        trace_id = trace_id,
                        span_id = root_span_id
                    )

                    retrieval_query = [query_text]

                    retrieval_span.set_inputs({
                        'query': retrieval_query
                    })

                    retrieval_span.set_attributes({f'request.{k}': v for k, v in retrieval_parameters.items()})

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
                    
                    created_context = assistant_format_context(
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

                    retrieval_span.set_outputs({
                        'created-context': created_context
                    })

                    assistant_prompt_replacements['content'] = created_context

                assistant_span = mlflow_start_span(
                    mlflow_client = mlflow_client, 
                    span_name = 'coding-assistant-request',
                    trace_id = trace_id,
                    span_id = root_span_id
                )
            
                assistant_prompt = mlflow_get_prompt(
                    mlflow_client = mlflow_client,
                    prompt_name = name,
                    prompt_version = metadata['version'],
                    prompt_replacements = assistant_prompt_replacements
                )

                sent_prompt = assistant_prompt['prompt']
                assistant_config = assistant_prompt['config']

                assistant_span_input = {
                    'messages': sent_prompt
                }

                assistant_span.set_inputs(assistant_span_input)

                assistant_span.set_attributes({f'request.{k}': v for k, v in assistant_config.items()})

                coding_assistant_request = assistant_span_input | assistant_config

                coding_assistant_request_ref = ray.put(coding_assistant_request)
                
                coding_assistant_ref = assistant_ref.generate_output.remote(
                    request = coding_assistant_request_ref 
                )

                coding_assistant_payload = ray.get(coding_assistant_ref)
                if coding_assistant_payload['status'] == 'success':
                    coding_assistant_metrics = coding_assistant_payload['metrics']
                    coding_assistant_output = coding_assistant_payload['response']

                    assistant_span.set_attributes(
                        mlflow_token_usage(
                            input_tokens = coding_assistant_metrics['prompt-tokens'], 
                            output_tokens = coding_assistant_metrics['completion-tokens']
                        )
                    )
        
                    input_cost = trace_attributes['utilization-cost-sec'] * coding_assistant_metrics['prompt-processing-time-sec']
                    output_cost = trace_attributes['utilization-cost-sec'] * coding_assistant_metrics['generation-time-sec']
                    
                    model_name = f'{trace_attributes['repo-id']}-{trace_attributes['file-name']}'
                    model_name = model_name.replace('*','')
                    assistant_span.set_attributes(
                        mlflow_llm_cost(
                            model_provider = trace_attributes['inference-framework'], 
                            model_name = model_name, 
                            input_cost = input_cost, 
                            output_cost = output_cost
                        )
                    )
        
                    assistant_span.set_attributes(
                        mlflow_llm_effiency(
                            prompt_tokens = coding_assistant_metrics['prompt-tokens'],
                            completion_tokens = coding_assistant_metrics['completion-tokens'],
                            total_tokens = coding_assistant_metrics['total-tokens'],
                            prompt_processing_time = coding_assistant_metrics['prompt-processing-time-sec'],
                            generation_time = coding_assistant_metrics['generation-time-sec'],
                            input_tokens_per_sec = coding_assistant_metrics['input-tokens-per-sec'],
                            output_tokens_per_sec = coding_assistant_metrics['output-tokens-per-sec'],
                            total_latency = coding_assistant_metrics['total-latency-sec'],
                            time_to_first_token = coding_assistant_metrics['time-to-first-token-sec'],
                            tokens_per_second = coding_assistant_metrics['tokens-per-second'],
                            time_per_output_token = coding_assistant_metrics['time-per-output-token-sec'],
                            input_to_output_ratio = coding_assistant_metrics['input-to-output-ratio'],
                            context_window_utilization = coding_assistant_metrics['context-window-utilization-pct'],
                        )
                    )

                    assistant_span.set_outputs({
                        'output': coding_assistant_output
                    })

                    trace_output = {
                        'response': coding_assistant_output
                    }

                    if 'pe-rag-bc' in name:
                        output_bc_span = mlflow_start_span(
                            mlflow_client = mlflow_client, 
                            span_name = 'behavior-controller-output-check',
                            trace_id = trace_id,
                            span_id = root_span_id
                        )

                        controller_prompt = mlflow_get_prompt(
                            mlflow_client = mlflow_client,
                            prompt_name = controller_prompts['output']['name'],
                            prompt_version = controller_prompts['output']['version'],
                            prompt_replacements = {
                                'query': query_text,
                                'output': coding_assistant_output
                            }
                        )

                        controller_input = {
                            'messages': controller_prompt
                        }
        
                        output_bc_span.set_attributes({f'request.{k}': v for k, v in controller_config.items()})
        
                        output_bc_span.set_inputs(controller_input)
        
                        output_controller_request = controller_input | controller_config
        
                        controller_request_ref = ray.put(output_controller_request)
        
                        output_controller_ref = controller_ref.generate_output.remote(
                            request = controller_request_ref
                        )
        
                        output_controller_payload = ray.get(output_controller_ref)
                        if input_controller_payload['status'] == 'success':
                            try:
                                output_controller_metrics = output_controller_payload['metrics']
                                output_controller_output = output_controller_payload['response']
        
                                output_bc_span.set_attributes(
                                    mlflow_token_usage(
                                        input_tokens = output_controller_metrics['prompt-tokens'], 
                                        output_tokens = output_controller_metrics['completion-tokens']
                                    )
                                )
                    
                                input_cost = trace_attributes['utilization-cost-sec'] * output_controller_metrics['prompt-processing-time-sec']
                                output_cost = trace_attributes['utilization-cost-sec'] * output_controller_metrics['generation-time-sec']
                                
                                model_name = f'{trace_attributes['repo-id']}-{trace_attributes['file-name']}'
                                model_name = model_name.replace('*','')
                                output_bc_span.set_attributes(
                                    mlflow_llm_cost(
                                        model_provider = trace_attributes['inference-framework'], 
                                        model_name = model_name, 
                                        input_cost = input_cost, 
                                        output_cost = output_cost
                                    )
                                )
                    
                                output_bc_span.set_attributes(
                                    mlflow_llm_effiency(
                                        prompt_tokens = output_controller_metrics['prompt-tokens'],
                                        completion_tokens = output_controller_metrics['completion-tokens'],
                                        total_tokens = output_controller_metrics['total-tokens'],
                                        prompt_processing_time = output_controller_metrics['prompt-processing-time-sec'],
                                        generation_time = output_controller_metrics['generation-time-sec'],
                                        input_tokens_per_sec = output_controller_metrics['input-tokens-per-sec'],
                                        output_tokens_per_sec = output_controller_metrics['output-tokens-per-sec'],
                                        total_latency = output_controller_metrics['total-latency-sec'],
                                        time_to_first_token = output_controller_metrics['time-to-first-token-sec'],
                                        tokens_per_second = output_controller_metrics['tokens-per-second'],
                                        time_per_output_token = output_controller_metrics['time-per-output-token-sec'],
                                        input_to_output_ratio = output_controller_metrics['input-to-output-ratio'],
                                        context_window_utilization = output_controller_metrics['context-window-utilization-pct'],
                                    )
                                )

                                output_behavior = controller_extract_output(
                                    output = output_controller_output
                                )

                                output_bc_span.set_outputs({
                                    'output': output_behavior
                                })
                            except Exception:
                                output_behavior = {
                                    'reasoning': 'Malformed JSON returned by guardrail', 
                                    'irrelevant': 0, 
                                    'verbose': 0, 
                                    'out-of-scope': 0
                                }
            else:
                reasons = []
                if input_behavior.get('secret-leak') == 1: reasons.append("SECRET_LEAK")
                if input_behavior.get('off-topic') == 1: reasons.append("OFF_TOPIC")

                trace_output = {
                    'response': 'REFUSED_INPUT',
                    'refusal-reason': " | ".join(reasons)
                }

            if output_behavior.get('irrelevant') == 1 or output_behavior.get('verbose') == 1 or output_behavior.get('out-of-scope') == 1:
                reasons = []
                if output_behavior.get('irrelevant') == 1: reasons.append("IRRELEVANT")
                if output_behavior.get('verbose') == 1: reasons.append("VERBOSE")
                if output_behavior.get('out-of-scope') == 1: reasons.append("OUT_OF_SCOPE")
                
                trace_output = {
                    'response': 'REFUSED_OUTPUT',
                    'refusal-reason': " | ".join(reasons)
                }

            mlflow_end_trace(
                mlflow_client = mlflow_client,
                trace_id = trace_id,
                trace_output = trace_output
            )
            
    end_time = t.time()
    total_time = round(end_time-start_time,5)
    print('Spent seconds', total_time)
    return {}