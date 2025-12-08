from typing import Optional

from pydantic import BaseModel


class Node(BaseModel):
    id: str
    handler: str
    dependencies: list[str]
    config: Optional[dict] = {}


class DAG(BaseModel):
    nodes: list[Node]


class WorkflowRequest(BaseModel):
    name: str
    dag: DAG

