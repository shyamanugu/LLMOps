/** Traces list page. */
import { useNavigate } from 'react-router-dom';
import { PageHeader } from '../components/PageHeader';
import { AsyncSection } from '../components/AsyncSection';
import { DataTable, type Column } from '../components/DataTable';
import { Badge } from '../components/MetricBadge';
import { useTraces } from '../hooks/useTraces';
import { dateTime, ms, usd, count, shortId } from '../lib/format';
import type { TraceSummary } from '../api/types';

export function Traces(): JSX.Element {
  const query = useTraces();
  const navigate = useNavigate();

  const columns: ReadonlyArray<Column<TraceSummary>> = [
    { id: 'trace', header: 'Trace', render: (t) => <span className="mono">{shortId(t.trace_id, 12)}</span> },
    { id: 'name', header: 'Pipeline', render: (t) => t.name },
    { id: 'usecase', header: 'Use case', render: (t) => t.usecase ?? '—' },
    {
      id: 'status',
      header: 'Status',
      render: (t) => <Badge tone={t.status === 'error' ? 'danger' : 'success'}>{t.status}</Badge>,
    },
    { id: 'duration', header: 'Duration', numeric: true, render: (t) => ms(t.duration_ms) },
    { id: 'spans', header: 'Spans', numeric: true, render: (t) => count(t.span_count) },
    { id: 'tokens', header: 'Tokens', numeric: true, render: (t) => count(t.total_tokens) },
    { id: 'cost', header: 'Cost', numeric: true, render: (t) => usd(t.cost_usd) },
    { id: 'start', header: 'Started', render: (t) => dateTime(t.start_time) },
  ];

  return (
    <>
      <PageHeader
        title="Traces"
        subtitle="Read-through of App Insights / Langfuse traces. Select a trace to inspect its span tree."
      />
      <section className="card">
        <div className="card__body">
          <AsyncSection query={query} loadingLabel="Loading traces…">
            {(rows) => (
              <DataTable
                columns={columns}
                rows={rows}
                rowKey={(t) => t.trace_id}
                onRowClick={(t) => navigate(`/traces/${encodeURIComponent(t.trace_id)}`)}
                caption="Recent traces"
                emptyTitle="No traces available"
              />
            )}
          </AsyncSection>
        </div>
      </section>
    </>
  );
}
