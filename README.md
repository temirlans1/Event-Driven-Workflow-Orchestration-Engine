# Event-Driven-Workflow-Orchestration-Engine

Production-grade Event-Driven Workflow Engine

## Dockerized setup

The repository ships with Docker assets to run all core components:

- **FastAPI app:** `main.py` exposed on port `8000` via Uvicorn.
- **Orchestrator loop:** `orchestrator.starter.py` continuously dispatches workflow tasks.
- **Worker(s):** `workers.worker` consumes Redis stream messages and can be scaled horizontally.
- **Redis:** Backing store for workflow coordination.

### Quick start

1. Build and start the stack:
   ```bash
   docker compose up --build
   ```

2. Scale workers as needed (each replica uses a unique consumer name):
   ```bash
   docker compose up --build --scale worker=3
   ```

3. Access the API at http://localhost:8000 and the health check at http://localhost:8000/health.

Environment variables for Redis connectivity (`REDIS_HOST`, `REDIS_PORT`, `REDIS_DB`) and debug mode (`DEBUG`) can be overridden in `docker-compose.yml` or via the CLI.
