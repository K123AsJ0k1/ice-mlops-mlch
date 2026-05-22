from pydantic import BaseModel, Field
from typing import List

class Scheduler(BaseModel):
    times: List[str] = Field(alias = 'times')
