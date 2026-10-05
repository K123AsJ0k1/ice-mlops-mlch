def mlflow_setup_client(
    mlflow_parameters: any
):
    try:
        import mlflow
        import os
        from mlflow.client import MlflowClient
    except ImportError as e:
        raise ImportError("mlflow/setup failed to import", e)
    
    mlflow_s3_endpoint_url = mlflow_parameters['s3-endpoint-url']
    mlflow_aws_access_key_id = mlflow_parameters['aws-access-key-id']
    mlflow_aws_secret_access_key = mlflow_parameters['aws-secret-access-key']
    mlflow_tracking_uri = mlflow_parameters['tracking-uri']
    
    os.environ['MLFLOW_S3_ENDPOINT_URL'] = mlflow_s3_endpoint_url
    os.environ['AWS_ACCESS_KEY_ID'] = mlflow_aws_access_key_id
    os.environ['AWS_SECRET_ACCESS_KEY'] = mlflow_aws_secret_access_key
    
    mlflow.set_tracking_uri(mlflow_tracking_uri)
    mlflow_client = MlflowClient( 
        tracking_uri = mlflow_tracking_uri
    )
    return mlflow_client