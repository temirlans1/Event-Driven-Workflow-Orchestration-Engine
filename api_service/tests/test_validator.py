import pytest
from core.validator import validate_workflow
from api.schemas.workflow import Node


def test_valid_dag():
    nodes = [
        Node(id="A", handler="input", dependencies=[]),
        Node(id="B", handler="service", dependencies=["A"]),
        Node(id="C", handler="output", dependencies=["B"]),
    ]
    validate_workflow(nodes)


def test_duplicate_node_ids():
    nodes = [
        Node(id="A", handler="input", dependencies=[]),
        Node(id="A", handler="service", dependencies=[]),
    ]
    with pytest.raises(ValueError, match="Duplicate node ID"):
        validate_workflow(nodes)


def test_invalid_dependency():
    nodes = [
        Node(id="A", handler="input", dependencies=["B"]),
        Node(id="C", handler="output", dependencies=[]),
    ]
    with pytest.raises(ValueError, match="Invalid dependency: B"):
        validate_workflow(nodes)


def test_cycle_detection():
    nodes = [
        Node(id="A", handler="input", dependencies=["C"]),
        Node(id="B", handler="service", dependencies=["A"]),
        Node(id="C", handler="output", dependencies=["B"]),
    ]
    with pytest.raises(ValueError, match="contains a cycle"):
        validate_workflow(nodes)
