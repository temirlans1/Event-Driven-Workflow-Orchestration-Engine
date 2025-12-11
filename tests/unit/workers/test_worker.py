import pytest
import json
from unittest.mock import patch
from orchestrator.models import NodeStatus
from orchestrator.state import set_node_status
from workers.worker import process_message


@patch("workers.worker.set_node_status")
@patch("workers.registry.get_handler")
def test_process_message_success(mock_get_handler, mock_set_node_status):
    mock_get_handler.return_value = lambda config: {"status": "ok"}

    fields = {
        "execution_id": "exec-123",
        "node_id": "task-1",
        "payload": json.dumps({
            "handler": "noop",
            "config": {}
        })
    }
    set_node_status("exec-123", "task-1", NodeStatus.QUEUED)

    process_message("msg-id-1", fields)

    mock_set_node_status.assert_any_call("exec-123", "task-1", NodeStatus.RUNNING)
    mock_set_node_status.assert_any_call("exec-123", "task-1", NodeStatus.COMPLETED)


@patch("workers.worker.set_node_status")
@patch("workers.worker.get_handler")
def test_process_message_failure(mock_get_handler, mock_set_node_status):
    def fail_handler(config):
        raise RuntimeError("Boom")

    mock_get_handler.return_value = fail_handler

    fields = {
        "execution_id": "exec-999",
        "node_id": "fail-task",
        "payload": json.dumps({
            "handler": "noop",
            "config": {}
        })
    }
    set_node_status("exec-999", "fail-task", NodeStatus.QUEUED)

    process_message("msg-id-fail", fields)

    mock_set_node_status.assert_any_call("exec-999", "fail-task", NodeStatus.RUNNING)
    mock_set_node_status.assert_any_call("exec-999", "fail-task", NodeStatus.FAILED, error="Boom")
