/** Model catalog endpoint (GET /models). */
import { getJson, withPlaceholder, type Resulted } from '../client';
import type { Environment, ModelAlias } from '../types';

/** Mirrors platform/models.yaml aliases resolved for the dev environment. */
function placeholder(env: Environment = 'dev'): ModelAlias[] {
  const deployments: Record<string, { dev: string; test: string; prod: string; kind: string; desc: string }> = {
    reason: { dev: 'gpt-5-mini', test: 'gpt-5-mini', prod: 'gpt-5.2', kind: 'chat', desc: 'High-reasoning default for complex steps.' },
    bulk: { dev: 'gpt-5-mini', test: 'gpt-5-mini', prod: 'gpt-5-mini', kind: 'chat', desc: 'Cheap/fast for bulk classification & summaries.' },
    judge: { dev: 'gpt-5-mini', test: 'gpt-5-mini', prod: 'gpt-5-mini', kind: 'chat', desc: 'LLM-as-judge for evaluation rubrics.' },
    voice: { dev: 'gpt-realtime-1.5', test: 'gpt-realtime-1.5', prod: 'gpt-realtime-1.5', kind: 'realtime', desc: 'Realtime voice interactions.' },
    embed: { dev: 'text-embedding-3-large', test: 'text-embedding-3-large', prod: 'text-embedding-3-large', kind: 'embedding', desc: 'Dense retrieval embeddings.' },
  };
  return Object.entries(deployments).map(([alias, d]) => ({
    alias,
    deployment: d[env],
    environment: env,
    kind: d.kind,
    description: d.desc,
  }));
}

/** List model aliases resolved to deployments for an environment. */
export function fetchModels(env?: Environment): Promise<Resulted<ModelAlias[]>> {
  return withPlaceholder(
    () => getJson<ModelAlias[]>('/models', { env }),
    () => placeholder(env),
  );
}
