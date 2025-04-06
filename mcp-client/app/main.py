import os
import httpx
import logging
import uuid
import traceback
import json
from fastapi import FastAPI, HTTPException, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(os.getenv("LOG_DIR", "./logs"), "mcp-client.log"))
    ]
)
logger = logging.getLogger("mcp-client")

from .services.registry_client import RegistryClient

app = FastAPI(title="MCP Client")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
REGISTRY_URL = os.getenv("REGISTRY_URL", "http://localhost:8000")
registry_client = RegistryClient(REGISTRY_URL)


@app.get("/", response_class=HTMLResponse)
async def root():
    """Simple HTML interface for the MCP client."""
    # Get all services
    services = await registry_client.get_all_services()

    # Get MCP servers
    mcp_servers = await registry_client.get_services_by_type("mcp")

    # Create HTML response
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>MCP Client</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1, h2 {{ color: #333; }}
            .container {{ max-width: 800px; margin: 0 auto; }}
            .service {{ border: 1px solid #ddd; padding: 10px; margin-bottom: 10px; border-radius: 5px; }}
            .form-group {{ margin-bottom: 15px; }}
            label {{ display: block; margin-bottom: 5px; }}
            input, select, textarea {{ width: 100%; padding: 8px; box-sizing: border-box; }}
            button {{ background-color: #4CAF50; color: white; padding: 10px 15px; border: none; cursor: pointer; }}
            .response {{ background-color: #f5f5f5; padding: 10px; border-radius: 5px; white-space: pre-wrap; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>MCP Client</h1>

            <h2>Registered Services</h2>
            <div id="services">
                {generate_services_html(services)}
            </div>

            <h2>AI-Powered Request</h2>
            <form action="/ai-request" method="post">
                <div class="form-group">
                    <label for="user_input">What would you like to do?</label>
                    <textarea name="user_input" id="user_input" rows="4" placeholder="Describe what you want in natural language. Examples:\n- Translate this text to Spanish: Hello world\n- Summarize this article: [paste text]\n- Analyze the sentiment of this review: [paste review]\n- Generate a response to this question: [your question]" required></textarea>
                </div>
                <button type="submit" style="background-color: #6200EA; color: white;">Send AI Request</button>
            </form>

            <h2>Manual MCP Message</h2>
            <form action="/send-message" method="post">
                <div class="form-group">
                    <label for="target_server">Target MCP Server:</label>
                    <select name="target_server" id="target_server" required>
                        {generate_server_options(mcp_servers)}
                    </select>
                </div>
                <div class="form-group">
                    <label for="action">Action:</label>
                    <select name="action" id="action" required>
                        <option value="generate_text">Generate Text</option>
                        <option value="summarize">Summarize Text</option>
                        <option value="analyze_data">Analyze Data</option>
                        <option value="translate_text">Translate Text</option>
                        <option value="classify_text">Classify Text</option>
                        <option value="analyze_sentiment">Analyze Sentiment</option>
                        <option value="get_status">Get Status</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="prompt">Input Text/Prompt:</label>
                    <textarea name="prompt" id="prompt" rows="4"></textarea>
                </div>
                <div class="form-group">
                    <label for="max_tokens">Max Tokens/Length:</label>
                    <input type="number" name="max_tokens" id="max_tokens" value="100">
                </div>
                <button type="submit">Send Message</button>
            </form>

            <h2>Direct API Access</h2>
            <form action="/direct-api" method="post">
                <div class="form-group">
                    <label for="api_type">API Type:</label>
                    <select name="api_type" id="api_type" required>
                        <option value="rest">REST API</option>
                        <option value="graphql">GraphQL API</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="api_prompt">Prompt:</label>
                    <textarea name="api_prompt" id="api_prompt" rows="4"></textarea>
                </div>
                <div class="form-group">
                    <label for="api_max_tokens">Max Tokens:</label>
                    <input type="number" name="api_max_tokens" id="api_max_tokens" value="100">
                </div>
                <button type="submit">Send Request</button>
            </form>
        </div>
    </body>
    </html>
    """

    return html_content


def generate_services_html(services: List[Dict[str, Any]]) -> str:
    """Generate HTML for displaying services."""
    if not services:
        return "<p>No services registered.</p>"

    html = ""
    for service in services:
        html += f"""
        <div class="service">
            <h3>{service.get('name', 'Unknown Service')}</h3>
            <p><strong>ID:</strong> {service.get('id', 'N/A')}</p>
            <p><strong>URL:</strong> {service.get('url', 'N/A')}</p>
            <p><strong>Type:</strong> {service.get('type', 'N/A')}</p>
            <p><strong>Status:</strong> {service.get('status', 'N/A')}</p>
            <p><strong>Capabilities:</strong> {', '.join(service.get('capabilities', []))}</p>
        </div>
        """

    return html


def generate_server_options(servers: List[Dict[str, Any]]) -> str:
    """Generate HTML options for server selection."""
    if not servers:
        return "<option value=''>No servers available</option>"

    options = ""
    for server in servers:
        server_id = server.get('id', '')
        server_name = server.get('name', 'Unknown Server')
        options += f'<option value="{server_id}">{server_name} ({server_id})</option>'

    return options


@app.post("/ai-request", response_class=HTMLResponse)
async def ai_request(
    request: Request,
    user_input: str = Form(...)
):
    """Send an AI-powered request that automatically determines the action."""
    request_id = str(uuid.uuid4())
    logger.info(f"[{request_id}] Received AI request with input: '{user_input[:50]}...'" if len(user_input) > 50 else f"[{request_id}] Received AI request with input: '{user_input}'")

    try:
        # Get MCP Server 1 (which has the action determiner)
        logger.info(f"[{request_id}] Retrieving MCP servers from registry")
        mcp_servers = await registry_client.get_services_by_type("mcp")
        mcp_server_1 = next((s for s in mcp_servers if "REST" in s.get("name", "")), None)
        logger.info(f"[{request_id}] Found MCP servers: {len(mcp_servers)}, Selected server: {mcp_server_1['name'] if mcp_server_1 else 'None'}")

        if not mcp_server_1:
            error_msg = "MCP Server 1 not found."
            logger.error(f"[{request_id}] {error_msg}")
            return generate_response_html("Error", error_msg)

        server_url = mcp_server_1.get("url")
        if not server_url:
            error_msg = "Server URL not found."
            logger.error(f"[{request_id}] {error_msg}")
            return generate_response_html("Error", error_msg)

        # Prepare message content with just the user input
        content = {"input": user_input}
        logger.info(f"[{request_id}] Sending request to MCP server at {server_url}")

        # Send message to MCP Server 1 for AI action determination
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                logger.info(f"[{request_id}] Sending POST request to {server_url}/mcp/message")
                response = await client.post(
                    f"{server_url}/mcp/message",
                    json={
                        "message_id": f"client-ai-request-{request_id}",
                        "source_id": "mcp-client",
                        "target_id": mcp_server_1.get("id"),
                        "content": content,
                        "timestamp": "2023-01-01T00:00:00"  # Placeholder
                    }
                )
                logger.info(f"[{request_id}] Received response with status code: {response.status_code}")
            except httpx.TimeoutException as e:
                error_msg = "Request timed out. The server took too long to respond."
                logger.error(f"[{request_id}] {error_msg}: {str(e)}")
                return generate_response_html("Error", error_msg)
            except httpx.ConnectError as e:
                error_msg = "Connection error. Could not connect to the server."
                logger.error(f"[{request_id}] {error_msg}: {str(e)}")
                return generate_response_html("Error", error_msg)
            except Exception as e:
                error_msg = f"Error sending request: {str(e)}"
                logger.error(f"[{request_id}] {error_msg}\n{traceback.format_exc()}")
                return generate_response_html("Error", error_msg)

            if response.status_code == 200:
                try:
                    result = response.json()
                    logger.info(f"[{request_id}] Successfully parsed JSON response")

                    # Check if there's an error in the response
                    if "error" in result:
                        error_message = result.get("error", "Unknown error")
                        error_details = result.get("details", "")
                        error_msg = f"Server error: {error_message}\nDetails: {error_details}"
                        logger.error(f"[{request_id}] {error_msg}")

                        # Log the full response for debugging
                        logger.error(f"[{request_id}] Full response: {json.dumps(result)}")

                        # Create a more user-friendly error message
                        if "Failed to connect to REST API" in error_message:
                            error_display = "Could not connect to the AI service. Please try again later."
                        elif "timed out" in error_message.lower():
                            error_display = "The request took too long to process. Please try again with a simpler request."
                        elif "Server ID not set" in error_message:
                            error_display = "The server is not properly configured. Please try again later."
                        else:
                            error_display = f"Error: {error_message}\n\nDetails: {error_details}"

                        return generate_response_html("Error", error_display)

                    # Add information about the AI determination
                    determined_action = result.get("determined_action")
                    service_type = result.get("service_type")
                    trace_id = result.get("trace_id")

                    logger.info(f"[{request_id}] Request processed successfully. Action: {determined_action}, Service: {service_type}, Trace ID: {trace_id}")

                    if determined_action and service_type:
                        result["ai_explanation"] = f"AI determined this was a '{determined_action}' request and routed it to the {service_type.upper()} service."
                    elif determined_action:
                        result["ai_explanation"] = f"AI determined this was a '{determined_action}' request."

                    return generate_response_html("AI Request Processed", json.dumps(result, indent=2))
                except json.JSONDecodeError as e:
                    error_msg = f"Failed to parse response: {response.text}"
                    logger.error(f"[{request_id}] {error_msg}: {str(e)}\n{traceback.format_exc()}")
                    return generate_response_html("Error", error_msg)
            else:
                error_text = response.text
                try:
                    error_json = response.json()
                    if isinstance(error_json, dict) and "detail" in error_json:
                        error_text = error_json["detail"]
                except (json.JSONDecodeError, ValueError) as e:
                    logger.error(f"[{request_id}] Failed to parse error response: {str(e)}")

                error_msg = f"Failed to process AI request: {error_text} (Status code: {response.status_code})"
                logger.error(f"[{request_id}] {error_msg}")
                return generate_response_html("Error", f"Failed to process AI request: {error_text} (Status code: {response.status_code})")
    except Exception as e:
        error_msg = f"Error processing AI request: {str(e)}"
        logger.error(f"Unhandled exception in ai_request: {str(e)}\n{traceback.format_exc()}")

        # Create a more user-friendly error message
        if "'NoneType' object has no attribute 'get'" in str(e):
            error_display = "The server is not properly configured. Please try again later."
        else:
            error_display = error_msg

        return generate_response_html("Error", error_display)


@app.post("/send-message", response_class=HTMLResponse)
async def send_message(
    target_server: str = Form(...),
    action: str = Form(...),
    prompt: str = Form(""),
    max_tokens: int = Form(100)
):
    """Send an MCP message to a target server."""
    try:
        # Get target server details
        server = await registry_client.get_service(target_server)
        if not server:
            return generate_response_html("Error", f"Server with ID {target_server} not found.")

        server_url = server.get("url")
        if not server_url:
            return generate_response_html("Error", "Server URL not found.")

        # Prepare message content
        content = {"action": action}
        if action == "generate_text":
            content["prompt"] = prompt
            content["max_tokens"] = max_tokens
        elif action == "summarize":
            content["text"] = prompt  # Reuse the prompt field for text
            content["max_length"] = max_tokens  # Reuse max_tokens for max_length
        elif action == "analyze_data":
            # Try to parse the prompt as JSON for data
            try:
                data = json.loads(prompt)
                content["data"] = data
                content["query"] = "Analyze this data"
            except:
                content["data"] = {}
                content["query"] = prompt
        elif action == "translate_text":
            content["text"] = prompt
            content["source_language"] = "en"  # Default
            content["target_language"] = "es"  # Default
        elif action == "classify_text":
            content["text"] = prompt
            content["categories"] = ["positive", "negative", "neutral"]  # Default categories
        elif action == "analyze_sentiment":
            content["text"] = prompt

        # Send message to target server
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{server_url}/mcp/message",
                json={
                    "message_id": "client-message",
                    "source_id": "mcp-client",
                    "target_id": target_server,
                    "content": content,
                    "timestamp": "2023-01-01T00:00:00"  # Placeholder
                }
            )

            if response.status_code == 200:
                result = response.json()
                return generate_response_html("Success", json.dumps(result, indent=2))
            else:
                return generate_response_html("Error", f"Failed to send message: {response.text}")
    except Exception as e:
        return generate_response_html("Error", f"Error sending message: {str(e)}")


@app.post("/direct-api", response_class=HTMLResponse)
async def direct_api(
    api_type: str = Form(...),
    api_prompt: str = Form(""),
    api_max_tokens: int = Form(100)
):
    """Send a direct request to the API servers."""
    try:
        # Get API servers
        if api_type == "rest":
            servers = await registry_client.get_services_by_type("rest")
        else:  # graphql
            servers = await registry_client.get_services_by_type("graphql")

        if not servers:
            return generate_response_html("Error", f"No {api_type.upper()} API servers found.")

        server = servers[0]  # Use the first server
        server_url = server.get("url")

        if not server_url:
            return generate_response_html("Error", "Server URL not found.")

        # Send request to API server
        async with httpx.AsyncClient() as client:
            if api_type == "rest":
                # REST API request
                response = await client.post(
                    f"{server_url}/api/generate",
                    json={
                        "prompt": api_prompt,
                        "max_tokens": api_max_tokens
                    }
                )
            else:
                # GraphQL API request
                response = await client.post(
                    f"{server_url}/graphql",
                    json={
                        "query": """
                        query GenerateText($prompt: String!, $maxTokens: Int) {
                            generateText(prompt: $prompt, maxTokens: $maxTokens) {
                                text
                                confidence
                                modelUsed
                            }
                        }
                        """,
                        "variables": {
                            "prompt": api_prompt,
                            "maxTokens": api_max_tokens
                        }
                    }
                )

            if response.status_code == 200:
                result = response.json()
                return generate_response_html("Success", json.dumps(result, indent=2))
            else:
                return generate_response_html("Error", f"API request failed: {response.text}")
    except Exception as e:
        return generate_response_html("Error", f"Error sending API request: {str(e)}")


def generate_response_html(status: str, message: str) -> str:
    """Generate HTML response page."""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>MCP Client - Response</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1, h2 {{ color: #333; }}
            .container {{ max-width: 800px; margin: 0 auto; }}
            .success {{ color: green; }}
            .error {{ color: red; }}
            .response {{ background-color: #f5f5f5; padding: 10px; border-radius: 5px; white-space: pre-wrap; }}
            .back-button {{ background-color: #4CAF50; color: white; padding: 10px 15px; border: none; cursor: pointer; text-decoration: none; display: inline-block; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>MCP Client - Response</h1>

            <h2 class="{'success' if status == 'Success' else 'error'}">{status}</h2>

            <div class="response">{message}</div>

            <a href="/" class="back-button">Back to Client</a>
        </div>
    </body>
    </html>
    """


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("SERVICE_HOST", "0.0.0.0")
    port = int(os.getenv("SERVICE_PORT", "8000"))
    uvicorn.run(app, host=host, port=port)
