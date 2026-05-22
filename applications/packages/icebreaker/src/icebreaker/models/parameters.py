from pydantic import BaseModel, Field
from typing import List, Dict

class SwiftParameters(BaseModel):
    pre_auth_token: str = Field(alias = 'pre-auth-token')
    pre_auth_url: str = Field(alias = 'pre-auth-url')
    auth_version: str = Field(alias = 'auth-version')
    project_name: str = Field(alias = 'project-name')
    user_domain_name: str = Field(alias = 'user-domain-name')
    project_domain_name: str = Field(alias = 'project-domain-name')
    
class MLflowParameters(BaseModel):
    tracking_uri: str = Field(alias = 'tracking-uri')
    s3_endpoint_url: str = Field(alias = 's3-endpoint-url')
    experiment_name: str = Field(alias = 'experiment-name')
    run_name: str = Field(alias = 'run-name')
    run_tags: Dict[str, str] = Field(alias = 'run-tags')

class StorageParameters(BaseModel):
    swift: SwiftParameters = Field(alias = 'swift_parameters')
    mlflow: MLflowParameters = Field(alias = 'mlflow_parameters')

class IntegrationParameters(BaseModel):
    cluster_yamls: Dict = Field(alias = 'cluster-yamls')
    resource_weights: Dict[str, float] = Field(alias = 'resource-weights')

class ProcessParameters(BaseModel):
    worker: int = Field(alias = 'worker-number')
    actor: int = Field(alias = 'actor-number')

class JobParameters(BaseModel):
    main: str = Field(alias = 'main-file')
    runtime: Dict = Field(alias = 'runtime')

class ClusterParameters(BaseModel):
    process: ProcessParameters = Field(alias = 'process')
    job: JobParameters = Field(alias = 'job')

class Step(BaseModel):
    general: Dict = Field(alias = 'general-parameters')
    cluster: Dict[str,ClusterParameters] = Field(alias = 'cluster-parameters')
    
class Parameters(BaseModel):
    storage: StorageParameters = Field(alias = 'storage_parameters')
    integration: IntegrationParameters = Field(alias = 'integration_parameters')
    process: Dict[str, Step] = Field(alias = 'process_parameters')