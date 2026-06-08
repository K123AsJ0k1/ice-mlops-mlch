from pydantic import BaseModel, Field
 
class Metadata(BaseModel):
    version: int = Field(alias = 'version')