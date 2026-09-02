"""Build a golden evaluation dataset from a historical analysis parquet (Phase 5).

Run from the pipeline's real venv (needs polars + the program config). Each
denoised transcript becomes a `schema` case whose `output_schema` is the
program's analysis Pydantic model JSON schema — so the gate checks that the
analysis step still produces structurally-valid output for known-good inputs.

    python -m ai_pipeline.eval.build_dataset --program telesales \
        --parquet /path/to/analysis/2025-08-28.parquet \
        --out ai_pipeline/eval/dataset/telesales_golden.jsonl --limit 50
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def build(program: str, parquet_path: str, out_path: str, limit: int = 50) -> int:
    import polars as pl

    from ai_pipeline.programs_config import load_program_config

    cfg = load_program_config(program)
    schema_json = (
        cfg.analysis_schema.model_json_schema() if cfg.analysis_schema else {"type": "object"}
    )

    df = pl.read_parquet(parquet_path)
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    n = 0
    with open(out, "w", encoding="utf-8") as f:
        for row in df.head(limit).iter_rows(named=True):
            transcript = row.get("denoised_text")
            if not transcript:
                continue
            case = {
                "id": f"{program}_{row.get('contact_id', n)}",
                "input": {"transcript": transcript},
                "evaluator": "schema",
                "output_schema": schema_json,
            }
            f.write(json.dumps(case, default=str) + "\n")
            n += 1
    return n


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Build AI Pipeline golden eval dataset from analysis parquet")
    p.add_argument("--program", required=True)
    p.add_argument("--parquet", required=True, help="path to a historical analysis parquet")
    p.add_argument("--out", required=True, help="output JSONL path")
    p.add_argument("--limit", type=int, default=50)
    args = p.parse_args(argv)
    n = build(args.program, args.parquet, args.out, args.limit)
    print(f"Wrote {n} case(s) to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
