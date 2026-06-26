# Challenge 02 — Coach notes

The teaching goal is the **secretless registration flow**, not just "deploy a VM". Keep attendees focused
on *where the trust comes from* at each hop: managed identity → Key Vault → JIT token → ephemeral runner,
and separately, job-side GitHub OIDC → Azure.

## Timing (45 min)

| Min | Segment | Notes |
| --- | --- | --- |
| 0–8 | Why self-hosted + design | Walk the Mermaid diagram; contrast with GitHub-hosted. |
| 8–15 | Read cloud-init + Bicep | Show there is no token in Git; trace IMDS → Key Vault → `config.sh`. |
| 15–20 | Mint token → Key Vault | Emphasize short TTL and ephemeral re-mint implications. |
| 20–30 | what-if + deploy | Discuss Spot/B-series while it provisions (~4–6 min). |
| 30–40 | Verify online + run a job | Prove `azure/login` over OIDC with no runner secret. |
| 40–45 | Cost + ARC + Q&A | When VMSS vs ARC; scale-to-zero. |

> Provisioning the VMSS + NAT can take several minutes. Start the deploy, then fill the time with the cost
> and ARC discussion so nobody sits watching a spinner.

## Key teaching points

- **Two independent trust chains.** (1) *Host bootstrap*: the VM's **managed identity** proves who it is to
  Azure via IMDS, reads the **registration token** from Key Vault (RBAC: Key Vault Secrets User), and
  registers the runner. (2) *Job auth*: a workflow uses **GitHub OIDC** with `azure/login` to get an Azure
  token. Neither stores a long-lived secret. Don't let people conflate them.
- **Ephemeral runners are a security control.** `--ephemeral` means one job per runner, then de-register —
  no state leaks between jobs, and a compromised job can't persist on the host. The VMSS replaces the
  instance.
- **Cost engineering.** Spot (Deallocate eviction) + B-series burstable + small instance count is the
  cheapest sensible profile for bursty lab CI. Name the trade-offs: Spot can be evicted; B-series throttles
  once CPU credits are exhausted.
- **Closed by default.** The subnet egresses through a **NAT Gateway**; the NSG denies inbound. SSH is only
  reachable if a coach explicitly sets `adminSshPublicKey` + `allowSshFromCidr` for break-glass.
- **SHA-pinned, checksum-verified runner.** The runner version is pinned and its tarball SHA-256 is
  verified at boot — supply-chain hygiene mirrors the SHA-pinned Actions in the workflows.

## Common pitfalls + fixes

| Symptom | Cause | Fix |
| --- | --- | --- |
| Runners never appear in GitHub | Registration token expired (~1h) or wrong scope | Re-mint with `gh api ... registration-token`; re-set the Key Vault secret; reimage instances (`az vmss reimage`). |
| `FATAL: could not obtain managed-identity token` in bootstrap log | Managed identity not attached / IMDS blocked | Confirm `managedIdentityResourceId` was passed; check the VMSS identity block; ensure `client_id` matches `managedIdentityClientId`. |
| `FATAL: registration token secret is empty/missing` | Secret not written or wrong vault/name | Verify `az keyvault secret show --vault-name <kv> --name gh-runner-registration-token`; check the MI has **Key Vault Secrets User**. |
| `403` reading Key Vault | RBAC propagation lag or missing role | Wait 1–2 min after Challenge 00; re-check the role assignment on the vault. |
| Runner checksum mismatch | `runnerVersion`/`runnerSha256` drift | Bump both together; the SHA is for `actions-runner-linux-x64-<version>.tar.gz`. |
| Job stuck "Waiting for a runner" | Labels don't match `runs-on` | Match labels exactly (`self-hosted, linux, ccmh`); confirm runners are **Idle**, not **Offline**. |
| Spot capacity error on deploy | Region lacks Spot B-series | Set `useSpot=false` temporarily, or change region in the param file. |

## Discussion questions

1. Where would a long-lived secret normally live in a self-hosted runner setup, and how did we remove it?
2. Why prefer **ephemeral** runners over persistent ones for CI? When are persistent runners acceptable?
3. The host uses a **managed identity** but the job uses **GitHub OIDC** — why two mechanisms instead of
   one?
4. When does **ARC on AKS** beat a **VMSS**? Consider scale-to-zero, pod isolation, and operational cost.
5. What's your token-renewal strategy for a fleet that scales up overnight?

## What good looks like

- No registration token anywhere in Git, Bicep, or cloud-init — only a Key Vault secret read via managed
  identity.
- `what-if` is a clean Create plan; `az bicep lint` is silent on the module.
- Runners register **ephemeral**, show Online with the right labels, and de-register after each job.
- A `runs-on: [self-hosted, ccmh]` job logs in to Azure via OIDC with **zero** secrets on the host.
- Attendees can draw both trust chains from memory and state the cost levers (Spot, B-series, ephemeral,
  instance count).

## Links

- Student lab: [`README.md`](README.md)
- Runner module + ARC notes: [`../../../infra/README.md`](../../../infra/README.md)
- Cloud-init bootstrap: [`../../../infra/runners/cloud-init.runner.yaml`](../../../infra/runners/cloud-init.runner.yaml)
- VMSS module: [`../../../infra/modules/runners-vmss.bicep`](../../../infra/modules/runners-vmss.bicep)
