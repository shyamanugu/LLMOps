/** Health endpoint (GET /health). */
import { getJson, withPlaceholder, type Resulted } from '../client';
import type { HealthStatus } from '../types';

function placeholder(): HealthStatus {
  return {
    status: 'degraded',
    environment: 'dev',
    version: '0.1.0',
    checks: {
      api: 'ok',
      tracing: 'degraded',
      registry: 'ok',
      models: 'degraded',
    },
  };
}

/** Fetch platform health; falls back to a placeholder when unreachable. */
export function fetchHealth(): Promise<Resulted<HealthStatus>> {
  return withPlaceholder(
    () => getJson<HealthStatus>('/health'),
    placeholder,
    'API is unreachable — showing placeholder health.',
  );
}
