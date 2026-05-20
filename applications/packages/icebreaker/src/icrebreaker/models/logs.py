from pydantic import BaseModel, Field
 
class Logs(BaseModel):
    name: str = Field(alias = 'name')
    rows: list[str] = Field(alias = 'rows')