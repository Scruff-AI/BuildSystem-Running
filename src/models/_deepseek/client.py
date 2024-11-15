"""DeepSeek Coder client implementation."""

import os
from typing import List, Optional
import httpx
from ..core.models import (
    LLMMessage,
    CreateResult,
    RequestUsage,
    ModelCapabilities,
    SystemMessage,
    UserMessage,
    AssistantMessage
)

class DeepSeekChatCompletionClient:
    """Client for DeepSeek Coder API."""
    
    def __init__(self, model: str, api_key: Optional[str] = None):
        """Initialize client.
        
        Args:
            model: Model identifier
            api_key: DeepSeek API key (defaults to env var)
        """
        self.model = model
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("DeepSeek API key not found")
            
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        
    @property
    def capabilities(self) -> ModelCapabilities:
        """Get model capabilities."""
        return ModelCapabilities(
            vision=False,
            function_calling=True,
            json_output=True
        )
        
    async def create(self, messages: List[LLMMessage]) -> CreateResult:
        """Create a chat completion.
        
        Args:
            messages: List of messages in the conversation
            
        Returns:
            Completion result
        """
        # Convert messages to DeepSeek format
        deepseek_messages = []
        for msg in messages:
            if isinstance(msg, SystemMessage):
                deepseek_messages.append({
                    "role": "system",
                    "content": msg.content
                })
            elif isinstance(msg, UserMessage):
                deepseek_messages.append({
                    "role": "user", 
                    "content": msg.content
                })
            elif isinstance(msg, AssistantMessage):
                deepseek_messages.append({
                    "role": "assistant",
                    "content": msg.content
                })
        
        # Make API request
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": deepseek_messages
                }
            )
            response.raise_for_status()
            data = response.json()
        
        # Convert response
        return CreateResult(
            content=data["choices"][0]["message"]["content"],
            finish_reason=data["choices"][0]["finish_reason"],
            usage=RequestUsage(
                prompt_tokens=data["usage"]["prompt_tokens"],
                completion_tokens=data["usage"]["completion_tokens"]
            ),
            cached=False
        )
