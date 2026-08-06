/**
 * TypeScript types mirroring the backend pydantic models and the API contract
 * defined in ARCHITECTURE_SPEC.md §3. These are the wire shapes returned by the
 * FastAPI service under `/api/v1`. No `any` — every field is explicitly typed.
 */

/** Deployment environments (mirrors llmops.common.types.Environment). */
export type Environment = 'dev' | 'test' | 'prod';

/** Token usage for a single model call. */
export interface Usage {
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
}

/** Result of a single chat/completion call. */
export interface ChatResult {
  text: string;
  model: string;
  usage: Usage;
  cost_usd: number;
  latency_ms: number;
  finish_reason: string | null;
  cache_hit: boolean;
}

/** A retrieved knowledge chunk (RAG). */
export interface Chunk {
  id: string;
  text: string;
  score: number;
  source: string | null;
  metadata: Record<string, JsonValue>;
}

/** JSON-serialisable value (used for span attributes, tool args, metadata). */
export type JsonValue =
  | string
  | number
  | boolean
  | null
  | JsonValue[]
  | { [key: string]: JsonValue };

/* ---- Prompts ------------------------------------------------------------ */

/** Mirrors prompts/schema.py PromptSpec (the .prompt.yaml contract). */
export interface PromptSpec {
  id: string;
  version: number;
  labels: string[];
  model_alias: string;
  temperature: number;
  inputs: string[];
  template: string;
  eval_refs: string[];
  changelog: string[];
}

/** Lightweight prompt row for list views (GET /prompts). */
export interface PromptSummary {
  id: string;
  version: number;
  labels: string[];
  model_alias: string;
}

/** Response body for POST /prompts/{id}/render. */
export interface RenderResult {
  prompt_id: string;
  rendered: string;
}

/* ---- Models ------------------------------------------------------------- */

/** An alias -> Azure deployment mapping for a given environment (GET /models). */
export interface ModelAlias {
  alias: string;
  deployment: string;
  environment: Environment;
  kind: string;
  description: string | null;
}

/* ---- Evaluations -------------------------------------------------------- */

export type GateStatus = 'pass' | 'fail' | 'running' | 'error';

/** Score for a single evaluation metric within a gate report. */
export interface MetricResult {
  name: string;
  score: number;
  threshold: number;
  passed: boolean;
  detail: string | null;
}

/** Mirrors evaluation/gate.py GateReport (GET /evaluations). */
export interface GateReport {
  id: string;
  usecase: string;
  status: GateStatus;
  subset: boolean;
  cases_total: number;
  cases_passed: number;
  metrics: MetricResult[];
  started_at: string;
  finished_at: string | null;
  commit_sha: string | null;
}

/** Request body for POST /evaluations/run. */
export interface EvaluationRunRequest {
  usecase: string;
  scope: 'subset' | 'full';
}

/** Response for POST /evaluations/run (async task handle). */
export interface EvaluationRunResponse {
  task_id: string;
  usecase: string;
  status: GateStatus;
  accepted: boolean;
}

/* ---- Traces ------------------------------------------------------------- */

export type SpanKind = 'request' | 'agent' | 'model' | 'tool' | 'guardrail';
export type SpanStatus = 'ok' | 'error';

/** A summarised trace row (GET /traces). */
export interface TraceSummary {
  trace_id: string;
  name: string;
  usecase: string | null;
  status: SpanStatus;
  start_time: string;
  duration_ms: number;
  span_count: number;
  cost_usd: number;
  total_tokens: number;
}

/** A single span within a trace tree. Children nest to form the tree. */
export interface Span {
  span_id: string;
  parent_id: string | null;
  name: string;
  kind: SpanKind;
  status: SpanStatus;
  start_time: string;
  duration_ms: number;
  attributes: Record<string, JsonValue>;
  cost_usd: number | null;
  tokens: number | null;
  children: Span[];
}

/** Full trace detail (GET /traces/{id}). */
export interface TraceDetail {
  trace_id: string;
  name: string;
  usecase: string | null;
  status: SpanStatus;
  start_time: string;
  duration_ms: number;
  cost_usd: number;
  total_tokens: number;
  root: Span;
}

/* ---- Costs -------------------------------------------------------------- */

/** A single cost aggregation bucket (GET /costs). */
export interface CostAggregate {
  dimension: 'usecase' | 'model' | 'day';
  key: string;
  cost_usd: number;
  requests: number;
  input_tokens: number;
  output_tokens: number;
}

/** Grouped cost response for the Costs page. */
export interface CostReport {
  total_usd: number;
  window_days: number;
  by_day: CostAggregate[];
  by_usecase: CostAggregate[];
  by_model: CostAggregate[];
}

/* ---- Feedback ----------------------------------------------------------- */

export type FeedbackKind = 'thumbs' | 'edit' | 'override';

/** Mirrors feedback/models.py FeedbackEvent (POST /feedback). */
export interface FeedbackEvent {
  id: string;
  trace_id: string;
  kind: FeedbackKind;
  value: string;
  reason: string | null;
  user_hash: string;
  ts: string;
}

/** Request body to capture a new feedback event. */
export interface FeedbackCreate {
  trace_id: string;
  kind: FeedbackKind;
  value: string;
  reason?: string | null;
}

/* ---- Agents / pipelines ------------------------------------------------- */

/** One agent within a pipeline (from usecases agents definitions). */
export interface AgentDef {
  name: string;
  role: string;
  prompt_id: string;
  model_alias: string;
  tools: string[];
}

/** A pipeline definition (GET /agents). */
export interface PipelineDef {
  name: string;
  usecase: string;
  description: string | null;
  agents: AgentDef[];
}

/* ---- Guardrails --------------------------------------------------------- */

export type GuardOutcome = 'allowed' | 'blocked' | 'redacted';

/** A configured guard in the guardrail engine. */
export interface GuardrailConfig {
  name: string;
  category: string;
  stage: 'input' | 'output' | 'both';
  enabled: boolean;
  provider: string;
}

/** A recorded guardrail event (GET /guardrails). */
export interface GuardrailEvent {
  id: string;
  guard: string;
  category: string;
  outcome: GuardOutcome;
  detail: string | null;
  trace_id: string | null;
  ts: string;
}

/** Combined guardrails response. */
export interface GuardrailsReport {
  configs: GuardrailConfig[];
  events: GuardrailEvent[];
}

/* ---- Use cases / onboarding --------------------------------------------- */

export type OnboardingStepStatus = 'done' | 'in_progress' | 'pending';

/** One step of the platform onboarding checklist for a use case. */
export interface OnboardingStep {
  key: string;
  title: string;
  description: string;
  status: OnboardingStepStatus;
}

/** An onboarded (or in-progress) use case (GET /usecases). */
export interface UseCase {
  slug: string;
  name: string;
  description: string | null;
  environment: Environment;
  status: 'active' | 'onboarding' | 'archived';
  owner: string | null;
  steps: OnboardingStep[];
}

/* ---- Health ------------------------------------------------------------- */

export interface HealthStatus {
  status: 'ok' | 'degraded' | 'down';
  environment: Environment;
  version: string;
  checks: Record<string, 'ok' | 'degraded' | 'down'>;
}

/* ---- Dashboard KPIs ----------------------------------------------------- */

export type TrendDirection = 'up' | 'down' | 'flat';

/** A single KPI value plus trend, used by the Dashboard tiles. */
export interface Kpi {
  key: string;
  label: string;
  value: number;
  unit: string;
  trend: TrendDirection;
  changePct: number;
}
