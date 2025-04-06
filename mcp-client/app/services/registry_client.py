import os
import httpx
from typing import Dict, Any, List, Optional


class RegistryClient:
    def __init__(self, registry_url: Optional[str] = None):
        self.registry_url = registry_url or os.getenv("REGISTRY_URL", "http://localhost:8000")
    
    async def get_all_services(self) -> List[Dict[str, Any]]:
        """Get all registered services from the registry."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.registry_url}/registry/services")
                
                if response.status_code == 200:
                    return response.json()
                else:
                    print(f"Failed to get services: {response.text}")
                    return []
            except Exception as e:
                print(f"Error getting services: {str(e)}")
                return []
    
    async def get_services_by_type(self, service_type: str) -> List[Dict[str, Any]]:
        """Get all services of a specific type from the registry."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.registry_url}/registry/services?type={service_type}")
                
                if response.status_code == 200:
                    return response.json()
                else:
                    print(f"Failed to get services: {response.text}")
                    return []
            except Exception as e:
                print(f"Error getting services: {str(e)}")
                return []
    
    async def get_service(self, service_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific service from the registry."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.registry_url}/registry/services/{service_id}")
                
                if response.status_code == 200:
                    return response.json()
                else:
                    print(f"Failed to get service: {response.text}")
                    return None
            except Exception as e:
                print(f"Error getting service: {str(e)}")
                return None
