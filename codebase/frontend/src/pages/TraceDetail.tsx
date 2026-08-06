/** Trace detail: header stats plus the nested span tree. */
import { Link, useParams } from 'react-router-dom';
import { PageHeader } from '../components/PageHeader';
import { AsyncSection } from '../components/AsyncSection';
import { SpanTree } from '../components/SpanTree';
import { StatTile } from '../components/StatTile';
import { Badge } from '../components/MetricBadge';
import { useTrace } from '../hooks/useTraces';
import { ms, usd, count } from '../lib/format';

export function TraceDetail(): JSX.Element {
  const { id = '' } = useParams();
  const query = useTrace(id);

  return (
    <>
      <PageHeader
        title="Trace"
        subtitle={id}
        actions={
          <Link to="/traces" className="btn btn--secondary btn--sm">
            Back to traces
          </Link>
        }
      />
      <AsyncSection query={query} loadingLabel="Loading trace…">
        {(trace) => (
          <div className="stack">
            <div className="grid grid--kpis">
              <StatTile label="Status" value={trace.status} />
              <StatTile label="Duration" value={ms(trace.duration_ms)} />
              <StatTile label="Total tokens" value={count(trace.total_tokens)} />
              <StatTile label="Cost" value={usd(trace.cost_usd)} />
            </div>
            <section className="card">
              <div className="card__header">
                <h2 className="card__title">Span tree</h2>
                <span className="row">
                  <span className="muted">{trace.name}</span>
                  {trace.usecase ? <Badge tone="info">{trace.usecase}</Badge> : null}
                </span>
              </div>
              <div className="card__body">
                <SpanTree root={trace.root} />
              </div>
            </section>
          </div>
        )}
      </AsyncSection>
    </>
  );
}
