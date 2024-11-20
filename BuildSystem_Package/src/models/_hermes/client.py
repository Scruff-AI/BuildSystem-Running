"""Hermes model client implementation via OpenRouter."""

import os
from typing import List, Dict, Any
import httpx
from utils.logging_config import model_logger
from ...core.models import (
    LLMMessage,
    CreateResult,
    RequestUsage,
    SystemMessage,
    UserMessage,
    AssistantMessage
)

class OpenRouterError(Exception):
    """Custom exception for OpenRouter API errors."""
    pass

class ModelValidationError(Exception):
    """Custom exception for model validation errors."""
    pass

class HermesChatCompletionClient:
    """Client for Hermes chat completion API via OpenRouter."""
    
    def __init__(self, model: str, api_key: str):
        """Initialize client."""
        self.model = model  # Keep original model name from .env
        self.api_key = api_key
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        
        # Get backup models from .env
        self.backup_models = [
            os.getenv("HERMES_BACKUP_1", "openrouter/google/gemini-flash-1.5"),
            os.getenv("HERMES_BACKUP_2", "openrouter/meta-llama/llama-2-70b-instruct")
        ]
        self.logger = model_logger.getChild("hermes")
        self.logger.info(f"Initialized with primary model: {self.model}")
        self.logger.info(f"Backup models: {', '.join(self.backup_models)}")
        
    async def create(self, messages: List[LLMMessage]) -> CreateResult:
        """Create chat completion."""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "http://localhost:3000",  # Required by OpenRouter
            "X-Title": "BuildSystem"  # Required by OpenRouter
        }
        
        # Convert messages to API format
        api_messages = []
        for msg in messages:
            if isinstance(msg, SystemMessage):
                api_messages.append({"role": "system", "content": msg.content})
            elif isinstance(msg, UserMessage):
                api_messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AssistantMessage):
                api_messages.append({"role": "assistant", "content": msg.content})
                
        data = {
            "model": self.model,
            "messages": api_messages,
            "temperature": 0.7,
            "max_tokens": 2048
        }
        
        # Try primary model first, then backup models
        models_to_try = [self.model] + self.backup_models
        last_error = None
        
        for i, model in enumerate(models_to_try):
            try:
                # Remove openrouter/ prefix if present in .env
                model_name = model.replace("openrouter/", "")
                data["model"] = model_name
                extra = {"model": model_name}
                
                if i == 0:
                    self.logger.info("Attempting request with primary model", extra=extra)
                else:
                    self.logger.info(f"Primary model failed, trying backup model {i}", extra=extra)
                
                async with httpx.AsyncClient() as client:
                    try:
                        response = await client.post(
                            self.api_url,
                            headers=headers,
                            json=data,
                            timeout=30.0
                        )
                        response.raise_for_status()
                    except httpx.HTTPError as e:
                        raise OpenRouterError(f"HTTP error: {str(e)}")
                    except httpx.TimeoutException:
                        raise OpenRouterError("Request timed out")
                        
                    result = response.json()
                    self.logger.debug(f"Raw response: {result}", extra=extra)
                    
                    # Check for error response
                    if "error" in result:
                        error = result["error"]
                        raise OpenRouterError(f"API error: {error}")
                    
                    # Handle missing fields gracefully
                    if "choices" not in result or not result["choices"]:
                        raise OpenRouterError("Response missing choices")
                        
                    choice = result["choices"][0]
                    if "message" not in choice:
                        raise OpenRouterError("Response missing message")
                        
                    usage = result.get("usage", {})
                    
                    self.logger.info(f"Request successful with model {model_name}", extra=extra)
                    return CreateResult(
                        content=choice["message"].get("content", ""),
                        finish_reason=choice.get("finish_reason", "stop"),
                        usage=RequestUsage(
                            prompt_tokens=usage.get("prompt_tokens", 0),
                            completion_tokens=usage.get("completion_tokens", 0)
                        )
                    )
                    
            except (OpenRouterError, httpx.HTTPError, httpx.TimeoutException) as e:
                error_msg = f"Model {model_name} failed: {str(e)}"
                if i < len(models_to_try) - 1:
                    self.logger.warning(f"{error_msg}, will try backup model", extra={"model": model_name})
                else:
                    self.logger.error(f"{error_msg}, no more backup models to try", extra={"model": model_name})
                last_error = e
                continue
                
        # If we get here, all models failed
        raise last_error
