from fastapi import APIRouter, HTTPException, Depends, Request
import time
import json
import uuid
import os
import httpx
from typing import Dict, Any, Optional

from ..models import MCPMessage, GenerateTextRequest
from ..services.rest_client import RestApiClient
from ..services.mcp_client import MCPClient
from ..services.action_determiner import ActionDeterminer

# Import OpenAI for direct testing
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

# Import the logger if available
try:
    from common.logger import get_logger
    COMMON_AVAILABLE = True
except ImportError:
    COMMON_AVAILABLE = False
    # Simple logging fallback
    import logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    def get_logger(name):
        return logging.getLogger(name)

router = APIRouter(tags=["mcp"])

# Initialize logger
logger = get_logger("mcp-router")

# Track server start time for uptime calculation
START_TIME = time.time()
if COMMON_AVAILABLE:
    logger.info("MCP Router initialized", extra_data={"start_time": START_TIME})


def get_rest_client():
    return RestApiClient()


def get_mcp_client():
    return MCPClient()


def get_action_determiner():
    return ActionDeterminer()


@router.get("/health")
async def health_check():
    """Health check endpoint for the MCP server."""
    import asyncio
    import os

    # Get uptime
    uptime = time.time() - START_TIME

    # Check if registry is available
    registry_status = "unknown"
    registry_url = os.getenv("REGISTRY_URL", "http://localhost:8000")
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(f"{registry_url}/registry/health")
            if response.status_code == 200:
                registry_status = "healthy"
            else:
                registry_status = "unhealthy"
    except Exception as e:
        registry_status = f"error: {str(e)}"

    # Check if REST API is available
    rest_api_status = "unknown"
    rest_api_url = os.getenv("REST_API_URL", "http://rest-api-server:8000")
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(f"{rest_api_url}/api/health")
            if response.status_code == 200:
                rest_api_status = "healthy"
            else:
                rest_api_status = "unhealthy"
    except Exception as e:
        rest_api_status = f"error: {str(e)}"

        # Try alternative URL
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get("http://localhost:8001/api/health")
                if response.status_code == 200:
                    rest_api_status = "healthy (via localhost)"
                else:
                    rest_api_status = "unhealthy (via localhost)"
        except Exception as alt_e:
            rest_api_status = f"error: {str(e)} / {str(alt_e)}"

    return {
        "status": "healthy",
        "service": "mcp-server-1",
        "uptime": uptime,
        "registry": registry_status,
        "rest_api": rest_api_status
    }


