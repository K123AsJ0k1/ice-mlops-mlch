def setup_mlflow(
    mlflow_parameters: any
):
    try:
        import mlflow
        import os
        from mlflow.client import MlflowClient
    except ImportError as e:
        raise ImportError("mlflow/setup failed to import", e)
    
    mlflow_s3_endpoint_url = mlflow_parameters['s3-endpoint-url']
    mlflow_tracking_uri = mlflow_parameters['tracking-uri']
    
    os.environ['MLFLOW_S3_ENDPOINT_URL'] = mlflow_s3_endpoint_url
    
    mlflow.set_tracking_uri(mlflow_tracking_uri)
    mlflow_client = MlflowClient( 
        tracking_uri = mlflow_tracking_uri
    )
    return mlflow_client