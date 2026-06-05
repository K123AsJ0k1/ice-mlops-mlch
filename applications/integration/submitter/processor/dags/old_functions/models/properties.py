from pydantic import BaseModel, Field
from typing import List, Dict

'''
Workspace definitions:
- path = platfrom workspace path
- used_capacity = platform workspace used memory 
- max_capacity = platform workspace available memory
- used_files = platform worksapce current file amount 
- max_files = platform workspace maximum file amount

Properties definitions:
- directory = default directory name in platform
- languages = dictionary of checked languages and their version in platfrom
- workspaces = Details of platform workspaces in platform
- modules = list of default platform modules
'''
   
class Workspace(BaseModel):
    path: str = Field('fill', alias = 'path')
    used_capacity: str = Field('fill', alias = 'used-capacity')
    max_capacity: str = Field('fill', alias = 'max-capacity')
    used_files: str = Field('fill', alias = 'used-files') 
    max_files: str = Field('fill', alias = 'max-files')

class Properties(BaseModel):
    directory: str = Field('fill', alias = 'directory')
    languages: Dict = Field(alias = 'languages')
    workspaces: List[Workspace] = Field(alias = 'workspaces')
    modules: List[str] = Field(default_factory = list, alias = 'modules')