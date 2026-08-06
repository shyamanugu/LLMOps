/** Guardrails endpoint (GET /guardrails). */
import { getJson, withPlaceholder, type Resulted } from '../client';
import type { GuardrailsReport } from '../types';

function placeholder(): GuardrailsReport {
  return {
    configs: [
      { name: 'prompt_injection', category: 'injection', stage: 'input', enabled: true, provider: 'Azure Prompt Shields' },
      { name: 'content_safety', category: 'harm', stage: 'both', enabled: true, provider: 'Azure Content Safety' },
      { name: 'pii_redaction', category: 'pii', stage: 'output', enabled: true, provider: 'Presidio / Azure Language' },
      { name: 'schema_validation', category: 'schema', stage: 'output', enabled: true, provider: 'pydantic / json-schema' },
    ],
    events: [
      { id: 'ev-501', guard: 'pii_redaction', category: 'pii', outcome: 'redacted', detail: 'Redacted 1 email address', trace_id: 'a1b2c3d4e5f60718293a4b5c6d7e8f90', ts: '2026-08-06T09:41:16Z' },
      { id: 'ev-500', guard: 'prompt_injection', category: 'injection', outcome: 'blocked', detail: 'Detected instruction override attempt', trace_id: 'd4e5f60718293a4b5c6d7e8f90123456', ts: '2026-08-06T09:37:44Z' },
      { id: 'ev-499', guard: 'content_safety', category: 'harm', outcome: 'allowed', detail: 'Severity below threshold', trace_id: 'c3d4e5f60718293a4b5c6d7e8f901234', ts: '2026-08-06T09:35:10Z' },
      { id: 'ev-498', guard: 'schema_validation', category: 'schema', outcome: 'blocked', detail: 'Output failed JSON contract, retried', trace_id: 'b2c3d4e5f60718293a4b5c6d7e8f9012', ts: '2026-08-06T09:33:02Z' },
    ],
  };
}

/** Fetch configured guardrails and their recent events. */
export function fetchGuardrails(): Promise<Resulted<GuardrailsReport>> {
  return withPlaceholder(() => getJson<GuardrailsReport>('/guardrails'), placeholder);
}
