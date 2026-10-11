<!-- Contoso Commerce MicroHack — Pull Request -->
## What & why
<!-- Summary of the change and which challenge / reference architecture it serves. -->

## Workstream

- [ ] Foundation/trainer  - [ ] Infra (B)  - [ ] Legacy+Migration (C)  - [ ] Secure SDLC (D)  - [ ] Agent+MCP (E)  - [ ] Agentic pipeline (F)

Closes # <!-- issue -->

## Checklist

- [ ] Only edits paths owned by this workstream (see `plan.md` ownership table)
- [ ] Builds/lints/tests pass locally (`dotnet`/`ruff`+`mypy`+`pytest`/`az bicep lint`/`actionlint`)
- [ ] No secrets committed; uses OIDC / `DefaultAzureCredential` / Key Vault
- [ ] Dependencies are latest stable with **0 known vulnerabilities**
- [ ] AI calls go through the modular-inference factory (no direct single-provider calls)
- [ ] Student `README.md` + trainer `coach-notes.md` added/updated for affected challenge(s)
- [ ] Azure resources are cost-optimized and covered by the teardown script
