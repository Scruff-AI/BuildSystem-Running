"""Claude model client implementation."""

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

class ClaudeChatCompletionClient:
    """Client for Claude's chat completion API."""
    
    def __init__(self, model: str, api_key: str):
        """Initialize client."""
        # Map display model name to API model name
        self.model_map = {
            "Claude 3.5 Sonnet": "claude-3-haiku-20240307"
        }
        self.model = self.model_map.get(model, "claude-3-haiku-20240307")
        self.api_key = api_key
        self.api_url = "https://api.anthropic.com/v1/messages"
        
    async def create(self, messages: List[LLMMessage]) -> CreateResult:
        """Create chat completion."""
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01"
        }
        
        # Convert messages to API format
        api_messages = []
        
        for msg in messages:
            if isinstance(msg, SystemMessage):
                # Prepend system message as user message
                api_messages.insert(0, {"role": "user", "content": msg.content})
            elif isinstance(msg, UserMessage):
                api_messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AssistantMessage):
                api_messages.append({"role": "assistant", "content": msg.content})
                
        data = {
            "model": self.model,
            "messages": api_messages,
            "max_tokens": 4096
        }
            
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.api_url,
                headers=headers,
                json=data,
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()
            
            return CreateResult(
                content=result["content"][0]["text"],
                finish_reason=result.get("stop_reason", "stop"),
                usage=RequestUsage(
                    prompt_tokens=result.get("usage", {}).get("input_tokens", 0),
                    completion_tokens=result.get("usage", {}).get("output_tokens", 0)
                )
            )
