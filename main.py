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

# Debug: Log env vars at startup
print(f"DEBUG: ANTHROPIC_API_KEY present: {'ANTHROPIC_API_KEY' in os.environ}")
print(f"DEBUG: ANTHROPIC_API_KEY length: {len(os.environ.get('ANTHROPIC_API_KEY', ''))}")

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


@app.get("/debug/env")
async def debug_env():
    """Debug endpoint to check env vars and CLI availability."""
    import subprocess
    import shutil

    # Check if claude CLI is available
    claude_path = shutil.which("claude")
    node_path = shutil.which("node")
    npm_path = shutil.which("npm")

    # Try to get claude version
    claude_version = None
    try:
        result = subprocess.run(["claude", "--version"], capture_output=True, text=True, timeout=10)
        claude_version = result.stdout.strip() if result.returncode == 0 else f"error: {result.stderr}"
    except Exception as e:
        claude_version = f"exception: {str(e)}"

    return {
        "anthropic_key_present": "ANTHROPIC_API_KEY" in os.environ,
        "anthropic_key_length": len(os.environ.get("ANTHROPIC_API_KEY", "")),
        "port": os.environ.get("PORT", "not set"),
        "claude_path": claude_path,
        "claude_version": claude_version,
        "node_path": node_path,
        "npm_path": npm_path,
    }


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
    import traceback

    logger.info(f"Query received: {request.prompt[:50]}...")

    try:
        # Get settings for model info
        logger.info("Loading settings...")
        settings = get_settings()
        logger.info(f"Settings loaded. Model: {settings.model}")

        # Initialize client with optional overrides
        logger.info("Initializing AgentClient...")
        client = AgentClient(
            system_prompt=request.system_prompt,
            model=request.model,
        )
        logger.info("AgentClient initialized")

        # Execute query
        logger.info("Executing query...")
        result = await client.query(request.prompt)
        logger.info(f"Query completed. Result length: {len(result)}")

        return QueryResponse(
            result=result,
            model=request.model or settings.model,
        )

    except ValueError as e:
        # Configuration errors (missing API key, etc.)
        logger.error(f"Configuration error: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        # Unexpected errors
        logger.error(f"Query failed: {type(e).__name__}: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Query failed: {type(e).__name__}: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )
