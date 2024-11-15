"""Core model types for BuildSystem."""

from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass

@dataclass
class RequestUsage:
    """Token usage information for a request."""
    prompt_tokens: int
    completion_tokens: int

@dataclass
class ModelCapabilities:
    """Capabilities of a language model."""
    vision: bool = False
    function_calling: bool = False
    json_output: bool = False

@dataclass
class LLMMessage:
    """Base class for all message types."""
    content: Union[str, List[Dict[str, str]]]

@dataclass
class SystemMessage(LLMMessage):
    """System message to set context or behavior."""
    pass

@dataclass
class UserMessage(LLMMessage):
    """Message from a user or on behalf of a user."""
    source: str

@dataclass
class AssistantMessage(LLMMessage):
    """Message from an AI assistant."""
    pass

@dataclass
class CreateResult:
    """Result of a model completion request."""
    content: str
    finish_reason: str
    usage: RequestUsage
    cached: bool
