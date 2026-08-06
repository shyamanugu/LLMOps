/**
 * Clearly-labelled banner shown whenever a page is rendering placeholder/mock
 * data because a backend endpoint is not yet wired (ARCHITECTURE_SPEC §4).
 */

interface PlaceholderBannerProps {
  note?: string;
}

export function PlaceholderBanner({ note }: PlaceholderBannerProps): JSX.Element {
  return (
    <div className="placeholder-banner" role="note">
      <span className="placeholder-banner__tag">Placeholder data</span>
      <span>
        {note ??
          'This view is showing locally-generated placeholder data. Connect the backend endpoint to see live values.'}
      </span>
    </div>
  );
}
