from fastapi import APIRouter, HTTPException
import time
import random
import asyncio

from ..models import (
    GenerateRequest, GenerateResponse, generate_mock_text,
    SummarizeRequest, SummarizeResponse, summarize_mock_text,
    AnalyzeRequest, AnalyzeResponse, analyze_mock_data,
    ServerStatus
)

router = APIRouter(prefix="/api", tags=["api"])

# Track server start time for uptime calculation
START_TIME = time.time()


@router.post("/generate", response_model=GenerateResponse)
async def generate_text(request: GenerateRequest):
    """Generate text based on the provided prompt."""
    try:
        # Simulate processing time
        await asyncio.sleep(random.uniform(0.1, 0.5))

        # Generate mock response
        response = generate_mock_text(request.prompt, request.max_tokens)
        return response
    except Exception as e:
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
