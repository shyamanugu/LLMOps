import React, { useState } from 'react'
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, Legend, Cell,
} from 'recharts'
import { fmtInt, fmtPercent, fmtValue } from '../data/format.js'

export default function EmployeePanel({ employees }) {
  const [selected, setSelected] = useState(0)
  if (!employees || employees.length === 0) return null
  const emp = employees[selected] || employees[0]

  return (
    <section className="section">
      <h2 className="section-title">Agent Coaching Intelligence</h2>
      <div className="emp-layout">
        <aside className="emp-list">
          {employees.map((e, i) => (
            <button
              key={e.employee_id || i}
              className={'emp-list-item' + (i === selected ? ' emp-list-item-active' : '')}
              onClick={() => setSelected(i)}
            >
              <div className="emp-list-name">{e.name}</div>
              <div className="emp-list-meta">Coach: {e.coach || '—'}</div>
              <div className="emp-list-meta">{fmtInt(e.calls_analyzed)} calls analyzed</div>
            </button>
          ))}
        </aside>

        <div className="emp-detail">
          <EmployeeDetail emp={emp} />
        </div>
      </div>
    </section>
  )
}

function EmployeeDetail({ emp }) {
  const scoreData = (emp.scores || []).map((s) => ({
    label: s.label,
    pct: Math.round((s.value || 0) * 100),
  }))
  const cmpData = (emp.comparisons || []).map((c) => ({
    metric: c.metric,
    Individual: Number(c.individual || 0),
    'Team Avg': Number(c.teamAvg || 0),
  }))

  return (
    <>
      <div className="emp-head">
        <div>
          <div className="emp-name">{emp.name}</div>
          <div className="emp-sub">Coach: {emp.coach || '—'} · {fmtInt(emp.calls_analyzed)} calls</div>
        </div>
      </div>

      {emp.reflection && (
        <div className="callout">
          <div className="callout-label">AI Coaching Reflection</div>
          <p className="callout-text">{emp.reflection}</p>
        </div>
      )}

      <div className="emp-charts">
        {scoreData.length > 0 && (
          <div className="chart-card">
            <div className="chart-title">Behavior scores</div>
            <ResponsiveContainer width="100%" height={Math.max(180, scoreData.length * 34)}>
              <BarChart data={scoreData} layout="vertical" margin={{ top: 4, right: 24, bottom: 4, left: 8 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e9f0" horizontal={false} />
                <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 11 }} unit="%" />
                <YAxis type="category" dataKey="label" width={130} tick={{ fontSize: 11 }} />
                <Tooltip formatter={(v) => v + '%'} />
                <Bar dataKey="pct" radius={[0, 4, 4, 0]}>
                  {scoreData.map((d, i) => (
                    <Cell key={i} fill={d.pct >= 80 ? '#5a9367' : d.pct >= 60 ? '#c79a3a' : '#c05a5a'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {cmpData.length > 0 && (
          <div className="chart-card">
            <div className="chart-title">Individual vs team average</div>
            <ResponsiveContainer width="100%" height={Math.max(180, cmpData.length * 44)}>
              <BarChart data={cmpData} margin={{ top: 4, right: 16, bottom: 4, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e9f0" />
                <XAxis dataKey="metric" tick={{ fontSize: 11 }} interval={0} angle={-10} textAnchor="end" height={50} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Legend wrapperStyle={{ fontSize: 12 }} />
                <Bar dataKey="Individual" fill="#3b6fb6" radius={[4, 4, 0, 0]} />
                <Bar dataKey="Team Avg" fill="#a9bcd0" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {(emp.top_calls || []).length > 0 && (
        <div className="subsection">
          <h3 className="subsection-title">Top calls</h3>
          <div className="call-grid">
            {emp.top_calls.map((c, i) => (
              <div className="call-card" key={c.contact_id || i}>
                <div className="call-head">
                  <span className="call-id">#{c.contact_id}</span>
                  {c.outcome && <span className="badge badge-outcome">{c.outcome}</span>}
                </div>
                {c.intent && <div className="call-intent">{c.intent}</div>}
                {(c.tags || []).length > 0 && (
                  <div className="tag-row">
                    {c.tags.map((tg) => <span className="tag" key={tg}>{tg}</span>)}
                  </div>
                )}
                {c.excerpt && <p className="call-excerpt">{c.excerpt}</p>}
              </div>
            ))}
          </div>
        </div>
      )}

      {(emp.escalations || []).length > 0 && (
        <div className="subsection">
          <h3 className="subsection-title">Escalations</h3>
          <div className="call-grid">
            {emp.escalations.map((e, i) => (
              <div className="call-card call-card-alert" key={e.contact_id || i}>
                <div className="call-head">
                  <span className="call-id">#{e.contact_id}</span>
                  <span className="badge badge-alert">escalation</span>
                </div>
                {e.reason && <div className="call-intent">{e.reason}</div>}
                {e.excerpt && <p className="call-excerpt">{e.excerpt}</p>}
              </div>
            ))}
          </div>
        </div>
      )}
    </>
  )
}
