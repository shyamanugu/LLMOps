"""Golden dataset CRUD (stdlib only). Datasets are JSONL files under
config.DATASET_DIR (local, writable) — one JSON case per line, matching the
Evaluation Gate format. In mock mode this is all local; nothing is uploaded
anywhere. The Ops UI can list, view, edit, add, delete cases and upload a whole
dataset.

Case shape: {"id","input":{"transcript":...},"evaluator":"schema|exact_match",
             "expected":..., "output_schema":..., "rubric":...}
"""
import json

from . import config


def _path(name: str):
    safe = "".join(c for c in name if c.isalnum() or c in ("-", "_", ".")) or "dataset"
    if not safe.endswith(".jsonl"):
        safe += ".jsonl"
    return config.DATASET_DIR / safe


def list_datasets():
    config.ensure_dirs()
    out = []
    for p in sorted(config.DATASET_DIR.glob("*.jsonl")):
        try:
            n = sum(1 for line in p.read_text(encoding="utf-8").splitlines() if line.strip())
        except Exception:
            n = 0
        out.append({"name": p.name, "cases": n})
    return out


def read_cases(name: str):
    p = _path(name)
    cases = []
    if p.exists():
        for i, line in enumerate(p.read_text(encoding="utf-8").splitlines()):
            line = line.strip()
            if not line:
                continue
            try:
                c = json.loads(line)
            except Exception:
                c = {"id": f"line{i}", "_parse_error": line[:200]}
            cases.append(c)
    return cases


def write_cases(name: str, cases: list):
    config.ensure_dirs()
    p = _path(name)
    with open(p, "w", encoding="utf-8") as f:
        for c in cases:
            f.write(json.dumps(c, ensure_ascii=True) + "\n")
    return {"name": p.name, "cases": len(cases)}


def add_case(name: str, case: dict):
    cases = read_cases(name)
    if not case.get("id"):
        case["id"] = f"case_{len(cases) + 1}"
    case.setdefault("evaluator", "schema")
    if case["evaluator"] == "schema":
        case.setdefault("output_schema", {"type": "object"})
    cases.append(case)
    return write_cases(name, cases)


def update_case(name: str, case_id: str, case: dict):
    cases = read_cases(name)
    for i, c in enumerate(cases):
        if str(c.get("id")) == str(case_id):
            case["id"] = case_id
            cases[i] = case
            return write_cases(name, cases)
    return add_case(name, case)


def delete_case(name: str, case_id: str):
    cases = [c for c in read_cases(name) if str(c.get("id")) != str(case_id)]
    return write_cases(name, cases)


def upload_dataset(name: str, content: str):
    """Accept a whole dataset as JSONL text or a JSON array; normalise to JSONL."""
    content = (content or "").strip()
    cases = []
    if content.startswith("["):
        cases = json.loads(content)
    else:
        for line in content.splitlines():
            line = line.strip()
            if line:
                cases.append(json.loads(line))
    for i, c in enumerate(cases):
        c.setdefault("id", f"case_{i + 1}")
        c.setdefault("evaluator", "schema")
    return write_cases(name, cases)


def seed_defaults():
    """Copy the committed seed dataset into the writable dir + add a richer one,
    so the Golden Datasets and Evaluation tabs have content on first run."""
    config.ensure_dirs()
    if list_datasets():
        return
    # 1) mirror the eval seed if present
    src = config.PKG_DIR / "eval" / "dataset" / "analysis_golden.seed.jsonl"
    if src.exists():
        write_cases("analysis_golden.jsonl", _cases_from_text(src.read_text(encoding="utf-8")))
    # 2) a richer telesales golden set (transcript -> expected structured fields)
    rich = [
        {"id": "gt_upgrade", "input": {"transcript": "Customer wants to upgrade plan due to data overages; agent frames unlimited vs overage cost."},
         "evaluator": "schema", "output_schema": {"type": "object", "required": ["intent", "outcome"],
          "properties": {"intent": {"type": "string"}, "outcome": {"type": "string"}}}},
        {"id": "gt_retention", "input": {"transcript": "Billing dispute over price increase; agent applies loyalty credit and retains."},
         "evaluator": "schema", "output_schema": {"type": "object"}},
        {"id": "gt_escalation", "input": {"transcript": "Repeat caller, international texts failing; agent fixes add-on and issues goodwill credit."},
         "evaluator": "schema", "output_schema": {"type": "object"}},
        {"id": "gt_save", "input": {"transcript": "Customer moving abroad wants to cancel; agent offers suspend up to 24 months."},
         "evaluator": "schema", "output_schema": {"type": "object"}},
        {"id": "gt_addline", "input": {"transcript": "Parent adds a line for daughter with a free entry device."},
         "evaluator": "schema", "output_schema": {"type": "object"}},
    ]
    write_cases("telesales_golden.jsonl", rich)


def _cases_from_text(text):
    out = []
    for line in text.splitlines():
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except Exception:
                pass
    return out
