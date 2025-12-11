"""Centralized Redis key templates for workflow orchestration.

This module stores all Redis key patterns in one place so they can be
consistently formatted elsewhere. Templates are plain strings that should be
formatted with ``str.format`` using the documented placeholders.
"""


class RedisKeyTemplates:
    """Reusable Redis key templates with ``str.format`` placeholders."""

    WORKFLOW = "workflow:{execution_id}"
    WORKFLOW_STATUS = "workflow:{execution_id}:status"
    WORKFLOW_NODE = "workflow:{execution_id}:node:{node_id}"
    WORKFLOW_NODE_OUTPUT = "workflow:{execution_id}:node:{node_id}:output"
    WORKFLOWS_ACTIVE = "workflows:active"
    WORKFLOW_TASK_STREAM = "workflow:tasks"
