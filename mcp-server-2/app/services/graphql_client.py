import os
import httpx
import json
from typing import Dict, Any, Optional, List

from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport


class GraphQLClient:
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or os.getenv("GRAPHQL_API_URL", "http://localhost:8002")
        self.graphql_endpoint = f"{self.base_url}/graphql"

    async def generate_text(self, prompt: str, max_tokens: int = 100) -> Dict[str, Any]:
        """Call the GraphQL API to generate text."""
        try:
            # Create a transport
            transport = AIOHTTPTransport(url=self.graphql_endpoint)

            # Create a client
            async with Client(
                transport=transport,
                fetch_schema_from_transport=True,
            ) as client:
                # Define the query
                query = gql("""
                query GenerateText($prompt: String!, $maxTokens: Int) {
                    generateText(prompt: $prompt, maxTokens: $maxTokens) {
                        text
                        confidence
                        modelUsed
                    }
                }
                """)

                # Execute the query
                result = await client.execute_async(
                    query,
                    variable_values={
                        "prompt": prompt,
                        "maxTokens": max_tokens
                    }
                )

                # Convert from GraphQL naming convention to our model
                if "generateText" in result:
                    return {
                        "text": result["generateText"]["text"],
                        "confidence": result["generateText"]["confidence"],
                        "model_used": result["generateText"]["modelUsed"]
                    }
                else:
                    return {
                        "error": "Unexpected response format",
                        "details": result
                    }
        except Exception as e:
            return {
                "error": "Failed to connect to GraphQL API",
                "details": str(e)
            }

    async def translate_text(self, text: str, source_language: str, target_language: str) -> Dict[str, Any]:
        """Call the GraphQL API to translate text."""
        try:
            # Create a transport
            transport = AIOHTTPTransport(url=self.graphql_endpoint)

            # Create a client
            async with Client(
                transport=transport,
                fetch_schema_from_transport=True,
            ) as client:
                # Define the query
                query = gql("""
                query TranslateText($text: String!, $sourceLanguage: String!, $targetLanguage: String!) {
                    translateText(text: $text, sourceLanguage: $sourceLanguage, targetLanguage: $targetLanguage) {
                        translatedText
                        confidence
                        modelUsed
                        languagePair
                    }
                }
                """)

                # Execute the query
                result = await client.execute_async(
                    query,
                    variable_values={
                        "text": text,
                        "sourceLanguage": source_language,
                        "targetLanguage": target_language
                    }
                )

                # Convert from GraphQL naming convention to our model
                if "translateText" in result:
                    return {
                        "translated_text": result["translateText"]["translatedText"],
                        "confidence": result["translateText"]["confidence"],
                        "model_used": result["translateText"]["modelUsed"],
                        "language_pair": result["translateText"]["languagePair"]
                    }
                else:
                    return {
                        "error": "Unexpected response format",
                        "details": result
                    }
        except Exception as e:
            return {
                "error": "Failed to connect to GraphQL API",
                "details": str(e)
            }

    async def classify_text(self, text: str, categories: Optional[List[str]] = None) -> Dict[str, Any]:
        """Call the GraphQL API to classify text."""
        try:
            # Create a transport
            transport = AIOHTTPTransport(url=self.graphql_endpoint)

            # Create a client
            async with Client(
                transport=transport,
                fetch_schema_from_transport=True,
            ) as client:
                # Define the query
                query = gql("""
                query ClassifyText($text: String!, $categories: [String!]) {
                    classifyText(text: $text, categories: $categories) {
                        result
                        categories {
                            category
                            confidence
                        }
                        modelUsed
                    }
                }
                """)

                # Execute the query
                result = await client.execute_async(
                    query,
                    variable_values={
                        "text": text,
                        "categories": categories
                    }
                )

                # Convert from GraphQL naming convention to our model
                if "classifyText" in result:
                    return {
                        "result": result["classifyText"]["result"],
                        "categories": [
                            {"category": cat["category"], "confidence": cat["confidence"]}
                            for cat in result["classifyText"]["categories"]
                        ],
                        "model_used": result["classifyText"]["modelUsed"]
                    }
                else:
                    return {
                        "error": "Unexpected response format",
                        "details": result
                    }
        except Exception as e:
            return {
                "error": "Failed to connect to GraphQL API",
                "details": str(e)
            }

    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Call the GraphQL API to analyze sentiment."""
        try:
            # Create a transport
            transport = AIOHTTPTransport(url=self.graphql_endpoint)

            # Create a client
            async with Client(
                transport=transport,
                fetch_schema_from_transport=True,
            ) as client:
                # Define the query
                query = gql("""
                query AnalyzeSentiment($text: String!) {
                    analyzeSentiment(text: $text) {
                        result
                        confidence
                        scores {
                            positive
                            negative
                            neutral
                        }
                        modelUsed
                    }
                }
                """)

                # Execute the query
                result = await client.execute_async(
                    query,
                    variable_values={
                        "text": text
                    }
                )

                # Convert from GraphQL naming convention to our model
                if "analyzeSentiment" in result:
                    return {
                        "result": result["analyzeSentiment"]["result"],
                        "confidence": result["analyzeSentiment"]["confidence"],
                        "scores": {
                            "positive": result["analyzeSentiment"]["scores"]["positive"],
                            "negative": result["analyzeSentiment"]["scores"]["negative"],
                            "neutral": result["analyzeSentiment"]["scores"]["neutral"]
                        },
                        "model_used": result["analyzeSentiment"]["modelUsed"]
                    }
                else:
                    return {
                        "error": "Unexpected response format",
                        "details": result
                    }
        except Exception as e:
            return {
                "error": "Failed to connect to GraphQL API",
                "details": str(e)
            }

    async def get_status(self) -> Dict[str, Any]:
        """Get the status of the GraphQL API server."""
        try:
            # Create a transport
            transport = AIOHTTPTransport(url=self.graphql_endpoint)

            # Create a client
            async with Client(
                transport=transport,
                fetch_schema_from_transport=True,
            ) as client:
                # Define the query
                query = gql("""
                query GetStatus {
                    getStatus {
                        status
                        load
                        uptime
                        capabilities
                    }
                }
                """)

                # Execute the query
                result = await client.execute_async(query)

                if "getStatus" in result:
                    return {
                        "status": result["getStatus"]["status"],
                        "load": result["getStatus"]["load"],
                        "uptime": result["getStatus"]["uptime"],
                        "capabilities": result["getStatus"].get("capabilities", [])
                    }
                else:
                    return {
                        "error": "Unexpected response format",
                        "details": result
                    }
        except Exception as e:
            return {
                "error": "Failed to connect to GraphQL API",
                "details": str(e)
            }
