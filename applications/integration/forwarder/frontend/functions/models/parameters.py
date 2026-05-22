from pydantic import BaseModel, Field

class Parameters(BaseModel):
    bucket_prefix: str = Field(alias = 'bucket-prefix')
    ice_id: str = Field(alias = 'ice-id')
    user: str = Field(alias = 'user')
    used_client: str = Field(alias = 'used-client')
    pre_auth_url: str = Field(alias = 'pre-auth-url')
    pre_auth_token: str = Field(alias = 'pre-auth-token')
    user_domain_name: str = Field(alias = 'user-domain-name')
    project_domain_name: str = Field(alias = 'project-domain-name')
    project_name: str = Field(alias = 'project-name')
    auth_version: str = Field(alias = 'auth-version')