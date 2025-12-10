from fastapi import FastAPI
from api.endpoints import workflow, workflows
from config import settings

app = FastAPI(
    title="Workflow Orchestration Engine",
    version="1.0.0",
    debug=settings.DEBUG
)


app.include_router(workflow.router, prefix="/workflow", tags=["Workflow"])
app.include_router(workflows.router, prefix="/workflows", tags=["Workflows"])


@app.get("/health")
def health_check():
    return {"status": "ok"}
