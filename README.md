# Event-Driven Workflow Orchestration Engine

An end-to-end, Redis-backed workflow runner built with FastAPI, a lightweight orchestrator loop, and horizontally scalable workers. This guide explains the architecture, setup, configuration, and how to run and test the bundled sample workflows.

## Table of contents
- [High-level architecture](#high-level-architecture)
- [Component responsibilities](#component-responsibilities)
- [Local setup](#local-setup)
- [Running the stack](#running-the-stack)
- [Workflow definition format](#workflow-definition-format)
- [Lifecycle: from submission to completion](#lifecycle-from-submission-to-completion)
- [API reference](#api-reference)
- [Triggering the sample workflows](#triggering-the-sample-workflows)
- [Testing](#testing)
- [Configuration](#configuration)
- [Project layout](#project-layout)

## High-level architecture

```
┌──────────┐   submit/trigger   ┌──────────────┐   enqueue runnable nodes  ┌──────────┐
│  Client  │  ─────────────────▶│   FastAPI    │ ─────────────────────────▶│ Redis    │
│ (HTTP)   │                    │    API       │                           │ Streams  │
└──────────┘                    └──────────────┘                           └────┬─────┘
                                                                              │
                             poll active executions / dispatch                │
                      ┌──────────────────────────────┐                        │
                      │ Orchestrator scheduler loop  │◀───────────────────────┘
                      └──────────────┬───────────────┘   ack + write results
                                     │
                                     ▼
                         ┌─────────────────────┐
                         │  Worker processes   │  resolve dependencies, execute
                         │ (one or more)       │  handlers, and persist outputs
                         └─────────────────────┘
```

- **FastAPI service (`main.py`)** accepts workflow DAGs, runs validation, persists definitions, and exposes status/results endpoints.
- **Redis** stores workflow definitions, per-node status/output, the active execution set, and a Redis Stream (`workflow:tasks`) that feeds workers.
- **Orchestrator loop (`orchestrator/starter.py`)** iterates over active executions, resolves dependency readiness, emits runnable nodes into the stream, and marks completions.
- **Workers (`workers/worker.py`)** consume stream entries, resolve handler names to callables in `workers/handlers.py`, execute them, and store outputs plus status transitions.
- **Shared utilities** live in `orchestrator/` (dependency resolution, templating, dispatch) and `clients/` (Redis wrapper with JSON helpers).

## Component responsibilities

- **Submission & validation**
  - `api/validator.py` rejects DAGs with cycles or unknown handlers before anything is persisted.
  - Incoming workflows are stored at `workflow:{execution_id}` with each node initialized to `PENDING` status and the workflow marked `PENDING`.
- **Triggering & activation**
  - `POST /workflow/trigger/{execution_id}` adds the workflow to the Redis set `workflows:active` and immediately dispatches any nodes whose dependencies are satisfied.
- **Scheduling**
  - `orchestrator/executor.py` checks node readiness via `all_dependencies_succeeded`, resolves templated configs (e.g., `{{ A.data }}`) against upstream outputs, and enqueues runnable nodes onto the `workflow:tasks` stream with status transitioned to `QUEUED`.
- **Execution**
  - `workers/worker.py` creates a consumer group (`workflow_group` by default) and continuously `XREADGROUP`s tasks, marking nodes `RUNNING` → `COMPLETED` or `FAILED`, and persisting outputs/errors.
- **Completion detection**
  - `orchestrator/starter.py` removes finished executions from `workflows:active` once all nodes reach a terminal state (`COMPLETED`/`FAILED`) and updates `workflow:{execution_id}:status`.

## Local setup

1. **Prerequisites**
   - Python 3.11+.
   - Redis 7+ reachable at `localhost:6379` (or override via environment variables below). Use a disposable/dev Redis for tests; the suite flushes all keys.

2. **Install dependencies**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Environment variables (optional)**
   Populate a `.env` file or export variables to override defaults from `config.py`:
   - `REDIS_HOST` (default `localhost`)
   - `REDIS_PORT` (default `6379`)
   - `REDIS_DB`   (default `0`)
   - `ENVIRONMENT` (default `development`)
   - `DEBUG` (default `True`)

## Running the stack

### Option A: Docker Compose (API + orchestrator + worker + Redis)

In environments with Docker available:

```bash
docker compose up --build
```

The API will listen on `http://localhost:8000` and Redis on `localhost:6379`. The orchestrator and a single worker start automatically (scale workers via `docker compose up --scale worker=3`).

### Option B: Manual processes (no Docker)

Ensure Redis is running locally, then start each component in separate terminals (after activating your virtualenv):

```bash
# Terminal 1: API server
uvicorn main:app --host 0.0.0.0 --port 8000

# Terminal 2: Orchestrator scheduler loop
python -m orchestrator.starter

# Terminal 3+: One or more workers (unique consumer names recommended)
WORKER_NAME=worker-1 python -m workers.worker
```

Health check: `curl http://localhost:8000/health` should return `{ "status": "ok" }`.

## Workflow definition format

Workflows are DAGs comprised of nodes with IDs, handlers, dependency lists, and optional config payloads. The API schema (`api/schemas/workflow.py`) enforces this shape:

```json
{
  "name": "linear",
  "dag": {
    "nodes": [
      {"id": "A", "handler": "call_external_service", "dependencies": [], "config": {"url": "http://service-a"}},
      {"id": "B", "handler": "llm", "dependencies": ["A"], "config": {"prompt": "Summarize {{ A.data }}"}},
      {"id": "C", "handler": "call_external_service", "dependencies": ["B"], "config": {"url": "http://consumer/{{ B.answer }}"}}
    ]
  }
}
```

Notes:
- Dependencies are node IDs; cycles are rejected during validation.
- Handlers must exist in `workers/handlers.py` and be registered via `workers/registry.py`.
- Config values support simple templating like `{{ NodeId.output_key }}` which is resolved against upstream outputs before dispatch.

## Lifecycle: from submission to completion

1. **Submit** a workflow DAG to `POST /workflow`. The API validates for cycles and handler existence, then persists the definition and initializes node/workflow status to `PENDING`.
2. **Trigger** execution with `POST /workflow/trigger/{execution_id}`. The orchestrator marks the workflow `RUNNING`, adds it to `workflows:active`, and enqueues runnable nodes.
3. **Dispatch & execution**
   - The scheduler repeatedly calls `execute_workflow`, queuing any newly unblocked nodes onto `workflow:tasks` with status `QUEUED`.
   - Workers consume tasks, mark nodes `RUNNING`, execute handlers, persist outputs to `workflow:{execution_id}:node:{node_id}:output`, and set status to `COMPLETED` or `FAILED`.
4. **Completion tracking**
   - The orchestrator detects when all nodes reach terminal states, updates `workflow:{execution_id}:status`, and removes the execution from `workflows:active`.
5. **Inspection**
   - `GET /workflows/{execution_id}` returns overall status.
   - `GET /workflows/{execution_id}/results` returns node outputs keyed by node ID.

## API reference

Base URL: `http://localhost:8000`

- `GET /health` → `{ "status": "ok" }` (liveness probe).
- `POST /workflow`
  - Body: workflow DAG (see [Workflow definition format](#workflow-definition-format)).
  - Responses: `200` with `{ "execution_id": str, "message": "Workflow accepted" }` or `400` if validation fails.
- `POST /workflow/trigger/{execution_id}`
  - Starts scheduling for an existing workflow.
  - Responses: `200` with `{ "message": "Workflow triggered", "execution_id": str }` or `404` if unknown execution ID.
- `GET /workflows/{execution_id}`
  - Returns `{ "execution_id": str, "status": "PENDING" | "RUNNING" | "COMPLETED" | "FAILED" }`.
- `GET /workflows/{execution_id}/results`
  - Returns `{ "execution_id": str, "results": { <node_id>: <output_dict> } }`.

## Triggering the sample workflows

The integration suite defines three canonical workflows in `tests/integration/test_workflows.py`. You can exercise them manually against a running stack:

1. **Linear chain (`A → B → C`)**
   ```bash
   curl -X POST http://localhost:8000/workflow \
        -H "Content-Type: application/json" \
        -d @<(cat <<'EOF'
{
  "name": "linear",
  "dag": {"nodes": [
    {"id": "A", "handler": "call_external_service", "dependencies": [], "config": {"url": "http://service-a"}},
    {"id": "B", "handler": "llm", "dependencies": ["A"], "config": {"prompt": "Summarize {{ A.data }}"}},
    {"id": "C", "handler": "call_external_service", "dependencies": ["B"], "config": {"url": "http://consumer/{{ B.answer }}"}}
  ]}
}
EOF
)
   # Capture execution_id from the response, then trigger
   curl -X POST http://localhost:8000/workflow/trigger/<execution_id>
   ```

2. **Fan-out/fan-in (`A → {B, C} → D`)**
   - Submit the `fanout` DAG from the tests and trigger once. The orchestrator will emit `A`, then `B` and `C` in parallel, then `D` after both complete.

3. **Race guard (`{B, C} → D` with no shared dependencies)**
   - Submit the `race` DAG and trigger twice: the first call enqueues `B` and `C`; the second call enqueues `D` once both have finished.

To observe progress while running:

```bash
curl http://localhost:8000/workflows/<execution_id>
curl http://localhost:8000/workflows/<execution_id>/results
```

## Testing

- **Important:** The test fixtures flush **all** Redis keys before each test; never point tests at a production Redis deployment.
- **Run all tests** (requires a running Redis):
  ```bash
  pytest
  ```
- **Manual smoke check without workers:** submit a workflow, trigger it, then inspect queued stream entries:
  ```bash
  redis-cli XRANGE workflow:tasks - +
  ```
  You can also run `python -m workers.worker` in a separate shell to process tasks.

## Configuration

- **Application settings** (`config.py`)
  - `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB` control all Redis connections.
  - `ENVIRONMENT` and `DEBUG` are forwarded to FastAPI initialization.
- **Worker overrides** (environment variables)
  - `WORKER_STREAM` (default `workflow:tasks`)
  - `WORKER_GROUP` (default `workflow_group`)
  - `WORKER_NAME` (default `worker-<hostname>`)
- **Redis key conventions** (`orchestrator/redis_keys.py`)
  - Workflow: `workflow:{execution_id}`
  - Workflow status: `workflow:{execution_id}:status`
  - Node status: `workflow:{execution_id}:node:{node_id}`
  - Node outputs: `workflow:{execution_id}:node:{node_id}:output`
  - Active workflow set: `workflows:active`
  - Task stream: `workflow:tasks`

## Project layout

- `main.py` – FastAPI app creation and router wiring.
- `api/routers/` – HTTP endpoints for submission, triggering, status, and results.
- `api/schemas/` – Pydantic models for workflow payloads.
- `api/validator.py` – DAG validation and handler existence checks.
- `clients/redis_client.py` – Redis helper with JSON convenience methods and stream/group utilities.
- `orchestrator/` – Workflow loading, dependency resolution, templating, dispatch, scheduler loop, and Redis key definitions.
- `workers/` – Worker loop, handler registry, and built-in handlers (`noop`, `call_external_service`, `llm`, `unreliable_handler`).
- `tests/` – Unit and integration suites containing sample workflows and fixtures that flush Redis between tests.
- `docker-compose.yml` – Compose file wiring Redis, API, orchestrator, and worker services.

With these notes you should have everything needed to run, extend, and test the orchestration engine confidently.
