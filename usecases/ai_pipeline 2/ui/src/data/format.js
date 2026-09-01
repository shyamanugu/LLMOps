// Number/label formatting shared across components.

export function fmtInt(n) {
  return (n ?? 0).toLocaleString('en-US')
}

// A 0..1 fraction -> "88%"; falls back gracefully for out-of-range values.
export function fmtPercent(v, digits = 0) {
  if (v == null) return '—'
  return (v * 100).toFixed(digits) + '%'
}

export function fmtValue(value, unit, digits = 0) {
  if (value == null) return '—'
  if (unit === 'percent') return fmtPercent(value, digits)
  return fmtInt(Math.round(value))
}

// Small currency: show enough precision to be meaningful when tiny.
export function fmtUSD(n) {
  const v = n ?? 0
  if (v === 0) return '$0.00'
  if (v < 1) return '$' + v.toFixed(4)
  return '$' + v.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

export function fmtMs(n) {
  const v = n ?? 0
  if (v >= 1000) return (v / 1000).toFixed(2) + 's'
  return Math.round(v) + 'ms'
}

// delta -> { text, dir } where dir is 'up' | 'down' | 'flat'
export function deltaMeta(delta, unit) {
  if (delta == null) return { text: '', dir: 'flat' }
  const dir = delta > 0 ? 'up' : delta < 0 ? 'down' : 'flat'
  const mag = unit === 'percent' ? (Math.abs(delta) * 100).toFixed(1) + 'pp'
                                  : fmtInt(Math.abs(Math.round(delta)))
  const arrow = dir === 'up' ? '▲' : dir === 'down' ? '▼' : '■'
  return { text: `${arrow} ${mag}`, dir }
}
