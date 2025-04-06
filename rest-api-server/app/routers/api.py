from fastapi import APIRouter, HTTPException
import time
import random
import asyncio
import os
import httpx
import json
import requests

from ..models import (
    GenerateRequest, GenerateResponse, generate_mock_text,
    SummarizeRequest, SummarizeResponse, summarize_mock_text,
    AnalyzeRequest, AnalyzeResponse, analyze_mock_data,
    ServerStatus
)

router = APIRouter(prefix="/api", tags=["api"])

# Track server start time for uptime calculation
START_TIME = time.time()


@router.get("/health")
async def health_check():
    """Health check endpoint for the REST API server."""
    uptime = time.time() - START_TIME

    # Check if Ollama is available
    ollama_status = "unknown"
    if os.getenv("USE_LOCAL_LLM", "false").lower() == "true":
        ollama_api_url = os.getenv("OLLAMA_API_URL", "http://ollama:11434")
        try:
            response = requests.get(f"{ollama_api_url}/api/version", timeout=2)
            if response.status_code == 200:
                ollama_status = "healthy"
            else:
                ollama_status = "unhealthy"
        except Exception as e:
            ollama_status = f"error: {str(e)}"

    return {
        "status": "healthy",
        "service": "rest-api-server",
        "uptime": uptime,
        "ollama": ollama_status
    }


@router.get("/status")
async def server_status():
    """Get the current status of the server."""
    uptime = time.time() - START_TIME
    return ServerStatus(
        status="running",
        uptime=uptime,
        version="1.0.0"
    )


@router.post("/generate", response_model=GenerateResponse)
async def generate_text(request: GenerateRequest):
    """Generate text based on the provided prompt."""
    try:
        # Check if we should use local LLM
        use_local_llm = os.getenv("USE_LOCAL_LLM", "false").lower() == "true"
        print(f"USE_LOCAL_LLM: {use_local_llm}")

        if use_local_llm:
            # Get Ollama configuration
            ollama_api_url = os.getenv("OLLAMA_API_URL", "http://ollama:11434")
            ollama_model = os.getenv("OLLAMA_MODEL", "llama2:latest")
            print(f"OLLAMA_API_URL: {ollama_api_url}")
            print(f"OLLAMA_MODEL: {ollama_model}")

            # Prepare the request payload
            # Use a default prompt if the provided prompt is empty
            prompt = request.prompt if request.prompt else "Write a poem"
            print(f"Using prompt: {prompt}")

            payload = {
                "model": ollama_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": request.max_tokens
                }
            }

            # Make the API call
            print(f"Making API call to {ollama_api_url}/api/generate")
            print(f"Payload: {payload}")
            try:
                # Use the requests library instead of httpx
                response = requests.post(
                    f"{ollama_api_url}/api/generate",
                    json=payload,
                    timeout=60.0  # Longer timeout for LLM processing
                )
                print(f"API call completed with status code: {response.status_code}")

                # Check if the request was successful
                if response.status_code == 200:
                    # Parse the response
                    response_data = response.json()
                    generated_text = response_data.get("response", "")
                    print(f"Generated text: {generated_text[:100]}..." if len(generated_text) > 100 else f"Generated text: {generated_text}")

                    return GenerateResponse(
                        text=generated_text,
                        confidence=0.95,  # Placeholder confidence value
                        model_used=ollama_model
                    )
                else:
                    # Fall back to mock response if Ollama fails
                    print(f"Error calling Ollama API: {response.status_code} - {response.text}")
                    response = generate_mock_text(request.prompt, request.max_tokens)
                    return response
            except Exception as e:
                print(f"Error making API call: {str(e)}")
                # Fall back to mock response if Ollama fails
                response = generate_mock_text(request.prompt, request.max_tokens)
                return response
        else:
            # Simulate processing time
            await asyncio.sleep(random.uniform(0.1, 0.5))

            # Generate mock response
            response = generate_mock_text(request.prompt, request.max_tokens)
            return response
    except Exception as e:
        print(f"Error generating text: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating text: {str(e)}")


@router.post("/summarize", response_model=SummarizeResponse)
async def summarize_text(request: SummarizeRequest):
    """Summarize the provided text."""
    try:
        # Simulate processing time
        await asyncio.sleep(random.uniform(0.1, 0.5))

        # Generate mock summary
        response = summarize_mock_text(request.text, request.max_length)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error summarizing text: {str(e)}")


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_data(request: AnalyzeRequest):
    """Analyze the provided data based on the query."""
    try:
        # Simulate processing time
        await asyncio.sleep(random.uniform(0.2, 0.7))

        # Generate mock analysis
        response = analyze_mock_data(request.query, request.data)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing data: {str(e)}")


@router.get("/status", response_model=ServerStatus)
async def get_status():
    """Get the current status of the server."""
    uptime = int(time.time() - START_TIME)
    return ServerStatus(
        status="online",
        load=random.uniform(0.1, 0.8),
        uptime=uptime,
        capabilities=["text_generation", "summarization", "data_analysis"]
    )
