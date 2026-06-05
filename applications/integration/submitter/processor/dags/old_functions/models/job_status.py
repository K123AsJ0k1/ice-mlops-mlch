from pydantic import BaseModel, Field
from typing import List
 
'''
JobOrder definitions:
- start = user orders the job to start (user intearction)
- stop = user orders the job to stop (user intearction)

JobIntearction definitions:
- submitter = platfrom submitter job (platform intearction)
- stopped = platform stopped the job (platform interaction)
- stored = job artifacts stored (platrom inteaction)
- cleanre = job traces cleaned (platfrom inteaction)

JobSubmitter definitions:
- operating = submitter is operating job (submitter state)
- monitoring = submitter is monitoring job (submitter job)
- halted = submitter halted the job (submitter job)
- failed = submitter operations failed (submitter state)
- success = submitter operations succeeded (submitter state)

JobStatus definitions:
- states = List of all the seen job states
- orders = user intearction details for the job
- intearction = platfrom intearction details for the job
- submitter = submitter interaction details for the job
'''

class JobOrder(BaseModel):
    start: bool = Field(False, alias = 'start')
    stop: bool = Field(False, alias = 'stop')

class JobInteraction(BaseModel):
    submitted: bool = Field(False, alias = 'submitted')
    stopped: bool = Field(False, alias = 'stopped')
    stored: bool = Field(False, alias = 'stored')
    cleaned: bool = Field(False, alias = 'cleaned')

class JobSubmitter(BaseModel):
    operating: bool = Field(False, alias = 'operating')
    monitoring: bool = Field(False, alias = 'monitoring')
    halted: bool = Field(False, alias = 'halted')
    failed: bool = Field(False, alias = 'failed')
    success: bool = Field(False, alias = 'success')

class JobStatus(BaseModel):
    states: List[str] = Field(alias = 'states')
    order: JobOrder = Field(alias = 'order')
    interaction: JobInteraction = Field(alias = 'interaction')
    submitter: JobSubmitter = Field(alias = 'submitter')