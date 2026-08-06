/**
 * Renders a nested trace/span tree. Spans nest request > agent > model/tool,
 * matching the OpenTelemetry GenAI conventions used by the backend tracing.
 */
import { useState } from 'react';
import type { Span, SpanKind } from '../api/types';
import { Badge } from './MetricBadge';
import type { StatusTone } from '../theme/theme';

const KIND_TONE: Record<SpanKind, StatusTone> = {
  request: 'info',
  agent: 'info',
  model: 'success',
  tool: 'warning',
  guardrail: 'neutral',
};

interface SpanNodeProps {
  span: Span;
  depth: number;
}

function formatMs(ms: number): string {
  return ms >= 1000 ? `${(ms / 1000).toFixed(2)}s` : `${ms}ms`;
}

function SpanNode({ span, depth }: SpanNodeProps): JSX.Element {
  const [open, setOpen] = useState(true);
  const hasChildren = span.children.length > 0;

  return (
    <div className="span-node" role="treeitem" aria-expanded={hasChildren ? open : undefined}>
      <div className="span-node__row">
        {hasChildren ? (
          <button
            type="button"
            className="span-node__toggle"
            onClick={() => setOpen((prev) => !prev)}
            aria-label={open ? 'Collapse span' : 'Expand span'}
          >
            {open ? '▾' : '▸'}
          </button>
        ) : (
          <span className="span-node__toggle" aria-hidden="true">
            ·
          </span>
        )}
        <Badge tone={span.status === 'error' ? 'danger' : KIND_TONE[span.kind]}>
          {span.kind}
        </Badge>
        <span className="span-node__name">{span.name}</span>
        <span className="span-node__meta">
          <span>{formatMs(span.duration_ms)}</span>
          {span.tokens !== null ? <span>{span.tokens.toLocaleString()} tok</span> : null}
          {span.cost_usd !== null ? <span>${span.cost_usd.toFixed(4)}</span> : null}
        </span>
      </div>
      {hasChildren && open ? (
        <div className="span-node__children" role="group">
          {span.children.map((child) => (
            <SpanNode key={child.span_id} span={child} depth={depth + 1} />
          ))}
        </div>
      ) : null}
    </div>
  );
}

interface SpanTreeProps {
  root: Span;
}

export function SpanTree({ root }: SpanTreeProps): JSX.Element {
  return (
    <div className="span-tree" role="tree" aria-label="Trace span tree">
      <SpanNode span={root} depth={0} />
    </div>
  );
}
