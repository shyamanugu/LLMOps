# ADR 0014: FinOps — infrastructure cost, distinct from Observability's LLM cost, Workbook deferred

## Status
Accepted

## Context
Observability (05) already computes cost per model call (`compute_cost()`, reading Model Management's `pricing.yaml`). That's LLM token usage cost, not Azure resource billing — a Container Apps environment idling, an Azure AI Search Basic-tier fixed monthly charge, and Cognitive Services consumption all cost money with no relationship to `pricing.yaml`. This component is where that other kind of cost — actual Azure billing — gets visibility and alerting. Separately, Phase 0's access audit already flagged budget-creation permissions as unconfirmed under Contributor, and a cost dashboard would normally be an Azure Workbook, whose serialized JSON body carries the same "don't fabricate an unverified integration" risk already flagged for Content Safety's Prompt Shields (ADR 0009).

## Decision
1. **Two authored Bicep resources**: `Microsoft.Consumption/budgets` (monthly amount, 50%/80%/forecasted-100% notification thresholds) and `Microsoft.CostManagement/exports` (daily actual-cost CSV to Blob Storage). Both are well-documented, stable ARM resource schemas authored with high confidence — unlike a Workbook's body.
2. **The cost-export destination is a parameter** (`exportStorageAccountId`), not a new Storage Account this component provisions — reusing Feedback Loop (11)'s account (or any existing one) avoids proliferating storage accounts for a small, low-volume export.
3. **No Workbook is built.** `Microsoft.Insights/workbooks`' `serializedData` is a deeply nested, version-sensitive JSON blob that isn't something to author with confidence without verifying against a live Workbook first — the identical reasoning already applied to Content Safety's Prompt Shields in ADR 0009. `queries/cost-by-tag.kql` is a plain reference query instead, explicitly marked unverified since no cost export has ever actually run to check column names against.
4. **Whether Contributor can even create a budget is left as an open, resolvable-by-attempting question**, not assumed either way — `budget.bicep` is authored and ready; the deployment attempt itself is how the Phase 0 checklist's "confirm Cost Management Contributor is included" question gets answered, rather than guessed at in advance.
5. **No Python package** — like CI/CD (09), this component's deliverable is Bicep and a reference query, verified by `az bicep build` (already part of CI, component 09), not by a test suite.

## Alternatives Considered
- **Building a Workbook now, best-effort**: rejected — a subtly wrong `serializedData` body would deploy successfully (Bicep/ARM wouldn't reject malformed-but-valid-JSON workbook content) yet render as a broken or empty dashboard, a failure mode that's silent until a human actually opens it. That's a worse outcome than not building it and saying so.
- **Unifying infrastructure cost and LLM usage cost into one tracked number now**: rejected — no usecase exists yet whose total cost anyone needs to report on, and forcing a premature unification risks picking the wrong join key (by tag? by session_id? by time window?) before a real reporting need clarifies which one matters.
- **Provisioning a dedicated Storage Account for cost exports**: rejected — the export volume is small (daily CSV), and reusing an existing account (Feedback Loop's) avoids a resource that exists only to hold a few files.

## Consequences
- Budget and export are ready to deploy the moment someone runs the `az deployment group create` commands in this component's README — no further authoring blocks that attempt.
- If the budget deployment fails with an authorization error, that's new, concrete information for the Phase 0 permission queue (a specific error message, not a hypothetical), rather than something guessed at and requested speculatively.
- There is currently no dashboard — `cost-by-tag.kql` is a starting point for building one by hand once real export data exists, not a working Workbook today.
- Infrastructure cost and LLM usage cost remain two separate numbers a human has to look at separately; there is no single "this usecase cost $X all-in" report yet.

## Revisit When
- The budget deployment is actually attempted — record whether it succeeded or hit an authorization error, and update this ADR's "unconfirmed" framing with the real answer.
- Real cost export data exists — verify `cost-by-tag.kql`'s column names against it, fix as needed, and consider building the Workbook for real once its expected shape can be checked against actual exported data rather than guessed at.
- A real usecase needs a unified cost view (infrastructure + LLM tokens, by usecase/client) — design the join between this component's exported data and Observability's `StepEvent`/`PipelineEvent` data at that point, informed by what that usecase's actual reporting need looks like.