@router.post("/message")
async def receive_message(
    request: Request,
    message: MCPMessage,
    rest_client: RestApiClient = Depends(get_rest_client),
    mcp_client: MCPClient = Depends(get_mcp_client),
    action_determiner: ActionDeterminer = Depends(get_action_determiner)
):
    """Handle incoming MCP messages."""
    # Get trace_id from request state or generate a new one
    trace_id = getattr(request.state, "trace_id", str(uuid.uuid4()))

    if COMMON_AVAILABLE:
        logger.info(f"Received MCP message", trace_id=trace_id, extra_data={
            "message_id": message.message_id,
            "source_id": message.source_id,
            "target_id": message.target_id
        })

    try:
        # Process the message based on content
        content = message.content
        action = content.get("action")

        # If no action is specified, use AI to determine the action
        if not action and "input" in content:
            user_input = content.get("input", "")
            if COMMON_AVAILABLE:
                logger.info(f"No action specified, determining action from input", trace_id=trace_id, extra_data={
                    "input": user_input[:100] + "..." if len(user_input) > 100 else user_input
                })

            # Pass trace_id to action determiner for consistent logging
            action, params, service_type = action_determiner.determine_action(user_input, trace_id)

            # Log the determined action
            if COMMON_AVAILABLE:
                logger.info(f"AI determined action: {action}, service: {service_type}", trace_id=trace_id, extra_data={
                    "action": action,
                    "service_type": service_type,
                    "parameters": params
                })
            else:
                print(f"AI determined action: {action}, service: {service_type}")

            # If the service type is GraphQL, forward to MCP Server 2
            if service_type == "graphql":
                # Forward to MCP Server 2
                if COMMON_AVAILABLE:
                    logger.info(f"Forwarding to GraphQL MCP server", trace_id=trace_id)

                mcp_servers = await mcp_client.get_mcp_servers()
                mcp_server_2 = next((s for s in mcp_servers if "GraphQL" in s.get("name", "")), None)

                if mcp_server_2 and mcp_server_2.get("id"):
                    # Forward to MCP Server 2
                    forward_content = {
                        "action": action,
                        **params
                    }

                    if COMMON_AVAILABLE:
                        logger.info(f"Sending message to MCP Server 2", trace_id=trace_id, extra_data={
                            "target_id": mcp_server_2.get("id"),
                            "content": forward_content
                        })

                    result = await mcp_client.send_message(
                        mcp_server_2.get("id"),
                        forward_content
                    )

                    if COMMON_AVAILABLE:
                        logger.info(f"Received response from MCP Server 2", trace_id=trace_id)

                    return {
                        "message_id": message.message_id,
                        "response": result,
                        "determined_action": action,
                        "service_type": service_type,
                        "trace_id": trace_id
                    }
                else:
                    error_msg = "GraphQL MCP server not found or server ID not set"
                    if COMMON_AVAILABLE:
                        logger.error(f"{error_msg}", trace_id=trace_id, extra_data={
                            "mcp_server_2": mcp_server_2
                        })

                    # Fall back to REST API instead
                    if COMMON_AVAILABLE:
                        logger.warning(f"Falling back to REST API for GraphQL request", trace_id=trace_id)

                    service_type = "rest"

                    # Continue to REST API processing below

            # Otherwise, update the content with the determined action and parameters
            content = {
                "action": action,
                **params
            }

            if COMMON_AVAILABLE:
                logger.info(f"Using REST API for action: {action}", trace_id=trace_id)

        # Process based on the action
        action = content.get("action")

        if action == "generate_text":
            # Forward to REST API
            prompt = content.get("prompt", "")
            max_tokens = content.get("max_tokens", 100)

            if COMMON_AVAILABLE:
                logger.info(f"Generating text with REST API", trace_id=trace_id, extra_data={
                    "prompt": prompt[:100] + "..." if len(prompt) > 100 else prompt,
                    "max_tokens": max_tokens
                })

            result = await rest_client.generate_text(prompt, max_tokens)

            if COMMON_AVAILABLE:
                logger.info(f"Text generation completed", trace_id=trace_id)

            # Check if there's an error in the response
            if "error" in result:
                error_message = result["error"]
                error_details = result.get("details", "")
                if COMMON_AVAILABLE:
                    logger.error(f"Error generating text: {error_message}", trace_id=trace_id, extra_data={
                        "error": error_message,
                        "details": error_details,
                        "base_url": rest_client.base_url,
                        "prompt": prompt[:100] + "..." if len(prompt) > 100 else prompt
                    })
                return {
                    "message_id": message.message_id,
                    "response": {
                        "text": f"Error: {error_message}",
                        "confidence": 0.0,
                        "model_used": "error"
                    },
                    "error": error_message,
                    "details": error_details,
                    "determined_action": action if "input" in message.content else None,
                    "trace_id": trace_id
                }
            else:
                return {
                    "message_id": message.message_id,
                    "response": result,
                    "determined_action": action if "input" in message.content else None,
                    "trace_id": trace_id
                }
        elif action == "summarize":
            # Forward to REST API
            text = content.get("text", "")
            max_length = content.get("max_length", 100)

            if COMMON_AVAILABLE:
                logger.info(f"Summarizing text with REST API", trace_id=trace_id, extra_data={
                    "text_length": len(text),
                    "max_length": max_length
                })

            result = await rest_client.summarize_text(text, max_length)

            if COMMON_AVAILABLE:
                logger.info(f"Text summarization completed", trace_id=trace_id)

            # Check if there's an error in the response
            if "error" in result:
                error_message = result["error"]
                error_details = result.get("details", "")
                if COMMON_AVAILABLE:
                    logger.error(f"Error summarizing text: {error_message}", trace_id=trace_id, extra_data={
                        "error": error_message,
                        "details": error_details,
                        "base_url": rest_client.base_url,
                        "text_length": len(text)
                    })
                return {
                    "message_id": message.message_id,
                    "response": {
                        "summary": f"Error: {error_message}",
                        "reduction_percentage": 0.0,
                        "model_used": "error"
                    },
                    "error": error_message,
                    "details": error_details,
                    "determined_action": action if "input" in message.content else None,
                    "trace_id": trace_id
                }
            else:
                return {
                    "message_id": message.message_id,
                    "response": result,
                    "determined_action": action if "input" in message.content else None,
                    "trace_id": trace_id
                }
        elif action == "analyze_data":
            # Forward to REST API
            query = content.get("query", "")
            data = content.get("data", {})

            if COMMON_AVAILABLE:
                logger.info(f"Analyzing data with REST API", trace_id=trace_id, extra_data={
                    "query": query,
                    "data_size": len(str(data))
                })

            result = await rest_client.analyze_data(query, data)

            if COMMON_AVAILABLE:
                logger.info(f"Data analysis completed", trace_id=trace_id)

            # Check if there's an error in the response
            if "error" in result:
                error_message = result["error"]
                error_details = result.get("details", "")
                if COMMON_AVAILABLE:
                    logger.error(f"Error analyzing data: {error_message}", trace_id=trace_id, extra_data={
                        "error": error_message,
                        "details": error_details,
                        "base_url": rest_client.base_url,
                        "query": query[:100] + "..." if len(query) > 100 else query
                    })
                return {
                    "message_id": message.message_id,
                    "response": {
                        "analysis": f"Error: {error_message}",
                        "insights": [],
                        "model_used": "error"
                    },
                    "error": error_message,
                    "details": error_details,
                    "determined_action": action if "input" in message.content else None,
                    "trace_id": trace_id
                }
            else:
                return {
                    "message_id": message.message_id,
                    "response": result,
                    "determined_action": action if "input" in message.content else None,
                    "trace_id": trace_id
                }
        elif action == "get_status":
            # Get status from REST API
            if COMMON_AVAILABLE:
                logger.info(f"Getting status from REST API", trace_id=trace_id)

            result = await rest_client.get_status()

            if COMMON_AVAILABLE:
                logger.info(f"Status retrieved from REST API", trace_id=trace_id, extra_data={"status": result})

            return {
                "message_id": message.message_id,
                "response": result,
                "trace_id": trace_id
            }
        else:
            if COMMON_AVAILABLE:
                logger.warning(f"Unknown action requested", trace_id=trace_id, extra_data={"action": action})

            return {
                "message_id": message.message_id,
                "error": f"Unknown action: {action}",
                "trace_id": trace_id
            }
    except Exception as e:
        if COMMON_AVAILABLE:
            logger.error(f"Error processing message", trace_id=trace_id, extra_data={"error": str(e)})

        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")


