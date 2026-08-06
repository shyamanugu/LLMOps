"""SQL data source — NL2SQL then *safe*, read-only, parameterised execution.

This is a deliberately paranoid data source. Two independent controls protect the database:

1. **NL2SQL** turns a natural-language question into SQL using a model (via the model client).
2. A **SQL safety guard** then statically validates the generated (or supplied) SQL before it is
   ever executed: only a single ``SELECT`` is permitted, every referenced table must be on an
   explicit allow-list, and any write / DDL / stacked statement is rejected. Execution itself is
   parameterised (no string interpolation of user values).

The database driver is intentionally not wired here (drivers are deployment-specific); the
``execute`` path is marked ``# TODO(wiring)`` and returns a dev mock. The *safety guard is real*
and fully unit-testable without a database.
"""

from __future__ import annotations

import re
from typing import Any, Final

from llmops.common.errors import LLMOpsError
from llmops.common.logging import get_logger
from llmops.config.settings import Settings, get_settings

_logger = get_logger(__name__)

#: Statement keywords that must never appear in a read-only query.
_FORBIDDEN_KEYWORDS: Final[frozenset[str]] = frozenset(
    {
        "insert",
        "update",
        "delete",
        "drop",
        "alter",
        "truncate",
        "create",
        "replace",
        "merge",
        "grant",
        "revoke",
        "exec",
        "execute",
        "call",
        "attach",
        "pragma",
    }
)

_TABLE_REF_RE: Final[re.Pattern[str]] = re.compile(
    r"\b(?:from|join)\s+([a-zA-Z_][\w.]*)", re.IGNORECASE
)


class UnsafeSqlError(LLMOpsError):
    """Raised when generated or supplied SQL fails the read-only safety guard."""

    code = "unsafe_sql"
    http_status = 400


class SqlDataSource:
    """Natural-language querying over a relational database with strict safety controls.

    Args:
        allowed_tables: The only tables that may be referenced by a query (least privilege).
        model_alias: Model alias used for NL2SQL (resolved via the model router at call time).
        settings: Platform settings. Defaults to the process singleton.
        max_rows: Hard cap applied to every executed query.
    """

    name = "sql"

    def __init__(
        self,
        allowed_tables: list[str],
        *,
        model_alias: str = "reason",
        settings: Settings | None = None,
        max_rows: int = 1000,
    ) -> None:
        self._settings = settings or get_settings()
        self._allowed_tables = {t.lower() for t in allowed_tables}
        self._model_alias = model_alias
        self._max_rows = max_rows
        self._pool: Any | None = None

    async def nl2sql(self, question: str, *, schema_hint: str | None = None) -> str:
        """Translate a natural-language ``question`` into a single ``SELECT`` statement.

        Args:
            question: The user's natural-language question.
            schema_hint: Optional DDL / column description to ground the generation.

        Returns:
            A SQL string (not yet executed — still subject to :meth:`assert_safe`).
        """
        # TODO(wiring): call ModelClient.chat(alias=self._model_alias, ...) with a NL2SQL prompt
        #   grounded on the allow-listed tables + schema_hint, then extract the SQL. Until the
        #   models package is wired, return a safe dev mock over the first allowed table.
        _logger.debug("nl2sql dev mock", question=question)
        table = next(iter(sorted(self._allowed_tables)), "unknown_table")
        return f"SELECT * FROM {table} LIMIT {self._max_rows}"

    def assert_safe(self, sql: str) -> str:
        """Validate that ``sql`` is a single read-only, allow-listed ``SELECT``.

        Args:
            sql: The SQL statement to validate.

        Returns:
            The normalised (single-statement) SQL when it is safe.

        Raises:
            UnsafeSqlError: If the statement is not a single read-only ``SELECT`` over
                allow-listed tables.
        """
        normalised = sql.strip().rstrip(";").strip()
        if not normalised:
            raise UnsafeSqlError("empty SQL statement")

        # No stacked statements.
        if ";" in normalised:
            raise UnsafeSqlError("multiple statements are not allowed", detail={"sql": sql})

        lowered = normalised.lower()
        if not (lowered.startswith("select") or lowered.startswith("with")):
            raise UnsafeSqlError("only read-only SELECT queries are allowed", detail={"sql": sql})

        for keyword in _FORBIDDEN_KEYWORDS:
            if re.search(rf"\b{keyword}\b", lowered):
                raise UnsafeSqlError(f"forbidden keyword '{keyword}' in query", detail={"sql": sql})

        referenced = {t.lower() for t in _TABLE_REF_RE.findall(normalised)}
        illegal = {
            t
            for t in referenced
            if t.split(".")[0] not in self._allowed_tables and t not in self._allowed_tables
        }
        if illegal:
            raise UnsafeSqlError(
                f"query references non-allow-listed tables: {sorted(illegal)}",
                detail={"allowed": sorted(self._allowed_tables), "referenced": sorted(referenced)},
            )
        return normalised

    async def execute(self, sql: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Safely execute a read-only ``SELECT`` and return rows as dicts.

        The statement is validated by :meth:`assert_safe` first; values are always bound as
        parameters (never interpolated).

        Args:
            sql: The SQL to execute.
            params: Named bind parameters.

        Returns:
            A list of row mappings (capped at ``max_rows``).

        Raises:
            UnsafeSqlError: If the SQL fails the safety guard.
        """
        safe_sql = self.assert_safe(sql)
        pool = self._get_pool()
        if pool is None:  # dev mock
            _logger.debug("sql dev mock execute", sql=safe_sql, params=params or {})
            return [{"mock": True, "sql": safe_sql, "params": params or {}}]

        # TODO(wiring): acquire a read-only connection from the pool and execute with bound
        #   params, e.g. `async with pool.acquire() as conn: rows = await conn.fetch(safe_sql, ...)`.
        raise NotImplementedError("TODO(wiring): execute parameterised query against the DB pool")

    async def query(self, q: str, **kwargs: Any) -> list[dict[str, Any]]:
        """:class:`DataSource` entry point — NL2SQL then safe execute.

        Args:
            q: The natural-language question.
            **kwargs: ``schema_hint`` and/or ``params`` forwarded downstream.

        Returns:
            Query result rows.
        """
        sql = await self.nl2sql(q, schema_hint=kwargs.get("schema_hint"))
        return await self.execute(sql, kwargs.get("params"))

    def _get_pool(self) -> Any | None:
        """Lazily construct the database connection pool, or ``None`` in dev."""
        if self._pool is not None:
            return self._pool
        # TODO(wiring): construct a read-only connection pool (asyncpg / aioodbc) from a
        #   Key Vault-backed connection string using managed identity where supported.
        return None
