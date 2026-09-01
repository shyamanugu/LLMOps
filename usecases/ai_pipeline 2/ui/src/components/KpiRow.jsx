import React from 'react'
import { fmtValue, deltaMeta } from '../data/format.js'

export default function KpiRow({ kpis }) {
  if (!kpis || kpis.length === 0) return null
  return (
    <section className="section">
      <h2 className="section-title">Key Performance Indicators</h2>
      <div className="kpi-grid">
        {kpis.map((k) => {
          const d = deltaMeta(k.delta, k.unit)
          return (
            <div className="kpi-card" key={k.key || k.label}>
              <div className="kpi-label">{k.label}</div>
              <div className="kpi-value">{fmtValue(k.value, k.unit, k.unit === 'percent' ? 0 : 0)}</div>
              {d.text && <div className={'kpi-delta kpi-delta-' + d.dir}>{d.text} vs prior</div>}
            </div>
          )
        })}
      </div>
    </section>
  )
}
