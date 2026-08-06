/** Feedback endpoints (GET /feedback stream, POST /feedback). */
import { getJson, postJson, withPlaceholder, type Resulted } from '../client';
import type { FeedbackCreate, FeedbackEvent } from '../types';

function stream(): FeedbackEvent[] {
  return [
    {
      id: 'fb-9001',
      trace_id: 'a1b2c3d4e5f60718293a4b5c6d7e8f90',
      kind: 'thumbs',
      value: 'up',
      reason: null,
      user_hash: 'u_8f21',
      ts: '2026-08-06T09:42:00Z',
    },
    {
      id: 'fb-9000',
      trace_id: 'b2c3d4e5f60718293a4b5c6d7e8f9012',
      kind: 'edit',
      value: 'Corrected urgency from medium to high',
      reason: 'Customer flagged outage',
      user_hash: 'u_3a10',
      ts: '2026-08-06T09:39:20Z',
    },
    {
      id: 'fb-8999',
      trace_id: 'c3d4e5f60718293a4b5c6d7e8f901234',
      kind: 'override',
      value: 'rejected',
      reason: 'Model recommended wrong category',
      user_hash: 'u_77c2',
      ts: '2026-08-06T09:31:05Z',
    },
    {
      id: 'fb-8998',
      trace_id: 'a1b2c3d4e5f60718293a4b5c6d7e8f90',
      kind: 'thumbs',
      value: 'down',
      reason: 'Summary missed a key point',
      user_hash: 'u_1b44',
      ts: '2026-08-06T09:22:41Z',
    },
  ];
}

/** Fetch the recent feedback stream. */
export function fetchFeedback(): Promise<Resulted<FeedbackEvent[]>> {
  return withPlaceholder(() => getJson<FeedbackEvent[]>('/feedback'), stream);
}

/** Capture a new feedback event. */
export function captureFeedback(
  payload: FeedbackCreate,
): Promise<Resulted<FeedbackEvent>> {
  return withPlaceholder(
    () =>
      postJson<FeedbackEvent>('/feedback', {
        trace_id: payload.trace_id,
        kind: payload.kind,
        value: payload.value,
        reason: payload.reason ?? null,
      }),
    () => ({
      id: `placeholder-${Date.now()}`,
      trace_id: payload.trace_id,
      kind: payload.kind,
      value: payload.value,
      reason: payload.reason ?? null,
      user_hash: 'u_local',
      ts: new Date().toISOString(),
    }),
    'Feedback store is not wired yet — this event was recorded locally only.',
  );
}
