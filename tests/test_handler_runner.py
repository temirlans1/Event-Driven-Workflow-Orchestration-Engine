import pytest
from orchestrator.models import DAGNode
from orchestrator.registry import register_handler
from orchestrator.handler_runner import run_handler


def test_handler_runner_positive(capsys):
    @register_handler("sample_handler")
    def handler(n, e):
        print(f"node={n.id}, exec={e}")

    node = DAGNode(id="n1", handler="sample_handler")
    run_handler(node, "exec123")

    out = capsys.readouterr().out
    assert "node=n1, exec=exec123" in out


def test_handler_runner_unregistered():
    node = DAGNode(id="x", handler="unknown")
    with pytest.raises(ValueError):
        run_handler(node, "exec")
