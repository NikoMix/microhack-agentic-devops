# Microsoft Defender for Cloud — enablement notes

Defender for Cloud is the lab's **cloud security posture management (CSPM)** and **workload protection** layer.
It scores the lab subscription against the Microsoft Cloud Security Benchmark, raises hardening
recommendations, and — relevant to this MicroHack — can **ingest GitHub Advanced Security findings** so code,
secret, and dependency alerts surface next to runtime alerts in one place (DevOps security).

> No secrets are created or committed by anything here. Every command authenticates with your existing
> `az login` (Entra ID); the GitHub connector uses an Azure-managed app, not a stored credential.

## Lab scope and cost discipline

Enable the **free CSPM** tier broadly (it is free and gives you the secure score + recommendations), and turn on
the **paid workload plans only for what the lab actually runs** — Containers and Key Vault — to keep cost low.
Disable them again at teardown.

| Plan | Lab use | Tier |
| --- | --- | --- |
| Foundational CSPM | Secure score, recommendations, asset inventory | **Free** |
| Defender CSPM | Attack-path analysis, agentless scanning | Paid (optional in lab) |
| Defender for Containers | ACR image scan + ACA runtime posture | Paid — **on** for the lab |
| Defender for Key Vault | Anomalous secret-access detection | Paid — **on** for the lab |
| DevOps security | Ingest GitHub Code Security / Secret Protection results | Free connector |

## 1. Register and turn on CSPM (free)

```bash
az login
az account set --subscription "<sub-id>"

# Defender for Cloud lives behind the Security resource provider
az provider register --namespace Microsoft.Security

# Foundational CSPM (free) is on by default; make it explicit
az security pricing create --name CloudPosture --tier Free
```

## 2. Turn on the workload plans the lab uses

```bash
# Container posture + image scanning (ACR/ACA)
az security pricing create --name Containers --tier Standard

# Key Vault threat detection
az security pricing create --name KeyVaults --tier Standard

# Confirm what is enabled
az security pricing list --query "value[].{plan:name, tier:pricingTier}" -o table
```

> Defender for Containers can scan images **in ACR** and surface vulnerabilities right next to the **SBOM** you
> generated in [`artifact-signing.md`](artifact-signing.md) — the same image, two independent lenses.

## 3. Connect GitHub (DevOps security)

The DevOps security connector pulls **CodeQL**, **Dependabot**, and **secret-scanning** results into Defender so
posture is visible end to end — code to cloud.

- Portal: **Defender for Cloud → Environment settings → Add environment → GitHub**, then authorize the Microsoft
  Security DevOps app for the `NikoMix` org/repo and pick the repositories to onboard.
- The connector is **read-only** over security results; it does not need write access to your code and stores no
  long-lived secret in the repo.

Once connected, GitHub findings appear under **Defender for Cloud → Recommendations → DevOps** and feed the
secure score.

## 4. Read the posture

```bash
# Current secure score for the subscription
az security secure-score-controls list \
  --query "value[].{control:displayName, healthy:healthyResourceCount, unhealthy:unhealthyResourceCount}" \
  -o table

# Active recommendations (assessments)
az security assessment list \
  --query "value[].{name:displayName, status:status.code}" -o table 2>/dev/null | head
```

## 5. Wire alerts to Log Analytics (optional, ties into Challenge 02/05)

Point Defender's continuous export at the lab Log Analytics workspace (`log-ccmh-lab`) so alerts and
recommendations land alongside app telemetry:

- **Environment settings → continuous export → Log Analytics workspace**, select `log-ccmh-lab`, export
  *Security recommendations* and *Security alerts*.

## 6. Teardown

Disable the paid plans so nothing accrues after the lab; the `az group delete` in
[`docs/trainer/teardown.md`](../docs/trainer/teardown.md) removes the resources, but plan pricing is
subscription-scoped and must be reset explicitly:

```bash
az security pricing create --name Containers --tier Free
az security pricing create --name KeyVaults --tier Free
```

## What good looks like

CSPM is on, the two workload plans the lab uses are enabled, GitHub security results are flowing into Defender,
and an attendee can point at the **same vulnerability** in both the GitHub Code Security alerts and the Defender
recommendation list — proving the "code to cloud" story end to end.
