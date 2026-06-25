# Prerequisites & pre-flight

Read this before the day. It covers attendee accounts, Azure subscriptions, quotas, cost guardrails, and the
trainer's pre-flight. The goal: **zero setup time lost on the day**.

## Attendee prerequisites

| Requirement | Detail |
| --- | --- |
| GitHub account | With **GitHub Copilot** enabled (Business/Enterprise recommended for agents + Code Security demos) |
| Azure subscription | **Owner** on a subscription or resource group (Contributor + User Access Administrator also works) |
| Region access | Ability to deploy in **Sweden Central** (best Azure AI Foundry model availability), or `West Europe` / `East US 2` |
| Browser | Chrome/Edge/Firefox — everything runs in **GitHub Codespaces** |
| (Optional) Local | VS Code + Docker Desktop if running the dev container locally |
| (Challenge 01) | Access to a source **Azure DevOps** org, *or* use the provided sample export under `migration/` |

Attendees do **not** need to pre-install anything — the dev container provisions .NET 10, Python 3.12, Azure
CLI, Bicep, `gh`, Node, `uv`, and `cosign` automatically.

## Trainer pre-flight (do this 1 day before)

```bash
# 1) Confirm tooling resolves (inside the dev container / Codespace)
dotnet --version && python --version && az version -o table && gh --version && bicep --version

# 2) Confirm Azure context + quota in the target region
az account show -o table
az vm list-usage -l swedencentral -o table          # capacity for runners
az provider show -n Microsoft.App --query registrationState -o tsv   # Container Apps
az cognitiveservices account list-skus --query "[?kind=='AIServices']" -o table 2>/dev/null || true

# 3) Confirm model availability for the chosen inference provider
#    (GitHub Models needs only a GitHub token; Azure OpenAI/Foundry need a deployment)
```

### Required Azure resource providers

Register these once per subscription (the bootstrap script does this for you):

`Microsoft.App`, `Microsoft.ContainerRegistry`, `Microsoft.KeyVault`, `Microsoft.OperationalInsights`,
`Microsoft.Insights`, `Microsoft.CognitiveServices`, `Microsoft.ManagedIdentity`, `Microsoft.Compute`,
`Microsoft.Network`, `Microsoft.ContainerService` (only if using ARC on AKS for runners).

### GitHub prerequisites for migration (Challenge 01)

- A **personal access token** (classic) or GitHub App with `repo`, `workflow`, and (for `gh gei`) the
  appropriate **Enterprise Importer** scopes. The challenge lists exact scopes.
- For Boards → Issues, the `project` scope.

## Inference options & when to use them

| Provider | Setup cost | Use during | Notes |
| --- | --- | --- | --- |
| **GitHub Models** | None (just a GitHub token) | Challenges 04–05 dev/iteration | `models.github.ai/inference`, model `openai/gpt-4o-mini`. Zero Azure spend. |
| **Azure OpenAI** | A deployment in your sub | Challenge 05 deploy | Keyless via Entra ID; lowest-latency in-region |
| **Azure AI Foundry** | A Foundry project + deployment | Challenge 05 deploy / agent hosting | Showcases Foundry Agent Service + tracing |

Switch providers by changing **one env var** (`INFERENCE_PROVIDER`) — that's the whole point of the modular
inference layer. **No image generation** is used anywhere.

## Cost guardrails 💷

- All Azure resources use **free/low SKUs** (Container Apps consumption, Key Vault standard, B-series/spot VMSS
  for runners, Log Analytics pay-as-you-go with a low daily cap).
- Resource groups are **ephemeral and per-attendee** (`rg-ccmh-lab` by default) and are deleted at teardown.
- Expect **< a few USD per attendee** for a single day if teardown is run. See [`teardown.md`](teardown.md).
- Set a **budget alert** on the subscription before the event (the bootstrap script offers to create one).

## Accessibility & logistics

- Share the deck + repo link in a channel attendees can copy from (many CLI snippets).
- Provide the [`agenda.md`](agenda.md) checkpoints up front so attendees can self-pace.
- Captioning: enable live captions in your meeting tool; all demos should be narrated.
