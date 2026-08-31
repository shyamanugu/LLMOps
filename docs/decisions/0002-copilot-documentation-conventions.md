# ADR 0002: GitHub Copilot-readable documentation conventions

## Status
Accepted

## Context
This repository is also opened directly in a separate environment where only GitHub Copilot is available. Documentation needs to be legible to Copilot's native conventions there, and must read as self-contained — it cannot assume the reader has any other context about how or where it was produced.

## Decision
1. Adopt GitHub Copilot's native custom-instructions convention: `.github/copilot-instructions.md` for repository-wide guidance, and `.github/instructions/*.instructions.md` (scoped via an `applyTo` front-matter glob) for path-specific guidance.
2. Instruction files are added only for components that actually exist. No speculative instructions for components that haven't been built yet.
3. Instruction files point back to the relevant ADRs and component `README.md` files rather than duplicating their content — one source of truth per decision.
4. Further Copilot conventions (reusable prompt files under `.github/prompts/`, custom chat modes under `.github/chatmodes/`) are introduced later, only once a real, repeated pattern emerges worth capturing — not scaffolded empty ahead of need.

## Alternatives Considered
- A single combined instructions file covering every tool that might touch this repo: rejected. Different tools have different native conventions for this; conflating them risks one tool's instructions reading as noise to another.

## Consequences
- Two environments (this one, and the Copilot-only one) can both operate on this repo without either needing awareness of the other.
- Instruction files need upkeep as components are added — accepted as the cost of keeping them accurate instead of letting them go stale.

## Revisit When
A real, repeated prompt or workflow pattern emerges that would justify adding a Copilot prompt file or chat mode.
