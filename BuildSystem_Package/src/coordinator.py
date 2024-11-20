"""Coordinator for managing LLM interactions and web search integration."""

import os
import asyncio
import tiktoken
from typing import List, Dict, Any
from BuildSystem_Package.utils.logging_config import debug_logger, model_logger
from .web_search import search, parallel_search
from .core.models import (
    SystemMessage,
    UserMessage,
    AssistantMessage,
    RequestUsage,
    system_context
)

class Coordinator:
    """Manages LLM interactions and web search integration."""
    
    def __init__(self):
        """Initialize the coordinator."""
        self.model_roles = system_context["model_roles"]
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        self.token_limits = {
            "claude": 200000,
            "gpt4": 128000,
            "deepseek": 32000,
            "liquid": 32000
        }
        
    def count_tokens(self, text: str) -> int:
        """Count tokens in a text string."""
        return len(self.tokenizer.encode(text))
        
    def check_token_limit(self, text: str, model: str) -> bool:
        """Check if text exceeds token limit for specified model."""
        token_count = self.count_tokens(text)
        limit = self.token_limits.get(model, 32000)  # Default to 32k if model not found
        return token_count <= limit
        
    async def perform_web_search(self, query: str, max_results: int = 5) -> List[Dict]:
        """Perform web search with automatic failover."""
        try:
            debug_logger.info(f"Initiating web search for query: {query}")
            results = await search(query, max_results)
            return results
        except Exception as e:
            debug_logger.error(f"Web search failed: {str(e)}")
            return []
            
    async def process_task(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process a task using appropriate models and web search."""
        try:
            debug_logger.info(f"Processing task: {task}")
            
            # Check if web search is needed
            if "search" in task.lower() or "find" in task.lower() or "latest" in task.lower():
                search_results = await self.perform_web_search(task)
                if search_results:
                    context = context or {}
                    context["search_results"] = search_results
            
            # Select appropriate model based on token count and task type
            task_tokens = self.count_tokens(task)
            selected_model = self.select_model(task_tokens, task)
            
            # Create messages for the selected model
            messages = self.create_messages(task, context)
            
            # Process with selected model
            model_logger.info(f"Processing with model: {selected_model}")
            response = await self.process_with_model(selected_model, messages)
            
            return {
                "result": response,
                "model_used": selected_model,
                "token_count": task_tokens
            }
            
        except Exception as e:
            error_msg = f"Task processing failed: {str(e)}"
            debug_logger.error(error_msg)
            raise ValueError(error_msg)
            
    def select_model(self, token_count: int, task: str) -> str:
        """Select appropriate model based on token count and task type."""
        if "code" in task.lower():
            return "deepseek" if token_count <= self.token_limits["deepseek"] else "claude"
        elif token_count > self.token_limits["gpt4"]:
            return "claude"
        else:
            return "gpt4"
            
    def create_messages(self, task: str, context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Create messages for model processing."""
        messages = [
            SystemMessage(content=system_context["system_description"]),
            UserMessage(content=task)
        ]
        
        if context and "search_results" in context:
            search_content = "Search Results:\n" + "\n".join(
                f"- {result['title']}: {result['content']}"
                for result in context["search_results"]
            )
            messages.append(AssistantMessage(content=search_content))
            
        return messages
        
    async def process_with_model(self, model: str, messages: List[Dict[str, Any]]) -> str:
        """Process messages with selected model."""
        try:
            # Implement actual model processing here
            # This is a placeholder - actual implementation would use the appropriate API
            model_logger.info(f"Processing with {model}")
            return f"Processed with {model}"
            
        except Exception as e:
            error_msg = f"Model processing failed: {str(e)}"
            model_logger.error(error_msg)
            raise ValueError(error_msg)

# Initialize coordinator
coordinator = Coordinator()
