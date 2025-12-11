import threading
import time

import pytest

from clients.redis_client import redis_client
from orchestrator.models import NodeStatus
from orchestrator.state import get_node_status, set_node_status
from orchestrator.task_queue import push_task
from workers import registry, worker


@pytest.fixture
def worker_runner():
    """Start lightweight worker loops that can be stopped via an event."""
    stop_event = threading.Event()
    threads: list[threading.Thread] = []

    def start(consumer_name: str):
        def _run():
            worker.ensure_group_exists()
            while not stop_event.is_set():
                messages = redis_client.xreadgroup(
                    groupname=worker.GROUP,
                    consumername=consumer_name,
                    streams={worker.STREAM: ">"},
                    count=1,
                    block=500,
                )

                if not messages:
                    continue

                for _stream, entries in messages:
                    for msg_id, fields in entries:
                        worker.process_message(msg_id, fields)
                        redis_client._redis.xack(worker.STREAM, worker.GROUP, msg_id)

        thread = threading.Thread(target=_run, daemon=True)
        threads.append(thread)
        thread.start()
        return thread

    yield start

    stop_event.set()
    for thread in threads:
        thread.join(timeout=2)


@pytest.fixture
def counting_handler(monkeypatch):
    call_counter = {"count": 0}
    lock = threading.Lock()

    def handler(config):
        with lock:
            call_counter["count"] += 1
            return {"status": "ok", "call": call_counter["count"]}

    monkeypatch.setitem(registry.HANDLER_REGISTRY, "counting", handler)
    return call_counter


def wait_for_status(execution_id: str, node_id: str, expected: NodeStatus, timeout: float = 5) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            if get_node_status(execution_id, node_id) == expected:
                return True
        except ValueError:
            pass
        time.sleep(0.05)
    return False


def enqueue_task(execution_id: str, node_id: str, handler_name: str, config: dict | None = None):
    set_node_status(execution_id, node_id, NodeStatus.QUEUED)
    payload = {"handler": handler_name}
    if config:
        payload["config"] = config
    push_task(execution_id, node_id, payload)


def test_single_worker_processes_task(worker_runner):
    worker_runner("worker-1")

    enqueue_task("exec-1", "node-1", handler_name="noop")

    assert wait_for_status("exec-1", "node-1", NodeStatus.COMPLETED)


def test_single_worker_skips_duplicate_task(worker_runner, counting_handler):
    worker_runner("worker-1")

    enqueue_task("exec-2", "node-1", handler_name="counting")
    enqueue_task("exec-2", "node-1", handler_name="counting")

    assert wait_for_status("exec-2", "node-1", NodeStatus.COMPLETED)
    time.sleep(0.2)
    assert counting_handler["count"] == 1


def test_two_workers_process_separate_tasks(worker_runner):
    worker_runner("worker-a")
    worker_runner("worker-b")

    enqueue_task("exec-3", "node-1", handler_name="noop")
    enqueue_task("exec-3", "node-2", handler_name="noop")

    assert wait_for_status("exec-3", "node-1", NodeStatus.COMPLETED)
    assert wait_for_status("exec-3", "node-2", NodeStatus.COMPLETED)


def test_two_workers_process_duplicate_only_once(worker_runner, counting_handler):
    worker_runner("worker-a")
    worker_runner("worker-b")

    enqueue_task("exec-4", "node-1", handler_name="counting")
    enqueue_task("exec-4", "node-1", handler_name="counting")

    assert wait_for_status("exec-4", "node-1", NodeStatus.COMPLETED)
    time.sleep(0.2)
    assert counting_handler["count"] == 1
