from pydantic import BaseModel, Field
from typing import List
 
class Direction(BaseModel):
    place: str = Field(alias = 'place')
    path: str = Field(alias = 'path')
    value: str = Field(alias = 'value')

class Transfer(BaseModel):
    source: Direction = Field(alias = 'source')
    target: Direction = Field(alias = 'target')

class Send(BaseModel):
    transfer: Transfer = Field(alias = 'transfer')
    overwrite: bool = Field(False, alias = 'overwrite')

class Get(BaseModel):
    transfer: Transfer = Field(alias = 'transfer')
    remove: bool = Field(False, alias = 'remove') 

class Files(BaseModel):
    send: List[Send] = Field(default_factory = list, alias = 'send')
    get: List[Get] = Field(default_factory = list, alias = 'get')