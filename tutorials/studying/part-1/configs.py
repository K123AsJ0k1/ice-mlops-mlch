from pydantic import BaseModel, Field
from typing import List

class Venv(BaseModel):
    name: str = Field(alias = 'name')
    path: str = Field(alias = 'path')
    modules: List[str] = Field(default_factory = list, alias = 'modules')
    packages: List[str] = Field(default_factory = list, alias = 'packages')

class Configs(BaseModel):
    venv: Venv = Field(alias = 'venv')