import pytest

from clients.redis_client import redis_client
from orchestrator.redis_keys import RedisKeyTemplates
from orchestrator.state import (
    set_node_status,
    get_node_status,
    all_dependencies_succeeded, set_node_output, get_node_output
)
from orchestrator.models import NodeStatus


def test_set_and_get_node_status():
    set_node_status("wf1", "n1", NodeStatus.COMPLETED)
    assert get_node_status("wf1", "n1") == NodeStatus.COMPLETED


def test_get_node_status_raises_on_missing_node():
    execution_id = "test-exec"
    node_id = "nonexistent-node"

    # Ensure the key does not exist
    redis_client._redis.delete(
        RedisKeyTemplates.WORKFLOW_NODE.format(
            execution_id=execution_id, node_id=node_id
        )
    )

    with pytest.raises(ValueError) as exc:
        get_node_status(execution_id, node_id)

    assert "Node not found" in str(exc.value)


def test_all_dependencies_succeeded_positive():
    set_node_status("wf2", "a", NodeStatus.COMPLETED)
    set_node_status("wf2", "b", NodeStatus.COMPLETED)
    assert all_dependencies_succeeded("wf2", ["a", "b"]) is True


def test_all_dependencies_succeeded_negative():
    set_node_status("wf3", "a", NodeStatus.FAILED)
    assert all_dependencies_succeeded("wf3", ["a"]) is False


def test_all_dependencies_succeeded_missing_node_defaults_to_not_succeeded():
    # Missing dependency should block execution
    with pytest.raises(ValueError) as exc:
        all_dependencies_succeeded("wf4", ["missing"])

    assert "Node not found" in str(exc.value)


def test_set_and_get_node_output():
    execution_id = "exec-out"
    node_id = "node-A"
    output = {
        "result": "42",
        "extra": True
    }

    set_node_output(execution_id, node_id, output)
    stored = get_node_output(execution_id, node_id)

    assert stored == output


def test_get_node_output_returns_empty_if_missing():
    execution_id = "exec-none"
    node_id = "missing-node"

    output = get_node_output(execution_id, node_id)
    assert output == {}
