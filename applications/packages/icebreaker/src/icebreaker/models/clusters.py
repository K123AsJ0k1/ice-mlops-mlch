from pydantic import BaseModel, Field
from typing import List, Dict

class GPU(BaseModel):
    hardware: str = Field(alias = 'hardware')
    vram: str = Field(alias = 'vram')

class Resources(BaseModel):
    nodes: str = Field(alias = 'nodes')
    cpu: str = Field(alias = 'cpu')
    ram: str = Field(alias = 'ram')
    gpu: List[GPU] = Field(default_factory = list, alias = 'gpu')

class Connections(BaseModel):
    dash: str = Field(alias = 'dash')
    serve: str = Field(alias = 'serve')

class Network(BaseModel):
    kubernetes: Connections = Field(alias = 'kubernetes')
    istio: Connections = Field(alias = 'istio')

class Cluster(BaseModel):
    resources: Resources = Field(alias = 'resources')
    network: Network = Field(alias = 'network')
    activate: bool = Field(False, alias = 'activate')

class Clusters(BaseModel):
    clusters: Dict[str, Cluster] = Field(default_factory = list, alias = 'times')