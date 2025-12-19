"""Orchestrator handler for sequential (synchronous) services.

Import this module and implement your methods in service.py.
"""

import logging
import os

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class DataReference(BaseModel):
    """Reference to data location."""

    protocol: str
    uri: str
    format: str


class ExecuteRequest(BaseModel):
    """Execute request from orchestrator."""

    method: str
    workflow_id: str
    task_id: str
    inputs: list[dict] = []
    parameters: dict = {}


class ExecuteResponse(BaseModel):
    """Execute response to orchestrator."""

    status: str
    output: DataReference | None = None
    error: str | None = None


def create_app(service_module) -> FastAPI:
    """Create FastAPI app that dispatches to service methods.

    Args:
        service_module: Module containing execute_<MethodName> functions.

    Returns:
        FastAPI application.
    """
    app = FastAPI(
        title="Sequential Service",
        description="Synchronous service using orchestrator control interface",
        version="1.0.0",
    )

    @app.post("/control/execute", response_model=ExecuteResponse)
    def execute(request: ExecuteRequest) -> ExecuteResponse:
        """Execute a task by dispatching to service method."""
        logger.info(f"Execute: method={request.method}, task={request.task_id}")

        handler_name = f"execute_{request.method}"
        handler = getattr(service_module, handler_name, None)

        if handler is None:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown method: {request.method}",
            )

        try:
            return handler(request)
        except Exception as e:
            logger.error(f"Execute failed: {e}")
            return ExecuteResponse(status="failed", error=str(e))

    @app.get("/health")
    def health() -> dict:
        """Health check."""
        return {"status": "ok"}

    return app


def run(service_module) -> None:
    """Run the service.

    Args:
        service_module: Module containing execute_<MethodName> functions.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )

    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8080"))

    logger.info(f"Starting sequential service on {host}:{port}")
    app = create_app(service_module)
    uvicorn.run(app, host=host, port=port)
