from pydantic import BaseModel, Field
from typing import Dict
 
class Swift(BaseModel):
    pre_auth_url: str = Field(alias = 'pre-auth-url')
    pre_auth_token: str = Field(alias = 'pre-auth-token')
    user_domain_name: str = Field(alias = 'user-domain-name')
    project_domain_name: str = Field(alias = 'project-domain-name')
    project_name: str = Field(alias = 'project-name')
    auth_version: str = Field(alias = 'auth-version')

class Bucket(BaseModel):
    target: str = Field(alias = 'target')
    prefix: str = Field(alias = 'prefix')
    user: str = Field(alias = 'user')

class Parameters(BaseModel):
    swift_parameters: Swift = Field(alias = 'swift-parameters')
    bucket_parameters: Bucket = Field(alias = 'bucket-parameters')
    storage_parameters: Dict = Field(alias = 'storage-parameters')