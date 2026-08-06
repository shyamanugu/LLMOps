/** Centered loading spinner with an accessible live region. */

interface LoadingStateProps {
  label?: string;
}

export function LoadingState({ label = 'Loading…' }: LoadingStateProps): JSX.Element {
  return (
    <div className="state" role="status" aria-live="polite">
      <div className="spinner" aria-hidden="true" />
      <div className="state__desc">{label}</div>
    </div>
  );
}
