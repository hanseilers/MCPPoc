import random
from typing import List, Optional, Dict, Any, Tuple
from enum import Enum

# Mock models for demonstration
MOCK_MODELS = ["gpt-3.5-turbo", "gpt-4", "claude-2", "llama-2"]


def generate_mock_text(prompt: str, max_tokens: int = 100) -> Tuple[str, float, str]:
    """Generate mock AI text response."""
    # Simple mock response generator
    responses = [
        f"This is a mock response to: '{prompt}'. It simulates an AI response with {max_tokens} tokens.",
        f"I'm a simulated AI model responding to: '{prompt}'. This response is limited to {max_tokens} tokens.",
        f"Mock AI processing complete for prompt: '{prompt}'. Response generated with {max_tokens} token limit.",
        f"Here's what I think about '{prompt}': This is a simulated response with {max_tokens} tokens."
    ]

    return (
        random.choice(responses),
        random.uniform(0.7, 0.99),
        random.choice(MOCK_MODELS)
    )


def translate_mock_text(text: str, source_lang: str, target_lang: str) -> Tuple[str, float, str, str]:
    """Generate mock translation."""
    # Simple mock translation generator
    translation = f"TRANSLATED [{source_lang} → {target_lang}]: {text}"

    return (
        translation,
        random.uniform(0.7, 0.99),  # confidence
        random.choice(MOCK_MODELS),  # model
        f"{source_lang}-{target_lang}"  # language pair
    )


def classify_mock_text(text: str, categories: List[str]) -> Tuple[str, List[Tuple[str, float]], str]:
    """Generate mock text classification."""
    # Generate mock classification results
    if not categories:
        categories = ["positive", "negative", "neutral"]

    # Select a primary category
    primary_category = random.choice(categories)

    # Generate confidence scores for all categories
    category_scores = []
    remaining_confidence = 1.0

    # Assign high confidence to primary category
    primary_confidence = random.uniform(0.6, 0.9)
    remaining_confidence -= primary_confidence
    category_scores.append((primary_category, primary_confidence))

    # Distribute remaining confidence among other categories
    other_categories = [c for c in categories if c != primary_category]
    for i, category in enumerate(other_categories):
        if i == len(other_categories) - 1:
            # Last category gets all remaining confidence
            category_scores.append((category, remaining_confidence))
        else:
            # Randomly assign confidence to this category
            confidence = remaining_confidence * random.uniform(0.1, 0.5)
            remaining_confidence -= confidence
            category_scores.append((category, confidence))

    # Sort by confidence (descending)
    category_scores.sort(key=lambda x: x[1], reverse=True)

    return (
        f"The text has been classified as: {primary_category}",
        category_scores,
        random.choice(MOCK_MODELS)
    )


def sentiment_mock_analysis(text: str) -> Tuple[str, float, Dict[str, float], str]:
    """Generate mock sentiment analysis."""
    # Generate mock sentiment scores
    sentiment_scores = {
        "positive": random.uniform(0, 1),
        "negative": random.uniform(0, 1),
        "neutral": random.uniform(0, 1)
    }

    # Normalize scores
    total = sum(sentiment_scores.values())
    for key in sentiment_scores:
        sentiment_scores[key] /= total

    # Determine overall sentiment
    max_sentiment = max(sentiment_scores.items(), key=lambda x: x[1])
    overall_sentiment = max_sentiment[0]
    confidence = max_sentiment[1]

    return (
        f"The sentiment of the text is: {overall_sentiment.upper()}",
        confidence,
        sentiment_scores,
        random.choice(MOCK_MODELS)
    )
