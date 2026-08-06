"""Local CLI to run a use-case pipeline once, off-Azure where possible.

A developer convenience for exercising a use-case pipeline without the API or CI::

    python pipelines_cli.py --usecase apix --input '{"question": "reset my key"}'
    python pipelines_cli.py --usecase apix --input-file payload.json

It constructs the pipeline from the orchestration package when available and degrades to a
clearly-labelled dev echo when it is not, so the command always produces output. Sync entry
point only — the pipeline itself is async (ARCHITECTURE_SPEC §6).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any

# Ensure ``src`` is importable when run directly from the backend directory.
_SRC = Path(__file__).resolve().parent / "src"
if _SRC.exists() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from llmops.common.logging import configure_logging, get_logger  # noqa: E402

_log = get_logger(__name__)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Run a use-case pipeline locally.")
    parser.add_argument("--usecase", required=True, help="Use-case name (dir under usecases/).")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--input", help="Inline JSON input object for the pipeline.")
    group.add_argument("--input-file", help="Path to a JSON file with the pipeline input.")
    parser.add_argument("--usecases-dir", default="usecases", help="Root of use-case dirs.")
    return parser.parse_args(argv)


def _load_input(args: argparse.Namespace) -> dict[str, Any]:
    """Read the pipeline input object from ``--input`` or ``--input-file``."""
    raw = Path(args.input_file).read_text(encoding="utf-8") if args.input_file else args.input
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("pipeline input must be a JSON object")
    return data


def _build_pipeline(usecase: str, usecases_dir: str) -> Any | None:
    """Construct the use-case pipeline from orchestration, or ``None`` for the dev stub."""
    try:
        from llmops.orchestration.pipeline import Pipeline  # type: ignore[import-not-found]

        # TODO(wiring): confirm the exact loader once orchestration lands.
        loader = getattr(Pipeline, "from_usecase", None)
        if callable(loader):
            return loader(usecase)
        path = Path(usecases_dir) / usecase / "agents" / "pipeline.agent.yaml"
        from_yaml = getattr(Pipeline, "from_yaml", None)
        if callable(from_yaml) and path.exists():
            return from_yaml(path)
    except Exception as exc:  # noqa: BLE001
        _log.warning("orchestration pipeline unavailable; using dev echo", error=str(exc))
    return None


async def _run(usecase: str, payload: dict[str, Any], usecases_dir: str) -> Any:
    """Run the pipeline (or dev echo) and return its result."""
    pipeline = _build_pipeline(usecase, usecases_dir)
    if pipeline is None:
        _log.warning("running dev echo stand-in (no live pipeline)", usecase=usecase)
        from llmops.evaluation.runner import _DevEchoPipeline

        pipeline = _DevEchoPipeline()
    return await pipeline.run(payload)


def main(argv: list[str] | None = None) -> int:
    """Entry point: run the pipeline and print its result as JSON."""
    args = _parse_args(argv)
    configure_logging()
    try:
        payload = _load_input(args)
        result = asyncio.run(_run(args.usecase, payload, args.usecases_dir))
    except Exception as exc:  # noqa: BLE001
        _log.error("pipeline run failed", usecase=args.usecase, error=str(exc))
        print(f"pipeline run ERROR for '{args.usecase}': {exc}", file=sys.stderr)
        return 1

    serialisable = result if isinstance(result, (dict, list)) else getattr(result, "__dict__", str(result))
    print(json.dumps(serialisable, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
