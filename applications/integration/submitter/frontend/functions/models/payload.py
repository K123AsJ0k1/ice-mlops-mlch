from pydantic import BaseModel, Field

class Payload(BaseModel):
    mode: str = Field(None, alias = 'mode')
    type: str = Field(None, alias = 'type')
    input: str = Field(None, alias = 'input')