/** Cost aggregation endpoint (GET /costs). */
import { getJson, withPlaceholder, type Resulted } from '../client';
import type { CostAggregate, CostReport } from '../types';

function placeholder(): CostReport {
  const by_day: CostAggregate[] = [
    { dimension: 'day', key: '2026-07-31', cost_usd: 41.22, requests: 3120, input_tokens: 1_820_000, output_tokens: 610_000 },
    { dimension: 'day', key: '2026-08-01', cost_usd: 38.9, requests: 2980, input_tokens: 1_740_000, output_tokens: 590_000 },
    { dimension: 'day', key: '2026-08-02', cost_usd: 22.14, requests: 1610, input_tokens: 980_000, output_tokens: 300_000 },
    { dimension: 'day', key: '2026-08-03', cost_usd: 19.8, requests: 1490, input_tokens: 900_000, output_tokens: 280_000 },
    { dimension: 'day', key: '2026-08-04', cost_usd: 47.31, requests: 3410, input_tokens: 2_010_000, output_tokens: 680_000 },
    { dimension: 'day', key: '2026-08-05', cost_usd: 52.06, requests: 3720, input_tokens: 2_180_000, output_tokens: 740_000 },
    { dimension: 'day', key: '2026-08-06', cost_usd: 33.47, requests: 2440, input_tokens: 1_420_000, output_tokens: 480_000 },
  ];
  const by_usecase: CostAggregate[] = [
    { dimension: 'usecase', key: 'apix', cost_usd: 168.4, requests: 12_900, input_tokens: 7_400_000, output_tokens: 2_500_000 },
    { dimension: 'usecase', key: 'hiring', cost_usd: 86.5, requests: 5_870, input_tokens: 3_650_000, output_tokens: 1_080_000 },
  ];
  const by_model: CostAggregate[] = [
    { dimension: 'model', key: 'gpt-5.2', cost_usd: 141.2, requests: 6_100, input_tokens: 3_900_000, output_tokens: 1_600_000 },
    { dimension: 'model', key: 'gpt-5-mini', cost_usd: 92.7, requests: 11_400, input_tokens: 6_200_000, output_tokens: 1_700_000 },
    { dimension: 'model', key: 'text-embedding-3-large', cost_usd: 21.0, requests: 1_270, input_tokens: 950_000, output_tokens: 0 },
  ];
  const total_usd = by_day.reduce((sum, d) => sum + d.cost_usd, 0);
  return { total_usd, window_days: by_day.length, by_day, by_usecase, by_model };
}

/** Fetch cost aggregates grouped by day, use case and model. */
export function fetchCosts(windowDays = 7): Promise<Resulted<CostReport>> {
  return withPlaceholder(
    () => getJson<CostReport>('/costs', { window_days: windowDays }),
    placeholder,
  );
}
