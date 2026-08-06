/** Guardrails page: configured guards and their recent events. */
import { PageHeader } from '../components/PageHeader';
import { AsyncSection } from '../components/AsyncSection';
import { DataTable, type Column } from '../components/DataTable';
import { Badge } from '../components/MetricBadge';
import { useGuardrails } from '../hooks/useGuardrails';
import { dateTime, shortId } from '../lib/format';
import type { GuardOutcome, GuardrailConfig, GuardrailEvent, GuardrailsReport } from '../api/types';

const OUTCOME_TONE: Record<GuardOutcome, 'success' | 'danger' | 'warning'> = {
  allowed: 'success',
  blocked: 'danger',
  redacted: 'warning',
};

function GuardrailsBody({ report }: { report: GuardrailsReport }): JSX.Element {
  const configColumns: ReadonlyArray<Column<GuardrailConfig>> = [
    { id: 'name', header: 'Guard', render: (c) => <strong>{c.name}</strong> },
    { id: 'category', header: 'Category', render: (c) => <Badge tone="neutral">{c.category}</Badge> },
    { id: 'stage', header: 'Stage', render: (c) => c.stage },
    { id: 'provider', header: 'Provider', render: (c) => <span className="muted">{c.provider}</span> },
    {
      id: 'enabled',
      header: 'Enabled',
      render: (c) => <Badge tone={c.enabled ? 'success' : 'danger'}>{c.enabled ? 'on' : 'off'}</Badge>,
    },
  ];

  const eventColumns: ReadonlyArray<Column<GuardrailEvent>> = [
    { id: 'outcome', header: 'Outcome', render: (e) => <Badge tone={OUTCOME_TONE[e.outcome]}>{e.outcome}</Badge> },
    { id: 'guard', header: 'Guard', render: (e) => e.guard },
    { id: 'category', header: 'Category', render: (e) => <Badge tone="neutral">{e.category}</Badge> },
    { id: 'detail', header: 'Detail', render: (e) => <span className="muted">{e.detail ?? '—'}</span> },
    {
      id: 'trace',
      header: 'Trace',
      render: (e) => (e.trace_id ? <span className="mono">{shortId(e.trace_id, 10)}</span> : '—'),
    },
    { id: 'ts', header: 'When', render: (e) => dateTime(e.ts) },
  ];

  return (
    <div className="stack">
      <section className="card">
        <div className="card__header">
          <h2 className="card__title">Configured guards</h2>
        </div>
        <div className="card__body">
          <DataTable columns={configColumns} rows={report.configs} rowKey={(c) => c.name} caption="Guardrail config" />
        </div>
      </section>
      <section className="card">
        <div className="card__header">
          <h2 className="card__title">Recent events</h2>
        </div>
        <div className="card__body">
          <DataTable
            columns={eventColumns}
            rows={report.events}
            rowKey={(e) => e.id}
            caption="Guardrail events"
            emptyTitle="No guardrail events"
          />
        </div>
      </section>
    </div>
  );
}

export function Guardrails(): JSX.Element {
  const query = useGuardrails();
  return (
    <>
      <PageHeader
        title="Guardrails"
        subtitle="Ordered input/output guards: injection, content safety, PII and schema validation."
      />
      <AsyncSection query={query} loadingLabel="Loading guardrails…">
        {(report) => <GuardrailsBody report={report} />}
      </AsyncSection>
    </>
  );
}
