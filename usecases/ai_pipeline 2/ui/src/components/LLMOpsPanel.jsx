import React from 'react'
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, Cell,
} from 'recharts'
import { fmtInt, fmtUSD, fmtMs } from '../data/format.js'

function Stat({ label, value, accent }) {
  return (
    <div className={'stat' + (accent ? ' stat-accent' : '')}>
      <div className="stat-value">{value}</div>
      <div className="stat-label">{label}</div>
    </div>
  )
}

export default function LLMOpsPanel({ llmops }) {
  const t = llmops.totals || {}
  const byStep = llmops.by_step || []
  const costIsZero = !t.cost_usd

  const latencyData = byStep.map((s) => ({ step: s.step, latency: Math.round(s.avg_latency_ms || 0) }))
  const costData = byStep.map((s) => ({ step: s.step, cost: Number((s.cost_usd || 0).toFixed(6)) }))

  return (
    <section className="section">
      <h2 className="section-title">LLMOps Observability</h2>
      <p className="section-caption">
        Every model call is traced by the AFNI LLMOps platform. PII is flagged, not blocked —
        call data is never dropped; secrets are blocked.
      </p>

      <div className="stat-grid">
        <Stat label="LLM Calls" value={fmtInt(t.llm_calls)} accent />
        <Stat label="Input Tokens" value={fmtInt(t.input_tokens)} />
        <Stat label="Output Tokens" value={fmtInt(t.output_tokens)} />
        <Stat label="Cost (USD)" value={fmtUSD(t.cost_usd)} />
        <Stat label="Avg Latency" value={fmtMs(t.avg_latency_ms)} />
        <Stat label="Guardrail Flags" value={fmtInt(t.guardrail_flags)} />
        <Stat label="Errors" value={fmtInt(t.errors)} />
      </div>

      {costIsZero && (
        <div className="note">
          Cost shows <strong>$0</strong> until per-token rates are set for this deployment in
          <code> pricing.yaml</code>. Tokens, latency, and guardrail data are live.
        </div>
      )}

      <div className="chart-row">
        <div className="chart-card">
          <div className="chart-title">Avg latency by step</div>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={latencyData} margin={{ top: 8, right: 12, bottom: 8, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e9f0" />
              <XAxis dataKey="step" tick={{ fontSize: 11 }} interval={0} angle={-12} textAnchor="end" height={50} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip formatter={(v) => fmtMs(v)} />
              <Bar dataKey="latency" radius={[4, 4, 0, 0]}>
                {latencyData.map((_, i) => <Cell key={i} fill="#3b6fb6" />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-card">
          <div className="chart-title">Cost by step (USD)</div>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={costData} margin={{ top: 8, right: 12, bottom: 8, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e9f0" />
              <XAxis dataKey="step" tick={{ fontSize: 11 }} interval={0} angle={-12} textAnchor="end" height={50} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip formatter={(v) => fmtUSD(v)} />
              <Bar dataKey="cost" radius={[4, 4, 0, 0]}>
                {costData.map((_, i) => <Cell key={i} fill="#5a9367" />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </section>
  )
}
