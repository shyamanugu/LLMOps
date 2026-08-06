/** Neutral empty-state placeholder for lists/tables with no rows. */
import type { ReactNode } from 'react';

interface EmptyStateProps {
  title?: string;
  description?: string;
  icon?: string;
  action?: ReactNode;
}

export function EmptyState({
  title = 'Nothing here yet',
  description,
  icon = '∅',
  action,
}: EmptyStateProps): JSX.Element {
  return (
    <div className="state">
      <div className="state__icon" aria-hidden="true">
        {icon}
      </div>
      <div className="state__title">{title}</div>
      {description ? <div className="state__desc">{description}</div> : null}
      {action}
    </div>
  );
}
