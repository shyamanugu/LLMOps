"""Azure Blob / ADLS storage helpers."""

from __future__ import annotations

import os
from typing import Optional

import duckdb
import fsspec
import polars as pl

from ai_pipeline.programs_config.base import StorageConfig
from ai_pipeline.logging_config import get_logger

logger = get_logger("services.storage")


class StorageService:
    """Thin wrapper around fsspec + duckdb for Azure Blob access."""

    def __init__(self, config: StorageConfig) -> None:
        self.config = config
        self.fs = fsspec.filesystem(
            "abfs",
            account_name=config.account_name,
            account_key=config.account_key,
        )
        try:
            duckdb.register_filesystem(self.fs)
        except duckdb.InvalidInputException:
            pass  # already registered in this session
        logger.info("StorageService initialised | account=%s", config.account_name)

    # ── reads ────────────────────────────────────────────────────────────

    def read_parquet_sql(self, container: str, filename: str, where: Optional[str] = None) -> pl.DataFrame:
        path = f"abfs://{container}/{filename}"
        q = f"SELECT * FROM read_parquet('{path}')"
        if where:
            q += f" WHERE {where}"
        logger.info("read_parquet_sql | %s", q)
        try:
            return duckdb.query(q).pl()
        except duckdb.IOException as exc:
            if "No files found" in str(exc):
                raise FileNotFoundError(f"No source file at {path}") from exc
            raise

    def read_parquet_sql_multi(self, container: str, filenames: list[str], where: Optional[str] = None, columns: Optional[list[str]] = None) -> pl.DataFrame:
        paths = [f"abfs://{container}/{f}" for f in filenames]
        cols = ", ".join(columns) if columns else "*"
        q = f"SELECT {cols} FROM read_parquet({paths}, filename=true)"
        if where:
            q += f" WHERE {where}"
        logger.info("read_parquet_sql_multi | files=%d", len(filenames))
        return duckdb.query(q).pl()

    def read_parquet(self, container: str, filename: str) -> pl.DataFrame:
        path = f"abfs://{container}/{filename}"
        with self.fs.open(path, "rb") as f:
            return pl.read_parquet(f)

    def read_json(self, container: str, filename: str) -> dict:
        import json
        path = f"abfs://{container}/{filename}"
        with self.fs.open(path, "r") as f:
            return json.loads(f.read())

    # ── writes ───────────────────────────────────────────────────────────

    def _ensure_container(self, container: str) -> None:
        """Create the top-level blob container if it does not already exist.

        ``container`` may include a virtual sub-path (e.g. ``temp/weekly-summary``);
        only the first segment is a real Azure Blob container.
        """
        root = str(container).split("/")[0]
        if not root:
            return
        try:
            if not self.fs.exists(root):
                self.fs.mkdir(root)
                logger.info("Created missing container | %s", root)
        except Exception as exc:  # noqa: BLE001 - best-effort; write will surface real errors
            logger.debug("ensure_container(%s) skipped: %s", root, exc)

    def write_parquet(self, df: pl.DataFrame, container: str, filename: str) -> None:
        self._ensure_container(container)
        path = f"abfs://{container}/{filename}"
        logger.info("write_parquet | %s | rows=%d", path, len(df))
        with self.fs.open(path, "wb") as f:
            df.write_parquet(f)

    def write_json(self, data: dict, container: str, filename: str) -> None:
        import json
        self._ensure_container(container)
        path = f"abfs://{container}/{filename}"
        logger.info("write_json | %s", path)
        with self.fs.open(path, "w", encoding="utf-8") as f:
            f.write(json.dumps(data, indent=4, ensure_ascii=True))

    def exists(self, container: str, filename: str) -> bool:
        return self.fs.exists(f"abfs://{container}/{filename}")

    def mkdir(self, container: str, dirname: str) -> None:
        self._ensure_container(container)
        self.fs.mkdir(f"{container}/{dirname}")

    def list_files(self, container: str, prefix: str = "", suffix: str | None = None) -> list[str]:
        """List blob names directly under ``container/prefix``.

        Returns bare names (not full paths). ``prefix`` scopes the listing to a
        virtual sub-directory (e.g. a date folder); ``suffix`` optionally filters
        by extension (e.g. ``.json``).
        """
        base = f"{container}/{prefix}".rstrip("/")
        try:
            entries = self.fs.ls(base, detail=False)
        except FileNotFoundError:
            return []
        names = [str(e).rstrip("/").split("/")[-1] for e in entries]
        if suffix:
            names = [n for n in names if n.endswith(suffix)]
        return names


