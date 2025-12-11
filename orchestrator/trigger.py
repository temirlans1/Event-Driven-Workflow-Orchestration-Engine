from orchestrator.executor import execute_workflow


def trigger_workflow_execution(execution_id: str):
    execute_workflow(execution_id)
