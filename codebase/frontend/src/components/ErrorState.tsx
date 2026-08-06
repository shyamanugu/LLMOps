/** Error state that renders a friendly message plus an optional retry action. */
import { ApiError } from '../api/client';

interface ErrorStateProps {
  error: unknown;
  onRetry?: () => void;
}

function describe(error: unknown): string {
  if (error instanceof ApiError) {
    return `${error.message}${error.body ? ` — ${error.body.slice(0, 180)}` : ''}`;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return 'An unexpected error occurred.';
}

export function ErrorState({ error, onRetry }: ErrorStateProps): JSX.Element {
  return (
    <div className="state state--error" role="alert">
      <div className="state__icon" aria-hidden="true">
        !
      </div>
      <div className="state__title">Something went wrong</div>
      <div className="state__desc">{describe(error)}</div>
      {onRetry ? (
        <button type="button" className="btn btn--secondary btn--sm" onClick={onRetry}>
          Retry
        </button>
      ) : null}
    </div>
  );
}
