"""
Service for determining the appropriate action based on user input.
This service uses OpenAI to analyze the input and determine the appropriate action.
"""

import re
import os
import json
import uuid
import httpx
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
    """Determines the appropriate action based on user input using OpenAI or Ollama."""

    # Class variable to ensure logger is only created once
    _logger = None

    def __init__(self):
        # Initialize logger only if it doesn't exist yet
        if ActionDeterminer._logger is None:
            ActionDeterminer._logger = get_logger("action-determiner")
        self.logger = ActionDeterminer._logger

        self.logger.info("Initializing ActionDeterminer")

        # Check if we should use local LLM
        self.use_local_llm = os.getenv("USE_LOCAL_LLM", "false").lower() == "true"

        if self.use_local_llm:
            # Initialize Ollama client
            self.ollama_api_url = os.getenv("OLLAMA_API_URL", "http://localhost:11434")
            self.ollama_model = os.getenv("OLLAMA_MODEL", "llama3")
            self.logger.info(f"Using local LLM: {self.ollama_model} at {self.ollama_api_url}")
        else:
            # Initialize OpenAI client
            api_key = os.getenv("OPENAI_API_KEY")
            self.client = OpenAI(api_key=api_key)
            self.model = "gpt-3.5-turbo"  # Using GPT-3.5 Turbo for faster responses
            self.logger.info(f"Using OpenAI API with model: {self.model}")

        # Define capabilities of each service
        self.service_capabilities = {
            "rest": ["generate_text", "summarize", "analyze_data"],
            "graphql": ["generate_text", "translate_text", "classify_text", "analyze_sentiment"]
        }

        # Define the system prompt for action determination
        self.system_prompt = """
You are an AI assistant that ONLY determines the appropriate action to take based on user input.

IMPORTANT: You MUST respond ONLY with a valid JSON object and nothing else. Do not generate any text outside the JSON structure.
Do NOT include any comments in the JSON. Do NOT use JavaScript-style comments like // or /* */.
The JSON must be parseable by Python's json.loads() function.

Available actions:
1. generate_text - Generate text based on a prompt (REST API)
2. summarize - Summarize a piece of text (REST API)
3. analyze_data - Analyze data and provide insights (REST API)
4. translate_text - Translate text from one language to another (GraphQL API)
5. classify_text - Classify text into categories (GraphQL API)
6. analyze_sentiment - Analyze the sentiment of text (GraphQL API)

Your task is to determine which action best matches the user's request and which service (REST or GraphQL) should handle it.
You must also extract the relevant parameters for the action.

EXAMPLE 1:
User input: "Make a poem about flowers"
Your response should be exactly:
{
    "action": "generate_text",
    "service_type": "rest",
    "parameters": {
        "prompt": "Make a poem about flowers",
        "max_tokens": 100
    },
    "reasoning": "The user wants to generate a poem, which is a text generation task."
}

EXAMPLE 2:
User input: "Translate 'Hello world' to Spanish"
Your response should be exactly:
{
    "action": "translate_text",
    "service_type": "graphql",
    "parameters": {
        "text": "Hello world",
        "source_language": "en",
        "target_language": "es"
    },
    "reasoning": "The user wants to translate text from English to Spanish."
}

Respond ONLY with a JSON object with the following structure:
{
    "action": "action_name",
    "service_type": "rest" or "graphql",
    "parameters": {
        "param1": "value1",
        "param2": "value2"
    },
    "reasoning": "Brief explanation of why you chose this action"
}
"""

    def determine_action(self, input_text: str, trace_id: Optional[str] = None) -> Tuple[str, Dict[str, Any], str]:
        """
        Determine the appropriate action based on the input text using OpenAI or Ollama.

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

        # Using only the LLM for action determination
        self.logger.info(f"Using LLM-based determination for input", trace_id=trace_id)
        try:
            if self.use_local_llm:
                # Call Ollama API
                self.logger.debug(f"Calling Ollama API with model {self.ollama_model}", trace_id=trace_id)

                # Prepare the request payload
                payload = {
                    "model": self.ollama_model,
                    "messages": [
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": input_text}
                    ],
                    "stream": False,
                    "temperature": 0.1
                }

                # Make the API call
                response = httpx.post(
                    f"{self.ollama_api_url}/api/chat",
                    json=payload,
                    timeout=60.0  # Longer timeout for LLM processing
                )

                # Check if the request was successful
                if response.status_code == 200:
                    # Parse the response
                    response_data = response.json()
                    response_content = response_data.get("message", {}).get("content", "")
                    self.logger.debug("Received response from Ollama", trace_id=trace_id, extra_data={"response": response_content[:200] + "..." if len(response_content) > 200 else response_content})

                    # Special handling for Phi model which often returns JSON with comments
                    if "//" in response_content or "/*" in response_content:
                        self.logger.info("Detected comments in JSON response, applying special handling for Phi model", trace_id=trace_id)

                        # Extract action and service_type using regex
                        action_match = re.search(r'"action"\s*:\s*"([^"]+)"', response_content)
                        service_match = re.search(r'"service_type"\s*:\s*"([^"]+)"', response_content)
                        reasoning_match = re.search(r'"reasoning"\s*:\s*"([^"]+)"', response_content)

                        if action_match and service_match:
                            action = action_match.group(1)
                            service_type = service_match.group(1)
                            reasoning = reasoning_match.group(1) if reasoning_match else "No reasoning provided"

                            self.logger.info(f"Extracted action: {action}, service: {service_type} using regex", trace_id=trace_id)

                            # Create a valid JSON response
                            response_content = json.dumps({
                                "action": action,
                                "service_type": service_type,
                                "parameters": {},
                                "reasoning": reasoning
                            })
                else:
                    # Log the error and fall back to rule-based determination
                    self.logger.error(f"Error calling Ollama API: {response.status_code} - {response.text}", trace_id=trace_id)
                    return self._fallback_determination(input_text, trace_id)
            else:
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

                    # Clean up the JSON string by removing comments and fixing common issues
                    # Remove JavaScript-style comments
                    json_str = re.sub(r'//.*?\n', '\n', json_str)  # Remove single-line comments
                    json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)  # Remove multi-line comments

                    # Remove trailing commas in objects and arrays
                    json_str = re.sub(r',\s*}', '}', json_str)
                    json_str = re.sub(r',\s*\]', ']', json_str)

                    # Log the cleaned JSON for debugging
                    self.logger.debug(f"Cleaned JSON: {json_str}", trace_id=trace_id)

                    try:
                        result = json.loads(json_str)
                    except json.JSONDecodeError as e:
                        self.logger.error(f"Error parsing cleaned JSON: {e}", trace_id=trace_id, extra_data={"cleaned_json": json_str})

                        # Try a more aggressive approach - extract just the key parts we need
                        action_match = re.search(r'"action"\s*:\s*"([^"]+)"', json_str)
                        service_match = re.search(r'"service_type"\s*:\s*"([^"]+)"', json_str)
                        reasoning_match = re.search(r'"reasoning"\s*:\s*"([^"]+)"', json_str)

                        if action_match and service_match:
                            action = action_match.group(1)
                            service_type = service_match.group(1)
                            reasoning = reasoning_match.group(1) if reasoning_match else "No reasoning provided"

                            self.logger.info(f"Extracted action: {action}, service: {service_type} using regex", trace_id=trace_id)
                            self.logger.info(f"Extracted reasoning: {reasoning}", trace_id=trace_id)

                            # Create a minimal valid result
                            result = {
                                "action": action,
                                "service_type": service_type,
                                "parameters": {},
                                "reasoning": reasoning
                            }
                        else:
                            # If we can't extract the key parts, fall back
                            self.logger.warning(f"Could not extract action and service_type using regex", trace_id=trace_id)
                            return self._fallback_determination(input_text, trace_id)
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
        """Fallback method for determining action when LLM API fails."""
        trace_id = trace_id or str(uuid.uuid4())
        self.logger.warning("Using fallback action determination - defaulting to generate_text", trace_id=trace_id)

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
