/** Dashboard: platform KPI tiles derived from costs, traces, evals, guardrails. */
import { Link } from 'react-router-dom';
import { PageHeader } from '../components/PageHeader';
import { StatTile } from '../components/StatTile';
import { LoadingState } from '../components/LoadingState';
import { PlaceholderBanner } from '../components/PlaceholderBanner';
import { MetricBadge, Badge } from '../components/MetricBadge';
import { useCosts } from '../hooks/useCosts';
import { useTraces } from '../hooks/useTraces';
import { useEvaluations } from '../hooks/useEvaluations';
import { useGuardrails } from '../hooks/useGuardrails';
import { usd, ms, count } from '../lib/format';

function p95(values: number[]): number {
  if (values.length === 0) return 0;
  const sorted = [...values].sort((a, b) => a - b);
  const idx = Math.min(sorted.length - 1, Math.ceil(0.95 * sorted.length) - 1);
  return sorted[idx];
}

export function Dashboard(): JSX.Element {
  const costs = useCosts();
  const traces = useTraces();
  const evals = useEvaluations();
  const guardrails = useGuardrails();

  const anyLoading =
    costs.isPending || traces.isPending || evals.isPending || guardrails.isPending;

  const anyPlaceholder =
    Boolean(costs.data?.isPlaceholder) ||
    Boolean(traces.data?.isPlaceholder) ||
    Boolean(evals.data?.isPlaceholder) ||
    Boolean(guardrails.data?.isPlaceholder);

  if (anyLoading) {
    return (
      <>
        <PageHeader title="Dashboard" subtitle="Platform health at a glance" />
        <LoadingState label="Loading platform KPIs…" />
      </>
    );
  }

  const report = costs.data?.data;
  const traceRows = traces.data?.data ?? [];
  const gateReports = evals.data?.data ?? [];
  const guardEvents = guardrails.data?.data.events ?? [];

  const costPerDay = report && report.by_day.length > 0
    ? report.by_day[report.by_day.length - 1].cost_usd
    : 0;
  const requestsToday = report && report.by_day.length > 0
    ? report.by_day[report.by_day.length - 1].requests
    : 0;
  const latencyP95 = p95(traceRows.map((t) => t.duration_ms));
  const blockedEvents = guardEvents.filter((e) => e.outcome !== 'allowed').length;
  const passRate =
    gateReports.length > 0
      ? gateReports.filter((r) => r.status === 'pass').length / gateReports.length
      : 0;

  const latest = gateReports[0];

  return (
    <>
      <PageHeader
        title="Dashboard"
        subtitle="Requests, latency, spend, quality and guardrail activity across the platform."
      />
      {anyPlaceholder ? (
        <PlaceholderBanner note="One or more KPIs are derived from placeholder data — connect the backend to see live values." />
      ) : null}

      <div className="grid grid--kpis" style={{ marginBottom: 20 }}>
        <StatTile
          label="Requests (today)"
          value={count(requestsToday)}
          trend="up"
          changePct={6.2}
          hint="vs prior day"
        />
        <StatTile label="p95 latency" value={ms(latencyP95)} trend="down" changePct={3.1} hint="recent traces" />
        <StatTile label="Cost / day" value={usd(costPerDay)} unit="" trend="up" changePct={4.8} hint="last day in window" />
        <StatTile
          label="Quality (gate pass)"
          value={`${Math.round(passRate * 100)}%`}
          trend={passRate >= 0.8 ? 'up' : 'down'}
          hint="recent gate reports"
        />
        <StatTile
          label="Guardrail events"
          value={count(blockedEvents)}
          trend="flat"
          hint="blocked/redacted"
        />
      </div>

      <div className="grid grid--two">
        <section className="card">
          <div className="card__header">
            <h2 className="card__title">Latest gate report</h2>
            <Link to="/evaluations" className="btn btn--ghost btn--sm">
              View all
            </Link>
          </div>
          <div className="card__body">
            {latest ? (
              <div className="stack">
                <div className="row row--between">
                  <div className="row">
                    <strong>{latest.usecase}</strong>
                    <Badge tone={latest.status === 'pass' ? 'success' : 'danger'}>
                      {latest.status}
                    </Badge>
                    <span className="muted">
                      {latest.cases_passed}/{latest.cases_total} cases
                    </span>
                  </div>
                </div>
                <div className="chip-row">
                  {latest.metrics.map((m) => (
                    <MetricBadge
                      key={m.name}
                      name={m.name}
                      score={m.score}
                      threshold={m.threshold}
                      passed={m.passed}
                    />
                  ))}
                </div>
              </div>
            ) : (
              <p className="muted">No gate reports yet.</p>
            )}
          </div>
        </section>

        <section className="card">
          <div className="card__header">
            <h2 className="card__title">Recent guardrail activity</h2>
            <Link to="/guardrails" className="btn btn--ghost btn--sm">
              View all
            </Link>
          </div>
          <div className="card__body">
            <div className="stack">
              {guardEvents.slice(0, 4).map((e) => (
                <div key={e.id} className="row row--between">
                  <span className="row">
                    <Badge
                      tone={
                        e.outcome === 'blocked'
                          ? 'danger'
                          : e.outcome === 'redacted'
                            ? 'warning'
                            : 'success'
                      }
                    >
                      {e.outcome}
                    </Badge>
                    <span>{e.guard}</span>
                  </span>
                  <span className="muted truncate">{e.detail}</span>
                </div>
              ))}
            </div>
          </div>
        </section>
      </div>
    </>
  );
}
