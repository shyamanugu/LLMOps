/** Evaluations page: recent gate reports plus a Run gate action. */
import { useState } from 'react';
import { PageHeader } from '../components/PageHeader';
import { AsyncSection } from '../components/AsyncSection';
import { DataTable, type Column } from '../components/DataTable';
import { Badge, MetricBadge } from '../components/MetricBadge';
import { useEvaluations, useRunEvaluation } from '../hooks/useEvaluations';
import { useUsecases } from '../hooks/useUsecases';
import { dateTime } from '../lib/format';
import type { GateReport, GateStatus } from '../api/types';

const STATUS_TONE: Record<GateStatus, 'success' | 'danger' | 'warning' | 'neutral'> = {
  pass: 'success',
  fail: 'danger',
  running: 'warning',
  error: 'danger',
};

function RunPanel(): JSX.Element {
  const usecases = useUsecases();
  const run = useRunEvaluation();
  const options = usecases.data?.data.map((u) => u.slug) ?? ['apix', 'hiring'];
  const [usecase, setUsecase] = useState<string>(options[0] ?? 'apix');
  const [scope, setScope] = useState<'subset' | 'full'>('subset');

  const result = run.data?.data;

  return (
    <section className="card">
      <div className="card__header">
        <h2 className="card__title">Run evaluation gate</h2>
      </div>
      <div className="card__body">
        <div className="row" style={{ flexWrap: 'wrap' }}>
          <label className="topbar__env">
            <span className="field__label">Use case</span>
            <select value={usecase} onChange={(e) => setUsecase(e.target.value)}>
              {options.map((o) => (
                <option key={o} value={o}>
                  {o}
                </option>
              ))}
            </select>
          </label>
          <label className="topbar__env">
            <span className="field__label">Scope</span>
            <select
              value={scope}
              onChange={(e) => setScope(e.target.value === 'full' ? 'full' : 'subset')}
            >
              <option value="subset">subset</option>
              <option value="full">full</option>
            </select>
          </label>
          <button
            type="button"
            className="btn btn--primary"
            disabled={run.isPending}
            onClick={() => run.mutate({ usecase, scope })}
          >
            {run.isPending ? 'Starting…' : 'Run gate'}
          </button>
          {result ? (
            <span className="row">
              <Badge tone={STATUS_TONE[result.status]}>{result.status}</Badge>
              <span className="muted mono">task {result.task_id}</span>
            </span>
          ) : null}
        </div>
        {run.data?.isPlaceholder ? (
          <p className="muted" style={{ marginTop: 12 }}>
            Runner not wired — this run was simulated locally (see todo.html).
          </p>
        ) : null}
      </div>
    </section>
  );
}

export function Evaluations(): JSX.Element {
  const query = useEvaluations();

  const columns: ReadonlyArray<Column<GateReport>> = [
    { id: 'usecase', header: 'Use case', render: (r) => <strong>{r.usecase}</strong> },
    { id: 'status', header: 'Status', render: (r) => <Badge tone={STATUS_TONE[r.status]}>{r.status}</Badge> },
    { id: 'scope', header: 'Scope', render: (r) => (r.subset ? 'subset' : 'full') },
    {
      id: 'cases',
      header: 'Cases',
      numeric: true,
      render: (r) => `${r.cases_passed}/${r.cases_total}`,
    },
    {
      id: 'metrics',
      header: 'Metrics',
      render: (r) => (
        <span className="chip-row">
          {r.metrics.map((m) => (
            <MetricBadge key={m.name} name={m.name} score={m.score} threshold={m.threshold} passed={m.passed} />
          ))}
        </span>
      ),
    },
    { id: 'commit', header: 'Commit', render: (r) => <span className="mono">{r.commit_sha ?? '—'}</span> },
    { id: 'finished', header: 'Finished', render: (r) => (r.finished_at ? dateTime(r.finished_at) : '—') },
  ];

  return (
    <>
      <PageHeader
        title="Evaluations"
        subtitle="Gate reports block CI when metrics fall below absolute floors or baseline-relative thresholds."
      />
      <div className="stack">
        <RunPanel />
        <section className="card">
          <div className="card__header">
            <h2 className="card__title">Recent gate reports</h2>
          </div>
          <div className="card__body">
            <AsyncSection query={query} loadingLabel="Loading gate reports…">
              {(rows) => (
                <DataTable
                  columns={columns}
                  rows={rows}
                  rowKey={(r) => r.id}
                  caption="Gate reports"
                  emptyTitle="No gate reports"
                />
              )}
            </AsyncSection>
          </div>
        </section>
      </div>
    </>
  );
}
