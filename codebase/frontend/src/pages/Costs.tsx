/** Costs page: spend broken down by day, use case and model. */
import { PageHeader } from '../components/PageHeader';
import { AsyncSection } from '../components/AsyncSection';
import { StatTile } from '../components/StatTile';
import { DataTable, type Column } from '../components/DataTable';
import { useCosts } from '../hooks/useCosts';
import { usd, count } from '../lib/format';
import type { CostAggregate, CostReport } from '../api/types';

/** Horizontal CSS bar for a value relative to the group's max. */
function Bar({ value, max }: { value: number; max: number }): JSX.Element {
  const pct = max > 0 ? Math.round((value / max) * 100) : 0;
  return (
    <div style={{ background: 'var(--gray-100)', borderRadius: 4, overflow: 'hidden' }}>
      <div
        style={{
          width: `${pct}%`,
          background: 'var(--teal)',
          height: 8,
          borderRadius: 4,
        }}
        aria-hidden="true"
      />
    </div>
  );
}

function BreakdownCard({
  title,
  rows,
}: {
  title: string;
  rows: CostAggregate[];
}): JSX.Element {
  const max = Math.max(0, ...rows.map((r) => r.cost_usd));
  const columns: ReadonlyArray<Column<CostAggregate>> = [
    { id: 'key', header: title, render: (r) => <strong>{r.key}</strong> },
    { id: 'cost', header: 'Cost', numeric: true, render: (r) => usd(r.cost_usd) },
    { id: 'bar', header: 'Share', width: '30%', render: (r) => <Bar value={r.cost_usd} max={max} /> },
    { id: 'requests', header: 'Requests', numeric: true, render: (r) => count(r.requests) },
  ];
  return (
    <section className="card">
      <div className="card__header">
        <h2 className="card__title">By {title}</h2>
      </div>
      <div className="card__body">
        <DataTable columns={columns} rows={rows} rowKey={(r) => r.key} caption={`Cost by ${title}`} />
      </div>
    </section>
  );
}

function CostBody({ report }: { report: CostReport }): JSX.Element {
  const avgPerDay = report.window_days > 0 ? report.total_usd / report.window_days : 0;
  return (
    <div className="stack">
      <div className="grid grid--kpis">
        <StatTile label={`Total (${report.window_days}d)`} value={usd(report.total_usd)} />
        <StatTile label="Avg / day" value={usd(avgPerDay)} />
        <StatTile label="Use cases" value={String(report.by_usecase.length)} />
        <StatTile label="Models" value={String(report.by_model.length)} />
      </div>
      <BreakdownCard title="day" rows={report.by_day} />
      <div className="grid grid--two">
        <BreakdownCard title="usecase" rows={report.by_usecase} />
        <BreakdownCard title="model" rows={report.by_model} />
      </div>
    </div>
  );
}

export function Costs(): JSX.Element {
  const query = useCosts(7);
  return (
    <>
      <PageHeader title="Costs" subtitle="Spend aggregated by day, use case and model." />
      <AsyncSection query={query} loadingLabel="Loading cost aggregates…">
        {(report) => <CostBody report={report} />}
      </AsyncSection>
    </>
  );
}
