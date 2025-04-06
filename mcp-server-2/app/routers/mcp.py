from fastapi import APIRouter, HTTPException, Depends
import time
import json
from typing import Dict, Any, List, Optional

from ..models import MCPMessage, GenerateTextRequest
from ..services.graphql_client import GraphQLClient
from ..services.mcp_client import MCPClient

router = APIRouter(prefix="/mcp", tags=["mcp"])

# Track server start time for uptime calculation
START_TIME = time.time()


def get_graphql_client():
    return GraphQLClient()


def get_mcp_client():
    return MCPClient()


@router.post("/message")
async def receive_message(
    message: MCPMessage,
    graphql_client: GraphQLClient = Depends(get_graphql_client)
):
    """Handle incoming MCP messages."""
    try:
        # Process the message based on content
        content = message.content
        action = content.get("action")

        if action == "generate_text":
            # Forward to GraphQL API
            prompt = content.get("prompt", "")
            max_tokens = content.get("max_tokens", 100)

            result = await graphql_client.generate_text(prompt, max_tokens)

            return {
                "message_id": message.message_id,
                "response": result
            }
        elif action == "translate_text":
            # Forward to GraphQL API
            text = content.get("text", "")
            source_language = content.get("source_language", "en")
            target_language = content.get("target_language", "es")

            result = await graphql_client.translate_text(text, source_language, target_language)

            return {
                "message_id": message.message_id,
                "response": result
            }
        elif action == "classify_text":
            # Forward to GraphQL API
            text = content.get("text", "")
            categories = content.get("categories")

            result = await graphql_client.classify_text(text, categories)

            return {
                "message_id": message.message_id,
                "response": result
            }
        elif action == "analyze_sentiment":
            # Forward to GraphQL API
            text = content.get("text", "")

            result = await graphql_client.analyze_sentiment(text)

            return {
                "message_id": message.message_id,
                "response": result
            }
        elif action == "get_status":
            # Get status from GraphQL API
            result = await graphql_client.get_status()

            return {
                "message_id": message.message_id,
                "response": result
            }
        else:
            return {
                "message_id": message.message_id,
                "error": f"Unknown action: {action}"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")


@router.post("/generate")
async def generate_text(
    request: GenerateTextRequest,
    graphql_client: GraphQLClient = Depends(get_graphql_client)
):
    """Generate text using the GraphQL API."""
    try:
        result = await graphql_client.generate_text(request.prompt, request.max_tokens)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating text: {str(e)}")


@router.get("/status")
async def get_status(
    graphql_client: GraphQLClient = Depends(get_graphql_client),
    mcp_client: MCPClient = Depends(get_mcp_client)
):
    """Get the status of this MCP server and connected services."""
    try:
        # Get GraphQL API status
        graphql_status = await graphql_client.get_status()

        # Get MCP servers
        mcp_servers = await mcp_client.get_mcp_servers()
        connected_services = [server.get("name") for server in mcp_servers if server.get("id") != mcp_client.server_id]

        uptime = int(time.time() - START_TIME)

        return {
            "status": "online",
            "load": graphql_status.get("load", 0.0) if isinstance(graphql_status, dict) else 0.0,
            "uptime": uptime,
            "connected_services": connected_services,
            "graphql_api_status": graphql_status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting status: {str(e)}")
