/** Prompt registry endpoints (GET /prompts, GET /prompts/{id}, POST /prompts/{id}/render). */
import { getJson, postJson, withPlaceholder, type Resulted } from '../client';
import type { JsonValue, PromptSpec, PromptSummary, RenderResult } from '../types';

const SAMPLE_SPECS: PromptSpec[] = [
  {
    id: 'apix.triage',
    version: 4,
    labels: ['prod', 'reason'],
    model_alias: 'reason',
    temperature: 0.2,
    inputs: ['ticket_subject', 'ticket_body'],
    template:
      'You are a support triage assistant.\n\nClassify the ticket into a category and urgency.\n\nSubject: {{ticket_subject}}\nBody: {{ticket_body}}\n\nRespond as strict JSON: {"category": "...", "urgency": "low|medium|high"}.',
    eval_refs: ['apix.triage.golden', 'apix.triage.rubric'],
    changelog: [
      'v4: tightened JSON contract, added urgency floor',
      'v3: added few-shot examples',
      'v2: switched to reason alias',
    ],
  },
  {
    id: 'apix.summarize',
    version: 2,
    labels: ['prod', 'bulk'],
    model_alias: 'bulk',
    temperature: 0.3,
    inputs: ['thread'],
    template:
      'Summarize the following support thread in 3 bullet points, neutral tone.\n\n{{thread}}',
    eval_refs: ['apix.summarize.golden'],
    changelog: ['v2: cap at 3 bullets', 'v1: initial'],
  },
  {
    id: 'hiring.screen',
    version: 6,
    labels: ['prod', 'staging', 'reason'],
    model_alias: 'reason',
    temperature: 0.1,
    inputs: ['job_desc', 'resume'],
    template:
      'Evaluate the candidate resume against the job description.\n\nJob: {{job_desc}}\nResume: {{resume}}\n\nReturn a structured assessment with a 0-100 fit score and rationale.',
    eval_refs: ['hiring.screen.golden', 'hiring.screen.rubric', 'hiring.bias.check'],
    changelog: [
      'v6: added bias guardrail reference',
      'v5: JSON schema tightened',
      'v4: rubric refresh',
    ],
  },
];

function summaries(): PromptSummary[] {
  return SAMPLE_SPECS.map((s) => ({
    id: s.id,
    version: s.version,
    labels: s.labels,
    model_alias: s.model_alias,
  }));
}

/** List all prompts. */
export function fetchPrompts(): Promise<Resulted<PromptSummary[]>> {
  return withPlaceholder(() => getJson<PromptSummary[]>('/prompts'), summaries);
}

/** Fetch a single prompt spec by id. */
export function fetchPrompt(id: string): Promise<Resulted<PromptSpec>> {
  return withPlaceholder(
    () => getJson<PromptSpec>(`/prompts/${encodeURIComponent(id)}`),
    () => {
      const found = SAMPLE_SPECS.find((s) => s.id === id);
      if (found) return found;
      return { ...SAMPLE_SPECS[0], id };
    },
  );
}

/** Render a prompt with variables (dev helper). */
export function renderPrompt(
  id: string,
  vars: Record<string, JsonValue>,
): Promise<Resulted<RenderResult>> {
  return withPlaceholder(
    () => postJson<RenderResult>(`/prompts/${encodeURIComponent(id)}/render`, vars),
    () => ({
      prompt_id: id,
      rendered: `[placeholder render for ${id}]\n\n${JSON.stringify(vars, null, 2)}`,
    }),
  );
}
