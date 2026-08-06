/** Feedback page: stream of thumbs/edit/override events + a capture form. */
import { useState } from 'react';
import { PageHeader } from '../components/PageHeader';
import { AsyncSection } from '../components/AsyncSection';
import { DataTable, type Column } from '../components/DataTable';
import { Badge } from '../components/MetricBadge';
import { useCaptureFeedback, useFeedback } from '../hooks/useFeedback';
import { dateTime, shortId } from '../lib/format';
import type { FeedbackEvent, FeedbackKind } from '../api/types';

const KIND_TONE: Record<FeedbackKind, 'success' | 'info' | 'warning'> = {
  thumbs: 'success',
  edit: 'info',
  override: 'warning',
};

function CaptureForm(): JSX.Element {
  const capture = useCaptureFeedback();
  const [traceId, setTraceId] = useState('');
  const [kind, setKind] = useState<FeedbackKind>('thumbs');
  const [value, setValue] = useState('up');
  const [reason, setReason] = useState('');

  return (
    <section className="card">
      <div className="card__header">
        <h2 className="card__title">Capture feedback</h2>
      </div>
      <div className="card__body">
        <div className="row" style={{ flexWrap: 'wrap' }}>
          <label className="topbar__env">
            <span className="field__label">Trace id</span>
            <input
              type="text"
              value={traceId}
              onChange={(e) => setTraceId(e.target.value)}
              placeholder="trace_id"
            />
          </label>
          <label className="topbar__env">
            <span className="field__label">Kind</span>
            <select value={kind} onChange={(e) => setKind(e.target.value as FeedbackKind)}>
              <option value="thumbs">thumbs</option>
              <option value="edit">edit</option>
              <option value="override">override</option>
            </select>
          </label>
          <label className="topbar__env">
            <span className="field__label">Value</span>
            <input type="text" value={value} onChange={(e) => setValue(e.target.value)} />
          </label>
          <label className="topbar__env">
            <span className="field__label">Reason</span>
            <input type="text" value={reason} onChange={(e) => setReason(e.target.value)} placeholder="optional" />
          </label>
          <button
            type="button"
            className="btn btn--primary"
            disabled={capture.isPending || traceId.trim().length === 0}
            onClick={() =>
              capture.mutate({
                trace_id: traceId.trim(),
                kind,
                value,
                reason: reason.trim() || null,
              })
            }
          >
            {capture.isPending ? 'Saving…' : 'Submit'}
          </button>
        </div>
        {capture.data?.isPlaceholder ? (
          <p className="muted" style={{ marginTop: 12 }}>
            Feedback store not wired — event recorded locally only.
          </p>
        ) : null}
      </div>
    </section>
  );
}

export function Feedback(): JSX.Element {
  const query = useFeedback();

  const columns: ReadonlyArray<Column<FeedbackEvent>> = [
    { id: 'kind', header: 'Kind', render: (f) => <Badge tone={KIND_TONE[f.kind]}>{f.kind}</Badge> },
    { id: 'value', header: 'Value', render: (f) => f.value },
    { id: 'reason', header: 'Reason', render: (f) => <span className="muted">{f.reason ?? '—'}</span> },
    { id: 'trace', header: 'Trace', render: (f) => <span className="mono">{shortId(f.trace_id, 10)}</span> },
    { id: 'user', header: 'User', render: (f) => <span className="mono">{f.user_hash}</span> },
    { id: 'ts', header: 'When', render: (f) => dateTime(f.ts) },
  ];

  return (
    <>
      <PageHeader
        title="Feedback"
        subtitle="Thumbs, edits and overrides feed back into golden-set candidates."
      />
      <div className="stack">
        <CaptureForm />
        <section className="card">
          <div className="card__header">
            <h2 className="card__title">Feedback stream</h2>
          </div>
          <div className="card__body">
            <AsyncSection query={query} loadingLabel="Loading feedback…">
              {(rows) => (
                <DataTable
                  columns={columns}
                  rows={rows}
                  rowKey={(f) => f.id}
                  caption="Feedback events"
                  emptyTitle="No feedback yet"
                />
              )}
            </AsyncSection>
          </div>
        </section>
      </div>
    </>
  );
}
