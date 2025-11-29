"""FastAPI entry point for Claude Agent SDK service.

This file is at the root for Render deployment convention.
Start command: uvicorn main:app --host 0.0.0.0 --port $PORT
"""

import logging
import os
import sys

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from agent.client import AgentClient
from agent.config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Claude Agent SDK Service",
    description="Generic Claude Agent powered by the Claude Agent SDK",
    version="0.1.0",
)


class QueryRequest(BaseModel):
    """Request model for /query endpoint."""
    prompt: str
    system_prompt: str | None = None
    model: str | None = None


class QueryResponse(BaseModel):
    """Response model for /query endpoint."""
    result: str
    model: str


@app.get("/health")
async def health():
    """Health check endpoint for Render."""
    return {"status": "ok"}


@app.get("/")
async def root():
    """Root endpoint with service info."""
    return {
        "service": "claude-agent",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
    }


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """Execute a query against the Claude Agent.

    Args:
        request: Query request with prompt and optional overrides

    Returns:
        Agent response with result and model used
    """
    try:
        # Get settings for model info
        settings = get_settings()

        # Initialize client with optional overrides
        client = AgentClient(
            system_prompt=request.system_prompt,
            model=request.model,
        )

        # Execute query
        result = await client.query(request.prompt)

        return QueryResponse(
            result=result,
            model=request.model or settings.model,
        )

    except ValueError as e:
        # Configuration errors (missing API key, etc.)
        logger.error(f"Configuration error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        # Unexpected errors
        logger.exception(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )
