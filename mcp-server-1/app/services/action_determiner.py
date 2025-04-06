"""
Service for determining the appropriate action based on user input.
This service uses OpenAI to analyze the input and determine the appropriate action.
"""

import re
import os
import json
import uuid
from typing import Dict, Any, Tuple, List, Optional
from openai import OpenAI

# Import the logger
try:
    from common.logger import get_logger
except ImportError:
    # Fallback if common package is not available
    import logging
    def get_logger(service_name, log_level="INFO"):
        logger = logging.getLogger(service_name)
        logger.setLevel(getattr(logging, log_level))
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
        return logger


class ActionDeterminer:
    """Determines the appropriate action based on user input using OpenAI."""

    def __init__(self):
        # Initialize logger
        self.logger = get_logger("action-determiner")
        self.logger.info("Initializing ActionDeterminer")

        # Initialize OpenAI client
        api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-3.5-turbo"  # Using GPT-3.5 Turbo for faster responses

        # Define capabilities of each service
        self.service_capabilities = {
            "rest": ["generate_text", "summarize", "analyze_data"],
            "graphql": ["generate_text", "translate_text", "classify_text", "analyze_sentiment"]
        }

        # Define the system prompt for action determination
        self.system_prompt = """
You are an AI assistant that determines the appropriate action to take based on user input.

Available actions:
1. generate_text - Generate text based on a prompt (REST API)
2. summarize - Summarize a piece of text (REST API)
3. analyze_data - Analyze data and provide insights (REST API)
4. translate_text - Translate text from one language to another (GraphQL API)
5. classify_text - Classify text into categories (GraphQL API)
6. analyze_sentiment - Analyze the sentiment of text (GraphQL API)

Your task is to determine which action best matches the user's request and which service (REST or GraphQL) should handle it.
You must also extract the relevant parameters for the action.

Respond in JSON format with the following structure:
{
    "action": "action_name",
    "service_type": "rest" or "graphql",
    "parameters": {
        // Action-specific parameters
    },
    "reasoning": "Brief explanation of why you chose this action"
}
"""

    def determine_action(self, input_text: str, trace_id: Optional[str] = None) -> Tuple[str, Dict[str, Any], str]:
        """
        Determine the appropriate action based on the input text using OpenAI.

        Args:
            input_text: The user's input text

        Returns:
            Tuple containing:
            - action: The determined action
            - params: Parameters for the action
            - service_type: The type of service to use ("rest" or "graphql")
        """
        # Generate trace_id if not provided
        trace_id = trace_id or str(uuid.uuid4())

        self.logger.info(f"Determining action for input: '{input_text[:50]}...'" if len(input_text) > 50 else f"Determining action for input: '{input_text}'", trace_id=trace_id)

        try:
            # Call OpenAI API
            self.logger.debug("Calling OpenAI API", trace_id=trace_id)
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": input_text}
                ],
                temperature=0.1,  # Low temperature for more deterministic responses
                max_tokens=1000
            )

            # Extract the response content
            response_content = response.choices[0].message.content
            self.logger.debug("Received response from OpenAI", trace_id=trace_id, extra_data={"response": response_content[:200] + "..." if len(response_content) > 200 else response_content})

            # Try to parse the JSON response
            try:
                # Find JSON in the response (in case there's additional text)
                json_match = re.search(r'\{[\s\S]*\}', response_content)
                if json_match:
                    json_str = json_match.group(0)
                    result = json.loads(json_str)
                else:
                    # Fallback if no JSON is found
                    self.logger.warning(f"No JSON found in OpenAI response", trace_id=trace_id, extra_data={"response": response_content})
                    return self._fallback_determination(input_text, trace_id)

                # Extract action, service_type, and parameters
                action = result.get("action", "generate_text")
                service_type = result.get("service_type", "rest")
                params = result.get("parameters", {})

                # Log the reasoning for debugging
                reasoning = result.get("reasoning", "No reasoning provided")
                self.logger.info(f"OpenAI reasoning: {reasoning}", trace_id=trace_id)

                # Validate the action and service_type
                if action not in self.service_capabilities["rest"] + self.service_capabilities["graphql"]:
                    self.logger.warning(f"Invalid action: {action}. Falling back to default.", trace_id=trace_id)
                    return self._fallback_determination(input_text, trace_id)

                if service_type not in ["rest", "graphql"]:
                    self.logger.warning(f"Invalid service type: {service_type}. Falling back to default.", trace_id=trace_id)
                    return self._fallback_determination(input_text, trace_id)

                # Ensure the action is supported by the service
                if action not in self.service_capabilities[service_type]:
                    # If the action is not supported by the service, use the other service
                    other_service = "graphql" if service_type == "rest" else "rest"
                    if action in self.service_capabilities[other_service]:
                        service_type = other_service
                        self.logger.info(f"Action {action} is not supported by {service_type}. Using {other_service} instead.", trace_id=trace_id)
                    else:
                        self.logger.warning(f"Action {action} is not supported by any service. Falling back to default.", trace_id=trace_id)
                        return self._fallback_determination(input_text, trace_id)

                # Ensure required parameters are present
                if action == "generate_text" and "prompt" not in params:
                    params["prompt"] = input_text
                    params["max_tokens"] = params.get("max_tokens", 100)

                elif action == "summarize" and "text" not in params:
                    params["text"] = input_text
                    params["max_length"] = params.get("max_length", 100)

                elif action == "analyze_data":
                    if "data" not in params:
                        # Try to extract JSON data
                        data = self._extract_json(input_text)
                        params["data"] = data or {}
                    if "query" not in params:
                        params["query"] = input_text.split("{")[0].strip() if "{" in input_text else input_text

                elif action == "translate_text":
                    if "text" not in params:
                        params["text"] = self._extract_text_for_translation(input_text)
                    if "source_language" not in params or "target_language" not in params:
                        source_lang, target_lang = self._extract_languages(input_text)
                        params["source_language"] = params.get("source_language", source_lang)
                        params["target_language"] = params.get("target_language", target_lang)

                elif action == "classify_text":
                    if "text" not in params:
                        params["text"] = self._extract_text_for_classification(input_text)
                    if "categories" not in params:
                        categories = self._extract_categories(input_text)
                        if categories:
                            params["categories"] = categories

                elif action == "analyze_sentiment":
                    if "text" not in params:
                        params["text"] = self._extract_text_for_sentiment(input_text)

                self.logger.info(f"Determined action: {action}, service: {service_type}", trace_id=trace_id, extra_data={"action": action, "service_type": service_type, "parameters": params})
                return action, params, service_type

            except json.JSONDecodeError as e:
                self.logger.error(f"Error parsing OpenAI response as JSON: {e}", trace_id=trace_id, extra_data={"response": response_content})
                return self._fallback_determination(input_text, trace_id)

        except Exception as e:
            self.logger.error(f"Error calling OpenAI: {e}", trace_id=trace_id)
            return self._fallback_determination(input_text, trace_id)

    def _fallback_determination(self, input_text: str, trace_id: Optional[str] = None) -> Tuple[str, Dict[str, Any], str]:
        """Fallback method for determining action when OpenAI fails."""
        trace_id = trace_id or str(uuid.uuid4())
        self.logger.warning("Using fallback action determination", trace_id=trace_id)

        # Simple keyword-based fallback
        if any(word in input_text.lower() for word in ["translate", "translation", "spanish", "french", "german"]):
            source_lang, target_lang = self._extract_languages(input_text)
            text = self._extract_text_for_translation(input_text)
            return "translate_text", {"text": text, "source_language": source_lang, "target_language": target_lang}, "graphql"

        elif any(word in input_text.lower() for word in ["summarize", "summary", "shorten", "brief"]):
            return "summarize", {"text": input_text, "max_length": 100}, "rest"

        elif any(word in input_text.lower() for word in ["sentiment", "feeling", "emotion", "positive", "negative"]):
            return "analyze_sentiment", {"text": input_text}, "graphql"

        elif any(word in input_text.lower() for word in ["classify", "categorize", "category", "type"]):
            categories = self._extract_categories(input_text)
            params = {"text": input_text}
            if categories:
                params["categories"] = categories
            return "classify_text", params, "graphql"

        elif any(word in input_text.lower() for word in ["analyze", "analysis", "data", "statistics"]) or "{" in input_text:
            data = self._extract_json(input_text)
            query = input_text.split("{")[0].strip() if "{" in input_text else input_text
            return "analyze_data", {"query": query, "data": data or {}}, "rest"

        # Default to generate_text
        return "generate_text", {"prompt": input_text, "max_tokens": 100}, "rest"

    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Try to extract JSON data from the input text."""
        try:
            # Find text between curly braces
            match = re.search(r'{.*}', text, re.DOTALL)
            if match:
                import json
                json_str = match.group(0)
                return json.loads(json_str)
        except:
            pass
        return None

    def _is_translation_request(self, text: str) -> bool:
        """Check if the input is a translation request."""
        translation_keywords = [
            "translate", "translation", "convert to", "in spanish", "in french",
            "in german", "in chinese", "in japanese", "in italian", "in russian",
            "from english to", "from spanish to", "from french to"
        ]
        return any(keyword in text.lower() for keyword in translation_keywords)

    def _extract_languages(self, text: str) -> Tuple[str, str]:
        """Extract source and target languages from the input."""
        # Default languages
        source_lang = "en"
        target_lang = "es"

        # Try to extract languages from text
        from_pattern = r"(?i)from\s+(\w+)\s+to\s+(\w+)"
        match = re.search(from_pattern, text)
        if match:
            source_lang = match.group(1).lower()
            target_lang = match.group(2).lower()
            return source_lang, target_lang

        # Check for target language mentions
        lang_map = {
            "spanish": "es", "french": "fr", "german": "de", "italian": "it",
            "chinese": "zh", "japanese": "ja", "russian": "ru", "portuguese": "pt",
            "arabic": "ar", "hindi": "hi", "korean": "ko", "dutch": "nl"
        }

        for lang, code in lang_map.items():
            if f"in {lang}" in text.lower() or f"to {lang}" in text.lower():
                target_lang = code
                break

        return source_lang, target_lang

    def _extract_text_for_translation(self, text: str) -> str:
        """Extract the text to be translated."""
        # Remove translation instructions to get the actual text
        for phrase in ["translate", "translation", "convert to", "in spanish", "in french",
                      "in german", "in chinese", "in japanese", "in italian", "in russian",
                      "from english to", "from spanish to", "from french to"]:
            text = text.lower().replace(phrase, "")

        return text.strip()

    def _is_classification_request(self, text: str) -> bool:
        """Check if the input is a classification request."""
        classification_keywords = [
            "classify", "categorize", "categorise", "sort", "group",
            "what category", "which category", "what type", "which type"
        ]
        return any(keyword in text.lower() for keyword in classification_keywords)

    def _extract_categories(self, text: str) -> List[str]:
        """Extract categories from the input."""
        # Look for categories in brackets or parentheses
        bracket_pattern = r'\[(.*?)\]'
        paren_pattern = r'\((.*?)\)'

        categories = []

        # Check for bracketed categories
        bracket_match = re.search(bracket_pattern, text)
        if bracket_match:
            cats = bracket_match.group(1).split(',')
            categories.extend([c.strip() for c in cats])

        # Check for parenthesized categories
        paren_match = re.search(paren_pattern, text)
        if paren_match:
            cats = paren_match.group(1).split(',')
            categories.extend([c.strip() for c in cats])

        return categories

    def _extract_text_for_classification(self, text: str) -> str:
        """Extract the text to be classified."""
        # Remove classification instructions and category lists
        for phrase in ["classify", "categorize", "categorise", "sort", "group",
                      "what category", "which category", "what type", "which type"]:
            text = text.lower().replace(phrase, "")

        # Remove bracketed categories
        text = re.sub(r'\[.*?\]', '', text)

        # Remove parenthesized categories
        text = re.sub(r'\(.*?\)', '', text)

        return text.strip()

    def _is_sentiment_request(self, text: str) -> bool:
        """Check if the input is a sentiment analysis request."""
        sentiment_keywords = [
            "sentiment", "feeling", "emotion", "tone", "attitude",
            "positive or negative", "mood", "opinion"
        ]
        return any(keyword in text.lower() for keyword in sentiment_keywords)

    def _extract_text_for_sentiment(self, text: str) -> str:
        """Extract the text for sentiment analysis."""
        # Remove sentiment analysis instructions
        for phrase in ["sentiment", "feeling", "emotion", "tone", "attitude",
                      "positive or negative", "mood", "opinion", "analyze"]:
            text = text.lower().replace(phrase, "")

        return text.strip()