class LocalStorageService:
    """Filesystem-backed drop-in for ``StorageService`` used in **mock** mode.

    Same method surface the pipeline steps call, but reads/writes parquet + JSON
    under a local base directory (``AI_PIPELINE_LOCAL_DATA_DIR``, default
    ``./data``) instead of Azure Blob — so the whole pipeline runs on a laptop
    with no Azure Storage account. Containers map to sub-directories:
    ``<base>/<container>/<filename>``. Reads use duckdb on the local parquet
    (identical SQL to the Azure path), keeping step behaviour unchanged.
    """

    def __init__(self, config: StorageConfig, base_dir: str | None = None) -> None:
        self.config = config
        base = base_dir or os.environ.get("AI_PIPELINE_LOCAL_DATA_DIR", "").strip() or "./data"
        from pathlib import Path

        self.base = Path(base).expanduser().resolve()
        self.base.mkdir(parents=True, exist_ok=True)
        logger.info("LocalStorageService (mock) initialised | base=%s", self.base)

    def _path(self, container: str, filename: str):
        return self.base / container / filename

    def _posix(self, container: str, filename: str) -> str:
        return self._path(container, filename).as_posix()

    # ── reads ────────────────────────────────────────────────────────────
    def read_parquet_sql(self, container: str, filename: str, where: Optional[str] = None) -> pl.DataFrame:
        path = self._path(container, filename)
        if not path.exists():
            raise FileNotFoundError(f"No source file at {path}")
        q = f"SELECT * FROM read_parquet('{path.as_posix()}')"
        if where:
            q += f" WHERE {where}"
        logger.info("read_parquet_sql (local) | %s", q)
        return duckdb.query(q).pl()

    def read_parquet_sql_multi(self, container: str, filenames: list[str], where: Optional[str] = None, columns: Optional[list[str]] = None) -> pl.DataFrame:
        paths = [self._posix(container, f) for f in filenames if self._path(container, f).exists()]
        if not paths:
            raise FileNotFoundError(f"No source files in {self.base / container}")
        cols = ", ".join(columns) if columns else "*"
        q = f"SELECT {cols} FROM read_parquet({paths}, filename=true)"
        if where:
            q += f" WHERE {where}"
        return duckdb.query(q).pl()

    def read_parquet(self, container: str, filename: str) -> pl.DataFrame:
        path = self._path(container, filename)
        if not path.exists():
            raise FileNotFoundError(f"No source file at {path}")
        return pl.read_parquet(path)

    def read_json(self, container: str, filename: str) -> dict:
        import json
        with open(self._path(container, filename), "r", encoding="utf-8") as f:
            return json.loads(f.read())

    # ── writes ───────────────────────────────────────────────────────────
    def write_parquet(self, df: pl.DataFrame, container: str, filename: str) -> None:
        path = self._path(container, filename)
        path.parent.mkdir(parents=True, exist_ok=True)
        logger.info("write_parquet (local) | %s | rows=%d", path, len(df))
        df.write_parquet(path)

    def write_json(self, data: dict, container: str, filename: str) -> None:
        import json
        path = self._path(container, filename)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(json.dumps(data, indent=4, ensure_ascii=True))

    def exists(self, container: str, filename: str) -> bool:
        return self._path(container, filename).exists()

    def mkdir(self, container: str, dirname: str) -> None:
        (self.base / container / dirname).mkdir(parents=True, exist_ok=True)

    def list_files(self, container: str, prefix: str = "", suffix: str | None = None) -> list[str]:
        base = self.base / container / prefix if prefix else self.base / container
        if not base.exists():
            return []
        names = [p.name for p in base.iterdir() if p.is_file()]
        if suffix:
            names = [n for n in names if n.endswith(suffix)]
        return names


def make_storage(config: StorageConfig):
    """Return the storage backend for the current runtime mode: filesystem in
    **mock** mode (no Azure needed), Azure Blob in **real** mode. Single seam —
    steps receive whichever object and call the same methods."""
    from ai_pipeline import mode as run_mode

    if run_mode.is_mock():
        return LocalStorageService(config)
    return StorageService(config)

