from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional


class NodeStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    QUEUED = "QUEUED"


@dataclass
class DAGNode:
    id: str
    handler: str
    dependencies: List[str] = field(default_factory=list)
    config: Dict = field(default_factory=dict)


@dataclass
class Workflow:
    execution_id: str
    name: str
    nodes: List[DAGNode]


@dataclass
class NodeExecutionStatus:
    id: str
    status: NodeStatus
    error: Optional[str] = None
