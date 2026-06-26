# Challenge 01 — reference solution

The reference implementation for this challenge is the **real, maintained code in the repository** —
there is nothing to copy out of a `solution/` folder. Use this as the answer key if you get stuck at a
checkpoint.

| You were asked to… | Reference answer |
| --- | --- |
| Understand the "before" | [`src/legacy-orders-api/`](../../../../src/legacy-orders-api/) + [`azure-pipelines.yml`](../../../../src/legacy-orders-api/azure-pipelines.yml) |
| Migrate the repository | [`migration/scripts/migrate-repo.sh`](../../../../migration/scripts/migrate-repo.sh) · [`.ps1`](../../../../migration/scripts/migrate-repo.ps1) |
| Translate the pipeline | [`migration/pipelines-to-actions.md`](../../../../migration/pipelines-to-actions.md) → [`.github/workflows/orders-api-ci.yml`](../../../../.github/workflows/orders-api-ci.yml) |
| Migrate the boards | [`migration/boards-to-issues.md`](../../../../migration/boards-to-issues.md) + [`scripts/boards-to-issues.sh`](../../../../migration/scripts/boards-to-issues.sh) |
| Work without a source org | [`migration/sample-export/`](../../../../migration/sample-export/) + every `--dry-run` flag |

The full end-to-end walkthrough is the runbook at
[`migration/README.md`](../../../../migration/README.md).
