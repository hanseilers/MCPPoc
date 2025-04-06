import os
import httpx
import logging
import traceback
import json
from typing import Dict, Any, Optional, List

from ..models import GenerateTextRequest

# Configure logging
logger = logging.getLogger("rest-client")


class RestApiClient:
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or os.getenv("REST_API_URL", "http://rest-api-server:8000")

    async def generate_text(self, prompt: str, max_tokens: int = 100) -> Dict[str, Any]:
        """Call the REST API to generate text."""
        request_id = os.environ.get("TRACE_ID", "unknown")
        # Use a longer timeout for LLM processing
        logger.info(f"[{request_id}] Generating text with prompt: '{prompt[:50]}...'" if len(prompt) > 50 else f"[{request_id}] Generating text with prompt: '{prompt}'")

        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                logger.info(f"[{request_id}] Sending request to {self.base_url}/api/generate with max_tokens: {max_tokens}")
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "prompt": prompt,
                        "max_tokens": max_tokens
                    }
                )
                logger.info(f"[{request_id}] Received response with status code: {response.status_code}")

                if response.status_code == 200:
                    try:
                        result = response.json()
                        logger.info(f"[{request_id}] Successfully generated text with model: {result.get('model_used', 'unknown')}")
                        return result
                    except json.JSONDecodeError as e:
                        error_msg = f"Failed to parse JSON response: {str(e)}"
                        logger.error(f"[{request_id}] {error_msg}\nResponse text: {response.text}\n{traceback.format_exc()}")
                        return {
                            "error": "Invalid response from REST API",
                            "details": error_msg
                        }
                else:
                    error_msg = f"API request failed with status {response.status_code}"
                    logger.error(f"[{request_id}] {error_msg}\nResponse text: {response.text}")
                    return {
                        "error": error_msg,
                        "details": response.text
                    }
            except httpx.TimeoutException as e:
                error_msg = f"Request timed out after 120 seconds: {str(e)}"
                logger.error(f"[{request_id}] {error_msg}")
                return {
                    "error": "REST API request timed out",
                    "details": error_msg
                }
            except httpx.ConnectError as e:
                error_msg = f"Connection error to {self.base_url}: {str(e)}"
                logger.error(f"[{request_id}] {error_msg}")
                return {
                    "error": "Failed to connect to REST API",
                    "details": error_msg
                }
            except Exception as e:
                error_msg = f"Unexpected error: {str(e)}"
                logger.error(f"[{request_id}] {error_msg}\n{traceback.format_exc()}")
                return {
                    "error": "Failed to connect to REST API",
                    "details": error_msg
                }

    async def summarize_text(self, text: str, max_length: int = 100) -> Dict[str, Any]:
        """Call the REST API to summarize text."""
        request_id = os.environ.get("TRACE_ID", "unknown")
        logger.info(f"[{request_id}] Summarizing text of length {len(text)} with max_length: {max_length}")

        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                logger.info(f"[{request_id}] Sending request to {self.base_url}/api/summarize")
                response = await client.post(
                    f"{self.base_url}/api/summarize",
                    json={
                        "text": text,
                        "max_length": max_length
                    }
                )
                logger.info(f"[{request_id}] Received response with status code: {response.status_code}")

                if response.status_code == 200:
                    try:
                        result = response.json()
                        logger.info(f"[{request_id}] Successfully summarized text with model: {result.get('model_used', 'unknown')}")
                        return result
                    except json.JSONDecodeError as e:
                        error_msg = f"Failed to parse JSON response: {str(e)}"
                        logger.error(f"[{request_id}] {error_msg}\nResponse text: {response.text}\n{traceback.format_exc()}")
                        return {
                            "error": "Invalid response from REST API",
                            "details": error_msg
                        }
                else:
                    error_msg = f"API request failed with status {response.status_code}"
                    logger.error(f"[{request_id}] {error_msg}\nResponse text: {response.text}")
                    return {
                        "error": error_msg,
                        "details": response.text
                    }
            except httpx.TimeoutException as e:
                error_msg = f"Request timed out after 120 seconds: {str(e)}"
                logger.error(f"[{request_id}] {error_msg}")
                return {
                    "error": "REST API request timed out",
                    "details": error_msg
                }
            except httpx.ConnectError as e:
                error_msg = f"Connection error to {self.base_url}: {str(e)}"
                logger.error(f"[{request_id}] {error_msg}")
                return {
                    "error": "Failed to connect to REST API",
                    "details": error_msg
                }
            except Exception as e:
                error_msg = f"Unexpected error: {str(e)}"
                logger.error(f"[{request_id}] {error_msg}\n{traceback.format_exc()}")
                return {
                    "error": "Failed to connect to REST API",
                    "details": error_msg
                }

    async def analyze_data(self, query: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Call the REST API to analyze data."""
        request_id = os.environ.get("TRACE_ID", "unknown")
        logger.info(f"[{request_id}] Analyzing data with query: '{query[:50]}...'" if len(query) > 50 else f"[{request_id}] Analyzing data with query: '{query}'")

        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                logger.info(f"[{request_id}] Sending request to {self.base_url}/api/analyze")
                response = await client.post(
                    f"{self.base_url}/api/analyze",
                    json={
                        "query": query,
                        "data": data
                    }
                )
                logger.info(f"[{request_id}] Received response with status code: {response.status_code}")

                if response.status_code == 200:
                    try:
                        result = response.json()
                        logger.info(f"[{request_id}] Successfully analyzed data with model: {result.get('model_used', 'unknown')}")
                        return result
                    except json.JSONDecodeError as e:
                        error_msg = f"Failed to parse JSON response: {str(e)}"
                        logger.error(f"[{request_id}] {error_msg}\nResponse text: {response.text}\n{traceback.format_exc()}")
                        return {
                            "error": "Invalid response from REST API",
                            "details": error_msg
                        }
                else:
                    error_msg = f"API request failed with status {response.status_code}"
                    logger.error(f"[{request_id}] {error_msg}\nResponse text: {response.text}")
                    return {
                        "error": error_msg,
                        "details": response.text
                    }
            except httpx.TimeoutException as e:
                error_msg = f"Request timed out after 120 seconds: {str(e)}"
                logger.error(f"[{request_id}] {error_msg}")
                return {
                    "error": "REST API request timed out",
                    "details": error_msg
                }
            except httpx.ConnectError as e:
                error_msg = f"Connection error to {self.base_url}: {str(e)}"
                logger.error(f"[{request_id}] {error_msg}")
                return {
                    "error": "Failed to connect to REST API",
                    "details": error_msg
                }
            except Exception as e:
                error_msg = f"Unexpected error: {str(e)}"
                logger.error(f"[{request_id}] {error_msg}\n{traceback.format_exc()}")
                return {
                    "error": "Failed to connect to REST API",
                    "details": error_msg
                }

    async def get_status(self) -> Dict[str, Any]:
        """Get the status of the REST API server."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                print(f"Checking status of REST API at {self.base_url}/api/status")
                response = await client.get(f"{self.base_url}/api/status")
                print(f"Received status response with code: {response.status_code}")

                if response.status_code == 200:
                    result = response.json()
                    print(f"REST API status: {result}")
                    return result
                else:
                    error_msg = f"API status request failed with status {response.status_code}"
                    print(f"Error: {error_msg}")
                    return {
                        "status": "offline",
                        "error": error_msg,
                        "details": response.text
                    }
            except httpx.TimeoutException as e:
                error_msg = f"Status request timed out: {str(e)}"
                print(f"Error: {error_msg}")
                return {
                    "status": "offline",
                    "error": "REST API status request timed out",
                    "details": error_msg
                }
            except httpx.ConnectError as e:
                error_msg = f"Status connection error: {str(e)}"
                print(f"Error: {error_msg}")
                return {
                    "status": "offline",
                    "error": "Failed to connect to REST API",
                    "details": error_msg
                }
            except Exception as e:
                error_msg = f"Unexpected error in status check: {str(e)}"
                print(f"Error: {error_msg}")
                return {
                    "status": "offline",
                    "error": "Failed to connect to REST API",
                    "details": error_msg
                }
