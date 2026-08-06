/** KPI stat tile with value, unit and an optional trend indicator. */
import type { TrendDirection } from '../api/types';

interface StatTileProps {
  label: string;
  value: string;
  unit?: string;
  trend?: TrendDirection;
  changePct?: number;
  hint?: string;
}

const TREND_GLYPH: Record<TrendDirection, string> = {
  up: '▲',
  down: '▼',
  flat: '▬',
};

export function StatTile({
  label,
  value,
  unit,
  trend,
  changePct,
  hint,
}: StatTileProps): JSX.Element {
  return (
    <div className="stat-tile">
      <div className="stat-tile__label">{label}</div>
      <div className="stat-tile__value">
        {value}
        {unit ? <span className="muted" style={{ fontSize: 14, marginLeft: 4 }}>{unit}</span> : null}
      </div>
      <div className="stat-tile__foot">
        {trend ? (
          <span className={`trend trend--${trend}`}>
            {TREND_GLYPH[trend]}
            {changePct !== undefined ? ` ${Math.abs(changePct).toFixed(1)}%` : ''}
          </span>
        ) : null}
        {hint ? <span>{hint}</span> : null}
      </div>
    </div>
  );
}
