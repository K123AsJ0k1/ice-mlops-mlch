import ray
from icebreaker.controller.utility import controller_extract_output
from icebreaker.mlflow.use import mlflow_get_prompt
from icebreaker.mlflow.utility import mlflow_token_usage, mlflow_llm_cost, mlflow_llm_effiency
from functions.utility import utility_managed_span

def controller_input_check(
    mlflow_client: any,
    span_name: str,
    trace_id: any,
    root_span_id: any,
    controller_prompts: dict,
    query_text: str,
    controller_ref: any,
    trace_attributes: dict,
    pipeline_record: dict
):
    with utility_managed_span(
        mlflow_client = mlflow_client, 
        span_name = span_name, 
        trace_id = trace_id, 
        parent_span_id = root_span_id
    ) as input_bc_span:
        print('Checking the input with behavior controller')

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

        pipeline_record['input-controller-data']['input'] = controller_input

        input_bc_span.set_attributes({f'request.{k}': v for k, v in controller_config.items()})

        input_bc_span.set_inputs(controller_input)

        input_controller_request = controller_input | controller_config

        controller_request_ref = ray.put(input_controller_request)

        input_controller_ref = controller_ref.generate_output.remote(
            request = controller_request_ref
        )

        input_controller_payload = ray.get(input_controller_ref)

        input_behavior = {
            'reasoning': '', 
            'secret-leak': 0, 
            'off-topic': 0
        }
        input_controller_metadata = {}
        print(f'Input controller request status: {input_controller_payload['status']}')
        if input_controller_payload['status'] == 'success':
            try:
                input_controller_metrics = input_controller_payload['metrics']
                input_controller_output = input_controller_payload['response']
                input_controller_metadata = input_controller_payload['metadata']

                input_bc_span.set_attributes(
                    mlflow_token_usage(
                        input_tokens = input_controller_metrics['prompt-tokens'], 
                        output_tokens = input_controller_metrics['completion-tokens']
                    )
                )

                input_cost = trace_attributes['utilization-cost-sec'] * input_controller_metrics['prompt-processing-time-sec']
                output_cost = trace_attributes['utilization-cost-sec'] * input_controller_metrics['generation-time-sec']

                input_controller_metadata['input-cost'] = input_cost
                input_controller_metadata['output-cost'] = output_cost
                input_controller_metadata['total-cost'] = input_cost + output_cost
                
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

                input_controller_metrics['input-cost'] = input_cost
                input_controller_metrics['output-cost'] = output_cost
                input_controller_metrics['total-cost'] = input_cost + output_cost
                pipeline_record['input-controller-data']['metrics'] = input_controller_metrics

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

            except Exception:
                input_behavior = {
                    'reasoning': 'Malformed JSON returned by guardrail', 
                    'secret-leak': 0, 
                    'off-topic': 0
                }

        input_bc_span.set_outputs({
            'output': input_behavior
        })

        span_output = input_behavior | input_controller_metadata
                        
        pipeline_record['input-controller-data']['output'] = span_output

        return input_behavior

def controller_output_check(
    mlflow_client: any,
    span_name: str,
    trace_id: any,
    root_span_id: any,
    controller_prompts: dict,
    query_text: str,
    controller_ref: any,
    trace_attributes: dict,
    assistant_output: str,
    pipeline_record: dict
):
    with utility_managed_span(
        mlflow_client = mlflow_client, 
        span_name = span_name, 
        trace_id = trace_id, 
        parent_span_id = root_span_id
    ) as output_bc_span: 
        print('Checking output with behavior controller')
        controller_prompt = mlflow_get_prompt(
            mlflow_client = mlflow_client,
            prompt_name = controller_prompts['output']['name'],
            prompt_version = controller_prompts['output']['version'],
            prompt_replacements = {
                'query': query_text,
                'output': assistant_output
            }
        )

        sent_prompt = controller_prompt['prompt']
        controller_config = controller_prompt['config']

        controller_input = {
            'messages': sent_prompt 
        }

        pipeline_record['output-controller-data']['input'] = controller_input

        output_bc_span.set_attributes({f'request.{k}': v for k, v in controller_config.items()})

        output_bc_span.set_inputs(controller_input)

        output_controller_request = controller_input | controller_config

        controller_request_ref = ray.put(output_controller_request)

        output_controller_ref = controller_ref.generate_output.remote(
            request = controller_request_ref
        )

        output_behavior = {
            'reasoning': '', 
            'irrelevant': 0, 
            'verbose': 0, 
            'out-of-scope': 0
        }

        output_controller_metadata = {}

        output_controller_payload = ray.get(output_controller_ref)
        print(f'Output controller request status: {output_controller_payload['status']}')
        if output_controller_payload['status'] == 'success':
            try:
                output_controller_metrics = output_controller_payload['metrics']
                output_controller_output = output_controller_payload['response']
                output_controller_metadata = output_controller_payload['metadata']

                output_bc_span.set_attributes(
                    mlflow_token_usage(
                        input_tokens = output_controller_metrics['prompt-tokens'], 
                        output_tokens = output_controller_metrics['completion-tokens']
                    )
                )
    
                input_cost = trace_attributes['utilization-cost-sec'] * output_controller_metrics['prompt-processing-time-sec']
                output_cost = trace_attributes['utilization-cost-sec'] * output_controller_metrics['generation-time-sec']

                output_controller_metadata['input-cost'] = input_cost
                output_controller_metadata['output-cost'] = output_cost
                output_controller_metadata['total-cost'] = input_cost + output_cost
                
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

                output_controller_metrics['input-cost'] = input_cost
                output_controller_metrics['output-cost'] = output_cost
                output_controller_metrics['total-cost'] = input_cost + output_cost
                pipeline_record['output-controller-data']['metrics'] = output_controller_metrics
    
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

            except Exception:
                output_behavior = {
                    'reasoning': 'Malformed JSON returned by guardrail', 
                    'irrelevant': 0, 
                    'verbose': 0, 
                    'out-of-scope': 0
                }

        output_bc_span.set_outputs({
            'output': output_behavior
        })

        span_output = output_behavior | output_controller_metadata
                                
        pipeline_record['output-controller-data']['output'] = span_output

        return output_behavior