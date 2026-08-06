/** Agents / pipelines endpoint (GET /agents). */
import { getJson, withPlaceholder, type Resulted } from '../client';
import type { PipelineDef } from '../types';

function pipelines(): PipelineDef[] {
  return [
    {
      name: 'apix.pipeline',
      usecase: 'apix',
      description: 'Support ticket triage and summarisation (sequential, not A2A).',
      agents: [
        {
          name: 'triage',
          role: 'Classify ticket category and urgency',
          prompt_id: 'apix.triage',
          model_alias: 'reason',
          tools: ['search_knowledge', 'get_record'],
        },
        {
          name: 'summarize',
          role: 'Summarise the thread for the agent queue',
          prompt_id: 'apix.summarize',
          model_alias: 'bulk',
          tools: [],
        },
      ],
    },
    {
      name: 'hiring.pipeline',
      usecase: 'hiring',
      description: 'Resume screening against a job description with bias checks.',
      agents: [
        {
          name: 'extract',
          role: 'Extract structured resume fields',
          prompt_id: 'hiring.extract',
          model_alias: 'bulk',
          tools: ['extract_document'],
        },
        {
          name: 'screen',
          role: 'Score candidate fit 0-100 with rationale',
          prompt_id: 'hiring.screen',
          model_alias: 'reason',
          tools: ['query_sql'],
        },
      ],
    },
  ];
}

/** List pipelines/agents defined under each usecase's agents directory. */
export function fetchAgents(): Promise<Resulted<PipelineDef[]>> {
  return withPlaceholder(() => getJson<PipelineDef[]>('/agents'), pipelines);
}
