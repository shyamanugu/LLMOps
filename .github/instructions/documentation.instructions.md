---
applyTo: "**"
---

# Documentation-first practice

Every decision, setup step, or deviation from a prior decision gets written down at the time it happens — not after the fact, and not only in a pull-request description.

- Architectural or approach decisions → a new file in `docs/decisions/`, following `docs/decisions/0000-template.md`, numbered sequentially from the highest existing ADR.
- New Azure resources → update `docs/architecture/azure-resource-map.md`.
- Anything requiring access beyond Contributor → add it to the permission request queue in `docs/checklist/BUILD-CHECKLIST.md` (Phase 0); don't just mention it in passing.
- Component setup or scope changes → update that component's own `README.md` directly. It should always describe what was actually built, not what was originally planned.

Presentation materials (`presentation/`) are updated only once, at the end of a build phase, from these documents — never the other way around.
