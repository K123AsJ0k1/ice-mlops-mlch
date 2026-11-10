from icebreaker.mlflow.use import mlflow_start_span, mlflow_end_span
from contextlib import contextmanager

@contextmanager
def utility_managed_span(
    mlflow_client: any, 
    span_name: str, 
    trace_id: any, 
    parent_span_id: any
):
    span = mlflow_start_span(
        mlflow_client = mlflow_client,
        span_name = span_name,
        trace_id = trace_id,
        span_id = parent_span_id
    )
    try:
        yield span
    except Exception as e:
        span.set_attributes({'error.type': type(e).__name__, 'error.message': str(e)})
        span.set_status('ERROR')
        raise
    finally:
        print(f'Ending span {span_name}')
        mlflow_end_span(
            mlflow_client = mlflow_client,
            child_trace_id = trace_id,
            child_span_id = span.span_id
        )