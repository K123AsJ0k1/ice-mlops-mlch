from pydantic import BaseModel, Field
from typing import List, Dict

from functions.models.configs import Configs
from functions.models.files import Files
from functions.models.job import Job

class Platform(BaseModel):
    configs: Configs = Field(alias = 'configs')
    files: Files = Field(default_factory = list, alias = 'files')
    jobs: List[Job] = Field(default_factory = list, alias = 'jobs') 

class Orchestration(BaseModel):
    name: str = Field(alias = 'name')
    platforms: Dict[str, Platform] = Field(alias = 'platforms')