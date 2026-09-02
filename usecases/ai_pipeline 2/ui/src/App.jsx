import React, { useEffect, useState } from 'react'
import Header from './components/Header.jsx'
import PipelineFlow from './components/PipelineFlow.jsx'
import LLMOpsStory from './components/LLMOpsStory.jsx'
import LLMOpsPanel from './components/LLMOpsPanel.jsx'
import KpiRow from './components/KpiRow.jsx'
import EmployeePanel from './components/EmployeePanel.jsx'
import { loadDefaultData, parseFile } from './data/loadData.js'

export default function App() {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadDefaultData()
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  async function handleLoadFile(file) {
    try {
      setError(null)
      setData(await parseFile(file))
    } catch (e) {
      setError(e.message)
    }
  }

  if (loading) return <div className="state">Loading pipeline data…</div>

  return (
    <div className="app">
      <Header meta={data?.meta || {}} onLoadFile={handleLoadFile} />
      {error && <div className="state state-error">⚠ {error}</div>}
      {data && (
        <main className="main">
          <LLMOpsStory />
          <PipelineFlow byStep={data.llmops?.by_step} />
          <LLMOpsPanel llmops={data.llmops || { totals: {}, by_step: [] }} />
          <KpiRow kpis={data.kpis} />
          <EmployeePanel employees={data.employees} />
          <footer className="footer">
            AI Pipeline AI Pipeline · instrumented by the AFNI LLMOps platform ·
            observability · model routing · guardrails · prompt management · evaluation gate · feedback loop
          </footer>
        </main>
      )}
    </div>
  )
}
