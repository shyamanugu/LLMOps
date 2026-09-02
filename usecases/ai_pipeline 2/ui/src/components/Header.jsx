import React, { useRef } from 'react'

export default function Header({ meta, onLoadFile }) {
  const fileRef = useRef(null)

  const chips = [
    ['Program', meta.program],
    ['Date', meta.date],
    ['Environment', meta.environment],
    ['Model', meta.model_deployment],
    ['Run', meta.run_id],
  ].filter(([, v]) => v)

  // Resolve mock vs live from meta.mode (fallback to the legacy source field).
  function ModePill({ meta }) {
    const isMock = (meta.mode || (meta.source === 'live' ? 'real' : 'mock')) !== 'real'
    return (
      <span className={'badge ' + (isMock ? 'badge-mock' : 'badge-live')}>
        {isMock ? '● MOCK DEMO' : '● LIVE DATA'}
      </span>
    )
  }

  function handleFile(e) {
    const file = e.target.files?.[0]
    if (file) onLoadFile(file)
    e.target.value = ''
  }

  return (
    <header className="header">
      <div className="header-main">
        <div>
          <h1 className="title">
            AI Pipeline <span className="title-dim">— AI Pipeline Intelligence</span>
          </h1>
          <p className="subtitle">Powered by AFNI LLMOps</p>
        </div>
        <div className="header-actions">
          <ModePill meta={meta} />
          <button className="btn" onClick={() => fileRef.current?.click()}>Load run…</button>
          <input
            ref={fileRef}
            type="file"
            accept="application/json,.json"
            style={{ display: 'none' }}
            onChange={handleFile}
          />
        </div>
      </div>
      <div className="chips">
        {chips.map(([k, v]) => (
          <span className="chip" key={k}>
            <span className="chip-key">{k}</span>
            <span className="chip-val">{v}</span>
          </span>
        ))}
      </div>
    </header>
  )
}
