import ray
from functions.utility import utility_managed_span
from icebreaker.judge.utility import judge_extract_output
from icebreaker.mlflow.use import mlflow_get_prompt
from icebreaker.mlflow.utility import mlflow_token_usage, mlflow_llm_cost, mlflow_llm_effiency

def judge_send_request(
    mlflow_client: any,
    span_name: str,
    trace_id: any,
    root_span_id: any,
    prompt_name: str,
    prompt_version: str,
    prompt_replacements: dict,
    judge_ref: any,
    trace_attributes: dict,
    pipeline_record: dict
):
    with utility_managed_span(
        mlflow_client = mlflow_client, 
        span_name = span_name, 
        trace_id = trace_id, 
        parent_span_id = root_span_id
    ) as judge_span:
        judge_prompt = mlflow_get_prompt(
            mlflow_client = mlflow_client,
            prompt_name = prompt_name,
            prompt_version = prompt_version,
            prompt_replacements = prompt_replacements
        )

        sent_prompt = judge_prompt['prompt']
        judge_config = judge_prompt['config']

        judge_span_input = {
            'messages': sent_prompt
        }

        pipeline_record['judge-data']['input'] = judge_span_input

        judge_span.set_inputs(judge_span_input)

        judge_span.set_attributes({f'request.{k}': v for k, v in judge_config.items()})

        answer_judge_request = judge_span_input | judge_config

        answer_judge_request_ref = ray.put(answer_judge_request)
        
        answer_judge_ref = judge_ref.generate_output.remote(
            request = answer_judge_request_ref 
        )

        answer_judge_payload = ray.get(answer_judge_ref)
        
        answer_score = {
            'reasoning': '', 
            'correctness': 0,
            'faithfulness': 0,
            'relevance': 0,
        }

        answer_judge_metadata = {
            'judge-variant': prompt_name
        }
        print(f'Answer judge request status: {answer_judge_payload['status']}')
        if answer_judge_payload['status'] == 'success':
            answer_judge_metrics = answer_judge_payload['metrics']
            answer_judge_output = answer_judge_payload['response']
            answer_judge_metadata = answer_judge_payload['metadata']

            judge_span.set_attributes(
                mlflow_token_usage(
                    input_tokens = answer_judge_metrics['prompt-tokens'], 
                    output_tokens = answer_judge_metrics['completion-tokens']
                )
            )

            input_cost = trace_attributes['utilization-cost-sec'] * answer_judge_metrics['prompt-processing-time-sec']
            output_cost = trace_attributes['utilization-cost-sec'] * answer_judge_metrics['generation-time-sec']
            
            answer_judge_metadata['input-cost'] = input_cost
            answer_judge_metadata['output-cost'] = output_cost
            answer_judge_metadata['total-cost'] = input_cost + output_cost
                            
            model_name = f'{trace_attributes['judge-repo-id']}-{trace_attributes['judge-file-name']}'
            model_name = model_name.replace('*','')
            judge_span.set_attributes(
                mlflow_llm_cost(
                    model_provider = trace_attributes['inference-framework'], 
                    model_name = model_name, 
                    input_cost = input_cost, 
                    output_cost = output_cost
                )
            )

            answer_judge_metrics['input-cost'] = input_cost
            answer_judge_metrics['output-cost'] = output_cost
            answer_judge_metrics['total-cost'] = input_cost + output_cost
            pipeline_record['judge-data']['metrics'] = answer_judge_metrics

            judge_span.set_attributes(
                mlflow_llm_effiency(
                    prompt_tokens = answer_judge_metrics['prompt-tokens'],
                    completion_tokens = answer_judge_metrics['completion-tokens'],
                    total_tokens = answer_judge_metrics['total-tokens'],
                    prompt_processing_time = answer_judge_metrics['prompt-processing-time-sec'],
                    generation_time = answer_judge_metrics['generation-time-sec'],
                    input_tokens_per_sec = answer_judge_metrics['input-tokens-per-sec'],
                    output_tokens_per_sec = answer_judge_metrics['output-tokens-per-sec'],
                    total_latency = answer_judge_metrics['total-latency-sec'],
                    time_to_first_token = answer_judge_metrics['time-to-first-token-sec'],
                    tokens_per_second = answer_judge_metrics['tokens-per-second'],
                    time_per_output_token = answer_judge_metrics['time-per-output-token-sec'],
                    input_to_output_ratio = answer_judge_metrics['input-to-output-ratio'],
                    context_window_utilization = answer_judge_metrics['context-window-utilization-pct'],
                )
            ) 

            model_score = judge_extract_output(
                output = answer_judge_output
            )

            for key, value in model_score.items():
                answer_score[key] = value

        judge_span.set_outputs({
            'output': answer_score
        })

        span_output = answer_score | answer_judge_metadata
                                
        pipeline_record['judge-data']['output'] = span_output
        
        return answer_judge_output 