import os
import httpx
import logging
import uuid
import json
import datetime
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

# Configure basic logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("simple-client")

# Create FastAPI app
app = FastAPI(title="Simple MCP Client")

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Configuration
# Use localhost:8003 when running locally, mcp-server-1:8000 when running in Docker
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://mcp-server-1:8000")
# Try alternative URL if the main one fails
MCP_SERVER_ALT_URL = os.getenv("MCP_SERVER_ALT_URL", "http://localhost:8003")
SERVICE_ID = os.getenv("SERVICE_ID", "simple-client")

@app.get("/", response_class=HTMLResponse)
async def index():
    """Serve the main page."""
    with open("app/static/index.html", "r") as f:
        return f.read()

@app.get("/debug", response_class=JSONResponse)
async def debug():
    """Debug endpoint to check if the code is updated."""
    return {
        "status": "updated",
        "version": "1.0.1",
        "timestamp": str(datetime.datetime.now())
    }

@app.post("/api/send", response_class=JSONResponse)
async def send_request(prompt: str = Form(...)):
    """Send a request to the MCP server."""
    request_id = str(uuid.uuid4())
    logger.info(f"[{request_id}] Received request: {prompt}")

    try:
        # Prepare the message for the MCP server
        message = {
            "message_id": f"simple-client-{request_id}",
            "source_id": SERVICE_ID,
            "content": {
                "input": prompt
            }
        }

        # Send the message to the MCP server
        logger.info(f"[{request_id}] Sending message to MCP server: {MCP_SERVER_URL}/mcp/message")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{MCP_SERVER_URL}/mcp/message",
                    json=message
                )
        except Exception as e:
            # Try alternative URL if main URL fails
            logger.warning(f"[{request_id}] Failed to connect to primary MCP server: {str(e)}. Trying alternative URL.")
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{MCP_SERVER_ALT_URL}/mcp/message",
                    json=message
                )

        # Process the response
        if response.status_code == 200:
            result = response.json()
            logger.info(f"[{request_id}] Received response from MCP server")

            # Check if the response contains an error
            if "response" in result and "error" in result["response"]:
                # Extract the error from the response
                error_message = result["response"]["error"]
                error_details = result["response"]["details"] if "details" in result["response"] else ""

                logger.warning(f"[{request_id}] Error in MCP server response: {error_message}")

                # Return a consistent error format
                return {
                    "success": False,
                    "error": error_message,
                    "details": error_details,
                    "request_id": request_id
                }
            else:
                # Return the successful result
                return {
                    "success": True,
                    "result": result,
                    "request_id": request_id
                }
        else:
            error_text = response.text
            logger.error(f"[{request_id}] Error from MCP server: {response.status_code} - {error_text}")
            return {
                "success": False,
                "error": f"Server error: {response.status_code}",
                "details": error_text,
                "request_id": request_id
            }

    except Exception as e:
        logger.error(f"[{request_id}] Error sending request: {str(e)}")
        return {
            "success": False,
            "error": "Failed to process request",
            "details": str(e),
            "request_id": request_id
        }

@app.get("/health", response_class=JSONResponse)
async def health_check():
    """Health check endpoint."""
    # Check MCP server health
    mcp_server_status = "unknown"
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(f"{MCP_SERVER_URL}/health")
            if response.status_code == 200:
                mcp_server_status = "healthy"
            else:
                mcp_server_status = "unhealthy"
    except Exception as e:
        # Try alternative URL
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(f"{MCP_SERVER_ALT_URL}/health")
                if response.status_code == 200:
                    mcp_server_status = "healthy (via alternative URL)"
                else:
                    mcp_server_status = "unhealthy (via alternative URL)"
        except Exception as alt_e:
            mcp_server_status = f"error: {str(e)} / {str(alt_e)}"

    return {
        "status": "healthy",
        "service": "simple-client",
        "mcp_server": mcp_server_status
    }

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("SERVICE_HOST", "0.0.0.0")
    port = int(os.getenv("SERVICE_PORT", "8000"))
    uvicorn.run(app, host=host, port=port)
