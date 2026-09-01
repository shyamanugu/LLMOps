import React from 'react'

// The client-facing "why this matters" narrative: what the LLMOps platform is,
// the components wrapping THIS pipeline, and why it's reusable across use cases.

const COMPONENTS = [
  { n: '02', name: 'Prompt Management', in: true,
    desc: 'Versioned, git-backed prompts. Edit prompts without touching code.' },
  { n: '03', name: 'Model Management', in: true,
    desc: 'Model choice by alias (reason / bulk), config-as-code. Swap models per environment, no redeploy.' },
  { n: '04', name: 'Evaluation Gate', in: true,
    desc: 'Golden-dataset tests in CI. A prompt or model change can’t ship unless it passes.' },
  { n: '05', name: 'Observability', in: true,
    desc: 'Every model call traced: tokens, cost, latency, guardrail decisions.' },
  { n: '06', name: 'Guardrails', in: true,
    desc: 'PII flagged, secrets blocked, before/after every call — governed by policy.' },
  { n: '11', name: 'Feedback Loop', in: true,
    desc: 'Human corrections captured and promoted into the next round of golden tests.' },
]

const REUSE = [
  { title: 'This use case', body: 'AIA call analytics — one pipeline, onboarded to the platform.' },
  { title: 'Voice Agent', body: 'Real-time contact-center automation — same platform, same guardrails.' },
  { title: 'PI Index', body: 'Performance intelligence across 100% of interactions.' },
  { title: 'Hiring Intelligence', body: 'Fair, high-volume recruitment — reuses the same paved road.' },
]

export default function LLMOpsStory() {
  return (
    <section className="section story">
      <h2 className="section-title">What is LLMOps &mdash; and why it matters</h2>
      <p className="story-lead">
        AFNI didn&rsquo;t build a one-off AI feature. It built a <strong>governed platform</strong> &mdash;
        a factory that produces AI use cases quickly, safely, and cost-effectively. This dashboard is
        one use case (<strong>AIA call analytics</strong>) running <em>on</em> that platform. The pipeline
        stays focused on the domain; the platform wraps every model call with observability, cost control,
        guardrails, versioned prompts, and an evaluation gate &mdash; <strong>by construction, not bolted on.</strong>
      </p>

      <div className="story-block">
        <h3 className="story-h3">The components wrapping this pipeline</h3>
        <div className="story-grid">
          {COMPONENTS.map((c) => (
            <div className="story-card" key={c.n}>
              <div className="story-card-head">
                <span className="story-num">{c.n}</span>
                <span className="story-name">{c.name}</span>
                <span className="story-live" title="active for this pipeline">live</span>
              </div>
              <p className="story-desc">{c.desc}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="story-block">
        <h3 className="story-h3">Reusability &mdash; build once, onboard many</h3>
        <p className="story-lead">
          Onboarding a new use case is a <strong>config change, not a rebuild</strong>: register model
          aliases, a guardrail policy, prompts, and eval thresholds. The 4th, 10th, and 40th use case
          reuse the same paved road &mdash; time-to-value drops from quarters to weeks.
        </p>
        <div className="reuse-row">
          {REUSE.map((r, i) => (
            <React.Fragment key={r.title}>
              <div className={'reuse-card' + (i === 0 ? ' reuse-card-active' : '')}>
                <div className="reuse-title">{r.title}</div>
                <div className="reuse-body">{r.body}</div>
              </div>
              {i < REUSE.length - 1 && <div className="reuse-plus">+</div>}
            </React.Fragment>
          ))}
        </div>
        <p className="story-foot">
          One platform &middot; one multi-agent pattern &middot; every use case governed the same way.
        </p>
      </div>
    </section>
  )
}
