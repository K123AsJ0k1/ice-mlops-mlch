from pydantic import BaseModel, Field
from typing import List, Dict
 
from functions.models.configs import Configs
from functions.models.job import Job
from functions.models.files import Files
from functions.models.properties import Properties
from functions.models.orch_state import OrchState
from functions.models.time import Time
  
'''
Platfrom definitions:
- state = platform orchestration details (platform interaction)
- properties = platform property details (platform intearction)
- configs = platfrom configurations details (platfro intearction)
- files = orchestration file movement details (submitter intearctions)
- jobs = orchestration job details (platform intearctions)

Orchestration defintions:
- name = orchestration input name
- platfroms = orchestration platfrom details (platform intearctions)
- times = action time details gathered from orchestrating platroms
'''
 
class Platform(BaseModel):
    state: OrchState = Field(alias = 'state')
    properties: Properties = Field(alias = 'properties')
    configs: Configs = Field(alias = 'configs')
    files: Files = Field(default_factory = list, alias = 'files')
    jobs: List[Job] = Field(default_factory = list, alias = 'jobs') 
    times: List[Time] = Field(default_factory = list, alias = 'times')
    
class Orchestration(BaseModel):
    name: str = Field(alias = 'name')
    platforms: Dict[str, Platform] = Field(alias = 'platforms')
    times: List[Time] = Field(default_factory = list, alias = 'times')