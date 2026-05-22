from pydantic import BaseModel, Field

class Job(BaseModel):
    path: str = Field(alias = 'path')