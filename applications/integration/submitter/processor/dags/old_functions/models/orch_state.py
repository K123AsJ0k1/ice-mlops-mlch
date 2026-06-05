from pydantic import BaseModel, Field

'''
OrchOrder definitions (in acton order):
- config = user wants configuration for operations (user interaction)
- start = user wants operations to start (user interaction)
- stop = user wants to operations to stop (user intearction)

OrchIntearction definitions (in action order):
- filled = platform details filled (platform interaction)
- setup = platform ready for operations (platform interaction)
- running = platform is running jobs (platfrom interaction)
- stored = operation artifacts stored (platform interaction)
- cleaned = operation traces removed (platfrom intearction)

OrchSubmitter definitions (in action order):
- operating = submitter is operating orch (submitter state)
- monitoring = submitter is monitoring orch (submitter state)
- halted = submitter has stopped operating orch (submitter state)
- failed = submitter operations failed (submitter state)
- success = submitter operations success(submitter state)

OrchState defintions:
- order = user intearction details
- interaction = platform intearction details
- submitter = submitter interaction details
'''
  
class OrchOrder(BaseModel):
    config: bool = Field(False, alias = 'config')
    start: bool = Field(False, alias = 'start')
    stop: bool = Field(False, alias = 'stop')

class OrchInteraction(BaseModel):
    filled: bool = Field(False, alias = 'filled')
    setup: bool = Field(False, alias = 'setup') 
    running: bool = Field(False, alias = 'running')
    complete: bool = Field(False, alias = 'complete')
    stored: bool = Field(False, alias = 'stored')
    cleaned: bool = Field(False, alias = 'cleaned')

class OrchSubmitter(BaseModel):
    operating: bool = Field(False, alias = 'operating')
    monitoring: bool = Field(False, alias = 'monitoring')
    halted: bool = Field(False, alias = 'halted')
    failed: bool = Field(False, alias = 'failed')
    success: bool = Field(False, alias = 'success')

class OrchState(BaseModel):
    order: OrchOrder = Field(alias = 'order')
    interaction: OrchInteraction = Field(alias = 'interaction')
    submitter: OrchSubmitter = Field(alias = 'submitter')