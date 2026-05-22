from pydantic import BaseModel, Field
from typing import Dict, Optional 
 
class Row(BaseModel):
    job_id: Optional[str] = Field(required=False, default = 'empty', alias = 'job-id') 
    job_name: Optional[str] = Field(required=False, default = 'empty',alias = 'job-name') 
    account: Optional[str] = Field(required=False, default = 'empty', alias = 'account') 
    parition: Optional[str] = Field(required=False, default = 'empty', alias = 'partition') 
    req_cpus: Optional[int] = Field(required=False, default = 0, alias = 'req-cpus') 
    alloc_cpus: Optional[int] = Field(required=False, default = 0, alias = 'alloc-cpus') 
    req_nodes: Optional[int] = Field(required=False, default = 0, alias = 'req-nodes') 
    alloc_nodes: Optional[int] = Field(required=False, default = 0,alias = 'alloc-nodes') 
    state: Optional[str] = Field(required=False, default = 'empty',alias = 'state') 
    ave_cpu: Optional[float] = Field(required=False, default = 0, alias = 'ave-cpu-seconds') 
    ave_cpu_freq: Optional[float] = Field(required=False, default = 0, alias = 'ave-cpu-freq-khz') 
    ave_disk_read: Optional[float] = Field(required=False, default = 0, alias = 'ave-disk-read-bytes') 
    ave_disk_write: Optional[float] = Field(required=False, default = 0, alias = 'ave-disk-write-bytes') 
    timelimit: Optional[float] = Field(required=False, default = 0, alias = 'timelimit-seconds') 
    submit: Optional[float] = Field(required=False, default = 0, alias = 'submit-time') 
    start: Optional[float] = Field(required=False, default = 0,alias = 'start-time') 
    elapsed: Optional[float] = Field(required=False, default = 0,alias = 'elapsed-seconds') 
    planned: Optional[float] = Field(required=False, default = 0,alias = 'planned-seconds') 
    end: Optional[float] = Field(required=False, default = 0,alias = 'end-time') 
    planned_cpu: Optional[float] = Field(required=False, default = 0,alias = 'planned-cpu-seconds') 
    cpu_time: Optional[float] = Field(required=False, default = 0, alias = 'cpu-time-seconds') 
    total_cpu: Optional[float] = Field(required=False, default = 0, alias = 'total-cpu-seconds') 
   
class Sacct(BaseModel):
    name: str = Field(alias = 'name')
    rows: Dict[int, Row] = Field(alias = 'rows')