@router.post("/generate")
async def generate_text(
    request: GenerateTextRequest,
    rest_client: RestApiClient = Depends(get_rest_client)
):
    """Generate text using the REST API."""
    try:
        result = await rest_client.generate_text(request.prompt, request.max_tokens)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating text: {str(e)}")


@router.get("/status")
async def get_status(
    rest_client: RestApiClient = Depends(get_rest_client),
    mcp_client: MCPClient = Depends(get_mcp_client)
):
    """Get the status of this MCP server and connected services."""
    try:
        # Get REST API status
        rest_status = await rest_client.get_status()

        # Get MCP servers
        mcp_servers = await mcp_client.get_mcp_servers()
        connected_services = [server.get("name") for server in mcp_servers if server.get("id") != mcp_client.server_id]

        uptime = int(time.time() - START_TIME)

        return {
            "status": "online",
            "load": rest_status.get("load", 0.0) if isinstance(rest_status, dict) else 0.0,
            "uptime": uptime,
            "connected_services": connected_services,
            "rest_api_status": rest_status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting status: {str(e)}")


@router.get("/llm-status")
async def check_llm_status():
    """Check if the LLM is online and functioning."""
    # Get trace_id for logging
    trace_id = str(uuid.uuid4())

    # Check if we're using a local LLM
    use_local_llm = os.getenv("USE_LOCAL_LLM", "false").lower() == "true"

    if use_local_llm:
        # Get Ollama configuration
        ollama_api_url = os.getenv("OLLAMA_API_URL", "http://localhost:11434")
        ollama_model = os.getenv("OLLAMA_MODEL", "llama2")

        if COMMON_AVAILABLE:
            logger.info(f"Checking Ollama LLM status", trace_id=trace_id, extra_data={
                "api_url": ollama_api_url,
                "model": ollama_model
            })

        try:
            # Check if Ollama API is accessible
            response = httpx.get(f"{ollama_api_url}/api/tags", timeout=5.0)

            if response.status_code == 200:
                # Check if the model is available
                models = response.json().get("models", [])
                model_available = any(model.get("name") == ollama_model for model in models)

                if model_available:
                    return {
                        "status": "ok",
                        "llm_type": "ollama",
                        "model": ollama_model,
                        "api_url": ollama_api_url
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"Model '{ollama_model}' not found in Ollama",
                        "available_models": [model.get("name") for model in models]
                    }
            else:
                return {
                    "status": "error",
                    "message": f"Ollama API returned status code {response.status_code}",
                    "response": response.text
                }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error connecting to Ollama API: {str(e)}"
            }
    else:
        # Check OpenAI API
        openai_api_key = os.getenv("OPENAI_API_KEY")

        if not openai_api_key:
            return {
                "status": "error",
                "message": "OpenAI API key not configured"
            }

        if COMMON_AVAILABLE:
            logger.info(f"Checking OpenAI API status", trace_id=trace_id)

        try:
            # Initialize OpenAI client
            client = OpenAI(api_key=openai_api_key)

            # Make a simple API call to check if the API is accessible
            response = client.models.list()

            return {
                "status": "ok",
                "llm_type": "openai",
                "available_models": [model.id for model in response.data[:5]]  # Show first 5 models
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error connecting to OpenAI API: {str(e)}"
            }
