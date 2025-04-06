import os
import httpx
from typing import Dict, Any, Optional, List

from ..models import GenerateTextRequest


class RestApiClient:
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or os.getenv("REST_API_URL", "http://localhost:8001")

    async def generate_text(self, prompt: str, max_tokens: int = 100) -> Dict[str, Any]:
        """Call the REST API to generate text."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "prompt": prompt,
                        "max_tokens": max_tokens
                    }
                )

                if response.status_code == 200:
                    return response.json()
                else:
                    return {
                        "error": f"API request failed with status {response.status_code}",
                        "details": response.text
                    }
            except Exception as e:
                return {
                    "error": "Failed to connect to REST API",
                    "details": str(e)
                }

    async def summarize_text(self, text: str, max_length: int = 100) -> Dict[str, Any]:
        """Call the REST API to summarize text."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/summarize",
                    json={
                        "text": text,
                        "max_length": max_length
                    }
                )

                if response.status_code == 200:
                    return response.json()
                else:
                    return {
                        "error": f"API request failed with status {response.status_code}",
                        "details": response.text
                    }
            except Exception as e:
                return {
                    "error": "Failed to connect to REST API",
                    "details": str(e)
                }

    async def analyze_data(self, query: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Call the REST API to analyze data."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/analyze",
                    json={
                        "query": query,
                        "data": data
                    }
                )

                if response.status_code == 200:
                    return response.json()
                else:
                    return {
                        "error": f"API request failed with status {response.status_code}",
                        "details": response.text
                    }
            except Exception as e:
                return {
                    "error": "Failed to connect to REST API",
                    "details": str(e)
                }

    async def get_status(self) -> Dict[str, Any]:
        """Get the status of the REST API server."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.base_url}/api/status")

                if response.status_code == 200:
                    return response.json()
                else:
                    return {
                        "error": f"API request failed with status {response.status_code}",
                        "details": response.text
                    }
            except Exception as e:
                return {
                    "error": "Failed to connect to REST API",
                    "details": str(e)
                }
