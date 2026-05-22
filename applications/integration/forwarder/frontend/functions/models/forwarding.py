from pydantic import BaseModel, Field
from typing import List, Union

class Service(BaseModel):
    name: str = Field(alias = 'name')
    address: str = Field(alias = 'address')
    port: str = Field(alias = 'port')

class Forwarding(BaseModel):
    user: str = Field(alias = 'user')
    imports: Union[List[Service], List[None]] = Field(alias = 'imports')
    exports: Union[List[Service], List[None]] = Field(alias = 'exports')