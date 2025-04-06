import os
import httpx
import json
from typing import Dict, Any, List, Optional

from ..models import MCPMessage


class MCPClient:
    def __init__(self, registry_url: Optional[str] = None):
        self.registry_url = registry_url or os.getenv("REGISTRY_URL", "http://localhost:8000")
        self.server_id = None
    
    async def get_mcp_servers(self) -> List[Dict[str, Any]]:
        """Get all registered MCP servers from the registry."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.registry_url}/registry/services?type=mcp")
                
                if response.status_code == 200:
                    return response.json()
                else:
                    print(f"Failed to get MCP servers: {response.text}")
                    return []
            except Exception as e:
                print(f"Error getting MCP servers: {str(e)}")
                return []
    
    async def send_message(self, target_id: str, content: Dict[str, Any]) -> Dict[str, Any]:
        """Send an MCP message to another MCP server."""
        if not self.server_id:
            return {"error": "Server ID not set"}
        
        # Get target server details
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.registry_url}/registry/services/{target_id}")
                
                if response.status_code != 200:
                    return {
                        "error": f"Failed to get target server details: {response.text}"
                    }
                
                target_server = response.json()
                target_url = target_server.get("url")
                
                if not target_url:
                    return {"error": "Target server URL not found"}
                
                # Create MCP message
                message = MCPMessage(
                    source_id=self.server_id,
                    target_id=target_id,
                    content=content
                )
                
                # Send message to target server
                response = await client.post(
                    f"{target_url}/mcp/message",
                    json=message.dict()
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return {
                        "error": f"Failed to send message: {response.text}"
                    }
            except Exception as e:
                return {
                    "error": f"Error sending message: {str(e)}"
                }
    
    def set_server_id(self, server_id: str):
        """Set the server ID for this client."""
        self.server_id = server_id
