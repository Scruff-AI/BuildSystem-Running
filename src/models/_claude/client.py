"""Claude client implementation."""

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

class ClaudeChatCompletionClient:
    """Client for Claude API."""
    
    def __init__(self, model: str, api_key: Optional[str] = None):
        """Initialize client.
        
        Args:
            model: Model identifier
            api_key: Anthropic API key (defaults to env var)
        """
        self.model = model
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key not found")
            
        self.api_url = "https://api.anthropic.com/v1/messages"
        
    @property
    def capabilities(self) -> ModelCapabilities:
        """Get model capabilities."""
        return ModelCapabilities(
            vision=True,
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
        # Convert messages to Claude format
        claude_messages = []
        system_prompt = ""
        
        for msg in messages:
            if isinstance(msg, SystemMessage):
                system_prompt = msg.content
            elif isinstance(msg, UserMessage):
                claude_messages.append({
                    "role": "user",
                    "content": msg.content
                })
            elif isinstance(msg, AssistantMessage):
                claude_messages.append({
                    "role": "assistant",
                    "content": msg.content
                })
        
        # Make API request
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.api_url,
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": claude_messages,
                    "system": system_prompt
                }
            )
            response.raise_for_status()
            data = response.json()
        
        # Convert response
        return CreateResult(
            content=data["content"][0]["text"],
            finish_reason=data["stop_reason"],
            usage=RequestUsage(
                prompt_tokens=data["usage"]["input_tokens"],
                completion_tokens=data["usage"]["output_tokens"]
            ),
            cached=False
        )
