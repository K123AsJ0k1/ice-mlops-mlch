import ray
from functions.utility import utility_managed_span
from icebreaker.mlflow.use import mlflow_get_prompt
from icebreaker.mlflow.utility import mlflow_token_usage, mlflow_llm_cost, mlflow_llm_effiency

def assistant_send_request(
    mlflow_client: any,
    span_name: str,
    trace_id: any,
    root_span_id: any,
    prompt_name: str,
    prompt_version: str,
    prompt_replacements: dict,
    assistant_ref: any,
    trace_attributes: dict,
    pipeline_record: dict
):
    with utility_managed_span( 
        mlflow_client = mlflow_client, 
        span_name = span_name, 
        trace_id = trace_id, 
        parent_span_id = root_span_id
    ) as assistant_span:
        assistant_prompt = mlflow_get_prompt(
            mlflow_client = mlflow_client,
            prompt_name = prompt_name,
            prompt_version = prompt_version,
            prompt_replacements = prompt_replacements
        )

        sent_prompt = assistant_prompt['prompt']
        assistant_config = assistant_prompt['config']

        assistant_span_input = {
            'messages': sent_prompt
        }

        pipeline_record['assistant-data']['input'] = assistant_span_input

        assistant_span.set_inputs(assistant_span_input)

        assistant_span.set_attributes({f'request.{k}': v for k, v in assistant_config.items()})

        coding_assistant_request = assistant_span_input | assistant_config

        coding_assistant_request_ref = ray.put(coding_assistant_request)
        
        coding_assistant_ref = assistant_ref.generate_output.remote(
            request = coding_assistant_request_ref 
        )

        coding_assistant_payload = ray.get(coding_assistant_ref)
        coding_assistant_output = 'failed'
        coding_assistant_metadata = {
            'assistant-variant': prompt_name
        }
        print(f'Coding assistant request status: {coding_assistant_payload['status']}')
        if coding_assistant_payload['status'] == 'success':
            coding_assistant_metrics = coding_assistant_payload['metrics']
            coding_assistant_output = coding_assistant_payload['response']
            coding_assistant_metadata = coding_assistant_payload['metadata']

            assistant_span.set_attributes(
                mlflow_token_usage(
                    input_tokens = coding_assistant_metrics['prompt-tokens'], 
                    output_tokens = coding_assistant_metrics['completion-tokens']
                )
            )

            input_cost = trace_attributes['utilization-cost-sec'] * coding_assistant_metrics['prompt-processing-time-sec']
            output_cost = trace_attributes['utilization-cost-sec'] * coding_assistant_metrics['generation-time-sec']
            
            coding_assistant_metadata['input-cost'] = input_cost
            coding_assistant_metadata['output-cost'] = output_cost
            coding_assistant_metadata['total-cost'] = input_cost + output_cost
                            
            model_name = f'{trace_attributes['assistant-repo-id']}-{trace_attributes['assistant-file-name']}'
            model_name = model_name.replace('*','')
            assistant_span.set_attributes(
                mlflow_llm_cost(
                    model_provider = trace_attributes['inference-framework'], 
                    model_name = model_name, 
                    input_cost = input_cost, 
                    output_cost = output_cost
                )
            )

            coding_assistant_metrics['input-cost'] = input_cost
            coding_assistant_metrics['output-cost'] = output_cost
            coding_assistant_metrics['total-cost'] = input_cost + output_cost
            pipeline_record['assistant-data']['metrics'] = coding_assistant_metrics

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

        span_output = {'answer': coding_assistant_output} | coding_assistant_metadata
                                
        pipeline_record['assistant-data']['output'] = span_output
        
        return coding_assistant_output 