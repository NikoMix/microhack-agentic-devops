"""Provider factory — the single switch that selects an inference backend.

``create_inference_client`` maps ``INFERENCE_PROVIDER`` onto a concrete
:class:`InferenceClient`. Switching providers is therefore a configuration
change with **no code change** anywhere else in the codebase. Provider modules
are imported lazily so a single deployment never needs every provider's SDK
credentials present at import time.
"""

from __future__ import annotations

from order_support_agent.config import InferenceProvider, Settings, get_settings

from .base import InferenceClient
from .errors import InferenceConfigurationError


def create_inference_client(settings: Settings | None = None) -> InferenceClient:
    """Construct the :class:`InferenceClient` for the configured provider.

    Args:
        settings: Optional settings override. Defaults to process settings.

    Returns:
        A ready-to-use, provider-specific inference client.

    Raises:
        InferenceConfigurationError: If the selected provider is misconfigured.
    """
    settings = settings or get_settings()
    match settings.inference_provider:
        case InferenceProvider.GITHUB_MODELS:
            from .github_models import GitHubModelsClient

            return GitHubModelsClient(settings)
        case InferenceProvider.AZURE_OPENAI:
            from .azure_openai import AzureOpenAIClient

            return AzureOpenAIClient(settings)
        case InferenceProvider.FOUNDRY:
            from .foundry import FoundryClient

            return FoundryClient(settings)
    raise InferenceConfigurationError(  # pragma: no cover - exhaustive match above
        f"Unsupported inference provider: {settings.inference_provider!r}"
    )
