import ray
from functions.utility import utility_managed_span
from icebreaker.assistant.utility import assistant_format_context

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

def assistant_send_request(
    mlflow_client: any,
    span_name: str,
    trace_id: any,
    root_span_id: any,
    prompt_name: str,
    prompt_version: str,
    prompt_replacements: dict,
    assistant_ref: any,
    trace_attributes: dict
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

        assistant_span.set_inputs(assistant_span_input)

        assistant_span.set_attributes({f'request.{k}': v for k, v in assistant_config.items()})

        coding_assistant_request = assistant_span_input | assistant_config

        coding_assistant_request_ref = ray.put(coding_assistant_request)
        
        coding_assistant_ref = assistant_ref.generate_output.remote(
            request = coding_assistant_request_ref 
        )

        coding_assistant_payload = ray.get(coding_assistant_ref)
        coding_assistant_output = 'failed'
        print(f'Coding assistant request status: {coding_assistant_payload['status']}')
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

        return coding_assistant_output