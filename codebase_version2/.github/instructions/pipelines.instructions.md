---
applyTo: "pipelines/**,.github/workflows/**,jobs/**"
---

# CI/CD and scheduled jobs

The LLMOps discipline here **is** the eval gate. Protect it.

- **The eval gate runs before deploy and blocks on failure.** `run_eval_gate.py` must succeed (exit 0) before any deploy step runs. Never deploy an ungated build.
- **Order:** pull request → run the gate (`pr-eval-gate.yml`) → merge only if green → `deploy.yml` deploys only when gated.
- **Use OIDC / federated credentials — no stored secrets.** Authenticate to Azure with workload-identity federation; do not put endpoints, keys, or connection strings in pipeline YAML. Runtime secrets come from Managed Identity.
- **The nightly job re-runs the gate** (`jobs/nightly_eval/`, `nightly.yml`) to catch drift — model, data, or prompt changes that silently degrade quality between pull requests.
- **Keep pipeline files small and commented.** One clear job per file, comments saying *why* a step exists. Only `.yml` here.
