from pydantic import BaseModel
from typing import List, Optional, Dict


class Node(BaseModel):
    id: str
    handler: str
    dependencies: List[str]
    config: Optional[Dict] = {}


class DAG(BaseModel):
    nodes: List[Node]


class WorkflowRequest(BaseModel):
    name: str
    dag: DAG
