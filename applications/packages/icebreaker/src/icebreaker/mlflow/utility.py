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
    

