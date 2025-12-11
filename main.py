from fastapi import FastAPI
from api.routers import workflow, workflows
from config import settings
from logging_config import get_logger

logger = get_logger(__name__)

app = FastAPI(
    title="Workflow Orchestration Engine",
    version="1.0.0",
    debug=settings.DEBUG
)


app.include_router(workflow.router, prefix="/workflow", tags=["Workflow"])
app.include_router(workflows.router, prefix="/workflows", tags=["Workflows"])


@app.get("/health")
def health_check():
    logger.info("Health check endpoint called")
    return {"status": "ok"}
