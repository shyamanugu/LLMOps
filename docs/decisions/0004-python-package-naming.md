# ADR 0004: Python package naming across components

## Status
Accepted

## Context
Model Management's Python code was originally laid out as `src/*.py` — a bare `src` package. While building Orchestration, which needs to import Model Management's provider classes directly (Model Management resolves models but deliberately does not call them; Orchestration does the calling), it became clear that every component using the same generic `src` package name cannot coexist on the same Python path. Only one module named `src` can be loaded in a process at a time — the second component to import it would silently get the first component's code, or fail outright depending on path order. This was caught before Orchestration was written, not after, but it required a retroactive fix to the already-built Model Management component.

## Decision
Every component's importable Python package is named after its function, nested one level under `src/`: `src/model_management/`, `src/orchestration/`, and so on for future components. The `src/` folder itself is not a package — it exists only as the conventional "source lives here" directory; `pytest.ini` (`pythonpath = src`) and any run script add it to the path so the inner, uniquely-named package is what's actually importable.

Model Management was restructured from `src/*.py` to `src/model_management/*.py` to comply with this, including fixing its config-path resolution (`Path(__file__).resolve().parents[2]`, since the module is now one directory deeper) and its test imports.

## Alternatives Considered
- A single shared virtual environment with all components installed as proper pip packages (`pyproject.toml` per component, editable installs): more correct long-term, but real packaging overhead (build metadata, version pinning, an install step) isn't justified yet with two components and no CI/CD (component 09) to run an install step in. Revisit once CI/CD exists.
- Leaving `src` as-is and having Orchestration reach into Model Management via a `sys.path` insert pointed at a specific file path: rejected — fragile, and doesn't scale past two components without collisions resurfacing elsewhere (e.g., two components' `tests/` folders, or `config/` naming).

## Consequences
- Every future component must nest its code under `src/<component_name>/`, not `src/*.py` directly — this is now the convention, not a one-off.
- Cross-component imports (like Orchestration importing Model Management) work via `pythonpath` entries in `pytest.ini` pointing at sibling components' `src/` directories — documented per-component in each README, not assumed.
- This is still not real packaging. A component copied out to its own repo (as discussed for component 01) would need its cross-component imports resolved differently at that point — either vendored, or the dependency installed as a real package.

## Revisit When
CI/CD (component 09) is built — that's the natural point to introduce real per-component packaging (`pyproject.toml`, editable installs) instead of `pythonpath` path manipulation.
