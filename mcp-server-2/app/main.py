import os
import httpx
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import mcp
from .services.mcp_client import MCPClient
from .services.graphql_client import GraphQLClient

app = FastAPI(title="MCP Server 2 (GraphQL)")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(mcp.router)

# Configuration
REGISTRY_URL = os.getenv("REGISTRY_URL", "http://localhost:8000")
SERVICE_HOST = os.getenv("SERVICE_HOST", "localhost")
SERVICE_PORT = os.getenv("SERVICE_PORT", "8000")
SERVICE_URL = f"http://{SERVICE_HOST}:{SERVICE_PORT}"
GRAPHQL_API_URL = os.getenv("GRAPHQL_API_URL", "http://localhost:8002")

# Service registration data
service_id = None
mcp_client = MCPClient(REGISTRY_URL)
graphql_client = GraphQLClient(GRAPHQL_API_URL)


async def register_with_registry():
    """Register this service with the registry."""
    global service_id
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{REGISTRY_URL}/registry/services",
                json={
                    "name": "MCP Server 2 (GraphQL)",
                    "url": SERVICE_URL,
                    "type": "mcp",
                    "capabilities": ["text_generation"]
                }
            )
            
            if response.status_code == 201:
                data = response.json()
                service_id = data.get("id")
                mcp_client.set_server_id(service_id)
                print(f"Successfully registered with registry. Service ID: {service_id}")
            else:
                print(f"Failed to register with registry: {response.text}")
        except Exception as e:
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
                print(f"Failed to send heartbeat: {response.text}")
        except Exception as e:
            print(f"Error sending heartbeat: {str(e)}")


async def check_graphql_api():
    """Check if the GraphQL API is available."""
    try:
        status = await graphql_client.get_status()
        if "error" in status:
            print(f"GraphQL API not available: {status['error']}")
        else:
            print("GraphQL API is available")
    except Exception as e:
        print(f"Error checking GraphQL API: {str(e)}")


async def heartbeat_task():
    """Background task to send periodic heartbeats."""
    while True:
        await send_heartbeat()
        await check_graphql_api()
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
                print("Successfully deregistered from registry")
            except Exception as e:
                print(f"Error deregistering from registry: {str(e)}")


@app.get("/")
async def root():
    return {"message": "MCP Server 2 (GraphQL)"}


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("SERVICE_HOST", "0.0.0.0")
    port = int(os.getenv("SERVICE_PORT", "8000"))
    uvicorn.run(app, host=host, port=port)
