from pydantic import BaseModel, Field
from typing import List

'''
Venv definitions:
- name = used platfrom venv name (platfrom interaction)
- path = used platform path (platfrom intearction)
- modules = used venv modules (platfrom interaction)
- packages = used venv packages (platfrom interaction)

Configs definitions:
- venv = used venv details (platfrom intearction)
'''
   
class Venv(BaseModel):
    name: str = Field(alias = 'name')
    path: str = Field(alias = 'path')
    modules: List[str] = Field(default_factory = list, alias = 'modules')
    packages: List[str] = Field(default_factory = list, alias = 'packages')
    
class Configs(BaseModel):
    venv: Venv = Field(alias = 'venv')