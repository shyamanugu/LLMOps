/**
 * Trace endpoints (GET /traces, GET /traces/{id}).
 *
 * These are read-through to App Insights / Langfuse and are a TODO on the
 * backend (ARCHITECTURE_SPEC §3), so the console will typically show clearly
 * labelled placeholder traces here.
 */
import { getJson, withPlaceholder, type Resulted } from '../client';
import type { Span, TraceDetail, TraceSummary } from '../types';

function summaries(): TraceSummary[] {
  return [
    {
      trace_id: 'a1b2c3d4e5f60718293a4b5c6d7e8f90',
      name: 'apix.pipeline',
      usecase: 'apix',
      status: 'ok',
      start_time: '2026-08-06T09:41:12Z',
      duration_ms: 3820,
      span_count: 7,
      cost_usd: 0.0142,
      total_tokens: 5120,
    },
    {
      trace_id: 'b2c3d4e5f60718293a4b5c6d7e8f9012',
      name: 'hiring.pipeline',
      usecase: 'hiring',
      status: 'error',
      start_time: '2026-08-06T09:38:55Z',
      duration_ms: 5210,
      span_count: 9,
      cost_usd: 0.0231,
      total_tokens: 7340,
    },
    {
      trace_id: 'c3d4e5f60718293a4b5c6d7e8f901234',
      name: 'apix.pipeline',
      usecase: 'apix',
      status: 'ok',
      start_time: '2026-08-06T09:35:02Z',
      duration_ms: 2960,
      span_count: 6,
      cost_usd: 0.0108,
      total_tokens: 4010,
    },
  ];
}

function sampleTree(traceId: string): Span {
  return {
    span_id: 'root',
    parent_id: null,
    name: 'apix.pipeline',
    kind: 'request',
    status: 'ok',
    start_time: '2026-08-06T09:41:12Z',
    duration_ms: 3820,
    attributes: { 'usecase': 'apix', 'trace_id': traceId },
    cost_usd: 0.0142,
    tokens: 5120,
    children: [
      {
        span_id: 'guard-in',
        parent_id: 'root',
        name: 'guardrail.input',
        kind: 'guardrail',
        status: 'ok',
        start_time: '2026-08-06T09:41:12Z',
        duration_ms: 120,
        attributes: { 'guard': 'injection', 'outcome': 'allowed' },
        cost_usd: null,
        tokens: null,
        children: [],
      },
      {
        span_id: 'agent-triage',
        parent_id: 'root',
        name: 'agent.triage',
        kind: 'agent',
        status: 'ok',
        start_time: '2026-08-06T09:41:12Z',
        duration_ms: 2100,
        attributes: { 'role': 'triage', 'prompt_id': 'apix.triage' },
        cost_usd: 0.0091,
        tokens: 3200,
        children: [
          {
            span_id: 'tool-search',
            parent_id: 'agent-triage',
            name: 'tool.search_knowledge',
            kind: 'tool',
            status: 'ok',
            start_time: '2026-08-06T09:41:12Z',
            duration_ms: 340,
            attributes: { 'mcp_server': 'rag', 'was_correct_tool': true, 'k': 5 },
            cost_usd: null,
            tokens: null,
            children: [],
          },
          {
            span_id: 'model-reason',
            parent_id: 'agent-triage',
            name: 'model.reason',
            kind: 'model',
            status: 'ok',
            start_time: '2026-08-06T09:41:13Z',
            duration_ms: 1600,
            attributes: {
              'alias': 'reason',
              'deployment': 'gpt-5-mini',
              'prompt_id': 'apix.triage',
              'prompt_version': 4,
            },
            cost_usd: 0.0091,
            tokens: 3200,
            children: [],
          },
        ],
      },
      {
        span_id: 'agent-summary',
        parent_id: 'root',
        name: 'agent.summarize',
        kind: 'agent',
        status: 'ok',
        start_time: '2026-08-06T09:41:15Z',
        duration_ms: 1300,
        attributes: { 'role': 'summarize', 'prompt_id': 'apix.summarize' },
        cost_usd: 0.0051,
        tokens: 1920,
        children: [
          {
            span_id: 'model-bulk',
            parent_id: 'agent-summary',
            name: 'model.bulk',
            kind: 'model',
            status: 'ok',
            start_time: '2026-08-06T09:41:15Z',
            duration_ms: 1200,
            attributes: { 'alias': 'bulk', 'deployment': 'gpt-5-mini', 'prompt_id': 'apix.summarize' },
            cost_usd: 0.0051,
            tokens: 1920,
            children: [],
          },
        ],
      },
      {
        span_id: 'guard-out',
        parent_id: 'root',
        name: 'guardrail.output',
        kind: 'guardrail',
        status: 'ok',
        start_time: '2026-08-06T09:41:16Z',
        duration_ms: 90,
        attributes: { 'guard': 'pii', 'outcome': 'redacted' },
        cost_usd: null,
        tokens: null,
        children: [],
      },
    ],
  };
}

function detail(traceId: string): TraceDetail {
  return {
    trace_id: traceId,
    name: 'apix.pipeline',
    usecase: 'apix',
    status: 'ok',
    start_time: '2026-08-06T09:41:12Z',
    duration_ms: 3820,
    cost_usd: 0.0142,
    total_tokens: 5120,
    root: sampleTree(traceId),
  };
}

const TRACE_NOTE =
  'Trace read-through (App Insights / Langfuse) is a TODO on the backend — showing placeholder spans.';

/** List recent traces. */
export function fetchTraces(): Promise<Resulted<TraceSummary[]>> {
  return withPlaceholder(() => getJson<TraceSummary[]>('/traces'), summaries, TRACE_NOTE);
}

/** Fetch a single trace tree by id. */
export function fetchTrace(traceId: string): Promise<Resulted<TraceDetail>> {
  return withPlaceholder(
    () => getJson<TraceDetail>(`/traces/${encodeURIComponent(traceId)}`),
    () => detail(traceId),
    TRACE_NOTE,
  );
}
