from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from enum import Enum
import random
import json


class GenerateRequest(BaseModel):
    prompt: str
    max_tokens: int = 100


class GenerateResponse(BaseModel):
    text: str
    confidence: float
    model_used: str


class SummarizeRequest(BaseModel):
    text: str
    max_length: int = 100


class SummarizeResponse(BaseModel):
    summary: str
    reduction_percentage: float
    model_used: str


class AnalyzeRequest(BaseModel):
    query: str
    data: Dict[str, Any]


class AnalyzeResponse(BaseModel):
    analysis: str
    insights: List[str]
    model_used: str


class ServerStatus(BaseModel):
    status: str
    load: float
    uptime: int
    capabilities: List[str] = ["text_generation", "summarization", "data_analysis"]


# Mock models for demonstration
MOCK_MODELS = ["gpt-3.5-turbo", "gpt-4", "claude-2", "llama2"]


def generate_mock_text(prompt: str, max_tokens: int = 100) -> GenerateResponse:
    """Generate mock AI text response."""
    # Simple mock response generator
    responses = [
        f"This is a mock response to: '{prompt}'. It simulates an AI response with {max_tokens} tokens.",
        f"I'm a simulated AI model responding to: '{prompt}'. This response is limited to {max_tokens} tokens.",
        f"Mock AI processing complete for prompt: '{prompt}'. Response generated with {max_tokens} token limit.",
        f"Here's what I think about '{prompt}': This is a simulated response with {max_tokens} tokens."
    ]

    return GenerateResponse(
        text=random.choice(responses),
        confidence=random.uniform(0.7, 0.99),
        model_used=random.choice(MOCK_MODELS)
    )


def summarize_mock_text(text: str, max_length: int = 100) -> SummarizeResponse:
    """Generate mock text summarization."""
    # Calculate a fake reduction percentage
    original_length = len(text)
    reduction = random.uniform(0.5, 0.9)

    # Simple mock summary generator
    summary = f"SUMMARY: This is a summarized version of the original text ({len(text)} chars). "
    summary += f"The key points are: 1) Important point one; 2) Critical insight two; 3) Notable observation three."

    if len(summary) > max_length:
        summary = summary[:max_length] + "..."

    return SummarizeResponse(
        summary=summary,
        reduction_percentage=reduction,
        model_used=random.choice(MOCK_MODELS)
    )


def analyze_mock_data(query: str, data: Dict[str, Any]) -> AnalyzeResponse:
    """Generate mock data analysis."""
    # Simple mock analysis generator
    analysis = f"ANALYSIS: Based on the provided data with {len(data)} fields, here's my analysis of '{query}'."

    # Generate some fake insights
    insights = [
        f"The data shows a correlation between key metrics.",
        f"There appears to be an anomaly in the '{random.choice(list(data.keys()) if data else ['data'])}' field.",
        f"Based on this data, I recommend focusing on optimization strategies.",
        f"The trend indicates a {random.choice(['positive', 'negative', 'neutral'])} outlook."
    ]

    return AnalyzeResponse(
        analysis=analysis,
        insights=random.sample(insights, k=min(3, len(insights))),
        model_used=random.choice(MOCK_MODELS)
    )
