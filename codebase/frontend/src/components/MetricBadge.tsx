/** Small status pill + metric-with-score badge used across the console. */
import type { StatusTone } from '../theme/theme';

interface BadgeProps {
  tone?: StatusTone;
  children: React.ReactNode;
}

/** A coloured pill for statuses, categories and labels. */
export function Badge({ tone = 'neutral', children }: BadgeProps): JSX.Element {
  return <span className={`badge badge--${tone}`}>{children}</span>;
}

interface MetricBadgeProps {
  name: string;
  score: number;
  threshold?: number;
  passed?: boolean;
}

/** Renders a named metric score, coloured by pass/fail against a threshold. */
export function MetricBadge({
  name,
  score,
  threshold,
  passed,
}: MetricBadgeProps): JSX.Element {
  const isPassed = passed ?? (threshold !== undefined ? score >= threshold : true);
  const tone: StatusTone = isPassed ? 'success' : 'danger';
  return (
    <span className="metric-badge" title={threshold !== undefined ? `threshold ${threshold}` : undefined}>
      <span className="metric-badge__name">{name}</span>
      <Badge tone={tone}>
        <span className="metric-badge__score">{score.toFixed(2)}</span>
      </Badge>
    </span>
  );
}
