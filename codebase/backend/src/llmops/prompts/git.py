"""Git-backed prompt registry — the default, and the source of truth.

Prompts live as ``usecases/<usecase>/prompts/<name>.prompt.yaml`` files in the repository.
This registry reads and validates them into :class:`PromptSpec` objects. Because Git is the
system of record, promotions between environments are ordinary reviewed pull requests that
must pass the evaluation gate before merge.

This is a *real* implementation: no client wiring is required, only the filesystem.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from llmops.common.errors import ConfigError, PromptNotFoundError
from llmops.common.logging import get_logger
from llmops.config.settings import Settings, get_settings
from llmops.prompts.schema import PromptSpec

logger = get_logger(__name__)

_GLOB = "*/prompts/*.prompt.yaml"


class GitPromptRegistry:
    """Reads prompt specs from ``usecases/*/prompts/*.prompt.yaml``.

    Args:
        usecases_dir: Root directory containing per-use-case folders. Defaults to the
            configured ``usecases_dir`` from :class:`Settings`.
    """

    def __init__(self, usecases_dir: str | Path | None = None, *, settings: Settings | None = None) -> None:
        settings = settings or get_settings()
        self._root = Path(usecases_dir if usecases_dir is not None else settings.usecases_dir)

    # -- loading ---------------------------------------------------------------------

    def _iter_spec_files(self) -> list[Path]:
        """Return all ``*.prompt.yaml`` paths under the use-cases root (may be empty)."""
        if not self._root.exists():
            logger.warning("usecases dir missing; no prompts loaded", path=str(self._root))
            return []
        return sorted(self._root.glob(_GLOB))

    @staticmethod
    def _load_file(path: Path) -> PromptSpec:
        """Parse and validate a single prompt YAML file into a :class:`PromptSpec`."""
        try:
            raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as exc:  # pragma: no cover - malformed authoring is rare
            raise ConfigError(f"invalid YAML in prompt file: {exc}", detail={"path": str(path)}) from exc
        try:
            return PromptSpec.model_validate(raw)
        except Exception as exc:  # noqa: BLE001 - re-wrap validation errors uniformly
            raise ConfigError(
                f"prompt file failed schema validation: {exc}", detail={"path": str(path)}
            ) from exc

    def list(self) -> list[PromptSpec]:
        """Return every prompt version found on disk, sorted by id then version."""
        specs = [self._load_file(p) for p in self._iter_spec_files()]
        specs.sort(key=lambda s: (s.id, s.version))
        return specs

    def get(self, prompt_id: str, label: str = "prod") -> PromptSpec:
        """Return the highest-version spec for ``prompt_id`` carrying ``label``.

        Args:
            prompt_id: The prompt identifier to resolve.
            label: The deployment label to filter on.

        Returns:
            The newest matching :class:`PromptSpec`.

        Raises:
            PromptNotFoundError: If no version matches the id (and label).
        """
        candidates = [s for s in self.list() if s.id == prompt_id]
        if not candidates:
            raise PromptNotFoundError(
                f"no prompt with id '{prompt_id}'",
                detail={"prompt_id": prompt_id, "root": str(self._root)},
            )
        labelled = [s for s in candidates if label in s.labels]
        if not labelled:
            known = sorted({lbl for s in candidates for lbl in s.labels})
            raise PromptNotFoundError(
                f"prompt '{prompt_id}' has no version labelled '{label}'",
                detail={"prompt_id": prompt_id, "label": label, "known_labels": known},
            )
        return max(labelled, key=lambda s: s.version)

    def push(self, spec: PromptSpec) -> None:
        """Write ``spec`` back to disk as a ``*.prompt.yaml`` file.

        The file is placed under ``<root>/_generated/prompts/`` when the originating use
        case is unknown. In normal operation prompts are authored by hand and reviewed via
        pull request; this method exists so tooling (e.g. a "promote from Langfuse" sync)
        can round-trip a spec into the Git source of truth.
        """
        target_dir = self._root / "_generated" / "prompts"
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / f"{spec.id}.prompt.yaml"
        payload = spec.model_dump(mode="json")
        target.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")
        logger.info("wrote prompt spec to git source", prompt_id=spec.id, path=str(target))
