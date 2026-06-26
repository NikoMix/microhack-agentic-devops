"""Azure AI Foundry provider — keyless via Entra ID (``DefaultAzureCredential``).

Targets a Foundry project's model-inference endpoint through the
``azure-ai-inference`` SDK. No keys are used or stored; the managed identity (or
developer identity) is granted the relevant data-plane role on the resource.
"""

from __future__ import annotations

from azure.identity.aio import DefaultAzureCredential

from order_support_agent.config import Settings

from ._azure_ai_inference import COGNITIVE_SERVICES_SCOPE, _AzureAIInferenceClient
from .errors import InferenceConfigurationError


class FoundryClient(_AzureAIInferenceClient):
    """Chat client backed by Azure AI Foundry, authenticated with Entra ID."""

    provider = "foundry"

    def __init__(self, settings: Settings) -> None:
        endpoint = settings.azure_ai_foundry_project_endpoint
        if not endpoint:
            raise InferenceConfigurationError(
                "Foundry provider requires AZURE_AI_FOUNDRY_PROJECT_ENDPOINT to be set."
            )
        self._credential = DefaultAzureCredential()
        super().__init__(
            endpoint=endpoint,
            credential=self._credential,
            model=settings.azure_ai_foundry_chat_deployment,
            timeout=settings.request_timeout_seconds,
            credential_scopes=(COGNITIVE_SERVICES_SCOPE,),
        )

    async def aclose(self) -> None:
        """Close the client and release the Entra credential."""
        await super().aclose()
        await self._credential.close()
