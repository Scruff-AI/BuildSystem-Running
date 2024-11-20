"""DeepSeek model client implementation."""

import os
from typing import List, Dict, Any
import httpx
from ...core.models import (
    LLMMessage,
    CreateResult,
    RequestUsage,
    SystemMessage,
    UserMessage,
    AssistantMessage
)

class DeepSeekChatCompletionClient:
    """Client for DeepSeek's chat completion API."""
    
    def __init__(self, model: str, api_key: str):
        """Initialize client."""
        self.model = model
        self.api_key = api_key
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        
    async def create(self, messages: List[LLMMessage]) -> CreateResult:
        """Create chat completion."""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
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
            "max_tokens": 4096,
            "temperature": 0.7,
            "stream": False
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.api_url,
                    headers=headers,
                    json=data,
                    timeout=30.0
                )
                response.raise_for_status()
                result = response.json()
                
                # Validate response format
                if "choices" not in result:
                    raise ValueError(f"Unexpected response format from DeepSeek: {result}")
                    
                if not result["choices"] or "message" not in result["choices"][0]:
                    raise ValueError(f"No valid completion in response: {result}")
                    
                # Extract usage information, defaulting to 0 if not provided
                usage = result.get("usage", {})
                prompt_tokens = usage.get("prompt_tokens", 0)
                completion_tokens = usage.get("completion_tokens", 0)
                
                return CreateResult(
                    content=result["choices"][0]["message"]["content"],
                    finish_reason=result["choices"][0].get("finish_reason", "stop"),
                    usage=RequestUsage(
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens
                    )
                )
                
            except httpx.HTTPError as e:
                raise ValueError(f"DeepSeek API request failed: {str(e)}")
            except KeyError as e:
                raise ValueError(f"Invalid response structure from DeepSeek: {str(e)}")
            except Exception as e:
                raise ValueError(f"Error processing DeepSeek response: {str(e)}")
