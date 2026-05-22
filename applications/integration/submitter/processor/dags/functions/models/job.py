from pydantic import BaseModel, Field
from typing import List

from functions.models.job_status import JobStatus 
from functions.models.time import Time

'''
Job definitions:
- path = file path in platrom (platform intearction)
- id = platfrom job SLURM id (platfrom interaction)
- status = job details
- time = time detailes gathered from the job
'''
  
class Job(BaseModel):
    path: str = Field(alias = 'path')
    id: str = Field('fill', alias = 'id')
    status: JobStatus = Field(alias = 'status')
    times: List[Time] = Field(default_factory = list, alias = 'times')