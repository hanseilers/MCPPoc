import strawberry
import time
import random
import asyncio
from typing import Optional, List, Dict

from .models import (
    generate_mock_text, translate_mock_text,
    classify_mock_text, sentiment_mock_analysis
)

# Track server start time for uptime calculation
START_TIME = time.time()


@strawberry.type
class GenerateResponse:
    text: str
    confidence: float
    model_used: str


@strawberry.type
class TranslationResponse:
    translated_text: str
    confidence: float
    model_used: str
    language_pair: str


@strawberry.type
class CategoryScore:
    category: str
    confidence: float


@strawberry.type
class ClassificationResponse:
    result: str
    categories: List[CategoryScore]
    model_used: str


@strawberry.type
class SentimentScore:
    positive: float
    negative: float
    neutral: float


@strawberry.type
class SentimentResponse:
    result: str
    confidence: float
    scores: SentimentScore
    model_used: str


@strawberry.type
class ServerStatus:
    status: str
    load: float
    uptime: int
    capabilities: List[str] = strawberry.field(default_factory=lambda: [
        "text_generation", "translation", "classification", "sentiment_analysis"
    ])


@strawberry.type
class Query:
    @strawberry.field
    async def generate_text(self, prompt: str, max_tokens: Optional[int] = 100) -> GenerateResponse:
        """Generate text based on the provided prompt."""
        # Simulate processing time
        await asyncio.sleep(random.uniform(0.1, 0.5))

        # Generate mock response
        text, confidence, model_used = generate_mock_text(prompt, max_tokens)
        return GenerateResponse(
            text=text,
            confidence=confidence,
            model_used=model_used
        )

    @strawberry.field
    async def translate_text(self, text: str, source_language: str, target_language: str) -> TranslationResponse:
        """Translate text from source language to target language."""
        # Simulate processing time
        await asyncio.sleep(random.uniform(0.2, 0.6))

        # Generate mock translation
        translated_text, confidence, model_used, language_pair = translate_mock_text(
            text, source_language, target_language
        )

        return TranslationResponse(
            translated_text=translated_text,
            confidence=confidence,
            model_used=model_used,
            language_pair=language_pair
        )

    @strawberry.field
    async def classify_text(self, text: str, categories: Optional[List[str]] = None) -> ClassificationResponse:
        """Classify text into categories."""
        # Simulate processing time
        await asyncio.sleep(random.uniform(0.2, 0.5))

        # Generate mock classification
        result, category_scores, model_used = classify_mock_text(text, categories or [])

        # Convert to CategoryScore objects
        categories_result = [CategoryScore(category=cat, confidence=conf) for cat, conf in category_scores]

        return ClassificationResponse(
            result=result,
            categories=categories_result,
            model_used=model_used
        )

    @strawberry.field
    async def analyze_sentiment(self, text: str) -> SentimentResponse:
        """Analyze the sentiment of the provided text."""
        # Simulate processing time
        await asyncio.sleep(random.uniform(0.1, 0.4))

        # Generate mock sentiment analysis
        result, confidence, scores, model_used = sentiment_mock_analysis(text)

        return SentimentResponse(
            result=result,
            confidence=confidence,
            scores=SentimentScore(
                positive=scores["positive"],
                negative=scores["negative"],
                neutral=scores["neutral"]
            ),
            model_used=model_used
        )

    @strawberry.field
    def get_status(self) -> ServerStatus:
        """Get the current status of the server."""
        uptime = int(time.time() - START_TIME)
        return ServerStatus(
            status="online",
            load=random.uniform(0.1, 0.8),
            uptime=uptime
        )


# Create the schema
schema = strawberry.Schema(query=Query)
