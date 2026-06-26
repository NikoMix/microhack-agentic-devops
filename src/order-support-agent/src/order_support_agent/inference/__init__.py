"""Modular inference layer.

Public surface: the neutral data types, the :class:`InferenceClient` interface,
the :func:`create_inference_client` factory, and the :class:`FakeInferenceClient`
used in tests. Concrete provider modules are imported on demand by the factory.
"""

from __future__ import annotations

from .base import (
    ChatMessage,
    CompletionResult,
    InferenceClient,
    ResponseFormat,
    Role,
    ToolCall,
    ToolChoice,
    ToolSpec,
    Usage,
)
from .errors import InferenceConfigurationError, InferenceError
from .factory import create_inference_client
from .fake import FakeInferenceClient, RecordedCall

__all__ = [
    "ChatMessage",
    "CompletionResult",
    "FakeInferenceClient",
    "InferenceClient",
    "InferenceConfigurationError",
    "InferenceError",
    "RecordedCall",
    "ResponseFormat",
    "Role",
    "ToolCall",
    "ToolChoice",
    "ToolSpec",
    "Usage",
    "create_inference_client",
]
