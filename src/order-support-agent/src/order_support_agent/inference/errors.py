"""Inference-layer error types."""

from __future__ import annotations


class InferenceError(RuntimeError):
    """Base class for inference-layer failures."""


class InferenceConfigurationError(InferenceError):
    """Raised when a provider is selected but its configuration is incomplete."""
