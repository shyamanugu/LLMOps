import React from 'react'
import { fmtInt, fmtUSD } from '../data/format.js'

const STAGES = [
  { key: 'denoise', label: 'Denoise', desc: 'Clean raw transcripts' },
  { key: 'analysis', label: 'Analysis', desc: 'Per-call scoring' },
  { key: 'summary', label: 'Summary', desc: 'Weekly reflection' },
  { key: 'individual_metrics', label: 'Individual Metrics', desc: 'Coaching metrics' },
  { key: 'kpi', label: 'KPI', desc: 'Aggregate → report' },
]

export default function PipelineFlow({ byStep }) {
  const byKey = Object.fromEntries((byStep || []).map((s) => [s.step, s]))

  return (
    <section className="section">
      <h2 className="section-title">Pipeline</h2>
      <div className="flow">
        {STAGES.map((stage, i) => {
          const s = byKey[stage.key]
          return (
            <React.Fragment key={stage.key}>
              <div className="flow-node">
                <div className="flow-label">{stage.label}</div>
                <div className="flow-desc">{stage.desc}</div>
                {s ? (
                  <div className="flow-stat">
                    {fmtInt(s.calls)} calls · {fmtUSD(s.cost_usd)}
                  </div>
                ) : (
                  <div className="flow-stat flow-stat-muted">no LLM calls</div>
                )}
              </div>
              {i < STAGES.length - 1 && <div className="flow-arrow">→</div>}
            </React.Fragment>
          )
        })}
      </div>
    </section>
  )
}
