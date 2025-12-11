import pytest
from unittest.mock import patch

from orchestrator.template import resolve_templates
from clients.redis_client import redis_client
from orchestrator.redis_keys import RedisKeyTemplates


@patch("orchestrator.template.get_node_output")
def test_single_template_resolves_value(mock_get_output):
    execution_id = "exec-1"
    config = {"url": "http://example.com/{{ get_user.id }}"}

    mock_get_output.return_value = {"id": "abc-123"}

    resolved = resolve_templates(execution_id, config)

    assert resolved["url"] == "http://example.com/abc-123"
    mock_get_output.assert_called_once_with("exec-1", "get_user")


def test_multiple_templates_resolve():
    execution_id = "exec-1"
    config = {
        "message": "{{ alice.name }} and {{ ben.name }} are friends."
    }
    alice_output = {"name": "Alice"}
    ben_output = {"name": "Ben"}
    redis_client.set_json(
        RedisKeyTemplates.WORKFLOW_NODE_OUTPUT.format(
            execution_id=execution_id, node_id="alice"
        ),
        alice_output,
    )
    redis_client.set_json(
        RedisKeyTemplates.WORKFLOW_NODE_OUTPUT.format(
            execution_id=execution_id, node_id="ben"
        ),
        ben_output,
    )

    resolved = resolve_templates(execution_id, config)
    assert resolved["message"] == "Alice and Ben are friends."


@patch("orchestrator.template.get_node_output")
def test_multiple_nodes_templates_resolve(mock_get_output):
    execution_id = "exec-2"
    config = {
        "message": "User {{ get_user.name }} has {{ get_user.count }} items."
    }

    mock_get_output.return_value = {
        "name": "Alice",
        "count": 3
    }

    resolved = resolve_templates(execution_id, config)
    assert resolved["message"] == "User Alice has 3 items."


@patch("orchestrator.template.get_node_output")
def test_template_with_missing_output_key(mock_get_output):
    execution_id = "exec-3"
    config = {
        "text": "Order {{ order.id }} placed by {{ order.user }}"
    }

    mock_get_output.return_value = {
        "id": "xyz"
        # 'user' key is missing
    }

    resolved = resolve_templates(execution_id, config)

    # We expect fallback placeholder
    assert resolved["text"] == "Order xyz placed by <missing:order.user>"
