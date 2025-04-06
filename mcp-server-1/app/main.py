import os
import httpx
import asyncio
import uuid
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from .routers import mcp
from .services.mcp_client import MCPClient
from .services.rest_client import RestApiClient

# Import the common utilities if available
try:
    from common.middleware import TracingMiddleware
    from common.logger import get_logger
    COMMON_AVAILABLE = True
except ImportError:
    COMMON_AVAILABLE = False
    # Simple logging fallback
    import logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger("mcp-server-1")

app = FastAPI(title="MCP Server 1 (REST)")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add tracing middleware if available
if COMMON_AVAILABLE:
    logger = get_logger("mcp-server-1")
    app.add_middleware(TracingMiddleware, service_name="mcp-server-1")
    logger.info("Added tracing middleware")

# Add middleware to add trace_id to request state
@app.middleware("http")
async def add_trace_id(request: Request, call_next):
    # Get trace_id from header or generate a new one
    trace_id = request.headers.get("X-Trace-ID", str(uuid.uuid4()))
    request.state.trace_id = trace_id

    # Process the request
    response = await call_next(request)

    # Add trace_id to response headers
    response.headers["X-Trace-ID"] = trace_id

    return response

# Include routers
app.include_router(mcp.router)

# Configuration
REGISTRY_URL = os.getenv("REGISTRY_URL", "http://localhost:8000")
SERVICE_HOST = os.getenv("SERVICE_HOST", "localhost")
SERVICE_PORT = os.getenv("SERVICE_PORT", "8000")
SERVICE_URL = f"http://{SERVICE_HOST}:{SERVICE_PORT}"
REST_API_URL = os.getenv("REST_API_URL", "http://localhost:8001")

# Service registration data
service_id = None
mcp_client = MCPClient(REGISTRY_URL)
rest_client = RestApiClient(REST_API_URL)


async def register_with_registry():
    """Register this service with the registry."""
    global service_id

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{REGISTRY_URL}/registry/services",
                json={
                    "name": "MCP Server 1 (REST)",
                    "url": SERVICE_URL,
                    "type": "mcp",
                    "capabilities": ["text_generation"]
                }
            )

            if response.status_code == 201:
                data = response.json()
                service_id = data.get("id")
                mcp_client.set_server_id(service_id)
                if COMMON_AVAILABLE:
                    logger.info(f"Successfully registered with registry", extra_data={"service_id": service_id})
                else:
                    print(f"Successfully registered with registry. Service ID: {service_id}")
            else:
                if COMMON_AVAILABLE:
                    logger.error(f"Failed to register with registry", extra_data={"response": response.text})
                else:
                    print(f"Failed to register with registry: {response.text}")
        except Exception as e:
            if COMMON_AVAILABLE:
                logger.error(f"Error registering with registry", extra_data={"error": str(e)})
            else:
                print(f"Error registering with registry: {str(e)}")


async def send_heartbeat():
    """Send periodic heartbeats to the registry."""
    global service_id

    if not service_id:
        return

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{REGISTRY_URL}/registry/services/{service_id}/heartbeat"
            )
            if response.status_code != 200:
                if COMMON_AVAILABLE:
                    logger.warning(f"Failed to send heartbeat", extra_data={"response": response.text})
                else:
                    print(f"Failed to send heartbeat: {response.text}")
        except Exception as e:
            if COMMON_AVAILABLE:
                logger.error(f"Error sending heartbeat", extra_data={"error": str(e)})
            else:
                print(f"Error sending heartbeat: {str(e)}")


async def check_rest_api():
    """Check if the REST API is available."""
    try:
        status = await rest_client.get_status()
        if "error" in status:
            if COMMON_AVAILABLE:
                logger.warning(f"REST API not available", extra_data={"error": status['error']})
            else:
                print(f"REST API not available: {status['error']}")
        else:
            if COMMON_AVAILABLE:
                logger.info("REST API is available")
            else:
                print("REST API is available")
    except Exception as e:
        if COMMON_AVAILABLE:
            logger.error(f"Error checking REST API", extra_data={"error": str(e)})
        else:
            print(f"Error checking REST API: {str(e)}")


async def heartbeat_task():
    """Background task to send periodic heartbeats."""
    while True:
        await send_heartbeat()
        await check_rest_api()
        await asyncio.sleep(30)  # Send heartbeat every 30 seconds


@app.on_event("startup")
async def startup_event():
    """Run startup tasks."""
    # Wait for registry to be available
    await asyncio.sleep(5)

    await register_with_registry()

    # Start heartbeat task
    asyncio.create_task(heartbeat_task())


@app.on_event("shutdown")
async def shutdown_event():
    """Run shutdown tasks."""
    global service_id

    if service_id:
        async with httpx.AsyncClient() as client:
            try:
                await client.delete(f"{REGISTRY_URL}/registry/services/{service_id}")
                if COMMON_AVAILABLE:
                    logger.info("Successfully deregistered from registry")
                else:
                    print("Successfully deregistered from registry")
            except Exception as e:
                if COMMON_AVAILABLE:
                    logger.error(f"Error deregistering from registry", extra_data={"error": str(e)})
                else:
                    print(f"Error deregistering from registry: {str(e)}")


@app.get("/")
async def root():
    return {"message": "MCP Server 1 (REST)"}


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("SERVICE_HOST", "0.0.0.0")
    port = int(os.getenv("SERVICE_PORT", "8000"))
    uvicorn.run(app, host=host, port=port)
