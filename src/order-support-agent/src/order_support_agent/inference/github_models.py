"""GitHub Models provider — zero Azure cost, only needs a ``GITHUB_TOKEN``.

GitHub Models exposes an Azure-AI-Inference-compatible endpoint, so this is a
thin wrapper over :class:`_AzureAIInferenceClient` using an API-key credential.
"""

from __future__ import annotations

from azure.core.credentials import AzureKeyCredential

from order_support_agent.config import Settings

from ._azure_ai_inference import _AzureAIInferenceClient
from .errors import InferenceConfigurationError


class GitHubModelsClient(_AzureAIInferenceClient):
    """Chat client backed by GitHub Models."""

    provider = "github_models"

    def __init__(self, settings: Settings) -> None:
        token = settings.github_token
        if not token:
            raise InferenceConfigurationError(
                "GitHub Models requires a token. Set GITHUB_TOKEN (a fine-grained PAT or the "
                "Actions token with the 'models: read' permission), e.g. "
                "`export GITHUB_TOKEN=$(gh auth token)`."
            )
        super().__init__(
            endpoint=settings.github_models_endpoint,
            credential=AzureKeyCredential(token),
            model=settings.github_models_model,
            timeout=settings.request_timeout_seconds,
        )
