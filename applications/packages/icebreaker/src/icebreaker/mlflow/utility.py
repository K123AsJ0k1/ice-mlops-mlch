def mlflow_token_usage(
    input_tokens: int,
    output_tokens: int
) -> dict:
    return {
        'mlflow.chat.tokenUsage': {
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'total_tokens': input_tokens + output_tokens,
        }
    }

def mlflow_llm_cost(
    model_provider: str,
    model_name: str,
    input_cost: int,
    output_cost: int
) -> dict:
    return {
        'mlflow.llm.provider': model_provider,
        'mlflow.llm.model': model_name,
        'mlflow.llm.cost': {
            'input_cost': input_cost,
            'output_cost': output_cost,
            'total_cost': input_cost + output_cost,
        }
    }
    
def mlflow_llm_effiency(
    prompt_tokens: int,
    completion_tokens: int,
    total_tokens: int,
    prompt_processing_time: float,
    generation_time: float,
    input_tokens_per_sec: float,
    output_tokens_per_sec: float,
    total_latency: float,
    time_to_first_token: float,
    tokens_per_second: float,
    time_per_output_token: float,
    input_to_output_ratio: float,
    context_window_utilization: float
) -> dict:
    return {
        'mlflow.chat_model.prompt_tokens': prompt_tokens,
        'mlflow.chat_model.completion_tokens': completion_tokens,
        'mlflow.chat_model.total_tokens': total_tokens,
        'efficiency.prompt_processing_time_sec': round(prompt_processing_time, 4),
        'efficiency.generation_time_sec': round(generation_time, 4),
        'efficiency.input_tokens_per_sec': round(input_tokens_per_sec, 4),
        'efficiency.output_tokens_per_sec': round(output_tokens_per_sec, 4),
        'efficiency.total_latency_sec': round(total_latency, 4),
        'efficiency.time_to_first_token_sec': round(time_to_first_token, 4),
        'efficiency.tokens_per_sec': round(tokens_per_second, 4),
        'efficiency.time_per_output_token_sec': round(time_per_output_token, 4),
        'efficiency.input_to_output_ratio': round(input_to_output_ratio, 2),
        'efficiency.context_window_utilization_pct': round(context_window_utilization, 2),
    }
