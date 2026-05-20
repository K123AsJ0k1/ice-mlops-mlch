from pydantic import BaseModel, Field
from typing import List, Dict
 
from .configs import Configs
from .job import Job
from .files import Files
from .properties import Properties
from .orch_state import OrchState
from .time import Time
  
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