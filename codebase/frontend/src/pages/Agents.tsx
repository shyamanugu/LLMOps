/** Agents page: pipelines and their sequential agent steps. */
import { PageHeader } from '../components/PageHeader';
import { AsyncSection } from '../components/AsyncSection';
import { Badge } from '../components/MetricBadge';
import { useAgents } from '../hooks/useAgents';
import type { PipelineDef } from '../api/types';

function PipelineCard({ pipeline }: { pipeline: PipelineDef }): JSX.Element {
  return (
    <section className="card">
      <div className="card__header">
        <h2 className="card__title">{pipeline.name}</h2>
        <Badge tone="info">{pipeline.usecase}</Badge>
      </div>
      <div className="card__body stack">
        {pipeline.description ? <p className="muted">{pipeline.description}</p> : null}
        <ol style={{ margin: 0, paddingLeft: 18 }}>
          {pipeline.agents.map((agent) => (
            <li key={agent.name} style={{ marginBottom: 12 }}>
              <div className="row" style={{ flexWrap: 'wrap' }}>
                <strong>{agent.name}</strong>
                <Badge tone="success">{agent.model_alias}</Badge>
                <span className="mono muted">{agent.prompt_id}</span>
              </div>
              <div className="muted">{agent.role}</div>
              {agent.tools.length > 0 ? (
                <div className="chip-row" style={{ marginTop: 4 }}>
                  {agent.tools.map((t) => (
                    <Badge key={t} tone="neutral">
                      {t}
                    </Badge>
                  ))}
                </div>
              ) : null}
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}

export function Agents(): JSX.Element {
  const query = useAgents();
  return (
    <>
      <PageHeader
        title="Agents"
        subtitle="Pipelines compose agents sequentially (not A2A), loaded from usecases/*/agents."
      />
      <AsyncSection query={query} loadingLabel="Loading pipelines…">
        {(pipelines) => (
          <div className="grid grid--two">
            {pipelines.map((p) => (
              <PipelineCard key={p.name} pipeline={p} />
            ))}
          </div>
        )}
      </AsyncSection>
    </>
  );
}
