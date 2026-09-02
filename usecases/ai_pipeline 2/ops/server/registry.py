"""Versioned prompt registry (JSON files) + model registry (reads platform YAML).

Prompt storage layout (shared with the pipeline's prompts_gate so an activated
version is what the pipeline runs — no redeploy):
    <REGISTRY_DIR>/<program>/<name>/v<N>.json   one file per version
    <REGISTRY_DIR>/<program>/<name>/active.json {"active_version": N}
"""
import json
from datetime import datetime, timezone

from . import config


def _now():
    return datetime.now(timezone.utc).isoformat()


def _pdir(program, name):
    return config.REGISTRY_DIR / program / name


def list_prompts():
    out = []
    if not config.REGISTRY_DIR.exists():
        return out
    for prog in sorted(p for p in config.REGISTRY_DIR.iterdir() if p.is_dir()):
        for nd in sorted(p for p in prog.iterdir() if p.is_dir()):
            versions = sorted(int(f.stem[1:]) for f in nd.glob("v*.json") if f.stem[1:].isdigit())
            out.append({"program": prog.name, "name": nd.name,
                        "versions": versions, "active_version": _active(prog.name, nd.name)})
    return out


def _active(program, name):
    f = _pdir(program, name) / "active.json"
    if f.exists():
        try:
            return json.loads(f.read_text(encoding="utf-8")).get("active_version")
        except Exception:
            return None
    return None


def get_prompt(program, name):
    nd = _pdir(program, name)
    if not nd.exists():
        return None
    versions = []
    for f in sorted(nd.glob("v*.json"), key=lambda p: int(p.stem[1:]) if p.stem[1:].isdigit() else 0):
        try:
            versions.append(json.loads(f.read_text(encoding="utf-8")))
        except Exception:
            continue
    return {"program": program, "name": name, "active_version": _active(program, name), "versions": versions}


def get_version(program, name, version):
    f = _pdir(program, name) / f"v{version}.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else None


def save_version(program, name, template, model_capability="reason", note=""):
    nd = _pdir(program, name)
    nd.mkdir(parents=True, exist_ok=True)
    existing = [int(f.stem[1:]) for f in nd.glob("v*.json") if f.stem[1:].isdigit()]
    version = (max(existing) + 1) if existing else 1
    spec = {"program": program, "name": name, "version": version, "template": template,
            "model_capability": model_capability, "note": note, "created_at": _now()}
    (nd / f"v{version}.json").write_text(json.dumps(spec, indent=2), encoding="utf-8")
    if not existing:  # first version becomes active automatically
        activate(program, name, version)
    return spec


def activate(program, name, version):
    nd = _pdir(program, name)
    if not (nd / f"v{version}.json").exists():
        raise FileNotFoundError(f"{program}/{name} v{version} does not exist")
    (nd / "active.json").write_text(json.dumps({"active_version": version}), encoding="utf-8")
    return {"program": program, "name": name, "active_version": version}


# ── model registry (from platform config) ──────────────────────────────────
def _platform_services():
    return config.PKG_DIR.parent.parent / "platform" / "services"


def list_models(environment="dev"):
    """Read model aliases + pricing from the platform YAML. Falls back to a
    small built-in list if pyyaml or the files aren't available (mock)."""
    svc = _platform_services()
    models_yaml = svc / "03-model-management" / "config" / "models.yaml"
    pricing_yaml = svc / "03-model-management" / "config" / "pricing.yaml"
    try:
        import yaml
        models = yaml.safe_load(models_yaml.read_text(encoding="utf-8")) or {}
        pricing = (yaml.safe_load(pricing_yaml.read_text(encoding="utf-8")) or {}).get("deployments", {})
        env = (models.get("environments", {}).get(environment, {}) or {}).get("models", {})
        out = []
        for alias, spec in env.items():
            dep = spec.get("deployment")
            rate = pricing.get(dep or "", {})
            out.append({"alias": alias, "provider": spec.get("provider"), "deployment": dep,
                        "kind": spec.get("kind"),
                        "input_per_1k": rate.get("input_per_1k"), "output_per_1k": rate.get("output_per_1k")})
        return out
    except Exception:
        return _FALLBACK_MODELS


# Richer default catalogue for demo (used when models.yaml/pyyaml aren't available,
# e.g. a bare VDI). Rates are illustrative — see engine._RATES / pricing.yaml.
_FALLBACK_MODELS = [
    {"alias": "reason", "provider": "azure_openai", "deployment": "gpt-4o", "kind": "chat",
     "input_per_1k": 0.005, "output_per_1k": 0.015, "note": "Deep analysis / reasoning"},
    {"alias": "bulk", "provider": "azure_openai", "deployment": "gpt-4o-mini", "kind": "chat",
     "input_per_1k": 0.00015, "output_per_1k": 0.0006, "note": "High-volume, cheap (denoise)"},
    {"alias": "nano", "provider": "azure_openai", "deployment": "gpt-5.4-nano", "kind": "chat",
     "input_per_1k": 0.0002, "output_per_1k": 0.0008, "note": "Fastest / lowest cost"},
    {"alias": "reason-pro", "provider": "azure_openai", "deployment": "gpt-4.1", "kind": "chat",
     "input_per_1k": 0.002, "output_per_1k": 0.008, "note": "Highest quality reasoning"},
    {"alias": "long-context", "provider": "azure_openai", "deployment": "gpt-5-mini", "kind": "chat",
     "input_per_1k": 0.0004, "output_per_1k": 0.0016, "note": "Large transcript windows"},
    {"alias": "judge", "provider": "azure_openai", "deployment": "gpt-4o-mini", "kind": "chat",
     "input_per_1k": 0.00015, "output_per_1k": 0.0006, "note": "LLM-as-judge for evals"},
    {"alias": "reasoning-o", "provider": "azure_openai", "deployment": "o3-mini", "kind": "chat",
     "input_per_1k": 0.0011, "output_per_1k": 0.0044, "note": "Step-by-step reasoning model"},
    {"alias": "embedding", "provider": "azure_openai", "deployment": "text-embedding-3-large",
     "kind": "embedding", "input_per_1k": 0.00013, "output_per_1k": 0.0, "note": "RAG embeddings"},
]
