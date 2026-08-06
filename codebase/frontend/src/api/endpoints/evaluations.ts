/** Evaluation gate endpoints (GET /evaluations, POST /evaluations/run). */
import { getJson, postJson, withPlaceholder, type Resulted } from '../client';
import type {
  EvaluationRunRequest,
  EvaluationRunResponse,
  GateReport,
} from '../types';

function reports(): GateReport[] {
  return [
    {
      id: 'gate-2041',
      usecase: 'apix',
      status: 'pass',
      subset: false,
      cases_total: 48,
      cases_passed: 47,
      metrics: [
        { name: 'groundedness', score: 0.94, threshold: 0.85, passed: true, detail: 'Ragas' },
        { name: 'answer_relevance', score: 0.91, threshold: 0.8, passed: true, detail: 'Ragas' },
        { name: 'tool_selection', score: 0.97, threshold: 0.9, passed: true, detail: 'trace-derived' },
        { name: 'writing_quality', score: 0.88, threshold: 0.75, passed: true, detail: 'G-Eval' },
      ],
      started_at: '2026-08-06T08:12:00Z',
      finished_at: '2026-08-06T08:19:40Z',
      commit_sha: '9f2a1c7',
    },
    {
      id: 'gate-2040',
      usecase: 'hiring',
      status: 'fail',
      subset: false,
      cases_total: 60,
      cases_passed: 52,
      metrics: [
        { name: 'groundedness', score: 0.9, threshold: 0.85, passed: true, detail: 'Ragas' },
        { name: 'bias_check', score: 0.71, threshold: 0.8, passed: false, detail: 'custom judge' },
        { name: 'fit_accuracy', score: 0.83, threshold: 0.8, passed: true, detail: 'golden' },
      ],
      started_at: '2026-08-06T07:40:00Z',
      finished_at: '2026-08-06T07:52:10Z',
      commit_sha: '3b7e0aa',
    },
    {
      id: 'gate-2039',
      usecase: 'apix',
      status: 'pass',
      subset: true,
      cases_total: 12,
      cases_passed: 12,
      metrics: [
        { name: 'groundedness', score: 0.95, threshold: 0.85, passed: true, detail: 'Ragas' },
        { name: 'answer_relevance', score: 0.9, threshold: 0.8, passed: true, detail: 'Ragas' },
      ],
      started_at: '2026-08-05T16:02:00Z',
      finished_at: '2026-08-05T16:04:30Z',
      commit_sha: 'c11d934',
    },
  ];
}

/** List recent gate reports. */
export function fetchEvaluations(): Promise<Resulted<GateReport[]>> {
  return withPlaceholder(() => getJson<GateReport[]>('/evaluations'), reports);
}

/** Trigger a gate run for a use case (async task on the backend). */
export function runEvaluation(
  req: EvaluationRunRequest,
): Promise<Resulted<EvaluationRunResponse>> {
  return withPlaceholder(
    () =>
      postJson<EvaluationRunResponse>('/evaluations/run', {
        usecase: req.usecase,
        scope: req.scope,
      }),
    () => ({
      task_id: `placeholder-${Date.now()}`,
      usecase: req.usecase,
      status: 'running',
      accepted: true,
    }),
    'Evaluation runner is not wired yet — this run was simulated locally.',
  );
}
