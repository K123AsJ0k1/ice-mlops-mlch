from pydantic import BaseModel, Field
from typing import List

'''
Direction definitions:
- place = indended file place 
- path = file path in the place
- access = way of using the file

Transfer definitions:
- source = place where the file is
- target = place where we want to move the file

Send definitions:
- transfer = file transfer details (platfrom intearction)
- overwrite = yes/no for file overwrite (platfrom intearction)

Get definitions:
- transfer = file transfer details (platfrom intearction)
- remove = yes/no for file removal (platfrom intearction)

Files definitions:
- send = transfer details for sending files (platfrom intearction)
- get = transfer details for getting files (platfrom intearction)
'''
    
class Direction(BaseModel):
    place: str = Field(alias = 'place')
    path: str = Field(alias = 'path')
    access: str = Field(alias = 'access')

class Transfer(BaseModel):
    source: Direction = Field(alias = 'source')
    target: Direction = Field(alias = 'target')

class Send(BaseModel):
    transfer: Transfer = Field(alias = 'transfer')
    overwrite: bool = Field(False, alias = 'overwrite')

class Get(BaseModel):
    transfer: Transfer = Field(alias = 'transfer')
    remove: bool = Field(False, alias = 'remove') 
    jobs: List[str] = Field(default_factory = list, alias = 'jobs')

class Files(BaseModel):
    send: List[Send] = Field(default_factory = list, alias = 'send')
    get: List[Get] = Field(default_factory = list, alias = 'get')