"""Core model types and interfaces."""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any

@dataclass
class RequestUsage:
    """Token usage information."""
    prompt_tokens: int
    completion_tokens: int

@dataclass
class CreateResult:
    """Result from model creation."""
    content: str
    finish_reason: str
    usage: RequestUsage
    cached: bool = False

@dataclass
class ModelCapabilities:
    """Model capabilities."""
    vision: bool = False
    function_calling: bool = False
    json_output: bool = True

@dataclass
class LLMMessage:
    """Base class for all message types."""
    content: str
    system_context: Optional[Dict[str, Any]] = None

class SystemMessage(LLMMessage):
    """System message."""
    pass

class UserMessage(LLMMessage):
    """User message with optional source."""
    def __init__(self, content: str, source: str = "user"):
        super().__init__(content)
        self.source = source

class AssistantMessage(LLMMessage):
    """Assistant message with optional metadata."""
    def __init__(self, content: str, metadata: Optional[Dict[str, Any]] = None):
        super().__init__(content)
        self.metadata = metadata or {}

# Define a constant for the duplicated string
CODING_TASK_DESCRIPTION = "Generates solutions for coding tasks."

# Example system context
system_context = {
    "system_name": "BuildSystem_Package",
    "system_description": "An AI-driven code generation and task solving platform built using FastAPI, integrating multiple AI models for collaborative task solving.",
    "model_roles": {
        "coordinator": "Handles task analysis, search result summarization, and solution review.",
        "coders": {
            "deepseek": CODING_TASK_DESCRIPTION,
            "claude": CODING_TASK_DESCRIPTION,
            "liquid": CODING_TASK_DESCRIPTION,
            "hermes": CODING_TASK_DESCRIPTION
        }
    },
    "web_search": "Performs web searches using the Tavily API if the task requires the latest information."
}

# Update system context for all messages
def update_system_context(messages: List[LLMMessage], context: Dict[str, Any]):
    for message in messages:
        message.system_context = context

# Example usage
messages = [
    SystemMessage(content="System message"),
    UserMessage(content="User message"),
    AssistantMessage(content="Assistant message")
]

update_system_context(messages, system_context)
