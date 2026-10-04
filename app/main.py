from fastapi import FastAPI

from app.api.coding import router as coding_router


app = FastAPI(
    title="Self-Healing Coding Agent",
    description="Agentic AI backend for autonomous code generation, debugging, repair, and validation.",
    version="0.1.0",
)


app.include_router(coding_router)


@app.get("/")
def root():
    return {
        "status": "success",
        "message": "Self-Healing Coding Agent backend is running",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "self-healing-coding-agent",
    }